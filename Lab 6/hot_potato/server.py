"""
Hot Potato server  (Lab 6, Part C)
==================================

Runs on the laptop. It is the single source of truth for the game:
  * listens for player actions over MQTT   ->  IDD/hotpotato/player/<name>/action
  * runs the timers (30 s round, hold limit, throws, catches, explosions)
  * tells every Pi what to draw            ->  IDD/hotpotato/player/<name>/state
  * serves the diamond view in a browser   ->  http://localhost:5000/<name>

Run:
    pip install -r ../requirements-server.txt
    python server.py

See PROTOCOL.md for the exact message formats.
"""

import json
import os
import random
import socket
import sys
import threading
import time
import traceback
import uuid

import paho.mqtt.client as mqtt
from flask import Flask, render_template
from flask_socketio import SocketIO

# --------------------------------------------------------------------------
# Config  (env vars let you point at a different broker / topic for testing)
# --------------------------------------------------------------------------
MQTT_BROKER = os.environ.get("MQTT_BROKER", "farlab.infosci.cornell.edu")
MQTT_PORT = int(os.environ.get("MQTT_PORT", "1883"))
MQTT_USER = os.environ.get("MQTT_USER", "idd")
MQTT_PASS = os.environ.get("MQTT_PASS", "device@theFarm")
BASE = os.environ.get("POTATO_TOPIC", "IDD/hotpotato").rstrip("/")
WEB_PORT = int(os.environ.get("PORT", "5000"))

ROUND_TIME = 30.0         # every round lasts 30 s; whoever has the potato at 0 explodes
START_HOLD_LIMIT = 10.0   # max seconds you may hold the potato at the start of a round
MIN_HOLD_LIMIT = 3.0      # it never gets shorter than this
SHRINK_PER_CATCH = 0.5    # every successful catch makes the limit this much shorter
FLIGHT_TIME = 1.5         # seconds in the air = the window to press CATCH
CATCH_LOCKOUT = 1.0       # pressing catch when nothing is coming locks catching for this long
BOOM_PAUSE = 3.0          # seconds of explosion before the next round starts
MAX_BOOMS = 3             # explode this many times and you lose the game
BOT_CATCH_CHANCE = 0.85   # bots miss the catch 15% of the time
TICK = 0.05               # game loop period (s)
HOLDER_REFRESH = 0.5      # how often Pis get fresh timer values while it matters (s)

SEATS = (1, 2, 3, 4)      # seats go CLOCKWISE around the table, seen from above
DIR_OFFSET = {"left": 1, "forward": 2, "right": 3}
DIR_ALIASES = {
    "l": "left", "left": "left",
    "f": "forward", "forward": "forward", "up": "forward", "across": "forward", "straight": "forward",
    "r": "right", "right": "right",
}
MAX_NAME = 20
LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "server_log.txt")
_log_lock = threading.Lock()


def log(line):
    """Print and append to server_log.txt (handy for debugging what the Pis really sent)."""
    print(line)
    try:
        with _log_lock, open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(time.strftime("%H:%M:%S ") + line + "\n")
    except OSError:
        pass


def target_seat(seat, direction):
    """Seat that sits to my left / across / right."""
    return (seat - 1 + DIR_OFFSET[direction]) % 4 + 1


def dir_between(src, dst):
    """Direction src is in, as seen by dst (left / forward / right)."""
    for d in DIR_OFFSET:
        if target_seat(dst, d) == src:
            return d
    return None


# --------------------------------------------------------------------------
# Game state
# --------------------------------------------------------------------------
class Game:
    def __init__(self):
        self.lock = threading.RLock()
        self.players = {s: None for s in SEATS}   # seat -> dict | None
        self.phase = "lobby"                      # lobby | playing | boom | gameover
        self.holder = None                        # seat
        self.hold_start = 0.0
        self.hold_limit = START_HOLD_LIMIT
        self.catches = 0
        self.flight = None                        # {"from", "to", "dir", "start", "caught", "bot_catch_at"}
        self.round_end = None
        self.boom_seat = None
        self.boom_reason = None
        self.boom_time = 0.0
        self.loser = None                         # seat
        self.bots_on = False
        self.message = "Waiting for players to join..."
        self.events = []
        self.dirty = True

    # ---------- helpers ----------
    def joined(self):
        return [s for s in SEATS if self.players[s]]

    def seat_of(self, name):
        """Seat of a player by name (exact match first, then case-insensitive)."""
        for s, p in self.players.items():
            if p and p["name"] == name:
                return s
        low = str(name).lower()
        for s, p in self.players.items():
            if p and p["name"].lower() == low:
                return s
        return None

    def name(self, seat):
        p = self.players.get(seat) if seat else None
        return p["name"] if p else None

    def _event(self, kind, **data):
        data["type"] = kind
        data["t"] = time.time()
        self.events.append(data)
        self.dirty = True

    def _new_player(self, seat, name, input_type, bot=False):
        old = self.players[seat]
        self.players[seat] = {
            "name": name, "input": input_type or ("bot" if bot else "?"), "bot": bot,
            "booms": old["booms"] if old else 0, "bot_throw_at": None, "lockout_until": 0.0,
        }
        self._event("join", seat=seat, name=name, input=self.players[seat]["input"])
        return seat

    def join(self, name, seat=None, input_type=None):
        """Put a player in a seat. Returns (seat | None, reason)."""
        current = self.seat_of(name)
        if current:
            if input_type:
                self.players[current]["input"] = input_type
            wanted = seat if seat in SEATS else None
            free = wanted and (not self.players[wanted] or self.players[wanted]["bot"])
            if wanted and wanted != current and free and self.phase not in ("playing", "boom"):
                self.players[wanted] = self.players[current]   # move seats (only between games)
                self.players[current] = None
                self._event("join", seat=wanted, name=name)
                return wanted, f"moved to seat {wanted}"
            return current, f"already in seat {current}"
        candidates = []
        if seat in SEATS:
            candidates.append(seat)
        candidates += [s for s in SEATS if not self.players[s]]
        candidates += [s for s in SEATS if self.players[s] and self.players[s]["bot"]]
        for s in candidates:
            p = self.players[s]
            if p is None or p["bot"]:
                self._new_player(s, name, input_type)
                if self.holder == s and p and p["bot"]:
                    self.hold_start = time.time()   # fair start for the human taking over
                self.message = f"{name} joined seat {s}"
                return s, f"joined seat {s}"
        return None, "game is full (4 players)"

    def _give_potato(self, seat, now):
        self.holder = seat
        self.hold_start = now
        self.flight = None
        p = self.players[seat]
        if p and p["bot"]:
            p["bot_throw_at"] = now + random.uniform(0.8, max(1.0, min(5.0, self.hold_limit - 1.0)))
        self.dirty = True

    # ---------- actions (from MQTT or browser) ----------
    def handle(self, name, msg):
        """name = player name from the topic, msg = dict like {"action": "throw", "dir": "left"}."""
        name = str(name).strip()
        if not name or len(name) > MAX_NAME:
            return False, f"name must be 1-{MAX_NAME} characters"
        action = str(msg.get("action", "throw" if "dir" in msg else "")).lower()
        with self.lock:
            if action == "join":
                seat = msg.get("seat")
                try:
                    seat = int(seat) if seat is not None else None
                except (TypeError, ValueError):
                    seat = None
                s, reason = self.join(name, seat, msg.get("input"))
                return s is not None, reason
            if action == "start":
                return self.start()
            if action == "reset":
                self.reset()
                return True, "reset"
            seat = self.seat_of(name)
            if action == "leave":
                if seat:
                    self._remove(seat)
                return True, "left"
            if seat is None:   # unknown player sending a throw/catch -> join them first
                seat, reason = self.join(name, None, msg.get("input"))
                if seat is None:
                    return False, reason
            if action == "throw":
                return self.throw(seat, msg.get("dir", ""))
            if action == "catch":
                return self.catch(seat)
            return False, f"unknown action '{action}'"

    def _remove(self, seat):
        """A player leaves. If the potato was theirs, pass it on instead of ending the game."""
        name = self.players[seat]["name"]
        self.players[seat] = None
        self._event("leave", seat=seat, name=name)
        self.message = f"{name} left seat {seat}"
        if self.phase not in ("playing", "boom"):
            return
        remaining = self.joined()
        if len(remaining) < 2:
            self.reset()
            self.message = "Not enough players left - back to the lobby"
            return
        if self.phase != "playing":
            return
        if self.holder == seat:
            self._give_potato(random.choice(remaining), time.time())
        elif self.flight and self.flight["to"] == seat:
            back = self.flight["from"]
            self._give_potato(back if self.players[back] else random.choice(remaining), time.time())

    def start(self):
        with self.lock:
            if self.phase in ("playing", "boom"):
                return False, "game already running (use Reset to restart)"
            if self.bots_on:
                self._fill_bots()
            seats = self.joined()
            if len(seats) < 2:
                self.message = "Need at least 2 players to start"
                self.dirty = True
                return False, "need 2+ players"
            for s in seats:
                self.players[s]["booms"] = 0
            self.loser = None
            self._new_round(time.time())
            return True, "started"

    def reset(self):
        with self.lock:
            self.phase = "lobby"
            self.holder = None
            self.flight = None
            self.round_end = None
            self.boom_seat = None
            self.boom_reason = None
            self.loser = None
            for p in self.players.values():
                if p:
                    p["booms"] = 0
            self.message = "Lobby - press Start"
            self._event("reset")

    def _new_round(self, now):
        self.phase = "playing"
        self.hold_limit = START_HOLD_LIMIT
        self.catches = 0
        self.boom_seat = None
        self.boom_reason = None
        self.round_end = now + ROUND_TIME
        first = random.choice(self.joined())
        self._give_potato(first, now)
        self.message = f"New round! {self.name(first)} has the potato"
        self._event("round", holder=first, holder_name=self.name(first), round_time=ROUND_TIME)

    def throw(self, seat, direction):
        direction = DIR_ALIASES.get(str(direction).lower().strip())
        if direction is None:
            return False, "dir must be left / forward / right"
        if self.phase != "playing":
            return False, f"game is not running ({self.phase})"
        if self.flight:
            return False, "potato is already in the air"
        if self.holder != seat:
            return False, "you don't have the potato"
        to = target_seat(seat, direction)
        if not self.players[to]:
            return False, f"nobody sits {direction} of you (seat {to})"
        now = time.time()
        bot_catch_at = None
        if self.players[to]["bot"] and random.random() < BOT_CATCH_CHANCE:
            bot_catch_at = now + random.uniform(0.25, FLIGHT_TIME - 0.15)
        self.holder = None
        self.flight = {"from": seat, "to": to, "dir": direction, "start": now,
                       "caught": False, "bot_catch_at": bot_catch_at}
        self.message = f"{self.name(seat)} threw {direction} to {self.name(to)} - CATCH!"
        self._event("throw", **{"from": seat, "to": to, "from_name": self.name(seat),
                                "to_name": self.name(to), "dir": direction, "flight_time": FLIGHT_TIME})
        return True, f"thrown to {self.name(to)}"

    def catch(self, seat):
        now = time.time()
        if self.phase != "playing":
            return False, f"game is not running ({self.phase})"
        p = self.players[seat]
        if self.flight and self.flight["to"] == seat:
            if self.flight["caught"]:
                return True, "already caught"
            if now < p["lockout_until"]:
                return False, f"butterfingers! wait {p['lockout_until'] - now:.1f}s"
            self.flight["caught"] = True
            self.message = f"{p['name']} is catching it!"
            self._event("catch_press", seat=seat, name=p["name"])
            return True, "caught"
        if self.holder == seat:
            return False, "you already have it - throw it!"
        # pressed catch with nothing coming: short lockout so spamming catch doesn't work
        p["lockout_until"] = now + CATCH_LOCKOUT
        self.dirty = True
        return False, f"nothing to catch - butterfingers for {CATCH_LOCKOUT:.0f}s"

    # ---------- bots ----------
    def set_bots(self, on):
        with self.lock:
            self.bots_on = bool(on)
            if self.bots_on:
                self._fill_bots()
            else:
                for s in SEATS:
                    p = self.players[s]
                    busy = self.holder == s or (self.flight and self.flight["to"] == s)
                    if p and p["bot"] and not (busy and self.phase == "playing"):
                        self.players[s] = None
                        self._event("leave", seat=s, name=p["name"])
            self.dirty = True

    def _fill_bots(self):
        for s in SEATS:
            if not self.players[s]:
                self._new_player(s, f"Bot {s}", "bot", bot=True)

    # ---------- clock ----------
    def tick(self, now):
        with self.lock:
            if self.phase == "playing":
                if now >= self.round_end:
                    victim = self.holder or (self.flight and self.flight["to"])
                    if victim and self.players[victim]:
                        self.holder = victim
                        self._boom(now, "time's up")
                        return
                if self.flight:
                    f = self.flight
                    if f["bot_catch_at"] and not f["caught"] and now >= f["bot_catch_at"]:
                        f["caught"] = True
                        self._event("catch_press", seat=f["to"], name=self.name(f["to"]))
                    if now - f["start"] >= FLIGHT_TIME:
                        to = f["to"]
                        if f["caught"]:
                            self.catches += 1
                            self.hold_limit = max(MIN_HOLD_LIMIT, START_HOLD_LIMIT - self.catches * SHRINK_PER_CATCH)
                            self._give_potato(to, now)
                            self.message = f"{self.name(to)} caught it!"
                            self._event("catch", seat=to, name=self.name(to), hold_limit=self.hold_limit)
                        else:
                            self.holder = to
                            self._boom(now, "dropped it")
                elif self.holder:
                    p = self.players[self.holder]
                    if now - self.hold_start >= self.hold_limit:
                        self._boom(now, "held it too long")
                    elif p and p["bot"] and p["bot_throw_at"] and now >= p["bot_throw_at"]:
                        p["bot_throw_at"] = None
                        options = [d for d in DIR_OFFSET if self.players[target_seat(self.holder, d)]]
                        if options:
                            self.throw(self.holder, random.choice(options))
            elif self.phase == "boom" and now - self.boom_time >= BOOM_PAUSE:
                if self.loser:
                    self.phase = "gameover"
                    self.message = f"GAME OVER - {self.name(self.loser)} exploded {MAX_BOOMS} times"
                    self._event("gameover", loser=self.loser, loser_name=self.name(self.loser))
                elif len(self.joined()) >= 2:
                    self._new_round(now)
                else:
                    self.reset()

    def _boom(self, now, reason):
        seat = self.holder
        p = self.players[seat]
        self.holder = None
        self.flight = None
        if p is None:            # holder vanished; just start over
            self._new_round(now) if len(self.joined()) >= 2 else self.reset()
            return
        p["booms"] += 1
        self.phase = "boom"
        self.boom_seat = seat
        self.boom_reason = reason
        self.boom_time = now
        if p["booms"] >= MAX_BOOMS:
            self.loser = seat
        self.message = f"BOOM! {p['name']} {reason} ({p['booms']}/{MAX_BOOMS})"
        self._event("boom", seat=seat, name=p["name"], booms=p["booms"], reason=reason)

    # ---------- views ----------
    def seat_view(self, seat, now):
        """What one Pi should draw. Published to IDD/hotpotato/player/<name>/state."""
        p = self.players[seat]
        mode, heat, time_left, incoming_from, caught = "waiting", 0.0, None, None, False
        flight_left = None
        if p is None:
            mode = "empty"
        elif self.phase == "lobby":
            mode = "lobby"
        elif self.phase == "gameover":
            mode = "gameover"
        elif self.phase == "boom":
            mode = "boom" if seat == self.boom_seat else "safe"
        elif self.holder == seat:
            mode = "holding"
            held = now - self.hold_start
            heat = min(1.0, held / self.hold_limit)
            time_left = max(0.0, self.hold_limit - held)
        elif self.flight and self.flight["to"] == seat:
            mode = "incoming"
            incoming_from = self.flight["from"]
            caught = self.flight["caught"]
            flight_left = max(0.0, FLIGHT_TIME - (now - self.flight["start"]))
        round_left = max(0.0, self.round_end - now) if self.phase == "playing" and self.round_end else None
        targets = {d: self.name(target_seat(seat, d)) for d in DIR_OFFSET}
        return {
            "name": p["name"] if p else None,
            "seat": seat,
            "mode": mode,
            "holder": self.name(self.holder),
            "targets": targets,
            "boom_name": self.name(self.boom_seat) if self.phase == "boom" else None,
            "heat": round(heat, 3),
            "time_left": None if time_left is None else round(time_left, 2),
            "hold_limit": self.hold_limit,
            "round_left": None if round_left is None else round(round_left, 2),
            "round_time": ROUND_TIME,
            "incoming_from": self.name(incoming_from),
            "incoming_dir": dir_between(incoming_from, seat) if incoming_from else None,
            "caught": caught,
            "flight_left": None if flight_left is None else round(flight_left, 2),
            "flight_time": FLIGHT_TIME,
            "butterfingers": bool(p and now < p["lockout_until"]),
            "booms": p["booms"] if p else 0,
            "max_booms": MAX_BOOMS,
            "boom_reason": self.boom_reason if mode == "boom" else None,
            "loser": self.name(self.loser),
            "phase": self.phase,
        }

    def snapshot(self, now):
        with self.lock:
            flight = None
            if self.flight:
                flight = {k: self.flight[k] for k in ("from", "to", "dir", "caught")}
                flight["progress"] = min(1.0, (now - self.flight["start"]) / FLIGHT_TIME)
                flight["flight_time"] = FLIGHT_TIME
            return {
                "phase": self.phase,
                "holder": self.holder,
                "hold_limit": self.hold_limit,
                "time_left": max(0.0, self.hold_limit - (now - self.hold_start)) if self.holder else None,
                "round_left": max(0.0, self.round_end - now) if self.phase == "playing" and self.round_end else None,
                "round_time": ROUND_TIME,
                "flight": flight,
                "boom_seat": self.boom_seat,
                "boom_reason": self.boom_reason,
                "loser": self.loser,
                "catches": self.catches,
                "bots_on": self.bots_on,
                "message": self.message,
                "max_booms": MAX_BOOMS,
                "players": {s: (None if not p else {k: p[k] for k in ("name", "input", "bot", "booms")})
                            for s, p in self.players.items()},
                "seats": {s: self.seat_view(s, now) for s in SEATS},
            }


game = Game()

# --------------------------------------------------------------------------
# Web server
# --------------------------------------------------------------------------
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")


@app.route("/")
@app.route("/<me>")
def index(me=""):
    return render_template("potato.html", me=me, base_topic=BASE)


@socketio.on("connect")
def on_web_connect():
    socketio.emit("state", game.snapshot(time.time()))


@socketio.on("action")
def on_web_action(data):
    """Browser test controls send the same messages a Pi would."""
    name = str(data.get("name") or "").strip()
    if not name:
        return {"ok": False, "reason": "open the page as /<your name> to play from the browser"}
    ok, reason = game.handle(name, data)
    log(f"[web]  {name}: {data.get('action')} {data.get('dir') or ''} -> {'OK' if ok else 'REJECTED'}: {reason}")
    return {"ok": ok, "reason": reason}


@socketio.on("control")
def on_web_control(data):
    cmd = data.get("cmd")
    if cmd == "start":
        ok, reason = game.start()
    elif cmd == "reset":
        game.reset()
        ok, reason = True, "reset"
    elif cmd == "bots":
        game.set_bots(data.get("on"))
        ok, reason = True, "bots"
    else:
        ok, reason = False, "unknown"
    return {"ok": ok, "reason": reason}


# --------------------------------------------------------------------------
# MQTT
# --------------------------------------------------------------------------
def make_client():
    cid = f"hotpotato-server-{uuid.uuid4().hex[:8]}"
    try:   # paho-mqtt 2.x
        return mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id=cid)
    except AttributeError:   # paho-mqtt 1.x (what requirements-server.txt installs)
        return mqtt.Client(client_id=cid)


mqttc = make_client()
SERVER_ID = uuid.uuid4().hex[:8]
STARTED_AT = time.time()
ACTION_PREFIX = f"{BASE}/player/"
resync = threading.Event()        # set on (re)connect -> republish every player's retained state
warned_other_server = False


def mqtt_on_connect(client, userdata, flags, rc):
    if rc == 0:
        client.subscribe(f"{BASE}/player/+/action")
        client.subscribe(f"{BASE}/game")
        print(f"[MQTT] connected to {MQTT_BROKER}:{MQTT_PORT}, listening on {BASE}/player/+/action")
        resync.set()
    else:
        print(f"[MQTT] connection refused (rc={rc}) - check user/password")


def mqtt_on_disconnect(client, userdata, rc):
    if rc != 0:
        print("[MQTT] lost connection to the broker, retrying...")


def check_other_server(payload):
    """Two laptops running server.py on the same topic would fight. Warn loudly."""
    global warned_other_server
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        return
    other = data.get("server_id")
    if other and other != SERVER_ID and data.get("t", 0) > STARTED_AT and not warned_other_server:
        warned_other_server = True
        print("!" * 62)
        print(f"  WARNING: another Hot Potato server ({other}) is publishing on {BASE}.")
        print("  Only ONE laptop should run server.py, or set POTATO_TOPIC to something unique.")
        print("!" * 62)


def parse_payload(raw):
    """Accept JSON ({"action": "throw", "dir": "left"}) or plain text ("left", "catch", "join")."""
    text = raw.decode("utf-8", errors="replace").strip()
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
        text = str(data)
    except json.JSONDecodeError:
        pass
    word = text.lower()
    if word in DIR_ALIASES:
        return {"action": "throw", "dir": word}
    return {"action": word}


def mqtt_on_message(client, userdata, msg):
    # Never let one bad message kill the MQTT thread (paho 1.x stops on exceptions).
    try:
        if msg.topic == f"{BASE}/game":
            check_other_server(msg.payload)
            return
        if not (msg.topic.startswith(ACTION_PREFIX) and msg.topic.endswith("/action")):
            return
        name = msg.topic[len(ACTION_PREFIX):-len("/action")]
        data = parse_payload(msg.payload)
        ok, reason = game.handle(name, data)
        log(f"[MQTT] {name}: {data} -> {'OK' if ok else 'REJECTED'}: {reason}")
        if not ok:
            client.publish(f"{BASE}/player/{name}/error", json.dumps({"request": data, "reason": reason}))
    except Exception:
        traceback.print_exc()


mqttc.username_pw_set(MQTT_USER, MQTT_PASS)
mqttc.on_connect = mqtt_on_connect
mqttc.on_disconnect = mqtt_on_disconnect
mqttc.on_message = mqtt_on_message


# --------------------------------------------------------------------------
# Game loop: advance timers, then push changes to Pis (MQTT) and browsers
# --------------------------------------------------------------------------
def view_key(v):
    return (v["seat"], v["mode"], v["holder"], v["incoming_from"], v["caught"], v["butterfingers"],
            v["booms"], v["phase"], v["hold_limit"], v["loser"], tuple(v["targets"].values()))


def game_loop():
    while True:
        try:
            _game_loop()
        except Exception:
            traceback.print_exc()
            print("[loop] recovered from an error, continuing")
            time.sleep(0.5)


def _game_loop():
    last_keys = {}     # player name -> key of last state we published
    last_sent = {}
    last_web = 0.0
    while True:
        now = time.time()
        if resync.is_set():          # just (re)connected: overwrite any stale retained states
            resync.clear()
            last_keys.clear()
            with game.lock:
                game.dirty = True
        game.tick(now)
        with game.lock:
            events, game.events = game.events, []
            changed, game.dirty = game.dirty, False
            snap = game.snapshot(now)

        for ev in events:
            if ev["type"] in ("throw", "catch", "boom", "round", "join", "leave", "gameover"):
                log("[game] " + ev["type"] + " " + " ".join(f"{k}={v}" for k, v in ev.items()
                                                               if k not in ("type", "t")))
            mqttc.publish(f"{BASE}/events", json.dumps(ev))
            socketio.emit("event", ev)

        present = set()
        for seat, view in snap["seats"].items():
            p = snap["players"][seat]
            if not p or p["bot"]:
                continue
            name = p["name"]
            present.add(name)
            key = view_key(view)
            live = view["phase"] == "playing" and now - last_sent.get(name, 0) >= HOLDER_REFRESH
            if key != last_keys.get(name) or live:
                mqttc.publish(f"{BASE}/player/{name}/state", json.dumps(view), retain=True)
                last_keys[name] = key
                last_sent[name] = now
        for name in [n for n in last_keys if n not in present]:   # players who left
            mqttc.publish(f"{BASE}/player/{name}/state", json.dumps({"name": name, "mode": "left"}), retain=True)
            del last_keys[name]

        if changed:
            public = {k: v for k, v in snap.items() if k != "seats"}
            public.update(server_id=SERVER_ID, t=now)
            mqttc.publish(f"{BASE}/game", json.dumps(public), retain=True)

        if changed or now - last_web >= 0.25:
            socketio.emit("state", snap)
            last_web = now

        time.sleep(TICK)


def local_ips():
    """Every IPv4 address this laptop has (Wi-Fi, Ethernet, VPN...). The first one is the default route."""
    ips = []
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ips.append(s.getsockname()[0])
        s.close()
    except OSError:
        pass
    try:
        for ip in socket.gethostbyname_ex(socket.gethostname())[2]:
            if ip not in ips and not ip.startswith("127."):
                ips.append(ip)
    except OSError:
        pass
    return ips or ["localhost"]


if __name__ == "__main__":
    # Windows consoles can't print every emoji; replace instead of crashing on a fancy name
    try:
        sys.stdout.reconfigure(errors="replace")
        sys.stderr.reconfigure(errors="replace")
    except AttributeError:
        pass
    log(f"---- server started, logging to {LOG_PATH}")
    mqttc.connect_async(MQTT_BROKER, MQTT_PORT, keepalive=30)
    mqttc.loop_start()
    threading.Thread(target=game_loop, daemon=True).start()

    print("=" * 62)
    print("  HOT POTATO server")
    print(f"  Topics:   {BASE}/player/<name>/action   (Pi -> server)")
    print(f"            {BASE}/player/<name>/state    (server -> Pi)")
    print(f"  You:      http://localhost:{WEB_PORT}/<your name>")
    print("  Others (same Wi-Fi) try these - the Wi-Fi one usually starts with 10. or 192.168.:")
    for ip in local_ips():
        print(f"            http://{ip}:{WEB_PORT}/<their name>")
    print("  Can't connect? See TESTING.md -> 'Friends can't open the link'")
    print("=" * 62)
    socketio.run(app, host="0.0.0.0", port=WEB_PORT, allow_unsafe_werkzeug=True)
