"""
Part G: the hand-off. Show an open palm to the camera and hold it for 1.5 seconds:
the screen shows "watching tonight" and the speaker says it too (Piper + sounddevice, as in Lab 4), then you
get a countdown to switch off the light, and then overnight.py starts.

    python start_night.py                    # window with a progress bar (VNC)
    python start_night.py --headless         # no window, over plain ssh
    python start_night.py --snaps --interval 10    # anything else is passed on to overnight.py
    python start_night.py --hold 1.5 --delay 20      # hold the palm 1.5 s, 20 s to switch off the light
    python start_night.py --say "Sleep well."      # change what it says

An open palm is easy to tell from a resting hand and from most things on a bed, and it needs no
tuning in the dark once the lamp is on. The thresholds below are a first guess: try them with
your own hand and change them.
"""
import argparse
import math
import os
import pathlib
import sys
import time

from screen import Screen

FINGER_OPEN = 1.5      # a finger counts as open if its tip is this many palm-sizes from the wrist
THUMB_OPEN = 1.0       # the thumb is open if its tip is this many palm-sizes from the base of the pinky


VOICE_MODEL = pathlib.Path(__file__).resolve().parent.parent / "Lab 3" / "voices" / "en_US-lessac-medium.onnx"
SPEAKER_GAIN = 1.2     # same as Lab 4


def speak(text, voice_model=VOICE_MODEL):
    """Say `text` through the speaker the way Lab 4 does: Piper in Python, played with sounddevice.
    Returns False (and the screen still says it) if something is missing, so the hand-off never
    breaks; the reason is printed."""
    try:
        import numpy as np
        import sounddevice as sd
        from piper import PiperVoice
        voice = PiperVoice.load(str(voice_model))
        for chunk in voice.synthesize(text):
            samples = np.frombuffer(chunk.audio_int16_bytes, dtype=np.int16)
            louder = np.clip(samples.astype(np.float32) * SPEAKER_GAIN, -32768, 32767).astype(np.int16)
            sd.play(louder, samplerate=chunk.sample_rate)
            sd.wait()
        return True
    except Exception as e:                              # missing package, voice file or sound device
        print(f"could not speak: {e!r}", flush=True)
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
    parser.add_argument("--hold", type=float, default=1.5, help="seconds the palm must stay open")
    parser.add_argument("--delay", type=float, default=20, help="seconds to switch off the light before watching starts")
    parser.add_argument("--headless", action="store_true", help="do not open a window")
    parser.add_argument("--say", default="Watching tonight. Good night.", help="what the device says when it accepts the hand-off")
    parser.add_argument("--voice", default=str(VOICE_MODEL), help="the Piper voice file from Lab 3")
    args, overnight_args = parser.parse_known_args()

    import cv2
    import HandTrackingModule as htm

    show = not args.headless and not (sys.platform.startswith("linux") and not os.environ.get("DISPLAY"))
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    detector = htm.handDetector(detectionCon=0)
    print("show an open palm to the camera and hold it", flush=True)

    screen = Screen()                                   # the Mini PiTFT; does nothing if it is not available
    screen.bar("Show an open palm", 0)
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
        screen.bar("Hold your palm", held / args.hold)
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
    screen.text("Watching tonight", "Good night", color="#00FF00")
    speak(args.say, args.voice)                         # ... and so does the speaker
    for left in range(int(args.delay), 0, -1):          # time to switch off the light
        screen.text("Watching tonight", f"Light off: {left} s")
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
    screen.off()                                        # a dark room: overnight.py keeps the screen off
    os.execvp(sys.executable, [sys.executable, "overnight.py", *overnight_args])


if __name__ == "__main__":
    main()
