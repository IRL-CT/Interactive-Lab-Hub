# sensors/gesture_apds9960.py

import board
import busio
from adafruit_apds9960.apds9960 import APDS9960


class GestureSensor:
    """
    Wrapper for the APDS-9960 sensor.

    - read_gesture(): returns a symbolic gesture string:
        "expand" / "shrink" / "cooler" / "warmer" / None
    - read_proximity(): returns a normalized proximity value in [0, 1]
        where 0 is far away and 1 is very close to the sensor.
    """

    def __init__(self):
        i2c = busio.I2C(board.SCL, board.SDA)
        self.sensor = APDS9960(i2c)
        self.sensor.enable_proximity = True
        self.sensor.enable_gesture = True

    def read_gesture(self):
        gesture = self.sensor.gesture()

        if gesture == 0x01:     # Up
            return "expand"
        elif gesture == 0x02:   # Down
            return "shrink"
        elif gesture == 0x03:   # Left
            return "cooler"
        elif gesture == 0x04:   # Right
            return "warmer"
        else:
            return None

    def read_proximity(self):
        """
        Read proximity and map 0-255 to 0.0-1.0.
        If the sensor fails, return None.
        """
        try:
            raw = self.sensor.proximity  # 0~255
        except Exception:
            return None

        # Normalize and clamp
        value = max(0.0, min(1.0, raw / 255.0))
        return value
