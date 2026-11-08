"""
Telephone Charades: check this Pi's parts before playing. Takes about 30 seconds.

    python check.py                 # everything
    python check.py --skip mic      # skip a part (screen, button, camera, mic, voice, broker)

It shows a test on the PiTFT, waits for a button press, records 2 s from the webcam (saved as
check_camera.jpg), records 3 s from the mic and transcribes it, says a sentence, and connects
to the class MQTT broker. Each part prints OK or what to fix.
"""
import argparse
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import hardware  # noqa: E402
from common import Bus  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
results = []


def report(part, ok, detail):
    results.append((part, ok, detail))
    print(f"  {'OK  ' if ok else 'FIX '} {part:<7} {detail}", flush=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--skip", default="", help="comma-separated parts to skip")
    ap.add_argument("--mic-device", default="default")
    ap.add_argument("--camera", type=int, default=0)
    args = ap.parse_args()
    skip = {s.strip() for s in args.skip.split(",") if s.strip()}
    print("Checking this Pi for Telephone Charades...\n")

    screen = hardware.TerminalScreen()
    if "screen" not in skip:
        screen = hardware.make_screen("auto")
        if isinstance(screen, hardware.PitftScreen):
            screen.show("CHECK", "hello!", "this is the PiTFT", "ok")
            report("screen", True, "PiTFT shows 'hello!'")
        else:
            report("screen", False, "no PiTFT (sudo systemctl stop piscreen.service, then try again)")

    if "button" not in skip:
        button = hardware.Button("auto")
        if button.kind in ("qwiic", "pitft"):
            screen.show("CHECK", "press the button", "within 10 s", "act")
            print("     press the button now (10 s)...", flush=True)
            got = button.wait(10)
            report("button", bool(got), f"{button.kind}: got a {got}" if got else f"{button.kind} found, but no press in 10 s")
        else:
            report("button", False, "no Qwiic Button (i2cdetect -y 1 should show 6f) and no PiTFT buttons; "
                                    "you can still use the laptop page")

    if "camera" not in skip:
        try:
            cam = hardware.Camera(args.camera)
            cam.open()
            cam.warm(1.0)
            frames = cam.record(2, 5)
            cam.close()
            if frames:
                (HERE / "check_camera.jpg").write_bytes(frames[len(frames) // 2])
                size = sum(map(len, frames)) // len(frames)
                report("camera", True, f"{len(frames)} frames, ~{size // 1000} KB each, saved check_camera.jpg")
            else:
                report("camera", False, "webcam opened but gave no frames")
        except ImportError:
            report("camera", False, "no OpenCV: pip install -r charades/requirements-charades.txt")
        except Exception as err:
            report("camera", False, str(err))

    if "mic" not in skip:
        mic = hardware.Mic(True, args.mic_device)
        if mic.available:
            screen.show("CHECK", "say: riding a horse", "3 seconds", "guess")
            print('     say "riding a horse" now (3 s)...', flush=True)
            t = time.time()
            text = mic.listen(3)
            took = time.time() - t
            if text is None:
                report("mic", False, "recording failed: check  arecord -l  and use --mic-device plughw:<card>,0")
            elif not text:
                report("mic", False, f"recorded, but understood nothing ({took:.0f} s). Speak closer, or check the mic")
            else:
                report("mic", True, f'heard "{text}" ({took:.0f} s)')
        else:
            report("mic", False, "no mic or no faster-whisper: guesses will be typed on the laptop (that's fine)")

    if "voice" not in skip:
        voice = hardware.Voice(True)
        if voice.ok:
            voice.say("Hello from Telephone Charades.")
            time.sleep(4)
            report("voice", True, f"{voice.cmd[0]} (did you hear it? if not: check the speaker and  aplay -l)")
        else:
            report("voice", False, "no voice: see the README (Piper voice download), the game works without it")

    if "broker" not in skip:
        try:
            import threading
            got = {}
            arrived = threading.Event()
            bus = Bus("check")
            topic = f"IDD/charades-check/{int(time.time())}"
            sizes = [2_000, 10_000, 20_000, 50_000]

            def on_msg(t, payload):
                got[len(payload)] = True
                if len(got) == len(sizes):
                    arrived.set()
            bus.subscribe(topic, on_msg)
            bus.start(timeout=10)
            for n in sizes:                       # does the class broker pass messages as big as our frames?
                bus.publish(topic, "x" * n)
            arrived.wait(8)
            bus.stop()
            ok = [n for n in sizes if n in got]
            lost = [n for n in sizes if n not in got]
            if not lost:
                report("broker", True, f"connected to {bus.broker}; messages up to 50 KB get through")
            elif 10_000 in ok:
                report("broker", True, f"connected; messages of {', '.join(f'{n // 1000} KB' for n in lost)} were lost, "
                                       "but clip frames (about 9 KB) fit")
            else:
                report("broker", False, f"connected, but these test messages were lost: "
                                        f"{', '.join(f'{n // 1000} KB' for n in lost)}. Clip frames may not get through")
        except Exception as err:
            report("broker", False, f"{err}")

    screen.show("CHECK", "done", "see the terminal", "info")
    must = {"camera", "broker"}
    bad = [p for p, ok, _ in results if not ok and p in must]
    print("\n" + ("Ready to play." if not bad else f"Fix before playing: {', '.join(bad)}. The others are optional."))


if __name__ == "__main__":
    main()
