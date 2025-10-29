# Observant Systems

**Huiying Zhan, Jiayi Sun**


For lab this week, we focus on creating interactive systems that can detect and respond to events or stimuli in the environment of the Pi, like the Boat Detector we mentioned in lecture. 
Your **observant device** could, for example, count items, find objects, recognize an event or continuously monitor a room.

This lab will help you think through the design of observant systems, particularly corner cases that the algorithms need to be aware of.

<details>
	<summary><h2> Prep </h2></summary>

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
</details>

## Overview
Building upon the paper-airplane metaphor (we're understanding the material of machine learning for design), here are the four sections of the lab activity:

A) [Play](#part-a)

B) [Fold](#part-b)

C) [Flight test](#part-c)

D) [Reflect](#part-d)

---
<details>
	<summary><h2>
    
### Part A
### Play with different sense-making algorithms.
<details>
	<summary><h4>Pytorch for object recognition</h4></summary>

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
</details>

[Video of testing PyTorch](https://youtu.be/nu0sheLPd38)

<details>
	<summary><h4> More classes </h4></summary>

[PyTorch supports transfer learning](https://pytorch.org/tutorials/beginner/transfer_learning_tutorial.html), so you can fine‑tune and transfer learn models to recognize your own objects. It requires extra steps, so we won't cover it here.

For more details on transfer learning and deployment to embedded devices, see Deep Learning on Embedded Systems: A Hands‑On Approach Using Jetson Nano and Raspberry Pi (Tariq M. Arif). [Chapter 10](https://onlinelibrary.wiley.com/doi/10.1002/9781394269297.ch10) covers transfer learning for object detection on desktop, and [Chapter 15](https://onlinelibrary.wiley.com/doi/10.1002/9781394269297.ch15) describes moving models to the Pi using ONNX.
</details>

### Machine Vision With Other Tools

<details>
	<summary><h4> MediaPipe </h4></summary>

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
</details>

The image of interaction with MediaPipe Hand Pose Tracking:  
<img src="MediaPipe.jpg" alt="MediaPipe Hand Pose Tracking" width="400"/>

🎥 The video of the interaction demo: [Watch on YouTube](https://www.youtube.com/shorts/eNRD24geNUE)   
#### **Concept:** Gesture-based media control  
I experimented with using MediaPipe’s hand tracking to build a simple contactless media controller — something that lets users adjust playback or volume just by moving their hands in front of the camera.

For example, raising an index finger upward could increase the volume, while pointing it downward could lower it.  
Swiping the hand to the left or right would move to the previous or next track.  
A closed fist would act as a play/pause toggle.  

Each gesture is recognized by checking which fingers are extended and how the hand moves in space.  
By tracking the 21 key points that MediaPipe provides, I can detect fingertip positions, calculate the relative distance to the palm center, and interpret movement direction over time.  

This allows the system to respond naturally to gestures like pointing, swiping, or closing the hand.


#### **Advantages:**  
This approach feels natural and doesn’t require any physical buttons, which makes it especially useful in situations like cooking or exercising, when touching a screen isn’t convenient.  
It’s intuitive, hygienic, and works smoothly for basic controls like volume and playback.  


#### **Challenges:**  
However, it can sometimes misinterpret casual hand motions as gestures, and lighting conditions strongly affect recognition accuracy.  

Users also need to hold their hands at a comfortable distance — too close or too far and tracking becomes unstable.  


#### **Future ideas:**  
Adding a short delay before confirming gestures could reduce accidental triggers, and simple on-screen or audio feedback would make interactions clearer.  

It could also be extended to recognize multiple hands or combined with face detection so the system only responds when someone is actually looking at the screen.


<details>
	<summary><h4> Moondream Vision-Language Model </h4></summary>

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
</details>

<details>
	<summary><h4>Teachable Machines</h4></summary>
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
</details>

<details>
	<summary><h4> (Optional) Legacy audio and computer vision observation approaches </h4></summary>
In an earlier version of this class students experimented with observing through audio cues. Find the material here:
[Audio_optional/audio.md](Audio_optional/audio.md). 
Teachable machines provides an audio classifier too. If you want to use audio classification this is our suggested method. 

In an earlier version of this class students experimented with foundational computer vision techniques such as face and flow detection. Techniques like these can be sufficient, more performant, and allow non discrete classification. Find the material here:
[CV_optional/cv.md](CV_optional/cv.md).
</details>

---

### Part B
<details>
	<summary><h3> Construct a simple interaction. </h3></summary>

* Pick one of the models you have tried, and experiment with prototyping an interaction.
* This can be as simple as the boat detector shown in lecture.
* Try out different interaction outputs and inputs.
</details>

### 1. Gesture-Based Music Controller; Model Used: MediaPipe Hand Tracking

I experimented with MediaPipe’s hand pose detection to build a simple hands-free music controller.  
The idea was to let users control playback and volume through natural hand movements — useful in situations like cooking or working out, when touching a screen isn’t convenient.

#### Design Process

At first, I tried basic one-finger gestures like pointing up or left, but they were too sensitive and often triggered by mistake.  

After a few rounds of testing, I found that combining finger positions worked much better — for example, using both the index finger and thumb for navigation, and using open or closed hand poses for play/pause control.

Here’s the final gesture set I settled on:
- **Index finger up** → Volume up  
- **Index finger down** → Volume down  
- **Index + thumb in “7” shape pointing right** → Next track  
- **Index + thumb in “7” shape pointing left** → Previous track  
- **Open hand** → Play  
- **Closed fist** → Stop  

These gestures felt stable and distinct enough that they weren’t accidentally triggered, even when I moved naturally in front of the camera.

#### Implementation

I used a Python script called `gesture_remote.py` to handle the gesture detection and link it to simple playback functions.   

The controller cycles through a small music library (four tracks from Lab 4) that loop automatically after finishing.

#### Interaction Flow

When the camera detects a recognized gesture, it sends a corresponding command to the music player.  
The open and closed hand gestures act like a “play/stop switch,” while finger gestures provide finer control for volume and track navigation.

This setup makes the interaction feel surprisingly natural — like conducting a small orchestra with your hands.

#### Demo
🎥 [Demo Video on YouTube](https://youtu.be/XQkTvs8Damo)

#### Why This Design
I wanted the controls to feel as natural as possible while still being reliable.   Simple actions like changing the volume use single-finger gestures, while more complex actions like switching tracks require a combination of fingers.   This layering keeps interactions intuitive but reduces the chance of false triggers. 

To avoid accidental repeats, I added a short cooldown between gestures.   A small on-screen display also appears each time a gesture is recognized, giving quick visual feedback so users know what command was detected.   Overall, the gestures are modeled on real-world motions — pointing up to increase, a fist to stop — so they feel immediately familiar.


### 2. Artistic Object Recognition Interaction; Model Used: YOLO Object Detection

For my prototype, I created a real-time interactive system that combines object detection with artistic visual effects.
The system uses a YOLO-based model to recognize objects through the webcam and overlays a color filter on the video feed depending on what it detects — turning machine perception into an expressive, dynamic art form.

#### Design Process
The project focuses on four stable and commonly detected categories: coffee mug, projector, iPod, and mouse.
Each of these categories is mapped to a distinct visual filter:  

- Coffee mug → Warm orange tone  
- Projector → Cool blue tone  
- iPod → Bright pink tone  
- Mouse → Vibrant green tone  

When the camera detects one of these objects, the corresponding artistic filter is applied across the frame, changing the mood of the screen.

#### Implementation  
Using Python and OpenCV, I connected YOLO detection results with a color overlay system.
The overlay intensity and blending ratio were carefully tuned to ensure that the artistic effect was clear but not overwhelming, maintaining the realism of the background.

To avoid flicker, color changes are triggered only when the detected class changes, not by continuous confidence fluctuations.

#### Interaction Flow  
1. The webcam captures the environment in real time.  
2. The YOLO model detects visible objects.  
3. When a recognized class is found, the filter color changes smoothly to match the detected object.  
4. The video feed updates continuously, creating a living, color-shifting atmosphere that reacts to your surroundings.

#### Demo  
🎥 [Demo Video on YouTube](https://youtu.be/2pXC5KdWHKQ)

#### Why This Design  
I wanted to create a system that doesn’t just detect — but also expresses how AI perceives the world.
Each color corresponds to a unique visual identity, turning everyday objects into sources of digital emotion.
It’s a playful way to visualize how machines “see,” while maintaining a minimal, aesthetic output that feels artistic rather than technical.



---

### Part C
<details>
	<summary><h3>Test the interaction prototype</h3></summary>

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
</details>

### 1. Gesture-Based Music Controller: When It Works Well

The system runs quite smoothly under good conditions — bright lighting, a clear background, and the hand kept about 30–60 cm away from the camera. It responds best when I make deliberate, steady gestures and hold them for about half a second while facing the camera.

In these situations, **fist** and **open hand** gestures are almost perfectly recognized.  
The **volume control** gestures work well once I find the right angle, and the **track navigation** gestures (the “7” shapes) perform reliably as long as the thumb is clearly visible.

#### When It Fails
There are a few situations that still cause problems:
- Low or uneven lighting or shadows make the model lose track of the hand.  
- Fast movements — quick gestures are often skipped or misread.  
- Two hands in the frame — MediaPipe sometimes switches between them.  
- Hand too close — fingertips go out of frame and break detection.  
- Similar poses — “index up” and “index down” can look almost the same.  
- Cluttered background — busy scenes occasionally confuse detection.

#### Why It Fails
Most of these issues come from **MediaPipe’s visual limitations**. It needs clear, well-lit views of the hand and struggles with occlusion. There’s also **gesture ambiguity** — the camera’s 2D perspective can’t always tell whether a finger is pointing up or forward.

The **cooldown timing** can also block valid gestures if the user moves too quickly. And since finger distances depend on hand size and camera distance, thresholds sometimes need manual tuning.

#### Real-World Challenges
In real use, certain contexts make the system unreliable:  
- Cooking or cleaning, when hands are messy or wet  
- Multiple people in the frame  
- Dim evening lighting or backlight from a window  
- Wearing gloves or accessories that hide fingers  

#### User Experience Reflections
Most users wouldn’t automatically understand the system’s limits. It doesn’t give clear feedback about hand distance, cooldowns, or lighting, so people might not know why a gesture fails.  

Small errors like missed volume changes aren’t a big deal, but bigger mistakes — like skipping songs by accident or the system freezing — can be quite frustrating.

#### Possible Improvements
To make it more user-friendly, we’d focus on better feedback and adaptive behavior:
1. **Visual feedback** — show the detected hand skeleton, highlight active fingers, and warn when the hand is too close or far.  
2. **Gesture confirmation** — require gestures to be held briefly before activating, and play a short sound when recognized.  
3. **Adaptive thresholds** — let users calibrate gestures for their hand size or lighting, and auto-tune sensitivity.  
4. **Error recovery** — add an “undo” or “reset” gesture, and pause detection when no hand is visible for a few seconds.


#### Performance Summary
- In testing, gesture accuracy was around **75 %** in good lighting and **40 %** in poor conditions.
- False positives occurred about **10 %** of the time, mostly from idle hand positions.
- Average response time was **0.3–0.5 s**.
- Most people got used to the gestures within about **5 minutes**.


### 2. Object Recognition Interaction Testing: When It Works Well   

The system performs reliably when:
- Objects are close and well-lit.  
- Only one recognizable category (coffee mug, projector, iPod, or mouse) appears at a time.  
- The object is centered in the camera’s field of view.  
- Under these conditions, color transitions are smooth, stable, and visually expressive.

#### When It Fails
The system struggles when:
- Lighting is poor or uneven, reducing YOLO’s confidence.  
- Multiple recognizable objects appear together (e.g., mug + mouse), causing color flickering.  
- The object is too small or partially blocked.  

#### Why It Fails   
Most failures occur due to detection confidence drops or rapid class switching between overlapping objects.
YOLO’s bounding box jittering can also cause quick toggles, producing unwanted flashing effects.

#### User Awareness
Users can immediately notice when detection fails — the screen flickers or turns neutral.
However, since this is an artistic visualization, misclassifications don’t cause real harm. Instead, they create a visible representation of the system’s uncertainty.

#### How to Improve
- Add a temporal smoothing algorithm to prevent quick color shifts.  
- Implement majority voting across recent frames for stable classification.  
- Fine-tune YOLO confidence thresholds per object class.  
- Potentially expand to more visually distinct filters or blending styles.


---




### Part D
<details>
	<summary><h3> Characterize your own Observant system </h3></summary>

Now that you have experimented with one or more of these sense-making systems **characterize their behavior**.
During the lecture, we mentioned questions to help characterize a material:
* What can you use X for?
* What is a good environment for X?
* What is a bad environment for X?
* When will X break?
* When it breaks how will X break?
* What are other properties/behaviors of X?
* How does X feel?

</details>

### 1. Gesture-Based Music Controller
[Demo Video of occasions not went well on YouTube](https://youtu.be/JEqSOrIqWyM)

#### What It’s Good For

From testing, MediaPipe hand tracking feels most suitable for casual, hands-free control tasks — things like playing music while cooking, navigating slides during a presentation, or controlling volume during a video call. It could also be extended to accessibility applications or simple interactive installations.

As shown in the part B video it works best when:
- Lighting is bright and even (natural daylight or good indoor lighting)  
- The background is simple and uncluttered  
- The user stays within 30–60 cm of the camera  
- Only one hand is visible, moving deliberately  

In these settings, it performs quite reliably — especially for gestures like “open hand” or “fist,” which are easy for the model to detect.

#### What It’s Not Great At

It’s less effective for anything that needs precision or speed, such as typing, fine adjustments, or real-time control (like gaming or drawing).  
Because gestures can be misread, it’s not suited for situations where mistakes would have serious consequences.  
Fast-paced environments or dim lighting quickly reduce accuracy.

#### Good vs. Bad Environments
**Good environments:**  
Well-lit indoor spaces, plain backgrounds, stationary users — such as at a desk or kitchen counter.

**Bad environments:**  
Dim rooms, backlighting, cluttered scenes, or multiple people moving in frame.  
Outdoors or crowded settings are especially challenging due to unpredictable lighting and background movement.

#### When and Why It Breaks
The system usually breaks down when:
- The hand goes out of frame or gets partially covered  
- Lighting drops below a usable level  
- The camera resolution or frame rate can’t keep up  
- Gestures are done too quickly or at awkward angles  

When it fails, it tends to do so quietly — gestures just don’t register. Occasionally it misfires (like skipping tracks twice or adjusting the wrong control). Sometimes there’s a short lag, which makes users repeat gestures and accidentally trigger twice. In rare cases, it freezes until the hand leaves the frame and re-enters.

#### How It Feels to Use

When it works, the experience is surprisingly smooth and a bit magical — you can control music just by moving your hand. It feels novel and even empowering, especially because it’s touch-free.  

But the reliability isn’t perfect, and that uncertainty can be tiring. Holding your arm up for too long causes fatigue, and users need to watch the screen closely to make sure the gesture was recognized. Small shifts in position or lighting can throw it off, which sometimes makes the interaction feel fragile.

#### Overall Impression
Compared with physical buttons, gesture control feels more dynamic and fun, but also more uncertain. It’s great for big, simple actions like “play,” “pause,” or “volume up,” but less practical for fine-tuned control. In short: engaging and futuristic, but not yet as dependable as traditional interfaces.


### 2. Object Recognition System Characterization   


#### What It’s Good For

This system is ideal for interactive art installations, educational demos, or visual perception experiments.  
It helps people intuitively understand how AI “sees” the world by turning detection results into expressive, colored feedback.

#### Good Environments
- Well-lit, stable indoor spaces  
- Single-object scenes with clear visibility  
- Matte or non-reflective surfaces  
- Static camera placement  

#### Bad Environments
- Dark or flickering light conditions  
- Multiple overlapping objects  
- Shiny, transparent, or reflective surfaces  

#### When It Breaks
The system fails when no known object is present or the detected object is too far away.  
It may also flicker when multiple classes compete for recognition.

#### How It Breaks
Instead of crashing, the system visually “shows” failure — by flickering, defaulting to a neutral tone, or freezing momentarily.  
This transparency makes the system’s uncertainty visible rather than hidden.

#### Other Properties
- Behavior is expressive, dynamic, and reactive to real-world input.  
- It creates an impression of machine mood — a color-based emotional mirror of detection.  
- The feedback loop between recognition and display gives users a sense of the system’s “attention.”

#### How It Feels
The interaction feels alive and immersive, as if the system is “feeling” the presence of each object.  
The gradual color shifts convey a kind of ambient intelligence — poetic rather than functional — which makes it both meditative and artistic.

---

### Part 2.

Following exploration and reflection from Part 1, finish building your interactive system, and demonstrate it in use with a video.

**\*\*\*Include a short video demonstrating the finished result.\*\*\***
