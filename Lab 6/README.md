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
