from sensors.touch_mpr121 import TouchSensor
from sensors.gesture_apds9960 import GestureSensor
from sensors.camera_reflection import CameraFeed
from sensors.tft_display import TFTDisplay

class SensorManager:
    def __init__(self):
        self.touch = TouchSensor()
        self.gesture = GestureSensor()
        self.camera = CameraFeed()
        self.tft = TFTDisplay()
        self.current_element = "None"

    def update(self):
        # 1. Touch (element selection)
        elem = self.touch.read_element()
        if elem:
            self.current_element = elem
            self.tft.show_element(elem)

        # 2. Gesture
        gesture = self.gesture.read_gesture()

        # 3. Camera frame
        frame = self.camera.get_frame()

        return {
            "element": self.current_element,
            "gesture": gesture,
            "frame": frame
        }
