import board
import busio
from adafruit_apds9960.apds9960 import APDS9960
import time

class GestureSensor:
    def __init__(self):
        try:
            # Correct I2C init for Pi
            i2c = busio.I2C(board.SCL, board.SDA)
            self.sensor = APDS9960(i2c)

            # Must enable proximity for gesture engine
            self.sensor.enable_proximity = True

            # Enable gesture mode
            self.sensor.enable_gesture = True

            # Recommended settings for more reliable gesture recognition
            self.sensor.gesture_gain = 2  # 0=1x, 1=2x, 2=4x, 3=8x
            self.sensor.gesture_threshold_out = 10
            self.sensor.gesture_threshold_in = 30

            print("[Gesture] APDS9960 gesture engine initialized.")

        except Exception as e:
            print(f"[Gesture] Failed to initialize APDS9960: {e}")
            self.sensor = None


    def read_gesture(self):
        """Read & convert APDS9960 gesture data to normalized actions."""
        if not self.sensor:
            return None

        g = self.sensor.gesture()  # Raw 0x01 / 0x02 / 0x03 / 0x04

        if g == 0x01:
            return "expand"     # Up → Expand energy field
        elif g == 0x02:
            return "shrink"     # Down → Shrink energy field
        elif g == 0x03:
            return "cooler"     # Left → Cooler colors
        elif g == 0x04:
            return "warmer"     # Right → Warmer colors
        else:
            return None
