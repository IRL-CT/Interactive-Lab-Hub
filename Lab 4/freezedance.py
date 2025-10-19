import time
import random
import pygame
import board
import busio
import adafruit_mpr121
import qwiic
import os

# --- Get base folder for music ---
base_path = os.path.dirname(os.path.abspath(__file__))
music_folder = os.path.join(base_path, "music")

# --- Build playlist dynamically ---
playlist = [os.path.join(music_folder, f) for f in sorted(os.listdir(music_folder)) if f.endswith(".mp3")]

if not playlist:
    print("No music files found in 'music' folder!")
    exit()

# --- Initialize I2C ---
i2c = busio.I2C(board.SCL, board.SDA)

# --- Initialize MPR121 capacitive touch sensor ---
mpr121 = adafruit_mpr121.MPR121(i2c)

# --- Initialize VL53L1X distance sensor ---
time.sleep(0.05)
vcnl4040 = qwiic.QwiicVL53L1X()
  # Give sensor time to power up
if not vcnl4040.begin():
    print("VL53L1X not detected. Check wiring.")
    exit()
print("VL53L1X online")

print("MPR121 online")

# --- Initialize pygame for music ---
pygame.mixer.init()
current_song = 0
volume = 0.5
pygame.mixer.music.set_volume(volume)

def play_song(index):
    pygame.mixer.music.load(playlist[index])
    pygame.mixer.music.play(-1)

def shuffle_songs():
    global current_song
    random.shuffle(playlist)
    current_song = 0
    play_song(current_song)
    print("🎵 Playlist shuffled")

def change_volume(delta):
    global volume
    volume = min(1.0, max(0.0, volume + delta))
    pygame.mixer.music.set_volume(volume)
    print(f"Volume set to {volume:.2f}")

# --- Start playback ---
play_song(current_song)
print("Freeze Dance Machine ready!")

# --- Main loop ---
MOTION_THRESHOLD = 2000  # adjust based on environment
last_motion = False

while True:
    # --- Read distance / motion ---
    try:
        vcnl4040.start_ranging()
        time.sleep(0.02)  # short delay to avoid I2C errors
        distance = vcnl4040.get_distance()
        vcnl4040.stop_ranging()
        motion = distance > MOTION_THRESHOLD
    except Exception as e:
        print("Distance sensor error:", e)
        motion = False

    if motion and not last_motion:
        print("Movement detected: Music playing")
        pygame.mixer.music.unpause()
    elif not motion and last_motion:
        print("No movement: Music paused")
        pygame.mixer.music.pause()

    last_motion = motion

    # --- Check capacitive touch inputs ---
    for i in range(12):
        if mpr121[i].value:
            if 0 <= i <= 5:
                shuffle_songs()
            elif 6 <= i <= 8:
                change_volume(-0.1)
            elif 9 <= i <= 11:
                change_volume(+0.1)
            time.sleep(0.3)  # debounce

    time.sleep(0.1)
