"""Six Twizzlers, one house beat.

The clock runs the whole time at 120 BPM in A minor. Touching a pad
unmutes that part, so the layers stay on the same bar even if you
bring one in late.

  0 kick     four on the floor
  1 hats     offbeats, open hat at the end of the bar
  2 clap     beats 2 and 4
  3 bass     A minor, one bar
  4 chord    A minor stab on the offbeats
  5 arp      A minor pentatonic, 16th notes
"""

import time
import board
import busio
import numpy as np
import sounddevice as sd
import adafruit_mpr121

SAMPLE_RATE = 44100
BPM = 120
BEAT = int(SAMPLE_RATE * 60 / BPM)  # 22050 samples, exactly one beat
BAR = BEAT * 4

# One bar of bass, in eighth notes. 0 is a rest.
BASS = np.array([110.00, 0.0, 130.81, 0.0, 110.00, 82.41, 98.00, 82.41])
# 16th-note arp, A minor pentatonic, repeated twice per bar.
ARP = np.array([440.00, 523.25, 659.25, 783.99, 659.25, 523.25, 440.00, 392.00])
# A minor stab: A3, C4, E4.
STAB = (220.00, 261.63, 329.63)

PARTS = ("kick", "hats", "clap", "bass", "chord", "arp")


def _kick(t):
    env = np.exp(-t * 12)
    phase = 2 * np.pi * (48 * t + (160 / 45) * (1 - np.exp(-45 * t)))
    click = np.exp(-t * 200) * np.sin(2 * np.pi * 800 * t)
    return env * np.sin(phase) + 0.2 * click


def _hats(t, eighth, noise):
    closed = (eighth == 1) | (eighth == 3) | (eighth == 5)
    opened = eighth == 7
    decay = np.where(opened, 12.0, 50.0)
    env = np.exp(-t * decay) * (closed | opened)
    tick = np.exp(-t * 90) * np.sin(2 * np.pi * 3500 * t)
    return env * noise * 0.55 + tick * 0.08 * (closed | opened)


def _clap(t, beat, noise):
    on = (beat == 1) | (beat == 3)
    tone = np.sin(2 * np.pi * 185 * t) * np.exp(-t * 18)
    burst = noise * np.exp(-t * 24)
    return on * (0.4 * tone + 0.75 * burst)


def _bass(t, eighth):
    freq = BASS[eighth]
    env = np.exp(-t * 6) * (freq > 0)
    w = 2 * np.pi * freq * t
    return env * (np.sin(w) + 0.4 * np.sin(2 * w) + 0.15 * np.sin(3 * w))


def _chord(t, eighth):
    on = (eighth == 1) | (eighth == 5)
    env = np.exp(-t * 9) * on
    tone = sum(np.sin(2 * np.pi * freq * t) for freq in STAB)
    return env * tone / 3


def _arp(t, step):
    freq = ARP[step % 8]
    env = np.exp(-t * 16)
    w = 2 * np.pi * freq * t
    return env * (np.sin(w) + 0.25 * np.sin(2 * w))


class Deck:
    """Shared clock. Each pad is a fader for one part."""

    def __init__(self) -> None:
        self.want = [False] * 6
        self.gain = [0.0] * 6
        self.n = 0
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
        n = np.arange(self.n, self.n + frames)
        self.n += frames
        pos = n % BAR
        t_beat = (pos % BEAT) / SAMPLE_RATE
        beat = (pos * 4) // BAR
        eighth = (pos * 8) // BAR
        step = (pos * 16) // BAR
        t_eighth = (pos - (eighth * BAR) // 8) / SAMPLE_RATE
        t_step = (pos - (step * BAR) // 16) / SAMPLE_RATE
        noise = np.random.uniform(-1.0, 1.0, frames).astype(np.float32)

        layers = (
            _kick(t_beat),
            _hats(t_eighth, eighth, noise),
            _clap(t_beat, beat, noise),
            _bass(t_eighth, eighth),
            _chord(t_eighth, eighth),
            _arp(t_step, step),
        )
        levels = (0.9, 0.35, 0.55, 0.45, 0.4, 0.28)

        mix = np.zeros(frames, dtype=np.float32)
        step_up = 1.0 / int(0.02 * SAMPLE_RATE)
        ramp = np.arange(1, frames + 1)
        for i, layer in enumerate(layers):
            target = 1.0 if self.want[i] else 0.0
            start = self.gain[i]
            if target == 0.0 and start <= 0.0:
                continue
            if target > start:
                gains = np.minimum(start + step_up * ramp, 1.0)
            else:
                gains = np.maximum(start - step_up * ramp, 0.0)
            self.gain[i] = float(gains[-1])
            mix += gains * layer * levels[i]
        outdata[:, 0] = np.clip(mix * 0.85, -1.0, 1.0)

    def close(self) -> None:
        self.stream.stop()
        self.stream.close()


def main() -> None:
    i2c = busio.I2C(board.SCL, board.SDA)
    mpr121 = adafruit_mpr121.MPR121(i2c)
    deck = Deck()
    held = [False] * 6

    print(f"Twizzler deck, {BPM} BPM, A minor. Hold a pad to bring a part in.")
    for i, name in enumerate(PARTS):
        print(f"  {i}: {name}")

    try:
        while True:
            for i in range(6):
                down = bool(mpr121[i].value)
                if down and not held[i]:
                    held[i] = True
                    deck.want[i] = True
                    print(f"in  {i} {PARTS[i]}")
                elif not down and held[i]:
                    held[i] = False
                    deck.want[i] = False
                    print(f"out {i} {PARTS[i]}")
            time.sleep(0.01)
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        deck.close()


if __name__ == "__main__":
    main()
