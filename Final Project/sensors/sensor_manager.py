# sensors/sensor_manager.py

from sensors.gesture_apds9960 import GestureSensor
from sensors.camera_reflection import CameraFeed
from sensors.tft_display import TFTDisplay
from sensors.touch_mpr121_selector import TouchElementSelector  


class SensorManager:
    def __init__(self):
        print("[SensorManager] Initializing sensors...")

        # 1. OLED display
        try:
            self.tft = TFTDisplay()
            print("[SensorManager] OLED/TFT ready (or dummy).")
        except Exception as e:
            print(f"[SensorManager] Failed to init TFTDisplay: {e}")
            self.tft = None

        # 2. Touch selector (3 picks)
        try:
            self.touch_selector = TouchElementSelector(oled=self.tft)
            print("[SensorManager] MPR121 touch selector ready.")
        except Exception as e:
            print(f"[SensorManager] Failed to init TouchElementSelector: {e}")
            self.touch_selector = None

        # 3. Gesture + proximity sensor (APDS-9960)
        try:
            self.gesture = GestureSensor()
            print("[SensorManager] Gesture sensor ready.")
        except Exception as e:
            print(f"[SensorManager] Failed to init GestureSensor: {e}")
            self.gesture = None

        # 4. Camera
        try:
            self.camera = CameraFeed()
            print("[SensorManager] Camera feed ready (or disabled).")
        except Exception as e:
            print(f"[SensorManager] Failed to init CameraFeed: {e}")
            self.camera = None

        # runtime state
        self.profile_selected = False
        self.user_profile = None
        self.current_element = "None"

        # smoothed proximity (0~1)
        self.proximity_level = 0.0

    # ----------------------------------------------------------------
    # MAIN UPDATE LOOP
    # ----------------------------------------------------------------
    def update(self):
        """
        Return a dict with:
            profile: ["Water","Fire","Wind"] once selected (3 elements)
            element: current simple element (fallback before profile)
            gesture: symbolic gesture string
            proximity: 0.0 ~ 1.0 (hand distance)
            frame: camera frame (or None)
        """

        # 1. Touch element selection (choose 3)
        profile = None
        if not self.profile_selected and self.touch_selector is not None:
            profile = self.touch_selector.update()

            if profile is not None:
                self.profile_selected = True
                self.user_profile = profile
                print(f"[SensorManager] Final profile locked: {profile}")

                if self.tft:
                    self.tft.show_element_list(profile)

        # 2. Gesture + proximity
        gesture = None
        proximity = None
        if self.gesture is not None:
            try:
                gesture = self.gesture.read_gesture()
            except Exception as e:
                print(f"[SensorManager] Error reading gesture: {e}")
                gesture = None

            try:
                proximity = self.gesture.read_proximity()
            except Exception as e:
                print(f"[SensorManager] Error reading proximity: {e}")
                proximity = None

        # 3. Camera frame
        frame = None
        if self.camera is not None:
            try:
                frame = self.camera.get_frame()
            except Exception as e:
                print(f"[SensorManager] Error reading camera: {e}")
                frame = None

        # 4. Fallback element (before 3-pick is finished)
        if not self.profile_selected:
            if self.touch_selector and len(self.touch_selector.selected) > 0:
                self.current_element = self.touch_selector.selected[-1]
            else:
                self.current_element = "None"

        # smooth proximity for stability
        if proximity is not None:
            self.proximity_level = 0.8 * self.proximity_level + 0.2 * proximity

        # RETURN SENSOR DATA
        return {
            "profile": self.user_profile if self.profile_selected else None,
            "element": self.current_element,
            "gesture": gesture,
            "proximity": self.proximity_level,
            "frame": frame,
        }
