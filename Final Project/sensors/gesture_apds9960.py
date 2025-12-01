import board
import busio
from adafruit_apds9960.apds9960 import APDS9960

class GestureSensor:
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
