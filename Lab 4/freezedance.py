import adafruit_mpr121
from adafruit_apds9960.apds9960 import APDS9960
import qwiic
import time
import random
import pygame

# --- Initialize sensors ---
vcnl4040 = qwiic.QwiicVL53L1X()
mpr121 = qwiic_mpr121.QwiicMPR121()

if not vcnl4040.is_connected():
    print("VCNL4040 not connected. Check wiring.")
    exit()

if not mpr121.is_connected():
    print("MPR121 not connected. Check wiring.")
    exit()

vcnl4040.begin()
mpr121.begin()

print("Sensors initialized successfully")

# --- Initialize pygame for music ---
pygame.mixer.init()

playlist = [
    "/music/song1.mp3",
    "/music/song2.mp3",
    "/music/song3.mp3",
    "/music/song4.mp3",
    "/music/song5.mp3"
]

current_song = 0
volume = 0.5
pygame.mixer.music.set_volume(volume)

def play_song(index):
    pygame.mixer.music.load(playlist[index])
    pygame.mixer.music.play(-1)

def stop_song():
    pygame.mixer.music.stop()

def shuffle_songs():
    global current_song
    random.shuffle(playlist)
    current_song = 0
    play_song(current_song)
    print("Playlist shuffled")

def change_volume(delta):
    global volume
    volume = min(1.0, max(0.0, volume + delta))
    pygame.mixer.music.set_volume(volume)
    print(f"Volume set to {volume:.2f}")

# --- Start playback ---
play_song(current_song)
print("Freeze Dance Machine ready!")

# --- Main Loop ---
MOTION_THRESHOLD = 2000  # adjust as needed
last_motion = False

while True:
    # --- Read distance/motion ---
    proximity = vcnl4040.get_proximity()
    motion = proximity > MOTION_THRESHOLD

    if motion and not last_motion:
        print("Movement detected: Music playing")
        pygame.mixer.music.unpause()
    elif not motion and last_motion:
        print("No movement: Music paused")
        pygame.mixer.music.pause()

    last_motion = motion

    # --- Check touch inputs ---
    touch_status = mpr121.get_touched()

    for i in range(12):
        if touch_status & (1 << i):  # bitmask check
            if 0 <= i <= 5:
                shuffle_songs()
            elif 6 <= i <= 8:
                change_volume(-0.1)
            elif 9 <= i <= 11:
                change_volume(+0.1)
            time.sleep(0.3)  # debounce delay

    time.sleep(0.1)
