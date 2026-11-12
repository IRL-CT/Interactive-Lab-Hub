"""Ode to Joy, layered by where the hand sits from left to right.

Same orchestra and fixed 0.80 volume as proximity_orchestra.py.
This file does not use swipes. gesture() only reports a finished
direction, and it waits until the hand leaves, so it cannot follow
a hand resting over the sensor.

While a hand is close, the APDS-9960 fills a small buffer with four
photodiode counts: up, down, left, right. This script reads that
buffer in the main loop and turns the left/right pair into a position:

    0  the hand is on the left photodiode
    1  the hand is on the right photodiode

That position is a balance, not centimeters. The zones match the
sketch. Both ends are silent. Moving right through the middle adds
a layer and leaves the earlier ones playing:

    far left              no sound
    violin
    violin + oboe
    violin + oboe + timpani
    far right             no sound

Tune LEFT_SILENCE and RIGHT_SILENCE from the pos lines this prints.
If violin shows up when your hand is on the right, set SWAP_SIDES
to True.
"""

import time
from typing import Optional

import board
import numpy as np
import sounddevice as sd
from adafruit_apds9960.apds9960 import APDS9960

import proximity_orchestra as music

# Fixed master level. 0.80 is 80% of full scale.
MASTER_VOLUME = 0.80

# pos below LEFT_SILENCE or above RIGHT_SILENCE is the silent margin.
# The sketch leaves silence at both ends of the left-to-right axis.
LEFT_SILENCE = 0.22
RIGHT_SILENCE = 0.78
# Swap the two photodiodes if the board is mounted the other way around.
SWAP_SIDES = False
# Left + right below this means the sample is empty, not a hand.
HAND_MIN = 40
# Keep the current layers briefly when a FIFO read comes back empty,
# so a one-sample gap does not cut the sound.
HAND_HOLD_S = 0.25

# Sketch order. Timpani is the percussion. Earlier names stay on.
LAYERS = ("violin", "oboe", "timpani")

# APDS-9960 gesture FIFO. Same registers the Adafruit driver uses.
_GFLVL = 0xAE
_GSTATUS = 0xAF
_GFOV = 0x02
_GCONF4 = 0xAB
_GFIFO_CLR = 0x04
_GFIFO_U = 0xFC


def layers_for_position(pos: float) -> int:
    """How many layers are on for a left-to-right position in 0..1."""
    if pos < LEFT_SILENCE or pos > RIGHT_SILENCE:
        return 0
    if RIGHT_SILENCE <= LEFT_SILENCE:
        raise ValueError("RIGHT_SILENCE must be greater than LEFT_SILENCE")
    span = (pos - LEFT_SILENCE) / (RIGHT_SILENCE - LEFT_SILENCE)
    count = int(span * len(LAYERS)) + 1
    if count > len(LAYERS):
        return len(LAYERS)
    return count


def _layer_names(count: int) -> str:
    if count <= 0:
        return "no sound"
    return " + ".join(LAYERS[:count])


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


def read_left_right(device) -> Optional[tuple[float, float]]:
    """Newest left and right counts, or None when no hand sample is waiting.

    Drains the gesture FIFO. Does not call gesture(), which would block
    until the hand moved away and throw away these counts.
    """
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

    left_sum = 0
    right_sum = 0
    used = 0
    for i in range(count):
        left = buf[1 + i * 4 + 2]
        right = buf[1 + i * 4 + 3]
        if left == 255 and right == 255:
            continue
        if left + right < HAND_MIN:
            continue
        left_sum += left
        right_sum += right
        used += 1
    if used == 0:
        return None
    return left_sum / used, right_sum / used


def position_from_counts(left: float, right: float) -> Optional[float]:
    """0 on the left photodiode, 1 on the right. None if the hand is absent."""
    if SWAP_SIDES:
        left, right = right, left
    total = left + right
    if total < HAND_MIN:
        return None
    return right / total


class Orchestra:
    """Shared clock. The main loop decides which layers are on."""

    def __init__(self) -> None:
        self.want = [False] * len(music.PARTS)
        self.gain = [0.0] * len(music.PARTS)
        self.n = 0
        self.bar = 0
        self.stream = sd.OutputStream(
            samplerate=music.SAMPLE_RATE,
            channels=1,
            dtype="float32",
            blocksize=512,
            callback=self._callback,
        )
        self.stream.start()

    def set_layers(self, count: int) -> None:
        active = set(LAYERS[:count])
        for i, name in enumerate(music.PARTS):
            self.want[i] = name in active

    def _callback(self, outdata, frames, _time, status) -> None:
        if status:
            print(status)
        idx = (self.n + np.arange(frames)) % music.PHRASE
        self.n = (self.n + frames) % music.PHRASE
        self.bar = int(idx[0] // (music.EIGHTH * 8))
        noise = np.random.uniform(-1.0, 1.0, frames)

        parts = (
            (music._violin, music.VIOLIN_F, music.VIOLIN_AGE, music.VIOLIN_DUR, 0.34),
            (music._viola, music.VIOLA_F, music.VIOLA_AGE, music.VIOLA_DUR, 0.30),
            (music._cello, music.CELLO_F, music.CELLO_AGE, music.CELLO_DUR, 0.42),
            (music._flute, music.FLUTE_F, music.FLUTE_AGE, music.FLUTE_DUR, 0.26),
            (music._horn, music.HORN_F, music.HORN_AGE, music.HORN_DUR, 0.36),
            (music._timpani, music.TIMPANI_F, music.TIMPANI_AGE, music.TIMPANI_DUR, 0.50),
            (music._oboe, music.OBOE_F, music.OBOE_AGE, music.OBOE_DUR, 0.34),
        )
        into = idx % music.EIGHTH
        mix = np.zeros(frames, dtype=np.float64)
        step_up = 1.0 / int(0.10 * music.SAMPLE_RATE)
        ramp = np.arange(1, frames + 1)
        for i, (voice, freq, age, dur, level) in enumerate(parts):
            target = 1.0 if self.want[i] else 0.0
            start = self.gain[i]
            if target == 0.0 and start <= 0.0:
                continue
            if target > start:
                gains = np.minimum(start + step_up * ramp, 1.0)
            else:
                gains = np.maximum(start - step_up * ramp, 0.0)
            self.gain[i] = float(gains[-1])
            slot = idx // music.EIGHTH
            t = (age[slot] * music.EIGHTH + into) / music.SAMPLE_RATE
            remain = dur[slot] * music.EIGHTH - age[slot] * music.EIGHTH - into
            mix += gains * voice(t, freq[slot], remain, noise) * level

        outdata[:, 0] = np.clip(mix * MASTER_VOLUME, -1.0, 1.0).astype(np.float32)

    def close(self) -> None:
        self.stream.stop()
        self.stream.close()


def main() -> None:
    i2c = board.I2C()
    apds = APDS9960(i2c)
    # The FIFO only runs when both engines are on. 8x is the highest
    # gain the library exposes, so a hand a few centimeters up is seen.
    apds.enable_proximity = True
    apds.proximity_gain = 3
    apds.gesture_gain = 3
    apds.enable_gesture = True

    orchestra = Orchestra()
    count = 0
    smoothed = None  # type: Optional[float]
    last_hand = 0.0
    last_print = 0.0
    last_printed_pos = -1.0

    print(f"Left-right orchestra, {music.BPM} BPM, C major. Volume fixed at {MASTER_VOLUME:.2f}.")
    print("Hold your hand a few centimeters above the sensor and slide left to right.")
    print("pos 0 is left, pos 1 is right. Both ends are silent.")
    print(f"  below {LEFT_SILENCE:.2f}     no sound")
    print( "  then              violin, violin + oboe, violin + oboe + timpani")
    print(f"  above {RIGHT_SILENCE:.2f}     no sound")
    print("Edit LEFT_SILENCE and RIGHT_SILENCE to match the pos lines.")
    print(_layer_names(0))

    try:
        while True:
            sample = read_left_right(apds.i2c_device)
            now = time.monotonic()
            pos = None
            if sample is not None:
                pos = position_from_counts(*sample)
            if pos is None:
                if smoothed is not None and now - last_hand > HAND_HOLD_S:
                    smoothed = None
                    if count != 0:
                        count = 0
                        orchestra.set_layers(0)
                        print("no sound")
                        last_print = now
            else:
                last_hand = now
                if smoothed is None:
                    smoothed = pos
                else:
                    smoothed = smoothed + (pos - smoothed) * 0.35
                new_count = layers_for_position(smoothed)
                if new_count != count:
                    count = new_count
                    orchestra.set_layers(count)
                    print(f"pos {smoothed:.2f}  {_layer_names(count)}")
                    last_print = now
                    last_printed_pos = smoothed

            if (
                smoothed is not None
                and now - last_print >= 0.5
                and abs(smoothed - last_printed_pos) >= 0.05
            ):
                last_print = now
                last_printed_pos = smoothed
                print(f"pos {smoothed:.2f}  {_layer_names(count)}")

            time.sleep(0.01)
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        orchestra.close()


if __name__ == "__main__":
    main()
