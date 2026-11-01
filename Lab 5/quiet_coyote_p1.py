#coded with assistance of ChatGPT, includes Piper speech, and references handtrackmod.py

import cv2
import math
import shutil
import subprocess
import time
import sys

from datetime import datetime, timedelta
from pathlib import Path

import handtrackmod as htm

import qwiic_button


# ---------- SETTINGS ----------

BASE_DIR = Path(__file__).resolve().parent
MUSIC_FILE = BASE_DIR / "Peaceful_Mind.wav"

CAMERA_INDEX = 0
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480

MUSIC_VOLUME = 50
GESTURE_HOLD_SECONDS = 0.5


# ---------- AUDIO ----------

def start_music():
    return subprocess.Popen(
        [
            "ffplay",
            "-nodisp",
            "-autoexit",
            "-loglevel", "error",
            "-loop", "0",
            "-volume", str(MUSIC_VOLUME),
            str(MUSIC_FILE),
        ],
        stdin=subprocess.DEVNULL,
    )


def stop_audio(process):
    if process is None:
        return

    if process.poll() is None:
        process.terminate()

        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


def prepare_goodnight():
    subprocess.run(
        [
            sys.executable,
            "-m", "piper",
            "-m", "en_US-lessac-medium",
            "-f", str(BASE_DIR / "goodnight.wav"),
            "--",
            "Okay, good night.",
        ],
        cwd=str(BASE_DIR),
        check=True,
    )


def say_goodnight():
    process = subprocess.Popen(
        [
            "ffplay",
            "-nodisp",
            "-autoexit",
            "-loglevel", "error",
            str(BASE_DIR / "goodnight.wav"),
        ],
        stdin=subprocess.DEVNULL,
    )

    try:
        if process.wait() != 0:
            raise RuntimeError("Goodnight playback failed.")
    finally:
        stop_audio(process)

    try:
        return_code = process.wait()

        if return_code != 0:
            raise RuntimeError("Piper speech failed.")
    finally:
        stop_audio(process)


button = qwiic_button.QwiicButton()

if not button.begin():
    raise RuntimeError(
        "Qwiic button not detected. Check its wiring and enable I2C."
    )

button.LED_off()

# ---------- SCHEDULE ----------

def wait_for_music_time():
    while True:
        answer = input(
            "\nEnter bedtime in 24-hour time, such as 23:00.\n"
            "Enter 'now' to test immediately: "
        ).strip()

        if answer.lower() == "now":
            print("Starting now.")
            return

        try:
            bedtime_clock = datetime.strptime(
                answer, "%H:%M"
            ).time()
            break
        except ValueError:
            print("Please enter a time such as 23:00, or now.")

    now = datetime.now()
    bedtime = datetime.combine(now.date(), bedtime_clock)

    # A bedtime that has passed means the next occurrence.
    if bedtime <= now:
        bedtime += timedelta(days=1)

    music_time = bedtime - timedelta(minutes=15)

    print(f"\nPi's current time: {now:%Y-%m-%d %H:%M}")
    print(f"Bedtime: {bedtime:%Y-%m-%d %H:%M}")
    print(f"Music starts: {music_time:%Y-%m-%d %H:%M}")
    print("Press Ctrl+C to cancel.", flush=True)

    while datetime.now() < music_time:
        time.sleep(0.5)


# ---------- HAND GESTURE ----------

def quiet_coyote_detected(landmarks):
    if len(landmarks) < 21:
        return False

    # Your helper returns [landmark ID, x, y].
    points = {
        landmark[0]: (landmark[1], landmark[2])
        for landmark in landmarks
    }

    required_ids = (4, 8, 12, 16, 20)

    if not all(index in points for index in required_ids):
        return False

    def distance(first, second):
        first_x, first_y = points[first]
        second_x, second_y = points[second]

        return math.hypot(
            second_x - first_x,
            second_y - first_y,
        )

    # These are the gesture rules from your original hand_pose.py.
    return (
        distance(4, 8) > 100
        and distance(8, 12) > 100
        and distance(12, 16) < 100
        and distance(16, 20) > 100
        and distance(4, 16) < 100
    )


# ---------- MAIN ROUTINE ----------

def main():
    camera = None
    audio_process = None

    try:
        # Check requirements before waiting until bedtime.
        if not MUSIC_FILE.is_file():
            raise FileNotFoundError(
                f"Music file not found: {MUSIC_FILE}"
            )

        for command in ("ffplay"):
            if shutil.which("ffplay") is None:
                raise RuntimeError(
                    "Missing ffplay. Run: sudo apt install ffmpeg"
                )

        print("Preparing Piper's goodnight response...", flush=True)
        prepare_goodnight()

        wait_for_music_time()

        camera = cv2.VideoCapture(CAMERA_INDEX)
        camera.set(
            cv2.CAP_PROP_FRAME_WIDTH,
            CAMERA_WIDTH,
        )
        camera.set(
            cv2.CAP_PROP_FRAME_HEIGHT,
            CAMERA_HEIGHT,
        )

        if not camera.isOpened():
            raise RuntimeError(
                "Could not open the camera. Check its connection "
                "and close other programs using it."
            )

        # Your handtrackmod.py must contain the corrected
        # MediaPipe Hands call using keyword arguments.
        detector = htm.handDetector(detectionCon=0.7)

        audio_process = start_music()

        print("\nMusic is playing.", flush=True)
        print("Camera is active; no preview window is needed.")
        print(
            "Hold quiet coyote for one second to stop the music."
        )
        print("Press Ctrl+C to quit.", flush=True)

        gesture_started = None
        gesture_confirmed = False
        previous_pose_detected = False

        while True:
            if audio_process.poll() is not None:
                raise RuntimeError(
                    "Music playback stopped unexpectedly. "
                    "Check Peaceful_Mind.wav and your audio output."
                )

            success, image = camera.read()

            if not success or image is None:
                raise RuntimeError(
                    "Could not read a frame from the camera."
                )

            image = detector.findHands(image, draw=True)
            landmarks = detector.findPosition(
                image, draw=False
            )

            pose_detected = quiet_coyote_detected(landmarks)

            if pose_detected:
                if gesture_started is None:
                    gesture_started = time.monotonic()
                    print(
                        "Quiet coyote detected. Keep holding...",
                        flush=True,
                    )

                held_for = (
                    time.monotonic() - gesture_started
                )

                if held_for >= GESTURE_HOLD_SECONDS:
                    gesture_confirmed = True
                    break

            else:
                if previous_pose_detected:
                    print(
                        "Pose lost. Try holding it again.",
                        flush=True,
                    )

                gesture_started = None

            previous_pose_detected = pose_detected

            # No imshow(), waitKey(), or desktop display required.
            cv2.imshow("Bedtime Camera", image)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

        music_pid = audio_process.pid
       
        stop_audio(audio_process)

        print(
            f"Music player {music_pid} stopped. "
            f"Exit code: {audio_process.returncode}",
            flush=True,
        )

        audio_process = None

        camera.release()
        camera = None

        if gesture_confirmed:
            print("\nGesture confirmed. Music stopped.", flush=True)

            say_goodnight()

            button.LED_config(
                brightness=30,    # Dim maximum brightness (0–255)
                cycle_time=3000,  # Slow 3-second pulse
                off_time=0,       # No pause between pulses
                granularity=1,
            )
            
            print("Red LED is glowing.")

            print(
                "Phase 1 complete. Camera released.",
                flush=True,
            )

    except KeyboardInterrupt:
        print("\nStopped by user.", flush=True)

    finally:
        stop_audio(audio_process)

        if camera is not None:
            camera.release()

        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
