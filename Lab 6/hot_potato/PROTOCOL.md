# Hot Potato: message protocol

This is the contract between the **laptop server** (`server.py`) and the **4 Pis**.
Every Pi does the same four things, whatever input it uses:

1. **Join** with its player name once at startup.
2. **Throw** (`left` / `forward` / `right`) when it holds the potato.
3. **Catch** when the potato is flying at it.
4. **Subscribe to its own state** and draw what the server says.

The server does all the rules and timers. A Pi never decides who has the potato. It only sends what its input did and draws what it's told.

```
          Pi "viktor"                          MQTT broker                       Laptop: server.py
  ┌───────────────────────┐            farlab.infosci.cornell.edu         ┌──────────────────────────┐
  │ input → throw / catch │ ──publish──▶ IDD/hotpotato/player/viktor/action ─▶│ rules, timers, holder    │
  │ PiTFT ← draw state    │ ◀─subscribe─ IDD/hotpotato/player/viktor/state ◀──│ publishes each player    │
  └───────────────────────┘                                               │ browser: /viktor view    │
                                                                          └──────────────────────────┘
```

Broker settings (same as the rest of Lab 6): host `farlab.infosci.cornell.edu`, port `1883`, user `idd`, password `device@theFarm`.

**Player names** go in the topic, so keep them simple: lowercase, no spaces, no `/` `+` `#`, at most 20 characters (`viktor`, `ana`, `ben`, `cy`).

---

## 1. Seats and directions

The game still needs to know where everyone sits, so "left" means the person really on your left. Seats are numbered **clockwise, seen from above**:

```
              seat 3
                ▲
     seat 2  ◀  ●  ▶  seat 4
                ▼
              seat 1
```

| Player name | Input | Seat |
|---|---|---|
| `viktor` | capacitive touch + button | **1** |
| ? | joystick | **2** |
| ? | rotary encoder | **3** |
| ? | IMU + button | **4** |

Put `"seat"` in your join message to sit in a specific seat. Leave it out and you get the next free seat. Either way, your state messages tell you your `seat`. Make sure the real table matches the laptop diamond.

Directions are **relative to the thrower**:

| I throw… | lands on |
|---|---|
| `left` | my seat + 1 (wraps 4 → 1) |
| `forward` | the person across (seat + 2) |
| `right` | my seat − 1 |

---

## 2. Pi → server: `IDD/hotpotato/player/<name>/action`

Publish **JSON** (recommended) or plain text. QoS 0, not retained.

| What | JSON payload | Plain-text shortcut |
|---|---|---|
| Join (send once on startup) | `{"action": "join", "seat": 1, "input": "touch"}` (`seat` optional) | `join` |
| Throw | `{"action": "throw", "dir": "left"}` (`left` / `forward` / `right`) | `left`, `forward`, `right` |
| **Catch** | `{"action": "catch"}` | `catch` |
| Start the game | `{"action": "start"}` | `start` |
| Restart a running game | `{"action": "reset"}` | `reset` |
| Leave | `{"action": "leave"}` | `leave` |

Notes
- A throw or catch from a name that never joined also joins it (next free seat).
- `dir` also accepts `l`, `f`, `r`, `up`, `across`.
- Rejected requests explain why on `IDD/hotpotato/player/<name>/error`:
  ```json
  {"request": {"action": "throw", "dir": "left"}, "reason": "you don't have the potato"}
  ```

---

## 3. Server → Pi: `IDD/hotpotato/player/<name>/state`

**Retained** JSON, so a Pi that (re)connects immediately gets its current state. It's sent whenever your situation changes, and every 0.5 s during a round (fresh timers).

```json
{
  "name": "viktor",
  "seat": 1,
  "mode": "incoming",
  "heat": 0.0,
  "time_left": null,
  "hold_limit": 9.5,
  "round_left": 21.4,
  "round_time": 30,
  "incoming_from": "ana",
  "incoming_dir": "forward",
  "caught": false,
  "flight_left": 1.1,
  "flight_time": 1.5,
  "butterfingers": false,
  "booms": 1,
  "max_booms": 3,
  "boom_reason": null,
  "loser": null,
  "phase": "playing"
}
```

### What to draw for each `mode`

| `mode` | Meaning | Suggested PiTFT drawing | Input does |
|---|---|---|---|
| `incoming` | The potato is flying at you. You have `flight_time` (1.5 s) to catch it. | **Light up / flash**, 🙌 open hands, an arrow toward `incoming_dir`. Once `caught` is `true`, show "got it!" | **catch** |
| `holding` | You have the potato. | Potato goes from yellow to red as `heat` goes 0 → 1. Show `time_left`. | **throw** |
| `waiting` | Someone else has it. | Relaxed hands ready to catch | nothing (pressing catch now = butterfingers) |
| `boom` | You exploded. `boom_reason` = `held it too long`, `dropped it` or `time's up`. | Red screen / explosion for 3 s | — |
| `safe` | Someone else just exploded. | Phew face | — |
| `lobby` | Joined, game not started. | "Ready", your seat | start |
| `gameover` | Game finished. `loser` = name of the player who hit `max_booms`. | Loser vs winner | start |
| `left` | You left the game (or the server dropped you). | "Disconnected" | join |

Always available: `round_left` (seconds left in the 30 s round) to show as a small countdown, and `booms` / `max_booms` for lives.

**Smooth timers tip:** when a message arrives, remember the local time. Each frame, subtract the seconds since then from `time_left`, `round_left` and `flight_left`, so the red fade and countdowns move smoothly between updates.

### Other topics (optional)

| Topic | Retained | Contents |
|---|---|---|
| `IDD/hotpotato/game` | yes | Whole game state (all players, holder, phase, message). Handy for debugging. |
| `IDD/hotpotato/events` | no | One message per event: `join`, `leave`, `round`, `throw`, `catch_press`, `catch`, `boom`, `gameover`, `reset`. Good for sounds (whoosh on `throw`, boom on `boom`). |
| `IDD/hotpotato/player/<name>/error` | no | Why a request was rejected. |

---

## 4. Game rules (defaults, all at the top of `server.py`)

| Setting | Default | |
|---|---|---|
| `ROUND_TIME` | 30 s | each round lasts 30 s. **Whoever has the potato at 0 explodes** (or whoever it's flying toward). |
| `START_HOLD_LIMIT` | 10 s | max time you may hold the potato at the start of a round |
| `SHRINK_PER_CATCH` | 0.5 s | every catch makes the hold limit shorter… |
| `MIN_HOLD_LIMIT` | 3 s | …down to this |
| `FLIGHT_TIME` | 1.5 s | time in the air = your window to press **catch** |
| `CATCH_LOCKOUT` | 1 s | pressing catch when nothing is coming = butterfingers, catch is locked for 1 s |
| `BOOM_PAUSE` | 3 s | explosion pause before the next round |
| `MAX_BOOMS` | 3 | explode this many times and you lose |

Three ways to explode: **held it too long** (hold limit), **dropped it** (didn't press catch in time), **time's up** (round hit 0).

The hold timer resets on every catch. A new round starts with a random player holding, and the hold limit goes back to 10 s. **Start** only works from the lobby or after game over. If a player leaves while holding the potato, it passes to someone else instead of ending the game.

---

## 5. Minimal Pi template

Fill in `read_input()` with your sensor. Everything else is the same on all 4 Pis.

```python
import json, time, uuid
import paho.mqtt.client as mqtt

NAME = "viktor"                # <- your player name (goes in the topic)
SEAT = 1                       # <- where you sit (clockwise from the laptop's bottom)
INPUT = "touch"
BASE = "IDD/hotpotato"
ACTION = f"{BASE}/player/{NAME}/action"

state = {"mode": "lobby"}      # latest state from the server
got_at = time.time()

def on_connect(client, userdata, flags, rc):
    client.subscribe(f"{BASE}/player/{NAME}/state")
    client.publish(ACTION, json.dumps({"action": "join", "seat": SEAT, "input": INPUT}))

def on_message(client, userdata, msg):
    global state, got_at
    state = json.loads(msg.payload)
    got_at = time.time()

def send(action, **extra):
    client.publish(ACTION, json.dumps({"action": action, **extra}))

client = mqtt.Client(str(uuid.uuid1()))
client.username_pw_set("idd", "device@theFarm")
# If this Pi crashes or loses power, the broker sends "leave" for us
client.will_set(ACTION, json.dumps({"action": "leave"}))
client.on_connect = on_connect
client.on_message = on_message
client.connect("farlab.infosci.cornell.edu", 1883)
client.loop_start()

while True:
    event = read_input()       # your sensor -> "left"/"forward"/"right"/"press" or None
    mode = state.get("mode")
    if event in ("left", "forward", "right") and mode == "holding":
        send("throw", dir=event)
    elif event == "press" and mode == "incoming":
        send("catch")
    # draw(state, time.time() - got_at)   # PiTFT drawing based on state["mode"]
    time.sleep(0.02)
```

Only sending catch while `mode == "incoming"` also protects you from butterfingers.

Suggested input mappings (each team decides its own):

| Input | Aim / throw | Catch |
|---|---|---|
| Capacitive touch + button | pad 0 / 1 / 2 = left / forward / right, button = throw | button (or any pad) |
| Joystick | push left / up / right | press the stick |
| Rotary encoder | turn to aim (show it on screen), press = throw | press |
| IMU + button | tilt left / forward / right + button | button (or shake) |

Remember to run `sudo systemctl stop piscreen.service` before drawing on the PiTFT.

---

## 6. Running and watching

**Laptop**
```powershell
cd "Lab 6"
.venv\Scripts\activate
cd hot_potato
python server.py
```

Then open the view **by name**: **http://localhost:5000/viktor**. Whoever's name is in the URL is drawn at the **bottom** of the diamond, and everyone else is placed as they sit around you. Teammates open `http://<laptop-ip>:5000/<their name>` (the server prints the IP). `http://localhost:5000/` alone is a spectator view.

In the browser, the name in the URL can also play: `J` join, `←` `↑` `→` throw, `↓` or `C` catch, `Space` start. The **🤖 Bots** button fills empty seats with bots that throw randomly and catch 85% of the time.

**Only one laptop runs `server.py`.** If two do, both print a WARNING about another server.

**Using a different topic** (e.g. to avoid clashing with another team): set `POTATO_TOPIC=IDD/yourteam/potato` before running the server, and change `BASE` on the Pis to match.
