#!/usr/bin/env python3
"""Publish one Pi's color to the mood ring.

Real sensor on this Pi:
    python mood_ring_publisher.py

Pretend to be another Pi (no sensor needed). Run one of these per fake Pi:
    python mood_ring_publisher.py --fake rose
    python mood_ring_publisher.py --fake ocean --r 20 --g 60 --b 200
"""

import argparse
import json
import signal
import socket
import time
import uuid
import zlib

import paho.mqtt.client as mqtt

from mood_ring_common import (
    COLOR_TOPIC,
    MQTT_BROKER,
    MQTT_PASSWORD,
    MQTT_PORT,
    MQTT_USERNAME,
)

PUBLISH_INTERVAL = 0.5

PRESETS = {
    'rose': (220, 40, 70),
    'amber': (240, 150, 30),
    'ocean': (30, 70, 220),
    'leaf': (40, 180, 70),
    'violet': (140, 40, 200),
}


def color_from_name(name):
    if name in PRESETS:
        return PRESETS[name]
    digest = zlib.adler32(name.encode())
    return ((digest >> 16) & 255, (digest >> 8) & 255, digest & 255)


def scale_sensor_color(raw_red, raw_green, raw_blue):
    """Match the Part B pixel-grid scaling so sensor colors look right."""
    red = int(raw_red * 1.2)
    green = int(raw_green * 1.2)
    blue = int(raw_blue * 1.7)
    peak = max(red, green, blue)
    if peak <= 0:
        return 0, 0, 0
    scale = 255.0 / peak
    return (
        int(min(255, red * scale)),
        int(min(255, green * scale)),
        int(min(255, blue * scale)),
    )


def setup_sensor():
    import board
    import busio
    import adafruit_apds9960.apds9960

    i2c = busio.I2C(board.SCL, board.SDA)
    sensor = adafruit_apds9960.apds9960.APDS9960(i2c)
    sensor.enable_color = True
    try:
        sensor.color_gain = 1
        sensor.integration_time = 10
    except Exception:
        pass
    return sensor


def setup_display():
    try:
        import board
        import digitalio
        from PIL import Image, ImageDraw, ImageFont
        import adafruit_rgb_display.st7789 as st7789
    except ImportError:
        return None

    try:
        cs_pin = digitalio.DigitalInOut(board.D5)
        dc_pin = digitalio.DigitalInOut(board.D25)
        backlight = digitalio.DigitalInOut(board.D22)
        backlight.switch_to_output()
        backlight.value = True
        disp = st7789.ST7789(
            board.SPI(),
            cs=cs_pin,
            dc=dc_pin,
            rst=None,
            baudrate=64000000,
            width=135,
            height=240,
            x_offset=53,
            y_offset=40,
            rotation=90,
        )
        image = Image.new('RGB', (240, 135))
        draw = ImageDraw.Draw(image)
        try:
            font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf', 18)
        except Exception:
            font = ImageFont.load_default()
        return disp, draw, image, font
    except Exception as exc:
        print(f'[WARN] display unavailable: {exc}')
        return None


def show_color(display, red, green, blue, device_id):
    if display is None:
        return
    disp, draw, image, font = display
    draw.rectangle((0, 0, image.width, image.height), fill=(red, green, blue))
    text = (255, 255, 255) if (red + green + blue) < 384 else (0, 0, 0)
    draw.text((8, 48), device_id, font=font, fill=text)
    draw.text((8, 76), f'{red:3d} {green:3d} {blue:3d}', font=font, fill=text)
    disp.image(image)


def connect_mqtt():
    client = mqtt.Client(str(uuid.uuid1()))
    client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print(f'[OK] connected to {MQTT_BROKER}')
        else:
            print(f'[ERROR] connection failed: {rc}')

    client.on_connect = on_connect
    client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
    client.loop_start()
    deadline = time.time() + 5
    while not client.is_connected() and time.time() < deadline:
        time.sleep(0.1)
    return client


def main():
    parser = argparse.ArgumentParser(description='Publish a color to the mood ring')
    parser.add_argument('--fake', metavar='NAME', help='publish as this device id, with no sensor')
    parser.add_argument('--r', type=int, help='red 0-255, only with --fake')
    parser.add_argument('--g', type=int, help='green 0-255, only with --fake')
    parser.add_argument('--b', type=int, help='blue 0-255, only with --fake')
    args = parser.parse_args()

    if args.fake:
        device_id = args.fake
        if args.r is None and args.g is None and args.b is None:
            fake_color = color_from_name(args.fake)
        else:
            fake_color = (
                max(0, min(255, args.r or 0)),
                max(0, min(255, args.g or 0)),
                max(0, min(255, args.b or 0)),
            )
        sensor = None
        display = None
        print(f'Fake Pi "{device_id}" RGB{fake_color}')
    else:
        device_id = socket.gethostname()
        print('Starting color sensor...')
        sensor = setup_sensor()
        display = setup_display()
        fake_color = None
        print('[OK] sensor ready')

    print(f'Publishing to {COLOR_TOPIC} as {device_id}')
    client = connect_mqtt()

    def stop(signum, frame):
        client.loop_stop()
        client.disconnect()
        raise SystemExit(0)

    signal.signal(signal.SIGINT, stop)

    while True:
        if sensor is None:
            red, green, blue = fake_color
        else:
            raw_red, raw_green, raw_blue, _clear = sensor.color_data
            red, green, blue = scale_sensor_color(raw_red, raw_green, raw_blue)

        payload = json.dumps({
            'id': device_id,
            'r': red,
            'g': green,
            'b': blue,
            'timestamp': int(time.time()),
        })
        client.publish(COLOR_TOPIC, payload)
        show_color(display, red, green, blue, device_id)
        print(f'[OK] {device_id} RGB({red:3d},{green:3d},{blue:3d})')
        time.sleep(PUBLISH_INTERVAL)


if __name__ == '__main__':
    main()
