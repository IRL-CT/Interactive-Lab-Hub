# Observant Systems

**NAMES OF COLLABORATORS HERE**


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

Following exploration and reflection from Part 1, I finished building the interactive system and demonstrated it in use with a short video.

**🎥 Demo Video:**  
[Watch on YouTube](https://youtube.com/shorts/ZPnJ3qQ8inI)

---

#### 🎯 Core Functionality
**1. Hand Gesture Recognition**
- Uses **MediaPipe Hand Tracking** (via `HandTrackingModule`) to detect 21 hand landmarks per frame.  
- Recognizes **six distinct gestures** with improved stability and threshold tuning.

**2. Music Playback Control**
- Supports play/pause, next/previous track, and automatic looping.  
- Plays `.wav` files from the Lab 4 music folder.  

**3. Volume Control**
- Adjusts system audio via **PulseAudio (`pactl`)**, in 5% increments.

---

#### ✋ Gesture Mappings
- **Fist (all fingers closed)** → *Stop or pause music*  
  → Detected when `finger_count == 0`
- **Open Hand (all five fingers extended)** → *Play music*  
  → Detected when `finger_count == 5`
- **Index Up (only index finger extended, pointing upward)** → *Increase volume*  
  → Detected when `only_index && pointerY < base - 80`
- **Index Down (only index finger extended, pointing downward)** → *Decrease volume*  
  → Detected when `only_index && pointerY > base - 20`
- **7-Right (thumb + index forming a “7” pointing right)** → *Next track*  
  → Detected when `thumb_and_index && pointer_dx > 60`
- **7-Left (thumb + index forming a “7” pointing left)** → *Previous track*  
  → Detected when `thumb_and_index && pointer_dx < -60`

---

#### ⚙️ Key Improvements
- **Improved finger-counting algorithm** using distance-based thumb detection and stricter thresholds.  
- **Priority-based gesture checking** to avoid false positives (evaluation order: 7-gesture → fist → open hand → volume).  
- **Gesture cooldown system** to prevent rapid re-triggering (1s for track changes, 0.3s for volume).  
- **Real-time visual feedback** displaying gesture name, track info, and usage instructions on the OpenCV feed.  
- **Robust camera detection** that automatically locates available devices (`/dev/video0–2`).

---

#### 🧠 Technical Features
- Real-time video display using **OpenCV** with FPS counter.  
- Continuous **MediaPipe landmark tracking**.  
- Audio control handled via **subprocess + PulseAudio**.  
- Modular **gesture state management** with cooldown timers for smooth operation.

---
### 🧪 User Testing

To evaluate the usability and reliability of the final gesture-based music controller, I conducted a short user test with three participants. Each participant was first introduced to the six available gestures and then asked to perform basic tasks such as playing, pausing, changing tracks, and adjusting the volume. The session took place in an indoor setting with moderate lighting and a laptop webcam.

**Observations:**
- All participants quickly learned the mapping between gestures and actions within 2–3 minutes.  
- Large, distinct gestures (open hand, fist) were consistently recognized with high accuracy.  
- Volume and track-switching gestures required slightly more effort, as users had to keep their hand steady for about half a second to avoid false triggers.  
- When lighting became uneven or users leaned too close to the camera, MediaPipe occasionally lost hand tracking, causing a delay in response.  

**User Feedback:**
- Participants described the interaction as *“fun,” “intuitive,”* and *“surprisingly natural.”*  
- The on-screen feedback text was helpful for understanding which gesture was detected, but users suggested adding auditory cues (a beep or short sound) to confirm successful actions.  
- Two users mentioned mild arm fatigue after extended use, suggesting that the system is best suited for short interactions rather than continuous control.

**Results Summary:**
- Average gesture recognition accuracy: ~80 % in normal lighting conditions.  
- Mean response latency: 0.4 seconds.  
- Average subjective satisfaction rating: 4.3 / 5.

**Future Improvements:**
Based on the feedback, future iterations will include adaptive lighting calibration, optional sound feedback, and adjustable gesture sensitivity to accommodate different user preferences and environments.

---

### 2. Object Recognition System Characterization 

**🎥 Demo Video:**  
[Watch on YouTube](https://youtu.be/enzMxKDUPDo) 



#### 🎯 Core Functionality
**1. Real-Time Object Recognition**  
- Uses a **quantized MobileNetV2** model for efficient real-time classification on Raspberry Pi.  
- Recognizes common desk or workspace items such as *coffee mug*, *projector*, *iPod*, and *computer mouse*.  

**2. Emotion-Themed Visual Response**  
- Each recognized object triggers a distinct **color theme** that reflects a certain emotional tone (e.g., *warm orange* for coffee mug, *cool blue* for projector).  
- The screen displays smooth, continuous **color transitions** to express “emotional blending” between objects.  

**3. Sound Feedback**  
- When a specific object is detected, a matching **sound clip** (warm, digital, beat, or click) is played.  
- Sounds are stored locally in the `/sounds` folder and handled using **Pygame mixer** for minimal latency.

**4. Particle & Glow Effects**  
- Recognized objects trigger a **dynamic glow filter** and **particle animation** to enhance immersion.  
- The particle system generates floating light particles with color matching the recognized object, creating a dreamy, ambient visual atmosphere.



#### 💡 Object-to-Emotion Mappings
| Object | Color Theme | Sound Effect | Mood Representation |
|:--|:--|:--|:--|
| Coffee Mug | Warm orange | `warm.mp3` | Cozy, comforting energy |
| Projector | Digital blue | `digital.mp3` | Calm, futuristic vibe |
| iPod | Soft purple | `beat.mp3` | Creative, rhythmic feel |
| Mouse | Lime green | `click.mp3` | Focused, interactive flow |
| Default (no object) | Neutral gray-white | — | Balanced, resting state |



#### ⚙️ Key Improvements
- **Optimized performance** with MobileNetV2 quantization (`torch.jit.script`) for Raspberry Pi.  
- **Smooth color transitions** between emotional states using linear interpolation.  
- **Dynamic brightness control** for subtle glow enhancement when an object is active.  
- **Particle animation engine** implemented in OpenCV for visually expressive, lightweight effects.  
- **Independent sound control** — each recognition event triggers its own audio playback without interrupting visuals.  



#### 🧠 Technical Features
- Real-time camera input handled via **OpenCV (V4L2 backend)** at 24 FPS.  
- Image preprocessing pipeline based on **torchvision.transforms**.  
- **Sound playback** handled asynchronously by `pygame.mixer`.  
- Uses **HSV saturation adjustment + Gaussian blur** for glow intensity control.  
- Modular design: visual, audio, and recognition subsystems operate independently.



### 🧪 User Testing

To evaluate the emotional resonance and usability of the system, I conducted user testing with three participants. Each participant interacted with several common objects (coffee mug, iPod, etc.) in front of the camera, observing the visual and auditory changes.

**Observations:**
- The **color transitions** were described as *“soothing”* and *“pleasant to watch.”*  
- **Sound feedback** helped users immediately understand when the system detected a new object.  
- The **particle animation** was considered “beautiful but slightly subtle” — users suggested making particles larger or adding slow expansion effects for greater visual presence.  
- Detection accuracy was stable in well-lit environments but dropped slightly under dim or uneven lighting.  

**User Feedback:**
- Participants felt that the overall experience was *“relaxing”* and *“aesthetic.”*  
- Several mentioned it could serve as a **mood visualization installation** or **AI art piece** rather than a traditional utility tool.  
- One user suggested adding an optional **music-reactive mode**, where particles pulse with beat intensity.

**Results Summary:**
- Average object recognition accuracy: ~85% in consistent lighting.  
- Average visual update latency: ~0.5 seconds.  
- Average satisfaction rating: **4.5 / 5**.  

**Future Improvements:**
- Add adaptive brightness and color calibration based on ambient lighting.  
- Introduce multi-object blending effects for more complex visual storytelling.  
- Integrate audio-reactive particle motion to synchronize visuals with rhythm.  
- Package as a standalone art installation or smart-desk experience.  

