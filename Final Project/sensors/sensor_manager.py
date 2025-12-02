# sensors/sensor_manager.py

from sensors.gesture_apds9960 import GestureSensor
from sensors.camera_reflection import CameraFeed
from sensors.tft_display import TFTDisplay
from sensors.touch_mpr121_selector import TouchElementSelector  

class SensorManager:
    def __init__(self):
        print("[SensorManager] Initializing sensors...")

        # -------------------------
        # 1. OLED display
        # -------------------------
        try:
            self.tft = TFTDisplay()
            print("[SensorManager] OLED/TFT ready (or dummy).")
        except Exception as e:
            print(f"[SensorManager] Failed to init TFTDisplay: {e}")
            self.tft = None

        # -------------------------
        # 2. Touch selector (3 picks)
        # -------------------------
        try:
            self.touch_selector = TouchElementSelector(oled=self.tft)
            print("[SensorManager] MPR121 touch selector ready.")
        except Exception as e:
            print(f"[SensorManager] Failed to init TouchElementSelector: {e}")
            self.touch_selector = None

        # -------------------------
        # 3. Gesture sensor
        # -------------------------
        try:
            self.gesture = GestureSensor()
            print("[SensorManager] Gesture sensor ready (or in dummy mode).")
        except Exception as e:
            print(f"[SensorManager] Failed to init GestureSensor: {e}")
            self.gesture = None

        # -------------------------
        # 4. Camera
        # -------------------------
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


    # ----------------------------------------------------------------
    #                      MAIN UPDATE LOOP
    # ----------------------------------------------------------------
    def update(self):
        """Return a dict with:
            profile: ["Water","Fire","Wind"] once
            element: current simple element (fallback)
            gesture: hand gesture
            frame: camera frame
        """

        # -----------------------------------------
        # 1. Touch element selection (choose 3)
        # -----------------------------------------
        profile = None
        if not self.profile_selected and self.touch_selector is not None:
            profile = self.touch_selector.update()

            if profile is not None:
                # three chosen
                self.profile_selected = True
                self.user_profile = profile
                print(f"[SensorManager] Final profile locked: {profile}")

                # show final on OLED
                if self.tft:
                    self.tft.show_element_list(profile)

        # -----------------------------------------
        # 2. Gesture sensor
        # -----------------------------------------
        gesture = None
        if self.gesture is not None:
            try:
                gesture = self.gesture.read_gesture()
            except Exception as e:
                print(f"[SensorManager] Error reading gesture: {e}")
                gesture = None

        # -----------------------------------------
        # 3. Camera frame
        # -----------------------------------------
        frame = None
        if self.camera is not None:
            try:
                frame = self.camera.get_frame()
            except Exception as e:
                print(f"[SensorManager] Error reading camera: {e}")
                frame = None

        # -----------------------------------------
        # 4. Fallback element (only used before 3-pick is finished)
        # -----------------------------------------
        if not self.profile_selected:
            # allow displaying last single element choice on OLED
            if self.touch_selector and len(self.touch_selector.selected) > 0:
                self.current_element = self.touch_selector.selected[-1]
            else:
                self.current_element = "None"

        # -----------------------------------------
        # RETURN SENSOR DATA
        # -----------------------------------------
        return {
            "profile": self.user_profile if self.profile_selected else None,  # ["Fire","Water","Light"]
            "element": self.current_element,
            "gesture": gesture,
            "frame": frame,
        }

