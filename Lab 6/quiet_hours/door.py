"""
Door Pi: a touch pad on my door that people tap instead of knocking.

    python door.py           # MPR121 pad 0 + PiTFT
    python door.py --fake    # no hardware: Enter = knock

Input:  a tap on the pad (the "knock").
Output: publishes IDD/quiethours/door/knock every time. The screen answers the person
        right away: if I'm asleep it says so and asks them to text instead, and the
        bedroom Pi keeps the knock quietly for my morning summary. If I'm awake, the
        bedroom screen lights up and this one says I've been told.
"""
import argparse
import threading

import common

parser = argparse.ArgumentParser()
parser.add_argument("--fake", action="store_true", help="no hardware; Enter = knock")
args = parser.parse_args()

screen = common.Screen(fake=args.fake)
asleep = False


def draw():
    if asleep:
        screen.show("Asleep", "Tap = leave a knock\nfor the morning", bg=(70, 0, 0))
    else:
        screen.show("Knock here", "Tap the pad", bg=(0, 90, 40))


def on_message(topic, msg):
    global asleep
    if topic == common.STATE:
        asleep = msg.get("state") == "asleep"
        draw()


def knock():
    common.send(client, common.KNOCK, {"t": common.now()})
    if asleep:
        screen.show("Shhh!", "Aryan's asleep. Text\ninstead, the knock\nwaits till morning", bg=(140, 0, 0))
    else:
        screen.show("Knocked!", "Aryan's been told", bg=(0, 60, 140))
    threading.Timer(5, draw).start()


client = common.connect("door", on_message, subscribe=[common.STATE])
draw()
common.touch_pad(knock, fake=args.fake, word="knock")

try:
    threading.Event().wait()
except KeyboardInterrupt:
    pass
finally:
    common.goodbye(client, "door")
