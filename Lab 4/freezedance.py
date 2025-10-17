# This script integrates a SparkFun Qwiic Proximity Sensor (VCNL4040)
# and an Adafruit I2C Rotary Encoder (seesaw) to control video playback.
#
# Proximity sensor controls: Play/Pause based on motion.
# Rotary Encoder controls: Volume adjustment (turn) and Mute toggle (press).

import time
import sys
import os
import statistics

# Hardware-specific imports
# NOTE: These libraries require specific hardware (Raspberry Pi/Linux) and setup.
# You must have 'qwiic_proximity', 'yt_dlp', and 'python-vlc' installed.
try:
    import qwiic_proximity
    import board
    from adafruit_seesaw import seesaw, rotaryio, digitalio
    import vlc
    import yt_dlp
except ImportError as e:
    print(f"Error importing dependencies: {e}")
    print("This script requires 'qwiic_proximity', 'adafruit-circuitpython-seesaw', 'python-vlc', and 'yt-dlp'.")
    sys.exit(1)


# --- CONFIGURATION ---
YOUTUBE_URL = "https://youtu.be/EPo5wWmKEaI?si=P4iQHYS6ml0Li500"
TEMP_FILE = "/tmp/video.mp4"
SAMPLE_WINDOW = 10         # Number of proximity readings to track
MOVEMENT_THRESHOLD = 5     # Standard deviation threshold for detecting motion
CHECK_INTERVAL = 0.4       # Delay between sensor checks (seconds)
VOLUME_STEP = 5            # Volume change per encoder click (0-100 range)
# ---------------------


def download_video(url):
    """Download YouTube video to a local MP4 file using yt_dlp."""
    print("Downloading video to /tmp/video.mp4 ... (this may take a moment)")
    # Ensure the /tmp directory exists, although it usually does on Linux/macOS
    os.makedirs(os.path.dirname(TEMP_FILE), exist_ok=True)
    ydl_opts = {
        'quiet': False,
        'format': 'best[ext=mp4]/best',
        'outtmpl': TEMP_FILE,
        'noplaylist': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return TEMP_FILE
    except Exception as e:
        print(f"Error during video download: {e}", file=sys.stderr)
        return None


def setup_rotary_encoder():
    """Initializes the I2C rotary encoder using adafruit_seesaw."""
    try:
        ss = seesaw.Seesaw(board.I2C(), addr=0x36)

        # Check product ID (optional, but good practice)
        seesaw_product = (ss.get_version() >> 16) & 0xFFFF
        if seesaw_product != 4991:
            print(f"Warning: Expected product 4991, found {seesaw_product}. Continuing anyway.")

        # Setup button on pin 24 with pull-up resistor
        ss.pin_mode(24, ss.INPUT_PULLUP)
        button = digitalio.DigitalIO(ss, 24)

        # Setup rotary encoder
        encoder = rotaryio.IncrementalEncoder(ss)

        # Negate the position so clockwise rotation increases value
        last_position = -encoder.position

        print("Rotary Encoder Initialized.")
        return ss, button, encoder, last_position
    except Exception as e:
        print(f"Warning: Rotary Encoder initialization failed. Volume control will be inactive. Error: {e}")
        return None, None, None, 0


def runExample():
    print("\n--- Proximity and Rotary Media Controller ---\n")

    # 1. Hardware Initialization
    oProx = qwiic_proximity.QwiicProximity()
    if not oProx.connected:
        print("The Qwiic Proximity device isn't connected. Please check your connection.", file=sys.stderr)
        return

    oProx.begin()
    ss, button, encoder, last_position = setup_rotary_encoder()
    button_held = False # State for button debouncing/toggling

    # 2. Video Download/Preparation
    if not os.path.exists(TEMP_FILE):
        video_path = download_video(YOUTUBE_URL)
        if not video_path:
            print("Video file is unavailable. Exiting.")
            return
    else:
        video_path = TEMP_FILE
        print("Using cached video:", video_path)

    # 3. VLC Player Setup
    print("Starting VLC player...")
    instance = vlc.Instance()
    player = instance.media_player_new()
    media = instance.media_new(video_path)
    player.set_media(media)

    # Start playback initially
    player.play()
    time.sleep(1) # Give player time to start
    is_playing = True
    print(f"Initial Volume: {player.audio_get_volume()}")

    # 4. Main Control Loop
    readings = []
    global last_position # Use global/nonlocal if this was in a nested function, but in this case, update the local variable passed back from setup

    try:
        while True:
            # --- PROXIMITY (Play/Pause) LOGIC ---
            proxValue = oProx.get_proximity()
            readings.append(proxValue)
            if len(readings) > SAMPLE_WINDOW:
                readings.pop(0)

            if len(readings) >= SAMPLE_WINDOW:
                # Calculate standard deviation of the readings over the window
                variation = statistics.stdev(readings)
                print(f"Proximity: {proxValue} | Variation: {variation:.2f} ", end="")

                if variation > MOVEMENT_THRESHOLD:
                    if not is_playing:
                        print("| ACTION: PLAY")
                        player.play()
                        is_playing = True
                    else:
                        print("| STATE: Playing")
                else:
                    if is_playing:
                        print("| ACTION: PAUSE")
                        player.pause()
                        is_playing = False
                    else:
                        print("| STATE: Paused (Stable)")
            else:
                 print(f"Proximity: {proxValue} | STATE: Warming up ({len(readings)}/{SAMPLE_WINDOW})")


            # --- ROTARY ENCODER (Volume/Mute) LOGIC ---
            if encoder:
                current_position = -encoder.position
                
                # Volume Adjustment
                if current_position != last_position:
                    delta = current_position - last_position
                    last_position = current_position

                    current_volume = player.audio_get_volume()
                    volume_change = delta * VOLUME_STEP
                    
                    new_volume = current_volume + volume_change
                    
                    # Clamp volume between 0 and 100
                    new_volume = max(0, min(100, new_volume))
                    
                    player.audio_set_volume(new_volume)
                    print(f"| ENCODER: Volume Adjusted. New Volume: {new_volume}")


                # Mute Toggle (Button Press)
                if not button.value and not button_held:
                    button_held = True
                    is_muted = player.audio_get_mute()
                    player.audio_set_mute(not is_muted)
                    print(f"| ENCODER: Button Pressed. Toggled Mute: {not is_muted}")
                
                if button.value and button_held:
                    button_held = False # Button released, reset state

            time.sleep(CHECK_INTERVAL)

    finally:
        # Cleanup VLC player (ensure it stops)
        if 'player' in locals() and player:
            player.stop()

# --- Cleanup and Exit ---
if __name__ == '__main__':
    try:
        runExample()
    except (KeyboardInterrupt, SystemExit):
        print("\nExiting program. Cleaning up temporary file.")
        
        # Best practice cleanup: stop player before deleting file (done in finally block)
        
        try:
            if os.path.exists(TEMP_FILE):
                os.remove(TEMP_FILE)
                print("Deleted:", TEMP_FILE)
        except Exception as e:
            print("Could not delete temp file:", e)
        sys.exit(0)
