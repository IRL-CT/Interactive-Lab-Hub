# This script integrates a SparkFun Qwiic Proximity Sensor (VCNL4040)
# and an Adafruit I2C Rotary Encoder (seesaw) to control video playback.
#
# Proximity sensor controls: Play/Pause based on motion.
# Rotary Encoder controls: Volume adjustment (turn) and Mute toggle (press).
import time
import sys
import os
import statistics
import vlc
import yt_dlp
import board
from adafruit_seesaw import seesaw, rotaryio, digitalio
import qwiic_proximity

# ------------------- CONFIG -------------------
YOUTUBE_URL = "https://youtu.be/EPo5wWmKEaI?si=P4iQHYS6ml0Li500"
TEMP_FILE = "/tmp/video.mp4"

SAMPLE_WINDOW = 10
MOVEMENT_THRESHOLD = 5
CHECK_INTERVAL = 0.4

VOLUME_STEP = 2  # how much volume changes per encoder tick
# ------------------------------------------------


def download_video(url):
    """Download YouTube video to a local MP4 file using yt_dlp."""
    print("Downloading video to /tmp/video.mp4 ... (this may take ~30s)")
    ydl_opts = {
        'quiet': False,
        'format': 'best[ext=mp4]/best',
        'outtmpl': TEMP_FILE,
        'noplaylist': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return TEMP_FILE


# def setup_rotary_encoder():
#     """Initialize Seesaw rotary encoder and button."""
#     ss = seesaw.Seesaw(board.I2C(), addr=0x71)

#     ss_product = (ss.get_version() >> 16) & 0xFFFF
#     print("Found Seesaw product {}".format(ss_product))
#     if ss_product != 4991:
#         print("Warning: expected 4991 firmware, got {}".format(ss_product))

#     ss.pin_mode(24, ss.INPUT_PULLUP)
#     button = digitalio.DigitalIO(ss, 24)
#     encoder = rotaryio.IncrementalEncoder(ss)

#     return ss, encoder, button


def runExample():
    print("\n=== SparkFun VCNL4040 + Rotary Encoder VLC Controller ===\n")
    # --- Setup Proximity Sensor ---
    oProx = qwiic_proximity.QwiicProximity()
    if not oProx.connected:
        print("The Qwiic Proximity device isn't connected. Please check your connection.", file=sys.stderr)
        return
    oProx.begin()

    # # --- Setup Rotary Encoder ---
    # ss, encoder, button = setup_rotary_encoder()
    # button_held = False
    # last_position = encoder.position

    # --- Prepare Video ---
    if not os.path.exists(TEMP_FILE):
        video_path = download_video(YOUTUBE_URL)
    else:
        video_path = TEMP_FILE
        print("Using cached video:", video_path)

    print("Starting VLC player...")
    player = vlc.MediaPlayer(video_path)
    player.play()
    time.sleep(5)

    # Initial volume
    volume = 50
    player.audio_set_volume(volume)
    print(f"Initial volume set to {volume}")

    readings = []
    is_playing = True
    is_muted = False

    while True:
        # --- Proximity Sensor Logic ---
        proxValue = oProx.get_proximity()
        print(f"Proximity Value: {proxValue}")

        readings.append(proxValue)
        if len(readings) > SAMPLE_WINDOW:
            readings.pop(0)

        if len(readings) >= SAMPLE_WINDOW:
            variation = statistics.stdev(readings)
            print(f"Variation: {variation:.2f}")

            if variation > MOVEMENT_THRESHOLD:
                if not is_playing:
                    print("Movement detected: PLAY")
                    player.play()
                    is_playing = True
            else:
                if is_playing:
                    print("Stable distance: PAUSE")
                    player.pause()
                    is_playing = False

        # # --- Rotary Encoder Logic ---
        # position = encoder.position
        # if position != last_position:
        #     delta = position - last_position
        #     last_position = position
        #     volume = max(0, min(100, volume + delta * VOLUME_STEP))
        #     player.audio_set_volume(volume)
        #     print(f"Volume changed to {volume}")

        # # --- Button Logic ---
        # if not button.value and not button_held:
        #     button_held = True
        #     is_muted = not is_muted
        #     player.audio_toggle_mute()
        #     print("Button pressed → Mute toggled:", is_muted)

        # if button.value and button_held:
        #     button_held = False
        #     print("Button released")

        # time.sleep(CHECK_INTERVAL)


if __name__ == '__main__':
    try:
        runExample()
    except (KeyboardInterrupt, SystemExit):
        print("\nExiting program. Cleaning up temporary file.")
        try:
            if os.path.exists(TEMP_FILE):
                os.remove(TEMP_FILE)
                print("Deleted:", TEMP_FILE)
        except Exception as e:
            print("Could not delete temp file:", e)
        sys.exit(0)
