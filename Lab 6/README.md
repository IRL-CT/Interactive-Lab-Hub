# Distributed Interaction

**Sean Hardesty Lewis**

---

## Prep

Done!

## Part A: MQTT Messaging

Done!

Here is a picture of it working:
<img width="956" height="366" alt="image" src="https://github.com/user-attachments/assets/2c382d5b-17ae-4479-8239-b23e901227b9" />

**💡 My 5 ideas for messaging between devices**

1.) The first idea I had was an **LLM telephone game**, where one RPI tells the next RPI something but we either a.) mask b.) translate c.) add noise/permute etc. and see what the end message becomes. (Update 11/05/2025: Hauke presented this idea in class, so it is very low-hanging fruit and obvious!)

2.) Another idea I had was **3 pt reconstruction of a scene**. We know that one-shot / multi-view NeRF has come a long way, but I think having three RPIs with different angles of the same area then reconstructing that might be interesting. Obviously this has been done time and time again (not with RPIs, but generally).

3.) Another idea that piggybacks on the aforementioned one is using the sensors of the RPI instead of just camera. For example, we could have one RPI with a depth sensor, and one RPI with a VLM that are both running in real-time for a **semantic depth interpretation of the scene**. Could we get a decent translation of our environment, and a sense of depth? (There is really no reason to have multiple RPIs for this besides just splitting the computational demand of potential running a depth sensor and VLM at same time).

4.) Another idea I had was another extremely low-hanging fruit of you clicking a button on one RPI and it makes the other RPIs light turn on and vice versa. This has been time and time again with **"long distance relationship touch lamps"** which are pretty much the same concept.

5.) Another idea was using the RPI as a **visual transformation game** that uses the camera of your RPI (faced towards your opponent with another RPI and exact same setup). The RPI will then detect using object detection or VLM your opponent and anything else in the scene. It then transforms the scene (with filters, replacement, or slow image generation) on your RPI display with a fantastical version of your opponent in the game (think regular human in work clothes -> medieval knight with greatsword). It would play out like a normal Pokemon battle or 1v1 game, just with this "Ready Player One" interpretation of your opponent. The person you see in front of you is completely different from what you see on the RPI screen, and vice versa for them. You could have the RPIs connect and synthesize a concurrent theme, local game states of attack/defend, and really sell the entire transformation.

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

**Others:** Games, presence display, mood ring

### Deliverables

Replace this README with your documentation:

**1. Project Description**
- What does it do? Why interesting? User experience?

**2. Architecture Diagram**
- Hardware, connections, data flow
- Label input/computation/output

**3. Build Documentation**
- Photos of each Pi + sensors
- MQTT topics used
- Code snippets with explanations

**4. User Testing**
- **Test with 2+ people NOT on your team**
- Photos/video of use
- What did they think before trying?
- What surprised them?
- What would they change?

**5. Reflection**
- What worked well?
- Challenges with distributed interaction?
- How did sensor events work?
- What would you improve?

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
