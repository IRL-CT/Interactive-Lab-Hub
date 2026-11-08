"""
Telephone Charades: pretend players, so you can test a whole game with just ONE Pi.

A bot joins the lobby like a real player. When it has to act, it sends drawn frames of a stick
figure with a hangman version of its prompt ("r_d_n_ a h_r_e"), so you can still guess it.
When it has to guess, it picks a random guess. It answers after a few seconds.

    python bots.py --names Bella,Chen                 # two bots on the default team
    python bots.py --names Bella,Chen --team charades-arnav --delay 2
"""
import argparse
import pathlib
import random
import sys
import threading
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from common import DEFAULT_TEAM, PROMPTS, VERSION, Bus, b64, decode, now, topics  # noqa: E402
from hardware import draw_frame  # noqa: E402

SILLY = ["a confused penguin", "doing taxes", "an angry chef", "walking on the moon", "a sneezing giraffe",
         "dancing badly", "a very tired robot", "looking for keys"]


def hangman(text, seed):
    rng = random.Random(seed)
    return "".join(c if (not c.isalpha() or rng.random() < 0.55) else "_" for c in text)


class Bot:
    def __init__(self, name, team, bus, delay=(3, 7), frames=12, fps=5, log=print, rng=None):
        self.name, self.team, self.bus = name, team, bus
        self.t = topics(team)
        self.delay, self.n_frames, self.fps = delay, frames, fps
        self.log, self.rng = log, rng or random.Random()
        self.done = set()                       # (game, round) handled
        self.sent_clips = {}                    # (game, key) -> frames, to resend if someone missed them
        self.lock = threading.Lock()

    def attach(self):
        self.bus.will(f"{self.t['players']}/{self.name}", b"", retain=True)
        self.bus.subscribe(self.t["state"], self.on_state)
        self.bus.subscribe(self.t["want"], self.on_want)
        self.bus.on_connected(self.announce)

    def announce(self):
        self.bus.publish(f"{self.t['players']}/{self.name}", {"name": self.name, "since": now(), "bot": True,
                                                              "version": VERSION, "uid": f"bot-{self.name}"}, retain=True)

    def on_want(self, topic, payload):
        msg = decode(payload) or {}
        frames = self.sent_clips.get((msg.get("game"), msg.get("key")))
        for i, jpg in enumerate(frames or []):
            self.bus.publish(f"{self.t['clip']}/{msg['game']}/{msg['key']}",
                             {"i": i, "n": len(frames), "jpg": jpg, "actor": self.name, "fps": self.fps, "resent": True})

    def leave(self):
        self.bus.publish(f"{self.t['players']}/{self.name}", b"", retain=True)

    def on_state(self, topic, payload):
        s = decode(payload) or {}
        if s.get("phase") != "play":
            return
        mine = (s.get("assignments") or {}).get(self.name)
        rk = (s.get("game"), s.get("round"))
        with self.lock:
            if not mine or rk in self.done or self.name in (s.get("submitted") or []):
                return
            self.done.add(rk)
        wait = self.rng.uniform(*self.delay)
        threading.Timer(wait, self.answer, args=(rk, mine)).start()

    def answer(self, rk, mine):
        game, rnd = rk
        if mine["task"] == "act":
            caption = f"{self.name} acts: {hangman(mine['text'], game + mine['key'])}"
            n = self.n_frames
            frames = [b64(draw_frame(i, n, caption)) for i in range(n)]
            self.sent_clips[(game, mine["key"])] = frames
            for i, jpg in enumerate(frames):
                self.bus.publish(f"{self.t['clip']}/{game}/{mine['key']}",
                                 {"i": i, "n": n, "jpg": jpg, "actor": self.name, "fps": self.fps})
            self.bus.publish(self.t["submit"], {"game": game, "round": rnd, "player": self.name, "kind": "act", "frames": n})
            self.log(f"[{self.name}] acted '{mine['text']}' ({n} frames)")
        else:
            guess = self.rng.choice(SILLY + PROMPTS)
            self.bus.publish(self.t["submit"], {"game": game, "round": rnd, "player": self.name, "kind": "guess", "text": guess})
            self.log(f"[{self.name}] guessed '{guess}'")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--names", default="Bella,Chen", help="comma-separated bot names")
    ap.add_argument("--team", default=DEFAULT_TEAM)
    ap.add_argument("--delay", type=float, default=5, help="about how many seconds a bot takes to answer")
    ap.add_argument("--broker", default=None)
    ap.add_argument("--port", type=int, default=None)
    args = ap.parse_args()
    kw = {k: v for k, v in (("broker", args.broker), ("port", args.port)) if v}
    bots = []
    for name in [n.strip() for n in args.names.split(",") if n.strip()]:
        bus = Bus(f"bot-{name}", **kw)
        bot = Bot(name, args.team, bus, delay=(max(0.5, args.delay * 0.6), args.delay * 1.4))
        bot.attach()
        bus.start()
        bots.append(bot)
        print(f"bot {name} joined team '{args.team}'", flush=True)
    print("Ctrl-C to remove the bots.", flush=True)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        for b in bots:
            b.leave()
        time.sleep(0.5)


if __name__ == "__main__":
    main()
