"""
Shared pieces for the three Quiet Hours Pis: broker settings, topic names,
the MQTT connection, the PiTFT screen and the MPR121 touch pad.

Every topic lives under IDD/quiethours/ so we don't collide with other teams.

    IDD/quiethours/bedroom/state     retained  {"state": "asleep" | "awake", "since": "...", "source": "tap" | "camera"}
    IDD/quiethours/livingroom/noise            {"level": -42.1}               every couple of seconds
    IDD/quiethours/livingroom/loud             {"level": -18.3, "t": "..."}   only while I'm asleep
    IDD/quiethours/door/knock                  {"t": "..."}
    IDD/quiethours/<pi>/online       retained  "1" while the Pi is running, "0" once it drops

The bedroom state is retained, so a Pi that starts late still learns right away
whether I'm asleep. The online flag uses MQTT's last will, so the broker
announces "0" for us when a Pi loses power without saying goodbye.
"""
import datetime
import json
import sys
import threading

import paho.mqtt.client as mqtt

BROKER = "farlab.infosci.cornell.edu"
PORT = 1883
USERNAME = "idd"
PASSWORD = "device@theFarm"

ROOT = "IDD/quiethours"
STATE = f"{ROOT}/bedroom/state"
NOISE = f"{ROOT}/livingroom/noise"
LOUD = f"{ROOT}/livingroom/loud"
KNOCK = f"{ROOT}/door/knock"


def now():
    return datetime.datetime.now().isoformat(timespec="seconds")


def connect(name, on_message=None, subscribe=()):
    """Connect to the class broker as `name` and start the network loop in the background."""
    client = mqtt.Client(client_id=f"quiethours-{name}", clean_session=True)
    client.username_pw_set(USERNAME, PASSWORD)
    online = f"{ROOT}/{name}/online"
    client.will_set(online, "0", retain=True)

    def on_connect(c, userdata, flags, rc):
        if rc != 0:
            print(f"broker refused the connection (rc={rc})")
            return
        c.publish(online, "1", retain=True)
        for topic in subscribe:
            c.subscribe(topic)
        print(f"connected to {BROKER} as {name}")

    def on_msg(c, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
        except ValueError:
            return              # not ours, or garbled; ignore it
        if on_message:
            on_message(msg.topic, payload)

    client.on_connect = on_connect
    client.on_message = on_msg
    client.connect(BROKER, PORT, keepalive=30)
    client.loop_start()
    return client


def send(client, topic, payload, retain=False):
    client.publish(topic, json.dumps(payload), retain=retain)


def goodbye(client, name):
    client.publish(f"{ROOT}/{name}/online", "0", retain=True).wait_for_publish(2)
    client.loop_stop()
    client.disconnect()


class Screen:
    """The MiniPiTFT from Lab 2, in landscape. Falls back to printing when there is no screen."""

    def __init__(self, fake=False):
        self.disp = None
        if fake:
            return
        try:
            import board
            import digitalio
            import adafruit_rgb_display.st7789 as st7789
            from PIL import Image, ImageDraw, ImageFont

            self.disp = st7789.ST7789(
                board.SPI(),
                cs=digitalio.DigitalInOut(board.D5),
                dc=digitalio.DigitalInOut(board.D25),
                rst=None,
                baudrate=64000000,
                width=135,
                height=240,
                x_offset=53,
                y_offset=40,
            )
            backlight = digitalio.DigitalInOut(board.D22)
            backlight.switch_to_output()
            backlight.value = True
            self.Image, self.ImageDraw = Image, ImageDraw
            path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
            self.big = ImageFont.truetype(path, 30)
            self.small = ImageFont.truetype(path, 16)
        except Exception as e:            # no PiTFT, or the screen service still owns it
            print(f"no PiTFT ({e}); printing to the terminal instead")
            self.disp = None

    def show(self, title, line="", bg=(0, 0, 0), fg=(255, 255, 255)):
        print(f"[screen] {title}" + (f" | {line}" if line else ""))
        if self.disp is None:
            return
        image = self.Image.new("RGB", (240, 135), bg)
        draw = self.ImageDraw.Draw(image)
        draw.text((10, 20), title, font=self.big, fill=fg)
        y = 70
        for part in line.split("\n"):
            draw.text((10, y), part, font=self.small, fill=fg)
            y += 22
        self.disp.image(image, 90)


def touch_pad(on_touch, fake=False, pad=0, word="tap"):
    """Call on_touch() once per touch of MPR121 pad `pad` (fake: once per typed line)."""
    def hardware():
        import time
        import board
        import busio
        import adafruit_mpr121
        sensor = adafruit_mpr121.MPR121(busio.I2C(board.SCL, board.SDA))
        was = False
        while True:
            touched = sensor[pad].value
            if touched and not was:       # count the press, not every 50 ms it stays down
                on_touch()
            was = touched
            time.sleep(0.05)

    def typed():
        print(f"(fake) press Enter to {word}")
        for _ in sys.stdin:
            on_touch()

    threading.Thread(target=typed if fake else hardware, daemon=True).start()
