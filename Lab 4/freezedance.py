import time
import random
import board
import busio
import pygame
from adafruit_vcnl4040 import VCNL4040
import adafruit_mpr121

# --- Setup I2C ---
i2c = busio.I2C(board.SCL, board.SDA)

# --- Initialize sensors ---
vcnl4040 = VCNL4040(i2c)
mpr121 = adafruit_mpr121.MPR121(i2c)

# --- Initialize Pygame for music ---
pygame.mixer.init()

# Your playlist
playlist = [
    "/home/pi/Music/song1.mp3",
    "/home/pi/Music/song2.mp3",
    "/home/pi/Music/song3.mp3"
]
current_song = 0
volume = 0.5
pygame.mixer.music.set_volume(volume)

# --- Helper functions ---
def play_song(index):
    pygame.mixer.music.load(playlist[index])
    pygame.mixer.music.play(-1)  # loop

def stop_song():
    pygame.mixer.music.stop()

def shuffle_songs():
    global current_song
    random.shuffle(playlist)
    current_song = 0
    play_song(current_song)

def change_volume(delta):
    global volume
    volume = min(1.0, max(0.0, volume + delta))
    pygame.mixer.music.set_volume(volume)
    print(f"Volume: {volume:.2f}")

# --- Start music system ---
play_song(current_song)
print("Freeze Dance Machine running! Move to play, stop when still...")

# --- Main Loop ---
MOTION_THRESHOLD = 2000  # adjust based on sensor sensitivity
last_motion = False

while True:
    # Read distance / motion
    prox = vcnl4040.proximity
    motion = prox > MOTION_THRESHOLD

    # Freeze Dance Logic
    if motion and not last_motion:
        print("Movement detected! Playing music...")
        pygame.mixer.music.unpause()
    elif not motion and last_motion:
        print("No movement! Pausing music...")
        pygame.mixer.music.pause()

    last_motion = motion

    # --- Touch Controls ---
    for i in range(12):
        if mpr121[i].value:
            if 0 <= i <= 5:
                print(f"Touch {i} → Shuffle playlist")
                shuffle_songs()
            elif 6 <= i <= 8:
                print(f"Touch {i} → Lower volume")
                change_volume(-0.1)
            elif 9 <= i <= 11:
                print(f"Touch {i} → Raise volume")
                change_volume(+0.1)
            time.sleep(0.3)  # debounce

    time.sleep(0.1)
