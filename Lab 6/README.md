# Distributed Interaction

Yangchen Jin(yj645)
Yan Shen(ys2473)
Simin Xu(sx333)
Flora Zhang(

Teamname: huadiweilao
---
## Part A: MQTT Messaging

<img width="860" height="458" alt="image" src="https://github.com/user-attachments/assets/72794da6-d7fb-4c5e-894f-de2ff10eb26a" />

**💡 Brainstorm 5 ideas for messaging between devices**

**Ideas:**

1. **Break vote light:** Each person waves in front of their own sensor to vote. Once everyone has voted, the Pi in the middle announces "Break time!"
2. **RGB color mixing together:** Three Pis each control one part of the color (red, green, or blue). The three people use their sensors to work together and match a target color shown on a web page.
3. **Color relay:** The first Pi detects a color and sends it out. The next person has to find an object with a similar color and get their sensor to recognize it, then pass it on to the next person.
4. **Tug of war over the air:** Two Pis count how many times each team waves and send the counts over MQTT to the Pi in the middle. A servo on the middle Pi turns toward whichever team is ahead.
5. **Combination lock:** Three Pis each check one condition: a certain color, a knob
---

## Part B: Collaborative Pixel Grid

**📸 Include: Screenshot of grid + photo of your Pi setup**

<img width="1512" height="906" alt="a2a1aae089b897a6de91ea1162132058" src="https://github.com/user-attachments/assets/d6a88a63-7880-4d4c-bf24-e97698afd40d" />

<img width="1280" height="1707" alt="e43c1871e6bfde431b308bc1f12249b9" src="https://github.com/user-attachments/assets/23f6fefc-4cdd-4d97-8ec3-90132270bdf6" />


---

## Part C: Break Vote Light

# 1. Project Description

When a group studies together, nobody wants to be the first one to say "let's take a break." The Break Vote Light lets everyone vote quietly instead. Each person votes from their own device, in their own way: one waves a hand over a proximity sensor, one shakes a motion sensor, and one presses a button. The center Pi counts the votes. Its screen turns gray when nobody has voted, yellow with the count (like "2/4") as votes come in, and green with "BREAK!" once everyone has voted. A vote only counts for 60 seconds, so old votes don't pile up.

Our fourth member's Pi was not working, so their vote is simulated by a script (bot_voter.py, shows up as "simone"). It joins a few seconds after someone else votes.

# 2. Architecture Diagram

<img width="1520" height="940" alt="image" src="https://github.com/user-attachments/assets/d58a4c7d-2344-46a5-972d-0252700e9301" />

- Input: APDS-9960 (wave), LSM6DS3 (shake), PiTFT button (press), plus one simulated voter
- Computation: Jin's Pi counts votes from the last 60 seconds
- Output: the PiTFT screen color, and a status message sent back to every voter

# 3. Build Documentation

Each Pi:

- Yanshen with APDS-9960
- Flora Zhang with LSM6DS3
- Jin's Pi with the Mini PiTFT

<img width="400" alt="a9ad691653fa56ae33cb5ed3be230b03" src="https://github.com/user-attachments/assets/f7ffad0b-876d-4836-9ef6-fd3d533cb1da" />

<img width="400" alt="43e95b0183c5fbab28362e759ff271fc" src="https://github.com/user-attachments/assets/bd3aeefb-fb0d-4441-816b-ece21983d068" />

<img width="1028" height="314" alt="5c4036090bff02fb59ced193316bdbc3" src="https://github.com/user-attachments/assets/6cfda432-bc89-46bc-9a87-bec9f353f7df" />

<img width="857" height="463" alt="869b649b888dd247610d60d371c08889" src="https://github.com/user-attachments/assets/3a9eceed-5a91-4196-b73e-be399ab7bf60" />

**MQTT topics:**

| Topic | Message | Who sends it |
|---|---|---|
| `IDD/huadiweilao/vote/<name>` | `1` | each voter |
| `IDD/huadiweilao/status` | `2/4 want a break: jin, yan` or `BREAK TIME!` | the center Pi |

**Code:**

- [center_light.py](center_light.py): runs on the center Pi
- [voter.py](voter.py): wave to vote (APDS-9960)
- [voter_shake.py](voter_shake.py): shake to vote (LSM6DS3)
- [bot_voter.py](bot_voter.py): the simulated fourth voter

Voting is just one MQTT message. When the hand is close enough, the voter Pi sends a vote under its own name:

```python
if sensor.proximity > THRESHOLD and time.time() - last > COOLDOWN:
    client.publish(f"{TEAM}/vote/{NAME}", "1")
```

The shake voter measures how far the total acceleration is from normal gravity (1 g). A quick shake pushes it over 0.7 g:

```python
strength = abs(math.sqrt(x * x + y * y + z * z) - 1.0)
if strength > SHAKE and time.time() - last > COOLDOWN:
    client.publish(f"{TEAM}/vote/{NAME}", "1")
```

The center Pi keeps the time of each person's last vote, and only counts votes from the last 60 seconds:

```python
live = sorted(n for n, t in votes.items() if now - t < VOTE_TTL)
if len(live) >= NEEDED:
    show((0, 220, 80), "BREAK!")
```
# 4. Video and User Testing

- [Test Video](https://youtube.com/shorts/swP6uVhB3Fg?feature=share)
- [Video 1](https://youtube.com/shorts/ggu9odhWcZg?feature=share)
- [Video2](https://youtube.com/shorts/weRjCOKrgaM?feature=share)

We tested with Lin and Eric.
Before trying: ___
What surprised them: ___
What they would change: ___
# 5. Reflection

What worked well: Using MQTT made it easy to add new kinds of voters. The center Pi doesn't care if a vote comes from a wave, a shake, or a button, it just counts messages on vote/<name>. So each person could use a different sensor without changing the center code.

Challenges with distributed interaction: The hardest part was hardware, not the network. My Qwiic connection didn't work, so my Pi couldn't read a sensor, and one member's Pi was not working at all. We had to move my vote to the PiTFT button and simulate the fourth vote. Also, everyone needs the exact same team name in their topics, or the messages never meet.

How sensor events worked: Each voter Pi checks its sensor about 20 to 50 times a second, but only sends a message when something happens (a wave or a shake), with a 3-second cooldown so one wave doesn't count many times.

What we would improve: Show who has voted on the screen, not just the count, and let people take back a vote.

Where computation happened: Each voter Pi decides locally whether a wave or shake happened, so only small vote messages go over the network. The center Pi does the counting and the 60-second window, because it is the only one that sees every vote. We did not use a language model.
