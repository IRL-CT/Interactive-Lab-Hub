from __future__ import print_function

import qwiic_proximity
import qwiic_gpio
import time
import sys
import statistics
import vlc
import yt_dlp
import os
import random

# --- CONFIGURATION ---
YOUTUBE_URL = "https://youtu.be/EPo5wWmKEaI?si=P4iQHYS6ml0Li500"
TEMP_FILE = "/tmp/video.mp4"
SAMPLE_WINDOW = 10       # Number of proximity readings to use for standard deviation
MOVEMENT_THRESHOLD = 5   # Standard deviation threshold to detect motion
CHECK_INTERVAL = 0.05    # Loop delay for responsiveness

# List of Qwiic GPIO pins used for active-low LEDs (connected 3.3V to pin)
LED_PINS = [0, 1, 2, 3]
# ---------------------

myGPIO = None  # Global Qwiic GPIO object

# --- UTILITY FUNCTIONS ---

def download_video(url):
    """Download YouTube video to local MP4 file using yt_dlp."""
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
    """Initializes the Qwiic GPIO board and sets pins as active-low output (OFF)."""
    global myGPIO
    myGPIO = qwiic_gpio.QwiicGPIO()

    if not myGPIO.isConnected():
        print("❌ The Qwiic GPIO isn't connected. Check your wiring.", file=sys.stderr)
        return False

    myGPIO.begin()

    # Configure LED pins
    for pin in LED_PINS:
        setattr(myGPIO, f"mode_{pin}", myGPIO.GPIO_OUT)
        setattr(myGPIO, f"out_status_{pin}", myGPIO.GPIO_HI)  # OFF (active-low)

    myGPIO.setMode()
    myGPIO.setGPIO()
    print(f"✅ Qwiic GPIO initialized. Pins {LED_PINS} set as OUTPUT (LEDs OFF).")
    return True

def set_gpio_pin(pin_num, state_on):
    """
    Controls a single Qwiic GPIO pin using active-low logic.
    state_on=True turns LED ON (sets pin LOW)
    state_on=False turns LED OFF (sets pin HIGH)
    """
    global myGPIO
    if myGPIO is None:
        return

    gpio_state = myGPIO.GPIO_LO if state_on else myGPIO.GPIO_HI
    setattr(myGPIO, f"out_status_{pin_num}", gpio_state)

def disco():
    """Random LED flash pattern."""
    global myGPIO
    if myGPIO is None:
        return

    pin_num = random.choice(LED_PINS)
    set_gpio_pin(pin_num, True)
    myGPIO.setGPIO()
    time.sleep(0.05)
    set_gpio_pin(pin_num, False)
    myGPIO.setGPIO()

def flash_lights_if_playing(player):
    """Flashes LEDs if VLC player is currently playing."""
    if player.get_state() == vlc.State.Playing:
        disco()

# -------------------------
# --- MAIN PROGRAM LOOP ---
# -------------------------

def runExample():
    global myGPIO
    print("\n🎵 SparkFun VCNL4040 + Qwiic GPIO + VLC (Motion-Activated Disco)\n")

    # Initialize GPIO
    if not initialize_gpio():
        print("Program halted due to missing Qwiic GPIO connection.")
        return

    # Initialize proximity sensor
    oProx = qwiic_proximity.QwiicProximity()
    if not oProx.connected:
        print("⚠️ The Qwiic Proximity device isn't connected.", file=sys.stderr)
    else:
        oProx.begin()

    # Step 1: Download or load cached video
    video_path = TEMP_FILE
    if not os.path.exists(TEMP_FILE):
        video_path = download_video(YOUTUBE_URL)
    else:
        print("Using cached video:", video_path)

    # Step 2: Set up VLC
    print("Setting up VLC player...")
    instance = vlc.Instance()
    player = instance.media_player_new()
    media = instance.media_new(video_path)
    player.set_media(media)
    player.pause()
    is_playing = False

    readings = []

    # --- MAIN LOOP ---
    while True:
        proxValue = oProx.get_proximity() if oProx.connected else 0
        readings.append(proxValue)
        if len(readings) > SAMPLE_WINDOW:
            readings.pop(0)

        if len(readings) >= SAMPLE_WINDOW:
            variation = statistics.stdev(readings) if len(readings) > 1 else 0

            # Motion-based play/pause control
            if variation > MOVEMENT_THRESHOLD:
                if not is_playing:
                    print(f"👋 Movement detected (Var: {variation:.2f}) → PLAY")
                    player.play()
                    is_playing = True
            else:
                if is_playing:
                    print(f"😌 Stable distance (Var: {variation:.2f}) → PAUSE")
                    player.pause()
                    is_playing = False

        # Flash LEDs while playing
        flash_lights_if_playing(player)

        time.sleep(CHECK_INTERVAL)

# -------------------------
# --- CLEANUP ON EXIT ---
# -------------------------

if __name__ == '__main__':
    try:
        runExample()
    except (KeyboardInterrupt, SystemExit):
        if myGPIO:
            # Turn all LEDs OFF
            for pin in LED_PINS:
                setattr(myGPIO, f"out_status_{pin}", myGPIO.GPIO_HI)
            myGPIO.setGPIO()

        print("\n🛑 Exiting program. Cleaning up temporary file.")
        if os.path.exists(TEMP_FILE):
            try:
                os.remove(TEMP_FILE)
                print("Deleted:", TEMP_FILE)
            except Exception as e:
                print("Could not delete temp file:", e)
        sys.exit(0)
