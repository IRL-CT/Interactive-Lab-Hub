"""
Telephone Charades: the rules, with no MQTT, camera or screen in it (so it can be tested anywhere).

Like Gartic Phone, but with acting instead of drawing. Every player starts a chain with a secret
prompt. Each round, every chain moves one player to the right, and the task alternates:

    round 0  ACT    the chain's owner acts out the prompt (the webcam records a short clip)
    round 1  GUESS  the next player watches that clip on their laptop and guesses (mic or typing)
    round 2  ACT    the next player acts out that guess
    round 3  GUESS  ... and so on, until the reveal shows how each prompt changed on the way

Everyone is busy every round, so a round ends when all players have handed something in
(or the host's timer runs out, and the missing ones are marked as skipped).
"""


class Game:
    def __init__(self, players, prompts, rounds, game_id):
        if len(players) < 2:
            raise ValueError("need at least 2 players")
        if len(prompts) < len(players):
            raise ValueError("need one prompt per player")
        self.players = list(players)
        self.n = len(self.players)
        self.rounds = rounds
        self.id = game_id
        self.round = 0
        self.chains = [{"owner": p, "steps": [{"kind": "prompt", "text": prompts[i]}]}
                       for i, p in enumerate(self.players)]
        self.submissions = {}                 # player -> submission, for the current round only

    # ------------------------------------------------------------------ who does what

    @staticmethod
    def task_for(r):
        return "act" if r % 2 == 0 else "guess"

    @property
    def task(self):
        return self.task_for(self.round)

    @property
    def finished(self):
        return self.round >= self.rounds

    def chain_for(self, player, r=None):
        r = self.round if r is None else r
        return (self.players.index(player) - r) % self.n

    def holder(self, chain, r=None):
        r = self.round if r is None else r
        return self.players[(chain + r) % self.n]

    @staticmethod
    def clip_key(chain, r):
        return f"c{chain}r{r}"

    def last_text(self, chain):
        """What the next actor must act: the latest guess, or the prompt if nobody guessed yet."""
        for step in reversed(self.chains[chain]["steps"]):
            if step["kind"] in ("prompt", "guess") and step.get("text"):
                return step["text"]
        return self.chains[chain]["steps"][0]["text"]

    def assignment(self, player, r=None):
        r = self.round if r is None else r
        c = self.chain_for(player, r)
        if self.task_for(r) == "act":
            return {"task": "act", "chain": c, "text": self.last_text(c), "key": self.clip_key(c, r)}
        prev = self.chains[c]["steps"][-1]
        return {"task": "guess", "chain": c, "clip": prev.get("clip"), "frames": prev.get("frames", 0),
                "from": prev.get("player")}

    def assignments(self):
        return {p: self.assignment(p) for p in self.players}

    # ------------------------------------------------------------------ handing things in

    def submit(self, player, round_, kind, text=None, frames=0):
        """Returns None if accepted, else why not."""
        if self.finished:
            return "the game is over"
        if player not in self.players:
            return f"{player} is not in this game"
        if round_ != self.round:
            return f"that was for round {round_}, we are in round {self.round}"
        if kind != self.task:
            return f"this round is '{self.task}', not '{kind}'"
        if player in self.submissions:
            return f"{player} already handed in this round"
        if kind == "guess" and not (text or "").strip():
            return "empty guess"
        if kind == "act" and frames <= 0:
            return "no frames in the clip"
        self.submissions[player] = {"text": (text or "").strip(), "frames": frames}
        return None

    def waiting_for(self):
        return [p for p in self.players if p not in self.submissions]

    def all_in(self):
        return not self.waiting_for()

    def end_round(self):
        """Write this round's submissions into the chains (skips for the missing) and move on."""
        r = self.round
        for p in self.players:
            c = self.chain_for(p, r)
            sub = self.submissions.get(p)
            if self.task_for(r) == "act":
                step = {"kind": "act", "player": p, "acting": self.last_text(c),
                        "clip": self.clip_key(c, r) if sub else None, "frames": sub["frames"] if sub else 0}
            else:
                step = {"kind": "guess", "player": p, "text": sub["text"] if sub else ""}
            if not sub:
                step["skipped"] = True
            self.chains[c]["steps"].append(step)
        self.submissions = {}
        self.round += 1
        return self.finished

    def summary(self):
        """One line per chain, for the terminal and the narrator: prompt -> ... -> final guess."""
        out = []
        for ch in self.chains:
            words = [ch["steps"][0]["text"]] + [s.get("text") or "(skipped)" for s in ch["steps"] if s["kind"] == "guess"]
            out.append({"owner": ch["owner"], "start": words[0], "end": words[-1], "words": words})
        return out
