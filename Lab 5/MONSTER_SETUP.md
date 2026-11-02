# Monster Under the Bed: setup and run

## Files (put all of them in `Interactive-Lab-Hub/Lab 5/`)

| File | What it is |
|---|---|
| `monster.py` | The whole system: voice → countdown → night watch → morning verdict → fade |
| `monster_screens.py` | The monster drawings for the PiTFT (`python monster_screens.py` writes previews) |
| `floor_check.py` | Aim the camera and tune the feet detector before the first night |

`monster.py` also uses things already in your repo: `yolo26n_ncnn_model` (Part A), `Lab 3/models/silero_vad.onnx` and `Lab 3/voices/en_US-lessac-medium.onnx`.

Getting the files onto the Pi: commit them to your repo from your laptop and `git pull` on the Pi, or copy them straight over:

```
scp monster.py monster_screens.py floor_check.py pi@gp.local:"~/Interactive-Lab-Hub/Lab\ 5/"
```

## 1. Install the Lab 3 voice/display packages into the Lab 5 venv

```
cd ~/Interactive-Lab-Hub/Lab\ 5
source .venv/bin/activate
pip install faster-whisper sherpa-onnx sounddevice piper-tts Adafruit-Blinka adafruit-circuitpython-rgb-display lgpio pillow
sudo apt install -y libportaudio2      # if sounddevice complains about PortAudio
```

Don't pin numpy: MediaPipe in this venv needs numpy < 2.

Every part is optional. If the mic, speaker, PiTFT or Ollama is missing, `monster.py` prints a warning and keeps going (keyboard instead of voice, printed text instead of speech, `monster_screen.png` instead of the PiTFT, a fixed line instead of Qwen).

## 2. Test without any hardware (2 minutes)

```
python overnight.py --demo --fake-feet --no-ears
```

Type a command and press Enter:
- `s`: going to sleep (10 s countdown in demo mode)
- `f`: put your fake feet on the floor; `f` again lifts them
- `a`: I'm awake (needs feet on the floor)
- `q`: quit

Try one long trip (feet down for 5 s or more), one short shuffle (under 3 s, which shouldn't count), then `a` followed by `f`.

## 3. Set up the hardware

- **Webcam:** under the bed frame, low, aimed at the floor where your feet land when you get up.
- **Light:** a dim red LED strip or night light under the bed, facing the floor. Without it, the camera reports "too dark to see" all night.
- **PiTFT:** where you can see it from bed or when you get up. At night it is drawn dark.
- **USB mic and speaker** from Lab 3, close enough to hear "I'm going to sleep".
- Tell your roommates. The camera only sees the floor, and one photo is saved per trip in `snaps/`. Delete them after the demo.

## 4. Tune the detector (through VNC)

```
python floor_check.py
```

Step on and off the floor. "change" should jump above 0.04 with feet and sit near 0 without. Turn the lights off and check that "bright" stays above 15. If your floor is only the bottom part of the picture, narrow the region, e.g. `--roi 0,0.4,1,1`. Press `s` to save a screenshot for the writeup.

## 5. Full demo with voice

```
python overnight.py --demo --window
```

Say "I'm going to sleep", get in bed, get up twice (stand there for 5+ seconds each time), then stand up and say "I'm awake".

## 6. A real night

```
tmux new -s night
cd ~/Interactive-Lab-Hub/Lab\ 5 && source .venv/bin/activate
python overnight.py --wake 7:30          # add your --roi / --change-area from step 4
```

Detach with Ctrl-b then d. In the morning: stand up and say "I'm awake". If you forget, feet on the floor for 2 minutes after 7:30 counts as morning. The program keeps running for the next night; `q` + Enter quits.

## What it writes

- `night_log.jsonl`: every change of reading (`feet` / `no feet` / `can't see`), each trip, the morning verdict. Same format as `overnight.py`, so `python morning.py --log night_log.jsonl` also works on it.
- `nights.jsonl`: one summary line per night. The monster mentions last night's count at bedtime.
- `morning_report.txt`: this morning's verdict.
- `snaps/trip-*.jpg`: one photo per trip, for checking false alarms (turn off with `--no-snaps`).
- `monster_screen.png`: whatever the screen is showing right now.

## Settings worth knowing

| Flag | Default | Meaning |
|---|---|---|
| `--countdown` | 60 | seconds to get into bed |
| `--interval` | 5 | seconds between looks at the floor |
| `--min-trip` | 15 | feet must be down this long to count as a trip |
| `--end-gap` | 20 | no feet for this long ends a trip |
| `--wake` | off | HH:MM after which 2 min of feet = morning |
| `--roi` | 0,0.2,1,1 | floor region of the picture (x0,y0,x1,y1) |
| `--change-area` | 0.04 | share of the floor that must change to count as feet |
| `--dark` | 15 | below this brightness the camera "can't see" |
| `--no-yolo` | | use floor change only |
| `--demo` | | 10 s countdown, look every 1 s, 3 s trips |
