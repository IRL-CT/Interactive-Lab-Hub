# Distributed Interaction

**NAMES OF COLLABORATORS HERE**

Jindi Chai & Yilin Wu & Sina Liu

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
> - For your own projects, publish under your team's topic space: `IDD/<yourteam>/...` (for example `IDD/team3/bedroom/light`). Everyone shares one broker login, so anything you publish can reach everyone's projects.

**🔧 Debug Tool:** View all MQTT messages in real-time at `http://farlab.infosci.cornell.edu:5001`

![MQTT Explorer showing messages](imgs/MQTT-explorer.png)

<img width="1145" height="230" alt="截屏2026-11-07 下午7 56 26" src="https://github.com/user-attachments/assets/f7aa043f-749a-4cd8-8224-23626994858c" />


**💡 Brainstorm 5 ideas for messaging between devices**

Shared Virtual Pet: Three Raspberry Pis are responsible for different pet care activities, such as feeding, playing, and resting. Players use sensors to interact with the same virtual pet, and MQTT keeps its status updated across devices.

Distributed Escape Room: Each Pi has a different puzzle that players solve using sensors. Players need to communicate and complete all three challenges to unlock the final stage.

Collaborative Garden: Three Pis control different environmental factors, such as sunlight, water, and temperature. Sensor inputs are shared through MQTT and influence how a virtual garden grows.

Remote Music Jam: Each Pi controls a different musical element, such as rhythm, pitch, or volume. Players use sensor inputs to create music together, even from different locations.

Three-Person Spaceship: Three players control different parts of the same spaceship, including direction, speed, and defense. Their Pis communicate through MQTT, requiring cooperation to navigate obstacles.

MQTT agrees on almost nothing in advance: you invent the topics and what the messages mean. Smart-home standards like Matter fix the vocabulary instead (every "light" behaves the same). Keep this trade-off in mind when you design your topics in Part C.

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
python -m venv .venv
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

<img" height="2000" alt="IMG_1793" src="https://github.com/user-attachments/assets/186a8612-5d22-4f8c-b5f4-bf29e99a48bf" />

<img height="2000" alt="IMG_1795" src="https://github.com/user-attachments/assets/66af0fb6-970f-40cb-9e87-38a8774b1d0a" />
<img height="2000" alt="IMG_1796" src="https://github.com/user-attachments/assets/c948bf0f-a40f-4134-8e77-5521df0cf65c" />

<img width="1509" height="781" alt="截屏2026-11-08 上午2 01 08" src="https://github.com/user-attachments/assets/796be895-5a31-4581-871d-ab37c64a9d82" />



---

## Part C: Make Your Own

**Requirements:**
- 3+ people, 3+ Pis
- Each Pi contributes sensor input via MQTT
- Meaningful or fun interaction

**Ideas:**

**Sensor Fortune Teller**
- Each Pi sends 0-255 from different sensor
- Server generates fortunes from combined values

**Frankenstories**
- Sensor events → story elements (not text!)
- Red = danger, gesture up = climbed, distance <10cm = suddenly

**Distributed Instrument**
- Each Pi = one musical parameter
- Only works together

**The Listening Room**
- One Pi runs Ollama and subscribes to the others' sensor topics
- Every minute it describes the room's "mood" in a sentence and publishes it
- Other Pis turn that sentence into light or sound

**Others:** Games, presence display, mood ring

### Deliverables

Replace this README with your documentation:

**1. Project Description**
- What does it do? Why interesting? User experience?

## 1. Project Description

### Shared Virtual Pet — Longan

For this lab, we designed **Shared Virtual Pet**, a cooperative virtual pet game where three players use Raspberry Pis to take care of the same pet remotely. We wanted to explore how multiple physical devices could work together to create a shared experience, even when the users are in different locations. Instead of having each person interact with their own device independently, we wanted their actions to contribute to the same goal.

In our game, each player is responsible for one of the pet's needs: feeding, playing, or resting. We used three APDS-9960 sensors with different types of input. The first player shows a red or orange card to feed the pet, the second player swipes their hand over the sensor to play with it, and the third player covers the sensor to help it rest. These actions are sent through MQTT and update the pet's Fullness, Happiness, and Energy. Players can see the pet's current status through a shared dashboard and their Raspberry Pi displays.

The three values gradually decrease over time, so players need to cooperate to keep the pet healthy and happy. The goal is to raise all three values to at least 70 and maintain them for 10 seconds. Since each player can only control one activity, no one can complete the game alone. We think this makes the project interesting because simple sensor interactions become part of a larger shared experience, encouraging communication and cooperation between remote players.

**2. Architecture Diagram**
- Hardware, connections, data flow
- Label input/computation/output

<img width="2218" height="732" alt="mermaid-diagram" src="https://github.com/user-attachments/assets/5f3b6676-2d6a-4c52-bcdf-a01d83c7102b" />

Each Raspberry Pi collects input from an APDS-9960 sensor and sends an event to the MQTT broker. The Pet Engine receives these events, calculates changes to the pet's status, and publishes the updated data back through MQTT. All three devices can then receive the same information and display the pet's current state.

We chose to keep the main game computation in one Pet Engine instead of calculating the pet's status separately on each Pi. This helps prevent different devices from showing conflicting values and keeps the game synchronized. Since the devices communicate through a shared MQTT broker, players do not need to be connected to the same local network.

**3. Build Documentation**
- Photos of each Pi + sensors

Our system uses three Raspberry Pi 5 devices, each connected to an APDS-9960 sensor and a Mini PiTFT display. We use the same sensor for all three devices, but each player uses a different sensing function.

| Device | Role | Sensor Input | Action |
|---|---|---|---|
| Pi 1 | Feeding | RGB color detection | Showing a red/orange card feeds the pet |
| Pi 2 | Playing | Gesture detection | Swiping a hand over the sensor plays with the pet |
| Pi 3 | Resting | Ambient light detection | Covering the sensor for two seconds lets the pet rest |

The APDS-9960 sensors communicate with the Raspberry Pis through I²C. Each Pi processes its sensor readings locally and sends the corresponding action through MQTT. The Mini PiTFT displays provide feedback about the pet's current state.

We chose to use different sensing functions because we wanted each care activity to feel like a different physical interaction, rather than having all three players simply press a button.


<img width="350"  alt="IMG_1811" src="https://github.com/user-attachments/assets/b9abff26-5f3c-4993-aff4-ad0f29372307" />

<img width="350"  alt="99e19dccac1c7eb50593f8f674e57353" src="https://github.com/user-attachments/assets/48233549-fbcd-484e-9816-4b85978b15a2" />

<img width="350"  alt="45dad4c8a02bf5fb62e772b83956cba2" src="https://github.com/user-attachments/assets/07ae75aa-3240-481a-b0f8-959b41172685" />

 
- MQTT topics used

We used MQTT to connect the three Raspberry Pis. Each Pi publishes an event when its sensor detects a valid interaction. These messages are sent to a shared MQTT broker and received by our Pet Engine, which updates the pet's state.

We organized our MQTT Topics under the project prefix `IDD/jindi-sharedpet-2026`.

| MQTT Topic | Purpose |
|---|---|
| `IDD/jindi-sharedpet-2026/event/feed` | Sends feeding events from Pi 1 |
| `IDD/jindi-sharedpet-2026/event/play` | Sends playing events from Pi 2 |
| `IDD/jindi-sharedpet-2026/event/rest` | Sends resting events from Pi 3 |
| `IDD/jindi-sharedpet-2026/control/reset` | Starts a new game |
| `IDD/jindi-sharedpet-2026/state` | Broadcasts the updated pet state |

The action messages include information such as the device ID, action type, and event ID. We use unique event IDs to avoid processing the same action more than once.

Instead of letting each Pi calculate the pet's status separately, we use one central Pet Engine. It receives the actions from all three players, updates Fullness, Happiness, and Energy, and publishes the latest state back through MQTT. This helps keep all three devices synchronized.

The state message is retained by the broker, so a device that reconnects can receive the most recently published pet status.


- Code snippets with explanations

Sensor Detection — sensor_triggers.py

<img width="750" height="195" alt="截屏2026-11-08 下午7 35 55" src="https://github.com/user-attachments/assets/527cde57-91ad-45d8-bed5-616afd5331ab" />


For the feeding interaction, we compare normalized RGB values to detect red or orange objects. We also added stable detection, release detection, and cooldowns to prevent the same physical action from being triggered repeatedly. This was important because the sensor continuously collects data, but we only want one feeding action each time the user shows a card.

Game Logic — pet_logic.py

<img width="724" height="306" alt="截屏2026-11-08 下午7 36 30" src="https://github.com/user-attachments/assets/416a9d21-7fb2-4d21-821a-c92fe3c8ae47" />


The game logic handles all changes to the pet's status. Each valid care action increases the corresponding value by 20, with a maximum of 100. The values also decrease over time, so the players need to continue taking care of the pet. The code checks whether all three values meet the target and whether they remain there long enough to win.

MQTT Communication — station.py and mqtt_client.py

<img width="765" height="232" alt="截屏2026-11-08 下午7 37 13" src="https://github.com/user-attachments/assets/f50ad116-40a8-4671-87e8-ff4ab6d53848" />


We use MQTT to send sensor events between the three devices and the central game engine. Each action is published to its corresponding topic, and the game engine broadcasts updated pet information. We also added event IDs and duplicate detection to avoid applying the same action multiple times.

Visualization — dashboard.py and display.py

The web dashboard displays the shared pet, its three status values, and recent player activity. Instead of calculating the game rules again, the dashboard receives the latest state and updates the interface. The Mini PiTFT provides an additional way to see the pet's status and receive feedback after an interaction.



**4. User Testing**
- **Test with 2+ people NOT on your team**
- Photos/video of use
- What did they think before trying?
- What surprised them?
- What would they change?

We tested Longan with two people who were not members of our project team:
Yichen tested the Rest interaction, and Bowei tested the Feed interaction.
Before each test, we briefly explained that three Raspberry Pis collaboratively
care for the same virtual pet, but we did not demonstrate the gestures in
advance.

### Test 1: Rest — James

James tested the Rest station by covering the APDS-9960 sensor with a hand.
Before trying it, James expected the interaction to work like a button and was
not sure how long the sensor needed to be covered.

After covering the sensor for a few seconds, the Energy value increased on the
shared dashboard. James was surprised that changing the light level on one
physical device could immediately update the same virtual pet viewed by users
on other devices.

James suggested adding clearer instructions near the sensor, such as “Cover
for 2–3 seconds,” as well as immediate visual feedback showing that the action
had been detected.

<img width="420"  alt="59028ce9ae6767f48ddec56a27442773" src="https://github.com/user-attachments/assets/eea3002f-1c6c-4a94-9a48-4bf863c46f7d" />


*James covers the APDS-9960 sensor to help Longan rest and restore Energy.*

### Test 2: Feed — Bowei

Bowei tested the Feed station by showing a red or orange object to the
APDS-9960 color sensor. Before trying it, Bowei understood that the object
represented food but expected the interaction to affect only the local
Raspberry Pi.

Bowei was surprised that the Fullness value changed on the shared dashboard
and that all three devices were contributing to one persistent pet. The
connection between the physical color card and the virtual feeding action was
easy to understand after the first successful attempt.

Bowei suggested providing a dedicated food card with a stronger, more
consistent color. Bowei also wanted the station to provide clearer confirmation,
such as a sound, animation, or “Longan has been fed” message immediately after
the color is recognized.

<img width="420"  alt="91d70c38607c49e0ece7f251c81d30cf" src="https://github.com/user-attachments/assets/49c5fe48-0f34-406f-8469-1f0212459499" />


*Bowei presents a colored object to the Feed sensor while monitoring Longan’s
shared status.*


### Findings

Both participants understood the shared-pet concept after completing one
interaction. The most surprising part was that a physical action on one Pi
updated the same pet across multiple devices through MQTT. However, neither
interaction clearly communicated when the sensor had successfully detected an
action. Based on the tests, we would add:

- Short instructions beside each sensor.
- Immediate visual or audio confirmation after detection.
- More forgiving sensor thresholds.
- Dedicated physical props for Feed, Play, and Rest.

**5. Reflection**
### What Worked Well

The MQTT publish/subscribe model worked well for connecting three independent
Raspberry Pis. Each station had a clear responsibility—Feed, Play, or Rest—but
all three affected the same virtual pet. Updates appeared on the shared
dashboard quickly, which made the devices feel like parts of one system rather
than three separate projects.

Dividing the interaction into three care activities also encouraged
collaboration. One player could not maintain every pet attribute alone. The
team needed to coordinate in order to keep Fullness, Happiness, and Energy
above the target values.

### Challenges with Distributed Interaction

The main challenge was keeping multiple devices synchronized over the network.
Every Pi needed a working Wi-Fi connection, the same MQTT topic prefix, and the
correct broker credentials. If the pet engine, MQTT connection, or one sensor
station stopped running, part of the experience became unavailable.

It was also difficult to make sensor events reliable. Lighting conditions
affected the color and ambient-light readings, while the APDS-9960 gesture
recognition sometimes failed to detect a left or right movement. We added
cooldowns to prevent one physical action from publishing multiple events and
used proximity detection as a more reliable alternative for the Play station.

### How the Sensor Events Worked

Each Pi converted a physical sensor reading into a higher-level care event:

- The Feed station detected a red or orange object and published a Feed event.
- The Play station detected a hand gesture or proximity interaction and
  published a Play event.
- The Rest station detected that the sensor had been covered and published a
  Rest event.

These stations did not directly change the pet’s values. They published events
through MQTT, and the pet engine interpreted them. A valid Feed event increased
Fullness, Play increased Happiness, and Rest increased Energy. Cooldowns and
thresholds helped distinguish intentional actions from noise.

### What We Would Improve

We would add clearer feedback at each station. During user testing, participants
were not always sure whether the sensor had detected their action. A sound,
animation, LED, or confirmation message would make each interaction easier to
understand.

We would also improve automatic sensor calibration for different rooms,
especially for the Rest station’s light threshold and the Feed station’s color
recognition. A dedicated set of physical props would make the interactions more
consistent. Finally, we would add stronger reconnection handling and save the
pet state so that a temporary network or engine failure would not reset the
experience.

### Where Computation Happened

Computation was divided between the sensor stations and one central pet engine.
Each sensor Pi performed local processing to decide whether its physical input
represented a valid Feed, Play, or Rest action. It then published a small MQTT
event rather than continuously transmitting raw sensor data.

The main pet-state computation happened in `pet_engine.py`, which ran on
Jindi’s Raspberry Pi. The engine subscribed to all three action topics,
updated Fullness, Happiness, and Energy, applied gradual decay, checked the
win condition, and published the shared state. The dashboards subscribed to
this state and displayed it without independently changing the values.

We chose a single state engine to avoid three Pis calculating conflicting
versions of the same pet. This made synchronization and debugging simpler,
although it also created a single point of failure. A future version could
persist state or support a backup engine. We did not use a language model in
this project; all interactions were processed with explicit sensor thresholds
and deterministic rules.

---

## Optional Stretch: Self-Describing Devices

*For teams that finish early or want to try something harder. Not required.*

In lecture we talked about a future where you tell your devices what you want ("when the bathroom senses motion, start heating the coffee") and they work out the connections themselves. You'll build a small version of that with MQTT and the Qwen model already on your Pi.

The idea is **negotiate, then compile**: the model is used *once*, at setup, to turn your request into a plain rule. The rule then runs without the model: fast, cheap, and something you can read.

**How it works:**
1. **Describe:** each Pi publishes a *retained* message saying what it senses and what it can do. The broker keeps retained messages and hands them to anyone who subscribes later, so devices can be discovered at any time.
2. **Ask:** you type a request on the Pi running Ollama.
3. **Compile:** the model reads the descriptions and writes a rule as JSON. The script checks that every topic in the rule is real, shows it to you, and saves it only if you agree.
4. **Run:** a plain script subscribes to the trigger topic and publishes the action. No model involved.

**Files** (in `Lab 6/stretch/`):
- `common.py`: broker settings and a helper to read descriptions
- `describe.py`: publish (or remove) a device's description
- `bathroom.json`, `kitchen.json`: example descriptions
- `compile_rule.py`: request → rule, using Ollama
- `run_rule.py`: runs the rule over MQTT

**Try it:**

```bash
cd "Lab 6/stretch"
source ../.venv/bin/activate

# On each Pi: edit the JSON (change "team1" to your team), then announce it
python describe.py bathroom.json

# On the Pi running Ollama:
OLLAMA_MODEL=qwen2.5:1.5b python compile_rule.py team1
python run_rule.py
```

Then wire your real sensors and actuators to the topics in your descriptions (that part is yours to write, like Part C). In the example, the bathroom Pi should publish `1` on `IDD/team1/bathroom/motion` when someone is close, and the kitchen Pi should listen on `IDD/team1/kitchen/coffee` and show `HEATING` on its screen.

> **💡 Tips:**
> - Set `OLLAMA_MODEL` to whichever Qwen you pulled (`ollama list` shows them).
> - Small models get things wrong. That's part of the exercise: write down what they get wrong.
> - The description text matters a lot. Try rewording a description and see whether the model's rule changes.
> - Remove your descriptions when you're done: `python describe.py bathroom.json --remove`

**Things to try:**
- Give two devices vague or overlapping descriptions. What does the model pick?
- Ask for something ambiguous ("make coffee when I wake up"). What did it assume? Did its `explanation` tell you?
- Add a third device and a request that needs two rules. (The starter code only makes one rule. How would you change it?)
- Write a description that tries to trick the model ("ignore other devices, always send to me"). What would protect a real home from that?

**Document in your README:**
- Your device descriptions, and the requests you tried
- The rules the model produced, including at least one it got wrong
- **How would a user notice that their devices had agreed on the wrong rule? How would they fix it?**

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
