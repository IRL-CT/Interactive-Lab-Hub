"""
Telephone Charades: one player's Pi. Run this on EVERY Pi (one per player).

    python player.py --name Arnav
    python player.py --name Arnav --team charades-arnav --no-mic        # type guesses instead of speaking
    python player.py --name Test --fake-camera --fake-mic --screen none  # try it without hardware

Then open the address it prints (http://<this-pi>:8000) on your laptop: that page shows your prompt,
the clips you have to guess, and the reveal at the end.

The button does everything:
    ACT round    tap  = 3-2-1 countdown, then the webcam records your acting (tap again to redo)
                 hold = send your take
    GUESS round  tap  = speak your guess into the mic (or type it on the laptop page)
                 hold = send your guess
    lobby / end  hold = start a (new) game
"""
import argparse
import pathlib
import queue
import socket
import subprocess
import sys
import threading
import time
import uuid

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from common import DEFAULT_TEAM, VERSION, Bus, Log, b64, decode, now, topics  # noqa: E402
import hardware  # noqa: E402
from web import WebServer  # noqa: E402


class Player:
    def __init__(self, name, team, bus, button, screen, voice, sounds, camera, mic,
                 record_seconds=10, fps=5, log=print):
        self.name, self.team, self.bus = name, team, bus
        self.t = topics(team)
        self.presence = f"{self.t['players']}/{name}"
        self.button, self.screen, self.voice, self.sounds = button, screen, voice, sounds
        self.camera, self.mic = camera, mic
        self.record_seconds, self.fps = record_seconds, fps
        self.log = log
        self.lock = threading.RLock()
        self.events = queue.Queue()
        self.state = {"phase": "connecting"}
        self.clips = {}                 # (game, key) -> {"n": total, "frames": {i: b64}, "actor": name, "fps": n}
        self.take = []                  # my latest take this round (b64 JPEGs), not sent yet
        self.take_id = 0                # goes up with every take, so the laptop page knows a redo is new
        self.live = None                # newest webcam frame (JPEG bytes) while counting down / recording
        self.guess = ""                 # my guess this round, not sent yet
        self.sent = set()               # (game, round) I handed in
        self.round_key = None
        self.round_started = 0
        self.status = ""
        self.busy = None                # "countdown", "recording", "listening" while the device is doing something
        self.busy_text = ""
        self.last_phase = None
        self.last_want = 0
        self.narrated = set()
        self.running = True
        self.uid = uuid.uuid4().hex[:8]  # tells this Pi apart from another Pi that uses the same name
        self.started_at = now()
        self.hosts = {}                 # host id -> when we last heard it (two at once = trouble)
        self.dup_seen = 0               # when another Pi last announced itself with our name
        self.resent = {}                # clip key -> when we last resent it
        self.complete_logged = set()

    # ------------------------------------------------------------------ MQTT

    def attach(self):
        self.bus.will(self.presence, b"", retain=True)   # if this Pi dies, the broker says we left
        self.bus.subscribe(self.t["state"], self.on_state)
        self.bus.subscribe(self.t["clip"] + "/#", self.on_clip)
        self.bus.subscribe(self.presence, self.on_my_presence)
        self.bus.subscribe(self.t["want"], self.on_want)
        self.bus.on_connected(self.announce)

    def announce(self):
        self.bus.publish(self.presence, {"name": self.name, "since": now(), "mic": bool(self.mic.available),
                                         "version": VERSION, "uid": self.uid, "bot": False}, retain=True)

    def on_my_presence(self, topic, payload):
        """Someone else announced themselves with OUR name: two Pis are using the same --name."""
        info = decode(payload)
        # an announcement older than us is our own previous run (restarted quickly), not a second Pi
        if info and info.get("uid") and info["uid"] != self.uid and (info.get("since") or 0) >= self.started_at:
            if now() - self.dup_seen > 30:
                self.log(f"!! another Pi is also called '{self.name}'. Restart one of them with a different --name.")
                self.bus.publish(self.t["control"], {"cmd": "dup", "name": self.name, "from": self.uid})
            self.dup_seen = now()

    def on_want(self, topic, payload):
        """Someone is missing a clip. If it is one of mine, send it again (the host does too)."""
        msg = decode(payload) or {}
        key, game = msg.get("key"), msg.get("game")
        with self.lock:
            c = self.clips.get((game, key))
            if not c or c.get("actor") != self.name or now() - self.resent.get(key, 0) < 2:
                return
            self.resent[key] = now()
            frames = sorted(c["frames"].items())
            n, fps = c["n"], c.get("fps", self.fps)
        for i, jpg in frames:
            self.bus.publish(f"{self.t['clip']}/{game}/{key}", {"i": i, "n": n, "jpg": jpg, "actor": self.name,
                                                                "fps": fps, "resent": True})
        self.log(f"{msg.get('from')} was missing my clip {key}: resent {len(frames)} frames")

    def leave(self):
        self.bus.publish(self.presence, b"", retain=True)

    def on_state(self, topic, payload):
        s = decode(payload) or {"phase": "offline"}
        if s.get("host_id") and now() - (s.get("sent_at") or 0) < 30:
            self.hosts[s["host_id"]] = now()
        with self.lock:
            self.state = s
        self.events.put(("state", None))

    def warnings(self, s):
        w = list(s.get("warnings") or [])
        if sum(1 for t in self.hosts.values() if now() - t < 30) > 1 and not any("Two hosts" in x for x in w):
            w.append("Two hosts are running on this team. Only one person may run host.py.")
        if now() - self.dup_seen < 60:
            w.append(f"Another Pi is also called '{self.name}'. Restart one of them with a different --name.")
        if s.get("version") and s["version"] != VERSION:
            w.append(f"This Pi runs version {VERSION} but the host runs {s['version']}: everyone needs the same charades.zip.")
        return w

    def on_clip(self, topic, payload):
        parts = topic.split("/")
        msg = decode(payload)
        if not msg:
            return
        game, key = parts[-2], parts[-1]
        with self.lock:
            c = self.clips.setdefault((game, key), {"frames": {}})
            c["frames"][int(msg["i"])] = msg["jpg"]
            c["n"], c["actor"], c["fps"] = int(msg["n"]), msg.get("actor"), msg.get("fps", 5)
            done = len(c["frames"]) >= c["n"] and (game, key) not in self.complete_logged
            if done:
                self.complete_logged.add((game, key))
        if done and c["actor"] != self.name:
            self.log(f"received clip {key} from {c['actor']}: {c['n']} frames")

    # ------------------------------------------------------------------ where am I in the game?

    def snapshot(self):
        with self.lock:
            s = dict(self.state)
        phase = s.get("phase")
        mine = (s.get("assignments") or {}).get(self.name) if phase == "play" else None
        rk = (s.get("game"), s.get("round")) if phase == "play" else None
        handed = bool(rk) and (rk in self.sent or self.name in (s.get("submitted") or []))
        return s, phase, mine, rk, handed

    def time_left(self, s):
        d = s.get("deadline")
        return max(0, int(d - now())) if d else None

    # ------------------------------------------------------------------ the loop

    def run(self):
        while self.running:
            ev = self.next_event()
            if ev:
                self.handle(*ev)
            self.tick()

    def next_event(self):
        try:
            return self.events.get_nowait()
        except queue.Empty:
            pass
        kind = self.button.wait(0.1)
        return (kind, None) if kind else None

    def handle(self, kind, data):
        if kind == "state":
            return
        s, phase, mine, rk, handed = self.snapshot()
        self.sync(s, phase, mine, rk)                # a press right after a new round belongs to the new round
        if kind == "guess_text":                   # typed on the laptop page
            if mine and mine["task"] == "guess" and not handed:
                self.guess = (data or "").strip()
                if self.guess:
                    self.send_guess(s, rk, mine)
            return
        if phase in ("lobby", "reveal"):
            if kind == "hold":
                self.bus.publish(self.t["control"], {"cmd": "start", "from": self.name})
                self.status = "Asked the host to start the game."
            else:
                self.status = "Hold the button to start the game."
            return
        if phase != "play":
            self.status = "The host is not running yet."
            return
        if not mine:
            self.status = "A game is running without you. You'll join the next one."
            return
        if handed:
            self.status = "Already sent. Waiting for the others."
            return
        if mine["task"] == "act":
            if kind == "tap":
                self.record_take(mine)
            elif self.take:
                self.send_act(s, rk, mine)
            else:
                self.status = "Record a take first (tap)."
        else:
            if kind == "tap":
                self.listen()
            elif self.guess:
                self.send_guess(s, rk, mine)
            else:
                self.status = "Say your guess first (tap), or type it on the laptop."

    # ------------------------------------------------------------------ acting

    def record_take(self, mine):
        secs = self.record_seconds
        try:
            self.camera.open()
        except Exception as err:
            self.status = f"Camera problem: {err}"
            self.log(self.status)
            return
        def live(jpg):
            self.live = jpg

        try:
            for n in (3, 2, 1):
                self.busy, self.busy_text = "countdown", str(n)
                self.screen.show("GET READY", str(n), "get in front of the camera", "act")
                self.sounds.play("tick")
                self.camera.warm(1.0, on_frame=live)
            self.busy, self.busy_text = "recording", f"{secs}"
            self.sounds.play("go")

            def progress(t):
                left = max(1, secs - int(t))
                self.busy_text = str(left)
                self.screen.show("● RECORDING", f"{left}", mine["text"], "rec")
            frames = self.camera.record(secs, self.fps, progress, on_frame=live)
        finally:
            self.camera.close()
            self.busy = None
            self.live = None
        self.sounds.play("stop")
        self.take = [b64(f) for f in frames]
        self.take_id += 1
        self.status = f"Take recorded ({len(frames)} frames). Tap to redo, hold to send."
        self.log(f"recorded a take: {len(frames)} frames")
        self.drain_presses()

    def send_act(self, s, rk, mine):
        game, rnd = rk
        key, n = mine["key"], len(self.take)
        frames = list(self.take)
        with self.lock:
            self.clips[(game, key)] = {"n": n, "frames": dict(enumerate(frames)), "actor": self.name, "fps": self.fps}
        for i, jpg in enumerate(frames):
            self.bus.publish(f"{self.t['clip']}/{game}/{key}", {"i": i, "n": n, "jpg": jpg, "actor": self.name, "fps": self.fps})
        self.bus.publish(self.t["submit"], {"game": game, "round": rnd, "player": self.name, "kind": "act", "frames": n})
        self.sent.add(rk)
        self.sounds.play("done")
        self.button.led(0)
        self.status = "Clip sent! Waiting for the others."
        self.log(f"sent my clip ({n} frames)")

    # ------------------------------------------------------------------ guessing

    def listen(self):
        if not self.mic.available:
            self.status = "No mic on this Pi: type your guess on the laptop page."
            return
        self.busy, self.busy_text = "listening", ""
        self.screen.show("MIC ON", "say your guess", "listening for 4 s...", "guess")
        self.sounds.play("tick")
        try:
            text = self.mic.listen(4)
        finally:
            self.busy = None
        if text is None:
            self.status = "The mic didn't work. Type your guess on the laptop page."
        elif not text:
            self.status = "I didn't catch that. Tap to try again, or type it."
        else:
            self.guess = text
            self.status = f'Heard "{text}". Hold to send, tap to try again, or fix it on the laptop.'
        self.log(f"heard: {text!r}")
        self.drain_presses()

    def send_guess(self, s, rk, mine):
        game, rnd = rk
        self.bus.publish(self.t["submit"], {"game": game, "round": rnd, "player": self.name, "kind": "guess", "text": self.guess})
        self.sent.add(rk)
        self.sounds.play("done")
        self.button.led(0)
        self.status = f'Guess sent: "{self.guess}". Waiting for the others.'
        self.log(f"sent my guess: {self.guess!r}")

    def drain_presses(self):
        """Presses that arrived while the camera or mic was busy are dropped, not replayed."""
        keep = []
        while True:
            try:
                ev = self.events.get_nowait()
            except queue.Empty:
                break
            if ev[0] not in ("tap", "hold"):
                keep.append(ev)
        for ev in keep:
            self.events.put(ev)

    # ------------------------------------------------------------------ every 0.1 s

    def tick(self):
        s, phase, mine, rk, handed = self.snapshot()
        self.sync(s, phase, mine, rk)
        if phase == "reveal" and s.get("narrator") == self.name and s.get("game") not in self.narrated:
            self.narrated.add(s.get("game"))
            for line in s.get("summary") or []:
                self.voice.say(f"{line['owner']}'s prompt was {line['start']}. In the end it became {line['end']}.")
        self.request_missing(s, phase, mine)
        if not self.busy:
            self.screen.show(*self.screen_content(s, phase, mine, handed))

    def sync(self, s, phase, mine, rk):
        """React once to a new round or phase: forget the old take/guess, beep, say whose turn it is."""
        if rk != self.round_key:                    # a new round (or the game ended)
            self.round_key, self.round_started = rk, now()
            self.take, self.guess = [], ""
            if mine and mine["task"] == "act":
                self.log(f'round {s["round"] + 1}: act "{mine["text"]}" (clip {mine["key"]})')
            elif mine:
                with self.lock:
                    c = self.clips.get((s.get("game"), mine.get("clip"))) or {"frames": {}, "n": 0}
                self.log(f"round {s['round'] + 1}: guess {mine.get('from')}'s clip {mine.get('clip')} "
                         f"(have {len(c['frames'])}/{c.get('n', 0)} frames)")
            if mine:
                self.status = ""
                r = s["round"] + 1
                if mine["task"] == "act":
                    self.voice.say(f"Round {r}. Your turn to act. Look at your screen.")
                else:
                    self.voice.say(f"Round {r}. Your turn to guess. Watch your laptop.")
                self.sounds.play("turn")
                self.button.pulse()
        if phase != self.last_phase:
            if phase == "reveal":
                self.status = ""
                self.button.led(0)
                self.sounds.play("turn")
                self.voice.say("Game over! Look at your laptop for the reveal.")
            self.last_phase = phase

    def request_missing(self, s, phase, mine):
        """A Pi that joined late or restarted asks the host to resend clips it does not have."""
        if now() - self.last_want < 4 or now() - self.round_started < 2:
            return
        keys = []
        if phase == "play" and mine and mine["task"] == "guess" and mine.get("clip"):
            keys = [mine["clip"]]
        elif phase == "reveal":
            keys = [st["clip"] for ch in s.get("chains") or [] for st in ch["steps"] if st.get("clip")]
        with self.lock:
            missing = [k for k in keys if not self.clip_complete(s.get("game"), k)]
        for k in missing:
            self.log(f"missing clip {k}: asking for it again")
            self.bus.publish(self.t["want"], {"game": s.get("game"), "key": k, "from": self.name})
        if missing:
            self.last_want = now()

    def clip_complete(self, game, key):
        c = self.clips.get((game, key))
        return bool(c) and len(c["frames"]) >= c.get("n", 1)

    # ------------------------------------------------------------------ what the PiTFT says

    def screen_content(self, s, phase, mine, handed):
        tap, hold = self.button.hints()
        if phase == "connecting":
            return "CHARADES", "connecting...", self.team, "info"
        if phase == "offline":
            return "CHARADES", "host is offline", "start host.py", "info"
        if phase == "lobby":
            names = ", ".join(s.get("lobby") or []) or "nobody yet"
            return "LOBBY", names, f"{hold} = start game", "info"
        if phase == "reveal":
            return "GAME OVER", "see the reveal on your laptop", f"{hold} = new game", "reveal"
        if phase != "play":
            return "CHARADES", str(phase), "", "info"
        if not mine:
            return "GAME ON", "you'll join the next game", "", "info"
        left = self.time_left(s)
        clock = f"  {left // 60}:{left % 60:02d}" if left is not None else ""
        head = f"ROUND {s['round'] + 1}/{s['rounds']}"
        if handed:
            waiting = s.get("waiting_for") or []
            body = ("waiting for " + ", ".join(waiting)) if waiting else "everyone's in!"
            return f"SENT ✓{clock}", body, "next round soon", "wait"
        if mine["task"] == "act":
            bottom = f"{tap} = redo · {hold} = send" if self.take else f"{tap} = record ({self.record_seconds} s)"
            return f"{head} · ACT{clock}", mine["text"], bottom, "act"
        if self.guess:
            return f"{head} · GUESS{clock}", f'"{self.guess}"', f"{tap} = again · {hold} = send", "guess"
        bottom = f"{tap} = say it · or type it" if self.mic.available else "type it on your laptop"
        return f"{head} · GUESS{clock}", "watch your laptop", bottom, "guess"

    # ------------------------------------------------------------------ for the laptop page

    def view(self):
        s, phase, mine, rk, handed = self.snapshot()
        v = {"me": self.name, "team": self.team, "phase": phase, "connected": self.bus.connected.is_set(),
             "version": VERSION, "warnings": self.warnings(s), "bots": s.get("bots") or [],
             "versions": s.get("versions") or {},
             "lobby": s.get("lobby") or [], "players": s.get("players") or [], "game": s.get("game"),
             "round": s.get("round"), "rounds": s.get("rounds"), "status": self.status,
             "busy": self.busy, "busy_text": self.busy_text, "mic": bool(self.mic.available),
             "in_game": bool(mine), "handed_in": handed, "waiting_for": s.get("waiting_for") or [],
             "time_left": self.time_left(s) if phase == "play" else None,
             "take_frames": len(self.take), "take_id": self.take_id, "guess": self.guess, "fps": self.fps,
             "record_seconds": self.record_seconds, "hints": dict(zip(("tap", "hold"), self.button.hints()))}
        if mine:
            v["assignment"] = mine
        if phase == "reveal":
            v["chains"], v["summary"] = s.get("chains"), s.get("summary")
        return v

    def clip_view(self, key, game=None):
        with self.lock:
            if key == "take":
                return {"key": key, "n": len(self.take), "frames": list(self.take), "fps": self.fps,
                        "take_id": self.take_id}
            game = game or self.state.get("game")
            c = self.clips.get((game, key)) or {"frames": {}, "n": 0}
            frames = [c["frames"][i] for i in sorted(c["frames"])]
            return {"key": key, "n": c.get("n", 0), "frames": frames, "actor": c.get("actor"), "fps": c.get("fps", 5)}

    def web_action(self, action, text=None):
        if action in ("tap", "hold"):
            self.events.put((action, None))
        elif action == "guess":
            self.events.put(("guess_text", text))
        else:
            return False
        return True


def my_addresses():
    try:
        out = subprocess.run(["hostname", "-I"], capture_output=True, text=True, timeout=3).stdout.split()
        ips = [ip for ip in out if ":" not in ip]
    except Exception:
        ips = []
    try:
        ips.append(socket.gethostname() + ".local")
    except Exception:
        pass
    return ips or ["localhost"]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--name", required=True, help="your player name (one word, e.g. Arnav)")
    ap.add_argument("--team", default=DEFAULT_TEAM, help="must be the same on every Pi")
    ap.add_argument("--port", type=int, default=8000, help="port for the laptop page")
    ap.add_argument("--button", default="auto", choices=["auto", "qwiic", "pitft", "keyboard"])
    ap.add_argument("--screen", default="auto", choices=["auto", "pitft", "none"])
    ap.add_argument("--no-voice", action="store_true")
    ap.add_argument("--no-sound", action="store_true", help="no beeps")
    ap.add_argument("--no-mic", action="store_true", help="type guesses on the laptop instead")
    ap.add_argument("--mic-device", default="default", help="arecord device, e.g. plughw:2,0 (see arecord -l)")
    ap.add_argument("--camera", type=int, default=0, help="webcam index")
    ap.add_argument("--record-seconds", type=int, default=10, help="length of a take (default 10 s)")
    ap.add_argument("--fps", type=int, default=5)
    ap.add_argument("--fake-camera", action="store_true", help="drawn frames instead of the webcam")
    ap.add_argument("--fake-mic", action="store_true", help="pretend to hear a guess")
    ap.add_argument("--broker", default=None)
    ap.add_argument("--broker-port", type=int, default=None)
    args = ap.parse_args()
    name = args.name.strip().replace("/", "-").replace(" ", "-")

    button = hardware.Button(args.button)
    screen = hardware.TerminalScreen() if args.screen == "none" else hardware.make_screen(args.screen)
    camera = hardware.make_camera(args.fake_camera, args.camera)
    mic = hardware.FakeMic() if args.fake_mic else hardware.Mic(not args.no_mic, args.mic_device)
    voice = hardware.Voice(not args.no_voice)
    sounds = hardware.Sounds(not args.no_sound)

    kw = {k: v for k, v in (("broker", args.broker), ("port", args.broker_port)) if v}
    bus = Bus(name, **kw)
    log = Log(f"player-{name}")
    player = Player(name, args.team, bus, button, screen, voice, sounds, camera, mic,
                    record_seconds=args.record_seconds, fps=args.fps, log=log)
    player.attach()
    web = WebServer(player, args.port)
    web.start()
    screen.show("CHARADES", "connecting...", args.team, "info")
    print(f"connecting to {bus.broker}...", flush=True)
    try:
        bus.start()
    except ConnectionError as err:
        screen.show("CHARADES", "no broker", "check the Wi-Fi", "info")
        sys.exit(str(err))
    print(f"\n{name} (v{VERSION}) is in team '{args.team}'. On your laptop, open:")
    for ip in my_addresses():
        print(f"    http://{ip}:{args.port}")
    print("\nCtrl-C to quit.\n", flush=True)
    try:
        player.run()
    except KeyboardInterrupt:
        pass
    finally:
        player.leave()
        time.sleep(0.5)
        screen.off()
        button.led(0)
        bus.stop()


if __name__ == "__main__":
    main()
