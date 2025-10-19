import qwiic_proximity
import time
import sys
import statistics
import vlc
import yt_dlp
import os
import random

# --- LED CONTROL PLACEHOLDERS (REPLACE THIS SECTION) ---
# Assuming a generic GPIO expander library and pins 0, 1, and 2 are used.
# You MUST replace 'your_expander_library' and 'your_expander_class' 
# with the actual code for your specific GPIO expander (e.g., PCF8574, MCP23017).

# ⚠️ PLACEHOLDER ⚠️ - Update these to match your actual library/setup
try:
    # Example placeholder for a GPIO expander object:
    # import your_expander_library as expander_lib
    # i2c_bus = expander_lib.I2C(1)
    # expander = your_expander_class(i2c_bus, address=0x20)
    
    # Mock class to simulate the active-low logic on the expander pins
    class ExpanderPin:
        def __init__(self, pin_num):
            self.pin = pin_num
            # Initialize pin state (assuming expander pins default to high/OFF)
            self._value = True 
        
        @property
        def value(self):
            return self._value
            
        @value.setter
        def value(self, state):
            # Your LEDs are active-low (3.3V to GPIO).
            # True (HIGH) = OFF, False (LOW) = ON
            
            # --- This is the key ACTIVE-LOW logic update ---
            if state:
                # Set pin HIGH (e.g., expander.pin_set(self.pin, True)) -> LED OFF
                pass 
            else:
                # Set pin LOW (e.g., expander.pin_set(self.pin, False)) -> LED ON
                pass
            # ---------------------------------------------
            
            self._value = state
            # print(f"Expander Pin {self.pin} set to {'HIGH/OFF' if state else 'LOW/ON'}")


    leds = [ExpanderPin(0), ExpanderPin(1), ExpanderPin(2), ExpanderPin(3)] 
    print("⚠️ WARNING: Using placeholder ExpanderPin objects. Replace the LED CONTROL section with your real hardware setup.")
except:
    leds = []
    print("CRITICAL: LED initialization failed. Lights will not flash.")
# --- END LED CONTROL PLACEHOLDERS ---


YOUTUBE_URL = "https://youtu.be/EPo5wWmKEaI?si=P4iQHYS6ml0Li500"
TEMP_FILE = "/tmp/video.mp4"
SAMPLE_WINDOW = 10
MOVEMENT_THRESHOLD = 5
CHECK_INTERVAL = 0.05 

def download_video(url):
    """Download YouTube video to a local MP4 file using yt_dlp."""
    print("Downloading video to /tmp/video.mp4 ... (this may take ~30s)")
    ydl_opts = {
        'quiet': True,
        'format': 'best[ext=mp4]/best',
        'outtmpl': TEMP_FILE,
        'noplaylist': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return TEMP_FILE

def disco(led_list):
    """Quick, random LED flash sequence."""
    if not led_list:
        return 
        
    # Quick, rhythmic flash using the active-low logic
    for _ in range(2):
        ld = random.choice(led_list)
        ld.value = False  # Set to LOW (ON)
        time.sleep(0.02)
        ld.value = True   # Set to HIGH (OFF)
        
def flash_lights_if_playing(player, led_list):
    """Check if the VLC player is playing and call the disco routine."""
    if player.get_state() == vlc.State.Playing:
        disco(led_list)
        
def runExample():
    print("\nSparkFun VCNL4040 Proximity Sensor + VLC (Local Playback Mode)\n")
    
    # Initialize VLC instance outside the try block for cleanup
    instance = vlc.Instance() 

    oProx = qwiic_proximity.QwiicProximity()

    if not oProx.connected:
        print("The Qwiic Proximity device isn't connected. Please check your connection.", file=sys.stderr)
        # return # Allows testing music/light logic without sensor
        
    # Check if a sensor connection is necessary before calling begin()
    if oProx.connected:
        oProx.begin()

    # Step 1: Ensure we have the video locally
    if not os.path.exists(TEMP_FILE):
        video_path = download_video(YOUTUBE_URL)
    else:
        video_path = TEMP_FILE
        print("Using cached video:", video_path)

    # Step 2: Play it with VLC
    print("Starting VLC player...")
    player = instance.media_player_new()
    media = instance.media_new(video_path)
    player.set_media(media)
    
    player.pause() 
    is_playing = False 

    readings = []

    while True:
        proxValue = 0
        if oProx.connected:
            proxValue = oProx.get_proximity()
        
        readings.append(proxValue)
        if len(readings) > SAMPLE_WINDOW:
            readings.pop(0)

        if len(readings) >= SAMPLE_WINDOW:
            variation = statistics.stdev(readings) if len(readings) > 1 else 0

            # --- Motion Detection Logic ---
            if variation > MOVEMENT_THRESHOLD:
                if not is_playing:
                    print("Movement detected: PLAY")
                    player.play()
                    is_playing = True
            else:
                if is_playing:
                    print("Stable distance: PAUSE")
                    player.pause()
                    is_playing = False
                    
        # --- CONTINUOUS LIGHT FLASHING LOGIC ---
        flash_lights_if_playing(player, leds)

        time.sleep(CHECK_INTERVAL)


if __name__ == '__main__':
    try:
        runExample()
    except (KeyboardInterrupt, SystemExit):
        # Ensure all LEDs are turned OFF before exiting
        for ld in leds:
            ld.value = True # Set active-low LED to HIGH (OFF)
            
        print("\nExiting program. Cleaning up temporary file.")
        try:
            if os.path.exists(TEMP_FILE):
                os.remove(TEMP_FILE)
                print("Deleted:", TEMP_FILE)
        except Exception as e:
            print("Could not delete temp file:", e)
        sys.exit(0)
