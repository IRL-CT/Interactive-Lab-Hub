**Part B**
📸 Include: Screenshot of grid + photo of your Pi setup

<img width="1170" height="1530" alt="Screenshot 2026-11-08 at 3 49 08 PM" src="https://github.com/user-attachments/assets/c7535e78-a696-4d60-b85d-f7adf70b1295" />

<img width="1190" height="1580" alt="Screenshot 2026-11-08 at 3 49 16 PM" src="https://github.com/user-attachments/assets/06185c84-5477-4703-9f80-90634e16d616" />

Deliverables

**1. Project Description**

**Telephone Charades**

Group members: Jessica Chon (jc3932), Shifeng Hong (sh2769), Arnav Whig (aww96)

Link to project: https://github.com/chonjessica23/Interactive-Lab-Hub/tree/Fall2026/Lab%206/charades 

Our project is a remote, interactive charades game that lets friends play and socialize even when they can’t be in the same room. It works like a game of telephone, but with acting. Each player starts with a secret prompt, acts it out in front of a camera, and passes the clip to another player to guess. In the next round, someone acts out that guess. At the end, everyone can see how the original prompts changed as they passed from person to person. The fun comes from seeing how differently people interpret the same gestures and how far a guess can drift from the original prompt.

In our three-player setup, each player uses a Raspberry Pi to record and submit their performance. They tap a physical button to start a short recording and hold it to send the clip. The Pi sends the camera frames over MQTT, and the next player watches the clip on a web page and enters a guess. Everyone gets something to do each round, and the game moves on once everyone has submitted or the round timer runs out.

Parts needed for three players
	• Three Raspberry Pis with power supplies and a network connection
	• Three USB webcams to record the performances
	• One Qwiic Button with a Qwiic cable per Pi, or the buttons on a Mini PiTFT
	• A laptop with a web browser for each player to watch clips and type guesses
	• Optional speakers for countdown beeps and voice prompts
	• Optional USB microphones for spoken guesses

Since the theme of this week was communication, we wanted to really focus and iterate on that concept in a playful manner. Below are the initial sketches detailing the user flow. 

<img width="1856" height="1466" alt="Screenshot 2026-11-08 at 3 53 11 PM" src="https://github.com/user-attachments/assets/78c9365b-d5c4-438d-bb71-bf147329d54b" />

<img width="854" height="1414" alt="Screenshot 2026-11-08 at 3 53 07 PM" src="https://github.com/user-attachments/assets/83de243a-e74e-4614-b1bc-8d054e89f5f6" />


**2. Architecture Diagram**

<img width="6555" height="2446" alt="Lab 6 architecture" src="https://github.com/user-attachments/assets/a474674c-ecd9-4aaa-9dbe-2a8dfe91eba0" />


**3. Build Documentation**

### The three Pis

Every Pi runs the same code ([`charades/`](charades/)) as one player. One of them, Arnav's, also runs the host program that keeps track of the rounds; no extra device is needed.

<img width="1862" height="1400" alt="image" src="https://github.com/user-attachments/assets/093e8448-a1d9-49b7-9de4-d3d886e3e59d" />


**What each part does in the game:**

- **Webcam:** records the acting: 4 seconds at 5 frames per second, each frame shrunk to 320×240 and compressed to a JPEG of about 7 KB.
- **Qwiic Button:** the only control you need. Tap to record a take or speak a guess; hold for a second to send it, or to start a game from the lobby. Its LED pulses when it's your turn.
- **Mic:** speak your guess; the Pi turns it into text with faster-whisper (`tiny.en`, from Lab 3), on the Pi itself. Guesses can also be typed on the laptop.
- **Mini PiTFT:** shows your secret prompt, the 3-2-1 countdown, and who the game is still waiting for.
- **Speaker:** beeps for the countdown, "your turn to act / guess" (Piper voice, from Lab 3), and one Pi reads the reveal aloud.
- **Laptop page:** each Pi serves its own player's page on port 8000, where you watch the clip you have to guess, and see the reveal at the end.

### MQTT topics

Everything lives in our team's space on the class broker, `IDD/charades-arnav/charades/...`:

| Topic | Retained | Sent by | Message |
|---|---|---|---|
| `.../players/<name>` | yes | each player | "I'm here": `{"name": "Arnav", "since": 1731090215.2, "mic": true}`. Emptied when the player leaves; a **last will** empties it if a Pi loses power. |
| `.../state` | yes | host | The whole game: phase, round, who acts or guesses what, who has sent, the deadline, and at the end the reveal. Retained, so a Pi that (re)joins gets the current state at once. |
| `.../submit` | | players | Hand in this round's work: `{"game": "g191502", "round": 1, "player": "Arnav", "kind": "guess", "text": "riding a horse"}` |
| `.../clip/<game>/<key>` | | the actor | One JPEG frame per message: `{"i": 7, "n": 20, "jpg": "/9j/4AAQ...", "actor": "Arnav", "fps": 5}`. `key` names the chain and round, e.g. `c0r2`. |
| `.../control` | | players | `{"cmd": "start", "from": "Arnav"}`: someone held their button in the lobby. |
| `.../want` | | a Pi that restarted | `{"game": "g191502", "key": "c0r2", "from": "Arnav"}`: "I missed this clip". The host keeps a copy of every clip and sends it again. |

A shortened `state` message during a guess round:

```json
{
  "phase": "play", "game": "g191502", "round": 1, "rounds": 4, "task": "guess",
  "players": ["Arnav", "TEAMMATE_2", "TEAMMATE_3"],
  "assignments": {
    "TEAMMATE_2": {"task": "guess", "chain": 0, "clip": "c0r0", "frames": 20, "from": "Arnav"}
  },
  "submitted": ["TEAMMATE_3"],
  "waiting_for": ["Arnav", "TEAMMATE_2"],
  "deadline": 1731090395.4
}
```

### Code snippets

**1. The rules: who does what each round** ([`game.py`](charades/game.py))

```python
def task_for(r):
    return "act" if r % 2 == 0 else "guess"

def chain_for(self, player, r=None):
    r = self.round if r is None else r
    return (self.players.index(player) - r) % self.n
```

This is the whole "telephone" idea in two functions. Every player starts one chain with a secret prompt. Each round, every chain moves one player along (`index - round`, wrapped around), and the task alternates between acting and guessing. Everyone is busy every round, and with 3 players nobody sees the same chain twice until the last round, when you guess what *your own* prompt turned into.

**2. Saying "I'm here" in a way that survives crashes** ([`player.py`](charades/player.py))

```python
def attach(self):
    self.bus.will(self.presence, b"", retain=True)   # if this Pi dies, the broker says we left
    self.bus.subscribe(self.t["state"], self.on_state)
    self.bus.subscribe(self.t["clip"] + "/#", self.on_clip)
    self.bus.on_connected(self.announce)
```

The lobby is built from retained messages, one per player. The **last will** is a message the broker sends on the player's behalf if the connection drops without a goodbye, so a Pi that loses power disappears from the lobby by itself. `on_connected` re-announces the player after every reconnect, so a Wi-Fi hiccup doesn't drop anyone from the game.

**3. Sending a clip through MQTT, one frame at a time** ([`player.py`](charades/player.py))

```python
for i, jpg in enumerate(frames):
    self.bus.publish(f"{self.t['clip']}/{game}/{key}",
                     {"i": i, "n": n, "jpg": jpg, "actor": self.name, "fps": self.fps})
self.bus.publish(self.t["submit"],
                 {"game": game, "round": rnd, "player": self.name, "kind": "act", "frames": n})
```

MQTT is made for small messages, so instead of one ~150 KB video, a clip is sent as about 20 small JPEG messages (base64, ~10 KB each). Each frame says its number (`i`) and the total (`n`), so the guesser's Pi knows when it has the whole clip, and the laptop page shows "receiving the clip… 12/20" until it does. The take is only published when you **send** it, so retakes stay on your own Pi.

**4. The host moves the game on** ([`host.py`](charades/host.py))

```python
late = self.deadline is not None and self.clock() >= self.deadline
if self.game.all_in() or late or self.skip_requested:
    if self.game.end_round():
        self.phase, self.deadline = "reveal", None
    else:
        self.deadline = self._deadline()
    self.dirty = True          # -> publish the new state (retained)
```

A round ends as soon as everyone has sent their clip or guess, or when the timer runs out (2 minutes to act, 90 seconds to guess). Anyone missing is marked as skipped, and the next player acts the last words that were actually said. The host never touches a camera or a screen; it only does the bookkeeping and publishes one `state` message that every Pi reacts to.

**5. Speaking a guess** ([`hardware.py`](charades/hardware.py))

```python
cmd = ["arecord", "-q", "-D", self.device, "-f", "S16_LE", "-r", "16000", "-c", "1",
       "-d", str(seconds), path]
subprocess.run(cmd, check=True, timeout=seconds + 5)
segments, _ = self.model.transcribe(path, beam_size=1, language="en", vad_filter=True)
text = " ".join(s.text.strip() for s in segments).strip()
```

A tap records 4 seconds from the mic, and faster-whisper turns it into text **on the Pi**, so only the words, not the audio, go over the network. The model loads in the background when `player.py` starts, so it's ready by the time you guess. `vad_filter` skips the silence, which helps stop the model from inventing words when nobody spoke. The text shows on the PiTFT and the laptop, where you can correct it before sending.

**6. The waiting screen** ([`player.py`](charades/player.py))

```python
if handed:
    waiting = s.get("waiting_for") or []
    body = ("waiting for " + ", ".join(waiting)) if waiting else "everyone's in!"
    return f"SENT ✓{clock}", body, "next round soon", "wait"
```

After you send, your PiTFT shows who the game is still waiting for, with the time left, e.g. **SENT ✓ 1:05 / waiting for TEAMMATE_2, TEAMMATE_3**. It updates by itself each time the host's `state` message changes.

**7. Recovering a missed clip** ([`host.py`](charades/host.py))

```python
def on_want(self, topic, payload):
    """A Pi that restarted asks for a clip it missed: send the copy the host kept."""
    msg = decode(payload) or {}
    ...
    for i, jpg in frames:
        self.bus.publish(f"{self.t['clip']}/{msg['game']}/{msg['key']}",
                         {"i": i, "n": n, "jpg": jpg, "actor": actor, "resent": True})
```

Clip frames aren't retained (a retained topic only keeps its last message), so a Pi that restarts mid-game would miss them. The host subscribes to every clip and keeps a copy, and a Pi that is missing one asks on `want` and gets it again.

### Running it

On every Pi (once): install with `pip install -r charades/requirements-charades.txt` and check the parts with `python charades/check.py`. To play: the host runs `python charades/host.py`, and every player runs `python charades/player.py --name <Name>` and opens the address it prints on their laptop. Full steps are in [`charades/README.md`](charades/README.md).

**4. User Testing**

First, we ran a few rounds of testing amongst ourselves to make sure the experience was smooth enough to move forward with non-team member testing. Initially, there was no live camera feed of the recording session and we agreed that adding that visual feedback would be helpful, so users could be properly positioned in frame. 

<img width="1888" height="1652" alt="Screenshot 2026-11-08 at 3 09 30 PM" src="https://github.com/user-attachments/assets/eeff6556-7f78-4acd-b133-f058749f8ea9" />

After we made some adjustments, we found 3 non-team members in the Tata master’s studio to user test. We received the following comments:

* The instructions were clear, the layout was intuitive and clear also. IT “made sense the way it was”
* All players said the interaction was more fun than they initially thought it’d be.  They appreciated being able to see all the clips and the progression of the tasks all at once in the end
* The camera quality wasn’t that strong and a bit laggy, so it’d be nice to have a smoother video feedback.
* It’d help to have more than 4 seconds to act out a seen
* They thought more rounds/opportunities for engagement would be nice since they wanted to keep playing. This led to a suggestion that it could later change so that players actions are streamed live and have to take turns guessing as many tasks in real-time as possible within 60 seconds.

We weren't able to do anything about the camera quality or feed but we did extend the recording session to 10 seconds. We did another round of user testing and were told that the extended time was much more helpful.  

**User testing videos:**

https://drive.google.com/file/d/16iZUg-9qkidZwZ3pFXzR4GNiiD_xoyOy/view?usp=drive_link
https://drive.google.com/file/d/1JBaXRVHbeEGvIPNhtnrFbn_-_RuEaRo3/view?usp=drive_link
https://drive.google.com/file/d/1XrJAe2J9sn0jBcxdHJswXT2f6j5UwFbc/view?usp=drive_link


**5. Reflection**

The communication between the Pis worked surprisingly smoothly. Most of the issues came from the game’s interaction flow. Testing with multiple players helped us notice problems we might have otherwise missed, since everyone had different setups, settings, and ways of interacting with the game. However, this also made troubleshooting more tedious. We had to figure out whether an issue came from someone’s device, their actions, or the game logic. Fixes also took longer to test because we needed everyone to repeat the interaction, and a change that worked for one player could create problems for another.
The camera captured each player’s performance, and the button controlled when to record and submit it. Each Pi processed these inputs locally, then sent the recorded frames and submission messages through MQTT so the other devices could receive them. This connected each player’s physical actions to the shared game.

We wanted to experiment more with rounds and points, but our access to Pis and available players limited how much we could test. If we revisited the project, we would develop those game mechanics further and test with more players to see how the experience changes as the group grows.
Computation was divided between the players’ Pis, the game host, and the laptop browsers. Each Pi handled its own camera, button inputs, and web page server, keeping device interactions close to the hardware. The game host managed the shared game state, including player assignments, submissions, and round progression. Keeping those decisions in one place helped all players stay on the same round. The MQTT broker routed messages between devices, while the laptop browsers displayed prompts, clips, and results and let players enter guesses. Prompts were selected from a predefined list, so gameplay did not require calls to a language model.


