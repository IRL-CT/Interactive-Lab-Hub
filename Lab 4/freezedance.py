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
# Playlist URL instead of single video URL
YOUTUBE_PLAYLIST_URL = "https://www.youtube.com/playlist?list=PLDEoYTx7cT4dC7dkTTYi1exK5iYVtBw0B"
SAMPLE_WINDOW = 10      # Number of proximity readings to use for standard deviation
MOVEMENT_THRESHOLD = 5  # Standard deviation threshold to detect motion
CHECK_INTERVAL = 0.05   # Loop delay for responsiveness

# List of Qwiic GPIO pins used for active-low LEDs (connected 3.3V to Pin)
LED_PINS = [0, 1, 2, 3] 
# ---------------------

# Global Qwiic GPIO object and VLC list player
myGPIO = None
list_player = None

# --- UTILITY FUNCTIONS ---

def get_playlist_urls(url):
    """Retrieves all video URLs from a YouTube playlist using yt_dlp."""
    print("Fetching playlist information...")
    ydl_opts = {
        'extract_flat': True,  # Only extract URLs, don't download
        'force_generic_extractor': True,
        'quiet': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        # Extract full URLs from the entries
        urls = [entry['url'] for entry in info['entries'] if 'url' in entry]
    
    print(f"Found {len(urls)} videos in the playlist.")
    return urls

# -------------------------
# --- GPIO CONTROL FUNCTIONS (No Change) ---
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

    status_attribute = f"out_status_{pin_num}"
    
    # Active-Low Logic: True (ON) -> GPIO_LO | False (OFF) -> GPIO_HI
    gpio_state = myGPIO.GPIO_LO if state_on else myGPIO.GPIO_HI
    
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
        
    myGPIO.setGPIO()

def flash_lights_if_playing(list_player):
    """Checks the VLC player state and calls the disco routine if music is playing."""
    # list_player.get_state() applies to the currently playing item
    if list_player.get_state() == vlc.State.Playing:
        disco()
        
# -------------------------
# --- MAIN PROGRAM LOOP ---
# -------------------------

def runExample():
    global myGPIO, list_player
    print("\nSparkFun VCNL4040 + Qwiic GPIO + VLC (Playlist Shuffle Mode)\n")
    
    if not initialize_gpio():
        print("Program halted due to missing Qwiic GPIO connection.")
        return

    oProx = qwiic_proximity.QwiicProximity()
    if not oProx.connected:
        print("The Qwiic Proximity device isn't connected.", file=sys.stderr)
    
    if oProx.connected:
        oProx.begin()

    # Step 1: Get all video URLs from the YouTube playlist
    playlist_urls = get_playlist_urls(YOUTUBE_PLAYLIST_URL)
    if not playlist_urls:
        print("Could not retrieve playlist URLs. Exiting.")
        return

    # Step 2: Set up VLC Media List Player for shuffling
    print("Setting up VLC Media List Player...")
    instance = vlc.Instance()
    
    # Create a VLC MediaList from the URLs
    media_list = instance.media_list_new(playlist_urls)
    
    # Create the List Player
    list_player = instance.media_list_player_new()
    list_player.set_media_list(media_list)
    
    # CRITICAL: Enable the Random (Shuffle) and Repeat modes
    list_player.set_playback_mode(vlc.PlaybackMode.loop) 
    list_player.set_playback_mode(vlc.PlaybackMode.random) 
    
    list_player.pause() # Start paused, waiting for movement
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
            
            # --- Motion Detection (Play/Pause) Logic ---
            if variation > MOVEMENT_THRESHOLD:
                if not is_playing:
                    print(f"Movement detected (Var: {variation:.2f}): PLAY")
                    
                    # If the player is STOPPED (which happens after a pause or at the end of the list)
                    # we must explicitly tell it to play the next item.
                    current_state = list_player.get_state()
                    if current_state in (vlc.State.Stopped, vlc.State.Ended, vlc.State.Error):
                        list_player.play_item_at_index(0) # Start playing the first item (randomly selected by shuffle mode)
                    elif current_state == vlc.State.Paused:
                        list_player.play() # Resume the current song
                    
                    is_playing = True
            else:
                if is_playing:
                    print(f"Stable distance (Var: {variation:.2f}): PAUSE")
                    list_player.pause()
                    is_playing = False
                    
        # --- Light Flashing Logic ---
        flash_lights_if_playing(list_player)

        time.sleep(CHECK_INTERVAL)


if __name__ == '__main__':
    try:
        runExample()
    except (KeyboardInterrupt, SystemExit):
        # --- Cleanup on Exit ---
        if list_player:
            list_player.stop()
            
        if myGPIO:
            # Ensure all LEDs are turned OFF (HIGH) before exiting
            for pin in LED_PINS:
                status_attribute = f"out_status_{pin}"
                setattr(myGPIO, status_attribute, myGPIO.GPIO_HI)
            myGPIO.setGPIO()
            
        print("\nExiting program.")
        sys.exit(0)
