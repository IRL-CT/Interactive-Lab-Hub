
import qwiic_proximity
import time
import sys
import statistics
import vlc
import yt_dlp
import os

YOUTUBE_URL = "https://youtu.be/EPo5wWmKEaI?si=P4iQHYS6ml0Li500"
TEMP_FILE = "/tmp/video.mp4"
SAMPLE_WINDOW = 10
MOVEMENT_THRESHOLD = 5
CHECK_INTERVAL = 0.4


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

def disco():
    """Random LED flashing"""
    for _ in range(12):
        ld = random.choice(leds)
        ld.value = False
        time.sleep(0.08)
        ld.value = True


def runExample():
    print("\nSparkFun VCNL4040 Proximity Sensor + VLC (Local Playback Mode)\n")
    oProx = qwiic_proximity.QwiicProximity()

    if not oProx.connected:
        print("The Qwiic Proximity device isn't connected. Please check your connection.", file=sys.stderr)
        return

    oProx.begin()

    # Step 1: Ensure we have the video locally
    if not os.path.exists(TEMP_FILE):
        video_path = download_video(YOUTUBE_URL)
    else:
        video_path = TEMP_FILE
        print("Using cached video:", video_path)

    # Step 2: Play it with VLC
    print("Starting VLC player...")
    player = vlc.MediaPlayer(video_path)
    player.play()
    time.sleep(5)

    readings = []
    is_playing = True

    while True:
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
                    disco()
                    player.play()
                    is_playing = True
            else:
                if is_playing:
                    print("Stable distance: PAUSE")
                    player.pause()
                    is_playing = False

        time.sleep(CHECK_INTERVAL)


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
