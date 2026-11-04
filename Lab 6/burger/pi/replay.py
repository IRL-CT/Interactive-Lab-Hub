"""Replay a recording through pan.py's MotionDetector (runs on the laptop, no hardware).
    python replay.py recordings/motion_20261103_193039.csv [--debug]"""
import csv, sys
from collections import Counter, OrderedDict
from pan import MotionDetector

det = MotionDetector(debug='--debug' in sys.argv)
found = OrderedDict()
for r in csv.DictReader(open(sys.argv[1])):
    out = det.update(*(float(r[k]) for k in ('t', 'ax', 'ay', 'az', 'gx', 'gy', 'gz')))
    found.setdefault(r['step'], [])
    for kind, value in out:
        found[r['step']].append(f'{kind}:{value}' if kind == 'mode' else value)
for step, events in found.items():
    print(f'{step:13s} {" ".join(events) or "-"}')
