"""Paw Clock v3. --setup: choose schedules/distance; --demo: temporary demo."""
import argparse
import copy
import json
import math
import random
import shutil
import struct
import subprocess
import wave
import time
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_FILE = ROOT / 'walk_data.json'
CONFIG_FILE = ROOT / 'dog_clock_settings.json'
STATES = ['sleep', 'awake', 'excited', 'waiting']
EXAMPLE = {'weekday': ['08:00', '14:00', '20:00'],
           'weekend': ['09:00', '15:00', '21:00'], 'distance_km': 1.0}


def theme_for(now):
    if 8 <= now.hour < 12:
        return '#FFF5E4', '#283442', '#DFD4BF', 'MORNING'
    if 12 <= now.hour < 19:
        return '#DDEED8', '#253A30', '#BED5B7', 'AFTERNOON'
    if 19 <= now.hour:
        return '#DCECF8', '#27394D', '#BED3E4', 'EVENING'
    return '#142642', '#FFF5E4', '#243C5A', 'NIGHT'


def make_bark(path):
    """Create an original synthetic two-woof effect; replace bark.wav with a recording if desired."""
    rate = 22050
    rng = random.Random(23)
    samples = []
    angle = 0.0
    noise = 0.0
    for index in range(int(rate * .95)):
        t = index / rate
        local = t if t < .36 else t - .46
        value = 0.0
        if 0 <= local < .32:
            envelope = min(1.0, local / .014) * math.exp(-10 * local) * min(1.0, (.32-local)/.035)
            freq = 190 - 100 * local / .32
            angle += 2 * math.pi * freq / rate
            noise = .65 * noise + .35 * rng.uniform(-1, 1)
            voiced = sum(math.sin(angle*k) / k for k in range(1, 9)) / 2
            value = .65 * envelope * (.7*voiced + .6*noise)
        samples.append(int(max(-1, min(1, value)) * 32767))
    with wave.open(str(path), 'wb') as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(rate)
        output.writeframes(struct.pack('<' + 'h'*len(samples), *samples))


class BarkPlayer:
    """Nonblocking playback; at most two pending sounds, never simultaneous players."""
    def __init__(self, path, device=None):
        self.process = None
        self.pending = 0
        self.failed = False
        self.command = None
        if not path.exists():
            try:
                make_bark(path)
            except OSError as error:
                print('Cannot create bark.wav:', error)
                return
        player = shutil.which('aplay')
        if player:
            self.command = [player, '-q'] + (['-D', device] if device else []) + [str(path)]
        else:
            print('Sound unavailable: install alsa-utils to provide aplay.')

    def play(self):
        if not self.command or self.failed:
            return False
        self.pending = min(2, self.pending + 1)
        self.poll()
        return not self.failed

    def poll(self):
        if self.process is not None:
            result = self.process.poll()
            if result is None:
                return
            self.process = None
            if result != 0:
                print('Audio playback failed. Check speaker/output with aplay -l; use --audio-device if needed.')
                self.failed = True
                self.pending = 0
        if self.pending and not self.failed:
            self.pending -= 1
            try:
                self.process = subprocess.Popen(self.command, stdin=subprocess.DEVNULL)
            except OSError as error:
                print('Audio playback failed:', error)
                self.failed = True
                self.pending = 0

    def close(self):
        if self.process is not None:
            if self.process.poll() is None:
                self.process.terminate()
                try:
                    self.process.wait(timeout=.5)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    self.process.wait()
            self.process = None


class AlarmTracker:
    def __init__(self, path):
        self.path = path
        self.seen = set(json.loads(path.read_text())) if path.exists() else set()

    def check(self, now, data, config):
        """Sound once in the scheduled minute. Never replay hours of missed alarms at startup."""
        alerts = []
        day = now.date()
        schedule = config['weekend' if day.weekday() >= 5 else 'weekday']
        for clock in schedule:
            key = day.isoformat() + 'T' + clock + ':00'
            if key in data['completed'] or key in data['skipped']:
                continue
            due = datetime.fromisoformat(data['snoozes'].get(key, key))
            token = key + '|' + due.isoformat()
            if 0 <= (now-due).total_seconds() < 60 and token not in self.seen:
                self.seen.add(token)
                alerts.append(token)
        if alerts:
            self.seen = {token for token in self.seen if token[:10] >= day.isoformat()}
            try:
                write_json(self.path, sorted(self.seen))
            except OSError as error:
                print('Cannot save alarm history; restart may repeat the current alarm:', error)
        return bool(alerts)


def write_json(path, data):
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(data, indent=2))
    tmp.replace(path)


def parse_times(value):
    result = []
    for part in value.replace('，', ',').split(','):
        hour, minute = map(int, part.strip().split(':'))
        if not (0 <= hour < 24 and 0 <= minute < 60):
            raise ValueError('Use 24-hour times, for example 08:30, 18:00')
        result.append(f'{hour:02d}:{minute:02d}')
    if not result:
        raise ValueError('Enter at least one time.')
    return sorted(set(result))


def configure():
    print('Choose your own schedule. Times use the Raspberry Pi local timezone.')
    config = {}
    for field, label in [('weekday', 'Weekdays'), ('weekend', 'Weekends')]:
        while True:
            try:
                config[field] = parse_times(input(label + ' (HH:MM, HH:MM): '))
                break
            except (ValueError, TypeError):
                print('Enter valid times, for example 08:30, 14:00, 20:00')
    while True:
        try:
            km = float(input('Estimated km per walk: '))
            if not math.isfinite(km) or km <= 0:
                raise ValueError()
            config['distance_km'] = round(km, 3)
            if config['distance_km'] <= 0:
                raise ValueError()
            break
        except ValueError:
            print('Enter a positive distance in km, for example 0.8')
    write_json(CONFIG_FILE, config)
    print('Settings saved. Saved walk distances will not change.')
    return config


def load_config():
    if not CONFIG_FILE.exists():
        return configure()
    config = json.loads(CONFIG_FILE.read_text())
    for field in ('weekday', 'weekend'):
        config[field] = parse_times(','.join(config[field]))
    km = float(config['distance_km'])
    if not math.isfinite(km) or km <= 0:
        raise ValueError('Invalid configured distance; run --setup.')
    config['distance_km'] = km
    return config


def new_data():
    return {'version': 2, 'walks': [], 'completed': [], 'skipped': [], 'snoozes': {}}


def load_data():
    if not DATA_FILE.exists():
        return new_data()
    data = json.loads(DATA_FILE.read_text())
    for field in ('walks', 'completed'):
        if not isinstance(data.get(field), list):
            raise ValueError('Invalid walk_data.json: ' + field)
    if not isinstance(data.get('snoozes'), dict):
        raise ValueError('Invalid snoozes')
    # Preserve v1 counts. Old entries have no known distance and are not guessed.
    migrated = any(isinstance(w, str) for w in data['walks'])
    for i, walk in enumerate(data['walks']):
        if isinstance(walk, str):
            data['walks'][i] = {'at': walk, 'km': None, 'slot': None}
        walk = data['walks'][i]
        datetime.fromisoformat(walk['at'])
        if walk['km'] is not None and (not math.isfinite(walk['km']) or walk['km'] < 0):
            raise ValueError('Invalid saved distance')
    data.setdefault('skipped', [])
    if not isinstance(data['skipped'], list):
        raise ValueError('Invalid skipped slots')
    for value in data['snoozes'].values():
        datetime.fromisoformat(value)
    if migrated:
        backup = DATA_FILE.with_name('walk_data_v1_backup.json')
        if not backup.exists():
            backup.write_text(DATA_FILE.read_text())
    data['version'] = 2
    return data


def next_walk(now, data, config):
    # Pending slots expire at local midnight; they are not counted as walks.
    for offset in range(8):
        day = now.date() + timedelta(days=offset)
        schedule = config['weekend' if day.weekday() >= 5 else 'weekday']
        for value in schedule:
            due = datetime.fromisoformat(day.isoformat() + 'T' + value + ':00')
            key = due.isoformat()
            if key not in data['completed'] and key not in data['skipped']:
                return key, datetime.fromisoformat(data['snoozes'].get(key, key))
    raise ValueError('No available schedule.')


def state_for(now, due):
    minutes = (due-now).total_seconds()/60
    return 'sleep' if minutes > 30 else 'awake' if minutes > 0 else 'excited' if minutes >= -15 else 'waiting'


def remember(data):
    data['undo'] = {k: copy.deepcopy(data[k]) for k in ('walks', 'completed', 'skipped', 'snoozes')}


def act(action, now, data, config):
    if action == 'undo':
        previous = data.pop('undo', None)
        if previous is None:
            return 'Nothing to undo'
        data.update(previous)
        return 'Last action undone'
    key, due = next_walk(now, data, config)
    if action == 'skip' and datetime.fromisoformat(key).date() != now.date():
        return 'No pending walk today'
    remember(data)
    if action == 'log':
        slot = key if datetime.fromisoformat(key).date() == now.date() else None
        data['walks'].append({'at': now.isoformat(), 'km': config['distance_km'], 'slot': slot})
        if slot:
            data['completed'].append(slot)
            data['snoozes'].pop(slot, None)
        return 'Walk saved. Thank you!'
    if action == 'skip':
        data['skipped'].append(key)
        data['snoozes'].pop(key, None)
        return 'Skipped; count unchanged'
    if action == 'snooze':
        data['snoozes'][key] = (max(now, due)+timedelta(minutes=30)).isoformat()
        return 'Reminder moved +30 min'
    raise ValueError(action)


def totals(data, now):
    walks = data['walks']
    return (sum(datetime.fromisoformat(w['at']).date() == now.date() for w in walks),
            sum(datetime.fromisoformat(w['at']).year == now.year for w in walks),
            sum(w['km'] for w in walks if w['km'] is not None),
            sum(w['km'] is None for w in walks))


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


def render(state, count, stats=False, demo=False, message='', phase=0, now=None):
    from PIL import Image, ImageDraw, ImageFont
    background, ink, bar, period = theme_for(now or datetime.now())
    image = Image.new('RGB', (240, 135), background)
    d = ImageDraw.Draw(image)
    try:
        small = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 11)
        large = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 16)
    except OSError:
        small = large = ImageFont.load_default()
    cream, tan, dark = '#fff3d4', '#dda46c', '#49352a'
    d.text((8, 4), period + (' [DEMO]' if demo else ''), font=small, fill=ink)
    d.text((183, 4), f'{count} walks', font=small, fill=ink)
    if stats:
        d.text((22, 42), 'WALKS TODAY', font=large, fill=ink)
        d.text((100, 70), str(count), font=large, fill=ink)
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
            d.text((181, 31), 'Zzz', font=large, fill=ink)
        else:
            d.ellipse((146, 49-y, 151, 56-y), fill=dark)
        d.line([(68, 69-y), (53, (90 if state == 'waiting' else 47 if phase else 61)-y)], fill=tan, width=7)
        if state == 'waiting':
            d.text((192, 36), '...', font=large, fill=ink)
        if state == 'excited':
            for x, py in [(29, 46), (204, 72)]:
                d.ellipse((x, py, x+11, py+10), fill=ink)
                for dx, dy in [(-3, -5), (3, -9), (9, -5)]:
                    d.ellipse((x+dx, py+dy, x+dx+5, py+dy+5), fill=ink)
        labels = {'sleep': 'Resting until our next walk', 'awake': 'A walk is coming soon',
                  'excited': "Let's go for a walk!", 'waiting': 'Walk overdue. Ready?'}
        d.text((8, 103), labels[state], font=small, fill=ink)
    d.rectangle((0, 119, 240, 135), fill=bar)
    d.text((6, 121), message or 'A: log walk   B: view / hold: later', font=small, fill=ink)
    return image


MENU = [('snooze', 'Postpone 30 min'), ('skip', 'Skip pending walk'),
        ('undo', 'Undo last action'), ('cancel', 'Back')]


def background_demo_time(now, elapsed):
    """Preview four day periods without changing real time, schedules or statistics."""
    hour = (8, 12, 19, 0)[int(max(0, elapsed) // 5) % 4]
    return now.replace(hour=hour, minute=0, second=0, microsecond=0)


def frame(state, data, now, page, menu, demo, message, phase, theme_now=None):
    from PIL import ImageDraw, ImageFont
    today, year, km, unknown = totals(data, now)
    theme_now = now if theme_now is None else theme_now
    background, ink, bar, period = theme_for(theme_now)
    image = render(state, today, demo=demo, phase=phase, now=theme_now)
    d = ImageDraw.Draw(image)
    try:
        small = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 11)
        large = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 18)
    except OSError:
        small = large = ImageFont.load_default()
    if page or menu is not None:
        d.rectangle((0, 23, 239, 118), fill=background)
        if menu is not None:
            title, value, note = 'CORRECTIONS', MENU[menu][1], 'Hold B: cancel'
        elif page == 1:
            title, value, note = 'WALKS TODAY', str(today), now.strftime('%Y-%m-%d')
        elif page == 2:
            title, value, note = 'WALKS THIS YEAR', str(year), str(now.year)
        else:
            title, value = 'DISTANCE TOGETHER', f'{km:.2f} km'
            note = f'Estimated; {unknown} old walks excluded' if unknown else 'Estimated / all recorded walks'
        d.text((9, 28), title, font=small, fill=ink)
        d.text((9, 51), value, font=large, fill=ink)
        d.text((9, 91), note, font=small, fill=ink)
    d.rectangle((0, 119, 239, 134), fill=bar)
    footer = 'A: choose  B: next' if menu is not None else 'A: log  B: page  Hold A: menu'
    d.text((5, 121), message or footer, font=small, fill=ink)
    return image


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--setup', action='store_true', help='Choose weekday/weekend times and estimated km')
    parser.add_argument('--demo', action='store_true', help='Temporary records; cycle states every 5 seconds')
    parser.add_argument('--basic', action='store_true', help='Display-only first iteration')
    parser.add_argument('--test-sound', action='store_true', help='Test the speaker without initializing the display')
    parser.add_argument('--audio-device', help='ALSA output name, e.g. plughw:CARD=Device,DEV=0')
    parser.add_argument('--demo-background', action='store_true',
                        help='Enable demo mode and cycle day backgrounds every 5 seconds')
    args = parser.parse_args()
    if args.demo_background:
        args.demo = True
        print('BACKGROUND DEMO: morning, afternoon, evening, night; 5 seconds each.')
    if args.test_sound:
        sound = BarkPlayer(ROOT / 'bark.wav', args.audio_device)
        try:
            sound.play()
            while sound.process is not None or sound.pending:
                sound.poll()
                time.sleep(.02)
        finally:
            sound.close()
        return
    if args.setup:
        configure()
        return
    # Ask for settings BEFORE initializing the hardware.
    config = (load_config() if CONFIG_FILE.exists() else copy.deepcopy(EXAMPLE)) if args.demo else load_config()
    data = new_data() if args.demo else load_data()
    if args.demo:
        print('DEMO: records are temporary. Example settings used if no settings file exists.')
    print('A: log. B: page. Hold A: correction menu. Hold B: postpone. Release after each press.')
    print('Local time:', datetime.now().astimezone().isoformat())
    import board
    import digitalio
    from adafruit_rgb_display import st7789
    sound = BarkPlayer(ROOT / 'bark.wav', args.audio_device)
    alarms = None if args.demo else AlarmTracker(ROOT / 'dog_clock_alarms.json')
    resources = []
    spi = None
    backlight = None
    try:
        cs = digitalio.DigitalInOut(board.D5); resources.append(cs)
        dc = digitalio.DigitalInOut(board.D25); resources.append(dc)
        spi = board.SPI()
        display = st7789.ST7789(spi, cs=cs, dc=dc, rst=None, baudrate=64000000,
                               width=135, height=240, x_offset=53, y_offset=40)
        backlight = digitalio.DigitalInOut(board.D22); resources.append(backlight)
        backlight.switch_to_output(value=True)
        pins = []
        if not args.basic:
            for pin in (board.D23, board.D24):
                button = digitalio.DigitalInOut(pin); resources.append(button)
                button.switch_to_input(pull=digitalio.Pull.UP)
                pins.append(button)
        buttons = [Button(), Button()]
        page, menu = 0, None
        message, message_until = '', 0
        start = time.monotonic()
        last_log = last_frame = -100
        demo_override_until = 0
        last_demo_alarm = -1
        while True:
            now, tick = datetime.now(), time.monotonic()
            for index, pin in enumerate(pins):
                event = buttons[index].update(not pin.value, tick)
                if event is None:
                    continue
                action = None
                if menu is not None:
                    if index == 1:
                        menu = None if event == 'long' else (menu + 1) % len(MENU)
                    elif event == 'short':
                        action = MENU[menu][0]
                        menu = None
                        if action == 'cancel':
                            action = None
                elif index == 0:
                    if event == 'long':
                        menu = 0
                    elif tick - last_log >= 3:
                        action = 'log'
                elif event == 'short':
                    page = (page + 1) % 4
                else:
                    action = 'snooze'
                if action:
                    # Commit only after a successful save; keep current in-memory state on failure.
                    candidate = copy.deepcopy(data)
                    result = act(action, now, candidate, config)
                    try:
                        if not args.demo:
                            write_json(DATA_FILE, candidate)
                        data = candidate
                        message = result
                        if action == 'log':
                            last_log = tick
                            if not sound.play():
                                print('Walk saved, but sound is unavailable.')
                        demo_override_until = tick + 3
                    except OSError as error:
                        message = 'Save failed; check terminal'
                        print('Could not save:', error)
                    message_until = tick + 3
            sound.poll()
            if alarms is not None and alarms.check(now, data, config):
                ok = sound.play()
                message = 'Walk time! Woof!' if ok else 'Walk time! Check audio'
                message_until = tick + 4
            _, due = next_walk(now, data, config)
            state = state_for(now, due)
            if args.demo:
                state = 'sleep' if tick < demo_override_until else STATES[int((tick-start)//5) % 4]
            if args.demo:
                demo_cycle = int((tick-start)//20)
                if state == 'excited' and demo_cycle != last_demo_alarm:
                    sound.play()
                    last_demo_alarm = demo_cycle
            if tick - last_frame >= .15:
                display.image(frame(state, data, now, page, menu, args.demo,
                                    message if tick < message_until else '', int(tick*2) % 2,
                                    theme_now=background_demo_time(now, tick-start) if args.demo_background else None), 90)
                last_frame = tick
            time.sleep(.01)
    except KeyboardInterrupt:
        print('\nClock stopped.')
    finally:
        sound.close()
        if backlight is not None:
            try:
                backlight.value = False
            except Exception:
                pass
        for resource in reversed(resources):
            resource.deinit()
        if spi is not None:
            spi.deinit()


if __name__ == '__main__':
    main()
