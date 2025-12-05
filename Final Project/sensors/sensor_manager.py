# sensors/sensor_manager.py

from sensors.camera_reflection import CameraFeed
from sensors.tft_display import TFTDisplay
from sensors.touch_mpr121_selector import TouchElementSelector
# GestureSensor is intentionally not used (camera-only interaction)


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
        # 3. Gesture sensor (DISABLED)
        # -------------------------
        self.gesture = None
        print("[SensorManager] Gesture sensor disabled (camera-only control).")

        # -------------------------
        # 4. Camera
        # -------------------------
        try:
            self.camera = CameraFeed()
            print("[SensorManager] Camera feed ready (or disabled).")
        except Exception as e:
            print(f"[SensorManager] Failed to init CameraFeed: {e}")
            self.camera = None

        # Runtime state
        self.profile_selected = False      # whether 3 elements have been locked in
        self.user_profile = None           # e.g. ["Fire", "Water", "Light"]
        self.current_element = "None"      # single element fallback before profile is locked

    # ----------------------------------------------------------------
    #                      MAIN UPDATE LOOP
    # ----------------------------------------------------------------
    def update(self):
        """
        Return a dict with:
            profile: ["Water","Fire","Wind"] once the 3-element profile is locked
            element: current single element name (fallback before profile selection)
            gesture: always None (gesture sensor disabled)
            frame: camera frame (or None)
        """

        # 1. Touch element selection (choose 3)
        if not self.profile_selected and self.touch_selector is not None:
            profile = self.touch_selector.update()

            if profile is not None:
                # three elements chosen
                self.profile_selected = True
                self.user_profile = profile
                print(f"[SensorManager] Final profile locked: {profile}")

                # show final on OLED
                if self.tft:
                    self.tft.show_element_list(profile)

        # 2. Gesture sensor (disabled → always None)
        gesture = None

        # 3. Camera frame
        frame = None
        if self.camera is not None:
            try:
                frame = self.camera.get_frame()
            except Exception as e:
                print(f"[SensorManager] Error reading camera: {e}")
                frame = None

        # 4. Fallback element (only used before 3-pick is finished)
        if not self.profile_selected:
            if self.touch_selector and len(self.touch_selector.selected) > 0:
                self.current_element = self.touch_selector.selected[-1]
            else:
                self.current_element = "None"

        # RETURN SENSOR DATA
        return {
            "profile": self.user_profile if self.profile_selected else None,
            "element": self.current_element,
            "gesture": gesture,   # always None now
            "frame": frame,
        }

    # ----------------------------------------------------------------
    #                  RESET PROFILE (for 'R' key)
    # ----------------------------------------------------------------
    def reset_profile(self):
        """
        Clear current 3-element profile so the user can re-select elements.

        This is called from main.py when the user presses 'R'.
        """
        # Reset internal state
        self.profile_selected = False
        self.user_profile = None
        self.current_element = "None"

        # Reset touch selector (allow choosing 3 new elements)
        if self.touch_selector is not None:
            self.touch_selector.selected = []
            self.touch_selector.selection_done = False

        # Update OLED display if available
        if self.tft is not None:
            self.tft.show_element("Ready")

        print("[SensorManager] Profile reset. User can select new elements.")
