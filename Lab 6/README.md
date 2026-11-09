# Distributed Interaction

Abiola Bolaji (ab3394), Pallavi Srinivas (ps2269), Pallavi Khanna (pk633), Alina Patel (ap2599)

---

## Part A: MQTT Messaging + Brainstorming

MQTT let our Pis send color readings to a shared server. Each Pi publishes a message to a topic, and the server subscribes to that topic to receive the messages.

The idea we developed was a Mood Ring: each person chooses a color to represent how they feel, and the Pis combine those readings into one shared color.

---

## Part B: Collaborative Pixel Grid

Each Pi = one pixel, controlled by RGB sensor, displayed in real-time grid.

**Architecture:** `Pi (sensor) → MQTT → Server → Web Browser`

For the class demo, each Pi used an APDS-9960 sensor to read color. It sent the reading through MQTT to a server, which showed each Pi as a colored pixel in a browser grid. Holding a colored object near the sensor changed that pixel.

The sensor connects to the Pi over Qwiic. The class demo used the course MQTT broker and the provided grid server.

**📸Screenshot of grid + photo of our Pi setup**
<img width="1511" height="939" alt="Screenshot 2026-11-04 at 6 33 12 PM" src="https://github.com/user-attachments/assets/9c0b3e8f-570a-4ec0-8b09-58ee901598c5" />
<img width="5712" height="4284" alt="IMG_7861" src="https://github.com/user-attachments/assets/0f58c72e-ea3b-4b6f-8aa8-e6f1097c5f92" />
<img width="5712" height="4284" alt="IMG_7862" src="https://github.com/user-attachments/assets/84fd8fe5-13b7-4afc-a1c7-9a2c7a5351df" />


---

## Part C: Make Your Own

### Deliverables

**1. Project Description**

Our project that we chose to make is a Mood Ring simulation that essentially aims to gauge the collective “mood” of a group of people; by averaging the RGB values of all of the Raspberry Pi’s together, we get a brand new color that we deem to be the overall mood. It is interesting because it is interesting to see how colors provide meaningful data regarding human emotion. The user experience depicts a mystical ring that updates smoothly, adding to the seamless experience.

It also encourages users to communicate with their friends about how they are feeling. With the advancement of social media and tech, social isolation has significantly increased. Implementing this can encourage users to maintain healthy relationships with their friends and maintain long distance friendships or relationships through communicating and expressing their feelings.


**2. Architecture Diagram**

- Hardware, connections, data flow
- Label input/computation/output

**3. Build Documentation**

Video of Build
https://drive.google.com/file/d/1wykvbs4ZpKpx3aWbcGs9hSafB7RIA_UC/view?usp=sharing

Each Pi was set up with a proximity/gesture sensor:

<img width="198" height="266" alt="Proximity/gesture sensor" src="https://github.com/user-attachments/assets/a0c28760-f077-407f-8029-88e31d458750" />

The webpage showed the colors of the two users (the left circle showed the left user's mood and the right circle showed the right user's mood):

<img width="622" height="346" alt="Webpage showing two mood circles" src="https://github.com/user-attachments/assets/6c370fae-337f-4d20-ad76-18df315f18cc" />

- MQTT topics used
```bash
TEAM = os.environ.get('MOODRING_TEAM', 'moodring')
COLOR_TOPIC = f'IDD/{TEAM}/colors'
IDD/moodring/colors
```

Code Snippets

```bash
def snapshot():
    """Average the Pis that published within STALE_SECONDS."""
    now = time.time()
    with lock:
        stale = [key for key, value in devices.items() if now - value['seen'] > STALE_SECONDS]
        for key in stale:
            del devices[key]
        live = [
            {'id': key, 'r': value['r'], 'g': value['g'], 'b': value['b']}
            for key, value in sorted(devices.items())
        ]

    if not live:
        return {'count': 0, 'average': None, 'devices': []}

    count = len(live)
    average = [
        sum(item['r'] for item in live) // count,
        sum(item['g'] for item in live) // count,
        sum(item['b'] for item in live) // count,
    ]
    return {'count': count, 'average': average, 'devices': live}
```
This code snippet contains the function snapshot which implements main mechanism that is averaging the RGB values across all of the Pi’s that are connected to the Mood Ring server. By deriving the live RGB values of all of the devices that are providing input, the live [averaged] RGB values of the singular color of the Mood Ring change in response to its environment. 

```bash
while True:
        if sensor is None:
            red, green, blue = fake_color
        else:
            raw_red, raw_green, raw_blue, _clear = sensor.color_data
            red, green, blue = scale_sensor_color(raw_red, raw_green, raw_blue)

        payload = json.dumps({
            'id': device_id,
            'r': red,
            'g': green,
            'b': blue,
            'timestamp': int(time.time()),
        })
```
The while True loop in mood_ring_publisher.py receives the live color data the user provides the sensor. The loop then converts these values into usable RGB values so that they can be provided to the server script. As stated previously, these RGB values are averaged across all connected Pi’s to provide the color of the Mood Ring.

**4. User Testing**

https://drive.google.com/file/d/1Oahv_7D-Oie_AFVXei_BwHu1hCiY6h72/view?usp=sharing

Initially, when we asked the users to try, they were not sure what to do and asked for clarification as the interface only demonstrated the users’ moods and a large circle demonstrating the combined colors. At the same time, they were intrigued by the combined color of all the users and how certain colors overpowered others. This could help start conversations and encourage individuals to communicate their feelings with long-distance partners or friends, strengthening relationships. One thing they recommended to change was adding more instructions on the interface to indicate how to operate the interaction.


**5. Reflection**

The overall user experience is very smooth and aesthetically pleasing, which makes the device much more fun to use. The main focus of our device was the UX as the input of data across all of the Pi’s was pretty much the exact same mechanism we employed as we were prepping/setting up our hardware.

The sensor event worked by each user showing a color that represented their mood to the sensor. Then the webpage we developed receives the colors and demonstrates each color on the screen. Since we used Cursor to create the webpage, Cursor computes the combination of both the colors and then demonstrates the resulting color on the webpage. The model that computed the resulting color had to re-run on every event, because every event had to be treated independently as users may choose a different color to express their feelings. This would mean that the model would have to recalculate the color every time a different color is presented.

Even though we got positive feedback regarding the overall experience, there are still some areas of improvement. For instance, we can improve the user interface by adding more instructions and also make the UI more engaging. One thing I noticed when testing the interaction is that it took a while for the model to sense the right shade of the color. So another thing we could improve is finding a way to make the sensor identify and demonstrate the color faster.

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
