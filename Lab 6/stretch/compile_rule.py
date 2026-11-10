#!/usr/bin/env python3
"""
Turn a natural-language request into a plain MQTT rule, using Ollama.

    python compile_rule.py team1

Reads the team's device descriptions, asks the local model to write a rule,
checks it, shows it to you, and saves it to rule.json only if you agree.
The model is used once here, at setup time. run_rule.py runs the rule without it.
"""

import json
import os
import sys
import urllib.request

from common import read_descriptions

OLLAMA_URL = 'http://localhost:11434/api/chat'
MODEL = os.environ.get('OLLAMA_MODEL', 'qwen2.5:1.5b')  # use whichever Qwen you pulled

SYSTEM = """You connect devices on an MQTT network. You are given the devices'
descriptions and a person's request. Reply with JSON only, in this form:
{"when": {"topic": "...", "equals": "..."},
 "then": {"topic": "...", "message": "..."},
 "cooldown_seconds": 0,
 "explanation": "one sentence a non-expert can check"}
"when.topic" must be a topic some device publishes. "then.topic" must be a
topic some device accepts. Use "equals": null to match any message.
If the request is ambiguous, still answer, and say what you assumed in
"explanation"."""


def ask_model(devices, request):
    body = {
        'model': MODEL,
        'stream': False,
        'format': 'json',
        'messages': [
            {'role': 'system', 'content': SYSTEM},
            {'role': 'user', 'content': 'Devices:\n' + json.dumps(devices, indent=1)
                                        + '\n\nRequest: ' + request},
        ],
    }
    req = urllib.request.Request(OLLAMA_URL, json.dumps(body).encode(),
                                 {'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=300) as resp:
        return json.loads(json.loads(resp.read())['message']['content'])


def check(rule, devices):
    """Small models invent topics. Only accept topics a device actually listed."""
    published = {p['topic'] for d in devices for p in d.get('publishes', [])}
    accepted = {a['topic'] for d in devices for a in d.get('accepts', [])}
    problems = []
    if rule.get('when', {}).get('topic') not in published:
        problems.append(f"no device publishes {rule.get('when', {}).get('topic')!r}")
    if rule.get('then', {}).get('topic') not in accepted:
        problems.append(f"no device accepts {rule.get('then', {}).get('topic')!r}")
    return problems


def main():
    team = sys.argv[1]
    devices = read_descriptions(team)
    if not devices:
        sys.exit(f'No device descriptions found under IDD/{team}/devices/. Run describe.py first.')
    print(f'Found {len(devices)} devices: ' + ', '.join(d['name'] for d in devices))

    request = input('\nWhat should happen? > ')
    print(f'Asking {MODEL} (this can take a while on a Pi)...')
    rule = ask_model(devices, request)

    print('\nProposed rule:\n' + json.dumps(rule, indent=2))
    problems = check(rule, devices)
    if problems:
        sys.exit('Rejected: ' + '; '.join(problems) + '. Try rewording the request.')
    if input('\nSave this rule? [y/N] ').strip().lower() == 'y':
        with open('rule.json', 'w') as f:
            json.dump(rule, f, indent=2)
        print('Saved rule.json. Start it with: python run_rule.py')


if __name__ == '__main__':
    main()
