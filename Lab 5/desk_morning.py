"""Compute facts from desk_watch.py logs, check Qwen's JSON, and render a factual report.

The report sentences are a Python template. Qwen's original structured answer
and the field-by-field comparison are saved separately, including failures.
"""
import argparse
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
import tempfile
import time


def validate_answer(raw, expected):
    try:
        answer = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return ['Qwen did not return valid JSON.']
    if not isinstance(answer, dict):
        return ['Qwen did not return a JSON object.']
    errors = []
    for key in sorted(set(answer) - set(expected)):
        errors.append(f'Unexpected field: {key}')
    for key, value in expected.items():
        if key not in answer:
            errors.append(f'Missing field: {key}')
            continue
        result = answer[key]
        same_type = type(result) is type(value)
        if type(value) is float:
            same_type = type(result) in (int, float) and math.isfinite(result)
        if not same_type or result != value:
            errors.append(f'{key}: expected {value!r}, received {result!r}')
    return errors


def response_schema():
    properties = {key: {'type': 'integer', 'minimum': 0} for key in (
        'valid_samples', 'samples_with_people', 'error_samples', 'long_gap_count')}
    for key in ('max_people', 'last_sample_people'):
        properties[key] = {'type': ['integer', 'null'], 'minimum': 0}
    for key in ('last_person_detection', 'last_sample_time'):
        properties[key] = {'type': ['string', 'null']}
    properties['observation_seconds'] = {'type': ['number', 'null'], 'minimum': 0}
    properties['session_closed'] = {'type': 'boolean'}
    return {'type': 'object', 'properties': properties,
            'required': list(properties), 'additionalProperties': False}


def main():
    from desk_report_facts import load_facts, render_report
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--log', required=True, type=Path)
    parser.add_argument('--interval', type=float, default=10,
                        help='configured sampling interval in seconds')
    parser.add_argument('--model', default='qwen3.5:0.8b')
    parser.add_argument('--facts-only', action='store_true', help='skip the Qwen comparison')
    args = parser.parse_args()
    source = args.log.resolve()
    original = source.read_bytes()
    checks = source.parent / 'morning-checks'
    checks.mkdir(exist_ok=True)
    output = Path(tempfile.mkdtemp(prefix=datetime.now().strftime('check-%Y%m%d-%H%M%S-'),
                                  dir=checks))
    snapshot = output / 'input_log.jsonl'
    snapshot.write_bytes(original)
    try:
        facts = load_facts(snapshot, interval=args.interval)
    except (ValueError, TypeError) as exc:
        message = f'Cannot produce a reliable report: {exc}'
        (output / 'validation.json').write_text(json.dumps({'status': 'invalid_log',
                                                          'error': message}, indent=2))
        print(message)
        print(f'Saved original input: {output}')
        return 1
    report = render_report(facts)
    (output / 'facts.json').write_text(json.dumps(facts, indent=2) + '\n')
    (output / 'verified_report.txt').write_text(report + '\n', encoding='utf-8')
    print('Verified log report (Python template; not free-form Qwen prose):', flush=True)
    print(report, flush=True)
    validation = {'status': 'skipped', 'source_log': str(source),
                  'source_sha256': hashlib.sha256(original).hexdigest(),
                  'report_source': 'Python template using computed log facts',
                  'long_gap_threshold_seconds': 2 * args.interval,
                  'model': args.model, 'elapsed_seconds': None, 'errors': []}
    if not args.facts_only:
        import requests
        prompt = (
            'Return only a JSON object with exactly the supplied fields and values. '
            'These are computed facts from a sampled camera log. Do not invent anything. '
            'samples_with_people counts samples, NOT distinct people; max_people is the '
            'largest number detected in any single sample. A zero final sample must stay zero. '
            'Keep full timestamps including dates and UTC offsets; duration is in seconds. '
            'Do not infer sleep, identity, continuous absence, or activity.\n\n'
            + json.dumps(facts))
        request = {'model': args.model, 'prompt': prompt, 'format': response_schema(),
                   'think': False, 'stream': False,
                   'options': {'temperature': 0, 'num_predict': 384, 'num_ctx': 4096}}
        (output / 'qwen_request.json').write_text(json.dumps(request, indent=2))
        print('Checking Qwen structured output against the log facts...', flush=True)
        started = time.monotonic()
        try:
            response = requests.post('http://localhost:11434/api/generate',
                                     json=request, timeout=180)
            (output / 'ollama_http_body.txt').write_text(response.text, encoding='utf-8')
            validation['http_status'] = response.status_code
            response.raise_for_status()
            data = response.json()
            (output / 'ollama_response.json').write_text(json.dumps(data, indent=2))
            raw = data['response']
            if not isinstance(raw, str):
                raise ValueError('Ollama response is not a string')
            (output / 'qwen_raw.txt').write_text(raw, encoding='utf-8')
            validation['errors'] = validate_answer(raw, facts)
            validation['status'] = 'rejected' if validation['errors'] else 'accepted'
        except (requests.RequestException, ValueError, KeyError, TypeError) as exc:
            validation['status'] = 'unavailable'
            validation['errors'] = [str(exc)]
        validation['elapsed_seconds'] = round(time.monotonic() - started, 3)
    (output / 'validation.json').write_text(json.dumps(validation, indent=2) + '\n')
    print(f"Qwen fact check: {validation['status']} ({validation['elapsed_seconds']} s)")
    if validation['errors']:
        print('Qwen output was not used for the report: ' + '; '.join(validation['errors']))
    print(f'Saved report, source log, and model evidence: {output}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
