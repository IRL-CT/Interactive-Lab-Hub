"""
Part I: Night at the Desk. Turn night_log.jsonl into the group chat
the objects on my desk had about me while I slept.

    python desk_chat.py
    python desk_chat.py --log some_other.jsonl
    python desk_chat.py --model qwen3:0.6b
"""
import argparse
import datetime
import json
import re

import requests

parser = argparse.ArgumentParser()
parser.add_argument("--log", default="night_log.jsonl")
parser.add_argument("--model", default="qwen3.5:0.8b")
parser.add_argument("--min-gap", type=int, default=60,
                    help="ignore blips shorter than this many seconds (use 10 for a fake night)")
args = parser.parse_args()

COLORS = ["\033[96m", "\033[95m", "\033[93m", "\033[92m", "\033[94m", "\033[91m"]
RESET, BOLD = "\033[0m", "\033[1m"

# YOLO sometimes calls the same thing by another name. Map it back here.
ALIASES = {"tv": "monitor"}


def parse(reading):
    """'1 person(s) at center/far; also cell phone, cup' -> (1, {'cell phone', 'cup'})"""
    head, _, tail = reading.partition("; also ")
    people = 0 if head == "nobody" else int(head.split()[0])
    things = {ALIASES.get(t.strip(), t.strip()) for t in tail.split(",")} if tail else set()
    return people, things


# Step 1: read the night log
entries = [json.loads(line) for line in open(args.log) if line.strip()]
readings = [e for e in entries if "reading" in e]
span = f"{entries[0]['t'][11:16]} to {entries[-1]['t'][11:16]}" if entries else "no time"

# Step 2: build an on/off timeline for each thing (and the human)
def ts(e):
    return datetime.datetime.fromisoformat(e["t"])


# The camera needs a few seconds to adjust its exposure, so the first frames are often dark.
# Skip the first 15 seconds and use the last reading in that window as the starting state.
WARMUP = 15
if readings:
    t0 = ts(readings[0])
    warm = [e for e in readings if (ts(e) - t0).total_seconds() < WARMUP]
    readings = warm[-1:] + [e for e in readings if (ts(e) - t0).total_seconds() >= WARMUP]


timeline = {}            # name -> list of (time, present)
state = {}
for e in readings:
    people, things = parse(e["reading"])
    now = {**{t: True for t in things}, "human": people > 0}
    for name in set(state) | set(now):
        present = now.get(name, False)
        if state.get(name) != present:
            timeline.setdefault(name, []).append((ts(e), present))
            state[name] = present

# Step 3: drop blips (something that flickers off and back on within --min-gap seconds)
for name, changes in timeline.items():
    kept = []
    for t, present in changes:
        if len(kept) > 1 and (t - kept[-1][0]).total_seconds() < args.min_gap and kept[-2][1] == present:
            kept.pop()   # the last change was a blip: undo it and skip this one
            continue
        kept.append((t, present))
    timeline[name] = kept

# Step 4: turn the cleaned timeline into events
start = ts(readings[0]) if readings else None
changes = sorted((t, name, present) for name, ch in timeline.items() for t, present in ch)
events, cast, current = [], set(), {}
for t, name, present in changes:
    if name != "human" and present:
        cast.add(name)
    if t == start:
        current[name] = present
        continue
    before = {n for n, p in current.items() if p and n not in ("cat", "dog", "human")}
    current[name] = present
    hhmm = t.strftime("%H:%M")
    if name == "human":
        events.append(f"{hhmm} the human {'came to' if present else 'left'} the desk")
    else:
        events.append(f"{hhmm} the {name} {'showed up' if present else 'disappeared'}")
    if before and not any(p for n, p in current.items() if n != "human"):
        events.append(f"{hhmm} everything went dark, nothing could be seen (lights off?)")
if start:
    on_desk = ", ".join(sorted(n for n, p in current.items() if n != "human" and timeline[n][0][0] == start and timeline[n][0][1])) or "nothing visible"
    first_human = timeline.get("human", [(start, False)])[0]
    who = "the human was at the desk" if first_human[0] == start and first_human[1] else "the human was not there"
    events.insert(0, f"{start:%H:%M} the night started. On the desk: {on_desk}. {who}")

print(f"{BOLD}Watched the desk from {span}. {len(readings)} changes, {len(events)} events.{RESET}")
for line in events[-15:]:
    print("  " + line)

# Step 4b: an honest quiet night, no model needed
if not readings:
    print("\nThe log is empty. Nobody said anything last night.")
    raise SystemExit

cast = sorted(cast) + ["camera"]   # the camera saw everything, so it is always in the chat
names = [c.title() for c in cast]
event_text = "\n".join(events[-40:]) if events else "Nothing changed all night."

prompt = f"""The objects on my desk have a group chat. Members: {', '.join(names)}.
Last night, from {span}, a camera watched the desk while the human slept. This is everything that happened:

{event_text}

Write 6 to 8 short, funny chat messages between the members. They gossip about the human and tease each other.
Each message is one short sentence. Mention real times from the list, like "22:05".
Every event they mention must come from the list above. Do not make up events.
If nothing happened, they complain about how boring the night was.

Example of the style (different events):
Cup: he left me at 23:40 and never came back
Phone: at least you didn't get picked up 40 times today"""

# Step 5: ask Qwen for the chat as JSON (try again if it writes fewer than 4 messages)
def ask_qwen():
    r = requests.post("http://localhost:11434/api/generate", json={
        "model": args.model,
        "prompt": prompt,
        "think": False,
        "stream": False,
        "format": {
            "type": "object",
            "properties": {"messages": {"type": "array", "items": {
                "type": "object",
                "properties": {"from": {"type": "string"}, "text": {"type": "string"}},
                "required": ["from", "text"]}}},
            "required": ["messages"],
        },
        "options": {"temperature": 0.7, "num_predict": 500},
    }, timeout=600)
    r.raise_for_status()
    return r.json()["response"]


# Small models like to invent times. Drop any message with a time that is not in the log.
valid_times = {line[:5] for line in events}


def honest(m):
    times = re.findall(r"\b\d{1,2}:\d{2}\b", str(m.get("text", "")))
    return all(t.zfill(5) in valid_times for t in times)


messages, raw, dropped = [], "", 0
for attempt in range(3):
    raw = ask_qwen()
    try:
        got = json.loads(raw)["messages"]
    except (json.JSONDecodeError, KeyError, TypeError):
        got = []
    kept = [m for m in got if honest(m)]
    dropped += len(got) - len(kept)
    if len(kept) > len(messages):
        messages = kept
    if len(messages) >= 4:
        break

# Step 6: show it like a chat
print(f"\n{BOLD}=== Desk Group Chat ({len(names)} members) ==={RESET}\n")
if not messages:
    print(raw)
    raise SystemExit
color_of = {}
with open("morning_chat.txt", "w") as out:
    for m in messages:
        who = str(m.get("from", "?")).title()
        color = color_of.setdefault(who, COLORS[len(color_of) % len(COLORS)])
        print(f"{color}{BOLD}{who}:{RESET} {m.get('text', '')}")
        out.write(f"{who}: {m.get('text', '')}\n")
if dropped:
    print(f"\n({dropped} message(s) dropped because they made up a time that is not in the log)")
print("(saved to morning_chat.txt)")
