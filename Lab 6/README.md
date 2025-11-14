# Distributed Interaction

**Team Members: Jessica Hsiao (dh779), Irene Wu (yw2785), Melody Huang (yh2353), Dingran Dai (dd699)**

<details><summary>Instruction</summary>

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

</details>

---

## Part A: MQTT Messaging

<details><summary><strong>Instruction</strong></summary>
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
</details>

**💡 Brainstorm 5 ideas for messaging between devices**

**1. Storyteller game:** Start randomly from a person’s pi, using a word chain structure. Participants collaboratively weave a narrative by linking words, where each subsequent word must begin with the last letter of the previous one. 

**2. An online forum:** such as Poll Everywhere, where everyone can participate in a real-time discussion. A central moderator publishes the questions or topics, and all the other users can express their opinion through pi.

**3. School announcements:** whenever the school sends out an announcement, it’s delivered directly to each student’s device. Students can also use the device to share useful information with each other.

**4. Personal Data Sharing:** sync all personal device data, such as notes, health data, and plans, across all personal devices without being limited to a single brand.

**5. When 2+ Pis come within Wi-Fi range**, they automatically open a chat window which could exchange personal symbols (emojis, sound or text that represents its user’s mood of the day). 


---

## Part B: Collaborative Pixel Grid


<details><summary><strong>Instruction</strong></summary>
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
</details>

**📸 Include: Screenshot of grid + photo of your Pi setup**

<img width='400' src="https://github.com/user-attachments/assets/01d498ba-b083-4a4a-bff5-857d3e768aaf"/>

---

## Part C: Make Your Own

<details><summary><strong>Instruction</strong></summary>

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

</details>


---

# Color Scavenger Hunt

**Team Members:** Jessica Hsiao (dh779), Irene Wu (yw2785), Melody Huang (yh2353), Dingran Dai (dd699)

## 1\. Project Description

### What does it do?

Our project is a real-time, competitive "Color Scavenger Hunt" game. A central "Game Master" (a laptop) publishes a target color (e.g., "RED") over MQTT. All players (using Raspberry Pis with APDS-9960 sensors) must then race to find a real-world object of that color and scan it.

### Why is it interesting?

This project creates a fun, high-energy interaction that bridges the digital and physical worlds. It uses a distributed system (MQTT) not just for passive data display, but as the core mechanic for a fast-paced game. The system has to instantly manage game state, identify a single winner from multiple simultaneous inputs, and reset for the next round, all using lightweight messages.

### What is the user experience?

A player's Pi screen displays, "Waiting for game to start...". Suddenly, it updates: "**Find: [ BLUE ]**". The player frantically looks around, grabs a blue water bottle, and points the sensor at it. Their screen flashes: "**You found it\!**". A moment later, all player screens update with the winner: "**Player 2 wins\!**" After a 3-second pause, a new round begins: "**Find: [ GREEN ]**".

## 2\. Architecture Diagram

Our system is built on a publish/subscribe model using one central server (Game Master) and multiple Pi clients (Players).

```
                                +-------------------+
                                |    MQTT Broker    |
                                | (farlab.infosci...) |
                                +-------------------+
                                    ^           |
                                    |           |
(Pub/Sub: All Topics) . . . . . . . |           | . . . . . . . (Pub/Sub: All Topics)
                                    |           v
+--------------------------+    +--------------------------+    +--------------------------+
|  Pi 1 (Player)           |    |  Server (Game Master)    |    |  Pi 2 (Player)           |
|  [Input]  APDS-9960 Sensor |    |  [Input]  MQTT Sub         |    |  [Input]  APDS-9960 Sensor |
|  [Compute] Check Color Match |    |  [Compute] Game Logic      |    |  [Compute] Check Color Match |
|  [Output] MQTT Pub, Screen |    |  [Output] MQTT Pub         |    |  [Output] MQTT Pub, Screen |
+--------------------------+    +--------------------------+    +--------------------------+
```

  * **Inputs:**
      * **Pi:** Reads (R, G, B) values from the APDS-9960 sensor.
      * **Pi:** Subscribes to `IDD/game/hunt/master` and `IDD/game/hunt/winner` topics.
      * **Server:** Subscribes to the `IDD/game/hunt/player_found` topic.
  * **Computation:**
      * **Pi:** Continuously compares its sensor's (R, G, B) value against the current target color.
      * **Server:** Runs the main game loop: selects a random color, publishes it, listens for the *first* player to respond, validates the winner, and publishes the result.
  * **Outputs:**
      * **Server:** Publishes the target color to `IDD/game/hunt/master`.
      * **Server:** Publishes the round's winner to `IDD/game/hunt/winner`.
      * **Pi:** Publishes its unique name (e.g., `Pi_1_Ariel`) to `IDD/game/hunt/player_found` when it detects a match.
      * **Pi:** Displays the current game state on its screen.

## 3\. Build Documentation

<img width="400" src="https://github.com/user-attachments/assets/57b3262e-5f51-4afb-9784-1bdcce3b7e46" />


Player setup, showing the Qwiic connection to the APDS-9960 sensor.

<img width="400" src="https://github.com/user-attachments/assets/902be737-003d-4e93-87c5-87dde6cf9ad5" />

The Game Master server running on a laptop, showing the console output as it manages a round.

### MQTT Topics Used

We created a dedicated namespace `IDD/game/hunt/` for our project.

1.  **`IDD/game/hunt/master`**

      * **Published by:** Server (Game Master)
      * **Subscribed by:** All Pis (Players)
      * **Message:** A string representing the target color (e.g., `RED`, `GREEN`, `BLUE`).
      * **Purpose:** To start a new round and tell all players what color to find.

2.  **`IDD/game/hunt/player_found`**

      * **Published by:** Any Pi (Player)
      * **Subscribed by:** Server (Game Master)
      * **Message:** The unique name of the player (e.g., `Pi_1_Ariel`).
      * **Purpose:** This is the "buzzer" topic. The first player to find the color publishes here to claim victory for the round.

3.  **`IDD/game/hunt/winner`**

      * **Published by:** Server (Game Master)
      * **Subscribed by:** All Pis (Players)
      * **Message:** A string announcing the winner (e.g., `Pi_1_Ariel wins!`).
      * **Purpose:** To inform all players who won the round and to signal the end of the round.

### Code Snippets & Explanations

#### Server (`game_master.py`)

The server's most important logic is in the `on_message` callback and the main `while` loop.

```python
# --- Global variable to track winner ---
round_winner = None 

# --- Callback for when a player "buzzes in" ---
def on_message(client, userdata, msg):
    global round_winner
    
    # This is the key logic: only accept the FIRST message
    if round_winner is None:
        player_name = msg.payload.decode()
        print(f"WINNER DETECTED: {player_name}")
        
        # Set the winner so no one else can win this round
        round_winner = player_name
        
        # Publish the winner to all players
        client.publish(WINNER_TOPIC, f"{player_name} wins this round!")

# --- Main Game Loop ---
try:
    while True:
        # 1. Reset the round
        round_winner = None
        
        # 2. Pick and publish a new color
        current_target_color = random.choice(TARGET_COLORS)
        print(f"\n--- NEW ROUND ---")
        print(f"Telling players to find: {current_target_color}")
        client.publish(MASTER_TOPIC, current_target_color)
        
        # 3. Wait for a winner (on_message will handle it)
        # We set a 10-second timer for the round
        start_time = time.time()
        while round_winner is None and (time.time() - start_time) < 10:
            time.sleep(0.1)
            
        # 4. Announce if time ran out
        if round_winner is None:
            client.publish(WINNER_TOPIC, "Time's up! No winner.")

        # 5. Pause before next round
        time.sleep(3)
```

**Explanation:** The server controls the game's state. It uses the `round_winner` variable as a "lock" to ensure only one winner is registered per round. The `on_message` function is triggered by any message on `IDD/game/hunt/player_found`. It immediately checks if `round_winner` is `None`. If it is, this player is the first and becomes the winner. Any subsequent messages that arrive for that same round are ignored.

-----

#### Pi (`player.py`)

The player code's logic is split between listening for game commands and checking its own sensor.

```python
# --- Global variables for game state ---
current_target_color = None
i_have_won_this_round = False # Prevents spamming the "found" message

# --- Simple color-matching logic ---
def check_color_match(r, g, b, target_color):
    MIN_CLEAR = 60 
    c = r + g + b
    if c < MIN_CLEAR:
        return False

    RATIO = 1.45

    if target_color == "RED":
        return (r > g * RATIO) and (r > b * RATIO)
    if target_color == "GREEN":
        return (g > r * RATIO) and (g > b * RATIO)
    if target_color == "BLUE":
        return (b > r * RATIO) and (b > g * RATIO)
    return False

# --- Callback for messages from the Game Master ---
def on_message(client, userdata, msg):
    global current_target_color, i_have_won_this_round
    
    payload = msg.payload.decode()
    
    if msg.topic == MASTER_TOPIC:
        # A new round has started!
        current_target_color = payload
        i_have_won_this_round = False # Reset our "won" flag
        print(f"*** New Target: Find [{current_target_color}]! ***")
        
    elif msg.topic == WINNER_TOPIC:
        # Round is over
        print(f"*** Game Status: {payload} ***")
        current_target_color = None # Stop sensing until next round

# --- Main Sensing Loop ---
try:
    while True:
        # Only check the sensor if there is a target and we haven't won yet
        if current_target_color is not None and not i_have_won_this_round:
            
            r, g, b, c = apds.color_data
            
            if check_color_match(r, g, b, current_target_color):
                print(f"MATCH FOUND! I see {current_target_color}!")
                
                # Set our flag to true so we don't send multiple messages
                i_have_won_this_round = True 
                
                # Publish our "I WON" message!
                client.publish(PLAYER_TOPIC, PLAYER_NAME)
        
        time.sleep(0.1) # Loop delay
```

**Explanation:** The Pi client is a state machine. It waits (looping `while current_target_color is None`). When `on_message` receives a color on the `MASTER_TOPIC`, it sets `current_target_color`, which activates the sensing logic in the main `while` loop. The Pi then continuously checks its sensor. If it finds a match, it sets `i_have_won_this_round = True` (to stop itself from sending more messages) and publishes its name to `PLAYER_TOPIC`. It then waits for the `WINNER_TOPIC` message to know the round is over, at which point it resets `current_target_color = None` and waits for the next round.

## 4\. User Testing

We tested our game with two users from another team.

**Screen Recordings**

https://github.com/user-attachments/assets/badba2af-08f1-4287-ba0d-273a12af5cdd

**Screenshot of game master**
<img src="https://github.com/user-attachments/assets/1c72b464-78cf-44d3-b5a8-34b87794b98c" />

> **Caption:** Users and frantically searching for a color object during our user test.

  * **What did they think before trying?**

    > "They were a bit confused about how the Pi would know what color it was seeing. They thought it would be slow or inaccurate. They seemed to think it was a trivia game, not a physical race."

  * **What surprised them?**

    > "They were most surprised by the speed and responsiveness of the sensor. The moment they put the correct color in front of it, the game registered it. They also loved the competitive, real-time aspect and how it made everyone jump up and run around. One user said, 'I can't believe how fast it is... it's actually stressful\!'"

  * **What would they change?**

    > "Their main feedback was to add more colors, like 'Yellow' or 'Purple', which would be harder to find. They also suggested adding a scoreboard to keep track of points over multiple rounds. One user suggested that instead of just 'GREEN', the server could ask for 'DARK GREEN', making the sensor challenge harder."

## 5\. Reflection

  * **What worked well?**

    > "The core game loop and MQTT messaging worked perfectly. The server's logic for using a `round_winner` variable as a 'lock' was very effective at handling the race condition of multiple players 'buzzing in' at nearly the same time. The color sensor was also surprisingly accurate for basic R, G, B detection, making the game playable and fun."

  * **Challenges with distributed interaction?**

    > "The biggest challenge was managing the game 'state.' All players and the server had to be in sync. We solved this by making the server the single 'source of truth.' The server is the only one that can start a round (by publishing to `master`) and end a round (by publishing to `winner`). The Pis are 'dumb clients' that just react to these two topics. This prevented the Pis from getting out of sync with each other."

  * **How did sensor events work?**

    > "We didn't use interrupts. Instead, the Pi client runs a continuous `while True` loop that actively polls the sensor. This 'polling' method was simple and effective. The game state (the `current_target_color` variable) acts as a switch: if it's `None`, the loop does nothing. If it's a color (e.g., 'RED'), the loop actively reads the sensor and checks for a match. This was much simpler than trying to manage sensor event interrupts."

  * **What would you improve?**

    > "First, we would implement the users' suggestion of a scoreboard. The server could keep a dictionary of player names and their scores, and publish it after each round. Second, we would improve the color detection logic (`check_color_match`) to be more robust. Right now, it's just simple thresholds. We could use a more advanced formula (like checking HSL/HSV values) to more accurately distinguish between, for example, 'Red' and 'Orange', or to add more complex colors like 'Yellow'."


