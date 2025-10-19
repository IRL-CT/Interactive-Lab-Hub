import qwiic_proximity
import time
import sys
import statistics
import vlc
import yt_dlp
import os
import random
# Qwiic GPIO Expander Library
from __future__ import print_function
import qwiic_gpio

# --- CONFIGURATION ---
YOUTUBE_URL = "https://youtu.be/EPo5wWmKEaI?si=P4iQHYS6ml0Li500"
TEMP_FILE = "/tmp/video.mp4"
SAMPLE_WINDOW = 10      # Number of proximity readings to use for standard deviation
MOVEMENT_THRESHOLD = 5  # Standard deviation threshold to detect motion
CHECK_INTERVAL = 0.05   # Loop delay for responsiveness

# List of Qwiic GPIO pins used for active-low LEDs (connected 3.3V to Pin)
LED_PINS = [0, 1, 2, 3] 
# ---------------------

# Global Qwiic GPIO object
myGPIO = None

# --- UTILITY FUNCTIONS ---

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

# -------------------------
# --- GPIO CONTROL FUNCTIONS ---
# -------------------------

def initialize_gpio():
    """Initializes the Qwiic GPIO board and sets pins to active-low output (OFF)."""
    global myGPIO
    myGPIO = qwiic_gpio.QwiicGPIO()

    if myGPIO.isConnected() == False:
        print("The Qwiic GPIO isn't connected. Check your connection.", file=sys.stderr)
        return False

    myGPIO.begin()
    
    for pin in LED_PINS:
        # Set pin mode to OUTPUT
        mode_attribute = f"mode_{pin}"
        setattr(myGPIO, mode_attribute, myGPIO.GPIO_OUT)
        
        # Set pin status to HIGH (LED OFF for active-low wiring)
        status_attribute = f"out_status_{pin}"
        setattr(myGPIO, status_attribute, myGPIO.GPIO_HI)
        
    myGPIO.setMode()  # Apply mode changes
    myGPIO.setGPIO()  # Apply status changes (turn all LEDs OFF)
    print(f"Qwiic GPIO initialized. Pins {LED_PINS} set to OUTPUT/OFF.")
    return True

def set_gpio_pin(pin_num, state_on):
    """
    Controls a single Qwiic GPIO pin using active-low logic.
    state_on=True turns LED ON (sets pin LOW); state_on=False turns LED OFF (sets pin HIGH).
    """
    global myGPIO
    if myGPIO is None: return

    # Get the name of the status attribute (e.g., 'out_status_0')
    status_attribute = f"out_status_{pin_num}"
    
    # Active-Low Logic: True (ON) -> GPIO_LO | False (OFF) -> GPIO_HI
    gpio_state = myGPIO.GPIO_LO if state_on else myGPIO.GPIO_HI
    
    # Set the attribute value dynamically
    setattr(myGPIO, status_attribute, gpio_state)

def disco():
    """Quick, random LED flash sequence."""
    global myGPIO
    if myGPIO is None: return
        
    # Pick a random pin to flash
    pin_num = random.choice(LED_PINS)
    
    # Flash sequence
    set_gpio_pin(pin_num, True)  # Set pin LOW (ON)
    time.sleep(0.02)
    set_gpio_pin(pin_num, False) # Set pin HIGH (OFF)
        
    # Must call setGPIO() once after setting the status properties
    myGPIO.setGPIO()

def flash_lights_if_playing(player):
    """Checks the VLC player state and calls the disco routine if music is playing."""
    # Check if the VLC player state is vlc.State.Playing (1)
    if player.get_state() == vlc.State.Playing:
        disco()
        
# -------------------------
# --- MAIN PROGRAM LOOP ---
# -------------------------
def runExample():
    global myGPIO
    print("\nSparkFun VCNL4040 + Qwiic GPIO + VLC (Motion-Activated Disco)\n")
    
    # Initialize GPIO board first
    if not initialize_gpio():
        print("Program halted due to missing Qwiic GPIO connection.")
        return

    oProx = qwiic_proximity.QwiicProximity()

    if not oProx.connected:
        print("The Qwiic Proximity device isn't connected.", file=sys.stderr)
        
    if oProx.connected:
        oProx.begin()

    # Step 1: Ensure we have the video locally
    video_path = TEMP_FILE
    if not os.path.exists(TEMP_FILE):
        video_path = download_video(YOUTUBE_URL)
    else:
        print("Using cached video:", video_path)

    # Step 2: Set up VLC player
    print("Setting up VLC player...")
    instance = vlc.Instance()
    player = instance.media_player_new()
    media = instance.media_new(video_path)
    player.set_media(media)
    
    player.pause() # Start paused, waiting for movement
    is_playing = False 

    readings = []

    while True:
        proxValue = 0
        if oProx.connected:
            proxValue = oProx.get_proximity()
        
        # Collect proximity readings
        readings.append(proxValue)
        if len(readings) > SAMPLE_WINDOW:
            readings.pop(0)

        if len(readings) >= SAMPLE_WINDOW:
            # Calculate variation (standard deviation)
            variation = statistics.stdev(readings) if len(readings) > 1 else 0
            
            # Check the current VLC state
            current_state = player.get_state()

            # --- Motion Detection (Play/Pause) Logic ---
            if variation > MOVEMENT_THRESHOLD:
                if not is_playing:
                    print(f"Movement detected (Var: {variation:.2f}): PLAY")
                    
                    # --- CRITICAL FIX ---
                    # If the clip has ended, set its position back to 0 before playing.
                    if current_state == vlc.State.Ended:
                        print("Clip ended, restarting from beginning.")
                        player.set_position(0.0)
                    # --------------------

                    player.play()
                    is_playing = True
            else:
                if is_playing:
                    print(f"Stable distance (Var: {variation:.2f}): PAUSE")
                    player.pause() # This correctly holds the current position
                    is_playing = False
                    
        # --- Light Flashing Logic ---
        flash_lights_if_playing(player)

        time.sleep(CHECK_INTERVAL)

if __name__ == '__main__':
    try:
        runExample()
    except (KeyboardInterrupt, SystemExit):
        # --- Cleanup on Exit ---
        if myGPIO:
            # Ensure all LEDs are turned OFF (HIGH) before exiting
            for pin in LED_PINS:
                status_attribute = f"out_status_{pin}"
                setattr(myGPIO, status_attribute, myGPIO.GPIO_HI)
            myGPIO.setGPIO()
            
        print("\nExiting program. Cleaning up temporary file.")
        try:
            if os.path.exists(TEMP_FILE):
                os.remove(TEMP_FILE)
                print("Deleted:", TEMP_FILE)
        except Exception as e:
            print("Could not delete temp file:", e)
        sys.exit(0)
