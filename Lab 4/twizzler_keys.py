"""Play a note while each Twizzler is touched.

Pads 0 through 11 are a C major scale, from C4 up to G5. Hold a pad to
sustain its note. Touch several at once to stack them.
"""

import time
import board
import busio
import numpy as np
import sounddevice as sd
import adafruit_mpr121

SAMPLE_RATE = 44100
# C major, one note per pad. Enough range to pick out a short melody.
NOTES = (
    ("C4", 261.63),
    ("D4", 293.66),
    ("E4", 329.63),
    ("F4", 349.23),
    ("G4", 392.00),
    ("A4", 440.00),
    ("B4", 493.88),
    ("C5", 523.25),
    ("D5", 587.33),
    ("E5", 659.25),
    ("F5", 698.46),
    ("G5", 783.99),
)


class Keys:
    """Mix a sine for every pad that is currently held."""

    def __init__(self) -> None:
        self.want = [False] * 12
        self.gain = [0.0] * 12
        self.phase = [0.0] * 12
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
        mix = np.zeros(frames, dtype=np.float32)
        step = 1.0 / int(0.015 * SAMPLE_RATE)
        ramp = np.arange(1, frames + 1)
        for i, (_name, freq) in enumerate(NOTES):
            target = 1.0 if self.want[i] else 0.0
            start = self.gain[i]
            if target > start:
                gains = np.minimum(start + step * ramp, 1.0)
            else:
                gains = np.maximum(start - step * ramp, 0.0)
            self.gain[i] = float(gains[-1])
            if self.gain[i] <= 0.0 and target == 0.0:
                self.phase[i] = 0.0
                continue
            phase = self.phase[i]
            mix += gains * np.sin(2 * np.pi * (phase + freq * ramp / SAMPLE_RATE))
            self.phase[i] = (phase + freq * frames / SAMPLE_RATE) % 1.0
        outdata[:, 0] = np.clip(mix * 0.25, -1.0, 1.0)

    def close(self) -> None:
        self.stream.stop()
        self.stream.close()


def main() -> None:
    i2c = busio.I2C(board.SCL, board.SDA)
    mpr121 = adafruit_mpr121.MPR121(i2c)
    keys = Keys()
    held = [False] * 12

    print("Twizzler keys. Touch a pad to play. Ctrl+C to stop.")
    for i, (name, _freq) in enumerate(NOTES):
        print(f"  {i}: {name}")

    try:
        while True:
            for i in range(12):
                down = bool(mpr121[i].value)
                if down and not held[i]:
                    held[i] = True
                    keys.want[i] = True
                    print(f"Twizzler {i}: {NOTES[i][0]}")
                elif not down and held[i]:
                    held[i] = False
                    keys.want[i] = False
            time.sleep(0.01)
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        keys.close()


if __name__ == "__main__":
    main()
