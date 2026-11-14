"""Pet Night Diary: a single night session, with optional PiTFT interaction."""
import argparse
from datetime import datetime
import json
import math
import multiprocessing as mp
import os
from pathlib import Path
import signal
import time
import uuid

from pet_detector import ConfirmationFilter, PRESENT, ABSENT, UNKNOWN, detector_worker
from pet_display import Display
from pet_morning import summarize, morning_report

ROOT = Path(__file__).resolve().parent


def now():
    return datetime.now().astimezone().isoformat(timespec='milliseconds')


class NightLog:
    def __init__(self, directory, config, mode):
        directory.mkdir(parents=True, exist_ok=True)
        self.path = directory / (datetime.now().strftime('night_%Y%m%d_%H%M%S_') + uuid.uuid4().hex[:8] + '.jsonl')
        self.file = self.path.open('x', encoding='utf-8')
        self.start = time.monotonic()
        self.write('start', config=config, mode=mode)

    def write(self, event, **fields):
        entry = {'t': now(), 'elapsed': round(time.monotonic()-self.start, 3), 'event': event, **fields}
        self.file.write(json.dumps(entry) + '\n')
        self.file.flush()
        if event in ('start', 'heartbeat', 'end'):
            os.fsync(self.file.fileno())

    def close(self, reason):
        try:
            self.write('end', reason=reason)
        finally:
            self.file.close()


class Worker:
    def __init__(self, config):
        context = mp.get_context('spawn')
        self.connection, child = context.Pipe()
        self.process = context.Process(target=detector_worker, args=(child, config), daemon=True)
        self.process.start()
        child.close()

    def close(self):
        if self.process.is_alive():
            self.process.terminate()
        self.process.join(timeout=2)
        if self.process.is_alive():
            self.process.kill()
            self.process.join(timeout=2)
        self.connection.close()


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--terminal', action='store_true', help='skip PiTFT initialization')
    parser.add_argument('--start', action='store_true', help='start without pressing A')
    parser.add_argument('--seconds', type=float, help='automatic stop after this many seconds')
    parser.add_argument('--interval', type=float, default=10)
    parser.add_argument('--confirm', type=int, default=3)
    parser.add_argument('--camera', type=int, default=0)
    parser.add_argument('--model', type=Path, default=ROOT/'yolo26n_ncnn_model')
    parser.add_argument('--roi', type=float, nargs=4, default=[0, 0, 1, 1], metavar=('X1', 'Y1', 'X2', 'Y2'))
    parser.add_argument('--overlap', type=float, default=.5)
    parser.add_argument('--conf', type=float, default=.4)
    parser.add_argument('--timeout', type=float, default=60, help='camera/inference deadline in seconds')
    parser.add_argument('--data-dir', type=Path, default=ROOT/'pet_night_data')
    parser.add_argument('--no-qwen', action='store_true')
    parser.add_argument('--simulate', action='store_true', help='explicit synthetic input; no camera/model required')
    args = parser.parse_args()
    positive = [args.interval, args.timeout] + ([args.seconds] if args.seconds is not None else [])
    if any(not math.isfinite(v) or v <= 0 for v in positive) or args.confirm < 1:
        parser.error('interval, timeout, seconds and confirm must be positive finite values')
    x1, y1, x2, y2 = args.roi
    if not (0 <= x1 < x2 <= 1 and 0 <= y1 < y2 <= 1):
        parser.error('ROI must satisfy 0 <= x1 < x2 <= 1 and 0 <= y1 < y2 <= 1')
    if not (0 < args.overlap <= 1 and 0 < args.conf <= 1):
        parser.error('overlap and conf must be in (0, 1]')
    return args


def run(args, display, stop):
    config = {'interval': args.interval, 'confirm': args.confirm, 'camera': args.camera,
              'model': str(args.model.resolve()), 'roi': args.roi, 'overlap': args.overlap, 'conf': args.conf}
    mode = 'SIMULATED' if args.simulate else ('short-session' if args.seconds else 'overnight')
    log = NightLog(args.data_dir, config, mode)
    print(f'Log ({mode}): {log.path}', flush=True)
    filtering = ConfirmationFilter(args.confirm)
    worker = None
    pending = ready = False
    deadline = next_sample = next_beat = 0
    blank_at = time.monotonic()+3
    error_active = False
    reason = 'stopped'
    sample_index = 0
    first_valid = True
    previous_sample = None
    display.show('SIMULATED session' if args.simulate else 'Monitoring started',
                 'Synthetic input' if args.simulate else 'Checking camera + YOLO', 'Hold B 1.5s to stop')
    try:
        while not stop['requested']:
            tick = time.monotonic()
            if display.poll() == 'b':
                reason = 'button_b'
                break
            if args.seconds and tick-log.start >= args.seconds:
                reason = 'duration'
                break
            if tick >= blank_at:
                display.blank()
            if tick >= next_beat:
                log.write('heartbeat', worker_ready=ready, pending=pending)
                next_beat = tick + 600
            result = None
            if args.simulate and tick >= next_sample:
                sequence = [PRESENT]*5 + [ABSENT] + [PRESENT]*3 + [UNKNOWN]*2 + [ABSENT]*5
                raw = sequence[sample_index % len(sequence)]
                result = {'raw': raw, 'in_roi': None if raw == UNKNOWN else raw == PRESENT,
                          'confidence': .9 if raw == PRESENT else None, 'captured_at': now()}
                if raw == UNKNOWN:
                    result['error'] = 'SIMULATED camera disconnection'
                sample_index += 1
            elif not args.simulate:
                if worker is None and tick >= next_sample:
                    worker = Worker(config)
                    deadline = tick + args.timeout
                if worker is not None:
                    if worker.connection.poll():
                        try:
                            message = worker.connection.recv()
                        except EOFError:
                            message = {'fatal': 'Detector process exited'}
                        if message.get('ready'):
                            ready = True
                        elif 'fatal' in message:
                            log.write('error', error=message['fatal'])
                            display.show('Setup error', message['fatal'][:70])
                            reason = 'setup_error'
                            break
                        else:
                            result, pending = message, False
                    if (pending or not ready) and tick > deadline:
                        result = {'raw': UNKNOWN, 'in_roi': None, 'confidence': None,
                                  'error': 'Camera/model timeout; restarting worker'}
                        worker.close()
                        worker, ready, pending = None, False, False
                    if worker and ready and not pending and result is None and tick >= next_sample:
                        worker.connection.send('sample')
                        pending, deadline = True, tick + args.timeout
            if result is not None:
                sampled_at = time.monotonic()
                if previous_sample is not None and sampled_at-previous_sample > args.interval*1.5:
                    filtering.update(UNKNOWN)
                    log.write('gap', seconds=sampled_at-previous_sample)
                previous_sample = sampled_at
                old = filtering.state
                confirmed = filtering.update(result['raw'])
                log.write('sample', **result, confirmed=confirmed, streak=filtering.count)
                if result['raw'] == UNKNOWN:
                    log.write('camera_or_inference_error', error=result.get('error', 'unknown'))
                    print('Unknown sample:', result.get('error'), flush=True)
                    error_active = True
                else:
                    if error_active:
                        log.write('recovery')
                    if first_valid or error_active:
                        display.show('Good Night, Longan!',
                                     'SIMULATED input ready' if args.simulate else 'Camera + YOLO ready',
                                     'Hold B to stop')
                        blank_at = time.monotonic()+3
                    first_valid = False
                    error_active = False
                if old != confirmed:
                    log.write('transition', previous=old, confirmed=confirmed)
                print(f'{now()} raw={result["raw"]} confirmed={confirmed}', flush=True)
                # Target cadence without a burst of catch-up inference.
                next_sample = max(tick, next_sample) + args.interval
            time.sleep(.05)
        if stop['requested']:
            reason = 'signal'
    except Exception as error:
        reason = 'error'
        log.write('error', error=str(error))
        raise
    finally:
        if worker:
            worker.close()
        log.close(reason)
    return log.path


def main():
    args = parse_args()
    stop = {'requested': False}
    def request_stop(signum, frame):
        stop['requested'] = True
    signal.signal(signal.SIGINT, request_stop)
    signal.signal(signal.SIGTERM, request_stop)
    display = Display(args.terminal)
    try:
        if not args.start:
            display.show('Pet Night Diary', 'Press A to start')
            while not stop['requested']:
                event = display.poll()
                if event == 'a':
                    break
                if event == 'b':
                    return
                time.sleep(.05)
        if stop['requested']:
            return
        path = run(args, display, stop)
        stats = summarize(path)
        display.show('Good Morning, Longan!', 'Preparing report...')
        report, source = morning_report(stats, not args.no_qwen and not stop['requested'])
        output = path.with_suffix('.report.json')
        with output.open('x') as file:
            json.dump({'statistics': stats, 'report': report, 'source': source}, file, indent=2)
        print(json.dumps(stats, indent=2), flush=True)
        print(f'\n[{stats["mode"]}; {source}] {report}\nSaved: {output}', flush=True)
        last = stats['last_confirmed_detection']
        last = datetime.fromisoformat(last).strftime('%m/%d %H:%M:%S') if last else 'Not confirmed'
        pages = [('Good Morning, Longan!', 'Last detected:', last, 'A: next / Hold B: exit'),
                 ('Sampled intervals', f'Detected: {stats["supported_seconds"][PRESENT]:.0f}s',
                  f'Not detected: {stats["supported_seconds"][ABSENT]:.0f}s', 'Not a sleep measurement'),
                 ('Data quality', f'Samples: {stats["samples"]}',
                  f'Unknown: {stats["raw_counts"].get(UNKNOWN, 0)}', f'Mode: {stats["mode"]}')]
        import textwrap
        report_lines = textwrap.wrap(report, 27)
        pages.extend(tuple(report_lines[i:i+5]) for i in range(0, len(report_lines), 5))
        page = 0
        display.show(*pages[page])
        while display.panel and not stop['requested']:
            event = display.poll()
            if event == 'b':
                break
            if event == 'a':
                page = (page+1) % len(pages)
                display.show(*pages[page])
            time.sleep(.05)
    finally:
        display.close()


if __name__ == '__main__':
    main()
