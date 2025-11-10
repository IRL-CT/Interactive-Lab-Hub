# Observant Systems

**Dingran Dai, Xiang Chang, Melody Huang**


For lab this week, we focus on creating interactive systems that can detect and respond to events or stimuli in the environment of the Pi, like the Boat Detector we mentioned in lecture. 
Your **observant device** could, for example, count items, find objects, recognize an event or continuously monitor a room.

This lab will help you think through the design of observant systems, particularly corner cases that the algorithms need to be aware of.

## Prep

1.  Install VNC on your laptop if you have not yet done so. This lab will actually require you to run script on your Pi through VNC so that you can see the video stream. Please refer to the [prep for Lab 2](https://github.com/FAR-Lab/Interactive-Lab-Hub/blob/-/Lab%202/prep.md#using-vnc-to-see-your-pi-desktop).
2.  Install the dependencies as described in the [prep document](prep.md). 
3.  Read about [OpenCV](https://opencv.org/about/),[Pytorch](https://pytorch.org/), [MediaPipe](https://mediapipe.dev/), and [TeachableMachines](https://teachablemachine.withgoogle.com/).
4.  Read Belloti, et al.'s [Making Sense of Sensing Systems: Five Questions for Designers and Researchers](https://www.cc.gatech.edu/~keith/pubs/chi2002-sensing.pdf).

### For the lab, you will need:
1. Pull the new Github Repo
1. Raspberry Pi
1. Webcam 

### Deliverables for this lab are:
1. Show pictures, videos of the "sense-making" algorithms you tried.
1. Show a video of how you embed one of these algorithms into your observant system.
1. Test, characterize your interactive device. Show faults in the detection and how the system handled it.

## Overview
Building upon the paper-airplane metaphor (we're understanding the material of machine learning for design), here are the four sections of the lab activity:

A) [Play](#part-a)

B) [Fold](#part-b)

C) [Flight test](#part-c)

D) [Reflect](#part-d)

---

### Part A
### Play with different sense-making algorithms.

#### Pytorch for object recognition

For this first demo, you will be using PyTorch and running a MobileNet v2 classification model in real time (30 fps+) on the CPU. We will be following steps adapted from [this tutorial](https://pytorch.org/tutorials/intermediate/realtime_rpi.html).

![torch](Readme_files/pyt.gif)


To get started, install dependencies into a virtual environment for this exercise as described in [prep.md](prep.md).

Make sure your webcam is connected.

You can check the installation by running:

```
python -c "import torch; print(torch.__version__)"
```

If everything is ok, you should be able to start doing object recognition. For this default example, we use [MobileNet_v2](https://arxiv.org/abs/1801.04381). This model is able to perform object recognition for 1000 object classes (check [classes.json](classes.json) to see which ones.

Start detection by running  

```
python infer.py
```

The first 2 inferences will be slower. Now, you can try placing several objects in front of the camera.

Read the `infer.py` script and become familiar with the code. You can change the video resolution and frames per second (FPS). You may also use the weights of the larger pre-trained mobilenet_v3_large model, as described [here](https://pytorch.org/tutorials/intermediate/realtime_rpi.html#model-choices).

#### More classes

[PyTorch supports transfer learning](https://pytorch.org/tutorials/beginner/transfer_learning_tutorial.html), so you can fine‑tune and transfer learn models to recognize your own objects. It requires extra steps, so we won't cover it here.

For more details on transfer learning and deployment to embedded devices, see Deep Learning on Embedded Systems: A Hands‑On Approach Using Jetson Nano and Raspberry Pi (Tariq M. Arif). [Chapter 10](https://onlinelibrary.wiley.com/doi/10.1002/9781394269297.ch10) covers transfer learning for object detection on desktop, and [Chapter 15](https://onlinelibrary.wiley.com/doi/10.1002/9781394269297.ch15) describes moving models to the Pi using ONNX.

### Machine Vision With Other Tools
The following sections describe tools ([MediaPipe](#mediapipe) and [Teachable Machines](#teachable-machines)).

#### MediaPipe

A established open source and efficient method of extracting information from video streams comes out of Google's [MediaPipe](https://mediapipe.dev/), which offers state of the art face, face mesh, hand pose, and body pose detection.

![Media pipe](Readme_files/mp.gif)

To get started, install dependencies into a virtual environment for this exercise as described in [prep.md](prep.md):

Each of the installs will take a while, please be patient. After successfully installing mediapipe, connect your webcam to your Pi and use **VNC to access to your Pi**, open the terminal, and go to Lab 5 folder and run the hand pose detection script we provide:
(***it will not work if you use ssh from your laptop***)


```
(venv-ml) pi@ixe00:~ $ cd Interactive-Lab-Hub/Lab\ 5
(venv-ml) pi@ixe00:~ Interactive-Lab-Hub/Lab 5 $ python hand_pose.py
```

Try the two main features of this script: 1) pinching for percentage control, and 2) "[Quiet Coyote](https://www.youtube.com/watch?v=qsKlNVpY7zg)" for instant percentage setting. Notice how this example uses hardcoded positions and relates those positions with a desired set of events, in `hand_pose.py`. 

Consider how you might use this position based approach to create an interaction, and write how you might use it on either face, hand or body pose tracking.

(You might also consider how this notion of percentage control with hand tracking might be used in some of the physical UI you may have experimented with in the last lab, for instance in controlling a servo or rotary encoder.)

I’ll use a position-to-percentage idea and map pose geometry to a 0–100% control. With hand tracking, take the distance between the thumb tip and index tip, divide by hand size (e.g., palm width) to normalize, then smooth it slightly. That percentage can directly drive the Lab 4 servo (0% → 0°, 100% → 180°) or step a rotary encoder value. Simple thresholds make quick commands: <15% = mute, >85% = max; the middle range gives continuous control (volume/brightness/scroll). The same approach also works with face (face box height ≈ distance → screen brightness) or body (torso lean angle → scroll speed). Do a quick min/max calibration and show the live percent on screen so users see “move a little → change a little,” matching the Lab 4 hardware loop.

#### Moondream Vision-Language Model

[Moondream](https://www.ollama.com/library/moondream) is a lightweight vision-language model that can understand and answer questions about images. Unlike the classification models above, Moondream can describe images in natural language and answer specific questions about what it sees.

To use Moondream, first make sure Ollama is running and pull the model:
```bash
ollama pull moondream
```

Then run the simple demo script:
```bash
python moondream_simple.py
```

This will capture an image from your webcam and let you ask questions about it in natural language. Note that vision-language models are slower than classification models (responses may take up to minutes on a Raspberry Pi). There are newer models like [LFM2-VL](https://huggingface.co/LiquidAI/LFM2-VL-450M-GGUF), but many are very recent and not yet optimized for embedded devices.

**Design consideration**: Think about how slower response times change your interaction design. What kinds of observant systems benefit from thoughtful, delayed responses rather than real-time classification? Consider systems that monitor over longer time periods or provide periodic summaries rather than instant feedback.

With slower VLMs like Moondream, design for windows, not frames: take periodic snapshots (e.g., every 5–10 minutes), aggregate results, then deliver a short summary or gentle prompt instead of real-time pop-ups. This suits observant systems that track longer trends—focus/attention coaching (dominant activity in the last window), posture/ergonomics (slouch ratio per hour), noise exposure (minutes above a dB threshold), or hydration/break reminders (no drink events for ≥45 min). The delayed, batched feedback reduces false alarms, respects attention, and matches the model’s latency.

#### Teachable Machines
Google's [TeachableMachines](https://teachablemachine.withgoogle.com/train) is very useful for prototyping with the capabilities of machine learning. We are using [a python package](https://github.com/MeqdadDev/teachable-machine-lite) with tensorflow lite to simplify the deployment process.

![Tachable Machines Pi](Readme_files/tml_pi.gif)

To get started, install dependencies into a virtual environment for this exercise as described in [prep.md](prep.md):

After installation, connect your webcam to your Pi and use **VNC to access to your Pi**, open the terminal, and go to Lab 5 folder and run the example script:
(***it will not work if you use ssh from your laptop***)


```
(venv-tml) pi@ixe00:~ Interactive-Lab-Hub/Lab 5 $ python tml_example.py
```


Next train your own model. Visit [TeachableMachines](https://teachablemachine.withgoogle.com/train), select Image Project and Standard model. The raspberry pi 4 is capable to run not just the low resource models. Second, use the webcam on your computer to train a model. *Note: It might be advisable to use the pi webcam in a similar setting you want to deploy it to improve performance.*  For each class try to have over 150 samples, and consider adding a background or default class where you have nothing in view so the model is trained to know that this is the background. Then create classes based on what you want the model to classify. Lastly, preview and iterate. Finally export your model as a 'Tensorflow lite' model. You will find an '.tflite' file and a 'labels.txt' file. Upload these to your pi (through one of the many ways such as [scp](https://www.raspberrypi.com/documentation/computers/remote-access.html#using-secure-copy), sftp, [vnc](https://help.realvnc.com/hc/en-us/articles/360002249917-VNC-Connect-and-Raspberry-Pi#transferring-files-to-and-from-your-raspberry-pi-0-6), or a connected visual studio code remote explorer).
![Teachable Machines Browser](Readme_files/tml_browser.gif)
![Tensorflow Lite Download](Readme_files/tml_download-model.png)

Include screenshots of your use of Teachable Machines, and write how you might use this to create your own classifier. Include what different affordances this method brings, compared to the OpenCV or MediaPipe options.

**First Attempt:** [with](https://teachablemachine.withgoogle.com/models/EKmkwjUou/)

<img width="1185" height="885" alt="image" src="https://github.com/user-attachments/assets/b92deb6e-2079-4ac3-88fa-ab5de0827383" />

I initially trained a Pose Project model to classify six actions — typing, writing, using phone, eating/drinking, daydreaming, and focused. However, the accuracy was poor. Two main issues emerged:

- The dataset was unbalanced, with different numbers of samples per class.

- The pose landmarks of these actions were very similar, since most of them involve sitting at a desk with small upper-body movements.
As a result, the model often confused actions like typing and writing.

**Second Attempt:** https://teachablemachine.withgoogle.com/models/ppuu4fin_/

To improve performance, I switched to an **Image Project**, allowing the model to use contextual cues such as objects (keyboard, pen, phone, cup) and background differences.
I also ensured that each class had a similar number of images (around 150–200 per class) and included a neutral “idle/background” class.
This change significantly improved classification stability and reduced confusion between similar actions.

<img width="1198" height="793" alt="image" src="https://github.com/user-attachments/assets/fea9a3c2-0586-4abc-93c9-ced4716afb28" />

video：


https://github.com/user-attachments/assets/f37626c5-9797-4601-b509-da71170144ab



#### (Optional) Legacy audio and computer vision observation approaches
In an earlier version of this class students experimented with observing through audio cues. Find the material here:
[Audio_optional/audio.md](Audio_optional/audio.md). 
Teachable machines provides an audio classifier too. If you want to use audio classification this is our suggested method. 

In an earlier version of this class students experimented with foundational computer vision techniques such as face and flow detection. Techniques like these can be sufficient, more performant, and allow non discrete classification. Find the material here:
[CV_optional/cv.md](CV_optional/cv.md).

### Part B
### Construct a simple interaction.

* Pick one of the models you have tried, and experiment with prototyping an interaction.
* This can be as simple as the boat detector shown in lecture.
* Try out different interaction outputs and inputs.


**\*\*\*Describe and detail the interaction, as well as your experimentation here.\*\*\***

🧠 Interaction Concept

This prototype is a live, on-device activity indicator running entirely on the Raspberry Pi.
Using a Teachable Machine image model, the Pi camera continuously classifies the user’s current activity and overlays two forms of visual feedback directly on the video:

Label text (top-left) — shows the detected class and confidence (e.g., drink 88 %)

Colored ring (center) — encodes the current category for at-a-glance awareness

Color mapping (BGR):

State	Color	Meaning
typing, writing	🟢 Green	Focused work
phone	🟠 Orange	Distracted by device
drink	🔵 Light blue	Short physical break
idle	⚪ Gray	Not engaged
other	⚫ Gray	Unmapped / default

This mirrors the “boat-detector” example from lecture—minimal logic, immediate visual feedback, and runs smoothly on the Pi.

⚙️ How It Works

The Pi camera captures frames continuously (cv2.VideoCapture(0)).

Each frame is saved as frame.jpg and classified with teachable_machine_lite.

The script parses results like
{'label': '2 drink', 'confidence': 87.66} → drink 87 %.

The label and confidence are drawn on the video (cv.putText).

A colored ring (cv.circle) is drawn at the center to represent the class category.

The video window is displayed live on the Pi screen. Press ESC to exit.

🧪 Experimentation and Tuning

Parsing labels: The model returns numeric prefixes (e.g., 2 drink); the script removes the number to match the color map.

Overlay design: Font size 0.6 and thin stroke (1 px) keep text readable without blocking the view.

Ring size: Dynamic radius min(w, h)//5 fits different resolutions.

Classification loop: Kept simple (save → classify → draw) for real-time responsiveness.

▶️ Run Instructions
# In the Lab 5 directory
python3 partB_demo.py


If no window appears, run from the Pi desktop or VNC session (not SSH).
If the camera fails, try cv.VideoCapture(1) or test with libcamera-hello -t 3000.

Dependencies

pip3 install teachable-machine-lite opencv-python

🎨 Inputs and Outputs
Type	Description
Input	Live camera feed classified by Teachable Machine model (model.tflite, labels.txt)
Output	Visual overlay (label text + colored ring) on video stream
👀 What to Expect

Typing / Writing → label typing or writing, ring turns 🟢 green.

Using phone → label phone, ring turns 🟠 orange.

Drinking → label drink, ring turns 🔵 light blue.

Idle → label idle, ring turns ⚪ gray.

🧩 Observations

The colored ring provides immediate, non-verbal feedback.

Confidence remains stable with good lighting and frontal camera angles.

Frame-level classification can flicker slightly during motion transitions.

💡 Design Choices

Clarity over complexity: Only two visual elements—text and ring.

Edge friendly: No external libraries beyond OpenCV and TM Lite.

Intuitive colors: Immediate semantic mapping of behavioral state.

⚠️ Limitations and Next Steps

No temporal smoothing → minor flicker possible.

Lighting conditions affect classification confidence.

Future extensions: add simple beep on label change or mirror video to a small TFT (/dev/fb1) display.


### Part C
### Test the interaction prototype

Now flight test your interactive prototype and **note down your observations**:
For example:

1. **When does it do what it is supposed to do?**
   - Good, even lighting; user centered ~0.5–1 m from camera.
   - Clear poses/objects visible: typing/writing, phone at face/chest, cup near face, neutral idle.
   - Minimal background motion; single person in frame.

2. **When does it fail?**
   - Lighting extremes (backlight, low light, glare).
   - Fast motions or occlusion (hands cover the object).
   - Atypical angles/shapes not seen in training (side-typing, unusual cups).
   - Multiple people or moving backgrounds.

3. **When it fails, why does it fail?**
   - Domain shift between training images and live scenes.
   - Per-frame classification → transient flicker during transitions.
   - Visually confusable items (dark mug vs. phone).

4. **Based on the behavior you have seen, what other scenarios could cause problems?**
   - Mirrors/monitor reflections; partial crops at frame edges.
   - Doing two actions at once (holding a cup while typing).
   - Similar desk objects (TV remote ≈ phone).

**\*\*\*Think about someone using the system. Describe how you think this will work.\*\*\***

1. **Are they aware of the uncertainties in the system?**
   - Partly. They see a confidence %, but it’s not strongly communicated; users may not interpret what “62%” means.

2. **How bad would they be impacted by a misclassification?**
   - Low risk for this ambient feedback; main downside is brief mistrust/ignoring the display if flicker is frequent.

3. **How could you change your interactive system to address this?**
   - Add an **Unknown** state below a confidence threshold (e.g., 60–70%).
   - Add **stickiness**: update label only after a short dwell or **k-of-N** consistent frames (e.g., 3/5).
   - Replace raw % with **Low / Medium / High** badges for clarity.

4. **Are there optimizations you can try to do on your sense-making algorithm?**
   - **Temporal smoothing:** k-of-N majority; short dwell (200–300 ms).
   - **Hysteresis:** higher threshold to enter a new class than to stay.
   - **Top-2 margin:** switch only if `p_top − p_second > δ` (e.g., 0.15).
   - **Input hygiene:** lock exposure/white balance; optional center ROI; expand training with hard negatives and varied lighting.




### Part D
### Characterize your own Observant system

Now that you have experimented with one or more of these sense-making systems **characterize their behavior**.
During the lecture, we mentioned questions to help characterize a material:


---
**X = Raspberry Pi + Teachable Machine image classifier (live label + colored ring).**  
The system classifies each camera frame and overlays a small text label (with confidence) and a colored ring indicating the class category.
**What can you use X for?**
- Ambient, **glanceable awareness** of current activity (typing/writing/phone/drink/idle).
- Lightweight **focus/distractor indicators** for personal productivity or demo kiosks.
- A teaching scaffold for **edge AI** (camera → classify → visual feedback).

**What is a good environment for X?**
- **Even, front-facing lighting** (no strong backlight).
- **Single user**, centered ~0.5–1 m from camera; clear view of hands/objects.
- **Calm background** (few moving distractors; simple textures).

**What is a bad environment for X?**
- **Low light / backlight / glare** (e.g., glossy phone, reflective mugs).
- **Busy scenes** (multiple people, mirrors/monitors, fast passerby).
- **Extreme angles/partial crops** (object at frame edge; side-typing).

**When will X break?**
- **Domain shift**: objects/poses unseen in training (new cup shape; phone with thick case).
- **Occlusion & fast motion**: hands block object; rapid switching between activities.
- **Resource issues**: camera fails to open; disk I/O slowdown (saving frames); high CPU load.

**When it breaks how will X break?**
- **Flicker/mislabels** (per-frame ambiguity) → ring/color flips rapidly.
- **Default/gray ring** when label mapping fails or confidence is very low.
- **Laggy preview** if I/O or CPU is saturated; window may stutter.

**What are other properties/behaviors of X?**
- **Local & private**: runs fully on-device; no network needed.
- **Immediate**: per-frame overlay feels responsive; no history by default.
- **Tunable**: behavior changes a lot with small policy tweaks (confidence threshold, k-of-N, ROI).
- **Data-bound**: accuracy follows training coverage (lighting, angles, object diversity).

**How does X feel?**
- **Glanceable and playful**—the colored ring communicates state instantly.
- **Occasionally twitchy** in edge cases (motion/lighting), reminding you it’s probabilistic.
- **Trustworthy enough** for ambient cues, not for high-stakes automation.


**\*\*\*Include a short video demonstrating the answers to these questions.\*\*\***

[Lab 5/fe50a0c817249c7b1928fe79615d706d.mp4](https://github.com/ChangXiang-SCU/Interactive-Lab-Hub/blob/Fall2025/Lab%205/fe50a0c817249c7b1928fe79615d706d.mp4)

### Part 2.

Following exploration and reflection from Part 1, finish building your interactive system, and demonstrate it in use with a video.

**\*\*\*Include a short video demonstrating the finished result.\*\*\***
