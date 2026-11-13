"""
tram_notify.py: push a phone notification for every tram, via ntfy (free, no account).

    python tram_notify.py              # run next to tram_watch.py (another tmux window)
    python tram_notify.py --test       # send one test notification and exit

Setup on each phone: install "ntfy" (App Store / Play Store), tap +, and subscribe to the topic
this script prints the first time it runs (a random name, saved in tram_config.json as
"ntfy_topic", so only people you give it to get the alerts). Share the topic to share the alerts.

What it sends, once per tram:
  heading to the island:  "Tram to Roosevelt Island: est. arrival ~13:42:10"
                          "80% likely 13:42:01-13:42:19, 93% chance within 30 s."
  leaving the island:     "Tram just left Roosevelt Island"
                          "Next tram ~13:52 (estimated; 80% likely 13:49-13:55)."
Quiet hours: nothing outside "notify_hours" in tram_config.json (default 6 to 24).
It only reads tram_state.json and tram_events.jsonl, so it can be started and stopped any time.
These are unofficial estimates from a window camera, and the message says so.
"""
import argparse
import datetime
import json
import secrets
import time

import requests

from tram_common import EVENTS, STATE, load_config, save_config

SERVER = "https://ntfy.sh"


def topic(cfg):
    if not cfg.get("ntfy_topic"):
        cfg["ntfy_topic"] = "ri-tram-" + secrets.token_hex(5)     # hard to guess = private
        save_config(cfg)
    return cfg["ntfy_topic"]


def send(cfg, title, body, tags="aerial_tramway"):
    headers = {"Title": title.encode("utf-8"), "Tags": tags}
    if cfg.get("public_url"):
        headers["Click"] = cfg["public_url"]          # tapping opens the live page
    try:
        r = requests.post(f"{cfg.get('ntfy_server', SERVER)}/{topic(cfg)}",
                          data=body.encode("utf-8"), headers=headers, timeout=10)
        ok = r.ok
    except requests.RequestException as e:
        print("could not send:", e, flush=True)
        ok = False
    print(f"{datetime.datetime.now():%H:%M:%S} {'sent' if ok else 'FAILED'}: {title} | {body}",
          flush=True)
    return ok


def hm(iso):
    return iso[11:16] if iso else "?"


def hms(iso):
    return iso[11:19] if iso else "?"


def next_text(state, direction=None):
    """'Next departure from the island ~13:52 (estimated; 80% likely 13:49-13:55).'
    With two cabins each direction has its own timetable, so ask for one if we can."""
    by = (state or {}).get("next_by_direction") or {}
    nxt = by.get(direction) if direction in by else (state or {}).get("next") or {}
    if nxt.get("status") == "ok" and nxt.get("eta"):
        what = ("arrival at the island" if direction and "island" in direction.lower() else
                "departure from the island" if direction and "manhattan" in direction.lower() else "tram")
        txt = f"Next {what} ~{hm(nxt['eta'])} (estimated"
        if nxt.get("low") and nxt.get("high"):
            txt += f"; 80% likely {hm(nxt['low'])}-{hm(nxt['high'])}"
        return txt + ")."
    return ""


def arrival_text(d, prefix="est_station_arrival"):
    """'80% likely 13:42:01-13:42:19, 93% chance within 30 s' from a live dict or a pass entry."""
    low, high, p30 = d.get(prefix + "_low"), d.get(prefix + "_high"), d.get(prefix + "_p30")
    parts = []
    if low and high:
        parts.append(f"80% likely {hms(low)}-{hms(high)}")
    if p30 is not None:
        parts.append(f"{round(p30 * 100)}% chance within 30 s")
    return ", ".join(parts)


def read_json(path):
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def new_events(path, seen):
    """Pass events added since we last looked (by start time)."""
    out = []
    try:
        with open(path) as f:
            for line in f:
                try:
                    e = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if e.get("event") == "pass" and e["start"] not in seen:
                    out.append(e)
    except OSError:
        pass
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true", help="send one test notification")
    args = parser.parse_args()
    cfg = load_config()
    t = topic(cfg)
    print(f"ntfy topic: {t}\nOn your phone: ntfy app -> + -> subscribe to '{t}'", flush=True)
    if args.test:
        send(cfg, "Tram watcher test", "If you see this, notifications work.")
        return

    island = cfg.get("island_name", "Roosevelt Island")
    lo, hi = cfg.get("notify_hours", [6, 24])
    notified = set()                                 # pass start times already announced
    notified.update(e["start"] for e in new_events(EVENTS, set()))   # don't replay old passes
    print("watching for trams (Ctrl-C to stop)", flush=True)
    while True:
        try:
            now = datetime.datetime.now()
            quiet = not (lo <= now.hour < hi)
            state = read_json(STATE)

            # 1. live: every cabin being tracked (both, when they pass each other)
            to_island = cfg.get("directions", {}).get("toward_station", "to Island")
            to_manhattan = cfg.get("directions", {}).get("toward_tower", "to Manhattan")
            cabins = (state or {}).get("cabins") or ([state["live"]] if state and state.get("live") else [])
            for live in cabins:
                if not (state.get("tram_in_view") and live.get("started")):
                    continue
                key = f"{live['started']}#{live.get('id', '')}"
                if key in notified or live["heading"] not in ("station", "tower"):
                    continue
                notified.update({key, live["started"]})      # also blocks the logged-pass fallback
                if quiet:
                    continue
                if live["heading"] == "station" and live.get("eta_station"):
                    body = arrival_text(live, "eta_station")
                    send(cfg, f"Tram to {island}: est. arrival ~{hms(live['eta_station'])}",
                         (body + ". " if body else "") + "Estimate from a window camera (unofficial).")
                elif live["heading"] == "tower":
                    body = "Heading to Manhattan. " + next_text(state, to_manhattan)
                    send(cfg, f"Tram just left {island}", body.strip() + " (unofficial estimate)")

            # 2. fallback: a finished pass that wasn't announced live (presence-only mode)
            for e in new_events(EVENTS, notified):
                notified.add(e["start"])
                if quiet:
                    continue
                if e.get("est_station_arrival"):
                    body = arrival_text(e, "est_station_arrival")
                    send(cfg, f"Tram reached {island} ~{hms(e['est_station_arrival'])} (est.)",
                         " ".join(x for x in ((body + ".") if body else "", next_text(state, e.get("direction"))) if x)
                         or "Unofficial estimate.")
                elif e.get("est_station_departure"):
                    body = arrival_text(e, "est_station_departure")
                    send(cfg, f"Tram left {island} ~{hms(e['est_station_departure'])} (est.)",
                         " ".join(x for x in ((body + ".") if body else "", next_text(state, e.get("direction"))) if x)
                         or "Unofficial estimate.")
                else:
                    send(cfg, "Tram went by", (f"{e.get('direction') or ''}. " +
                                               next_text(state)).strip(" ."))
            time.sleep(1)
        except KeyboardInterrupt:
            break


if __name__ == "__main__":
    main()
