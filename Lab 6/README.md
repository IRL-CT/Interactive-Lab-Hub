# Distributed Interaction

Abiola Bolaji (ab3394), Pallavi Srinivas (ps2269), Pallavi Khanna (pk633)

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

**💡 Brainstorm 5 ideas for messaging between devices**

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

flowchart TD
    A["Participant holds a chosen color near the sensor"] --> B["APDS-9960 reads raw RGB"]
    B --> C["Pi publisher scales RGB, adds Pi ID and timestamp, publishes every 0.5 seconds"]
    C -->|"JSON on IDD/moodring/colors"| D["MQTT broker at farlab.infosci.cornell.edu:1883"]
    D -->|"server subscribes to the topic"| E["mood_ring_server.py parses readings and stores the latest RGB per Pi"]
    E --> F["Server drops Pis silent for over 5 seconds and averages active RGB values"]
    F -->|"Socket.IO mood update; browser also fetches /state on load"| G["Webpage updates the large ring and each Pi's color swatch"]

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

---

---

Resources: [MQTT Guide](https://www.hivemq.com/mqtt-essentials/) | [Paho Python](https://www.eclipse.org/paho/index.php?page=clients/python/docs/index.php) | [Flask-SocketIO](https://flask-socketio.readthedocs.io/)
