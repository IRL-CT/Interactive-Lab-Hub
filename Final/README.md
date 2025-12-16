# Final

**Sean Hardesty Lewis (solo)**

<img width="4800" height="1200" alt="compass_header" src="https://github.com/user-attachments/assets/5f3f92ad-1209-4c28-a7a7-38021389ba5a" />

I built a pair of "compasses" that point towards each other no matter where they are in a room. While standard GPS tools reduce social connection to Cartesian coordinates on a map, the Friend Compass uses relative RF signal strength (RSSI) and sensor fusion to provide a continuous, egocentric bearing toward a partner. It explores how relative directional cues foster a sense of presence, turning navigation into a "warm" game of hot-and-cold rather than a cold turn-by-turn instruction.

## Overview

### Part A: The Scope Pivot (Hardware)

The original vision for this project was ambitious: a Femtoduino-driven watch with a physical brushless motor spinning a needle. I quickly realized this was extreme scope creep. Absolute position motors are expensive, and standard DC motors require complex encoders to know where they are pointing. I tried varying approaches like using a stepper motor (limited to 180 degrees) and a continuous brushless motor but mechanical drift was a constant enemy. Without a closed-loop control system, the physical needle would eventually lose its orientation relative to "North," making the compass useless.

I pivoted to using a Raspberry Pi 5 with a digital visualization. This allowed me to focus on the actual hard problem: the signal processing. While less "mechanical" than a moving needle, the digital display allowed for rapid iteration on the smoothing algorithms without worrying about the physical latency of a motor.

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

The core technical challenge was calculating direction using Wi-Fi signals. I initially hoped to use a GPS module, but it was incredibly brittle, failing completely indoors and requiring open sky. I shifted to using RSSI (Received Signal Strength Indicator) over a shared Wi-Fi network to estimate proximity and direction.

I learned the hard way that RSSI is extremely fickle. It suffers heavily from Multipath Interference: signals bouncing off walls, floors, and metal desks, creating noise that makes a static device look like it's teleporting. Even a hand covering the antenna can drop the signal strength significantly, throwing off the calculation. To combat this, I implemented a complementary filter. I used the Raspberry Pi's IMU (Gyroscope/Magnetometer) to stabilize the "needle." The compass relies on RF for the long-term trend but uses the Gyro to handle short-term movements, preventing the needle from jittering wildly with every packet drop.

Here is a picture showcasing the **Sphero Ollie (left)** and **Sphero BB-8 (right)**, both robots can be controlled manually via the smartphone app 'Sphero EDU'. Neither have any sort of autonomous capabilities or cameras, that's what I wanted to add.

![IMG_5722](https://github.com/user-attachments/assets/6af0b38b-35bc-4eb6-aa50-4afcba365ad2)

### Part C: The Interaction

Despite the brittleness of the underlying signal, the interaction feels magical when it works. In a confined, open environment (like a large living room or lab without heavy metal interference), the compass reliably points toward the partner device.

The "Pirates of the Caribbean" effect is real. Users noted that because the device is "alive" (constantly updating), their brains do a lot of the work. If the needle points generally in the right direction, the user feels a connection. The smoothing algorithms helped here immensely; by damping the rotation, the compass feels like it has weight and inertia, making it feel less like a glitchy computer and more like a physical object.

Observations

Where the system shines is the most common case: indoor lighting that isnt ridiculous, a single person 1-3m away, and a floor that isnt slippery. In these conditions, robot feels responsive and accelerates forward when the human is in view of the camera. However, it falls apart in predictable places. Backlight and low light (especially nighttime) makes YOLO break or hallucinate. More than one person and even temporary occlusions encourage target switches (and I thought it was out of scope to put effort into coding stickiness to the last seen person). Glossy floors were a completely unexpected issue- I found that the Ollie could slip on quick turns and then overshoot even if the perception was fine. I had to tone down the speed of accel/decel and the rotation just for this floor issue. The FOV of the camera was also interesting since my settings I used for webcam definitely did not translate perfectly to the FPV camera (more on this later).

Users

Thinking like a user, I realized very few people are aware theyre interacting with a probability distribution and not a robot. If the robot stops randomly, they dont see "low confidence", they just see weird behavior. I thought about using Sphero v2 API and potentially adding LED cues to make state legible (i.e. blue when it’s confidently tracking you, yellow when it’s searching, red when it stops for safety) but realized that this didn't transfer well across different Sphero models and I sort of wanted to make a "model-agnostic" camera/robot control code. I also realized that the starting and stopping were way too violent for users, and ended up softening behavior to be a lerp between accel and decel when it loses track of human/gains sight, instead of just an immediate stop or start. Finally, I replaced my naive "always correct to perfect center of camera" approach with bigger and more friendly dead-zone. If you’re approximately centered in the shot, it holds its course so it doesnt feel like its constantly hunting for a pixel-perfect alignment (rotating left and right and left and right...).

Here are some of the failures of the robot (Please note, this is after the FPV camera was attached for part 2. This is just to showcase some of the failures that are described above, like overrotating, glossy floors, accelerating into walls, and the like)

https://github.com/user-attachments/assets/0f6dcfd1-2ecd-4f9b-86b2-35c0f42ef667

### Part D

To describe my setup again, I used a PC webcam and my location and size on the webcam defined how the robot would accelerate, decelerate, and rotate. This made debugging a very interesting process of having to pick up the Sphero, take it to the end of the room, then face the camera and watch how my location/size on camera would affect the Sphero's movement in each iteration of the script. I realized that this setup worked best with plain bright indoor environments (with flat ground) and was bad with backlit hallways, dark lighting. When it breaks (and it broke often), it was often due to detection failing or my programming of the robot's behavior was not great. Most failures were recoverable by adjusting the code for its behavior, but detection being reliable was much more-so lighting conditions. Biggest fixes for this part were adding smoothing to speed and dead-zones for human being in center of frame so that the robot comes directly towards you and slightly rotates if you are off to one side. It felt kind of personable and the first time it did it I felt really happy when I saw the arc that it curved in to get to me- realizing that it could sort of navigate autonomouslyish.

| **Question** | **Answer** |
|---------------|------------|
| **What can you use X for?** | We can use our pet robot to provide companionship. We do not need to feed it or worry about taking care of it, and can enjoy a socio-affective relationship. |
| **What is a good environment for X?** | Good environments for the pet robot are generally well-lit areas for vision with non-slip surfaces for navigation, and only one human actor visible. |
| **What is a bad environment for X?** | Bad environments are dark areas, slippery floors, or have many human actors to detect and follow. |
| **When will X break?** | The pet robot will break when it gets stuck underneath chairs, beds, cabinets, etc. and needs to be retrieved. It also breaks in all of the bad environments described above, and especially breaks with high-latency instructions. |
| **When it breaks how will X break?** | When it breaks, the pet robot will be immobile (unable to escape a stuck position), will hop from person to person in a crowd, or will generally just not be responsive enough for a quality interaction (in high-latency settings). |
| **What are other properties/behaviors of X?** | The pet robot's behaviors need to be explicitly programmed. The width of the dead-zone for how much it rotates to keep a human centered in its vision, the speed and acceleration it uses, its stopping distance from the human, and its default mode (searching by rotating in circles) are all adjustable settings that make the robot interactable and animated. |
| **How does X feel?** | The pet robot, under low-latency settings, feels like a puppy that chases you around. It constantly nips at your feet and follows you everywhere you go. It is quite an adorable experience with the Sphero frames being designed to appear friendly to even children, so it following you isn’t anything scary. |

I believe that there are quite a few videos to refer to for this section: namely the working demo below, and the breaking demo above.

### Part 2.

For Part 2 I wanted to take what I had managed to do: a proof of concept/prototype on the PC using its webcam and the Sphero, to a real usable autonomous robot. Thankfully, I had some of the materials for the job already in my closet. I had a tiny FPV camera, a 5.8G OTG Skydroid Receiver, and a set of 6 200mW batteries, as well as some scotch tape. 

Here is a diagram of how I envisioned my robot to work after I switch from a PC webcam to a small FPV camera that goes on the robot.

<img width="1123" height="813" alt="image" src="https://github.com/user-attachments/assets/602d3eb7-2524-46c5-ba10-7cf64f3c2f3a" />

So the first thing I did was test out the FPV camera by plugging it into one of the batteries, then plugging in the receiver to my PC, and loading up VLC's Media > Open Capture Device to see if the receiver was getting anything. A "USB 2.0 Camera" showed up in the dropdown and when I clicked on it: total static and a completely unusable video feed! This is completely normal. I remember from the last time that I used this FPV camera that I had to tune it to a specific channel for the sender (camera) and receiver (PC) to be able to operate on the same wavelengths. After debugging for about an hour with many static and half-static video feeds being shown on my screen, I realized that half of my problem was really the connection signal from the receiver to the camera itself. FPV cameras are built with antennas meant for large open-space environments (to be retrofitted onto drones). So, using it indoors where there is lots of metal and other interferences gave a bunch of static noise to the video feed (and especially for me, since my PC was directly underneath a metal desk!). To fix this, I cleared the area around the camera and moved my PC out from underneath the metal desk. Suddenly, more channels started working with less noise and glitches. I found channel F4 to work the best for the camera and receiver to be able to communicate a smooth video on that VLC was able to receive.

The second thing I did was scotch tape the battery and the FPV camera to the front of the Sphero Ollie. It looked a little bit unpolished, and the battery would need to be untaped and replaced every 20min with a new one, but it got the job done. From there, I replaced my previous code's camera input from index 0 (my webcam) to index 1 (the USB 2.0 camera receiver). This was the moment of truth, and I hit the "Start" button on my script- only to realize that my 20 minutes had already expired and the battery had died and needed to be replaced. Once I unscotched the camera, reconnected the wires, and came back to my PC I first tested VLC and made sure the feed was working correctly, then for my second moment of truth- the robot started moving based on the camera feed that was transmitting from the FPV camera taped to it! I was so happy that I got it to work and how it moved towards me. I played around with it for the next 20 minutes and recorded what it was bad and good at. I quickly realized that when it lost track of the human, or when it got too close to the human (and consequently lost track), it had no idea what to do and essentially just stopped moving completely becoming inanimate. I didn't like this behavior since it went against the core of what I wanted it to feel: alive. So, my first order was to define a "Search" mode in which the robot would continuously move in a circle or something of the sort when it didnt see any human on the camera feed so that it would "find" a human. What I didnt realize is that this would lead to a whole lot more crashing, scuffs, and unintended movement than what I originally thought- but it definitely looked, and felt, more alive!

Here are everything I used above to create the robot:

<img width="1920" height="1080" alt="lab5_tools" src="https://github.com/user-attachments/assets/9f9822eb-2765-4120-97ef-ac26b4cad060" />

A major problem I had to deal with was the fact that the receiver was in my PC and the PC was directly controlling the robot. This essentailly made the robot unusable outside of my room since the range of my PC's bluetooth was only so far. I researched into whether the robot could be controlled over Wi-Fi and unfortunately it could not. So, I tried using the Raspberry Pi again for the receiving of the camera stream and CV analysis and movement instruction based on it. However, it was readily apparent that the RPI was not suited for such a computational task averaging only 1-3 fps as opposed to my PC's >30 fps. So I had to devise a different solution to make this robot semi-portable. My RPI would act as a controller and connection to the robot. It would pass the video stream to a localhost:#### which the PC could then read and perform CV detection on. Then, the PC would pass instructions back to which the Pi could read and apply to the robot. I implemented a basic version of this with Cloudflare's free tunneling system (similar to the local-tunnel package but more versatile).

The final system splits the job in a way that plays to each device’s strengths. The Ollie and Pi stay together; the Pi handles Bluetooth to the robot, sends the video stream to PC, and listens for commands over UDP. The camera stream rides the same network path to the desktop, which does detection, tracking, and control mapping. Commands are tiny, frequent, and timestamped so the Pi can ignore anything stale and brake if something errors. I set extremely conservative speed limits (these Spheros can go fast!), with what I thought was a comfortable following distance, as well as confidence floor that slows robot subtly when vision is sketchy.

Below is a short demo.

https://github.com/user-attachments/assets/d25c7462-78bb-4aa5-97b3-052394c6d728

### What worked and what didn’t

The biggest wins were exactly the things you’d expect. Offloading vision to the PC made everything snap into place, and moving from HTTP to UDP over Tailscale got rid of the mystery delays that made the robot feel almost unusable. Confidence-aware gains were a subtle but extremely quality of life fix, with a lerp in slowing down when detector is unsure. The obvious misses were also predictable. The Pi-only pipeline wasn’t even close to real time, so it never felt very interactive. Cloudflare’s tunnel was great for convenience but introduced just enough buffering to ruin the experience. The BB-8 form factor was adorable but unforgiving once I added a camera and battery (weight would always tilt it to one side), the Ollie’s flat stance is simply better for this payload.

I realized that my above end-to-end fixes like HTTP-UDP were good, but didn't account for general Wi-Fi speed and inter-Wi-Fi latency. So while the end-to-end works for the same Wi-Fi network, even the half-second delay over Wi-Fi as soon as we move the setup across Wi-Fi networks that interact makes the experience subpar. Since the robot moves and needs to re-calculate on the fly where it is going, the end-to-end being >0.5s leads to a very big performance hit in terms of how interactive the robot feels. If we set the speed of the robot down we can mitigate this latency, but the entire interaction gets slowed down as a result. See below for a video of the robot running in the Maker Lab with very jittery end-to-end latency due to different Wi-Fi networks. Even with UDP, this is a challenge. I am open to suggestions for how to improve this in a way that doesn't change the behavior of the robot to be slower so that it can adjust to delayed instructions.

https://github.com/user-attachments/assets/61803de7-fe3a-493a-a4fb-d03df16f09a3

### Lessons for making it more autonomous

The robot feels "smart" when the loop is consistently fast and its internal state is legible. That means explicit state transitions, search, lock, track, re-acquire, etc. rather than one giant controller fed by raw numbers. An easy improvement would be a little bit of identity memory so it doesnt jump to a new person when someone crosses the frame, with even a simple stickiness heuristic helping, or a small ReID embedding could help more. On the sensing side, using the bounding-box height as a distance proxy was the right hack for a first pass but obviously brittle, I imagine a front-facing ToF sensor fused with vision would immediately make spacing smarter. Some issues of it being autonomous were hallucinations and getting stuck. Sometimes it would detect a human where there aren't any and run straight into a wall. Or during searching it would crawl underneath a cabinet or bed and remain stuck there. It would actually get stuck very often underneath a table, bed, cabinet, etc. and I have to fish it out many times while debugging. Another issue that affected its autonomy and also the biggest non-obvious property I discovered was just how sensitive the movement was to jitter rather than just average latency. You could survive 70ms if its steady, but you cant survive sudden 200ms spikes even if your average is great (I was using Cloudflare's free tunnel service but realized it wasnt the most optimal compared to smoother operators like UDP). 

## What I’d do next

The first thing I’d change is the distance estimate. A VL53L1X ToF module on the front, fused with vision, would replace the bounding-box hack and immediately calm the approach behavior. After that, I would add a lightweight ReID head or at least a simple embedding to keep identity sticky in crowds. I think I've seen a duck on YouTube that [learned to follow its owner's red boots](https://www.youtube.com/watch?v=p-nXiHcZsY0) that I find adorable, and thats the kind of targetting I would aim for. On model side, I would love to test out a TensorRT-quantized nano detector and then track-then-detect between frames for even lower latency. On interaction side, I would make the gesture gate the default, try the shoulder-follow offset, and dress up the robot with a damped camera mount with an easily replaceable battery slot. Also, I think emotes and lightshows have been created for Sphero robots in the past, so maybe integrating that for personality.

Here is a longer format video of my pet robot that follows you around (left is FPV camera, right is what human sees).

https://github.com/user-attachments/assets/9f486826-e751-48cc-834f-3b95a3daea65

## Discussion

| Person | Viewpoint |
|---|---|
| **Sebastian Bidigain** | Thinks it’s “super cool” but also “super scary.” His initial reaction framed it as a potential “murder robot,” noting the same detection/tracking technologies appear in defense contexts (ex. government contractors like Palantir and Anduril outfitting drones to identify humans in active conflicts such as the Russia Ukraine war). After I clarified that this project detects humans only to follow them and provide socio-affective companionship, more like a friendly pet, he was relieved and appreciated the benign intent. |
| **Benthan Vu** | Loves the concept and the playfulness, but says the interaction “feels awful” when latency is high. On poor Wi-Fi, he experienced delayed updates that made following unreliable and unsatisfying. He still imagines future toys shipping with similar capabilities, maybe with less invasive sensing than cameras, so long as responsiveness stays consistently snappy. |
| **Anonymous** | Loves the idea and draws a connection to Daniela Rus’s vision of “turning anything into robots” (ex. “Maybe your chair or table could be robots. You could say, ‘Chair, come over here.’ Or ‘Table, bring me my cookies.’”). She was impressed that a manual toy became autonomous and that it could follow people even with heavy occlusion in the Maker Lab. Overall, she found it a compelling demonstration of adding intelligence to a simple, friendly form factor. |

## Code Pipeline

```
FPV Cam ──(5.8GHz RF)──> Skydroid USB Receiver
          └─> [camera_live.py]  : captures locally & re-broadcasts over HTTP (MJPEG/JPEG)
                     │
                     └─HTTP→  http://<cam-host>:7965/mjpeg/<index>  (or /snapshot/<index>.jpg)
                               │
                               v
                   [computeranalyze.py]  : YOLOv8 on GPU, outputs control
                     ├─ SSE → http://<pc>:7966/events  (control stream)
                     └─ UDP → <raspberrypi>:7970       (fast-path control, optional)
                                            │
                                            v
                   [raspberrypicontroller.py] : BLE driver @ ~66 Hz → Sphero Ollie/BB-8
```

## Components

### 1) `camera_live.py`  : low-latency camera rebroadcaster

- **Run on**: **PC or Raspberry Pi** (whichever has the Skydroid/USB receiver plugged in).  
  Keep this host physically **close to the FPV camera** for a clean RF link.
- **Purpose**: Capture frames from a local video device (`DEVICE_INDEX`, default `0`), keep **only the newest** frame, and **serve** it as:
  - `GET /` : minimal web UI (switch camera index, view stream)
  - `GET /mjpeg` : MJPEG of the **current** camera
  - `GET /mjpeg/{index}` : MJPEG for a **specific** device index
  - `GET /snapshot.jpg` and `/snapshot/{index}.jpg` : a single JPEG frame
  - `GET /raw`, `/raw/{index}` : chrome-less viewer pages
  - `GET /current` : JSON status (index, resolution, fps, last_error)
  - `POST /switch` : switch the **current** camera index
- **Defaults**:
  - Binds `HOST=127.0.0.1`, `PORT=7965`
  - Resolution `1280x720` @ `30fps` (override via env)
- **Notes**:
  - Uses a tiny, lock-free latest-frame buffer to minimize latency.
  - Auto-reaps idle per-index sources (`RAW_IDLE_SECONDS`).

**Example run**
```
HOST=0.0.0.0 PORT=7965 DEVICE_INDEX=1 VIDEO_WIDTH=1280 VIDEO_HEIGHT=720 VIDEO_FPS=30 \
python3 camera_live.py
# Preview: http://<cam-host>:7965/
# Stream:  http://<cam-host>:7965/mjpeg/1
```

### 2) `computeranalyze.py`  : vision + decision “brain” (GPU)

- **Run on**: **PC with GPU** (e.g., RTX 3090).
- **Purpose**:
  - Ingest the camera feed (`--kind udp|mjpeg|snapshot`).
  - Run **YOLOv8-nano** person detection, smooth/track target, compute **relative heading** + **speed**.
  - Broadcast **control** via:
    - **SSE** at `http://<pc>:7966/events` (latest-only),
    - **UDP** to the Pi (optional fast path) `--udp-host <pi_ip> --udp-port 7970`.
  - Serve a live **overlay**:
    - `GET /video` (HTML), `/video.mjpeg` (MJPEG), `/video.jpg` (snapshot), `/status` (JSON).
- **Defaults**:
  - Binds `0.0.0.0:7966`.
  - **UDP video ingest (default)**: `--video-base 'udp://@:7971?fifo_size=5000000&overrun_nonfatal=1'`
  - Metrics file `computer_metrics.jsonl` (10s rolling averages).
- **Behavior highlights**:
  - Search mode (forward + continuous spin) after brief holdoff.
  - “Stuck” detection (frame-diff) with timed reverse escape.
  - Stop at close distance (with tiny pivot speed to keep heading updates flowing).
  - Smoothed speeds, yaw slew limiting, dead-zone centering.

**Example run (MJPEG ingest from camera_live)**
```
python3 computeranalyze.py \
  --kind mjpeg \
  --video-base "http://<cam-host>:7965" \
  --index 1 \
  --host 0.0.0.0 \
  --port 7966 \
  --udp-host <raspberrypi> --udp-port 7970
# Control SSE: http://<pc>:7966/events
# Overlay MJPEG: http://<pc>:7966/video.mjpeg
```

**Example run (UDP video ingest)**
```
python3 computeranalyze.py \
  --kind udp \
  --video-base "udp://@:7971?fifo_size=5000000&overrun_nonfatal=1" \
  --host 0.0.0.0 --port 7966 \
  --udp-host <raspberrypi> --udp-port 7970
```

### 3) `raspberrypicontroller.py`  : robot motor controller (BLE)

- **Run on**: **Raspberry Pi 5** (near the Sphero for strong BLE).
- **Purpose**:
  - Maintain **BLE** to Sphero Ollie/BB-8; apply relative-heading + speed at ~**66 Hz** (40 Hz internal tick).
  - Receive control via:
    - **SSE client** → `http://<pc>:7966/events`
    - **UDP listener** (default **port 7970**) : ultra-low latency path
  - Provide a **GUI** (Tkinter): manual joystick, Manual/Autonomous switch, reverse mode, rotate helpers, connect/disconnect.
  - Record end-to-end **metrics** (PC→Pi network, recv→apply, apply→BLE) to `controller_metrics.jsonl`.
- **Notes**:
  - Auto collision recovery (brief back-up + turn).
  - Caps autonomous max speed via GUI slider.
  - Optional LED/stabilization setup on connect.

**Run**
```
python3 raspberrypicontroller.py
# In the GUI:
# 1) Connect Ollie/BB-8 (optionally filter by name)
# 2) (Optional) Connect SSE to http://<pc>:7966
# 3) Start UDP (default listen port 7970)
# 4) Switch to "Autonomous"
```

## Default Ports & Addresses

- **camera_live.py** : HTTP UI/stream on **7965** (`HOST` defaults to `127.0.0.1`)
- **computeranalyze.py** : HTTP/SSE on **7966**; **UDP control out** to Pi **7970**; **UDP video in** on **7971** (when `--kind udp`)
- **raspberrypicontroller.py** : **UDP control in** on **7970**; **SSE client** to `http://<pc>:7966/events`

*Please make sure to adjust hosts/ports as needed for your network (or expose via Tailscale/Cloudflare tunnel)!*

## Environment & Flags (quick reference)

- `camera_live.py`:
  - `HOST`, `PORT`, `DEVICE_INDEX`, `VIDEO_WIDTH`, `VIDEO_HEIGHT`, `VIDEO_FPS`, `RAW_IDLE_SECONDS`
- `computeranalyze.py`:
  - `--kind udp|mjpeg|snapshot`
  - `--video-base` (FFmpeg URL for UDP, or `http://<cam-host>:7965` for HTTP kinds)
  - `--index` (for HTTP kinds)
  - `--udp-host <pi_ip> --udp-port 7970`
  - Metrics file: `COMPUTER_METRICS_FILE`
- `raspberrypicontroller.py`:
  - GUI field for SSE base (default `http://localhost:7966`)
  - GUI control for UDP listen port (default `7970`)
  - Metrics file: `CONTROLLER_METRICS_FILE`

## Notes on Placement

- **Run `camera_live.py` on whichever machine has the Skydroid receiver.**  
  This script should be **physically near the FPV camera** (short RF path). Everything else can subscribe to its HTTP stream from elsewhere.

## AI Disclaimer

I used AI coding assistance (like GitHub Copilot) while building these scripts, especially for the Sphero v2 API, which I hadn’t used before. ChatGPT also nudged me to prefer UDP over HTTP for the control loop and helped with the UDP implementation. I originally tried to manually implement the behavior of the robot, but found Copilot to be quite intelligent when I formalized what I wanted in words (i.e. when the bounding box for human is 2/3 the screen, we should stop the robot's movement using Spherov2 API's stop movement command), and was able to iterate quickly with it on behavior.

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

Thanks to **Niti Parikh** for letting me experiment with her Sphero Ollie and to **Sebastian Bidigain** for performing surgery on the BB-8 head to shove the camera inside. Even though I didn't end up using the BB-8, I'd love to pick it up and figure out how to perfectly calibrate the weight (maybe a smaller battery or custom 3d printed head or stronger magnets) so that we can get the BB-8 to be an intelligent following pet as well. 
