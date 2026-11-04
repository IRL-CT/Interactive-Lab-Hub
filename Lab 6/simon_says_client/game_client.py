#!/usr/bin/env python3
"""APDS9960 player for the supplied Simon Says MQTT server."""
import argparse
import getpass
import os
import threading
import time

TEAM_NAME = 'simon_says_team'
BROKER = 'farlab.infosci.cornell.edu'
PORT = 1883
USER = 'idd'
COMMAND_TOPIC = f'IDD/{TEAM_NAME}/simon/command'


def mqtt_password():
    return os.environ.get('MQTT_PASSWORD') or getpass.getpass('Class MQTT broker password: ')


def event_topic(player):
    return f'IDD/{TEAM_NAME}/simon/{player}/event'


def parse_message(payload):
    kind, separator, text = payload.partition(':')
    if separator and kind in ('display', 'result'):
        return kind, text
    return None


def classify(proximity_value, color, proximity=200, clear=50, margin=50):
    if proximity_value > proximity:
        return 'close'
    r, g, b, c = color
    if c > clear:
        if r > g + margin and r > b + margin:
            return 'red'
        if g > r + margin and g > b + margin:
            return 'green'
        if b > r + margin and b > g + margin:
            return 'blue'
    return None


class GameState:
    """Call under a lock when the MQTT callback and sensor loop share it."""
    def __init__(self, settle_seconds=0.15):
        self.settle_seconds = settle_seconds
        self.active = False
        self.ready = False
        self.pending = None
        self.sent = False
        self.started = 0

    def message(self, kind, text, now):
        if kind == 'display':
            self.active = not text.upper().startswith('GAME OVER!')
            self.started = now
            self.sent = False
            self.pending = None
        elif kind == 'result':
            self.active = False
            self.pending = None

    def sample(self, action, now):
        if action is None:
            self.ready = True
        elif self.ready:
            self.ready = False
            if self.active and not self.sent and self.pending is None:
                self.pending = action
        if self.active and not self.sent and self.pending is not None and now - self.started >= self.settle_seconds:
            result = self.pending
            self.pending = None
            self.sent = True
            return result
        return None


class Display:
    def __init__(self):
        self.device = None
        try:
            import board
            import digitalio
            import adafruit_rgb_display.st7789 as st7789
            from PIL import Image, ImageDraw, ImageFont
            self.Image, self.ImageDraw, self.ImageFont = Image, ImageDraw, ImageFont
            self.cs = digitalio.DigitalInOut(board.D5)
            self.dc = digitalio.DigitalInOut(board.D25)
            self.backlight = digitalio.DigitalInOut(board.D22)
            self.backlight.switch_to_output(value=True)
            self.spi = board.SPI()
            self.device = st7789.ST7789(self.spi, cs=self.cs, dc=self.dc, rst=None,
                                         baudrate=64000000, width=135, height=240, x_offset=53,
                                         y_offset=40, rotation=90)
            try:
                self.font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 15)
            except OSError:
                self.font = ImageFont.load_default()
        except Exception as exc:
            print(f'TFT unavailable; continuing in terminal: {exc}', flush=True)
            self.device = None

    def show(self, text, kind='display'):
        print(f'\n[{kind.upper()}] {text}', flush=True)
        if self.device is None:
            return
        try:
            image = self.Image.new('RGB', (240, 135), 'black')
            draw = self.ImageDraw.Draw(image)
            words = text.split()
            lines = []
            line = ''
            for word in words:
                trial = (line + ' ' + word).strip()
                if line and draw.textbbox((0, 0), trial, font=self.font)[2] > 230:
                    lines.append(line)
                    line = word
                else:
                    line = trial
            if line:
                lines.append(line)
            # Actual server messages fit in this area with the 15px font.
            for i, line in enumerate(lines[:7]):
                draw.text((5, 4 + i * 18), line, font=self.font, fill='white')
            self.device.image(image)
        except Exception as exc:
            print(f'TFT failed; continuing in terminal: {exc}', flush=True)
            self.device = None


def arguments():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--player', choices=('pi1', 'pi2'), default='pi2', help='player identity (default: pi2)')
    parser.add_argument('--proximity', type=int, default=200, help='close threshold; trigger above this value (default: 200)')
    parser.add_argument('--clear', type=int, default=50, help='minimum color clear channel; trigger above this value (default: 50)')
    parser.add_argument('--margin', type=int, default=50, help='required lead over both other color channels (default: 50)')
    parser.add_argument('--settle', type=float, default=0.15, help='seconds to buffer first action after display (default: 0.15)')
    parser.add_argument('--calibrate', action='store_true', help='print sensor values without connecting to the game')
    return parser.parse_args()


def main():
    args = arguments()
    if args.settle < 0:
        raise SystemExit('--settle must be non-negative')
    try:
        import board
        import busio
        from adafruit_apds9960.apds9960 import APDS9960
        i2c = busio.I2C(board.SCL, board.SDA)
        sensor = APDS9960(i2c)
        sensor.enable_proximity = True
        sensor.enable_color = True
    except Exception as exc:
        raise SystemExit(f'Cannot start APDS9960 sensor: {exc}') from exc
    if args.calibrate:
        print('Proximity and RGBC readings (Ctrl+C to stop):', flush=True)
        try:
            while True:
                p, color = sensor.proximity, sensor.color_data
                action = classify(p, color, args.proximity, args.clear, args.margin)
                print(f'proximity={p} RGBC={color} action={action}', flush=True)
                time.sleep(0.5)
        except KeyboardInterrupt:
            return

    try:
        import paho.mqtt.client as mqtt
    except ImportError as exc:
        raise SystemExit('Install paho-mqtt<2 in the Pi environment.') from exc
    display = Display()
    state = GameState(args.settle)
    lock = threading.Lock()
    client = mqtt.Client()
    client.username_pw_set(USER, mqtt_password())

    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            client.subscribe(COMMAND_TOPIC)
            print(f'Connected. Listening as {args.player}.', flush=True)
        else:
            print(f'MQTT connection failed (code {rc}).', flush=True)

    def on_disconnect(client, userdata, rc):
        with lock:
            state.active = False
            state.pending = None
        if rc:
            print(f'MQTT disconnected (code {rc}); waiting to reconnect.', flush=True)

    def on_message(client, userdata, msg):
        try:
            parsed = parse_message(msg.payload.decode('utf-8'))
        except UnicodeDecodeError:
            return
        if parsed is not None:
            kind, text = parsed
            with lock:
                state.message(kind, text, time.monotonic())
            display.show(text, kind)

    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    display.show(f'{args.player.upper()} ready. Waiting for server.')
    try:
        client.connect(BROKER, PORT, 60)
        client.loop_start()
        while True:
            p = sensor.proximity
            color = sensor.color_data if p <= args.proximity else (0, 0, 0, 0)
            detected = classify(p, color, args.proximity, args.clear, args.margin)
            with lock:
                action = state.sample(detected, time.monotonic())
                if action:
                    info = client.publish(event_topic(args.player), action)
                    if info.rc != mqtt.MQTT_ERR_SUCCESS:
                        print(f'Could not publish {action} (MQTT code {info.rc}).', flush=True)
                    else:
                        print(f'[Triggered: {action}]', flush=True)
            time.sleep(0.05)
    except KeyboardInterrupt:
        print('\nShutting down client.', flush=True)
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == '__main__':
    main()
