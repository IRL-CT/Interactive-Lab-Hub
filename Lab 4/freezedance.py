import time
import random
import pygame
import board
import busio
import adafruit_mpr121
import qwiic

# --- Initialize I2C ---
i2c = busio.I2C(board.SCL, board.SDA)

# --- Initialize sensors ---
# MPR121 capacitive touch
mpr121 = adafruit_mpr121.MPR121(i2c)

# VL53L1X / VCNL4040 distance sensor
vcnl4040 = qwiic.QwiicVL53L1X()
if vcnl4040.sensor_init() is None:
    print("✅ VCNL4040 / VL53L1X sensor online!")
else:
    print("❌ VCNL4040 / VL53L1X not detected, check wiring.")
    exit()

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
    print("🎵 Playlist shuffled!")

def change_volume(delta):
    global volume
    volume = min(1.0, max(0.0, volume + delta))
    pygame.mixer.music.set_volume(volume)
    print(f"🔊 Volume set to {volume:.2f}")

# --- Start playback ---
play_song(current_song)
print("🕺 Freeze Dance Machine ready!")

# --- Main Loop ---
MOTION_THRESHOLD = 2000  # Adjust based on environment
last_motion = False

while True:
    # --- Read distance/motion ---
    try:
        vcnl4040.start_ranging()
        time.sleep(0.005)
        distance = vcnl4040.get_distance()  # mm
        vcnl4040.stop_ranging()
        motion = distance > MOTION_THRESHOLD
    except Exception as e:
        print("Distance sensor error:", e)
        motion = False

    if motion and not last_motion:
        print("🟢 Movement detected: Music playing")
        pygame.mixer.music.unpause()
    elif not motion and last_motion:
        print("🔴 No movement: Music paused")
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
