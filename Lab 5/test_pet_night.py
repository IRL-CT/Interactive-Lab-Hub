"""Synthetic tests only: do not claim camera, GPIO or overnight validation."""
import json
from pathlib import Path
import subprocess
import sys
import signal
import time
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

from pet_detector import ConfirmationFilter, PRESENT as P, ABSENT as A, UNKNOWN as U, overlap_fraction
from pet_morning import summarize, morning_report, fact_sentences
from pet_night_diary import NightLog, run


class FilteringTests(unittest.TestCase):
    def test_confirm_and_single_miss(self):
        f = ConfirmationFilter(3)
        self.assertEqual([f.update(s) for s in [P, P, P, A, P]], [U, U, P, P, P])
        self.assertEqual([f.update(A) for _ in range(3)], [P, P, A])

    def test_error_breaks_streak_and_state(self):
        f = ConfirmationFilter(3)
        self.assertEqual([f.update(s) for s in [P, P, U, P, P, P, U, A]], [U, U, U, U, U, P, U, U])

    def test_roi_fraction(self):
        self.assertEqual(overlap_fraction([0, 0, 1, 1], [0, 0, .5, 1]), .5)
        self.assertEqual(overlap_fraction([.6, .6, .9, .9], [0, 0, .5, .5]), 0)
        self.assertEqual(overlap_fraction([0, 0, 0, 0], [0, 0, 1, 1]), 0)


class SummaryTests(unittest.TestCase):
    def stats(self, sequence, end=True):
        entries = [{'event': 'start', 't': '2026-10-30T23:59:00-04:00',
                    'config': {'interval': 10}, 'mode': 'SIMULATED'}]
        for elapsed, raw, confirmed in sequence:
            entries.append({'event': 'sample', 't': f't{elapsed}', 'elapsed': elapsed,
                            'raw': raw, 'confirmed': confirmed})
        if end:
            entries.append({'event': 'end', 't': 'end', 'elapsed': 200})
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'night.jsonl'
            path.write_text('\n'.join(json.dumps(e) for e in entries))
            return summarize(path)

    def test_no_bridging_pending_unknown_or_large_gaps(self):
        stats = self.stats([(0, P, U), (10, P, U), (20, P, P), (30, P, P),
                            (40, A, P), (50, U, U), (60, A, U), (70, A, U),
                            (80, A, A), (90, A, A), (150, A, A)])
        self.assertEqual(stats['supported_seconds'], {P: 10, A: 10})
        self.assertEqual(stats['last_confirmed_detection'], 't30')
        self.assertEqual(stats['unclassified_seconds'], 180)
        self.assertEqual(len(stats['periods']), 2)

    def test_no_detection_and_empty(self):
        stats = self.stats([])
        report, _ = morning_report(stats, False)
        self.assertIn('insufficient', report)
        self.assertIsNone(stats['last_confirmed_detection'])
        stats = self.stats([(0, A, U), (10, A, U), (20, A, A), (30, A, A)])
        self.assertEqual(stats['supported_seconds'][A], 10)
        self.assertNotIn('slept', morning_report(stats, False)[0])

    def test_interrupted(self):
        stats = self.stats([(0, P, P), (10, P, P)], end=False)
        self.assertEqual(stats['supported_seconds'][P], 10)
        self.assertTrue(stats['warnings'])

    def test_corrupt_record_breaks_continuity(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'bad.jsonl'
            path.write_text('\n'.join([json.dumps({'event': 'sample', 'elapsed': 0, 'raw': P, 'confirmed': P}),
                                       '{broken', json.dumps({'event': 'sample', 'elapsed': 10, 'raw': P, 'confirmed': P})]))
            stats = summarize(path)
            self.assertEqual(stats['supported_seconds'][P], 0)
            self.assertTrue(stats['warnings'])

    def test_qwen_failure_and_hallucination(self):
        stats = self.stats([(0, P, P)])
        with patch('pet_morning.urlopen', side_effect=OSError('offline')):
            self.assertEqual(morning_report(stats)[1], 'python-fallback')
        with patch('pet_morning.urlopen') as url:
            url.return_value.__enter__.return_value.read.return_value = json.dumps(
                {'response': json.dumps({'sentences': ['Longan slept well for 8 hours.']})}).encode()
            self.assertEqual(morning_report(stats)[1], 'python-fallback')
            url.return_value.__enter__.return_value.read.return_value = json.dumps(
                {'response': json.dumps({'sentences': fact_sentences(stats)})}).encode()
            self.assertEqual(morning_report(stats)[1], 'qwen-verified')

    def test_unique_logs(self):
        with tempfile.TemporaryDirectory() as folder:
            a, b = NightLog(Path(folder), {}, 'SIMULATED'), NightLog(Path(folder), {}, 'SIMULATED')
            a.close('test')
            b.close('test')
            self.assertNotEqual(a.path, b.path)
            self.assertEqual(json.loads(a.path.read_text().splitlines()[-1])['event'], 'end')

    def test_hung_worker_records_unknown_and_stops(self):
        class HungWorker:
            def __init__(self, config):
                self.connection = self
            def poll(self):
                return False
            def close(self):
                pass
        class SilentDisplay:
            def show(self, *args):
                pass
            def poll(self):
                return None
            def blank(self):
                pass
        with tempfile.TemporaryDirectory() as folder:
            args = SimpleNamespace(interval=.05, confirm=3, camera=0, model=Path(folder),
                                   roi=[0, 0, 1, 1], overlap=.5, conf=.4, simulate=False,
                                   seconds=.35, timeout=.06, data_dir=Path(folder))
            with patch('pet_night_diary.Worker', HungWorker):
                path = run(args, SilentDisplay(), {'requested': False})
            stats = summarize(path)
            self.assertGreater(stats['raw_counts'].get(U, 0), 0)
            self.assertEqual(stats['supported_seconds'], {P: 0, A: 0})
            self.assertTrue(stats['end'])

    def test_sigterm_finalizes_log(self):
        with tempfile.TemporaryDirectory() as folder:
            proc = subprocess.Popen([sys.executable, str(Path(__file__).with_name('pet_night_diary.py')),
                                     '--simulate', '--terminal', '--start', '--interval', '.1',
                                     '--no-qwen', '--data-dir', folder],
                                    stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            try:
                deadline = time.monotonic()+5
                while not list(Path(folder).glob('*.jsonl')) and time.monotonic() < deadline:
                    time.sleep(.05)
                proc.send_signal(signal.SIGTERM)
                _, errors = proc.communicate(timeout=5)
                self.assertEqual(proc.returncode, 0, errors)
                path = next(Path(folder).glob('*.jsonl'))
                self.assertTrue(summarize(path)['end'])
            finally:
                if proc.poll() is None:
                    proc.kill()
                    proc.wait()

    def test_simulated_end_to_end(self):
        with tempfile.TemporaryDirectory() as folder:
            result = subprocess.run([sys.executable, str(Path(__file__).with_name('pet_night_diary.py')),
                                     '--simulate', '--terminal', '--start', '--seconds', '1',
                                     '--interval', '.05', '--no-qwen', '--data-dir', folder],
                                    capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            path = next(Path(folder).glob('*.jsonl'))
            stats = summarize(path)
            self.assertEqual(stats['mode'], 'SIMULATED')
            self.assertTrue(stats['end'])
            self.assertTrue(path.with_suffix('.report.json').exists())


if __name__ == '__main__':
    unittest.main()
