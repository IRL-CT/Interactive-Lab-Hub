# Distributed UNO

A round of UNO across 3 or 4 Pis. Each Pi is one player's hand: your cards are on your screen, and you play with your hand over the sensor. One Pi also runs the referee.

## Setup

On every Pi:

```bash
cd "Lab 6"
source .venv/bin/activate   # first time: python -m venv .venv && pip install -r requirements-pi.txt
sudo systemctl stop piscreen.service
cd uno
```

Check the sensor first (swipe in each direction, cover it, hold up colors):

```bash
python player.py --sensor-test
```

Teach each Pi the objects you'll use to pick wild colors. Readings change with the room's light, so do this where you'll play, and again if you move:

```bash
python player.py --calibrate
```

This saves `colors.json`, which belongs to that Pi and isn't committed. Without it, the Pi falls back to fixed thresholds, which can mistake blue for green.

Then, on each Pi, with the same `--team` and a different `--name`:

```bash
python player.py --team myteam --name abiola
```

And on any one Pi, in a second terminal:

```bash
python referee.py --team myteam --players 3
```

The cards are dealt as soon as enough players have joined. It doesn't matter who starts first. To play again, run the referee again.

Short a Pi? Fill the seat with `python player.py --team myteam --name bot --bot`. No hardware? Use `--keyboard`.

## Controls

| Screen | Sensor | Button A (top) | Button B (bottom) |
|---|---|---|---|
| Your hand | Swipe left/right: browse. Up: play. Down: draw | Next card | Press: play. Hold: draw |
| Pick a wild color | Hold a colored thing near it for about a second | Change color | Press: choose. Hold: cancel |
| UNO! | Cover it | Any button calls | Any button calls |

**The UNO race:** when someone gets down to one card, the game pauses for 4 seconds and every screen turns yellow. If they cover their sensor first, they're safe. If someone else does, they draw 2. If nobody does, they get away with it.

## Rules we changed

- Drawing ends your turn, even if you could play the card you drew.
- Wild Draw 4 only works if you have nothing in the active color, so there is no bluffing or challenging.
- The first card on the pile is always a number.
- If a player does nothing for 60 seconds (`--turn-timeout`), they draw and the game moves on.

## MQTT topics

Everything is under `IDD/<team>/uno/`, as JSON at QoS 1. Nothing is retained.

| Topic | From | Contents |
|---|---|---|
| `join` | player | `{"name": "abiola"}`, repeated until the referee lists them |
| `state` | referee | Whose turn, top card, color, card counts, UNO window, winner |
| `hand/<name>` | referee | That player's cards |
| `action/<name>` | player | `{"type": "play", "card": "R5", "turn": 12}`, `draw` or `call` |
| `notice/<name>` | referee | Why a move was refused |

The class broker has one shared login, so anyone can read `hand/<name>`. Don't subscribe to `IDD/#` during a game if you want to play fair.

## Files

- `game.py`: the rules, with no MQTT or hardware
- `referee.py`: runs the game and has the final say on every move
- `player.py`: one seat at the table, including `--bot` and `--keyboard`
- `screen.py`: draws the 240x135 screen
- `hardware.py`: the screen, buttons and APDS-9960
- `test_game.py`, `test_player.py`: `python -m unittest test_game test_player`
