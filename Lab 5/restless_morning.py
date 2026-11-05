"""
Part I, my version of morning.py: turn restless_log.jsonl into a restlessness report.

    python restless_morning.py                     # numbers, an hour-by-hour timeline, then Qwen's greeting
    python restless_morning.py --no-llm            # numbers and timeline only
    python restless_morning.py --threshold 0.08    # a box has to move more to count as a move
    python restless_morning.py --log some_other.jsonl

Part E showed that Qwen can't count from a log, so all the counting happens here.
On the Pi it also got the finished facts wrong when asked to summarize them (it called
my stillest stretch restless), so it no longer sees them. It only writes a greeting from
the overall tone, and a greeting with a number in it is thrown away.

Tune --threshold on a fake night: lie still for two minutes, then turn over a few times.
Lying still should give 0 moves, and each turn should give roughly one.
"""
import argparse
import collections
import datetime
import json

import requests

parser = argparse.ArgumentParser()
parser.add_argument("--log", default="restless_log.jsonl")
parser.add_argument("--threshold", type=float, default=0.05,
                    help="how far a box edge has to move, as a fraction of the frame, to count as a move")
parser.add_argument("--away", type=float, default=60, help="seconds with nobody in view before I count as out of bed")
parser.add_argument("--window", type=float, default=600, help="seconds; this many moves within it make a restless stretch")
parser.add_argument("--min-moves", type=int, default=3, help="moves within --window that make it a restless stretch")
parser.add_argument("--model", default="qwen3:0.6b")
parser.add_argument("--no-llm", action="store_true")
args = parser.parse_args()

looks = [json.loads(line) for line in open(args.log) if line.strip()]
looks = [e for e in looks if "box" in e]         # drop the hand-off line
for e in looks:
    e["t"] = datetime.datetime.fromisoformat(e["t"])
if not looks:
    raise SystemExit(f"{args.log} is empty: did the night shift run?")


def hm(t):
    return f"{t:%H:%M}"


# Moves: compare each box with the last box I was seen in. A short gap with nobody
# is YOLO dropping me for a look or two, not me leaving, so it doesn't reset anything.
moves, away, last_box, gap_start = [], [], None, None
for e in looks:
    if e["box"] is None:
        gap_start = gap_start or e["t"]
        continue
    if gap_start and (e["t"] - gap_start).total_seconds() >= args.away:
        away.append((gap_start, e["t"]))         # really out of bed; coming back is not a move
    elif last_box and max(abs(a - b) for a, b in zip(e["box"], last_box)) > args.threshold:
        moves.append(e["t"])
    last_box, gap_start = e["box"], None
if gap_start and (looks[-1]["t"] - gap_start).total_seconds() >= args.away:
    away.append((gap_start, looks[-1]["t"]))     # still gone when the log stopped

# Restless stretches: runs of moves where each one is within --window of the one before,
# kept only if there are at least --min-moves of them.
stretches, run = [], moves[:1]
for t in moves[1:]:
    if (t - run[-1]).total_seconds() <= args.window:
        run.append(t)
    else:
        stretches.append(run)
        run = [t]
if run:
    stretches.append(run)
stretches = [s for s in stretches if len(s) >= args.min_moves]

start, end = looks[0]["t"], looks[-1]["t"]
seen = sum(1 for e in looks if e["box"] is not None)
facts = [f"Watched from {hm(start)} to {hm(end)} ({(end - start).total_seconds() / 3600:.1f} hours, {len(looks)} looks)."]
if not seen:
    facts.append("Nobody was in view the whole time.")
else:
    facts.append(f"Moved {len(moves)} times.")
    facts += [f"Restless from {hm(s[0])} to {hm(s[-1])} ({len(s)} moves)." for s in stretches] or ["No restless stretches."]
    facts += [f"Out of bed from {hm(a)} to {hm(b)} ({(b - a).total_seconds() / 60:.0f} min)." for a, b in away]
    if moves:
        quiet = max(zip([start] + moves, moves + [end]), key=lambda p: p[1] - p[0])
        facts.append(f"Longest still stretch: {hm(quiet[0])} to {hm(quiet[1])}.")

print("\n".join(facts))
per_hour = collections.Counter(t.hour for t in moves)
print("\nmoves per hour:")
hour = start.replace(minute=0, second=0)
while hour <= end:
    print(f"  {hour:%H}:00 {'#' * per_hour[hour.hour]}")
    hour += datetime.timedelta(hours=1)

# A quiet night is reported as quiet, without asking the model to make something of it.
if args.no_llm or not seen or (not moves and not away):
    raise SystemExit

tone = "somewhat restless" if stretches else "mostly calm"
got_up = f" and got up {'once' if len(away) == 1 else 'more than once'}" if away else ""
prompt = (f"Write one warm good-morning sentence to someone who had a {tone} night{got_up}. "
          "Do not use any numbers or times. Do not give advice. Do not claim anything else about their night.")

r = requests.post("http://localhost:11434/api/generate", json={
    "model": args.model,
    "prompt": prompt,
    "think": False,
    "stream": False,
    "options": {"num_ctx": 2048, "temperature": 0.3},
}, timeout=600)
r.raise_for_status()
greeting = r.json()["response"].encode("ascii", "ignore").decode().strip()      # it sometimes adds emoji
print("\n" + ("Good morning." if any(c.isdigit() for c in greeting) else greeting))
