# music_player.py
# Compatible with Raspberry Pi + APDS9960
# Supports gesture control and proximity-based pause/resume
# Auto-converts WAVs to PCM if needed for pygame

import os
import time
import pygame
import board
import subprocess
from adafruit_apds9960.apds9960 import APDS9960

# === CONFIG ===
MUSIC_FOLDER = "/home/pi/Interactive-Lab-Hub/Lab 4/music"
PROX_CLOSE = 150     # adjust based on your sensor values
PROX_FAR = 50
GESTURE_DELAY = 0.5  # seconds

# === INIT SENSORS ===
i2c = board.I2C()
apds = APDS9960(i2c)
apds.enable_proximity = True
apds.enable_gesture = True

# === INIT PYGAME ===
pygame.mixer.init()

# === WAV CONVERSION ===
def convert_wav_to_pcm(filepath):
    """Ensure WAV is in PCM format for pygame."""
    fixed_path = filepath.replace(".wav", "_pcm.wav")
    if os.path.exists(fixed_path):
        return fixed_path
    try:
        subprocess.run([
            "ffmpeg", "-y", "-i", filepath,
            "-acodec", "pcm_s16le", "-ar", "44100", fixed_path
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"Converted to PCM: {os.path.basename(fixed_path)}")
        return fixed_path
    except Exception as e:
        print(f"Failed to convert {filepath}: {e}")
        return filepath

# === LOAD SONGS ===
songs = []
for f in os.listdir(MUSIC_FOLDER):
    if f.lower().endswith(".wav"):
        path = os.path.join(MUSIC_FOLDER, f)
        pcm_path = convert_wav_to_pcm(path)
        songs.append(os.path.basename(pcm_path))

if not songs:
    print("No WAV files found!")
    exit(1)

# === PLAYER STATE ===
current_index = 0
playback_state = "Stopped"
last_action = "None"

def play_song(index):
    global playback_state, last_action
    pygame.mixer.music.load(os.path.join(MUSIC_FOLDER, songs[index]))
    pygame.mixer.music.play()
    playback_state = "Playing"
    last_action = "Started"
    update_status()

def update_status():
    os.system('clear')
    print("=== Music Player Status ===")
    print(f"Current Song: {songs[current_index]}")
    print(f"Playback State: {playback_state}")
    print(f"Last Gesture / Action: {last_action}")
    print("============================")

def next_song():
    global current_index, last_action
    current_index = (current_index + 1) % len(songs)
    play_song(current_index)
    last_action = "Next Song"

def prev_song():
    global current_index, last_action
    current_index = (current_index - 1) % len(songs)
    play_song(current_index)
    last_action = "Previous Song"

# === START ===
play_song(current_index)

last_gesture_time = time.time()
while True:
    # --- Gesture control ---
    gesture = apds.gesture()
    if gesture == 0x01 and time.time() - last_gesture_time > GESTURE_DELAY:
        next_song()
        last_gesture_time = time.time()
    elif gesture == 0x02 and time.time() - last_gesture_time > GESTURE_DELAY:
        prev_song()
        last_gesture_time = time.time()

    # --- Proximity control ---
    proximity = apds.proximity
    if proximity > PROX_CLOSE and playback_state != "Paused":
        pygame.mixer.music.pause()
        playback_state = "Paused"
        last_action = "Near -> Pause"
        update_status()
    elif proximity < PROX_FAR and playback_state == "Paused":
        pygame.mixer.music.unpause()
        playback_state = "Playing"
        last_action = "Far -> Resume"
        update_status()

    time.sleep(0.1)
