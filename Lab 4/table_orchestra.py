"""One table, one speaker, three sensors, all in C major.

The piece is Beethoven's Ode to Joy, the same score as
twizzler_orchestra.py. It loops at 100 BPM. The parts are written to
enter on top of each other and stay in one harmony.

Sitting down. The Qwiic VCNL4040 watches the place setting. A higher
reading means closer. The harmony bed fades up as someone leans in:

    far                  silence
    cello
    cello + viola
    cello + viola + horn

That bed also gets louder as the reading rises. At startup the script
reads the empty table and stays silent until someone raises the count
above that. The servo gets no pulse until that same detection. While
someone is in range it sweeps the way servo_test.py does, and the
pulse is released again when they leave. The count is not centimeters.

Touch. Six conductive objects on the MPR121. Holding one plays that
line at full level. Letting go fades only that line. Viola and horn
also join the harmony when someone sits close, and stay if the pad
is still held after they lean away.

    pad 1    violin
    pad 3    flute
    pad 5    oboe
    pad 6    timpani
    pad 8    viola
    pad 10   horn

Notes written below middle C are played one or two octaves higher, in the
same key, so a small speaker can produce them. The timpani is a struck
drum on those same notes.

The bowl. The APDS-9960 sits under one object, looking up. A hand
resting over it stays silent. Circling the rim, the way a mallet wakes
a singing bowl, rings a C major drone (C, E, G), so it sits in the same
chord as Ode to Joy. Where the hand is around the circle picks which
harmonic is bright. The tone keeps ringing for a moment after the
circle stops.

All of this is mixed in one audio callback. The callback never reads
a sensor.
"""

import math
import time

import board
import numpy as np
import sounddevice as sd
import adafruit_mpr121
import qwiic_proximity
from adafruit_apds9960.apds9960 import APDS9960
from adafruit_servokit import ServoKit

import twizzler_orchestra as score

# 1.0 is full scale, the "volume 100" level.
MASTER = 1.0
# Small speakers fade out under middle C. Notes below this are doubled
# until they clear it. C stays C, so the harmony does not change.
SPEAKER_FLOOR = 261.63

# Qwiic proximity counts. Higher means closer.
# The empty table is measured at startup. Harmony and the servo stay
# off until the reading rises above that resting count by QWIIC_MARGIN.
# QWIIC_SPAN counts past that point bring in the full bed.
QWIIC_MARGIN = 30
QWIIC_SPAN = 180
# Harmony that arrives as someone sits down, in that order.
BED = ("cello", "viola", "horn")
# Same hat, channel, and pulse range as servo_test.py.
# angle None sends no pulse, so the servo stays still.
# A Qwiic detection starts the 180 / 0 sweep. Leaving releases it again.
SERVO_CHANNEL = 2
SERVO_SWEEP_S = 2.0
# MPR121 pad, then the part it plays while held.
TOUCH = (
    (1, "violin"),
    (3, "flute"),
    (5, "oboe"),
    (6, "timpani"),
    (8, "viola"),
    (10, "horn"),
)

# APDS-9960 photodiode sums. The bowl uses these, not gesture() directions.
# A rise above the resting sum also counts as a hand over the object.
BOWL_MIN = 30
BOWL_ENERGY_MARGIN = 50
BOWL_ENERGY_SPAN = 250
BOWL_HOLD_S = 0.20
BOWL_ATTACK_S = 0.30
BOWL_RELEASE_S = 1.80
# C major partials, from C4 up: fundamental, fifth, octave, third.
BOWL_FREQS = (score.C4, score.G4, score.C4 * 2, score.E4 * 2)
BOWL_NAMES = ("fundamental", "fifth", "octave", "third")

# Gesture FIFO registers. gesture() would block until the hand left and
# would throw these four counts away, so the bowl reads the FIFO itself.
_GFLVL = 0xAE
_GSTATUS = 0xAF
_GFOV = 0x02
_GCONF4 = 0xAB
_GFIFO_CLR = 0x04
_GFIFO_U = 0xFC


def _audible(span: float) -> float:
    """A detected hand starts at a level the speaker can actually play."""
    if span <= 0.0:
        return 0.0
    if span >= 1.0:
        return 1.0
    return 0.62 + 0.38 * span


def bed_state(prox: float, floor: float) -> tuple[int, float]:
    """How many bed parts are on, and how loud the bed is, from one proximity count.

    floor is the empty-table count. At or below it, the bed is silent.
    """
    if prox <= floor:
        return 0, 0.0
    span = min(prox - floor, QWIIC_SPAN) / QWIIC_SPAN
    count = int(span * len(BED)) + 1
    if count > len(BED):
        count = len(BED)
    return count, _audible(span)


def _angle_delta(a: float, b: float) -> float:
    """Shortest step between two angles, in radians."""
    return abs((a - b + math.pi) % (2 * math.pi) - math.pi)


def bowl_from_diodes(up: float, down: float, left: float, right: float, energy_floor: float):
    """Loudness, harmonic weights, and the hand's angle around the rim.

    Returns None when nothing is over the opening. A still hand keeps a
    steady angle, so the caller can tell a circle from a proximity hover.
    """
    energy = up + down + left + right
    if energy < BOWL_MIN:
        return None
    if energy <= energy_floor:
        level = 0.0
    else:
        span = min(energy - energy_floor, BOWL_ENERGY_SPAN) / BOWL_ENERGY_SPAN
        level = _audible(span)
    x = right - left
    y = up - down
    angle = math.atan2(y, x)
    if math.hypot(x, y) < 12:
        weights = (1.0, 0.22, 0.16, 0.12)
    else:
        fifth = 0.12 + 0.55 * (0.5 + 0.5 * math.cos(angle))
        octave = 0.12 + 0.55 * (0.5 + 0.5 * math.cos(angle - 2.094395))
        third = 0.08 + 0.42 * (0.5 + 0.5 * math.cos(angle + 2.094395))
        weights = (1.0, fifth, octave, third)
    return level, weights, angle


def _in_speaker_range(freq: np.ndarray) -> np.ndarray:
    """Move sounding notes up by octaves until they clear SPEAKER_FLOOR."""
    out = np.asarray(freq, dtype=np.float64).copy()
    for _ in range(3):
        low = (out > 0.0) & (out < SPEAKER_FLOOR)
        if not np.any(low):
            break
        out = np.where(low, out * 2.0, out)
    return out


def _timpani(t, f, remain, noise):
    """Struck drum on the written pitch, with a mallet attack and a short ring."""
    drop = (f * 0.1) * (1.0 - np.exp(-16.0 * t))
    phase = 2 * np.pi * (f * t - drop)
    ring = np.exp(-t * 8.0) * np.clip(remain / score.RELEASE, 0.0, 1.0) * (f > 0.0)
    head = np.sin(1.9 * phase) * np.exp(-t * 14.0)
    mallet = noise * np.exp(-t * 50.0)
    tick = np.sin(2 * np.pi * 1500.0 * t) * np.exp(-t * 70.0)
    return ring * (np.sin(phase) + 0.4 * head) + (f > 0.0) * (0.5 * mallet + 0.18 * tick)


def _glide(start: float, target: float, frames: int, seconds: float) -> tuple[np.ndarray, float]:
    step = 1.0 / max(1, int(seconds * score.SAMPLE_RATE))
    ramp = np.arange(1, frames + 1)
    if target >= start:
        values = np.minimum(start + step * ramp, target)
    else:
        values = np.maximum(start - step * ramp, target)
    return values, float(values[-1])


def _read8(device, register: int) -> int:
    buf = bytearray(2)
    buf[0] = register
    with device as i2c:
        i2c.write_then_readinto(buf, buf, out_end=1, in_end=1)
    return buf[0]


def _set_bit(device, register: int, mask: int) -> None:
    buf = bytearray(2)
    buf[0] = register
    with device as i2c:
        i2c.write_then_readinto(buf, buf, out_end=1, in_start=1)
    buf[0] = register
    buf[1] |= mask
    with device as i2c:
        i2c.write(buf, end=2)


def read_diodes(device):
    """Average up, down, left, right counts, or None if the hand is away."""
    if _read8(device, _GSTATUS) & _GFOV:
        _set_bit(device, _GCONF4, _GFIFO_CLR)
        return None
    level = _read8(device, _GFLVL)
    if level <= 0:
        return None
    count = min(level, 32)
    buf = bytearray(1 + count * 4)
    buf[0] = _GFIFO_U
    with device as i2c:
        i2c.write_then_readinto(buf, buf, out_end=1, in_start=1, in_end=1 + count * 4)
    sums = [0.0, 0.0, 0.0, 0.0]
    used = 0
    for i in range(count):
        sample = [buf[1 + i * 4 + k] for k in range(4)]
        if sample == [255, 255, 255, 255]:
            continue
        if sum(sample) < BOWL_MIN:
            continue
        for k in range(4):
            sums[k] += sample[k]
        used += 1
    if used == 0:
        return None
    return tuple(value / used for value in sums)


class Orchestra:
    """Shared clock. Sensors only set targets. This mixes them."""

    def __init__(self) -> None:
        n = len(score.PARTS)
        self.touch_on = [False] * n
        self.bed_on = [False] * n
        self.touch_gain = [0.0] * n
        self.bed_gain = [0.0] * n
        self.bed_level = 0.0
        self.bed_target = 0.0
        self.bowl_level = 0.0
        self.bowl_target = 0.0
        self.bowl_weights = [0.0, 0.0, 0.0, 0.0]
        self.bowl_targets = (1.0, 0.2, 0.15, 0.1)
        self.n = 0
        self.samples = 0
        self.stream = sd.OutputStream(
            samplerate=score.SAMPLE_RATE,
            channels=1,
            dtype="float32",
            blocksize=512,
            callback=self._callback,
        )
        self.stream.start()

    def _callback(self, outdata, frames, _time, status) -> None:
        if status:
            print(status)
        idx = (self.n + np.arange(frames)) % score.PHRASE
        self.n = (self.n + frames) % score.PHRASE
        noise = np.random.uniform(-1.0, 1.0, frames)
        parts = (
            (score._violin, score.VIOLIN_F, score.VIOLIN_AGE, score.VIOLIN_DUR, 0.34),
            (score._viola, score.VIOLA_F, score.VIOLA_AGE, score.VIOLA_DUR, 0.30),
            (score._cello, score.CELLO_F, score.CELLO_AGE, score.CELLO_DUR, 0.42),
            (score._flute, score.FLUTE_F, score.FLUTE_AGE, score.FLUTE_DUR, 0.26),
            (score._horn, score.HORN_F, score.HORN_AGE, score.HORN_DUR, 0.36),
            (_timpani, score.TIMPANI_F, score.TIMPANI_AGE, score.TIMPANI_DUR, 0.50),
            (score._oboe, score.OBOE_F, score.OBOE_AGE, score.OBOE_DUR, 0.34),
        )
        into = idx % score.EIGHTH
        mix = np.zeros(frames, dtype=np.float64)
        step_up = 1.0 / int(0.10 * score.SAMPLE_RATE)
        ramp = np.arange(1, frames + 1)
        bed_env, self.bed_level = _glide(self.bed_level, self.bed_target, frames, 0.25)
        for i, (voice, freq, age, dur, level) in enumerate(parts):
            touch_target = 1.0 if self.touch_on[i] else 0.0
            bed_part_target = 1.0 if self.bed_on[i] else 0.0
            if (
                touch_target == 0.0
                and self.touch_gain[i] <= 0.0
                and bed_part_target == 0.0
                and self.bed_gain[i] <= 0.0
            ):
                continue
            if touch_target > self.touch_gain[i]:
                touch_g = np.minimum(self.touch_gain[i] + step_up * ramp, 1.0)
            else:
                touch_g = np.maximum(self.touch_gain[i] - step_up * ramp, 0.0)
            self.touch_gain[i] = float(touch_g[-1])
            if bed_part_target > self.bed_gain[i]:
                bed_g = np.minimum(self.bed_gain[i] + step_up * ramp, 1.0)
            else:
                bed_g = np.maximum(self.bed_gain[i] - step_up * ramp, 0.0)
            self.bed_gain[i] = float(bed_g[-1])
            if score.PARTS[i] in BED:
                gains = np.maximum(touch_g, bed_g * bed_env)
            else:
                gains = touch_g
            slot = idx // score.EIGHTH
            heard = _in_speaker_range(freq[slot])
            t = (age[slot] * score.EIGHTH + into) / score.SAMPLE_RATE
            remain = dur[slot] * score.EIGHTH - age[slot] * score.EIGHTH - into
            mix += gains * voice(t, heard, remain, noise) * level

        bowl_seconds = BOWL_ATTACK_S if self.bowl_target >= self.bowl_level else BOWL_RELEASE_S
        bowl_env, self.bowl_level = _glide(self.bowl_level, self.bowl_target, frames, bowl_seconds)
        targets = self.bowl_targets
        for k in range(len(BOWL_FREQS)):
            self.bowl_weights[k] += (float(targets[k]) - self.bowl_weights[k]) * 0.2
        if self.bowl_level > 0.0008:
            bt = (self.samples + np.arange(frames)) / score.SAMPLE_RATE
            tone = np.zeros(frames, dtype=np.float64)
            for k, freq in enumerate(BOWL_FREQS):
                tone += self.bowl_weights[k] * np.sin(2 * np.pi * freq * bt)
            mix += tone * bowl_env * 0.42
        self.samples += frames
        outdata[:, 0] = np.clip(mix * MASTER, -1.0, 1.0).astype(np.float32)

    def close(self) -> None:
        self.stream.stop()
        self.stream.close()


def _bed_names(count: int) -> str:
    if count <= 0:
        return "silence"
    return " + ".join(BED[:count])


def main() -> None:
    touch_names = {name for _, name in TOUCH}
    if not touch_names <= set(score.PARTS) or not set(BED) <= set(score.PARTS):
        raise RuntimeError("Every part must come from the orchestra")

    i2c = board.I2C()
    mpr121 = adafruit_mpr121.MPR121(i2c)
    apds = APDS9960(i2c)
    apds.enable_proximity = True
    apds.proximity_gain = 3
    apds.gesture_gain = 3
    apds.enable_gesture = True

    qwiic = qwiic_proximity.QwiicProximity()
    if not qwiic.connected:
        raise RuntimeError("Qwiic proximity sensor not found. Check the Qwiic cable.")
    qwiic.begin()

    print("Step back from the Qwiic sensor, and leave the bowl object as it sits.")
    resting_samples = []
    energy_samples = []
    for _ in range(8):
        resting_samples.append(float(qwiic.get_proximity()))
        diodes = read_diodes(apds.i2c_device)
        if diodes is not None:
            energy_samples.append(sum(diodes))
        time.sleep(0.05)
    qwiic_floor = max(resting_samples) + QWIIC_MARGIN
    energy_floor = (max(energy_samples) if energy_samples else float(BOWL_MIN)) + BOWL_ENERGY_MARGIN
    print(
        f"Empty Qwiic reading {max(resting_samples):.0f}. "
        f"Harmony starts above {qwiic_floor:.0f}."
    )

    kit = ServoKit(channels=16, i2c=i2c)
    servo = kit.servo[SERVO_CHANNEL]
    servo.set_pulse_width_range(500, 2500)
    servo.angle = None

    part_index = {name: i for i, name in enumerate(score.PARTS)}
    orchestra = Orchestra()
    held = {pad: False for pad, _ in TOUCH}
    bed_count = 0
    prox_smooth = 0.0
    last_prox_print = -9999.0
    bowl_on = False
    bowl_color = ""
    last_bowl = 0.0
    last_angle = None
    circle_motion = 0.0
    servo_spinning = False
    servo_high = False
    servo_step_at = 0.0

    print(f"Table orchestra, Ode to Joy, {score.BPM} BPM, C major. One speaker.")
    print("Lean in. The Qwiic sensor adds the harmony, raises its volume, and only then moves the servo.")
    print(f"  far  <= {qwiic_floor:.0f}   silence")
    print(f"  near >= {qwiic_floor + QWIIC_SPAN:.0f}  {_bed_names(len(BED))}")
    print("Touch an object to add that line. Let go to fade it.")
    for pad, name in TOUCH:
        print(f"  pad {pad}  {name}")
    print("Circle a hand around the bowl. A still hand stays silent. It rings after you stop.")

    try:
        while True:
            now = time.monotonic()
            prox = float(qwiic.get_proximity())
            prox_smooth += (prox - prox_smooth) * 0.12
            count, level = bed_state(prox_smooth, qwiic_floor)
            orchestra.bed_target = level
            if count > 0:
                if not servo_spinning:
                    servo_spinning = True
                    servo_high = True
                    servo.angle = 180
                    servo_step_at = now
                    print("servo spin")
                elif now - servo_step_at >= SERVO_SWEEP_S:
                    servo_high = not servo_high
                    servo.angle = 180 if servo_high else 0
                    servo_step_at = now
            elif servo_spinning:
                servo_spinning = False
                servo.angle = None
                print("servo stop")
            if count != bed_count:
                for i, name in enumerate(BED):
                    orchestra.bed_on[part_index[name]] = i < count
                bed_count = count
                print(f"qwiic {prox_smooth:.0f}   {_bed_names(count)}")
                last_prox_print = prox_smooth
            elif abs(prox_smooth - last_prox_print) >= 15:
                last_prox_print = prox_smooth
                print(f"qwiic {prox_smooth:.0f}   {_bed_names(count)}")

            for pad, name in TOUCH:
                down = bool(mpr121[pad].value)
                if down and not held[pad]:
                    held[pad] = True
                    orchestra.touch_on[part_index[name]] = True
                    print(f"cue  {pad} {name}")
                elif not down and held[pad]:
                    held[pad] = False
                    orchestra.touch_on[part_index[name]] = False
                    print(f"cut  {pad} {name}")

            diodes = read_diodes(apds.i2c_device)
            heard = None if diodes is None else bowl_from_diodes(*diodes, energy_floor)
            circling = False
            if heard is not None:
                closeness, weights, angle = heard
                if last_angle is not None:
                    circle_motion = circle_motion * 0.8 + _angle_delta(angle, last_angle)
                last_angle = angle
                circling = circle_motion > 0.05
            else:
                last_angle = None
                circle_motion = 0.0
            if circling:
                last_bowl = now
                orchestra.bowl_target = max(closeness, 0.62)
                orchestra.bowl_targets = weights
                if not bowl_on:
                    bowl_on = True
                    print("bowl circle")
                color = BOWL_NAMES[1 + max(range(3), key=lambda k: weights[k + 1])]
                if color != bowl_color:
                    bowl_color = color
                    print(f"bowl {color}")
            elif bowl_on and now - last_bowl > BOWL_HOLD_S:
                bowl_on = False
                orchestra.bowl_target = 0.0
                print("bowl rings out")

            time.sleep(0.01)
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        servo.angle = None
        time.sleep(0.5)
        orchestra.close()


if __name__ == "__main__":
    main()
