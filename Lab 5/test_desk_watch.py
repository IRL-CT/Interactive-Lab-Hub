import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
from types import SimpleNamespace

import desk_watch


class Clock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now

    def sleep(self, seconds):
        self.now += seconds


class DeskWatchTests(unittest.TestCase):
    def test_people_count_rejects_unrecognized_output(self):
        for reading, expected in [('nobody', 0), ('1 person(s) at center', 1),
                                  ('3 person(s) at close', 3)]:
            self.assertEqual(desk_watch.people_count(reading), expected)
        with self.assertRaises(ValueError):
            desk_watch.people_count('camera failed')

    def test_errors_stay_errors_and_ready_follows_first_valid_log(self):
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / 'watch.jsonl'
            ready = Path(directory) / 'ready.json'
            clock = Clock()
            readings = iter([RuntimeError('frame missing'), '2 person(s) at center', 'nobody'])

            def sample():
                if clock.now < 2:
                    self.assertFalse(ready.exists())
                else:
                    metadata = json.loads(ready.read_text())
                    self.assertEqual(metadata['log'], str(log.resolve()))
                    self.assertTrue(metadata['pid'] > 0)
                    records = [json.loads(line) for line in log.read_text().splitlines()]
                    self.assertEqual(records[-1]['people'], 2)
                value = next(readings)
                if isinstance(value, Exception):
                    raise value
                return value

            reason = desk_watch.run_sampling(sample, log, ready, 1, 2,
                                             threading.Event(), clock, clock.sleep)
            self.assertEqual(reason, 'duration_complete')
            records = [json.loads(line) for line in log.read_text().splitlines()]
            self.assertEqual([row['event'] for row in records],
                             ['start', 'sample', 'sample', 'sample', 'stop'])
            self.assertEqual(records[1]['status'], 'error')
            self.assertIn('frame missing', records[1]['error'])
            self.assertNotIn('reading', records[1])
            self.assertEqual(records[2]['reading'], '2 person(s) at center')
            self.assertEqual(records[3]['people'], 0)
            self.assertNotIn('reading', records[0])
            self.assertNotIn('reading', records[-1])
            self.assertTrue(all(datetime.fromisoformat(row['t']).tzinfo for row in records))
            self.assertFalse(ready.exists())

    def test_repeated_startup_errors_have_a_deadline(self):
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / 'watch.jsonl'
            ready = Path(directory) / 'ready.json'
            clock = Clock()

            def sample():
                raise ValueError('bad inference')

            reason = desk_watch.run_sampling(sample, log, ready, 10, 0,
                                             threading.Event(), clock, clock.sleep)
            self.assertEqual(reason, 'startup_timeout')
            self.assertLessEqual(clock.now, 30)
            self.assertFalse(ready.exists())
            rows = [json.loads(line) for line in log.read_text().splitlines()]
            self.assertTrue(all(row['status'] == 'error' for row in rows[1:-1]))
            self.assertEqual(rows[-1]['reason'], 'startup_timeout')

    def test_stop_event_clears_ready_file(self):
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / 'watch.jsonl'
            ready = Path(directory) / 'ready.json'
            stop = threading.Event()
            clock = Clock()

            def sleep(seconds):
                self.assertTrue(ready.exists())
                stop.set()

            reason = desk_watch.run_sampling(lambda: 'nobody', log, ready, 10, 0,
                                             stop, clock, sleep)
            self.assertEqual(reason, 'stop_requested')
            self.assertFalse(ready.exists())

    def test_camera_unavailable_fails_without_retry(self):
        with tempfile.TemporaryDirectory() as directory:
            clock = Clock()

            def sample():
                raise desk_watch.CameraUnavailable('camera 0 did not open')

            reason = desk_watch.run_sampling(sample, Path(directory) / 'watch.jsonl',
                                             Path(directory) / 'ready.json', 10, 0,
                                             threading.Event(), clock, clock.sleep)
            self.assertEqual(reason, 'camera_unavailable')
            self.assertEqual(clock.now, 0)


    def test_camera_discards_buffered_frames_before_each_inference(self):
        class BufferedCamera:
            def __init__(self):
                self.frames = ['stale'] * 4 + ['fresh']
                self.settings = []

            def set(self, key, value):
                self.settings.append((key, value))
                return False  # Some drivers ignore the small-buffer request.

            def isOpened(self):
                return True

            def grab(self):
                return bool(self.frames and self.frames.pop(0))

            def read(self):
                return (True, self.frames.pop(0)) if self.frames else (False, None)

        camera = BufferedCamera()
        cv2 = SimpleNamespace(CAP_PROP_FRAME_WIDTH=3, CAP_PROP_FRAME_HEIGHT=4,
                              CAP_PROP_BUFFERSIZE=38, VideoCapture=lambda index: camera)
        yolo = SimpleNamespace(model=SimpleNamespace(predict=lambda frame, **kw: [frame]),
                               interpret=lambda result: result)
        with patch.dict(sys.modules, cv2=cv2, yolo_to_qwen=yolo):
            sampler = desk_watch.CameraSampler()
            self.assertEqual(sampler(), 'fresh')
            self.assertIn((38, 1), camera.settings)
            camera.frames = ['stale'] * 4 + ['fresh again']
            self.assertEqual(sampler(), 'fresh again')
            with self.assertRaises(RuntimeError):
                sampler()

    def test_cli_lock_signal_and_camera_cleanup(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'cv2.py').write_text("""
CAP_PROP_FRAME_WIDTH = 3
CAP_PROP_FRAME_HEIGHT = 4
CAP_PROP_BUFFERSIZE = 38
class VideoCapture:
    def __init__(self, index):
        assert index == 0
    def set(self, key, value):
        assert (key, value) in ((3, 640), (4, 480), (38, 1))
    def isOpened(self):
        return True
    def grab(self):
        return True
    def read(self):
        return True, 'frame'
    def release(self):
        open('released.txt', 'w').write('released')
""")
            (root / 'yolo_to_qwen.py').write_text("""
class Model:
    def predict(self, frame, **options):
        assert frame == 'frame'
        assert options == dict(imgsz=320, conf=0.4, classes=[0], verbose=False, save=False)
        return ['result']
model = Model()
def interpret(result):
    assert result == 'result'
    return '1 person(s) at center/close'
""")
            log, ready = root / 'watch.jsonl', root / 'ready.json'
            worker = root / 'desk_watch.py'
            worker.write_text(Path(desk_watch.__file__).read_text())
            command = [sys.executable, str(worker),
                       '--log', str(log), '--ready-file', str(ready), '--seconds', '0']
            environment = dict(os.environ, PYTHONPATH=str(root))
            first = subprocess.Popen(command, cwd=root, env=environment,
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            try:
                deadline = time.monotonic() + 5
                while not ready.exists() and first.poll() is None and time.monotonic() < deadline:
                    time.sleep(0.01)
                self.assertTrue(ready.exists(), 'CLI never became ready')
                self.assertEqual(json.loads(ready.read_text())['pid'], first.pid)
                second = subprocess.run(command, cwd=root, env=environment,
                                        capture_output=True, text=True, timeout=3)
                self.assertEqual(second.returncode, 1)
                self.assertTrue(ready.exists(), 'second watcher removed active readiness')
                first.terminate()
                stdout, stderr = first.communicate(timeout=3)
                self.assertEqual(first.returncode, 0, stderr)
                self.assertFalse(ready.exists())
                self.assertEqual((root / 'released.txt').read_text(), 'released')
                rows = [json.loads(line) for line in log.read_text().splitlines()]
                self.assertEqual(rows[1]['people'], 1)
                self.assertEqual(rows[-1]['reason'], 'stop_requested')
            finally:
                if first.poll() is None:
                    first.kill()
                first.communicate()

if __name__ == '__main__':
    unittest.main()
