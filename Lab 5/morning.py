"""Part I: the morning report for the Monster Under the Bed (our version of the lab's morning.py).

    python morning.py                         # report on night_log.jsonl
    python morning.py --log fake_night.jsonl
    python morning.py --model qwen3:0.6b

Reads the monster's log (readings "feet" / "no feet" / "can't see" and trip events),
computes the facts in code, and only asks Qwen to phrase them. Qwen's answer is checked
against the facts; if it gets the number or a time wrong, the fixed line is used instead.
A night with no trips never goes to Qwen.
"""
import argparse
import collections
import datetime as dt
import json

from overnight import check_line, template_line, ask_qwen, anger_level, clock

parser = argparse.ArgumentParser()
parser.add_argument("--log", default="night_log.jsonl")
parser.add_argument("--model", default="qwen3.5:0.8b")
args = parser.parse_args()

entries = [json.loads(line) for line in open(args.log) if line.strip()]

# use only the most recent night in the file (the log keeps growing across runs)
starts = [i for i, e in enumerate(entries) if e.get("event") == "watching"]
night = entries[starts[-1]:] if starts else entries
readings = [e for e in night if "reading" in e]
beats = sum(1 for e in night if e.get("alive"))
span = f"{night[0]['t'][11:16]} to {night[-1]['t'][11:16]}" if night else "no entries"

trips = [{"start": dt.datetime.fromisoformat(e["start"]),
          "end": dt.datetime.fromisoformat(e["start"]) + dt.timedelta(seconds=e["seconds"]),
          "seconds": e["seconds"]}
         for e in night if e.get("event") == "trip_end"]
per_hour = dict(sorted(collections.Counter(f"{t['start']:%H}:00" for t in trips).items()))
blind = [e["t"][11:16] for e in readings if e["reading"] == "can't see"]

print(f"night: {span} | {len(readings)} reading changes | {beats} heartbeats")
print(f"trips: {len(trips)} | per hour: {per_hour or '-'}")
for i, t in enumerate(trips, 1):
    print(f"  trip {i}: {clock(t['start'])}, {t['seconds']} s")
if blind:
    print(f"camera couldn't see at: {', '.join(blind)} (those periods are unknown, not empty)")

if not trips:                       # nothing happened: say so, don't ask the model to invent anything
    print(f"\nQuiet night. The monster watched from {span} and your feet never touched the floor.")
    if blind:
        print("(Except it couldn't see for part of the night, so it can't be completely sure.)")
    raise SystemExit

line, source = ask_qwen(trips, anger_level(trips), args.model, timeout=120)
print(f"\nMONSTER ({source}): {line}")
