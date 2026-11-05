"""Simulated restless_log.jsonl: 5 s looks, YOLO jitter, turns that take a few looks, dropouts."""
import json, random, datetime, sys
random.seed(7)
t = datetime.datetime(2026, 10, 30, 23, 52, 14)
out = open(sys.argv[1], "w")
def w(e): out.write(json.dumps(e) + "\n")
w({"t": t.isoformat(timespec="seconds"), "handoff": "wave"})
t += datetime.timedelta(seconds=120)
end = datetime.datetime(2026, 10, 31, 7, 4, 50)
poses = [[0.18, 0.41, 0.83, 0.79], [0.22, 0.38, 0.88, 0.81], [0.15, 0.44, 0.79, 0.77]]
pose = 0
pending = []          # boxes still to emit for a turn in progress
away_until = None
def j(b, s=0.008): return [round(min(1, max(0, v + random.gauss(0, s))), 3) for v in b]
while t < end:
    h = (t.hour + t.minute / 60 + 24) % 24 if t.hour < 12 else t.hour + t.minute / 60 - 24
    if away_until and t < away_until:
        b = None
    elif pending:
        b = pending.pop(0)
    else:
        away_until = None
        # turn rate: settling in, a restless patch around 2:40-3:20, lighter sleep near morning
        rate = 0.004
        if h < 0.4: rate = 0.02
        elif 2.65 <= h < 3.35: rate = 0.025
        elif h >= 5.8: rate = 0.008
        if 3.75 <= h < 3.76 and not away_until:          # bathroom trip
            away_until = t + datetime.timedelta(minutes=4, seconds=random.randint(0, 40))
            b = None
        elif random.random() < rate:
            new = random.choice([p for i, p in enumerate(poses) if i != pose])
            mid = [round((a + c) / 2, 3) for a, c in zip(poses[pose], new)]
            pose = poses.index(new)
            pending = [j(new)] if random.random() < 0.6 else [j(new), j(new)]
            b = j(mid, 0.02)                                  # caught halfway through the turn
        elif random.random() < 0.015:
            b = None                                          # blanket/dark: YOLO misses me
        else:
            b = j(poses[pose])
    w({"t": t.isoformat(timespec="seconds"), "box": b})
    t += datetime.timedelta(seconds=5 + random.choice([0, 0, 0, 1]))   # NCNN inference adds a second sometimes
