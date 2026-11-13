"""
tram_accuracy.py: compare ESTIMATED timings with TRUE timings, and learn from the difference.

Two kinds of truth:
  1. Next-tram predictions are checked automatically: when a tram really shows up, its start
     time is compared with what was predicted at the end of the previous pass.
  2. Island arrival / departure can't be seen by the camera (the cabin is behind the trees), so
     the truth comes from a person: the "I saw it arrive / leave" buttons in tram_web.py
     (or `python tram_accuracy.py arrival` / `departure` on the Pi) log the true time.

Each hand-timed event is matched to the nearest estimate. From those errors we get:
  - bias: the typical error (e.g. "estimates are 6 s early" because the real cabin slows down
    before the station); live estimates are shifted by it,
  - spread: how much the error varies; it widens the live "80% likely" range so the stated
    confidence matches reality.

    python tram_accuracy.py             # print the accuracy report
    python tram_accuracy.py arrival     # log "it arrived at the island just now"
    python tram_accuracy.py departure   # log "it left the island just now"
"""
import datetime
import json
import math
import sys
from pathlib import Path

import numpy as np

from tram_common import EVENTS

TRUTH = Path("tram_truth.jsonl")
MATCH_S = 180            # a hand-timed event matches an estimate within 3 minutes
PRIOR_SD = 10.0          # extra seconds of doubt about station times until 5+ are hand-timed
Z80 = 1.2816             # an 80% range is the estimate +/- 1.28 standard deviations


def _read(path):
    out = []
    try:
        with open(path) as f:
            for line in f:
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    except OSError:
        pass
    return out


def passes():
    return [e for e in _read(EVENTS) if e.get("event") == "pass"]


def truths():
    return [e for e in _read(TRUTH) if e.get("kind") in ("arrival", "departure")]


def log_truth(kind, when=None):
    when = when or datetime.datetime.now()
    entry = {"kind": kind, "t": when.isoformat(timespec="seconds")}
    with open(TRUTH, "a") as f:
        f.write(json.dumps(entry) + "\n")
    return entry


def ts(iso):
    return datetime.datetime.fromisoformat(iso)


def station_matches(kind, ps=None, tr=None):
    """[(pass, true time, raw error s)] for hand-timed arrivals or departures.
    error = estimate - truth, so negative means the estimate was early."""
    key = "raw_est_station_arrival" if kind == "arrival" else "raw_est_station_departure"
    fallback = "est_station_arrival" if kind == "arrival" else "est_station_departure"
    ps = passes() if ps is None else ps
    out = []
    for t in (truths() if tr is None else tr):
        if t["kind"] != kind:
            continue
        true = ts(t["t"])
        cands = [(p, ts(p.get(key) or p[fallback])) for p in ps if p.get(key) or p.get(fallback)]
        if not cands:
            continue
        p, est = min(cands, key=lambda c: abs((c[1] - true).total_seconds()))
        err = (est - true).total_seconds()
        if abs(err) <= MATCH_S:
            out.append((p, true, err))
    return out


def calibration(kind):
    """(bias s, extra spread s, n) learned from hand-timed events. Until 5 exist: no bias, PRIOR_SD."""
    errs = [e for _, _, e in station_matches(kind)]
    if len(errs) < 5:
        return 0.0, PRIOR_SD, len(errs)
    errs = np.array(errs)
    bias = float(np.median(errs))
    spread = float(1.4826 * np.median(np.abs(errs - bias)))      # robust standard deviation
    return bias, max(spread, 2.0), len(errs)


def with_confidence(seconds, model_sd, kind):
    """Apply the learned bias and spread to a raw 'seconds from now' estimate.
    Returns (corrected seconds, total sd, P(within +/-30 s of the estimate))."""
    bias, extra, _ = calibration(kind)
    sd = math.sqrt((model_sd or 0) ** 2 + extra ** 2)
    corrected = seconds - bias
    p30 = math.erf(30 / (sd * math.sqrt(2))) if sd > 0 else 1.0
    return corrected, sd, p30


def next_tram_checks(ps=None):
    """[(pass, predicted eta, error s, inside predicted range?)] for every pass that had a prediction."""
    out = []
    for p in (passes() if ps is None else ps):
        pred = p.get("predicted") or {}
        if not pred.get("eta"):
            continue
        err = (ts(pred["eta"]) - ts(p["start"])).total_seconds()
        inside = None
        if pred.get("low") and pred.get("high"):
            inside = ts(pred["low"]) - datetime.timedelta(seconds=30) <= ts(p["start"]) <= \
                ts(pred["high"]) + datetime.timedelta(seconds=30)
        out.append((p, pred["eta"], err, inside))
    return out


def summary():
    """Everything the web page shows about accuracy."""
    out = {}
    nt = next_tram_checks()
    if nt:
        errs = np.abs([e for _, _, e, _ in nt])
        ranged = [i for _, _, _, i in nt if i is not None]
        out["next_tram"] = {"n": len(nt), "median_abs_error_s": round(float(np.median(errs))),
                            "within_2_min": round(float(np.mean(errs <= 120)), 2),
                            "inside_range": round(float(np.mean(ranged)), 2) if ranged else None}
    for kind in ("arrival", "departure"):
        m = station_matches(kind)
        if m:
            bias, spread, n = calibration(kind)
            out[kind] = {"n": len(m), "median_abs_error_s": round(float(np.median(np.abs([e for _, _, e in m])))),
                         "bias_s": round(bias, 1) if n >= 5 else None,
                         "spread_s": round(spread, 1) if n >= 5 else None}
    return out


def recent(limit=10):
    """Recent passes with estimated vs true times, newest first, for the web page."""
    ps = passes()
    arr = {p["start"]: (true, err) for p, true, err in station_matches("arrival", ps)}
    dep = {p["start"]: (true, err) for p, true, err in station_matches("departure", ps)}
    nxt = {p["start"]: (eta, err, inside) for p, eta, err, inside in next_tram_checks(ps)}
    rows = []
    for p in reversed(ps[-limit:]):
        row = {"start": p["start"], "direction": p.get("direction"),
               "est_arrival": p.get("est_station_arrival"), "est_departure": p.get("est_station_departure")}
        if p["start"] in arr:
            row["true_arrival"], row["arrival_error_s"] = arr[p["start"]][0].isoformat(timespec="seconds"), \
                round(arr[p["start"]][1])
        if p["start"] in dep:
            row["true_departure"], row["departure_error_s"] = dep[p["start"]][0].isoformat(timespec="seconds"), \
                round(dep[p["start"]][1])
        if p["start"] in nxt:
            row["predicted_start"], row["prediction_error_s"] = nxt[p["start"]][0], round(nxt[p["start"]][1])
        rows.append(row)
    return rows


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ("arrival", "departure"):
        e = log_truth(sys.argv[1])
        print(f"logged: true {e['kind']} at {e['t'][11:]}")
    else:
        print(json.dumps(summary(), indent=2))
        for r in recent():
            print(r)
