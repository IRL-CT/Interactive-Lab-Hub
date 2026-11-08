"""
Tests for Telephone Charades. No Pi, camera or network needed:

    python -m pytest charades/tests -q        (or: python charades/tests/test_charades.py)

The first half tests the rules. The second half plays whole games: a host and three players
(with a drawn "camera" and a pretend mic) over an in-memory broker, and a host + 1 player + 2 bots.
"""
import json
import pathlib
import queue
import sys
import threading
import time
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import hardware  # noqa: E402
from bots import Bot, hangman  # noqa: E402
from common import VERSION, default_rounds, topic_matches  # noqa: E402
from fakebus import FakeBroker, FakeBus  # noqa: E402
from game import Game  # noqa: E402
from host import Host  # noqa: E402
from player import Player  # noqa: E402
from web import WebServer  # noqa: E402

PROMPTS = ["swimming", "riding a horse", "a robot dancing"]


# ============================================================================ the rules


def test_rotation_and_alternating_tasks():
    g = Game(["A", "B", "C"], PROMPTS, 4, "g1")
    assert g.assignment("A") == {"task": "act", "chain": 0, "text": "swimming", "key": "c0r0"}
    assert g.assignment("B")["text"] == "riding a horse"
    # round 1: everyone guesses the clip from the player on their left
    for p, sub in (("A", 5), ("B", 6), ("C", 7)):
        assert g.submit(p, 0, "act", frames=sub) is None
    assert g.all_in()
    g.end_round()
    assert g.task == "guess"
    a = g.assignment("B")
    assert (a["chain"], a["clip"], a["from"], a["frames"]) == (0, "c0r0", "A", 5)
    assert g.assignment("A")["from"] == "C"
    for p, text in (("A", "drowning"), ("B", "doing the crawl"), ("C", "a horse race")):
        g.submit(p, 1, "guess", text=text)
    g.end_round()
    # round 2: the third player acts the second player's guess
    a = g.assignment("C")
    assert (a["task"], a["chain"], a["text"]) == ("act", 0, "doing the crawl")
    # every player handles every chain at most once in the first n rounds
    seen = {p: {g.chain_for(p, r) for r in range(3)} for p in g.players}
    assert all(len(v) == 3 for v in seen.values())


def test_submit_rules():
    g = Game(["A", "B"], PROMPTS, 2, "g1")
    assert "round" in g.submit("A", 1, "act", frames=3)
    assert "not 'guess'" in g.submit("A", 0, "guess", text="x")
    assert "no frames" in g.submit("A", 0, "act", frames=0)
    assert "not in this game" in g.submit("Z", 0, "act", frames=3)
    assert g.submit("A", 0, "act", frames=3) is None
    assert "already" in g.submit("A", 0, "act", frames=3)
    assert g.waiting_for() == ["B"]


def test_skips_carry_the_last_words_forward():
    g = Game(["A", "B", "C"], PROMPTS, 4, "g1")
    g.submit("A", 0, "act", frames=4)
    g.end_round()                                     # B and C did not act
    assert g.assignment("C")["clip"] is None          # C must guess B's missing clip
    g.submit("B", 1, "guess", text="")                # empty guess is refused
    g.end_round()
    a = g.assignment("C", 2)                          # C acts chain 0, whose guess was skipped
    assert a["text"] == "swimming"
    steps = g.chains[1]["steps"]
    assert steps[1]["skipped"] and steps[1]["clip"] is None
    g.end_round()
    assert not g.finished
    g.end_round()
    assert g.finished
    assert g.summary()[0]["words"] == ["swimming", "(skipped)", "(skipped)"]


def test_default_rounds_end_on_a_guess():
    assert [default_rounds(n) for n in (2, 3, 4, 5)] == [2, 4, 4, 6]
    for n in (2, 3, 4, 5):
        assert Game.task_for(default_rounds(n) - 1) == "guess"


def test_topic_matching_and_hangman():
    assert topic_matches("IDD/t/charades/clip/#", "IDD/t/charades/clip/g1/c0r0")
    assert topic_matches("IDD/t/charades/players/+", "IDD/t/charades/players/Arnav")
    assert not topic_matches("IDD/t/charades/players/+", "IDD/t/charades/players/a/b")
    h = hangman("riding a horse", "x")
    assert len(h) == len("riding a horse") and h.count(" ") == 2


def test_pitft_text_fits():
    from PIL import Image, ImageDraw
    d = ImageDraw.Draw(Image.new("RGB", (240, 135)))
    for text in ["swimming", "a magician pulling a rabbit out of a hat", "waiting for Bella, Chen, Dominique"]:
        font, lines = hardware.fit_text(d, text, 228, 70)
        assert len(lines) * font.size * 1.15 <= 70 + 1
        assert all(d.textlength(ln, font=font) <= 228 for ln in lines)


# ============================================================================ whole games


class ScriptedButton:
    kind = "test"

    def __init__(self):
        self.q = queue.Queue()

    def press(self, kind):
        self.q.put(kind)

    def wait(self, timeout=None):
        try:
            return self.q.get(timeout=timeout or 0.01)
        except queue.Empty:
            return None

    def hints(self):
        return ("tap", "hold")

    def led(self, b):
        pass

    def pulse(self):
        pass


class QuietScreen(hardware.TerminalScreen):
    def show(self, top, body, bottom="", mood="info"):
        self.last = (top, body, bottom)


def wait_for(cond, timeout=10, step=0.02):
    end = time.time() + timeout
    while time.time() < end:
        if cond():
            return True
        time.sleep(step)
    raise AssertionError("timed out waiting")


class Table:
    """A host and some players around one in-memory broker."""

    def __init__(self, names, bots=(), act_seconds=0, guess_seconds=0):
        self.broker = FakeBroker()
        self.host = Host(FakeBus("host", self.broker), "t", act_seconds=act_seconds,
                         guess_seconds=guess_seconds, prompts=PROMPTS, log=lambda *a: None)
        self.host.attach()
        self.host.bus.start()
        self.players = {}
        for i, n in enumerate(names):
            p = Player(n, "t", FakeBus(n, self.broker), ScriptedButton(), QuietScreen(), hardware.Voice(False),
                       hardware.Sounds(False), hardware.FakeCamera(fast=True, quiet=True),
                       hardware.FakeMic([f"{n.lower()} guess {k}" for k in range(5)], fast=True, quiet=True),
                       record_seconds=1, fps=4, log=lambda *a: None)
            p.attach()
            p.bus.start()
            threading.Thread(target=p.run, daemon=True).start()
            self.players[n] = p
        self.bots = []
        for n in bots:
            b = Bot(n, "t", FakeBus(n, self.broker), delay=(0.01, 0.05), frames=6, log=lambda *a: None)
            b.attach()
            b.bus.start()
            self.bots.append(b)
        self.running = True
        threading.Thread(target=self._host_loop, daemon=True).start()

    def _host_loop(self):
        while self.running:
            self.host.tick()
            self.host.publish_state()
            time.sleep(0.02)

    def phase(self):
        return self.host.state()["phase"]

    def play_round(self, typed=()):
        g = self.host.game
        r = g.round
        for name, p in self.players.items():
            wait_for(lambda: p.snapshot()[3] == (g.id, r))       # the player has seen this round
            task = g.assignment(name)["task"]
            if task == "act":
                p.button.press("tap")
                wait_for(lambda: len(p.take) > 0)
                p.button.press("hold")
            elif name in typed:
                p.web_action("guess", f"typed by {name}")
            else:
                p.button.press("tap")
                wait_for(lambda: p.guess)
                p.button.press("hold")
        wait_for(lambda: g.round > r or g.finished)

    def stop(self):
        self.running = False


def test_full_game_three_players():
    t = Table(["Arnav", "Bella", "Chen"])
    wait_for(lambda: len(t.host.state()["lobby"]) == 3)
    wait_for(lambda: t.players["Arnav"].screen_content(*t.players["Arnav"].snapshot()[:3], False)[:2]
             == ("LOBBY", "Arnav, Bella, Chen"))
    t.players["Arnav"].button.press("hold")                      # holding in the lobby starts the game
    wait_for(lambda: t.phase() == "play")
    g = t.host.game
    assert g.rounds == 4 and g.players == ["Arnav", "Bella", "Chen"]

    # while Bella and Chen have not acted, Arnav's screen says who we are waiting for
    a = t.players["Arnav"]
    wait_for(lambda: a.snapshot()[3] == (g.id, 0))
    a.button.press("tap")
    wait_for(lambda: len(a.take) == 4)
    a.button.press("hold")
    wait_for(lambda: "Arnav" in t.host.state()["submitted"])
    wait_for(lambda: "waiting for Bella, Chen" in a.screen.last[1])
    for n in ("Bella", "Chen"):
        p = t.players[n]
        p.button.press("tap")
        wait_for(lambda: len(p.take) == 4)
        p.button.press("hold")
    wait_for(lambda: g.round == 1)

    # guessers receive the right clip, frame by frame
    b = t.players["Bella"]
    clip = g.assignment("Bella")["clip"]
    wait_for(lambda: b.clip_complete(g.id, clip))
    assert b.clip_view(clip)["actor"] == "Arnav"

    t.play_round(typed=("Chen",))                                # Chen types, the others speak
    t.play_round()
    t.play_round()
    wait_for(lambda: t.phase() == "reveal")
    s = t.host.state()
    assert len(s["chains"]) == 3
    for ch in s["chains"]:
        kinds = [st["kind"] for st in ch["steps"]]
        assert kinds == ["prompt", "act", "guess", "act", "guess"]
        assert all(not st.get("skipped") for st in ch["steps"])
    assert s["chains"][1]["steps"][2] == {"kind": "guess", "player": "Chen", "text": "typed by Chen"}
    # every Pi has every clip for the reveal
    keys = [st["clip"] for ch in s["chains"] for st in ch["steps"] if st.get("clip")]
    for p in t.players.values():
        wait_for(lambda: all(p.clip_complete(g.id, k) for k in keys))
        wait_for(lambda: p.screen_content(*p.snapshot()[:3], False)[0] == "GAME OVER")
    # holding again starts a new game
    t.players["Chen"].button.press("hold")
    wait_for(lambda: t.phase() == "play" and t.host.game is not g)
    t.stop()


def test_one_player_and_two_bots_and_the_laptop_page():
    t = Table(["Arnav"], bots=("Bella", "Chen"))
    wait_for(lambda: len(t.host.state()["lobby"]) == 3)
    me = t.players["Arnav"]
    web = WebServer(me, port=0, host="127.0.0.1")
    port = web.start()

    def get(path):
        return json.loads(urllib.request.urlopen(f"http://127.0.0.1:{port}{path}", timeout=5).read())

    def post(body):
        req = urllib.request.Request(f"http://127.0.0.1:{port}/api/action", json.dumps(body).encode(),
                                     {"Content-Type": "application/json"})
        return json.loads(urllib.request.urlopen(req, timeout=5).read())

    html = urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=5).read().decode()
    assert "Telephone Charades" in html
    assert get("/api/state")["phase"] == "lobby"
    post({"action": "hold"})                                     # the page's Start button
    wait_for(lambda: t.phase() == "play")
    g = t.host.game
    while not g.finished:
        r = g.round
        wait_for(lambda: me.snapshot()[3] == (g.id, r))
        v = get("/api/state")
        assert v["in_game"] and v["assignment"]["task"] == g.task
        assert "assignments" not in v                            # the page never sees the others' prompts
        if g.task == "act":
            post({"action": "tap"})
            wait_for(lambda: get("/api/state")["take_frames"] == 4)
            assert len(get("/api/clip?key=take")["frames"]) == 4
            post({"action": "hold"})
        else:
            key = v["assignment"]["clip"]
            wait_for(lambda: get(f"/api/clip?key={key}")["n"] == 6 and len(get(f"/api/clip?key={key}")["frames"]) == 6)
            post({"action": "guess", "text": "a sneezing giraffe"})
        wait_for(lambda: g.round > r or g.finished)
    wait_for(lambda: get("/api/state")["phase"] == "reveal")
    v = get("/api/state")
    assert len(v["chains"]) == 3 and len(v["summary"]) == 3
    web.stop()
    t.stop()


def test_timer_skips_a_player_who_never_answers():
    t = Table(["Arnav", "Bella"], act_seconds=1, guess_seconds=1)
    wait_for(lambda: len(t.host.state()["lobby"]) == 2)
    t.host.start_requested = True
    wait_for(lambda: t.phase() == "play")
    g = t.host.game
    a = t.players["Arnav"]
    wait_for(lambda: a.snapshot()[3] == (g.id, 0))
    a.button.press("tap")
    wait_for(lambda: len(a.take) > 0)
    a.button.press("hold")                                       # Bella never acts
    wait_for(lambda: g.round == 1, timeout=5)
    assert g.chains[1]["steps"][1]["skipped"]
    assert g.assignment("Arnav")["clip"] is None                 # Arnav must guess Bella's missing clip
    t.stop()


def test_redo_take_gets_a_new_id_and_live_frames_flow():
    """Regression: a redo kept the name 'take' and the same frame count, so the laptop page kept showing
    the first take. Every take now has its own id, and the webcam's newest frame is served while recording."""
    t = Table(["Arnav", "Bella"])
    wait_for(lambda: len(t.host.state()["lobby"]) == 2)
    t.host.start_requested = True
    wait_for(lambda: t.phase() == "play")
    a = t.players["Arnav"]
    wait_for(lambda: a.snapshot()[3] == (t.host.game.id, 0))
    a.button.press("tap")
    wait_for(lambda: a.take_id == 1 and not a.busy)
    first = a.clip_view("take")
    a.button.press("tap")                                        # redo
    wait_for(lambda: a.take_id == 2 and not a.busy)
    second = a.clip_view("take")
    assert (first["take_id"], second["take_id"]) == (1, 2)
    assert first["frames"] != second["frames"]                   # the fake camera numbers its takes
    assert a.view()["take_id"] == 2
    assert a.live is None                                        # no live frame once recording is over
    web = WebServer(a, port=0, host="127.0.0.1")
    port = web.start()
    assert urllib.request.urlopen(f"http://127.0.0.1:{port}/api/live", timeout=5).status == 204
    a.live = hardware.draw_frame(0, 1, "live")
    r = urllib.request.urlopen(f"http://127.0.0.1:{port}/api/live", timeout=5)
    assert r.status == 200 and r.headers["Content-Type"] == "image/jpeg" and r.read()[:2] == b"\xff\xd8"
    a.live = None
    a.button.press("hold")
    wait_for(lambda: "Arnav" in t.host.state()["submitted"])
    key = t.host.game.assignment("Arnav")["key"]
    wait_for(lambda: t.players["Bella"].clip_complete(t.host.game.id, key))
    assert t.players["Bella"].clip_view(key)["frames"] == second["frames"]   # the redo is what was sent
    web.stop()
    t.stop()


def test_live_frames_during_countdown_and_recording():
    cam = hardware.FakeCamera(fast=True, quiet=True)
    got = []
    cam.warm(1.0, on_frame=got.append)
    n_warm = len(got)
    frames = cam.record(1, 4, on_frame=got.append)
    assert n_warm >= 1 and len(got) == n_warm + len(frames) == n_warm + 4


def act_all(t, names):
    g = t.host.game
    for n in names:
        p = t.players[n]
        wait_for(lambda: p.snapshot()[3] == (g.id, g.round))
        p.button.press("tap")
        wait_for(lambda: len(p.take) > 0 and not p.busy)
        p.button.press("hold")


def test_lost_frames_are_resent_by_the_actor_before_guessing_starts():
    """A frame lost on the network (the host never gets it either) used to leave a clip incomplete for good.
    Now the host waits for every clip to be complete, asks the actor, and the actor's Pi resends it."""
    t = Table(["Arnav", "Bella", "Chen"])
    lost = set()

    def flaky(topic, payload):                       # lose frame 2 of every clip, the first time it is sent
        if "/clip/" in topic and b'"i": 2,' in payload and b'"resent"' not in payload and topic not in lost:
            lost.add(topic)
            return True
        return False
    t.broker.lose = flaky
    wait_for(lambda: len(t.host.state()["lobby"]) == 3)
    t.host.start_requested = True
    wait_for(lambda: t.phase() == "play")
    g = t.host.game
    act_all(t, ["Arnav", "Bella", "Chen"])
    wait_for(lambda: g.round == 1, timeout=10)
    assert len(lost) == 3                            # every clip really lost a frame
    for n, p in t.players.items():
        key = g.assignment(n)["clip"]
        wait_for(lambda: p.clip_complete(g.id, key), timeout=10)
    t.stop()


def test_duplicate_names_and_two_hosts_and_old_versions_are_reported():
    t = Table(["Arnav", "Bella"])
    wait_for(lambda: len(t.host.state()["lobby"]) == 2)
    # a second Pi starts with the name Arnav
    twin = Player("Arnav", "t", FakeBus("Arnav-2", t.broker), ScriptedButton(), QuietScreen(), hardware.Voice(False),
                  hardware.Sounds(False), hardware.FakeCamera(fast=True, quiet=True), hardware.FakeMic(fast=True, quiet=True),
                  log=lambda *a: None)
    time.sleep(0.05)
    twin.started_at = time.time()
    twin.attach()
    twin.bus.start()
    wait_for(lambda: any("Two Pis are using the name Arnav" in w for w in t.host.state()["warnings"]))
    wait_for(lambda: any("also called 'Arnav'" in w for w in t.players["Arnav"].view()["warnings"]))
    # a player on an old version
    t.broker.publish("IDD/t/charades/players/Old", b'{"name": "Old", "since": 1, "version": "1.0"}', retain=True)
    wait_for(lambda: any("Old runs an older version" in w for w in t.host.state()["warnings"]))
    # a second host on the same team
    other = Host(FakeBus("host2", t.broker), "t", log=lambda *a: None)
    other.attach()
    other.bus.start()
    other.publish_state(force=True)
    wait_for(lambda: any("Two hosts" in w for w in t.host.state()["warnings"]))
    t.host.publish_state(force=True)
    wait_for(lambda: any("Two hosts" in w for w in t.players["Bella"].view()["warnings"]))
    t.stop()


def test_host_can_add_time():
    clock = [1000.0]
    t = Table(["Arnav", "Bella"], act_seconds=60)
    t.host.clock = lambda: clock[0]
    wait_for(lambda: len(t.host.state()["lobby"]) == 2)
    t.host.start_requested = True
    wait_for(lambda: t.phase() == "play")
    d0 = t.host.deadline
    t.host.extra_requested = 60
    wait_for(lambda: t.host.deadline == d0 + 60)
    assert t.players["Arnav"].view()["version"] == VERSION
    t.stop()


def test_player_that_crashes_leaves_the_lobby():
    t = Table(["Arnav", "Bella"])
    wait_for(lambda: len(t.host.state()["lobby"]) == 2)
    t.broker.drop(t.players["Bella"].bus)                        # Bella's Pi loses power: the will fires
    wait_for(lambda: t.host.state()["lobby"] == ["Arnav"])
    t.stop()


def test_late_pi_gets_missing_clip_from_host():
    t = Table(["Arnav", "Bella"])
    wait_for(lambda: len(t.host.state()["lobby"]) == 2)
    t.host.start_requested = True
    wait_for(lambda: t.phase() == "play")
    g = t.host.game
    for p in t.players.values():
        wait_for(lambda: p.snapshot()[3] == (g.id, 0))
        p.button.press("tap")
        wait_for(lambda: len(p.take) > 0)
        p.button.press("hold")
    wait_for(lambda: g.round == 1)
    b = t.players["Bella"]
    key = g.assignment("Bella")["clip"]
    wait_for(lambda: b.clip_complete(g.id, key))
    with b.lock:
        b.clips.clear()                                          # as if Bella's Pi had restarted
    b.round_started = 0
    b.last_want = 0
    wait_for(lambda: b.clip_complete(g.id, key), timeout=10)
    t.stop()


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            t0 = time.time()
            fn()
            print(f"ok  {name}  ({time.time() - t0:.1f} s)")
