import os
import time
import board
import pygame
from adafruit_apds9960.apds9960 import APDS9960

os.environ["SDL_AUDIODRIVER"] = "alsa"

i2c = board.I2C()
apds = APDS9960(i2c)
apds.enable_proximity = True
apds.enable_gesture = True

pygame.mixer.pre_init(44100, -16, 2, 4096)
pygame.mixer.init()

MUSIC_FOLDER = "./music"
PREFERRED_SUFFIXES = ("_fixed.wav", ".ogg", ".wav")

def collect_songs(folder: str):
    found = []
    for suf in PREFERRED_SUFFIXES:
        for f in sorted(os.listdir(folder)):
            if f.lower().endswith(suf):
                found.append(f)
    return found

songs = collect_songs(MUSIC_FOLDER)
if not songs:
    raise Exception(f"No playable audio files found in {MUSIC_FOLDER}")

current_index = 0
playback_state = "Stopped"
last_gesture = "None"

PROXIMITY_CLOSE = 150
PROXIMITY_FAR = 50

def update_status():
    print("\033c", end="")
    print("=== Music Player Status ===")
    print(f"Current Song: {songs[current_index]}")
    print(f"Playback State: {playback_state}")
    print(f"Last Gesture / Action: {last_gesture}")
    print("============================")

def play_song(index):
    global playback_state, current_index, last_gesture
    path = os.path.join(MUSIC_FOLDER, songs[index])
    try:
        pygame.mixer.music.load(path)
        pygame.mixer.music.play()
        playback_state = "Playing"
        current_index = index
        update_status()
    except pygame.error as e:
        print(f"[SKIP] Cannot play {songs[index]} -> {e}")
        nxt = (index + 1) % len(songs)
        if nxt != index:
            last_gesture = "Auto-skip unsupported file"
            play_song(nxt)

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

play_song(current_index)

while True:
    gesture = apds.gesture()
    proximity = apds.proximity

    if gesture == 0x03:
        last_gesture = "Left -> Previous Song"
        play_song((current_index - 1) % len(songs))
    elif gesture == 0x04:
        last_gesture = "Right -> Next Song"
        play_song((current_index + 1) % len(songs))

    if proximity > PROXIMITY_CLOSE:
        if playback_state != "Paused":
            last_gesture = "Near -> Pause"
            pause_song()
    elif proximity < PROXIMITY_FAR:
        if playback_state != "Playing":
            last_gesture = "Far -> Resume"
            resume_song()

    time.sleep(0.2)
