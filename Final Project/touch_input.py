import board
import busio
import adafruit_mpr121

class TouchInput:
    def __init__(self):
        i2c = busio.I2C(board.SCL, board.SDA)
        self.mpr121 = adafruit_mpr121.MPR121(i2c)
        
        # NEW: Track previous state
        self.previous_state = [self.mpr121[i].value for i in range(12)]

    def get_touch(self):
        """Return index of touched pad (or None)."""
        for i in range(12):
            if self.mpr121[i].value:
                return i
        return None

    # NEW: Add this entire method
    def get_lifted(self):
        """Return pad index when object is LIFTED."""
        for i in range(12):
            current = self.mpr121[i].value
            was_touched = self.previous_state[i]
            self.previous_state[i] = current
            
            if was_touched and not current:
                return i
        return None