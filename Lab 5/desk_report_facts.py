"""Deterministic facts and a cautious three-sentence desk-watch report."""
from datetime import datetime
import json
import math
from pathlib import Path
import re


def _row_values(row):
    if not isinstance(row, dict):
        raise ValueError('expected a JSON object')
    kind, stamp = row.get('event'), row.get('t')
    if kind not in ('start', 'sample', 'stop'):
        raise ValueError('event must be start, sample, or stop')
    if not isinstance(stamp, str) or 'T' not in stamp:
        raise ValueError('t must be an aware ISO timestamp')
    time = datetime.fromisoformat(stamp.replace('Z', '+00:00'))
    if time.utcoffset() is None:
        raise ValueError('t must include a timezone')
    if kind != 'sample':
        if any(key in row for key in ('reading', 'people', 'status', 'error')):
            raise ValueError('start/stop events cannot contain sample data')
        return kind, time, stamp, None
    if row.get('status') == 'error':
        if ('reading' in row or 'people' in row or
                not isinstance(row.get('error'), str) or not row['error'].strip()):
            raise ValueError('error samples need an error and no reading/people')
        return kind, time, stamp, None
    if row.get('status') != 'ok' or 'error' in row:
        raise ValueError('sample status must be ok or error')
    people, reading = row.get('people'), row.get('reading')
    if type(people) is not int or people < 0 or not isinstance(reading, str):
        raise ValueError('ok samples need a nonnegative integer people and a reading')
    match = re.fullmatch(r'(\d+) person\(s\) at .+', reading)
    count = 0 if reading == 'nobody' else (int(match[1]) if match else None)
    if count != people:
        raise ValueError('reading is unrecognized or disagrees with people')
    return kind, time, stamp, people


def load_facts(path, interval=10):
    """Read one complete or unfinished JSONL session; invalid rows raise ValueError.

    last_sample_time includes failed samples; their last_sample_people is None.
    observation_seconds is an observed span, never total presence or sleep time.
    """
    if (type(interval) not in (int, float) or not math.isfinite(interval)
            or interval <= 0):
        raise ValueError('interval must be a finite positive number')
    facts = dict(valid_samples=0, samples_with_people=0, max_people=None,
                 last_person_detection=None, last_sample_time=None,
                 last_sample_people=None, error_samples=0, long_gap_count=0,
                 observation_seconds=None, session_closed=False)
    started = False
    previous = first_valid = last_sample = stop_time = None
    with Path(path).open(encoding='utf-8') as source:
        for number, line in enumerate(source, 1):
            try:
                row = json.loads(line)
                kind, time, stamp, people = _row_values(row)
                if previous is not None and time < previous:
                    raise ValueError('timestamps must be chronological')
                if facts['session_closed']:
                    raise ValueError('events after stop or multiple sessions are unsupported')
                if kind == 'start':
                    if started:
                        raise ValueError('multiple start events are unsupported')
                    started = True
                elif not started:
                    raise ValueError('session must begin with a start event')
                elif kind == 'stop':
                    facts['session_closed'] = True
                    stop_time = time
                    if last_sample is not None and (time - last_sample).total_seconds() > 2 * interval:
                        facts['long_gap_count'] += 1
                else:
                    if last_sample is not None and (time - last_sample).total_seconds() > 2 * interval:
                        facts['long_gap_count'] += 1
                    last_sample = time
                    facts['last_sample_time'] = stamp
                    facts['last_sample_people'] = people
                    if people is None:
                        facts['error_samples'] += 1
                    else:
                        if first_valid is None:
                            first_valid = time
                        facts['valid_samples'] += 1
                        maximum = facts['max_people']
                        facts['max_people'] = people if maximum is None else max(maximum, people)
                        if people > 0:
                            facts['samples_with_people'] += 1
                            facts['last_person_detection'] = stamp
                previous = time
            except (ValueError, TypeError, OverflowError) as error:
                raise ValueError(f'line {number}: {error}') from error
    if first_valid is not None:
        end = stop_time if stop_time is not None else last_sample
        facts['observation_seconds'] = round((end - first_valid).total_seconds(), 3)
    return facts


def render_report(facts):
    """Render only measured facts; samples cannot establish sleep or identity."""
    valid = facts['valid_samples']
    if valid:
        first = (f"Across {facts['observation_seconds']:.1f} seconds of observed span, "
                 f"{facts['samples_with_people']} of {valid} valid samples detected people "
                 f"(maximum {facts['max_people']} at once)")
    elif facts['error_samples']:
        first = 'No valid observations were recorded; presence cannot be assessed'
    else:
        first = 'No observations were recorded; presence cannot be assessed'
    last_person = facts['last_person_detection']
    second = (f'Last person detection: {last_person}' if last_person else
              'No person detection was recorded in valid samples')
    if facts['last_sample_time'] is not None:
        people = facts['last_sample_people']
        final = 'unknown due to an error' if people is None else f'{people} people'
        second += f"; last sample at {facts['last_sample_time']}: {final}"
    third = (f"Sampling cannot prove continuous presence or sleep; errors: {facts['error_samples']}; "
             f"long gaps: {facts['long_gap_count']}")
    if not facts['session_closed']:
        third += '; no stop event was recorded, so this session is unfinished'
    return f'{first}. {second}. {third}.'
