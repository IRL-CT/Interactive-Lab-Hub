import board
import os
import time
import pygame
from adafruit_apds9960.apds9960 import APDS9960

# -------------------------------
# Initialize sensor
# -------------------------------
i2c = board.I2C()
apds = APDS9960(i2c)
apds.enable_proximity = True
apds.enable_gesture = True

# -------------------------------
# Initialize pygame mixer
# -------------------------------
pygame.mixer.init()
MUSIC_FOLDER = "./music"  # adjust to your folder
songs = [f for f in os.listdir(MUSIC_FOLDER) if f.lower().endswith(".mp3")]
songs.sort()

if not songs:
    raise Exception(f"No mp3 files found in {MUSIC_FOLDER}")

current_index = 0
playback_state = "Playing"
last_gesture = "None"

# -------------------------------
# Helper functions
# -------------------------------
def play_song(index):
    global playback_state
    pygame.mixer.music.load(os.path.join(MUSIC_FOLDER, songs[index]))
    pygame.mixer.music.play()
    playback_state = "Playing"
    update_status()

def pause_song():
    global playback_state
    pygame.mixer.music.pause()
    playback_state = "Paused"
    update_status()

def resume_song():
    global playback_state
    pygame.mixer.music.unpause()
    playback_state = "Playing"
    update_status()

def update_status():
    print("\033c", end="")  # clear terminal
    print("=== Music Player Status ===")
    print(f"Current Song: {songs[current_index]}")
    print(f"Playback State: {playback_state}")
    print(f"Last Gesture: {last_gesture}")
    print("============================")

# -------------------------------
# Start first song
# -------------------------------
play_song(current_index)

# -------------------------------
# Main loop
# -------------------------------
while True:
    gesture = apds.gesture()
    proximity = apds.proximity

    # -------------------------------
    # Gesture control
    # -------------------------------
    if gesture == 0x03:  # Left swipe
        current_index = (current_index - 1) % len(songs)
        last_gesture = "Left -> Previous Song"
        play_song(current_index)

    elif gesture == 0x04:  # Right swipe
        current_index = (current_index + 1) % len(songs)
        last_gesture = "Right -> Next Song"
        play_song(current_index)

    # -------------------------------
    # Proximity control
    # -------------------------------
    if proximity > 100:  # adjust threshold as needed
        if playback_state != "Paused":
            last_gesture = "Near -> Pause"
            pause_song()
    elif proximity < 30:
        if playback_state != "Playing":
            last_gesture = "Far -> Resume"
            resume_song()

    time.sleep(0.2)
