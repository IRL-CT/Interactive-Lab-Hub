"""Seven Twizzlers, the mountain king's hall.

Grieg's march loops at 126 BPM in B minor. The clock never stops, so a
section you cue in late still lands on the beat. Same pads as the
Ode to Joy orchestra.

  0 violin    the tune
  1 viola     inner voice
  2 cello     the bass
  3 flute     the tune, an octave up
  4 horn      the open fifth
  5 timpani   the march
  6 oboe      a countermelody
"""

import time
import board
import busio
import numpy as np
import sounddevice as sd
import adafruit_mpr121

SAMPLE_RATE = 44100
BPM = 126
# A sixteenth is the grid, so the march can be short and pointed.
# 126 BPM keeps that sixteenth an integer number of samples.
STEP = SAMPLE_RATE * 15 // BPM
PHRASE_STEPS = 128  # 8 bars of 4/4
PHRASE = STEP * PHRASE_STEPS
RELEASE = int(0.03 * SAMPLE_RATE)

FS2, B2 = 92.50, 123.47
CS3, D3 = 138.59, 146.83
FS3, A3, AS3, B3 = 185.00, 220.00, 233.08, 246.94
C4, CS4, D4, E4 = 261.63, 277.18, 293.66, 329.63
F4, FS4, GS4, A4 = 349.23, 369.99, 415.30, 440.00
AS4, B4, C5 = 466.16, 493.88, 523.25
CS5, D5 = 554.37, 587.33

PARTS = ("violin", "viola", "cello", "flute", "horn", "timpani", "oboe")


def _score(*notes: tuple[float, int]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Expand (frequency, sixteenths) into parallel freq, age, and duration arrays."""
    freq = np.zeros(PHRASE_STEPS, dtype=np.float64)
    age = np.zeros(PHRASE_STEPS, dtype=np.int32)
    dur = np.zeros(PHRASE_STEPS, dtype=np.int32)
    i = 0
    for f, n in notes:
        if n < 1 or i + n > PHRASE_STEPS:
            raise ValueError(f"score ran long at sixteenth {i}")
        freq[i : i + n] = f
        dur[i : i + n] = n
        age[i : i + n] = np.arange(n)
        i += n
    if i != PHRASE_STEPS:
        raise ValueError(f"score is {i} sixteenths, need {PHRASE_STEPS}")
    return freq, age, dur


def _stacc(*notes: tuple[float, int]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """(frequency, eighths). The last quarter of each note is silence."""
    expanded: list[tuple[float, int]] = []
    for f, eighths in notes:
        steps = eighths * 2
        if f <= 0.0 or steps < 2:
            expanded.append((0.0, steps))
            continue
        gap = max(1, steps // 4)
        expanded.append((f, steps - gap))
        expanded.append((0.0, gap))
    return _score(*expanded)


def _held(*notes: tuple[float, int]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """(frequency, eighths), sounded for the whole value."""
    return _score(*((f, n * 2) for f, n in notes))


# First statement in B minor, then Grieg's answer a fifth higher.
# 0 is a rest. Durations are in eighth notes.
VIOLIN_F, VIOLIN_AGE, VIOLIN_DUR = _stacc(
    (B3, 1), (CS4, 1), (D4, 1), (E4, 1), (FS4, 1), (D4, 1), (FS4, 2),
    (F4, 1), (CS4, 1), (F4, 2), (E4, 1), (C4, 1), (E4, 2),
    (B3, 1), (CS4, 1), (D4, 1), (E4, 1), (FS4, 1), (D4, 1), (FS4, 1), (B4, 1),
    (A3, 1), (FS3, 1), (D3, 1), (FS3, 1), (A3, 2), (0.0, 2),
    (FS4, 1), (GS4, 1), (AS4, 1), (B4, 1), (CS5, 1), (AS4, 1), (CS5, 2),
    (D5, 1), (AS4, 1), (D5, 2), (CS5, 1), (AS4, 1), (CS5, 2),
    (FS4, 1), (GS4, 1), (AS4, 1), (B4, 1), (CS5, 1), (AS4, 1), (CS5, 1), (B4, 1),
    (CS5, 2), (AS4, 2), (GS4, 2), (FS4, 2),
)
VIOLA_F, VIOLA_AGE, VIOLA_DUR = _held(
    (D4, 7), (0.0, 1),
    (CS4, 4), (C4, 4),
    (D4, 4), (FS4, 4),
    (FS3, 4), (A3, 4),
    (AS3, 7), (0.0, 1),
    (AS3, 8),
    (AS3, 4), (CS4, 4),
    (AS3, 4), (FS3, 4),
)
CELLO_F, CELLO_AGE, CELLO_DUR = _held(
    (B2, 8),
    (B2, 4), (FS2, 4),
    (B2, 8),
    (D3, 4), (FS2, 4),
    (FS2, 8),
    (FS2, 8),
    (FS2, 4), (CS3, 4),
    (CS3, 4), (FS2, 4),
)
FLUTE_F = np.where(VIOLIN_F > 0.0, VIOLIN_F * 2.0, 0.0)
FLUTE_AGE, FLUTE_DUR = VIOLIN_AGE, VIOLIN_DUR
HORN_F, HORN_AGE, HORN_DUR = _held(
    (B3, 8),
    (B3, 4), (FS3, 4),
    (B3, 8),
    (D4, 4), (FS3, 4),
    (FS3, 8),
    (FS3, 8),
    (FS3, 4), (CS4, 4),
    (CS4, 4), (FS3, 4),
)
TIMPANI_F, TIMPANI_AGE, TIMPANI_DUR = _held(
    (B2, 2), (0.0, 2), (B2, 2), (0.0, 2),
    (B2, 2), (0.0, 2), (FS2, 2), (0.0, 2),
    (B2, 2), (0.0, 2), (B2, 2), (0.0, 2),
    (B2, 2), (0.0, 2), (FS2, 2), (0.0, 2),
    (FS2, 2), (0.0, 2), (FS2, 2), (0.0, 2),
    (FS2, 2), (0.0, 2), (FS2, 2), (0.0, 2),
    (FS2, 2), (0.0, 2), (CS3, 2), (0.0, 2),
    (FS2, 2), (0.0, 2), (FS2, 2), (0.0, 2),
)
OBOE_F, OBOE_AGE, OBOE_DUR = _stacc(
    (D5, 3), (0.0, 1), (CS5, 3), (0.0, 1),
    (C5, 3), (0.0, 1), (B4, 3), (0.0, 1),
    (D5, 3), (0.0, 1), (B4, 3), (0.0, 1),
    (C5, 2), (A4, 2), (FS4, 3), (0.0, 1),
    (AS4, 3), (0.0, 1), (CS5, 3), (0.0, 1),
    (AS4, 7), (0.0, 1),
    (CS5, 3), (0.0, 1), (FS4, 3), (0.0, 1),
    (AS4, 3), (0.0, 1), (FS4, 3), (0.0, 1),
)


def _tone(w: np.ndarray, amps: tuple[float, ...]) -> np.ndarray:
    weights = np.asarray(amps, dtype=np.float64)
    weights /= weights.sum()
    k = np.arange(1, weights.size + 1)
    return np.sin(np.asarray(w)[:, None] * k) @ weights


def _shaped(t: np.ndarray, remain: np.ndarray, attack: float, decay: float) -> np.ndarray:
    env = (1.0 - np.exp(-t * attack)) * np.exp(-t * decay)
    return env * np.clip(remain / RELEASE, 0.0, 1.0)


def _violin(t, f, remain, noise):
    vib = 0.75 * np.sin(2 * np.pi * 5.6 * t)
    w = 2 * np.pi * f * t + vib
    env = _shaped(t, remain, attack=24.0, decay=0.7) * (f > 0.0)
    bow = noise * np.exp(-t * 45.0) * 0.18
    return env * (_tone(w, (1.0, 0.55, 0.32, 0.16, 0.08)) + bow)


def _viola(t, f, remain, _noise):
    vib = 0.55 * np.sin(2 * np.pi * 4.8 * t)
    w = 2 * np.pi * f * t + vib
    env = _shaped(t, remain, attack=16.0, decay=0.55) * (f > 0.0)
    return env * _tone(w, (1.0, 0.62, 0.22, 0.08))


def _cello(t, f, remain, _noise):
    vib = 0.45 * np.sin(2 * np.pi * 4.2 * t)
    w = 2 * np.pi * f * t + vib
    env = _shaped(t, remain, attack=8.0, decay=0.35) * (f > 0.0)
    return env * _tone(w, (1.0, 0.7, 0.28, 0.1))


def _flute(t, f, remain, noise):
    vib = 0.35 * np.sin(2 * np.pi * 5.0 * t) * np.clip(t / 0.35, 0.0, 1.0)
    w = 2 * np.pi * f * t + vib
    env = _shaped(t, remain, attack=9.0, decay=0.25) * (f > 0.0)
    breath = noise * 0.14
    return env * (_tone(w, (1.0, 0.12, 0.03)) + breath)


def _horn(t, f, remain, noise):
    w = 2 * np.pi * f * t
    env = _shaped(t, remain, attack=3.2, decay=0.2) * (f > 0.0)
    blat = np.exp(-t * 12.0)
    tone = _tone(w, (1.0, 0.72, 0.38, 0.14))
    return env * (tone + blat * 0.22 * np.sin(5.0 * w))


def _oboe(t, f, remain, noise):
    # Odd harmonics and a short reed chirp. That is the nasal oboe color.
    vib = 0.4 * np.sin(2 * np.pi * 5.2 * t) * np.clip(t / 0.25, 0.0, 1.0)
    w = 2 * np.pi * f * t + vib
    env = _shaped(t, remain, attack=30.0, decay=0.45) * (f > 0.0)
    reed = noise * np.exp(-t * 60.0) * 0.12
    return env * (_tone(w, (1.0, 0.1, 0.72, 0.06, 0.42, 0.04, 0.16)) + reed)


def _timpani(t, f, remain, noise):
    fall = (0.5 * f / 9.0) * (1.0 - np.exp(-9.0 * t))
    phase = 2 * np.pi * (f * t + fall)
    ring = np.exp(-t * 2.4) * np.clip(remain / RELEASE, 0.0, 1.0) * (f > 0.0)
    head = noise * np.exp(-t * 35.0)
    tone = np.sin(phase) + 0.22 * np.sin(2.0 * phase) * np.exp(-t * 6.0)
    return ring * (tone + 0.28 * head)


class Orchestra:
    """Shared clock. Each pad cues one section."""

    def __init__(self) -> None:
        self.want = [False] * len(PARTS)
        self.gain = [0.0] * len(PARTS)
        self.n = 0
        self.bar = 0
        self.stream = sd.OutputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="float32",
            blocksize=512,
            callback=self._callback,
        )
        self.stream.start()

    def _callback(self, outdata, frames, _time, status) -> None:
        if status:
            print(status)
        idx = (self.n + np.arange(frames)) % PHRASE
        self.n = (self.n + frames) % PHRASE
        self.bar = int(idx[0] // (STEP * 16))
        noise = np.random.uniform(-1.0, 1.0, frames)

        parts = (
            (_violin, VIOLIN_F, VIOLIN_AGE, VIOLIN_DUR, 0.34),
            (_viola, VIOLA_F, VIOLA_AGE, VIOLA_DUR, 0.28),
            (_cello, CELLO_F, CELLO_AGE, CELLO_DUR, 0.42),
            (_flute, FLUTE_F, FLUTE_AGE, FLUTE_DUR, 0.18),
            (_horn, HORN_F, HORN_AGE, HORN_DUR, 0.32),
            (_timpani, TIMPANI_F, TIMPANI_AGE, TIMPANI_DUR, 0.48),
            (_oboe, OBOE_F, OBOE_AGE, OBOE_DUR, 0.30),
        )
        into = idx % STEP
        mix = np.zeros(frames, dtype=np.float64)
        step_up = 1.0 / int(0.10 * SAMPLE_RATE)
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
            slot = idx // STEP
            t = (age[slot] * STEP + into) / SAMPLE_RATE
            remain = dur[slot] * STEP - age[slot] * STEP - into
            mix += gains * voice(t, freq[slot], remain, noise) * level
        outdata[:, 0] = np.clip(mix * 0.72, -1.0, 1.0).astype(np.float32)

    def close(self) -> None:
        self.stream.stop()
        self.stream.close()


def main() -> None:
    i2c = busio.I2C(board.SCL, board.SDA)
    mpr121 = adafruit_mpr121.MPR121(i2c)
    orchestra = Orchestra()
    held = [False] * len(PARTS)
    shown = -1

    print(f"Mountain king, {BPM} BPM, B minor. Hold a pad to cue a section.")
    for i, name in enumerate(PARTS):
        print(f"  {i}: {name}")

    try:
        while True:
            bar = orchestra.bar
            if bar != shown:
                shown = bar
                print(f"bar {bar + 1}")
            for i in range(len(PARTS)):
                down = bool(mpr121[i].value)
                if down and not held[i]:
                    held[i] = True
                    orchestra.want[i] = True
                    print(f"cue  {i} {PARTS[i]}")
                elif not down and held[i]:
                    held[i] = False
                    orchestra.want[i] = False
                    print(f"cut  {i} {PARTS[i]}")
            time.sleep(0.01)
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        orchestra.close()


if __name__ == "__main__":
    main()
