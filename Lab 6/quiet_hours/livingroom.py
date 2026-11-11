"""
Living room Pi: listens to how loud the room is and asks people to keep it down while I'm asleep.

    python livingroom.py                       # webcam mic through arecord + PiTFT
    python livingroom.py --device plughw:2,0   # pick the mic (arecord -l lists them)
    python livingroom.py --threshold -25       # how loud counts as loud, in dBFS
    python livingroom.py --fake                # no hardware: type a level like -15 and press Enter

Input:  the microphone. Every --every seconds it measures the room's loudness in dBFS
        (0 is the loudest a mic can record, quiet rooms sit around -60 to -45).
Output: publishes the level on IDD/quiethours/livingroom/noise all the time.
        While the bedroom says I'm asleep, the screen is dim red, and a level above
        --threshold turns it bright red ("Aryan's asleep, keep it down") and publishes
        an event on IDD/quiethours/livingroom/loud that the bedroom counts for the morning.
"""
import argparse
import array
import math
import subprocess
import sys
import threading
import time

import common

parser = argparse.ArgumentParser()
parser.add_argument("--fake", action="store_true", help="no hardware; type levels instead")
parser.add_argument("--device", default="default", help="arecord device for the mic")
parser.add_argument("--threshold", type=float, default=-25, help="dBFS above this counts as loud")
parser.add_argument("--every", type=float, default=2, help="seconds per loudness reading")
parser.add_argument("--cooldown", type=float, default=15, help="seconds between loud events")
args = parser.parse_args()

screen = common.Screen(fake=args.fake)
asleep = False
last_loud = 0.0
warning_until = 0.0


def draw():
    if time.time() < warning_until:
        screen.show("Shhh!", "Aryan's asleep,\nkeep it down", bg=(220, 0, 0))
    elif asleep:
        screen.show("Quiet hours", "Aryan's asleep", bg=(70, 0, 0))
    else:
        screen.show("All good", "Aryan's awake", bg=(0, 90, 40))


def on_message(topic, msg):
    global asleep
    if topic == common.STATE:
        asleep = msg.get("state") == "asleep"
        draw()


client = common.connect("livingroom", on_message, subscribe=[common.STATE])
draw()


def levels():
    """Yield one loudness reading (dBFS) every --every seconds."""
    if args.fake:
        print("(fake) type a level in dBFS, e.g. -15, and press Enter")
        for line in sys.stdin:
            try:
                yield float(line)
            except ValueError:
                pass
        return
    rate = 16000
    chunk = int(rate * args.every) * 2          # 16-bit mono, so 2 bytes per sample
    mic = subprocess.Popen(
        ["arecord", "-q", "-D", args.device, "-f", "S16_LE", "-r", str(rate), "-c", "1", "-t", "raw"],
        stdout=subprocess.PIPE,
    )
    while True:
        data = mic.stdout.read(chunk)
        if len(data) < chunk:
            raise SystemExit("the mic stopped; check --device with arecord -l")
        samples = array.array("h", data)
        rms = math.sqrt(sum(s * s for s in samples) / len(samples))
        yield 20 * math.log10(max(rms, 1) / 32768)


def tick():
    """Redraw when a warning runs out."""
    while True:
        time.sleep(1)
        if warning_until and warning_until < time.time() < warning_until + 1.5:
            draw()


threading.Thread(target=tick, daemon=True).start()

try:
    for level in levels():
        level = round(level, 1)
        common.send(client, common.NOISE, {"level": level})
        loud = level > args.threshold
        print(f"{level:6.1f} dBFS" + ("  LOUD" if loud else ""))
        if loud and asleep:
            warning_until = time.time() + 6
            draw()
            if time.time() - last_loud > args.cooldown:   # one event per loud stretch, not per reading
                last_loud = time.time()
                common.send(client, common.LOUD, {"level": level, "t": common.now()})
except KeyboardInterrupt:
    pass
finally:
    common.goodbye(client, "livingroom")
