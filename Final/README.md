# Final

**Sean Hardesty Lewis (solo)**

<img width="4800" height="1200" alt="compass_header" src="https://github.com/user-attachments/assets/5f3f92ad-1209-4c28-a7a7-38021389ba5a" />

I built a pair of "compasses" that point towards each other no matter where they are in a room. While standard GPS tools reduce social connection to Cartesian coordinates on a map, the Friend Compass uses relative RF signal strength (RSSI) and sensor fusion to provide a continuous, egocentric bearing toward a partner. It explores how relative directional cues foster a sense of presence, turning navigation into a "warm" game of hot-and-cold rather than a cold turn-by-turn instruction.

## Inspiration

Please note that this project is heavily inspired by [komugiko2000's](https://www.instagram.com/komugiko_2000/) animation for [ZUTOMAYO – Hunch Gray (Music Video)](https://www.youtube.com/watch?v=ugpywe34_30). You can click on the thumbnail below to watch the YouTube video and understand the inspiration. I highly recommend it!

<div align="center">
  <a href="https://www.youtube.com/watch?v=ugpywe34_30" target="_blank">
 <img src="https://img.youtube.com/vi/ugpywe34_30/maxresdefault.jpg" alt="Watch the video" width="640" height="360" border="10" />
</a>
</div>

## Background

I actually watched the above video a few years ago and was fascinated by the concept of a compass wristwatch that points to a friend. However, I didn't have the knowledge, resources, or ability at the time for how to even go about building it- and this was my best guess. Here is my sketch from 2022/2023:

<img width="2161" height="582" alt="image" src="https://github.com/user-attachments/assets/2209add0-8e25-47cb-83a4-d1714367e740" />

...and here is a sketch I made for this project (November 2025):

<img width="2305" height="773" alt="image" src="https://github.com/user-attachments/assets/b50572c7-32c5-4001-b8b9-b7752bb7c6cd" />


## Overview

### Part A: The Scope Pivot (Hardware)

I started this project with an extremely ambitious "hardware-first" mindset. The original plan was to build a pair of physical wristwatches driven by Femtoduinos, using tiny brushless motors to spin a physical needle. I spent the first week diving into the mechanics of absolute positioning and quickly realized I was spiraling into scope creep. Absolute position motors are surprisingly expensive, and standard DC motors have no idea "where" they are pointing without complex optical encoders. I tried stepper motors, but they are often capped at 180 degrees or require bulky drivers. I considered continuous rotation servos with slip rings, but mechanical drift became a constant enemy; without a closed-loop control system, the physical needle would eventually lose its orientation relative to "North," making the compass useless after just a few minutes of walking.

I realized that while a physical needle is cool, I was solving a mechanical engineering problem instead of the interaction design problem I actually cared about. I pivoted hard. I swapped the Femtoduino for a Raspberry Pi 5 and the physical motor for a digital display. This allowed me to focus on the actual hard problem: the invisible signal processing. While less "mechanical" than a moving needle, the digital display allowed for rapid iteration on the smoothing algorithms without worrying about the physical inertia or latency of a motor. It shifted the project from "How do I spin this gear?" to "How do I know where my friend is?"

Here is my original pitch:

<img width="960" height="540" alt="idd_compass_s1" src="https://github.com/user-attachments/assets/2079abfc-df33-4493-8e58-43e7eb9de477" />
<img width="960" height="540" alt="idd_compass_s2" src="https://github.com/user-attachments/assets/58b91adb-99eb-4e30-a905-ab2732763a20" />

### Part B: The Signal Problem (RSSI vs. Reality)

Here is some of the different routes that were tested but ultimately not gone down.
From left to right:
- Pair of servo motors. While stepped variants exist they are often not continuous, and most continuous versions do not have a bearing.
- GPS Breakout. This didn't work at all indoors and when it connected to satellites outside, location was too brittle.
- Rotary encoder. This was just to test rubber band between a servo motor and the encoder. Interesting concept but bad execution.

  <img width="960" height="540" alt="idd_compass_tried" src="https://github.com/user-attachments/assets/b673298b-678a-4524-b47d-9e0f3337153a" />

The core technical challenge was calculating direction using Wi-Fi signals. My initial instinct was to use a GPS module on the Pi. I thought, "Satellites know where everything is, right?" I was wrong. The GPS modules were incredibly brittle, failing completely indoors (where most social interaction happens) and requiring a clear view of the sky to get even a 10-meter accuracy radius. For a "room-scale" interaction, 10 meters of error is useless, you could be in the kitchen while the compass says you’re outside.

So, I looked at what was already in the air: Wi-Fi. I shifted to using RSSI (Received Signal Strength Indicator) over a shared Wi-Fi network to estimate proximity and direction. I hypothesized that I could triangulate position based on signal strength (I did my undergraduate degree in Mathematics and Bellman's Lost in a Forest navigation problem was by far my favorite- but that is more geometric than this). The "Moment of Truth" came when I set up the two Pis on opposite ends of my apartment. I wrote a script to make the "Seeker" Pi scan for the "Target" Pi's unique beacon packets. I watched the console logs: RSSI: -45dBm, RSSI: -60dBm. It was working! The numbers moved as I moved. But they were pretty messy.

Here is a diagram of the pivoted architecture, moving from raw hardware to a sensor-fusion software approach:

<img width="4096" height="1962" alt="compass_new_diagram" src="https://github.com/user-attachments/assets/5fc7f168-f00a-4272-945b-55b91c463eec" />

### Part C: The Mess

However, seeing numbers on a console screen and getting an arrow to point at a person turned out to be two completely different realities. The gap between "I have data" and "I have a compass" was massive and filled with physics problems I hadn't anticipated. When I first hooked the RSSI data directly to the visual arrow, the result was a catastrophe. The arrow didn't point at my friend; it seized violently, vibrating back and forth across 180 degrees, or spinning in circles even when both devices were sitting perfectly still on a table.

I discovered that indoor environments are essentially "Halls of Mirrors" for radio waves. This is called Multipath Interference: signals bouncing off walls, floors, and metal desks, creating noise that makes a static device look like it's teleporting. Even a hand covering the antenna can drop the signal strength significantly, throwing off the calculation. The signal from my friend's device wasn't just coming in a straight line; it was bouncing off nearly everything around it. Sometimes a reflected signal was stronger than the direct line-of-sight signal because the direct path was blocked by my own body (maybe since humans are mostly water, and water blocks 2.4GHz waves effectively?). The compass would confidently point at a metal cabinet because that's where the strongest reflection was coming from. I first tried to solve this with machine learning regression, feeding it raw data to "learn" the room, but the environment was too dynamic. Moving a chair or opening a door changed the RF landscape completely.

The breakthrough came when I realized I couldn't rely on RF alone for direction. I needed to know what the device itself was doing. If the signal strength dropped, did my friend run away, or did I just turn my body? To answer this, I integrated an IMU (Inertial Measurement Unit) but I discovered it didn't have a magnetometer (compass chip), only a Gyroscope and Accelerometer. This meant the device had absolutely no idea where "North" was. It was blind to the world, only knowing how fast it was spinning. However, this was useful for the compass to know if we were "turning our body" and essentially could ensure that rotating the device keeps the needle still pointing in the same consistent direction with the IMU readings.

Since we could solve rotating in place, the biggest thing left was accuracy of the needle. Multipath inference was the boss of all bosses- to which I was stumped. Thankfully, real lifef comes to save us sometimes. Reggie Nintendo visited our campus the next day and reminded me that the Wii existed, and specifically Wii Sports Resort and the Wii Balance Board. I remembered something that every person who owned a Wii went through- and wondered if it could be applied to my own setting. Custom calibration the very first time you set it up. So I implemented a "Calibration" startup sequence. When we start using our compass, the user spins around their friend in a slow 360-degree circle. The system maps the RSSI strength and how it changes in that dynamic environment. It identifies the angle where the signal was strongest (the "Peak") and defines that virtual angle as "Friend." From that moment on, the system relies entirely on a calibrated environment that is custom to the person, and not some generic model from a completely different env. This smoothed the experience drastically. While RSSI and multipath inference were still issues, they were noticably less aparrent with the needle stopped jumping to reflections because it was anchored to that initial calibration scan. It wasn't perfect, since there was no magnetometer to correct it, and sometimes Gyro drift would eventually creep in, but it transformed the device from a broken random number generator into something that felt stable, heavy, and intentional.

Here is what the device looked like with needle pointing in direction of a friend:

<img width="2037" height="804" alt="compassespointing1" src="https://github.com/user-attachments/assets/42f23608-ee26-48ec-b801-6b35d0986fb2" />

### Part D: The Interaction

Observations

Despite the brittleness of the underlying signal, the interaction feels magical when it works. In a confined, open environment (like a large living room or lab without heavy metal interference), the compass can usually reliably point toward the partner device, with some drift/interference (it is impossible to get rid of all interference with Wi-Fi).

In an open room without too many obstacles, when you turn the device and the arrow spins to lock onto your friend, it feels genuinely alive. It feels like a magnetic pull. Users immediately understood the "game" of it without explanation. However, the system falls apart in predictable, physics-based ways. Even with the smoothing, Multipath Interference is a persistent enemy. In the Maker Lab, which is full of metal desks and equipment, the signal would sometimes bounce so hard that the "Peak" during calibration was actually a reflection off a wall, leading the user confidently in the wrong direction. I also found that the human body is a giant blocker; simply holding the device close to your chest (or enclosing the wifi sensors with your hands) could drop the signal strength by 10dBm, making the compass think your friend just sprinted 20 feet away.

Users

Thinking like a user, I realized that "accuracy" matters a bit less than "responsiveness." If the needle jumps around wildly (which raw RSSI data does), the user thinks the device is broken. If the needle moves smoothly but is slightly wrong, the user thinks they are reading it wrong or that it's "calibrating" (or like some users pointed out, were convinced that it was accurate and justified reasons for the needle's direction). I leaned into this. I implemented a heavy filter that trusts the Gyroscope for short-term rotation and ignores sudden, impossible jumps in RSSI signal. This makes the needle feel heavy and intentional, rather than jittery and digital. Users described this as feeling more like a "magnetic" compass, which was exactly the socio-affective vibe I wanted.

The "Pirates of the Caribbean" effect is real. Users noted that because the device is "alive" (constantly updating), their brains do a lot of the work. If the needle points generally in the right direction, the user feels a connection. The smoothing algorithms helped here immensely; by damping the rotation, the compass feels like it has weight and inertia, making it feel less like a glitchy computer and more like a physical object.

Here are some top-down photos of the compass:

<p align="center">
  <img src="https://github.com/user-attachments/assets/9e485272-d365-459f-a2f7-c7624004136e" width="45%" />
  <img src="https://github.com/user-attachments/assets/53e4c728-707e-4839-a466-9d2d334b77e6" width="45%" />
</p>

Here is a video of the compass when it is navigating towards its friend:

https://github.com/user-attachments/assets/ea61648a-68ff-4d69-92d7-91f7e831c4e8

Here is a video of the compass when it is near its friend:

https://github.com/user-attachments/assets/d746280c-711a-43e1-8f6f-bfefe4ae0745

### Part E: Lessons

I realized that the interaction worked best when I treated it as "Calm Technology." It shouldn't scream at you. It should just be.

| Question | Answer |
| :--- | :--- |
| **What can you use X for?** | The Friend Compass is used for maintaining a peripheral sense of connection. It allows you to find a friend in a crowd or a large venue without staring at a map app or texting "wya". |
| **What is a good environment for X?** | Open indoor spaces, line-of-sight scenarios (like a warehouse party or gym), or wood-framed houses where RF passes through walls easily. |
| **What is a bad environment for X?** | Metal-heavy labs (Faraday cage effect), dense concrete buildings, or incredibly crowded Wi-Fi environments (like a convention center) where packet loss is high. |
| **When will X break?** | It breaks when Multipath Interference overwhelms the filter (e.g., standing next to a large metal fridge) or when the devices hand-off to different Wi-Fi access points. |
| **When it breaks how will X break?** | The arrow will drift aimlessly (due to Gyro drift) or lock onto a "reflection" of the signal (like a wall) rather than the true source. |
| **What are other properties/behaviors of X?** | The "weight" of the needle is programmable. I can make it twitchy and reactive (good for tracking fast movement) or heavy and slow (good for general direction). |
| **How does X feel?** | It feels like a "living" artifact. The needle has a "magnetic" pull towards your friend. It feels playful, slightly mysterious, and warm. |

#### What worked and what didn’t
The Wins: The pivot was the biggest win. Moving away from hardware mechanics to software signal processing saved the project. The "vibe" was also a huge success. Even when the compass was technically inaccurate (pointing 15 degrees off), users didn't care. They corrected their path naturally, like playing "Hot and Cold." The visual feedback of the needle rotating smoothly (thanks to the Gyro) made the device feel high-quality, masking the noisy data underneath.

The Misses: RSSI is barely usable for precision. It is incredibly sensitive to the environment. The "GPS" idea was a total failure indoors. Also, the lack of a magnetometer means the device suffers from Gyro Drift over time. If you use it for 10 minutes straight without re-calibrating, "North" will slowly drift to the left or right, and the arrow will lose its accuracy.

#### Lessons for making it more autonomous
The biggest lesson was that filtering creates reality. The raw data says the friend is teleporting around the room. The filter says the friend is standing still. The user believes the filter. For a device to feel "smart," it doesn't need perfect sensors; it needs a model of the world that rejects impossible data.

I also learned that "calibration" can be a feature, not a bug. Asking the user to calibrate the device creates a ritual that builds trust in the machine. It makes the user an active participant in the sensing loop.

#### What I’d do next
The first thing I’d change is the radio. LoRaWAN is the answer. Wi-Fi is designed for Netflix, not ranging. LoRa modules (like the SX1280) have Time-of-Flight (ToF) capabilities that measure how long a signal takes to travel, which is infinitely more accurate for distance than measuring signal loudness (RSSI).

Second, Haptics. I want to integrate vibration motors. As you get closer to your friend, the watch should pulse like a heartbeat (The "Tell-Tale Heart" effect). This allows for eyes-free navigation, you could find your friend with your hands in your pockets.

Third, Magnetometer. I would absolutely ensure the next iteration has a working magnetometer. Relying solely on the Gyro creates a "time limit" on usage before drift makes it unusable. A 9-axis IMU (instead of 6-axis) is a requirement for version 2.

Here is a longer format video of the Friend Compass in action, showing the "seeking" behavior and its spin interaction on finding the friend. Thanks to Sebastian Bidigain for testing it out!

https://github.com/user-attachments/assets/76d5e89e-605a-4976-9143-8b986f3f2893

### Discussion

| Person | Viewpoint |
| :--- | :--- |
| **Sebastian Bidigain** | Thinks the concept is fantastic. He revealed he had a similar idea for a "festival wristband" using LoRaWAN and LED rings. He was impressed I managed to get a prototype working with just Wi-Fi RF, noting that existing commercial solutions (like Totem Compass) usually require extremely close range. He validated that moving to LoRa is the "smart way to go" for the future. |
| **Bil de Leon** | Jokingly called it "the future." He compared it to the compass in *Pirates of the Caribbean* that points to "what you desire most." He was skeptical of the accuracy, wondering if the "placebo effect" made him believe the needle was more accurate than it was, but admitted the smooth rotation made it feel convincing. |
| **Anonymous** | Found the interaction "playful." She noted that unlike a map, which demands your full attention, this device allows you to look around the room. She liked that it didn't give a distance number (ex. "10 meters"), but rather a feeling of direction, which felt more human. |

## Code Pipeline

```
[Receiver Pi (Target/Mirror)]                                 [Root Pi (Seeker/Compass)]
      (Runs beacon.py + mirror.py)                                     (Runs compass.py)
                  │                                                             │
                  │ 1. Emits UDP Beacon (:50050)                                │
                  │ "I am here!"                                                │
                  └────────────────────────────────────────────────────────────>│
                                                                                │
                                                                       [compass.py]
                                                                       2. Sniffs packets on wlan1 (Left)
                                                                          & wlan2 (Right) via Scapy.
                                                                       3. Fuses RSSI Delta + Gyro.
                                                                       4. Updates local Screen.
                                                                       5. Broadcasts Result via UDP.
                                                                                │
                  │                                                             │
                  │ 6. Receives Angle Data (:55555)                             │
                  │ <───────────────────────────────────────────────────────────┘
                  │
             [mirror.py]
             7. Calculates Inverse Angle (Angle + 180°).
             8. Renders "Mirror" arrow to screen.
```

## Components

### 1) `beacon.py`
* **Run on:** **Receiver Pi** (The Target).
* **Purpose:** Emits a "heartbeat" RF signal.
* **How it works:** It broadcasts small UDP packets (`RECEIV_BEACON_V1`) to the local network broadcast address (`255.255.255.255`) on port **50050** every 0.1 seconds.
* **Why:** This creates the constant radio noise that the Root Pi needs to track. By running this on the Receiver Pi, the Receiver becomes the physical "Friend" that is being tracked.

### 2) `mirror.py`
* **Run on:** **Receiver Pi** (The Target).
* **Hardware:** HDMI Monitor (I didn't have a second PiTFT screen).
* **Purpose:** The "Magic Mirror" display.
* **Logic:** It listens on port **55555** for status updates from the Root Pi. When it receives an angle (ex. "Friend is at 90°"), it calculates the reciprocal angle (270°) and displays it. This ensures that if the Compass points at the Mirror, the Mirror points back at the Compass.

### 3) `compass.py` (The Brain)
* **Run on:** **Root Pi** (The Seeker).
* **Hardware:**
    * **2x Wi-Fi Interfaces:** `wlan1` (Left Ear) and `wlan2` (Right Ear) in monitor mode.
    * **IMU:** LSM6DS3 (Gyroscope).
    * **Display:** ST7789 (SPI 1.3" Screen).
* **Purpose:** Performs the sensing and sensor fusion.
* **Logic:**
    * **Sniffing:** Uses `scapy` to capture the `beacon.py` packets emitted by the Receiver.
    * **Direction:** Compares signal strength between the Left and Right Wi-Fi antennas (`wlan1` vs `wlan2`) to determine direction.
    * **Fusion:** Blends this RF data with Gyroscope readings to smooth the motion.
    * **Broadcast:** Sends the calculated state `{angle, spin}` back to the Receiver so the Mirror stays in sync.
 
### 4) `calibrate.py` (Active Learning)
* **Run on:** **Root Pi** (The Seeker).
* **Purpose:** Trains the navigation model in real-time.
* **Workflow:**
    1.  **Bootstrap:** You record 3 baseline points (Center, Left 90, Right 90).
    2.  **Free Roam:** You walk around. If the needle is correct, you press `y` (reinforcing the model). If wrong, you press `n`.
    3.  **Save:** Generates a `.pkl` checkpoint file that `compass.py` can load.

### 5) `calibrate_spin.py` (Proximity)
* **Run on:** **Root Pi** (The Seeker).
* **Purpose:** Defines the "Arrival" zone.
* **Workflow:** You stand at the distance where you want the "Friend Found" spin animation to trigger. The script records the signal strength at that distance and saves it to `checkpoints/spin.json`.

### 6) `udp_checker.py` (Tooling)
* **Run on:** Either Pi (for debugging).
* **Purpose:** Verifies that the UDP broadcast packets are actually making it across the network, which is critical since the entire system relies on connectionless UDP for low latency.

## Default Ports & Addresses

* **Beacon Signal (Receiver -> Root):** UDP `50050` (Broadcast).
* **State Sync (Root -> Receiver):** UDP `55555` (Broadcast).
* **Target MAC:** Hardcoded in `compass.py`. *Note: You must update `RECEIV_MAC` in the code to match the Wi-Fi MAC address of the Receiver Pi.*

## Notes

The `compass.py` script relies on **Stereo RF**. The Root Pi must have **two separate Wi-Fi interfaces** (`wlan1` and `wlan2`) enabled in monitor mode. This is achieved by plugging in two external USB Wi-Fi adapters. This hardware setup allows the code to compare `raw_rssi_left` vs `raw_rssi_right` simultaneously, enabling "Direction Finding" based on the signal differential (Stereo Phase/Amplitude) rather than just a single signal strength.

### Critical Setup Instructions

To make this work, you cannot just run the scripts. You must configure the hardware environment first.

**1. Monitor Mode is Mandatory**
The `compass.py` script requires raw access to radio packets. You must manually set your USB Wi-Fi adapters (`wlan1` and `wlan2`) to Monitor Mode before running the script.

```bash
sudo ip link set wlan1 down
sudo iw wlan1 set type monitor
sudo ip link set wlan1 up

sudo ip link set wlan2 down
sudo iw wlan2 set type monitor
sudo ip link set wlan2 up
```

**2. Network Synchronization**
For the sniffer to see the packets, all devices must be on the same frequency. Connect your internal Wi-Fi (`wlan0`) to a specific network, and ensure your monitor interfaces are tuned to that channel.

```bash
# Connect internal wifi to your hotspot
sudo nmcli dev wifi connect "YourNetworkName" password "YourPassword"
# You can set specific wifis for different receivers like so:
sudo nmcli dev wifi connect "YourNetworkName" password "YourPassword" ifname wlan#
# You can check what wlan# your receivers are by using `iwconfig`
```

**3. Preempting the Lab Boot Screen**
If you are using a shared lab Raspberry Pi that has a default "System Info" screen running on boot, it will block access to the SPI display. You must kill this service before running the compass.

```bash
sudo systemctl stop screen-boot.service
# Or if running manually:
pkill -f "python.*screen_boot_script.py"
```

## AI Disclaimer

I used AI coding assistance (GitHub Copilot) to generate the `scapy` packet sniffing logic in `compass.py` and the `pygame` rendering boilerplate in `mirror.py`. The sensor fusion math (weighted averaging of RSSI delta and Gyroscope integration) and the distributed "Beacon/Mirror" architecture were implemented mostly manually to ensure low latency.

## Pictures of the robot

<table>
  <tr>
    <td>
      <img src="https://github.com/user-attachments/assets/3f095ea5-4396-4ae5-8052-7402fe28fc14" alt="1_finished_IMG_5726" width="100%"/>
    </td>
    <td>
      <img src="https://github.com/user-attachments/assets/d16ea9d6-74cd-4e93-91cd-1c52610657d0" alt="2_finished_IMG_5726" width="100%"/>
    </td>
  </tr>
  <tr>
    <td>
      <img src="https://github.com/user-attachments/assets/2e707e09-8f39-4ee3-a217-b9e7d04e1a3c" alt="3_finished_IMG_5726" width="100%"/>
    </td>
    <td>
      <img src="https://github.com/user-attachments/assets/bed0d4a0-06fc-47d0-91f0-a618bf0823fd" alt="4_finished_IMG_5726" width="100%"/>
    </td>
  </tr>
</table>

## Credits

Special thanks to **Sebastian Bidigain** for the critical feedback on RF protocols and the wristband concept validation, and **Bil de Leon** for the user experience testing and "Pirates" comparison. Also thanks to the Maker Lab staff for letting me run around the room endlessly to test signal drops. Also, special thanks since this is the final project of the semester to **Albert Han**, **Hauke Sandhaus**, and **Wendy Ju** for making this class really awesome. I loved getting to prototype my random ideas and seeing them come alive, and really appreciate all the hard work that they put in behind the scenes!
