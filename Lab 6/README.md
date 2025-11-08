# Distributed Interaction

**NAMES OF COLLABORATORS HERE**

For submission, replace this section with your documentation!

---

## Prep

1. Pull the new changes
2. Read: [The Presence Table](https://dl.acm.org/doi/10.1145/1935701.1935800) ([video](https://vimeo.com/15932020))

## Overview

Build interactive systems where **multiple devices communicate over a network** using MQTT messaging. Work in teams of 3+ with Raspberry Pis.

**Parts:**
- A: Learn MQTT messaging
- B: Try collaborative pixel grid demo  
- C: Build your own distributed system

---

## Part A: MQTT Messaging

MQTT = lightweight messaging for IoT. Publish/subscribe model with central broker.

**Concepts:**
- **Broker**: `farlab.infosci.cornell.edu:1883`
- **Topic**: Like `IDD/bedroom/temperature` (use `#` wildcard)
- **Publish/Subscribe**: Send and receive messages

**Install MQTT tools on your Pi:**
```bash
sudo apt-get update
sudo apt-get install -y mosquitto-clients
```

**Test it:**

**Subscribe to messages (listener):**
```bash
mosquitto_sub -h farlab.infosci.cornell.edu -p 1883 -t 'IDD/#' -u idd -P 'device@theFarm'
```

**Publish a message (sender):**
```bash
mosquitto_pub -h farlab.infosci.cornell.edu -p 1883 -t 'IDD/test/yourname' -m 'Hello!' -u idd -P 'device@theFarm'
```

> **💡 Tips:**
> - Replace `yourname` with your actual name in the topic
> - Use single quotes around the password: `'device@theFarm'`

**🔧 Debug Tool:** View all MQTT messages in real-time at `http://farlab.infosci.cornell.edu:5001`

![MQTT Explorer showing messages](imgs/MQTT-explorer.png)

**💡 Brainstorm 5 ideas for messaging between devices**

---

## Part B: Collaborative Pixel Grid

Each Pi = one pixel, controlled by RGB sensor, displayed in real-time grid.

**Architecture:** `Pi (sensor) → MQTT → Server → Web Browser`

**Setup:**

1. **Sensor**

#### Light/Proximity/Gesture sensor (APDS-9960)
We use this sensor [Adafruit APDS-9960](https://www.adafruit.com/product/3595) for this exmaple to detect light (also RGB)
 
<img src="https://cdn-shop.adafruit.com/970x728/3595-06.jpg" width=200>

Connect it to your pi with Qwiic connector


<img src="imgs/IMG_0270.jpg" height="200" />
We need to use the screen to display the color detection, so we need to stop the running piscreen.service to make your screen available again

```bash
# stop the screen service
sudo systemctl stop piscreen.service
```

if you want to restart the screen service
```bash
# start the screen service
sudo systemctl start piscreen.service
```
 
2. **Server** (one person on laptop):
```bash
cd "Lab 6"  
source .venv/bin/activate
pip install -r requirements-server.txt
python app.py
```

2. **View in browser:**
   - Grid: `http://farlab.infosci.cornell.edu:5000`
   - Controller: `http://farlab.infosci.cornell.edu:5000/controller`

3. **Pi publisher** (everyone on their Pi):
```bash
# First time setup - create virtual environment
cd "Lab 6"
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-pi.txt

# Run the publisher
python pixel_grid_publisher.py
```

Hold colored objects near sensor to change your pixel!

![Pixel grid with two devices](imgs/two-devices-grid.png)

**📸 Include: Screenshot of grid + photo of your Pi setup**

---

## Part C: Make Your Own


### Deliverables

Replace this README with your documentation:  

**1. Project Description**
This is a cooperative game in which three players attempt to retrieve a legendary treasure hidden deep inside an ancient temple. Each player controls a different physical sensor device. The Game Master script delivers the story narration and instructions over MQTT. Players must perform their assigned actions in the correct order to advance the story.

The interaction becomes meaningful because:

- Each player contributes a unique action.
- No player can solve the puzzle alone.
- Success depends on communication and timing.

The story framework turns simple sensor actions into dramatic “temple mechanisms” that must be activated to progress.

**2. Architecture Diagram**  

Three Raspberry Pis act as players:

- Player A uses a touch sensor
- Player B uses a joystick
- Player C uses a color sensor

A central Game Master coordinates the game:

1. Sends narration text to all players.
2. Sends individual tasks privately to each player.
3. Waits for each player to respond with either “success” or “fail.”
4. Determines whether the group continues or the adventure ends.

**(Diagram Here)**

**3. Build Documentation**  
**Set up Photos + 2 videos**
 
**Hardware Setup**  

Each Raspberry Pi is connected to:

- Power
- I2C communication lines for its sensor

Player A interacts by touching specific pads.
Player B interacts by moving or pressing the joystick.
Player C interacts by showing colored objects to the APDS-9960.

Each sensor continuously reads input and checks whether the required action has been performed.


**MQTT Communication Structure**

The Game Master sends story narration using the topic:
game/story


The Game Master sends individual task commands:
game/<player_name>/task


Each player reports success or failure to:
game/<player_name>/result


The Game Master broadcasts final outcome:
game/status


Payload: game_success or game_fail
Broker:
Host: farlab.infosci.cornell.edu
Port: 1883
Username: idd
Password: device@theFarm

**Story Integration**

Narration lines are stored inside game_master.py:  

#### Story Introduction

You are part of a legendary trio of master thieves, known across kingdoms as the Silent Serpents.
Tonight, you infiltrate the ancient Temple of the Sleeping Star, a place rumored to guard the priceless relic known as the Heart of Dawn.

The temple is protected by layered traps, intricate puzzles, and arcane barriers.
Only perfect coordination will allow you to survive… and escape with the treasure.

#### Challenge 1 — The Shifting Pathway

A long stone pathway stretches before you.
The floor panels slide and realign like living machinery, revealing hidden spike pits beneath.

To move forward safely, your steps must be chosen with precision.
The temple waits for your command.

#### Challenge 2 — The Runes of Awakening

A towering wall carved with ancient runes begins to glow in a cool blue light.
Each symbol corresponds to an old incantation — but only one correct combination will unlock the next chamber.

A single mistake could seal the passage forever.

#### Challenge 3 — The Veil of Spectral Light

Ahead, a shimmering arcane barrier blocks the path.
Its surface ripples like moonlit water, changing color with an otherworldly rhythm.

Only by matching its hue precisely can the barrier be dissolved and the path revealed.

#### Outcomes

**If the action is correct:**
Your movement is precise. The mechanism responds. The path forward opens.

**If the action fails:**
Your action falters. The mechanism resists. The temple remains sealed, and time is running out.




**4. User Testing**

- Photos/video of use
  
#### Before trying:
Most participants were curious but unsure how the different sensors would interact. They expected the game to be simple and linear.

#### During the game:
Players were surprised by how coordinated actions were required. The need to respond quickly and accurately to each step created tension and excitement. Participants particularly enjoyed seeing the story unfold in real-time as each sensor triggered events.

#### Feedback and observations:

- Players appreciated the story-driven experience; it added context and motivation for their actions.
- Some noted that the time limit for tasks was challenging but fun.
- A few suggested adding more variety to the story and sensor interactions to increase replay value.
- All participants enjoyed the distributed, collaborative nature — the game only worked when everyone succeeded together.

**5. Reflection**
What worked well:

- The narrative improved engagement and made sensor tasks feel meaningful.
- The sequential structure ensured that cooperation was required.

Challenges:

- Color sensor thresholds required careful tuning under different lighting.
- Players sometimes forgot to watch the terminal for story or task updates.

Future improvements:

- Add sound or LED cues to reinforce when to act.
- Expand story paths for alternative outcomes.

---

## Code Files

**Server files:**
- `app.py` - Pixel grid server (Flask + WebSocket + MQTT)
- `mqtt_viewer.py` - MQTT message viewer for debugging
- `mqtt_bridge.py` - MQTT → WebSocket bridge
- `requirements-server.txt` - Server dependencies

**Pi files:**
- `pixel_grid_publisher.py` - Example (RGB sensor → MQTT)
- `requirements-pi.txt` - Pi dependencies

**Web interface:**
- `templates/grid.html` - Pixel grid display
- `templates/controller.html` - Color picker
- `templates/mqtt_viewer.html` - Message viewer

---

## Debugging Tools

**MQTT Message Viewer:** `http://farlab.infosci.cornell.edu:5001`
- See all MQTT messages in real-time
- View topics and payloads
- Helpful for debugging your own projects

**Command line:**
```bash
# See all IDD messages
mosquitto_sub -h farlab.infosci.cornell.edu -p 1883 -t "IDD/#" -u idd -P "device@theFarm"
```

---

## Troubleshooting

**MQTT:** Broker `farlab.infosci.cornell.edu:1883`, user `idd`, pass `device@theFarm`

**Sensor:** Check `i2cdetect -y 1`, APDS-9960 at `0x39`

**Grid:** Verify server running, check MQTT in console, test with web controller

**Pi venv:** Make sure to activate: `source .venv/bin/activate`


---

## Submission Checklist

Before submitting:
- [ ] Delete prep/instructions above
- [ ] Add YOUR project documentation
- [ ] Include photos/videos/diagrams  
- [ ] Document user testing with non-team members
- [ ] Add reflection on learnings
- [ ] List team names at top

**Your README = story of what YOU built!**

---

Resources: [MQTT Guide](https://www.hivemq.com/mqtt-essentials/) | [Paho Python](https://www.eclipse.org/paho/index.php?page=clients/python/docs/index.php) | [Flask-SocketIO](https://flask-socketio.readthedocs.io/)
