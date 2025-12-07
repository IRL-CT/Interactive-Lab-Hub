# sensor_controller.py
"""
SensorController: integrates APDS9960 (color/gesture/proximity),
rotary encoder (Seesaw), and servo (ServoKit) to drive AudioEngine.

- Environment light -> selects genre (Chill/Energetic/Warm/Party)
- Gestures -> volume / next / previous
- Proximity hold -> pause/play
- Rotary encoder -> movement mode for decorative servo
"""

import time
import threading

import board
from adafruit_apds9960.apds9960 import APDS9960
from adafruit_apds9960 import colorutility
from adafruit_seesaw import seesaw, rotaryio
from adafruit_servokit import ServoKit

from audio_engine import AudioEngine

# ----- Environment / gesture parameters -----

LOW_LUX_THRESHOLD = 50       # < → Chill
HIGH_LUX_THRESHOLD = 150     # > → Party
WARM_COLOR_TEMP = 4000       # > → Warm, else Energetic

COLOR_UPDATE_INTERVAL = 0.5
ENVIRONMENT_STABILITY_TIME = 10.0

GESTURE_DEBOUNCE_TRACK = 0.2
GESTURE_DEBOUNCE_VOLUME = 0.1

PROXIMITY_THRESHOLD = 5
PROXIMITY_HOLD_TIME = 1.0

VOLUME_STEP = 0.15           # per gesture, 0.0–1.0 range

# Vibes/genres
VIBE_CHILL = "chill"
VIBE_ENERGETIC = "energetic"
VIBE_WARM = "warm"
VIBE_PARTY = "party"

# Movement modes
MODE_STOP = 0
MODE_SPIN_LEFT = 1
MODE_SPIN_RIGHT = 2


class SensorController:
    def __init__(self, engine: AudioEngine) -> None:
        self.engine = engine

        print("Initializing SensorController...")

        # I2C
        self.i2c = board.I2C()

        # APDS9960
        self.apds = APDS9960(self.i2c)
        self.apds.enable_color = True
        self.apds.enable_proximity = True
        self.apds.enable_gesture = True

        try:
            if hasattr(self.apds, "gesture_gain"):
                self.apds.gesture_gain = 2
        except Exception:
            pass

        print("[SENSOR] APDS9960 initialized")

        # Rotary encoder
        try:
            self.seesaw = seesaw.Seesaw(self.i2c, addr=0x36)
            seesaw_product = (self.seesaw.get_version() >> 16) & 0xFFFF
            if seesaw_product != 4991:
                print(f"[SENSOR WARNING] Seesaw product ID {seesaw_product}, expected 4991")

            self.encoder = rotaryio.IncrementalEncoder(self.seesaw)
            self.last_encoder_position = -self.encoder.position
            self.movement_mode = MODE_STOP
            print("[SENSOR] Rotary encoder initialized")
        except Exception as e:
            print(f"[SENSOR WARNING] Rotary encoder not found: {e}")
            self.encoder = None
            self.movement_mode = MODE_STOP

        # Servo
        try:
            self.servo_kit = ServoKit(channels=16)
            self.servo = self.servo_kit.servo[0]
            self.servo.set_pulse_width_range(500, 2500)
            self.servo.angle = 90
            print("[SENSOR] Servo initialized")
        except Exception as e:
            print(f"[SENSOR WARNING] Servo not found: {e}")
            self.servo = None

        # Gesture + environment state
        self.last_gesture_time_volume = 0.0
        self.last_gesture_time_track = 0.0
        self.last_color_check = 0.0

        self.current_vibe = None
        self.detected_vibe = None
        self.detected_vibe_start_time = 0.0

        # Proximity pause/play
        self.proximity_detected = False
        self.proximity_start_time = 0.0
        self.proximity_toggle_cooldown = 0.0

        # Servo thread
        self.servo_running = True
        self.servo_thread = threading.Thread(target=self._servo_control_loop, daemon=True)
        self.servo_thread.start()

        print("[SENSOR] SensorController ready.")

    # ---------- Vibe detection ----------

    def _detect_vibe_from_environment(self, lux: float, color_temp: float) -> str:
        if lux < LOW_LUX_THRESHOLD:
            return VIBE_CHILL
        elif lux > HIGH_LUX_THRESHOLD:
            return VIBE_PARTY
        elif color_temp > WARM_COLOR_TEMP:
            return VIBE_WARM
        else:
            return VIBE_ENERGETIC

    def _update_environment(self) -> None:
        current_time = time.time()
        if current_time - self.last_color_check < COLOR_UPDATE_INTERVAL:
            return
        self.last_color_check = current_time

        if not self.apds.color_data_ready:
            return

        r, g, b, c = self.apds.color_data
        lux = colorutility.calculate_lux(r, g, b)
        color_temp = colorutility.calculate_color_temperature(r, g, b)

        new_vibe = self._detect_vibe_from_environment(lux, color_temp)

        if not self.detected_vibe and new_vibe != self.current_vibe:
            self.detected_vibe = new_vibe
            self.detected_vibe_start_time = current_time
            print(
                f"[ENV] Detected {new_vibe} vibe ({lux:.1f} lux, {color_temp:.0f}K). "
                f"Waiting {ENVIRONMENT_STABILITY_TIME:.1f}s for stability..."
            )
            return

        # Same vibe; see if it's been stable long enough
        if self.detected_vibe and self.detected_vibe_start_time > 0:
            # If the environment changed again, cancel this candidate
            if new_vibe != self.detected_vibe:
                print(
                    f"[ENV] Detected vibe {self.detected_vibe} was unstable, "
                    f"resetting detection."
                )
                self.detected_vibe = None
                self.detected_vibe_start_time = 0.0
                return

            stability_duration = current_time - self.detected_vibe_start_time

            if stability_duration >= ENVIRONMENT_STABILITY_TIME:
                print(
                    f"[ENV] {self.detected_vibe} stable for {stability_duration:.1f}s. "
                    f"Switching genre and starting a new track."
                )

                self.engine.set_genre(self.detected_vibe)
                self.engine.play_random()

                self.current_vibe = self.detected_vibe
                self.detected_vibe = None
                self.detected_vibe_start_time = 0.0


    # ---------- Gestures ----------

    def _handle_gesture(self, gesture: int) -> None:
        now = time.time()

        # 0x01 = UP, 0x02 = DOWN, 0x03 = LEFT, 0x04 = RIGHT
        if gesture == 0x01:  # Up → Volume up
            if now - self.last_gesture_time_volume < GESTURE_DEBOUNCE_VOLUME:
                return
            self.last_gesture_time_volume = now
            self.engine.change_volume(+VOLUME_STEP)
            print(f"[GESTURE] Volume up → {self.engine.volume:.2f}")

        elif gesture == 0x02:  # Down → Volume down
            if now - self.last_gesture_time_volume < GESTURE_DEBOUNCE_VOLUME:
                return
            self.last_gesture_time_volume = now
            self.engine.change_volume(-VOLUME_STEP)
            print(f"[GESTURE] Volume down → {self.engine.volume:.2f}")

        elif gesture == 0x03:  # Left → Previous track
            if now - self.last_gesture_time_track < GESTURE_DEBOUNCE_TRACK:
                return
            self.last_gesture_time_track = now
            print("[GESTURE] Previous track")
            self.engine.previous_track()

        elif gesture == 0x04:  # Right → Next track
            if now - self.last_gesture_time_track < GESTURE_DEBOUNCE_TRACK:
                return
            self.last_gesture_time_track = now
            print("[GESTURE] Next track")
            self.engine.next_track()

    def _check_gestures(self) -> None:
        gesture = self.apds.gesture()
        if gesture != 0:
            self._handle_gesture(gesture)

    # ---------- Proximity pause/play ----------

    def _check_proximity_pause_play(self) -> None:
        now = time.time()
        if now - self.proximity_toggle_cooldown < 2.0:
            return

        proximity = self.apds.proximity

        if proximity > PROXIMITY_THRESHOLD:
            if not self.proximity_detected:
                self.proximity_detected = True
                self.proximity_start_time = now
            else:
                hold_duration = now - self.proximity_start_time
                if hold_duration >= PROXIMITY_HOLD_TIME:
                    # Toggle pause/play
                    status = self.engine.get_status()
                    if status["is_playing"]:
                        self.engine.pause()
                    else:
                        # resume or play
                        if status["is_paused"]:
                            self.engine.resume()
                        else:
                            self.engine.play_random()
                    self.proximity_toggle_cooldown = now
                    self.proximity_detected = False
        else:
            self.proximity_detected = False

    # ---------- Rotary encoder / servo ----------
    def _check_rotary_encoder(self) -> None:
        """Use rotary encoder to control servo direction + decade selection."""
        if self.encoder is None:
            return

        try:
            # Negate so clockwise feels "positive"
            position = self.encoder.position
        except OSError as e:
            # I2C sometimes glitches – don't crash the whole program
            print(f"[SENSOR WARNING] I2C error reading encoder: {e}")
            return

        if position == self.last_encoder_position:
            return

        delta = position - self.last_encoder_position
        self.last_encoder_position = position

        # Read current year from audio engine
        current_year = self.engine.get_year()

        if delta > 0:
            # Turned right: spin right + next decade
            self.movement_mode = MODE_SPIN_RIGHT
            new_year = min(2020, current_year + 10)
        else:
            # Turned left: spin left + previous decade
            self.movement_mode = MODE_SPIN_LEFT
            new_year = max(1950, current_year - 10)

        mode_names = ["STOP", "SPIN LEFT", "SPIN RIGHT"]
        print(f"[SERVO] Movement mode: {mode_names[self.movement_mode]}")

        if new_year != current_year:
            self.engine.set_year(new_year)
            self.engine.play_random()
            print(f"[ENCODER] Year changed from {current_year} → {new_year}")

    def _servo_control_loop(self) -> None:
        if self.servo is None:
            return

        angle = 90
        while self.servo_running:
            if self.movement_mode == MODE_STOP:
                # Gently return to center
                if abs(angle - 90) > 2:
                    if angle > 90:
                        angle -= 2
                    else:
                        angle += 2
                    self.servo.angle = angle
                else:
                    self.servo.angle = 90
                    time.sleep(0.1)
            elif self.movement_mode == MODE_SPIN_LEFT:
                angle -= 5
                if angle < 0:
                    angle = 180
                self.servo.angle = angle
                time.sleep(0.05)
            elif self.movement_mode == MODE_SPIN_RIGHT:
                angle += 5
                if angle > 180:
                    angle = 0
                self.servo.angle = angle
                time.sleep(0.05)
            else:
                time.sleep(0.1)

    # ---------- Track progress ----------

    def _check_music_finished(self) -> None:
        # If a track finished, advance to next within current playlist
        status = self.engine.get_status()
        if status["is_playing"] and not self.engine.is_track_playing():
            self.engine.next_track()

    # ---------- Main loop ----------

    def run_forever(self) -> None:
        try:
            # Initial environment-based genre + start playback
            print("[SENSOR] Detecting initial environment for vibe...")
            while not self.apds.color_data_ready:
                time.sleep(0.1)
            r, g, b, c = self.apds.color_data
            lux = colorutility.calculate_lux(r, g, b)
            color_temp = colorutility.calculate_color_temperature(r, g, b)
            initial_vibe = self._detect_vibe_from_environment(lux, color_temp)
            print(
                f"[SENSOR] Initial environment: {initial_vibe} "
                f"({lux:.1f} lux, {color_temp:.0f}K)"
            )
            self.engine.set_genre(initial_vibe)
            self.current_vibe = initial_vibe
            self.engine.play_random()

            while True:
                # Poll gestures fast
                for _ in range(5):
                    self._check_gestures()
                    time.sleep(0.001)

                self._update_environment()
                self._check_proximity_pause_play()
                self._check_rotary_encoder()
                self._check_music_finished()

                time.sleep(0.005)

        except KeyboardInterrupt:
            print("\n[SENSOR] KeyboardInterrupt, shutting down...")
        finally:
            self.servo_running = False
            if self.servo is not None:
                self.servo.angle = 90
            self.engine.stop()
            print("[SENSOR] Shutdown complete.")
