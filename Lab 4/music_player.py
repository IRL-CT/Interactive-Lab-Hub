import board
import os
import time
import subprocess
from adafruit_apds9960.apds9960 import APDS9960

# Initialize I2C and sensor
i2c = board.I2C()
apds = APDS9960(i2c)
apds.enable_proximity = True
apds.enable_gesture = True

# Music folder
MUSIC_FOLDER = "./music"  # Adjust path if needed
songs = [f for f in os.listdir(MUSIC_FOLDER) if f.lower().endswith(".mp3")]
songs.sort()
if not songs:
    raise Exception(f"No mp3 files found in {MUSIC_FOLDER}")

current_index = 0
player_process = None
playback_state = "Playing"
last_gesture = "None"

def play_song(index):
    global player_process, playback_state
    if player_process:
        player_process.terminate()
    song_path = os.path.join(MUSIC_FOLDER, songs[index])
    player_process = subprocess.Popen(["mpg123", "-q", song_path])
    playback_state = "Playing"
    update_status()

def pause_song():
    global player_process, playback_state
    if player_process:
        player_process.terminate()
        player_process = None
    playback_state = "Paused"
    update_status()

def resume_song():
    global playback_state
    play_song(current_index)
    playback_state = "Playing"
    update_status()

def update_status():
    # Clear the terminal line and print updated status
    print("\033c", end="")  # Clear screen
    print(f"=== Music Player Status ===")
    print(f"Current Song: {songs[current_index]}")
    print(f"Playback State: {playback_state}")
    print(f"Last Gesture: {last_gesture}")
    print("============================")

# Start first song
play_song(current_index)

while True:
    gesture = apds.gesture()
    proximity = apds.proximity

    # Gesture control
    if gesture == 0x03:  # Left
        current_index = (current_index - 1) % len(songs)
        last_gesture = "Left -> Previous Song"
        play_song(current_index)
    elif gesture == 0x04:  # Right
        current_index = (current_index + 1) % len(songs)
        last_gesture = "Right -> Next Song"
        play_song(current_index)

    # Proximity control
    if proximity > 200:  # Too close
        last_gesture = "Near -> Pause"
        pause_song()
    elif proximity < 50:  # Far away
        last_gesture = "Far -> Resume"
        if playback_state != "Playing":
            resume_song()

    time.sleep(0.2)
