"""Compute facts in Python; let local Qwen select only verified sentences."""
import argparse
from collections import Counter
from datetime import datetime
import json
from pathlib import Path
from urllib.request import Request, urlopen

from pet_detector import PRESENT, ABSENT, UNKNOWN


def summarize(path):
    entries, warnings = [], []
    for number, line in enumerate(Path(path).read_text().splitlines(), 1):
        try:
            entry = json.loads(line)
            if not isinstance(entry, dict):
                raise ValueError('not an object')
            entries.append(entry)
        except ValueError:
            # Break continuity across corrupt records; do not silently bridge them.
            entries.append({'event': 'sample', 'raw': UNKNOWN})
            warnings.append(f'Unreadable record on line {number}')
    start = next((e for e in entries if e.get('event') == 'start'), {})
    end = next((e for e in reversed(entries) if e.get('event') == 'end'), {})
    samples = [e for e in entries if e.get('event') == 'sample']
    interval = start.get('config', {}).get('interval', 10)
    counts = Counter(e.get('raw', UNKNOWN) for e in samples)
    seconds = {PRESENT: 0.0, ABSENT: 0.0}
    periods = []
    last_seen = None
    previous = None
    for sample in samples:
        raw = sample.get('raw', UNKNOWN)
        state = sample.get('confirmed', UNKNOWN)
        supported = raw == state and state in seconds
        if supported and state == PRESENT:
            last_seen = sample.get('captured_at', sample.get('t'))
        if previous is not None and supported:
            same = previous.get('confirmed') == state and previous.get('raw') == state
            gap = sample.get('elapsed', 0) - previous.get('elapsed', 0)
            if same and 0 < gap <= 1.5 * interval:
                seconds[state] += gap
                if periods and periods[-1]['state'] == state and periods[-1]['end'] == previous.get('t'):
                    periods[-1]['end'] = sample.get('t')
                    periods[-1]['seconds'] += gap
                else:
                    periods.append({'state': state, 'start': previous.get('t'),
                                    'end': sample.get('t'), 'seconds': gap})
        previous = sample
    if not end:
        warnings.append('No end record: interrupted or still running; no duration extrapolated')
    duration = max(0, end.get('elapsed', samples[-1].get('elapsed', 0) if samples else 0))
    return {'mode': start.get('mode', 'unspecified'), 'start': start.get('t'), 'end': end.get('t'),
            'samples': len(samples), 'raw_counts': dict(counts), 'last_confirmed_detection': last_seen,
            'supported_seconds': {k: round(v, 2) for k, v in seconds.items()},
            'unclassified_seconds': round(max(0, duration-sum(seconds.values())), 2),
            'periods': periods, 'warnings': warnings}


def fact_sentences(stats):
    last = stats['last_confirmed_detection']
    if last:
        first = f"Last confirmed dog detection in the resting area: {last}."
    elif stats['raw_counts'].get(PRESENT, 0):
        first = 'Some frames detected a dog in the resting area, but none reached confirmation.'
    else:
        first = 'No confirmed dog detection in the resting area was recorded.'
    seconds = stats['supported_seconds']
    second = (f"Supported sampled intervals total approximately {seconds[PRESENT]:.0f} seconds of detection "
              f"and {seconds[ABSENT]:.0f} seconds of non-detection.")
    third = 'Detection does not establish sleep, and non-detection does not prove the dog left.'
    if not stats['samples'] or stats['raw_counts'].get(UNKNOWN, 0) == stats['samples']:
        second = 'There is insufficient valid camera data to describe this session.'
    return [first, second, third]


def morning_report(stats, use_qwen=True):
    facts = fact_sentences(stats)
    fallback = ' '.join(facts)
    if not use_qwen or not stats['samples']:
        return fallback, 'python'
    # A tiny model cannot reliably be checked for arbitrary invented paraphrases.
    # Constrain it to composing a report from exact, already verified sentences.
    request = Request('http://localhost:11434/api/generate', headers={'Content-Type': 'application/json'},
                      data=json.dumps({'model': 'qwen3.5:0.8b', 'think': False, 'stream': False,
                          'format': 'json', 'options': {'temperature': 0, 'num_predict': 250},
                          'prompt': 'Compose a factual morning diary from verified data. Return JSON '
                          '{"sentences": [three sentences]}. Copy each supplied sentence exactly once, '
                          'in the supplied order. Add no claims. Verified data: '
                          + json.dumps({k: v for k, v in stats.items() if k != 'periods'})
                          + '\nAllowed sentences: ' + json.dumps(facts)}).encode())
    try:
        with urlopen(request, timeout=45) as response:
            result = json.loads(response.read())
        sentences = json.loads(result['response'])['sentences']
        if sentences != facts:
            raise ValueError('Qwen changed verified facts or wording')
        return ' '.join(sentences), 'qwen-verified'
    except Exception as error:
        print(f'Qwen unavailable/unverified; using Python report: {error}', flush=True)
        return fallback, 'python-fallback'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--log', required=True, type=Path)
    parser.add_argument('--no-qwen', action='store_true')
    args = parser.parse_args()
    stats = summarize(args.log)
    report, source = morning_report(stats, not args.no_qwen)
    print(json.dumps(stats, indent=2))
    print(f'\n[{stats["mode"]}; {source}] {report}')


if __name__ == '__main__':
    main()
