import json
from pathlib import Path
import tempfile
import unittest

from desk_report_facts import load_facts, render_report


def event(kind, time, **fields):
    return dict(event=kind, t=time, **fields)


def sample(time, people):
    reading = 'nobody' if people == 0 else f'{people} person(s) at center/close'
    return event('sample', time, status='ok', people=people, reading=reading)


class DeskReportFactsTests(unittest.TestCase):
    def load(self, rows, interval=10):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'watch.jsonl'
            path.write_text(''.join(json.dumps(row) + '\n' for row in rows))
            return load_facts(path, interval)

    def test_actual_three_sample_fixture_does_not_invent_people_or_duration(self):
        prefix = '2026-11-01T15:40:'
        facts = self.load([
            event('start', prefix + '26.263-05:00', pid=123),
            sample(prefix + '29.695-05:00', 1),
            sample(prefix + '40.066-05:00', 1),
            sample(prefix + '50.381-05:00', 0),
            event('stop', prefix + '59.721-05:00', reason='duration_complete')])
        self.assertEqual(facts, dict(
            valid_samples=3, samples_with_people=2, max_people=1,
            last_person_detection=prefix + '40.066-05:00',
            last_sample_time=prefix + '50.381-05:00', last_sample_people=0,
            error_samples=0, long_gap_count=0, observation_seconds=30.026,
            session_closed=True))
        report = render_report(facts)
        self.assertIn('30.0 seconds', report)
        self.assertIn('2 of 3', report)
        self.assertIn('maximum 1', report)
        self.assertIn(prefix + '40.066-05:00', report)
        self.assertIn('0 people', report)
        self.assertIn('sleep', report)
        self.assertEqual(len(report.split('. ')), 3)

    def test_midnight_uses_dates_and_elapsed_seconds(self):
        facts = self.load([
            event('start', '2026-11-01T23:59:58-05:00'),
            sample('2026-11-01T23:59:59-05:00', 2),
            sample('2026-11-02T00:00:09-05:00', 0),
            event('stop', '2026-11-02T00:00:10-05:00')])
        self.assertEqual(facts['observation_seconds'], 11.0)
        report = render_report(facts)
        self.assertIn('2026-11-01T23:59:59', report)
        self.assertIn('2026-11-02T00:00:09', report)
        self.assertIn('11.0 seconds', report)

    def test_all_zero_samples_do_not_claim_sleep(self):
        facts = self.load([event('start', '2026-11-01T10:00:00Z'),
                           sample('2026-11-01T10:00:01Z', 0),
                           event('stop', '2026-11-01T10:00:02Z')])
        self.assertEqual(facts['samples_with_people'], 0)
        self.assertEqual(facts['max_people'], 0)
        self.assertIsNone(facts['last_person_detection'])
        self.assertIn('No person detection', render_report(facts))

    def test_errors_are_unknown_not_nobody_and_gaps_include_them(self):
        facts = self.load([event('start', '2026-11-01T10:00:00Z'),
                           sample('2026-11-01T10:00:01Z', 1),
                           event('sample', '2026-11-01T10:00:22Z',
                                 status='error', error='camera failed'),
                           event('stop', '2026-11-01T10:00:43Z')])
        self.assertEqual(facts['error_samples'], 1)
        self.assertEqual(facts['long_gap_count'], 2)
        self.assertEqual(facts['valid_samples'], 1)
        self.assertEqual(facts['last_sample_time'], '2026-11-01T10:00:22Z')
        self.assertIsNone(facts['last_sample_people'])
        self.assertEqual(facts['observation_seconds'], 42.0)
        self.assertIn('unknown', render_report(facts))

    def test_all_error_session_cannot_assess_presence(self):
        facts = self.load([event('start', '2026-11-01T10:00:00Z'),
                           event('sample', '2026-11-01T10:00:01Z',
                                 status='error', error='no frame'),
                           event('stop', '2026-11-01T10:00:02Z')])
        self.assertEqual(facts['valid_samples'], 0)
        self.assertIsNone(facts['max_people'])
        self.assertIsNone(facts['observation_seconds'])
        self.assertIn('cannot be assessed', render_report(facts))
        self.assertIn('errors: 1', render_report(facts))

    def test_open_empty_and_unfinished_sessions_do_not_imply_full_night(self):
        for rows in ([], [event('start', '2026-11-01T10:00:00Z')]):
            facts = self.load(rows)
            self.assertFalse(facts['session_closed'])
            self.assertIsNone(facts['last_sample_time'])
            self.assertIn('No observations', render_report(facts))
            self.assertIn('no stop event', render_report(facts))
        facts = self.load([event('start', '2026-11-01T10:00:00Z'),
                           sample('2026-11-01T10:00:01Z', 1),
                           sample('2026-11-01T10:00:11Z', 0)])
        self.assertEqual(facts['observation_seconds'], 10.0)
        self.assertIn('no stop event', render_report(facts))

    def test_gap_threshold_is_strict_and_interval_is_configurable(self):
        rows = [event('start', '2026-11-01T10:00:00Z'),
                sample('2026-11-01T10:00:01Z', 0),
                sample('2026-11-01T10:00:21Z', 0),
                event('stop', '2026-11-01T10:00:41Z')]
        self.assertEqual(self.load(rows)['long_gap_count'], 0)
        self.assertEqual(self.load(rows, interval=5)['long_gap_count'], 2)
        for interval in (0, -1, float('nan'), float('inf'), True):
            with self.subTest(interval=interval), self.assertRaises(ValueError):
                self.load([], interval)

    def test_invalid_rows_fail_instead_of_being_silently_omitted(self):
        start = event('start', '2026-11-01T10:00:00Z')
        good = sample('2026-11-01T10:00:01Z', 1)
        bad_rows = [None, {}, dict(good, people=True), dict(good, people=-1),
                    dict(good, people=1.0), dict(good, people=2),
                    dict(good, reading='camera failed'), dict(good, reading=None),
                    dict(good, t='2026-11-01T10:00:01'),
                    dict(good, t='not a time'), dict(good, event='other'),
                    dict(good, status='error'), dict(start, reading='nobody')]
        for row in bad_rows:
            with self.subTest(row=row), self.assertRaisesRegex(ValueError, 'line'):
                self.load([start, row])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'bad.jsonl'
            for contents in ('not json\n', '\n'):
                path.write_text(contents)
                with self.assertRaisesRegex(ValueError, 'line 1'):
                    load_facts(path)

    def test_multiple_sessions_and_out_of_order_events_are_rejected(self):
        start = event('start', '2026-11-01T10:00:00Z')
        stop = event('stop', '2026-11-01T10:00:02Z')
        rows = [sample('2026-11-01T10:00:01Z', 0)]
        for events in ([start, start], [start, stop, stop], [start, stop] + rows,
                       [start] + rows + [sample('2026-11-01T10:00:00Z', 0)],
                       [start, stop, event('start', '2026-11-01T10:00:03Z')], rows):
            with self.subTest(events=events), self.assertRaises(ValueError):
                self.load(events)


if __name__ == '__main__':
    unittest.main()
