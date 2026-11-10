"""Headless Lab 5 camera sampler; save words, never images or audio."""
import argparse
from datetime import datetime
import fcntl
import json
import math
import os
from pathlib import Path
import re
import signal
import threading
import time


class CameraUnavailable(RuntimeError):
    pass


def people_count(reading):
    if reading == 'nobody':
        return 0
    match = re.fullmatch(r'(\d+) person\(s\) at .+', reading)
    if not match:
        raise ValueError(f'Unrecognized interpreter reading: {reading!r}')
    return int(match.group(1))


def timestamp():
    return datetime.now().astimezone().isoformat(timespec='milliseconds')


def run_sampling(sample, logpath, readyfile, interval, seconds, stop_event,
                 clock=time.monotonic, sleep=None):
    """Run an injected reader; seconds starts after the first valid reading."""
    if not math.isfinite(interval) or interval <= 0 or not math.isfinite(seconds) or seconds < 0:
        raise ValueError('interval must be positive and seconds must be nonnegative')
    logpath, readyfile = Path(logpath).resolve(), Path(readyfile).resolve()
    readyfile.unlink(missing_ok=True)
    temporary = readyfile.with_name(readyfile.name + f'.{os.getpid()}.tmp')
    started, first_valid = clock(), None
    reason = 'stop_requested'
    wait = sleep if sleep is not None else stop_event.wait
    with logpath.open('a', encoding='utf-8') as log:
        def record(**fields):
            row = {'t': timestamp(), **fields}
            log.write(json.dumps(row, ensure_ascii=False) + '\n')
            log.flush()
            os.fsync(log.fileno())
            return row

        record(event='start', pid=os.getpid())
        try:
            while not stop_event.is_set():
                deadline = started + 30 if first_valid is None else (
                    first_valid + seconds if seconds else None)
                if deadline is not None and clock() >= deadline:
                    reason = 'startup_timeout' if first_valid is None else 'duration_complete'
                    break
                try:
                    reading = sample()
                    count = people_count(reading)
                except Exception as error:
                    record(event='sample', status='error', error=f'{type(error).__name__}: {error}')
                    if isinstance(error, CameraUnavailable):
                        reason = 'camera_unavailable'
                        break
                else:
                    row = record(event='sample', status='ok', reading=reading, people=count)
                    if first_valid is None:
                        first_valid = clock()
                        metadata = {'pid': os.getpid(), 't': row['t'], 'log': str(logpath)}
                        with temporary.open('w', encoding='utf-8') as output:
                            json.dump(metadata, output)
                            output.flush()
                            os.fsync(output.fileno())
                        os.replace(temporary, readyfile)
                deadline = started + 30 if first_valid is None else (
                    first_valid + seconds if seconds else None)
                delay = interval if deadline is None else min(interval, max(0, deadline - clock()))
                wait(delay)
        except BaseException:
            reason = 'interrupted_or_failed'
            raise
        finally:
            readyfile.unlink(missing_ok=True)
            temporary.unlink(missing_ok=True)
            record(event='stop', reason=reason)
    return reason


class CameraSampler:
    def __init__(self):
        self.camera = None
        self.model = None

    def __call__(self):
        if self.camera is None:
            try:
                import cv2
                self.camera = cv2.VideoCapture(0)
                self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                try:
                    self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                except Exception:
                    pass  # Buffer size is optional and some backends reject it.
                if not self.camera.isOpened():
                    raise CameraUnavailable('camera 0 did not open')
                from yolo_to_qwen import model, interpret
                self.model, self.interpret = model, interpret
            except Exception as error:
                raise CameraUnavailable(str(error)) from error
        # Discard queued frames after each idle interval, as in the course code.
        for _ in range(4):
            if not self.camera.grab():
                raise RuntimeError('camera frame discard failed')
        ok, frame = self.camera.read()
        if not ok:
            raise RuntimeError('camera frame read failed')
        result = self.model.predict(frame, imgsz=320, conf=0.4, classes=[0],
                                    verbose=False, save=False)[0]
        return self.interpret(result)

    def close(self):
        if self.camera is not None:
            self.camera.release()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--log', required=True, type=Path)
    parser.add_argument('--ready-file', required=True, type=Path)
    parser.add_argument('--interval', type=float, default=10)
    parser.add_argument('--seconds', type=float, default=30, help='0 runs until stopped')
    args = parser.parse_args()
    if not math.isfinite(args.interval) or args.interval <= 0 or not math.isfinite(args.seconds) or args.seconds < 0:
        parser.error('--interval must be positive; --seconds must be nonnegative')
    if args.log.resolve() == args.ready_file.resolve():
        parser.error('--log and --ready-file must be different paths')
    stop = threading.Event()
    for signum in (signal.SIGINT, signal.SIGTERM):
        signal.signal(signum, lambda number, frame: stop.set())
    sampler = CameraSampler()
    # Launch from Lab 5: both its model directory and this shared lock live there.
    with Path('.desk_watch.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print('Another desk watcher already owns the Lab 5 camera.', flush=True)
            return 1
        try:
            reason = run_sampling(sampler, args.log, args.ready_file,
                                  args.interval, args.seconds, stop)
        finally:
            sampler.close()
    return 0 if reason in ('duration_complete', 'stop_requested') else 1


if __name__ == '__main__':
    raise SystemExit(main())
