# Bathroom Lights Tracker: How to Use

Two scripts for our Lab 5 night-time system. It watches the hallway after 9 pm, notices when
someone comes out of a bathroom, guesses who it was from their height, and checks whether
they left the light on. In the morning it tallies who left the lights on the most.

Run everything from the Lab 5 folder with the venv active:

```bash
cd ~/Documents/GitHub/Interactive-Lab-Hub/"Lab 5" && source .venv/bin/activate
```

Commands with `--show` or that draw boxes need the Pi desktop (Raspberry Pi Connect
Screen sharing), or `export DISPLAY=:0` first when using SSH.

---

## The files

| File | What it does |
|---|---|
| `calibrate.py` | One-time setup. You draw boxes on the camera view to mark the gap under each bathroom door, then measure how bright those gaps get with the lights on vs off. Saves `zones.json`. |
| `bathroom_night.py` | Everything else: learns each roommate's height (`--learn`), runs the night shift, and makes the morning report (`--morning`). |
| `zones.json` | Created by the scripts. Holds the light-strip boxes, light thresholds and each person's learned height. Do not move the camera after making it. |
| `bathroom_log.jsonl` | Created each night. One line per event (light on/off, came out, left light on, turned it off). |
| `calib_preview.jpg` | A picture of the camera view with your boxes drawn on it, to check them. |

---

## 1. Calibrate the camera (once)

Tape the webcam down at floor level, aimed down the hallway so both bathroom doors and the
gaps under them are visible.

If the camera sits on its side, rotate the view first (our camera needs `ccw`). This is saved
in `zones.json` and both scripts use it. If you change it later, redo steps 1 to 3.

```bash
python calibrate.py --rotate ccw
```

Otherwise just:

```bash
python calibrate.py
```

It asks for four boxes. For each one, **click one corner, then the opposite corner**, then press
**Enter** (`r` redoes the box, `q` quits). Clicks are used instead of dragging because drags
don't come through Raspberry Pi Connect screen sharing:

1. **near_door**: the whole near bathroom door (reference only)
2. **far_door**: the whole far bathroom door (reference only)
3. **near_strip**: a *thin* box along the gap under the near door
4. **far_strip**: a *thin* box along the gap under the far door

Check `calib_preview.jpg` to make sure the strips sit right on the gaps.

## 2. Measure the lights (once)

```bash
python calibrate.py --test
```

It prints each strip's brightness every second (0 = black, 255 = white). With the doors closed,
turn each bathroom light on for ~10 s, then off. The `p90` number should jump clearly when the
light is on. Ctrl-C to stop.

To set the thresholds yourself, add this to `zones.json` with values roughly halfway between
the off and on `p90` readings:

```json
"light_on": {"near": 120, "far": 100}
```

Without it, the night script assumes both lights are **off when it starts** and counts a
brightness jump of 40 as "on".

## 3. Learn each roommate's height (once per person)

Each person stands alone in front of each door for 10 seconds, facing the camera:

```bash
python bathroom_night.py --learn Viktor --door near --show
python bathroom_night.py --learn Viktor --door far --show
```

Repeat for every roommate. After each run it prints that person's height in pixels and
everyone else's at the same door, so you can see whether people are far enough apart.
No photos are saved, only box sizes.

## 4. Test it

```bash
python bathroom_night.py --now --show
```

Go into a bathroom, turn the light on, come out and leave it on. Within ~8 seconds you should
see:

```
21:42:10 Viktor came out of the near bathroom
21:42:18 Viktor left the near bathroom light ON
```

Press **q** (or Ctrl-C) to stop.

## 5. Run a real night

```bash
tmux new -s night
python bathroom_night.py
```

It waits until 9 pm, then checks once per second until you press Ctrl-C in the morning.
Detach from tmux with **Ctrl-B then D**; reattach with `tmux attach -t night`.

## 6. Morning report

```bash
python bathroom_night.py --morning
```

Prints the tally for the most recent night and asks Qwen for a short, light-hearted summary.
If nothing happened, it says so.

---

## Useful options

| Option | Meaning |
|---|---|
| `--now` | Start watching immediately instead of at 9 pm |
| `--start 22` | Start at a different hour |
| `--show` | Open a window with boxes and light states (good for the demo video) |
| `--snaps` | Save a photo of each exit to `bathroom_snaps/` to check the guesses. **Delete after the demo.** |
| `--interval 2` | Look every 2 s instead of every 1 s |
| `--model qwen3:0.6b` | Faster, smaller model for the morning report |

## Known limits

- **Who it was** comes from height in the frame. 6'2" vs 5'5" separates well; 5'10" is close to
  both, so the log may say "A or B" when unsure.
- **Darkness:** if the hallway is very dark, YOLO may miss people. Test a fake night first.
- **Camera moved?** Redo steps 1 to 3.

## Privacy

Roommates agreed before the first run. The camera points at the hallway, never into a
bathroom. Only event lines and box sizes are stored; photos only with `--snaps`, deleted after
the demo.
