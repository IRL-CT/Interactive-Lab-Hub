# Observant Systems

**Sean Hardesty Lewis (solo)**

I built a small "Pet Robot" that follows people around. The body is a Sphero Ollie carrying a tiny FPV camera and a single-cell battery. A Raspberry Pi 5 is the controller with local Bluetooth driver. The camera’s video stream leaves the robot over UDP via Tailscale and lands on my PC (RTX 3090), where I run real-time person detection at >30 fps. The desktop sends back steering and accel/decel instructions, the Pi applies it, and the Ollie "becomes intelligent". End to end, the pipeline sits around 50-60ms when Wi-Fi is strong (from camera -> RPI -> PC -> RPI -> robot movement). 

## Prep

Done!

## Overview

### Part A

I tried a handful of sense-making paths to understand what would actually hold up once a robot is trying to chase you. OpenCV’s traditional HOG+SVM person detector on the Pi was a good reality check but topped out around 1-3 fps, which was basically a slideshow on wheels. Swapping to YOLO-tiny style detector on my PC GPU immediately improved it with stable 30-45 fps at 720p and more importantly, smooth bounding boxes that didnt jitter with every lighting change.

I realized that while playing around with MobileNet and MediaPipe that I might just be "overengineering" the solution. While I did leave some MediaPipe code in my final version, spending lots of time on trying to get a robot that is currently accelerating to "stop" when it sees my hand up in a stop-handsign took much more time and effort and did not pay off that well. I realized that some of these tools are super cool to use, but knowing which ones to use for what situations is important. I knew that I did not need MediaPipe, MobileNet, or even MoonDream for what I wanted to do, even though these could help with various aspects, since I had already seen how useful and fast a YOLOv8 nano model could be on my PC. I will add that MoonDream was super interesting, and it is one of my inspirations for robotics that semantically defined maps from VLMs + depth maps will allow robots to navigate, memorize a scene, and re-navigate through it in the future. Something similar to [this paper](https://vlmaps.github.io/).

<img width="903" height="531" alt="image" src="https://github.com/user-attachments/assets/3666e5a3-6140-4225-a601-f027493779c1" />

### Part B

Here is what the Sphero EDU app looks like for manually controlling the robot via the phone (wizard of oz!).
<img width="1474" height="856" alt="spheroedu_ui" src="https://github.com/user-attachments/assets/917af14c-ed2d-4058-93d2-34824c180e79" />

For this part, I first used Sphero EDU app which allowed me to control the robot manually with my phone. I figured out how the interaction would work by thinking about where the camera would be in the scene: would it be from a static third person perspective, top-down, would the human be wearing the camera, would the robot be wearing the camera? Some of these ideas I quickly dropped because I felt like I wanted the robot to be as "autonomous" and as "intelligent" as it could possibly be. To test, I designed essentially what I wanted without any "turning" complexity. So, using my PC webcam and myself as the object to be recognized, I wrote a simple script that was basically "Move forward if there is a human object detected on the video feed", and used Sphero v2 Python API to do this. I had quite a few issues with Bluetooth and trying to connect the robot to the PC via Python, but after figuring that out, and consulting the [Sphero v2 API docs](https://spherov2.readthedocs.io/en/latest/sphero_edu.html), I was able to set it up so that it would accelerate when I walk in the frame. Please not that for Part A, B, C, I was using my Sphero BB-8 as opposed to the Ollie, and no camera was attached yet to the robot itself- I was using my PC webcam with a bluetooth connection to the robot and controlling via Python. 

Here is a picture showcasing the **Sphero Ollie (left)** and **Sphero BB-8 (right)**, both robots can be controlled manually via the smartphone app 'Sphero EDU'. Neither have any sort of autonomous capabilities or cameras, that's what I wanted to add.

![IMG_5722](https://github.com/user-attachments/assets/6af0b38b-35bc-4eb6-aa50-4afcba365ad2)

### Part C

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

## Credits

Thanks to **Niti Parikh** for letting me experiment with her Sphero Ollie and to **Sebastian Bidigain** for performing surgery on the BB-8 head to shove the camera inside. Even though I didn't end up using the BB-8, I'd love to pick it up and figure out how to perfectly calibrate the weight (maybe a smaller battery or custom 3d printed head or stronger magnets) so that we can get the BB-8 to be an intelligent following pet as well. 
