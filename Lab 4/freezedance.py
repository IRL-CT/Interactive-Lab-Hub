import time
import sys
import random
import vlc
import yt_dlp

# --- MPR121 HARDWARE IMPORTS ---
import board
import busio
import adafruit_mpr121
# -------------------------------

# --- CONFIGURATION ---
YOUTUBE_PLAYLIST_URL = "https://www.youtube.com/playlist?list=PLDEoYTx7cT4dC7dkTTYi1exK5iYVtBw0B"
DEFAULT_VOLUME = 60
VOLUME_STEP = 10 # Increase/decrease volume by 10%
CHECK_INTERVAL = 0.05 # Loop delay for responsiveness

# Global VLC list player and current volume
list_player = None
current_volume = DEFAULT_VOLUME

# --- UTILITY FUNCTIONS ---

def get_playlist_urls(url):
    """Retrieves all video URLs from a YouTube playlist using yt_dlp."""
    print("Fetching playlist information...")
    ydl_opts = {
        'extract_flat': True,
        'force_generic_extractor': True,
        'quiet': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            urls = [entry['url'] for entry in info.get('entries', []) if entry and 'url' in entry]
        
        print(f"Found {len(urls)} videos in the playlist.")
        return urls
    except Exception as e:
        print(f"Error fetching playlist: {e}", file=sys.stderr)
        return []

def control_playback(pin_index, player):
    """Handles playback control based on the touched MPR121 pin."""
    global current_volume
    
    # --- SHUFFLE / NEXT SONG (Pins 0-5) ---
    if 0 <= pin_index <= 5:
        print(f"Pin {pin_index} touched: SHUFFLE/NEXT SONG")
        player.next() # Moves to the next track in the shuffled playlist

    # --- VOLUME UP (Pins 6-8) ---
    elif 6 <= pin_index <= 8:
        current_volume = min(100, current_volume + VOLUME_STEP)
        player.get_media_player().audio_set_volume(current_volume)
        print(f"Pin {pin_index} touched: VOLUME UP -> {current_volume}%")

    # --- VOLUME DOWN (Pins 9-11) ---
    elif 9 <= pin_index <= 11:
        current_volume = max(0, current_volume - VOLUME_STEP)
        player.get_media_player().audio_set_volume(current_volume)
        print(f"Pin {pin_index} touched: VOLUME DOWN -> {current_volume}%")

# -------------------------
# --- MAIN PROGRAM LOOP ---
# -------------------------

def runExample():
    global list_player, current_volume
    print("\nMPR121 Touch Control for VLC Playlist Shuffle and Volume\n")
    
    # --- MPR121 INITIALIZATION ---
    try:
        i2c = busio.I2C(board.SCL, board.SDA)
        mpr121 = adafruit_mpr121.MPR121(i2c)
        print("MPR121 sensor initialized.")
    except ValueError as e:
        print(f"Error initializing MPR121: {e}. Check wiring/address.", file=sys.stderr)
        return
    # -----------------------------

    # Step 1: Get all video URLs from the YouTube playlist
    playlist_urls = get_playlist_urls(YOUTUBE_PLAYLIST_URL)
    if not playlist_urls:
        print("Could not retrieve playlist URLs. Exiting.")
        return

    # Step 2: Set up VLC Media List Player
    print("Setting up VLC Media List Player...")
    instance = vlc.Instance()
    
    # Create a VLC MediaList from the URLs
    media_list = instance.media_list_new(playlist_urls)
    
    # Create the List Player
    list_player = instance.media_list_player_new()
    list_player.set_media_list(media_list)
    
    # Enable the Random (Shuffle) and Loop modes
    list_player.set_playback_mode(vlc.PlaybackMode.loop) 
    list_player.set_playback_mode(vlc.PlaybackMode.random) 
    
    # Set initial volume
    list_player.get_media_player().audio_set_volume(current_volume)
    print(f"Initial volume set to {current_volume}%.")
    
    # Start playback of the first random song immediately, but pause it right after.
    list_player.play_item_at_index(0) 
    list_player.pause() 
    print("Player initialized in PAUSED state. Touch a pad to start!")

    # State tracking variable for debouncing/play-pause logic
    is_playing = False
    
    while True:
        # Check if the player is in the 'Ended' state (song finished) and automatically advance
        current_state = list_player.get_state()
        if current_state == vlc.State.Ended:
            print("Song ended, advancing to next shuffled track.")
            list_player.next() # Move to next shuffled track
            # VLC usually starts playing after list_player.next() if it was previously playing
            is_playing = True

        # --- MPR121 Reading Loop ---
        for i in range(12):
            if mpr121[i].value:
                # Debounce: only act on a touch if the player is currently paused, OR if
                # it's a control function (volume/shuffle) that should work anytime.
                
                # SHUFFLE PADS (0-5)
                if 0 <= i <= 5:
                    if not is_playing:
                        # If PAUSED, touching a shuffle pad should START playing
                        print(f"Pin {i} touched: START PLAYBACK and SHUFFLE/NEXT")
                        list_player.play()
                        is_playing = True
                    else:
                        # If PLAYING, touching a shuffle pad shuffles to the next song
                        control_playback(i, list_player)
                        
                # VOLUME PADS (6-11) - Always works
                elif 6 <= i <= 11:
                    control_playback(i, list_player)
                
                # Simple debouncing wait (optional, but prevents rapid fire)
                time.sleep(0.5) 
                
        time.sleep(CHECK_INTERVAL)


if __name__ == '__main__':
    try:
        runExample()
    except (KeyboardInterrupt, SystemExit):
        # --- Cleanup on Exit ---
        if list_player:
            list_player.stop()
        print("\nExiting program.")
        sys.exit(0)
