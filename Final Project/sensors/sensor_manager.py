# sensors/sensor_manager.py

from sensors.touch_mpr121 import TouchSensor
from sensors.gesture_apds9960 import GestureSensor
from sensors.camera_reflection import CameraFeed
from sensors.tft_display import TFTDisplay

class SensorManager:
    def __init__(self):
        print("[SensorManager] Initializing sensors...")
        try:
            self.touch = TouchSensor()
            print("[SensorManager] MPR121 touch ready.")
        except Exception as e:
            print(f"[SensorManager] Failed to init TouchSensor: {e}")
            self.touch = None

        try:
            self.gesture = GestureSensor()
            print("[SensorManager] Gesture sensor ready (or in dummy mode).")
        except Exception as e:
            print(f"[SensorManager] Failed to init GestureSensor: {e}")
            self.gesture = None

        try:
            self.camera = CameraFeed()
            print("[SensorManager] Camera feed ready (or disabled).")
        except Exception as e:
            print(f"[SensorManager] Failed to init CameraFeed: {e}")
            self.camera = None

        try:
            self.tft = TFTDisplay()
            print("[SensorManager] OLED/TFT ready (or dummy).")
        except Exception as e:
            print(f"[SensorManager] Failed to init TFTDisplay: {e}")
            self.tft = None

        self.current_element = "None"

    def update(self):
        # 1. Touch (element selection)
        element_read = None
        if self.touch is not None:
            try:
                element_read = self.touch.read_element()
            except Exception as e:
                print(f"[SensorManager] Error reading touch: {e}")
                element_read = None

        if element_read:
            self.current_element = element_read
            if self.tft is not None:
                try:
                    self.tft.show_element(self.current_element)
                except Exception as e:
                    print(f"[SensorManager] Error updating TFT/OLED: {e}")

        # 2. Gesture
        gesture = None
        if self.gesture is not None:
            try:
                # 注意：read_gesture 必须是「非阻塞」的实现
                gesture = self.gesture.read_gesture()
            except Exception as e:
                print(f"[SensorManager] Error reading gesture: {e}")
                gesture = None

        # 3. Camera frame
        frame = None
        if self.camera is not None:
            try:
                frame = self.camera.get_frame()
            except Exception as e:
                print(f"[SensorManager] Error reading camera frame: {e}")
                frame = None

        return {
            "element": self.current_element,
            "gesture": gesture,
            "frame": frame,
        }
