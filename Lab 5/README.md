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

Part B — Construct a Simple Interaction
Interaction concept

I prototyped a live, on-device activity indicator on Raspberry Pi using a Teachable Machine image model. The Pi camera captures frames continuously; each frame is classified, and the result is shown directly on the video as:

Small label text in the top-left (e.g., drink 88%).

A colored ring centered on the image that encodes the class category for quick, at-a-glance feedback.

Color mapping (BGR):

typing, writing → green (focused work)

phone → orange (distracted)

drink → light blue (short break)

idle → gray (not engaged)

Any unmapped label → default gray

This mirrors the “boat detector” style from lecture: immediate classification + minimal visual cue.

Inputs and outputs

Input: Live camera frame → model.tflite (Teachable Machine) via teachable_machine_lite.classify_image("frame.jpg").
The model returns a dict like {'label': '2 drink', 'confidence': 87.66, ...}; I strip numeric prefixes (e.g., 2 drink → drink) before display.

Output (visual):

Label text: <class> <confidence%> (small font, top-left).

Colored ring: center overlay; color chosen by the class mapping above.

What I experimented with

Parsing labels: The model includes numeric prefixes in label (e.g., 2 drink). I split by the first space and normalize to lowercase so the color map is robust.

Overlay tuning: Small font (0.6, thickness 1) to avoid obscuring the view; ring radius scales with frame size (min(w, h) // 5) and uses anti-aliased strokes for clarity.

Frame-by-frame loop: Kept the loop simple (save → classify → draw) to ensure the interaction feels immediate and mirrors the lecture demo.

How to run

Place these files together in Lab 5/: partB_demo.py, model.tflite, labels.txt.

From a Pi desktop session (local monitor or VNC), run:

python3 partB_demo.py


Press ESC to quit.
If the camera window doesn’t appear, try cv.VideoCapture(1) or verify the camera:
USB cam → ls -l /dev/video* • Pi cam → libcamera-hello -t 3000.

Observations

The ring gives instant, glanceable state without reading text.

Confidence is stable when subjects are centered and lighting is reasonable.

Without smoothing, very rapid transitions can briefly flicker—expected for a per-frame demo.

Design choices

Simplicity first: Kept only the elements that are visually useful in real time (label + color).

Edge-friendly: Uses teachable_machine_lite and OpenCV; no additional runtime services.

Human-readable mapping: Semantic color mapping makes the class meaning obvious.

Limitations and next steps

No debouncing or history: Flicker can occur when frames are ambiguous; adding a 3-frame commit would reduce this.

No audio/TFT mirroring: This version avoids extra dependencies; a tiny beep on class change or a framebuffer mirror to a small TFT (/dev/fb1) could be added later.

Model quality bound: Mislabels are mostly due to training data, lighting, and camera angle; improving the dataset would help.

Files (for reproducibility)

partB_demo.py — the script (live label + colored ring).

model.tflite — Teachable Machine image model used.

labels.txt — class labels for the model.

### Part C
### Test the interaction prototype

Now flight test your interactive prototype and **note down your observations**:
For example:
1. When does it what it is supposed to do?
1. When does it fail?
1. When it fails, why does it fail?
1. Based on the behavior you have seen, what other scenarios could cause problems?

**\*\*\*Think about someone using the system. Describe how you think this will work.\*\*\***
1. Are they aware of the uncertainties in the system?
1. How bad would they be impacted by a miss classification?
1. How could change your interactive system to address this?
1. Are there optimizations you can try to do on your sense-making algorithm.

### Part D
### Characterize your own Observant system

Now that you have experimented with one or more of these sense-making systems **characterize their behavior**.
During the lecture, we mentioned questions to help characterize a material:
* What can you use X for?
* What is a good environment for X?
* What is a bad environment for X?
* When will X break?
* When it breaks how will X break?
* What are other properties/behaviors of X?
* How does X feel?

**\*\*\*Include a short video demonstrating the answers to these questions.\*\*\***

### Part 2.

Following exploration and reflection from Part 1, finish building your interactive system, and demonstrate it in use with a video.

**\*\*\*Include a short video demonstrating the finished result.\*\*\***
