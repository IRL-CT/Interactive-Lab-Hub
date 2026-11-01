"""
Part I: turn night_log.jsonl into a short morning report about whether anyone got up
and walked around in the night. The camera cannot tell asleep from awake, so the report
says "got up", never "sleepwalking".

The episodes (when someone was upright, and for how long) are counted here in plain
code, so the small model only has to put facts into words, not find them.

    python morning.py                          # print the report
    python morning.py --model qwen3:0.6b
    python morning.py --log some_other.jsonl
"""
import argparse
import collections
import datetime
import json
import threading
import time

import requests

from screen import Screen
from voice import speak

parser = argparse.ArgumentParser()
parser.add_argument("--log", default="night_log.jsonl")
parser.add_argument("--model", default="qwen3.5:0.8b")
parser.add_argument("--print-only", action="store_true", help="only print the report: no screen, no voice")
args = parser.parse_args()

entries = [json.loads(line) for line in open(args.log) if line.strip()]
readings = [e for e in entries if "reading" in e]
seen = [e for e in readings if e["reading"] != "nobody"]
beats = sum(1 for e in entries if e.get("alive"))
per_hour = dict(sorted(collections.Counter(e["t"][11:13] + ":00" for e in seen).items()))

span = f"{entries[0]['t'][11:16]} to {entries[-1]['t'][11:16]}" if entries else "no entries"
print(f"{len(readings)} changes, {len(seen)} with someone in view, {beats} heartbeats, {span}")
print("changes per hour:", per_hour)


def deliver(text):
    """Print the report, show it on the Mini PiTFT page by page, and say it aloud."""
    print("\n" + text, flush=True)
    if args.print_only:
        return
    screen = Screen()
    pages = screen.pages(text)
    talker = threading.Thread(target=speak, args=(text,))
    talker.start()
    i = 0
    while pages and (talker.is_alive() or i < len(pages)):      # every page at least once
        screen.lines(pages[i % len(pages)])
        i += 1
        talker.join(timeout=4)
        if not talker.is_alive() and i < len(pages):
            time.sleep(4)
    talker.join()
    if pages:
        screen.lines(pages[0])                                  # leave the first page up


def clock(iso):
    return datetime.datetime.fromisoformat(iso)


# An episode starts when a reading says "upright" and ends at the next reading that does not.
episodes, start = [], None
for e in readings:
    if "upright" in e["reading"]:
        if start is None:
            start = e["t"]
    elif start is not None:
        then = "left the camera's view" if e["reading"] == "nobody" else "lay down again"
        episodes.append((start, e["t"], then))
        start = None
if start is not None:                          # still up when the log stopped
    episodes.append((start, entries[-1]["t"], "was still up when the log ended"))

if not entries:
    raise SystemExit("\nThe log is empty: the camera may not have run last night.")
if not seen:                                   # nothing to summarize: say so, do not ask the model
    deliver(f"Quiet night. The camera watched from {span} and saw nobody, "
            "so I cannot say whether you stayed in bed.")
    raise SystemExit
if not episodes:
    deliver(f"Quiet night. The camera watched from {span} and nobody got up.")
    raise SystemExit

facts = "\n".join(
    f"- got up at {s[11:16]}, up for {max(1, round((clock(t) - clock(s)).total_seconds() / 60))} min, then {then}"
    for s, t, then in episodes
)
prompt = f"""You are a bedside night-watch device. The camera watched from {span}.
It noticed {len(episodes)} time(s) when someone was upright (standing or sitting up):

{facts}

Write a warm three-sentence morning report. Say how many times they got up, when, and for how long.
Say "got up", never "sleepwalking", because a camera cannot tell if someone is asleep.
Only use facts from the list above."""

print("\n" + facts, flush=True)
r = requests.post("http://localhost:11434/api/generate", json={
    "model": args.model,
    "prompt": prompt,
    "think": False,
    "stream": False,
    "options": {"num_ctx": 4096, "temperature": 0.3},
}, timeout=600)
r.raise_for_status()
deliver(r.json()["response"].strip())
