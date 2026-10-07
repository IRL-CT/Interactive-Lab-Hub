"""Dog walking clock. Use --demo for recording, --basic for the first iteration."""
import argparse
import json
import time
from datetime import datetime, timedelta
from pathlib import Path

WALK_TIMES = [(8, 0), (14, 0), (20, 0)]  # Local Pi time: change these.
DATA_FILE = Path(__file__).with_name('walk_data.json')
STATES = ['sleep', 'awake', 'excited', 'waiting']


def new_data():
    return {'walks': [], 'completed': [], 'snoozes': {}}


def load_data():
    if not DATA_FILE.exists():
        return new_data()
    data = json.loads(DATA_FILE.read_text())
    if (not isinstance(data, dict) or
        not isinstance(data.get('walks'), list) or
        not isinstance(data.get('completed'), list) or
        not isinstance(data.get('snoozes'), dict)):
        raise ValueError('Invalid walk_data.json; back up and inspect it before restarting.')
    for value in data['walks']:
        datetime.fromisoformat(value)
    for value in data['snoozes'].values():
        datetime.fromisoformat(value)
    return data


def save_data(data):
    temporary = DATA_FILE.with_suffix('.tmp')
    temporary.write_text(json.dumps(data, indent=2))
    temporary.replace(DATA_FILE)


def next_walk(now, data):
    # Unlogged slots expire at midnight; they are never counted as completed.
    for day in (now.date(), now.date() + timedelta(days=1)):
        for hour, minute in sorted(WALK_TIMES):
            scheduled = datetime.combine(day, datetime.min.time()).replace(hour=hour, minute=minute)
            key = scheduled.isoformat()
            if key not in data['completed']:
                due = datetime.fromisoformat(data['snoozes'].get(key, key))
                return key, due
    raise ValueError('WALK_TIMES must contain at least one time.')


def state_for(now, due):
    minutes = (due - now).total_seconds() / 60
    if minutes > 30:
        return 'sleep'
    if minutes > 0:
        return 'awake'
    if minutes >= -15:
        return 'excited'
    return 'waiting'


class Button:
    """Debounce input; emit one short/long event on release."""
    def __init__(self):
        self.raw = self.stable = False
        self.changed = self.started = 0

    def update(self, pressed, tick):
        if pressed != self.raw:
            self.raw, self.changed = pressed, tick
        if self.raw != self.stable and tick - self.changed >= 0.04:
            self.stable = self.raw
            if self.stable:
                self.started = tick
            else:
                return 'long' if tick - self.started >= 1.2 else 'short'
        return None


def render(state, count, stats=False, demo=False, message='', phase=0):
    from PIL import Image, ImageDraw, ImageFont
    image = Image.new('RGB', (240, 135), '#14251f')
    d = ImageDraw.Draw(image)
    try:
        small = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 11)
        large = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 16)
    except OSError:
        small = large = ImageFont.load_default()
    cream, tan, dark = '#fff3d4', '#dda46c', '#49352a'
    d.text((8, 4), 'PAW CLOCK' + ('  [DEMO]' if demo else ''), font=small, fill=cream)
    d.text((183, 4), f'{count} walks', font=small, fill=cream)
    if stats:
        d.text((22, 42), 'WALKS TODAY', font=large, fill=cream)
        d.text((100, 70), str(count), font=large, fill='#a9db9c')
    else:
        # Vector shapes rendered to pixels: no image files or emoji fonts needed.
        y = 4 if state == 'excited' and phase else 0
        d.ellipse((63, 54-y, 151, 96-y), fill=tan)
        d.ellipse((118, 34-y, 173, 83-y), fill=tan)
        d.polygon([(121, 39-y), (110, 33-y), (115, 72-y), (131, 61-y)], fill=dark)
        d.ellipse((149, 59-y, 181, 79-y), fill=cream)
        d.ellipse((171, 60-y, 180, 68-y), fill=dark)
        d.rounded_rectangle((77, 83-y, 102, 100-y), radius=6, fill=cream)
        d.rounded_rectangle((132, 82-y, 151, 100-y), radius=6, fill=cream)
        if state == 'sleep':
            d.line((144, 54-y, 153, 54-y), fill=dark, width=2)
            d.text((181, 31), 'Zzz', font=large, fill=cream)
        else:
            d.ellipse((146, 49-y, 151, 56-y), fill=dark)
        d.line([(68, 69-y), (53, (47 if phase else 61)-y)], fill=tan, width=7)
        if state == 'excited':
            for x, py in [(29, 46), (204, 72)]:
                d.ellipse((x, py, x+11, py+10), fill='#a9db9c')
                for dx, dy in [(-3, -5), (3, -9), (9, -5)]:
                    d.ellipse((x+dx, py+dy, x+dx+5, py+dy+5), fill='#a9db9c')
        labels = {'sleep': 'Resting until our next walk', 'awake': 'A walk is coming soon',
                  'excited': "Let's go for a walk!", 'waiting': 'Ready when you are...'}
        d.text((8, 103), labels[state], font=small, fill=cream)
    d.rectangle((0, 119, 240, 135), fill='#284338')
    d.text((6, 121), message or 'A: log walk   B: view / hold: later', font=small, fill=cream)
    return image


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--demo', action='store_true', help='Cycle states every 5 seconds; no disk writes')
    parser.add_argument('--basic', action='store_true', help='First iteration: display only, no buttons')
    args = parser.parse_args()
    import board
    import digitalio
    from adafruit_rgb_display import st7789
    cs = digitalio.DigitalInOut(board.D5)
    dc = digitalio.DigitalInOut(board.D25)
    spi = board.SPI()
    display = st7789.ST7789(spi, cs=cs, dc=dc, rst=None, baudrate=64000000,
                           width=135, height=240, x_offset=53, y_offset=40)
    backlight = digitalio.DigitalInOut(board.D22)
    backlight.switch_to_output(value=True)
    pins = []
    if not args.basic:
        for pin in (board.D23, board.D24):
            button = digitalio.DigitalInOut(pin)
            button.switch_to_input(pull=digitalio.Pull.UP)
            pins.append(button)
    buttons = [Button(), Button()]
    data = new_data() if args.demo else load_data()
    stats = False
    message, message_until = '', 0
    start = time.monotonic()
    last_log, last_frame = -100, -100
    demo_override_until = 0
    print('Running. Ctrl+C exits. Demo records are temporary.' if args.demo else 'Running. Ctrl+C exits.')
    try:
        while True:
            now, tick = datetime.now(), time.monotonic()
            key, due = next_walk(now, data)
            state = state_for(now, due)
            if args.demo:
                state = STATES[int((tick-start) // 5) % 4]
                if tick < demo_override_until:
                    state = 'sleep'
            for index, pin in enumerate(pins):
                event = buttons[index].update(not pin.value, tick)
                if event is None:
                    continue
                if index == 0 and tick - last_log >= 3:
                    data['walks'].append(now.isoformat())
                    # One log completes one slot on the current day, never tomorrow's slot.
                    if datetime.fromisoformat(key).date() == now.date():
                        data['completed'].append(key)
                        data['snoozes'].pop(key, None)
                    if not args.demo:
                        save_data(data)
                    last_log = tick
                    demo_override_until = tick + 3
                    message, message_until = 'Walk saved. Thank you!', tick + 3
                elif index == 1:
                    if event == 'long':
                        data['snoozes'][key] = (max(now, due) + timedelta(minutes=30)).isoformat()
                        if not args.demo:
                            save_data(data)
                        demo_override_until = tick + 3
                        message, message_until = 'Reminder moved +30 min', tick + 3
                    else:
                        stats = not stats
            count = sum(datetime.fromisoformat(w).date() == now.date() for w in data['walks'])
            if tick - last_frame >= 0.15:
                display.image(render(state, count, stats, args.demo,
                                     message if tick < message_until else '', int(tick*2) % 2), 90)
                last_frame = tick
            time.sleep(0.01)
    except KeyboardInterrupt:
        print('\nClock stopped. Saved records are kept.')
    finally:
        backlight.value = False
        for pin in pins + [backlight, cs, dc]:
            pin.deinit()
        spi.deinit()


if __name__ == '__main__':
    main()
