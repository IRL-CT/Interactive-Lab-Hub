"""Part G: say 'Hello', then confirm a real camera log has begun.

Run with the Lab 3 Python environment; the camera worker uses Lab 5's environment.
The default run is a 30-second demo. Audio is temporary; text logs are retained.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import importlib.util
import json
from pathlib import Path
import re
import signal
import subprocess
import tempfile
import time
import wave


LAB = Path(__file__).resolve().parent
LAB3 = LAB.parent / 'Lab 3'


def is_start_command(text):
    words = re.findall(r"\w+", text.casefold())
    return bool(words) and all(word == 'hello' for word in words)


def wait_for_ready(child, ready_file, timeout=60):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if child.poll() is not None:
            raise RuntimeError(f'Camera worker exited with code {child.returncode}. See worker.txt.')
        try:
            data = json.loads(Path(ready_file).read_text(encoding='utf-8'))
            if data.get('pid') == child.pid and child.poll() is None:
                return data
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        time.sleep(.05)
    raise TimeoutError('Camera startup timed out. See worker.txt; the watch was not confirmed.')


def load_recognizer():
    from faster_whisper import WhisperModel
    return WhisperModel('tiny.en', device='cpu', compute_type='int8',
                        cpu_threads=4, local_files_only=True)


def transcribe(model, wav_path):
    segments, _ = model.transcribe(str(wav_path), language='en', beam_size=1,
                                   condition_on_previous_text=False, vad_filter=True)
    return ' '.join(part.text.strip() for part in segments).strip()


def load_screen():
    source = LAB3 / 'focus_buddy_woz.py'
    spec = importlib.util.spec_from_file_location('lab3_display', source)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    return helper.MiniPiTFT()


def prepare_prompts(folder):
    from piper import PiperVoice
    voice = PiperVoice.load(str(LAB3 / 'voices/en_US-lessac-medium.onnx'))
    paths = {}
    for key, text in [('ready', 'Say hello to start.'),
                      ('retry', 'Please say hello.'),
                      ('started', 'Night watch started.')]:
        path = folder / f'{key}.wav'
        with wave.open(str(path), 'wb') as wav:
            voice.synthesize_wav(text, wav)
        paths[key] = path
    return paths


def play(path):
    subprocess.run(['aplay', '-q', '-D', 'pulse', str(path)], check=True, timeout=20)


def stop_worker(child):
    if child is None or child.poll() is not None:
        return
    child.send_signal(signal.SIGINT)
    try:
        child.wait(timeout=5)
    except subprocess.TimeoutExpired:
        child.kill()
        child.wait(timeout=5)


def run(args):
    results = LAB / 'partG-results'
    results.mkdir(exist_ok=True)
    run_dir = Path(tempfile.mkdtemp(prefix=datetime.now().strftime('run-%Y%m%d-%H%M%S-'),
                                    dir=results))
    print(f'Results: {run_dir}', flush=True)
    screen = child = worker_output = None

    def event(name, **details):
        entry = {'t': datetime.now().astimezone().isoformat(timespec='seconds'),
                 'event': name, **details}
        with (run_dir / 'handoff.jsonl').open('a', encoding='utf-8') as output:
            output.write(json.dumps(entry) + '\n')
        print(json.dumps(entry), flush=True)

    def show(state, detail):
        event('display', state=state, detail=detail)
        if screen is not None:
            screen.show(state, detail)

    try:
        if not args.no_screen:
            screen = load_screen()
        show('LOADING', 'Preparing local speech')
        model = load_recognizer()
        with tempfile.TemporaryDirectory(prefix='night-handoff-audio-') as temp:
            folder = Path(temp)
            prompts = prepare_prompts(folder)
            event('plan', question='When was a person last detected in the desk area?',
                  interval=args.interval, seconds=args.seconds)
            accepted = False
            for attempt in range(3):
                show('READY', 'Say: Hello')
                play(prompts['ready' if attempt == 0 else 'retry'])
                show('LISTENING', 'Speak now: Hello')
                recording = folder / 'command.wav'
                subprocess.run(['arecord', '-q', '-D', 'pulse', '-f', 'S16_LE',
                                '-r', '16000', '-c', '1', '-d', '5', str(recording)],
                               check=True, timeout=10)
                show('PROCESSING', 'Checking your command')
                try:
                    heard = transcribe(model, recording)
                finally:
                    recording.unlink(missing_ok=True)
                accepted = is_start_command(heard)
                event('recognized', text=heard, accepted=accepted)
                if accepted:
                    break
            if not accepted:
                show('NOT STARTED', 'Command not recognized. Please retry.')
                time.sleep(3)
                return 2

            show('STARTING', 'Checking camera and log')
            ready = run_dir / 'ready.json'
            worker_output = (run_dir / 'worker.txt').open('w', encoding='utf-8')
            child = subprocess.Popen(
                [str(LAB / '.venv/bin/python'), '-u', str(LAB / 'desk_watch.py'),
                 '--log', str(run_dir / 'night_log.jsonl'), '--ready-file', str(ready),
                 '--interval', str(args.interval), '--seconds', str(args.seconds)],
                cwd=LAB, stdout=worker_output, stderr=subprocess.STDOUT,
                start_new_session=True)
            confirmed = wait_for_ready(child, ready)
            event('watch_started', worker=confirmed)
            show('WATCHING', f'Watch started\nEvery {args.interval:g} s')
            play(prompts['started'])
            shown_at = time.monotonic()
            dark = False
            while child.poll() is None:
                if args.seconds and time.monotonic() - shown_at > args.seconds + 15:
                    raise TimeoutError('Camera demo did not finish on time; stopping the worker.')
                if not dark and time.monotonic() - shown_at >= 12:
                    if screen is not None:
                        screen.backlight.value = False
                    event('screen_dark', reason='Night watch continues; microphone is closed')
                    dark = True
                time.sleep(.2)
            if screen is not None:
                screen.backlight.value = True
            if child.returncode != 0:
                raise RuntimeError('Camera worker stopped unexpectedly. See worker.txt.')
            show('DONE', 'Demo finished. Log saved.' if args.seconds else 'Night watch stopped.')
            event('completed', log=str(run_dir / 'night_log.jsonl'))
            time.sleep(3)
            return 0
    except KeyboardInterrupt:
        stop_worker(child)
        if screen is not None:
            screen.backlight.value = True
        show('STOPPED', 'Night watch stopped')
        return 130
    except Exception as exc:
        stop_worker(child)
        if screen is not None:
            screen.backlight.value = True
        show('ERROR', 'Not running. Check terminal.')
        event('error', message=str(exc))
        print(f'Error: {exc}', flush=True)
        time.sleep(3)
        return 1
    finally:
        stop_worker(child)
        if worker_output is not None:
            worker_output.close()
        if screen is not None:
            screen.close()
        print(f'Results saved: {run_dir}', flush=True)


def nonnegative(value):
    number = float(value)
    if not (0 <= number < float('inf')):
        raise argparse.ArgumentTypeError('Use a finite nonnegative number.')
    return number


def request_stop(*_):
    raise KeyboardInterrupt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seconds', type=nonnegative, default=30,
                        help='camera run duration; 0 runs until Ctrl-C')
    parser.add_argument('--interval', type=nonnegative, default=10)
    parser.add_argument('--no-screen', action='store_true', help='diagnostic mode')
    parser.add_argument('--check', action='store_true', help='load local models; no recording or playback')
    parser.add_argument('--transcribe-file', type=Path, help='transcribe an existing WAV without starting the watch')
    args = parser.parse_args()
    if args.interval <= 0:
        parser.error('--interval must be positive')
    if args.transcribe_file:
        text = transcribe(load_recognizer(), args.transcribe_file)
        print(json.dumps({'text': text, 'accepted': is_start_command(text)}))
        return 0
    if args.check:
        import board, digitalio, adafruit_rgb_display.st7789
        load_recognizer()
        with tempfile.TemporaryDirectory(prefix='night-handoff-check-') as temp:
            prompts = prepare_prompts(Path(temp))
            for path in prompts.values():
                with wave.open(str(path), 'rb') as wav:
                    if wav.getnframes() == 0:
                        raise RuntimeError('Empty speech prompt')
        print('Local speech models and display imports OK; no audio played or recorded.')
        return 0
    signal.signal(signal.SIGTERM, request_stop)
    signal.signal(signal.SIGHUP, request_stop)
    return run(args)


if __name__ == '__main__':
    raise SystemExit(main())
