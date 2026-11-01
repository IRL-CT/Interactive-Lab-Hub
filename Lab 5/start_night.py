"""
Part G: the hand-off. Show an open palm to the camera and hold it for two seconds:
the screen shows "watching tonight" and the speaker says it too (Piper, as in Lab 3), then you
get a countdown to switch off the light, and then overnight.py starts.

    python start_night.py                    # window with a progress bar (VNC)
    python start_night.py --headless         # no window, over plain ssh
    python start_night.py --snaps --interval 10    # anything else is passed on to overnight.py
    python start_night.py --hold 3 --delay 20      # hold the palm 3 s, 20 s to switch off the light
    python start_night.py --say "Sleep well."      # change what it says

An open palm is easy to tell from a resting hand and from most things on a bed, and it needs no
tuning in the dark once the lamp is on. The thresholds below are a first guess: try them with
your own hand and change them.
"""
import argparse
import math
import os
import pathlib
import subprocess
import sys
import time

FINGER_OPEN = 1.5      # a finger counts as open if its tip is this many palm-sizes from the wrist
THUMB_OPEN = 1.0       # the thumb is open if its tip is this many palm-sizes from the base of the pinky


VOICES_DIR = pathlib.Path(__file__).resolve().parent.parent / "Lab 3" / "voices"     # the voice you downloaded in Lab 3
VOICE = "en_US-lessac-medium"


def speak(text, voices_dir=VOICES_DIR):
    """Say `text` through the speaker with Piper, as in Lab 3. Returns False (and the screen
    still says it) if Piper, aplay or the voice is missing, so the hand-off never breaks."""
    try:
        tts = subprocess.Popen(
            [sys.executable, "-m", "piper", "--model", VOICE, "--data-dir", str(voices_dir),
             "--output-raw", "--", text],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        play = subprocess.Popen(["aplay", "-q", "-r", "22050", "-f", "S16_LE", "-t", "raw", "-"],
                                stdin=tts.stdout, stderr=subprocess.DEVNULL)
        tts.stdout.close()
        play.wait()
        return tts.wait() == 0 and play.returncode == 0
    except OSError as e:
        print("could not speak:", e, flush=True)
        return False


def dist(a, b):
    return math.hypot(a[1] - b[1], a[2] - b[2])


def is_open_palm(lm):
    """lm is the list from handDetector.findPosition: [[id, x, y], ...], 21 landmarks."""
    if len(lm) < 21:
        return False
    palm = dist(lm[0], lm[9])                          # wrist to the base of the middle finger
    if palm == 0:
        return False
    fingers_open = all(dist(lm[0], lm[tip]) > FINGER_OPEN * palm for tip in (8, 12, 16, 20))
    thumb_open = dist(lm[4], lm[17]) > THUMB_OPEN * palm
    return fingers_open and thumb_open


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--hold", type=float, default=2, help="seconds the palm must stay open")
    parser.add_argument("--delay", type=float, default=30, help="seconds to switch off the light before watching starts")
    parser.add_argument("--headless", action="store_true", help="do not open a window")
    parser.add_argument("--say", default="Watching tonight. Good night.", help="what the device says when it accepts the hand-off")
    parser.add_argument("--voices", default=str(VOICES_DIR), help="folder with the Piper voice from Lab 3")
    args, overnight_args = parser.parse_known_args()

    import cv2
    import HandTrackingModule as htm

    show = not args.headless and not (sys.platform.startswith("linux") and not os.environ.get("DISPLAY"))
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    detector = htm.handDetector(detectionCon=0.7)
    print("show an open palm to the camera and hold it", flush=True)

    palm_since = None
    while True:
        ok, img = cap.read()
        if not ok:
            time.sleep(0.2)
            continue
        img = detector.findHands(img, draw=show)
        lm = detector.findPosition(img, draw=False)
        if is_open_palm(lm):
            palm_since = palm_since or time.time()
            held = time.time() - palm_since
        else:
            palm_since, held = None, 0
        if held >= args.hold:
            break
        if show:
            cv2.rectangle(img, (20, 440), (20 + int(300 * held / args.hold), 465), (0, 200, 0), cv2.FILLED)
            cv2.rectangle(img, (20, 440), (320, 465), (255, 255, 255), 2)
            cv2.putText(img, "open palm: tonight, watch me", (20, 430), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.imshow("start night", img)
            if cv2.waitKey(1) == ord("q"):
                cap.release()
                cv2.destroyAllWindows()
                return
        else:
            time.sleep(0.1)

    print(f"watching tonight: starting in {args.delay:g} s, switch off the light", flush=True)
    if show:                                            # the screen says it ...
        img[:] = (0, 0, 0)
        cv2.putText(img, "watching tonight", (150, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.imshow("start night", img)
        cv2.waitKey(1)
    speak(args.say, args.voices)                        # ... and so does the speaker
    for left in range(int(args.delay), 0, -1):          # time to switch off the light
        if show:
            img[:] = (0, 0, 0)
            cv2.putText(img, "watching tonight", (150, 220), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            cv2.putText(img, f"switch off the light: {left} s", (130, 270), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (180, 180, 180), 2)
            cv2.imshow("start night", img)
            cv2.waitKey(1000)
        else:
            time.sleep(1)
    cap.release()                                       # overnight.py needs the camera
    cv2.destroyAllWindows()
    os.execvp(sys.executable, [sys.executable, "overnight.py", *overnight_args])


if __name__ == "__main__":
    main()
