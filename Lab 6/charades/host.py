"""
Telephone Charades: the host (game master). Run ONE of these per team, on any Pi or laptop.

It keeps the lobby, starts the game, hands out prompts, collects clips and guesses, moves to the
next round when everyone is in (or the timer runs out), and publishes the reveal at the end.
It never touches a camera or a screen; the players' Pis do that.

    python host.py
    python host.py --guess-seconds 0 --act-seconds 0      # no timers: rounds wait for everyone

In the host terminal:
    Enter      start the game (or a new one after the reveal)
    t + Enter  give everyone 60 more seconds this round
    n + Enter  skip to the next round (someone is stuck)
    q + Enter  quit
A player can also start the game by HOLDING their button in the lobby.
Everything printed here is also saved in charades/logs/host-<date-time>.log.
"""
import argparse
import json
import pathlib
import sys
import threading
import time
import uuid

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from common import (DEFAULT_TEAM, PROMPTS, VERSION, Bus, Log, decode, default_rounds,  # noqa: E402
                    now, pick_prompts, topics)
from game import Game  # noqa: E402

CLIP_WAIT = 10       # seconds to wait for a sent clip's frames to arrive before the guess round starts


class Host:
    def __init__(self, bus, team, rounds=None, act_seconds=180, guess_seconds=180, prompts=None,
                 log=print, clock=now):
        self.bus, self.team, self.t = bus, team, topics(team)
        self.rounds_arg = rounds
        self.seconds = {"act": act_seconds, "guess": guess_seconds}
        self.prompt_pool = prompts or PROMPTS
        self.log, self.clock = log, clock
        self.lock = threading.RLock()
        self.id = uuid.uuid4().hex[:8]
        self.started_at = clock()
        self.present = {}            # name -> presence info (version, uid, bot)
        self.game = None
        self.phase = "lobby"
        self.deadline = None
        self.clips = {}              # (game id, clip key) -> {frame index: jpeg b64}, plus "n", "actor"
        self.dirty = True
        self.start_requested = False
        self.skip_requested = False
        self.extra_requested = 0
        self.waiting_clips_since = None
        self.last_clip_want = 0
        self.other_hosts = {}        # host id -> last time we saw it publish
        self.dup_names = {}          # name -> time a Pi said "someone else uses my name"
        self.last_published = None

    # ------------------------------------------------------------------ wiring

    def attach(self):
        self.bus.will(self.t["state"], json.dumps({"phase": "offline"}), retain=True)
        self.bus.subscribe(self.t["players"] + "/+", self.on_presence)
        self.bus.subscribe(self.t["submit"], self.on_submit)
        self.bus.subscribe(self.t["control"], self.on_control)
        self.bus.subscribe(self.t["clip"] + "/#", self.on_clip)
        self.bus.subscribe(self.t["want"], self.on_want)
        self.bus.subscribe(self.t["state"], self.on_state)

    def on_presence(self, topic, payload):
        name = topic.rsplit("/", 1)[1]
        info = decode(payload)
        with self.lock:
            if info:
                old = self.present.get(name)
                if not old:
                    tags = [f"v{info.get('version', '?')}"] + (["bot"] if info.get("bot") else [])
                    self.log(f"+ {name} joined ({', '.join(tags)})")
                    if info.get("version") != VERSION:
                        self.log(f"  !! {name} runs version {info.get('version', 'old')}, the host runs {VERSION}: "
                                 f"{name} must copy the new charades.zip and restart player.py")
                elif old.get("uid") and info.get("uid") and old["uid"] != info["uid"]:
                    self.log(f"  ({name} restarted, or two Pis are using the name '{name}')")
                self.present[name] = info
            elif name in self.present:
                self.present.pop(name)
                self.log(f"- {name} left")
            self.dirty = True

    def on_state(self, topic, payload):
        """Another host on the same team? Its states would fight with ours."""
        s = decode(payload) or {}
        other = s.get("host_id")
        if other and other != self.id and (s.get("sent_at") or 0) > self.started_at:
            with self.lock:
                if other not in self.other_hosts:
                    self.log(f"  !! ANOTHER HOST is running on team '{self.team}' (id {other}). "
                             "Only one person may run host.py: stop the other one.")
                self.other_hosts[other] = self.clock()
                self.dirty = True

    def on_control(self, topic, payload):
        msg = decode(payload) or {}
        if msg.get("cmd") == "start":
            self.log(f"{msg.get('from', 'someone')} asked to start")
            with self.lock:
                self.start_requested = True
        elif msg.get("cmd") == "dup":
            with self.lock:
                self.dup_names[msg.get("name")] = self.clock()
                self.dirty = True
            self.log(f"  !! two Pis are using the name '{msg.get('name')}': restart one with a different --name")

    def on_submit(self, topic, payload):
        msg = decode(payload) or {}
        with self.lock:
            if not self.game or msg.get("game") != self.game.id:
                return
            why = self.game.submit(msg.get("player"), msg.get("round"), msg.get("kind"),
                                   text=msg.get("text"), frames=int(msg.get("frames") or 0))
            if why:
                self.log(f"  ignored a submission from {msg.get('player')}: {why}")
            else:
                if msg.get("kind") == "guess":
                    what = f'"{msg.get("text")}"'
                else:
                    key = self.game.assignment(msg.get("player"))["key"]
                    what = f"a {msg.get('frames')}-frame clip ({key})"
                self.log(f"  {msg.get('player')} handed in {what}  (waiting for: {', '.join(self.game.waiting_for()) or 'nobody'})")
            self.dirty = True

    def on_clip(self, topic, payload):
        parts = topic.split("/")
        msg = decode(payload)
        if not msg or len(parts) < 2:
            return
        game_id, key = parts[-2], parts[-1]
        with self.lock:
            clip = self.clips.setdefault((game_id, key), {})
            clip[int(msg["i"])] = msg["jpg"]
            clip["n"] = int(msg["n"])
            clip["actor"] = msg.get("actor")

    def frames_have(self, game_id, key):
        clip = self.clips.get((game_id, key)) or {}
        return sum(1 for k in clip if isinstance(k, int)), clip.get("n", 0)

    def on_want(self, topic, payload):
        """A Pi is missing a clip: send the copy the host kept (the actor's Pi resends too)."""
        msg = decode(payload) or {}
        if msg.get("from") == "host":
            return
        with self.lock:
            clip = self.clips.get((msg.get("game"), msg.get("key")))
            frames = [(i, clip[i]) for i in sorted(k for k in clip if isinstance(k, int))] if clip else []
            n, actor = (clip or {}).get("n", 0), (clip or {}).get("actor")
        for i, jpg in frames:
            self.bus.publish(f"{self.t['clip']}/{msg['game']}/{msg['key']}",
                             {"i": i, "n": n, "jpg": jpg, "actor": actor, "resent": True})
        self.log(f"  {msg.get('from')} is missing clip {msg.get('key')}: host resent {len(frames)}/{n} frames")

    # ------------------------------------------------------------------ the game

    def start_game(self):
        with self.lock:
            self.start_requested = False
            players = sorted(self.present)
            if len(players) < 2:
                self.log(f"need at least 2 players to start (have: {', '.join(players) or 'nobody'})")
                return False
            rounds = self.rounds_arg or default_rounds(len(players))
            game_id = "g" + uuid.uuid4().hex[:6]
            self.game = Game(players, pick_prompts(len(players), self.prompt_pool), rounds, game_id)
            self.phase = "play"
            self.deadline = self._deadline()
            self.clips = {}
            self.waiting_clips_since = None
            self.dirty = True
        self.log(f"\n=== game {game_id}: {', '.join(players)}, {rounds} rounds ===")
        for ch in self.game.chains:
            self.log(f"  {ch['owner']} starts with: {ch['steps'][0]['text']}")
        self._log_round()
        return True

    def _deadline(self):
        secs = self.seconds[self.game.task]
        return self.clock() + secs if secs else None

    def _log_round(self):
        g = self.game
        limit = self.seconds[g.task]
        self.log(f"\n--- round {g.round + 1}/{g.rounds}: {g.task.upper()} "
                 f"({f'{limit} s' if limit else 'no time limit'}) ---")
        for p, a in g.assignments().items():
            if a["task"] == "act":
                self.log(f'  {p}: act "{a["text"]}"  -> clip {a["key"]}')
            elif a.get("clip"):
                have, n = self.frames_have(g.id, a["clip"])
                self.log(f"  {p}: guess {a.get('from')}'s clip {a['clip']}  (host has {have}/{n} frames)")
            else:
                self.log(f"  {p}: guess, but {a.get('from')} sent no clip")

    def clips_missing(self):
        """Clips handed in this (act) round whose frames have not all reached the host yet."""
        g = self.game
        out = []
        for p in g.submissions:
            key = g.assignment(p)["key"]
            have, n = self.frames_have(g.id, key)
            if n == 0 or have < n:
                out.append((p, key, have, n))
        return out

    def tick(self):
        with self.lock:
            if self.start_requested:
                self.start_game()
            if self.phase != "play":
                return
            if self.extra_requested:
                self.deadline = (max(self.deadline, self.clock()) if self.deadline else self.clock()) + self.extra_requested
                self.log(f"  +{self.extra_requested} s for this round")
                self.extra_requested = 0
                self.dirty = True
            late = self.deadline is not None and self.clock() >= self.deadline
            if not (self.game.all_in() or late or self.skip_requested):
                return
            # before the guessers start, make sure the clips they will watch have arrived
            if self.game.task == "act" and not self.skip_requested:
                missing = self.clips_missing()
                if missing:
                    if self.waiting_clips_since is None:
                        self.waiting_clips_since = self.clock()
                    if self.clock() - self.waiting_clips_since < CLIP_WAIT:
                        if self.clock() - self.last_clip_want > 2:
                            self.last_clip_want = self.clock()
                            for p, key, have, n in missing:
                                self.log(f"  waiting for {p}'s clip {key}: {have}/{n} frames, asking {p} to resend")
                                self.bus.publish(self.t["want"], {"game": self.game.id, "key": key, "from": "host"})
                        return
                    self.log("  !! gave up waiting for: " + ", ".join(f"{p}'s clip {k} ({h}/{n})" for p, k, h, n in missing))
            self.waiting_clips_since = None
            if (late or self.skip_requested) and not self.game.all_in():
                self.log(f"  {'time is up' if late else 'skipped'}: {', '.join(self.game.waiting_for())} did not send")
            self.skip_requested = False
            if self.game.end_round():
                self.phase, self.deadline = "reveal", None
                self.log("\n=== reveal ===")
                for s in self.game.summary():
                    self.log(f"  {s['owner']}: " + "  ->  ".join(s["words"]))
                self.log("\nEnter (or a player holding their button) starts a new game.")
            else:
                self.deadline = self._deadline()
                self._log_round()
            self.dirty = True

    def warnings(self):
        w = []
        t = self.clock()
        if any(t - seen < 30 for seen in self.other_hosts.values()):
            w.append("Two hosts are running on this team. Only one person may run host.py.")
        old = [n for n, i in self.present.items() if i.get("version") != VERSION]
        if old:
            w.append(f"{', '.join(old)} {'runs' if len(old) == 1 else 'run'} an older version: "
                     "copy the new charades.zip and restart player.py.")
        dups = [n for n, seen in self.dup_names.items() if t - seen < 60]
        if dups:
            w.append(f"Two Pis are using the name {', '.join(dups)}: restart one with a different --name.")
        return w

    def state(self):
        with self.lock:
            s = {"phase": self.phase, "team": self.team, "lobby": sorted(self.present), "sent_at": self.clock(),
                 "host_id": self.id, "version": VERSION, "warnings": self.warnings(),
                 "bots": sorted(n for n, i in self.present.items() if i.get("bot")),
                 "versions": {n: i.get("version") for n, i in self.present.items()}}
            if self.game:
                g = self.game
                s.update({"game": g.id, "players": g.players, "rounds": g.rounds, "narrator": g.players[0]})
                if self.phase == "play":
                    s.update({"round": g.round, "task": g.task, "assignments": g.assignments(),
                              "submitted": sorted(g.submissions), "waiting_for": g.waiting_for(),
                              "deadline": self.deadline})
                if self.phase == "reveal":
                    s.update({"chains": g.chains, "summary": g.summary()})
            return s

    def publish_state(self, force=False):
        with self.lock:
            if not (self.dirty or force):
                return
            self.dirty = False
            s = self.state()
        self.bus.publish(self.t["state"], s, retain=True)
        self.last_published = s


def read_keys(host):
    for line in sys.stdin:
        cmd = line.strip().lower()
        if cmd in ("q", "quit", "exit"):
            host.log("bye")
            host.bus.publish(host.t["state"], {"phase": "offline"}, retain=True)
            time.sleep(0.5)
            import os
            os._exit(0)
        with host.lock:
            if cmd in ("n", "next", "skip"):
                host.skip_requested = True
            elif cmd in ("t", "time", "+"):
                host.extra_requested += 60
            elif host.phase in ("lobby", "reveal") or cmd == "start":
                host.start_requested = True


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--team", default=DEFAULT_TEAM, help="must be the same on every Pi")
    ap.add_argument("--rounds", type=int, help="default: number of players, rounded up to even (3 players -> 4)")
    ap.add_argument("--act-seconds", type=int, default=180, help="time limit to act (0 = no limit)")
    ap.add_argument("--guess-seconds", type=int, default=180, help="time limit to guess (0 = no limit)")
    ap.add_argument("--prompts", help="a text file with one prompt per line, instead of the built-in list")
    ap.add_argument("--broker", default=None, help="MQTT broker host (default: the class broker)")
    ap.add_argument("--port", type=int, default=None)
    args = ap.parse_args()

    pool = None
    if args.prompts:
        pool = [ln.strip() for ln in open(args.prompts) if ln.strip() and not ln.startswith("#")]
    kw = {k: v for k, v in (("broker", args.broker), ("port", args.port)) if v}
    log = Log("host")
    bus = Bus("host", **kw)
    host = Host(bus, args.team, rounds=args.rounds, act_seconds=args.act_seconds,
                guess_seconds=args.guess_seconds, prompts=pool, log=log)
    host.attach()
    log(f"connecting to {bus.broker}...")
    bus.start()
    log(f"host v{VERSION} ready: team '{args.team}'. Waiting for players (start player.py on each Pi).")
    log("Enter = start   t + Enter = +60 s   n + Enter = skip to next round   q + Enter = quit")
    if log.path:
        log(f"(log: {log.path})\n")
    host.publish_state(force=True)
    threading.Thread(target=read_keys, args=(host,), daemon=True).start()
    last_beat = 0
    try:
        while True:
            host.tick()
            beat = time.time() - last_beat > 10                # heartbeat so players know the host is alive
            host.publish_state(force=beat)
            if beat:
                last_beat = time.time()
            time.sleep(0.25)
    except KeyboardInterrupt:
        bus.publish(host.t["state"], {"phase": "offline"}, retain=True)
        time.sleep(0.5)
        bus.stop()


if __name__ == "__main__":
    main()
