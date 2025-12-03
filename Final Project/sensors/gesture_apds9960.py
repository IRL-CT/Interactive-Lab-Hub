import board
import busio
from adafruit_apds9960.apds9960 import APDS9960
import time


class GestureSensor:
    """
    Wrapper around APDS9960 gesture engine.

    Mapping:
    - Up    → "expand"  (grow energy field)
    - Down  → "shrink"  (shrink energy field)
    - Left  → "cooler"  (shift colors to cooler tones)
    - Right → "warmer"  (shift colors to warmer tones)
    """

    def __init__(self):
        self.sensor = None
        self.last_gesture_time = 0.0
        self.cooldown = 0.4  # seconds between two accepted gestures

        try:
            i2c = busio.I2C(board.SCL, board.SDA)
            self.sensor = APDS9960(i2c)

            # Proximity must be enabled for gesture engine
            self.sensor.enable_proximity = True

            # Enable gesture mode
            self.sensor.enable_gesture = True

            # Tunable parameters for better recognition
            # Gain: higher → more sensitive
            self.sensor.gesture_gain = 2  # 0=1x, 1=2x, 2=4x, 3=8x

            # These thresholds are somewhat empirical.
            # If gestures are not detected, try lowering them a bit.
            self.sensor.gesture_threshold_out = 10
            self.sensor.gesture_threshold_in = 30

            # Optionally, you can also tweak gesture_dimensions
            # and gesture_fifo_threshold here if needed.

            print("[Gesture] APDS9960 gesture engine initialized.")

        except Exception as e:
            print(f"[Gesture] Failed to initialize APDS9960: {e}")
            self.sensor = None

    def read_gesture(self):
        """
        Poll the sensor and convert APDS9960 gesture codes into
        high-level actions used by the animation engine.

        Returns:
            "expand" / "shrink" / "cooler" / "warmer" / None
        """
        if not self.sensor:
            return None

        now = time.monotonic()
        # Simple cooldown so one hand wave does not trigger many times
        if now - self.last_gesture_time < self.cooldown:
            # Still in cooldown → do not accept new gestures
            return None

        # Sometimes reading once can miss a short gesture.
        # We sample a few times very quickly.
        decoded_action = None
        for _ in range(3):
            g = self.sensor.gesture()  # Raw codes: 0x01 / 0x02 / 0x03 / 0x04
            if g == 0x01:
                decoded_action = "expand"   # Up
                direction = "UP"
                break
            elif g == 0x02:
                decoded_action = "shrink"   # Down
                direction = "DOWN"
                break
            elif g == 0x03:
                decoded_action = "cooler"   # Left
                direction = "LEFT"
                break
            elif g == 0x04:
                decoded_action = "warmer"   # Right
                direction = "RIGHT"
                break
            else:
                # No valid gesture in this quick sample
                continue

        if decoded_action is not None:
            self.last_gesture_time = now
            print(f"[Gesture] Detected {direction} to {decoded_action}")
            return decoded_action

        return None
