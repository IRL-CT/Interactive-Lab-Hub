import os
import time
import board
import pygame
import subprocess
from adafruit_apds9960.apds9960 import APDS9960
from sparkfun_qwiic_button import QwiicButton

# -------------------------------
# SDL audio driver for Raspberry Pi
# -------------------------------
os.environ["SDL_AUDIODRIVER"] = "alsa"

# -------------------------------
# Helper: Ensure WAV is PCM format
# -------------------------------
def ensure_pcm_wav(filepath):
    """Convert WAV to standard PCM if pygame can't play it."""
    fixed_path = filepath.replace(".wav", "_pygame.wav")
    if os.path.exists(fixed_path):
        return fixed_path
    try:
        subprocess.run([
            "ffmpeg", "-y", "-i", filepath,
            "-acodec", "pcm_s16le", "-ar", "44100", fixed_path
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"Converted {os.path.basename(filepath)} -> {os.path.basename(fixed_path)}")
        return fixed_path
    except Exception as e:
        print(f"Conversion failed for {filepath}: {e}")
        return filepath

# -------------------------------
# Initialize APDS-9960 sensor
# -------------------------------
i2c = board.I2C()
apds = APDS9960(i2c)
apds.enable_proximity = True
apds.enable_gesture = True

# -------------------------------
# Initialize Qwiic Button
# -------------------------------
button = QwiicButton()
if not button.begin():
    print("Button not detected. Check wiring!")
else:
    print("Qwiic Button connected!")

# -------------------------------
# Initialize pygame mixer
# -------------------------------
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=4096)

# -------------------------------
# Load music files
# -------------------------------
MUSIC_FOLDER = "./music"
songs = [
    f for f in os.listdir(MUSIC_FOLDER)
    if f.lower().endswith(".wav")
    and all(x not in f.lower() for x in ["_pcm", "_pygame"])
]
songs.sort()

if not songs:
    raise Exception(f"No wav files found in {MUSIC_FOLDER}")

current_index = 0
playback_state = "Playing"
last_gesture = "None"

# -------------------------------
# Helper functions
# -------------------------------
def play_song(index):
    global playback_state
    original_path = os.path.join(MUSIC_FOLDER, songs[index])
    safe_path = ensure_pcm_wav(original_path)
    pygame.mixer.music.load(safe_path)
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
    print("\033c", end="")  # Clear terminal
    print("=== Music Player Status ===")
    print(f"Current Song: {songs[current_index]}")
    print(f"Playback State: {playback_state}")
    print(f"Last Gesture / Action: {last_gesture}")
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

    # Gesture control
    if gesture == 0x03:  # Left swipe
        current_index = (current_index - 1) % len(songs)
        last_gesture = "Left -> Previous Song"
        play_song(current_index)

    elif gesture == 0x04:  # Right swipe
        current_index = (current_index + 1) % len(songs)
        last_gesture = "Right -> Next Song"
        play_song(current_index)

    # Button control (pause/resume)
    if button.is_button_pressed():
        if playback_state == "Playing":
            last_gesture = "Button -> Pause"
            pause_song()
        else:
            last_gesture = "Button -> Resume"
            resume_song()
        time.sleep(0.5)  

    time.sleep(0.1)
