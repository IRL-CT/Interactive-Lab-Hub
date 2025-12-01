import board
import busio
import adafruit_mpr121

# Element mapping: electrode → element
ELEMENT_MAP = {
    0: "Fire",
    1: "Water",
    2: "Wind",
    3: "Earth",
    4: "Light",
    5: "Shadow"
}

class TouchSensor:
    def __init__(self):
        i2c = busio.I2C(board.SCL, board.SDA)
        self.mpr121 = adafruit_mpr121.MPR121(i2c)
        self.current_element = None

    def read_element(self):
        for i in range(6):  # only use 6 electrodes
            if self.mpr121[i].value:
                self.current_element = ELEMENT_MAP[i]
                return self.current_element
        return None
