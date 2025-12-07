#!/usr/bin/env python3
"""
Final Project: Interactive Music Box
Features:
1. Environment-Based Music Selection: Color/brightness sensor selects music based on ambient light
2. Gesture Music Control: Hand gestures control playback (swipe to skip, up/down for volume, hold to pause/play)
3. Rotating Movement Modes: Rotary knob controls decorative figure movement (stop, spin left, spin right)
"""

import time
import board
import subprocess
import threading
from adafruit_apds9960.apds9960 import APDS9960
from adafruit_apds9960 import colorutility
from adafruit_seesaw import seesaw, rotaryio, digitalio
from adafruit_servokit import ServoKit
import pygame
import os
from pathlib import Path

# Configuration
MUSIC_DIR = Path(__file__).parent / "music"
LOW_LUX_THRESHOLD = 50   # Lux threshold for low brightness (Chill)
HIGH_LUX_THRESHOLD = 150  # Lux threshold for high brightness (Energetic/Party)
WARM_COLOR_TEMP = 4000    # Color temperature threshold for warm colors (Kelvin)
COLOR_UPDATE_INTERVAL = 0.5  # Seconds between environment checks (frequent for stability tracking)
ENVIRONMENT_STABILITY_TIME = 10.0  # Seconds environment must remain stable before switching (prevents switching from brief flashes)
GESTURE_DEBOUNCE_TRACK = 0.2  # Seconds to ignore track change gestures after one is detected
GESTURE_DEBOUNCE_VOLUME = 0.1  # Seconds to ignore volume gestures (shorter for responsiveness)
PROXIMITY_THRESHOLD = 5  # Proximity value to detect hand presence
PROXIMITY_HOLD_TIME = 1.0  # Seconds to hold hand still to pause/play
VOLUME_STEP = 15  # Volume change per gesture (increased for faster adjustment)
MIN_VOLUME = 0
MAX_VOLUME = 100

# Vibe playlists
VIBE_CHILL = "Chill"
VIBE_ENERGETIC = "Energetic"
VIBE_WARM = "Warm"
VIBE_PARTY = "Party"

# Movement modes
MODE_STOP = 0
MODE_SPIN_LEFT = 1
MODE_SPIN_RIGHT = 2


class MusicBox:
    def __init__(self):
        """Initialize the Interactive Music Box system."""
        print("Initializing Interactive Music Box...")
        
        # Initialize I2C and sensors
        self.i2c = board.I2C()
        
        # Initialize APDS9960 (color/brightness and gesture sensor)
        self.apds = APDS9960(self.i2c)
        self.apds.enable_color = True
        self.apds.enable_proximity = True
        self.apds.enable_gesture = True
        
        # Configure gesture sensor for better sensitivity (if supported)
        try:
            # Try to set gesture gain for better sensitivity
            if hasattr(self.apds, 'gesture_gain'):
                self.apds.gesture_gain = 2  # 0=1x, 1=2x, 2=4x, 3=8x (higher = more sensitive)
        except Exception:
            pass  # Attribute not available, use defaults
        
        print("[OK] Color and gesture sensor initialized")
        
        # Initialize rotary encoder (Seesaw)
        try:
            self.seesaw = seesaw.Seesaw(self.i2c, addr=0x36)
            # Verify it's the correct product (optional check)
            seesaw_product = (self.seesaw.get_version() >> 16) & 0xFFFF
            if seesaw_product != 4991:
                print(f"[WARNING] Seesaw product ID {seesaw_product}, expected 4991")
            
            self.encoder = rotaryio.IncrementalEncoder(self.seesaw)
            self.last_encoder_position = -self.encoder.position
            self.movement_mode = MODE_STOP
            print("[OK] Rotary encoder initialized (Seesaw)")
        except Exception as e:
            print(f"[WARNING] Rotary encoder not found: {e}")
            print("         Check I2C connections and ensure Seesaw is at address 0x36")
            self.encoder = None
            self.movement_mode = MODE_STOP
        
        # Initialize servo for decorative figure
        try:
            self.servo_kit = ServoKit(channels=16)
            self.servo = self.servo_kit.servo[0]  # Use channel 0
            self.servo.set_pulse_width_range(500, 2500)
            self.servo.angle = 90  # Center position
            print("[OK] Servo motor initialized")
        except Exception as e:
            print(f"[WARNING] Servo not found: {e}")
            self.servo = None
        
        # Initialize pygame mixer for audio playback
        # Try different audio backends for Raspberry Pi compatibility
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            print("[OK] Audio system initialized")
        except Exception as e:
            print(f"[WARNING] Audio initialization issue: {e}")
            print("         Trying alternative audio settings...")
            try:
                pygame.mixer.init()
                print("[OK] Audio system initialized (fallback mode)")
            except Exception as e2:
                print(f"[ERROR] Failed to initialize audio: {e2}")
                print("         Audio playback may not work properly")
        
        # Music state
        self.current_playlist = []
        self.current_track_index = 0
        self.is_playing = False
        self.volume = 50  # Start at 50%
        self.last_gesture_time_volume = 0  # Separate timing for volume gestures
        self.last_gesture_time_track = 0   # Separate timing for track gestures
        self.last_color_check = 0
        
        # Environment stability tracking
        self.detected_vibe = None  # Currently detected vibe (not yet switched to)
        self.detected_vibe_start_time = 0  # When this vibe was first detected
        
        # Proximity state for pause/play
        self.proximity_detected = False
        self.proximity_start_time = 0
        self.proximity_toggle_cooldown = 0
        
        # Load music files - four vibe playlists
        self.chill_music = []      # Chill vibe playlist
        self.energetic_music = []  # Energetic vibe playlist
        self.warm_music = []       # Warm vibe playlist
        self.party_music = []      # Party vibe playlist
        
        self._load_music_files()
        
        # Start servo control thread
        self.servo_running = True
        self.servo_thread = threading.Thread(target=self._servo_control_loop, daemon=True)
        self.servo_thread.start()
        
        print("\n[START] Interactive Music Box Ready!")
        print("Controls:")
        print("  - Gesture UP: Increase volume")
        print("  - Gesture DOWN: Decrease volume")
        print("  - Gesture LEFT: Previous track")
        print("  - Gesture RIGHT: Next track")
        print("  - Hold hand still: Pause/Play toggle")
        print("  - Rotary knob: Change movement mode")
        print("  - Environment: Auto-selects music based on brightness and color")
        print("    Vibes: Chill, Energetic, Warm, Party\n")
    
    def _load_music_files(self):
        """Load music files from the music directory and categorize by vibe."""
        if not MUSIC_DIR.exists():
            MUSIC_DIR.mkdir(parents=True, exist_ok=True)
            print(f"[WARNING] Created music directory: {MUSIC_DIR}")
            print("   Please add music files (.mp3, .wav, .ogg) to this directory")
            print("   File naming conventions:")
            print("     - chill_*.mp3 or relaxing_*.mp3 → Chill vibe")
            print("     - energetic_*.mp3 or upbeat_*.mp3 → Energetic vibe")
            print("     - warm_*.mp3 or cozy_*.mp3 → Warm vibe")
            print("     - party_*.mp3 or dance_*.mp3 → Party vibe")
            print("     - Other files (no prefix) → Chill vibe (default)")
            return
        
        # Find all music files
        music_files = list(MUSIC_DIR.glob("*.mp3")) + \
                     list(MUSIC_DIR.glob("*.wav")) + \
                     list(MUSIC_DIR.glob("*.ogg"))
        
        if not music_files:
            print(f"[WARNING] No music files found in {MUSIC_DIR}")
            print("   Please add music files to enable playback")
            return
        
        # Categorize music files by vibe
        for file in music_files:
            filename = file.name.lower()
            file_path = str(file)
            
            if filename.startswith("chill_") or filename.startswith("relaxing_") or filename.startswith("calm_"):
                self.chill_music.append(file_path)
            elif filename.startswith("energetic_") or filename.startswith("upbeat_") or filename.startswith("active_"):
                self.energetic_music.append(file_path)
            elif filename.startswith("warm_") or filename.startswith("cozy_") or filename.startswith("soft_"):
                self.warm_music.append(file_path)
            elif filename.startswith("party_") or filename.startswith("dance_") or filename.startswith("festive_"):
                self.party_music.append(file_path)
            else:
                # Default: add to Chill playlist if no prefix matches
                self.chill_music.append(file_path)
        
        # If no categorized files, use all files for Chill playlist (default)
        if not any([self.chill_music, self.energetic_music, self.warm_music, self.party_music]):
            all_files = [str(f) for f in music_files]
            self.chill_music = all_files
        
        print(f"[OK] Loaded playlists:")
        print(f"     Chill: {len(self.chill_music)} tracks")
        print(f"     Energetic: {len(self.energetic_music)} tracks")
        print(f"     Warm: {len(self.warm_music)} tracks")
        print(f"     Party: {len(self.party_music)} tracks")
    
    def _detect_vibe_from_environment(self, lux, color_temp):
        """
        Detect which vibe should be playing based on ambient brightness and color.
        Returns the vibe name (does not switch playlists).
        
        Vibe selection logic:
        - Chill: Low brightness (< LOW_LUX_THRESHOLD)
        - Warm: Medium brightness, warm color temperature (> WARM_COLOR_TEMP)
        - Energetic: High brightness, any color
        - Party: Very high brightness (> HIGH_LUX_THRESHOLD)
        """
        if lux < LOW_LUX_THRESHOLD:
            return VIBE_CHILL
        elif lux > HIGH_LUX_THRESHOLD:
            return VIBE_PARTY
        elif color_temp > WARM_COLOR_TEMP:
            return VIBE_WARM
        else:
            return VIBE_ENERGETIC
    
    def _get_playlist_for_vibe(self, vibe_name):
        """Get the playlist for a given vibe name."""
        if vibe_name == VIBE_CHILL:
            return self.chill_music
        elif vibe_name == VIBE_ENERGETIC:
            return self.energetic_music
        elif vibe_name == VIBE_WARM:
            return self.warm_music
        elif vibe_name == VIBE_PARTY:
            return self.party_music
        return None
    
    def _get_current_vibe_name(self):
        """Get the name of the current vibe playlist."""
        if self.current_playlist == self.chill_music:
            return VIBE_CHILL
        elif self.current_playlist == self.energetic_music:
            return VIBE_ENERGETIC
        elif self.current_playlist == self.warm_music:
            return VIBE_WARM
        elif self.current_playlist == self.party_music:
            return VIBE_PARTY
        else:
            return "Unknown"
    
    def _check_environment(self):
        """
        Check environment and update music selection if needed.
        Only switches after environment has been stable for ENVIRONMENT_STABILITY_TIME seconds.
        """
        current_time = time.time()
        if current_time - self.last_color_check < COLOR_UPDATE_INTERVAL:
            return
        
        self.last_color_check = current_time
        
        # Wait for color data to be ready
        if not self.apds.color_data_ready:
            return
        
        # Read color and calculate brightness and color temperature
        r, g, b, c = self.apds.color_data
        lux = colorutility.calculate_lux(r, g, b)
        color_temp = colorutility.calculate_color_temperature(r, g, b)
        
        # Detect which vibe the current environment should trigger
        detected_vibe = self._detect_vibe_from_environment(lux, color_temp)
        
        # Check if this is a new vibe detection
        if detected_vibe != self.detected_vibe:
            # Environment changed - start tracking new vibe
            self.detected_vibe = detected_vibe
            self.detected_vibe_start_time = current_time
            print(f"[ENV] Environment changed - Detected {detected_vibe} vibe ({lux:.1f} lux, {color_temp:.0f}K)")
            print(f"      Waiting {ENVIRONMENT_STABILITY_TIME:.1f}s for stability (music continues playing)...")
            return
        
        # Same vibe detected - check if it's been stable long enough
        if self.detected_vibe and self.detected_vibe_start_time > 0:
            new_playlist = self._get_playlist_for_vibe(self.detected_vibe)
            
            # If detected vibe matches current playlist, reset tracking (no change needed)
            if new_playlist == self.current_playlist:
                self.detected_vibe = None
                self.detected_vibe_start_time = 0
                return False
            
            # Check if we should switch to this vibe
            if new_playlist:
                stability_duration = current_time - self.detected_vibe_start_time
                remaining_time = ENVIRONMENT_STABILITY_TIME - stability_duration
                
                # Show progress every 2 seconds while waiting
                if int(stability_duration) % 2 == 0 and stability_duration > 0:
                    print(f"[ENV] Waiting for stability: {stability_duration:.1f}s / {ENVIRONMENT_STABILITY_TIME:.1f}s (music playing...)")
                
                if stability_duration >= ENVIRONMENT_STABILITY_TIME:
                    # Environment has been stable long enough - switch playlists
                    self.current_playlist = new_playlist
                    self.current_track_index = 0  # Reset to start of new playlist
                    print(f"[{self.detected_vibe.upper()}] Environment stable for {stability_duration:.1f}s")
                    print(f"         Switching to {self.detected_vibe} vibe playlist")
                    
                    # Reset tracking
                    self.detected_vibe = None
                    self.detected_vibe_start_time = 0
                    
                    # Restart playback with new playlist if playing
                    if self.is_playing:
                        self._play_current_track()
                    return True
                # else: Still waiting for stability, music continues playing from current playlist
    
    def _play_current_track(self):
        """Play the current track from the playlist."""
        if not self.current_playlist:
            print("[WARNING] No music files available")
            return
        
        if self.current_track_index >= len(self.current_playlist):
            self.current_track_index = 0
        
        track_path = self.current_playlist[self.current_track_index]
        track_name = Path(track_path).name
        vibe_name = self._get_current_vibe_name()
        
        try:
            pygame.mixer.music.load(track_path)
            pygame.mixer.music.set_volume(self.volume / 100.0)
            pygame.mixer.music.play()
            self.is_playing = True
            print(f"[PLAY] {vibe_name} vibe - Now playing: {track_name}")
        except Exception as e:
            print(f"[ERROR] Error playing {track_name}: {e}")
            self.is_playing = False
    
    def _stop_playback(self):
        """Stop music playback."""
        pygame.mixer.music.stop()
        self.is_playing = False
        print("[STOP] Playback stopped")
    
    def _handle_gesture(self, gesture):
        """Handle gesture input for music control."""
        current_time = time.time()
        
        if gesture == 0x01:  # UP - Increase volume
            # Use shorter debounce for volume gestures for better responsiveness
            if current_time - self.last_gesture_time_volume < GESTURE_DEBOUNCE_VOLUME:
                return
            self.last_gesture_time_volume = current_time
            
            self.volume = min(self.volume + VOLUME_STEP, MAX_VOLUME)
            pygame.mixer.music.set_volume(self.volume / 100.0)
            print(f"[VOL+] Volume: {self.volume}%")
        
        elif gesture == 0x02:  # DOWN - Decrease volume
            # Use shorter debounce for volume gestures for better responsiveness
            if current_time - self.last_gesture_time_volume < GESTURE_DEBOUNCE_VOLUME:
                return
            self.last_gesture_time_volume = current_time
            
            self.volume = max(self.volume - VOLUME_STEP, MIN_VOLUME)
            pygame.mixer.music.set_volume(self.volume / 100.0)
            print(f"[VOL-] Volume: {self.volume}%")
        
        elif gesture == 0x03:  # LEFT - Previous track (same playlist)
            # Use longer debounce for track changes to prevent accidental skips
            if current_time - self.last_gesture_time_track < GESTURE_DEBOUNCE_TRACK:
                return
            self.last_gesture_time_track = current_time
            
            if not self.current_playlist:
                return
            # Navigate within current playlist only
            self.current_track_index = (self.current_track_index - 1) % len(self.current_playlist)
            track_name = Path(self.current_playlist[self.current_track_index]).name
            if self.is_playing:
                self._play_current_track()
            else:
                # Determine current vibe name for feedback
                vibe_name = self._get_current_vibe_name()
                print(f"[PREV] Previous track in {vibe_name} playlist: {track_name}")
        
        elif gesture == 0x04:  # RIGHT - Next track (same playlist)
            # Use longer debounce for track changes to prevent accidental skips
            if current_time - self.last_gesture_time_track < GESTURE_DEBOUNCE_TRACK:
                return
            self.last_gesture_time_track = current_time
            
            if not self.current_playlist:
                return
            # Navigate within current playlist only
            self.current_track_index = (self.current_track_index + 1) % len(self.current_playlist)
            track_name = Path(self.current_playlist[self.current_track_index]).name
            if self.is_playing:
                self._play_current_track()
            else:
                # Determine current vibe name for feedback
                vibe_name = self._get_current_vibe_name()
                print(f"[NEXT] Next track in {vibe_name} playlist: {track_name}")
    
    def _check_gestures(self):
        """Check for gesture input - simple check like gesture_test.py for better sensitivity."""
        # Simple gesture check (matching gesture_test.py pattern that works well)
        gesture = self.apds.gesture()
        if gesture != 0:
            self._handle_gesture(gesture)
    
    def _check_proximity_pause_play(self):
        """Check proximity sensor for pause/play toggle (hold hand still)."""
        current_time = time.time()
        
        # Check cooldown to prevent rapid toggling
        if current_time - self.proximity_toggle_cooldown < 2.0:
            return
        
        # Read proximity value
        proximity = self.apds.proximity
        
        if proximity > PROXIMITY_THRESHOLD:
            # Hand detected
            if not self.proximity_detected:
                # Just detected - start timer
                self.proximity_detected = True
                self.proximity_start_time = current_time
            else:
                # Hand still there - check if held long enough
                hold_duration = current_time - self.proximity_start_time
                if hold_duration >= PROXIMITY_HOLD_TIME:
                    # Toggle pause/play
                    if self.is_playing:
                        pygame.mixer.music.pause()
                        self.is_playing = False
                        print("[PAUSE] Paused")
                    else:
                        if self.current_playlist:
                            if not pygame.mixer.music.get_busy():
                                # Not playing anything, start current track
                                self._play_current_track()
                            else:
                                # Already loaded, just unpause
                                pygame.mixer.music.unpause()
                            self.is_playing = True
                            print("[PLAY] Playing")
                    
                    self.proximity_toggle_cooldown = current_time
                    self.proximity_detected = False  # Reset to require new detection
        else:
            # No hand detected
            self.proximity_detected = False
    
    def _check_rotary_encoder(self):
        """Check rotary encoder for movement mode changes."""
        if self.encoder is None:
            return
        
        # Read encoder position (negate to make clockwise rotation positive)
        position = -self.encoder.position
        
        if position != self.last_encoder_position:
            # Encoder moved - change mode based on position
            mode_change = position - self.last_encoder_position
            
            if mode_change > 0:
                # Clockwise - cycle through modes
                self.movement_mode = (self.movement_mode + 1) % 3
            else:
                # Counter-clockwise - cycle backwards
                self.movement_mode = (self.movement_mode - 1) % 3
            
            mode_names = ["STOP", "SPIN LEFT", "SPIN RIGHT"]
            print(f"[MODE] Movement mode: {mode_names[self.movement_mode]}")
            
            self.last_encoder_position = position
    
    def _servo_control_loop(self):
        """Control servo movement in a separate thread."""
        if self.servo is None:
            return
        
        angle = 90  # Center position
        direction = 1  # 1 for right, -1 for left
        
        while self.servo_running:
            if self.movement_mode == MODE_STOP:
                # Keep servo at center
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
                # Rotate left (counter-clockwise)
                angle -= 5
                if angle < 0:
                    angle = 180
                self.servo.angle = angle
                time.sleep(0.05)
            
            elif self.movement_mode == MODE_SPIN_RIGHT:
                # Rotate right (clockwise)
                angle += 5
                if angle > 180:
                    angle = 0
                self.servo.angle = angle
                time.sleep(0.05)
            
            else:
                time.sleep(0.1)
    
    def _check_music_status(self):
        """Check if current track finished and play next."""
        if self.is_playing and not pygame.mixer.music.get_busy():
            # Track finished, play next
            if self.current_playlist:
                self.current_track_index = (self.current_track_index + 1) % len(self.current_playlist)
                self._play_current_track()
    
    def run(self):
        """Main loop for the music box."""
        try:
            # Initialize playlist based on current environment
            if not self.current_playlist:
                # Wait for first color reading to determine initial vibe
                print("Detecting environment to select initial vibe...")
                while not self.apds.color_data_ready:
                    time.sleep(0.1)
                r, g, b, c = self.apds.color_data
                lux = colorutility.calculate_lux(r, g, b)
                color_temp = colorutility.calculate_color_temperature(r, g, b)
                
                # Set initial vibe and playlist immediately (no stability check on startup)
                initial_vibe = self._detect_vibe_from_environment(lux, color_temp)
                self.current_playlist = self._get_playlist_for_vibe(initial_vibe)
                self.detected_vibe = initial_vibe
                self.detected_vibe_start_time = time.time()
                print(f"[INIT] Initial environment: {initial_vibe} vibe ({lux:.1f} lux, {color_temp:.0f}K)")
            
            # Start with first track
            if self.current_playlist:
                self._play_current_track()
            
            while True:
                # PRIORITY: Check for gestures first (most time-sensitive)
                # Check multiple times per loop to catch quick gestures (like gesture_test.py)
                for _ in range(5):  # Check 5 times per main loop iteration
                    self._check_gestures()
                    time.sleep(0.001)  # Very tiny delay between checks
                
                # Check environment and update music selection
                self._check_environment()
                
                # Check proximity for pause/play
                self._check_proximity_pause_play()
                
                # Check rotary encoder
                self._check_rotary_encoder()
                
                # Check if track finished
                self._check_music_status()
                
                # Very small delay for maximum gesture responsiveness
                time.sleep(0.005)  # Minimal delay to match gesture_test.py responsiveness
        
        except KeyboardInterrupt:
            print("\n\n[SHUTDOWN] Shutting down Interactive Music Box...")
            self.servo_running = False
            if self.is_playing:
                self._stop_playback()
            if self.servo:
                self.servo.angle = 90  # Return to center
            print("[OK] Shutdown complete")


def main():
    """Main entry point."""
    music_box = MusicBox()
    music_box.run()


if __name__ == "__main__":
    main()

