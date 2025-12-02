
import time
import board
import busio
import adafruit_mpr121


class TouchElementSelector:
    def __init__(self, oled=None):
        i2c = board.I2C()
        self.mpr121 = adafruit_mpr121.MPR121(i2c)
        self.oled = oled

        self.element_map = {
            0: "Fire",
            1: "Water",
            2: "Wind",
            3: "Earth",
            4: "Light",
            5: "Shadow",
        }

        self.selected = []
        self.selection_done = False

        print("[Touch] Element selector initialized.")

    def update(self):
        """Read touch and return final 3-element profile once."""

        if self.selection_done:
            return None

        for pad in range(6):
            if self.mpr121[pad].value:
                elem = self.element_map[pad]

                if elem not in self.selected:
                    self.selected.append(elem)
                    print(f"[Touch] Selected: {elem}")

                    # update OLED
                    if self.oled:
                        self.oled.show_element_list(self.selected)

                time.sleep(0.4)

                if len(self.selected) == 3:
                    self.selection_done = True
                    print(f"[Touch] Final user profile selected {self.selected}")
                    return self.selected

        return None
