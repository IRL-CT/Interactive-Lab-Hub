# Observant Systems

For lab this week, we focus on creating interactive systems that can detect and respond to events or stimuli in the environment of the Pi, like the Boat Detector we mentioned in lecture. 
Your **observant device** could, for example, count items, find objects, recognize an event or continuously monitor a room.

This lab will help you think through the design of observant systems, particularly corner cases that the algorithms need to be aware of.

<details>
<summary><strong>Prep</strong></summary>

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
### Part A
<details>
    
<summary>Instruction</summary>

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

### The Process of Teachable Machines
<img  width="800" src="https://github.com/user-attachments/assets/74eeea24-5120-47ac-99ea-9f1751c22c4e" />

**Results**

<img width="800" src="https://github.com/user-attachments/assets/a66b4f6e-1779-4aeb-8799-8ff5f6fd6b5d" />

<img width="800" src='https://github.com/user-attachments/assets/fd5ddb61-6c3d-4fe0-9a3f-09a71137acb7'  />

The main "affordance," or key advantage, of Teachable Machine is its simplicity and accessibility. It allows anyone, even those without any coding or machine learning experience, to build a custom model. The entire process is visual. This is perfect for rapid prototyping—I can test an idea for an object detector in minutes instead of days.

#### (Optional) Legacy audio and computer vision observation approaches
In an earlier version of this class students experimented with observing through audio cues. Find the material here:
[Audio_optional/audio.md](Audio_optional/audio.md). 
Teachable machines provides an audio classifier too. If you want to use audio classification this is our suggested method. 

In an earlier version of this class students experimented with foundational computer vision techniques such as face and flow detection. Techniques like these can be sufficient, more performant, and allow non discrete classification. Find the material here:
[CV_optional/cv.md](CV_optional/cv.md).

</details>

### Part B

<details><summary>Instuction</summary>
    
### Construct a simple interaction.

* Pick one of the models you have tried, and experiment with prototyping an interaction.
* This can be as simple as the boat detector shown in lecture.
* Try out different interaction outputs and inputs.

</details>

### Concept

I designed a slow, observant system called Desk Observer — a vision-based agent that periodically checks my workspace and gently reminds me to tidy it up if it looks messy.
Instead of reacting to fast gestures or motion, it takes time to “think” and gives a thoughtful textual reflection.


| Component          | Description                                                                              |
| ------------------ | ---------------------------------------------------------------------------------------- |
| **Input**          | Raspberry Pi camera captures an image of my desk every few minutes                       |
| **Processing**     | The Moondream model describes the image in natural language                              |
| **Interpretation** | The description is analyzed for words like “messy”, “cluttered”, “clean”, or “organized” |
| **Output**         | A printed message or notification reminding me to tidy up or praising a clean desk       |

**Example Logic (Simplified)**
```
if "messy" in description or "cluttered" in description:
    print("😅 Looks messy — maybe tidy up your desk?")
elif "clean" in description or "organized" in description:
    print("✨ Nice and clean today!")
else:
    print("🤔 Not sure how it looks.")
```

The system runs automatically every five minutes, acting as a “slow observer” that quietly monitors my space.

**Design Considerations**

- **Timing:** Since Moondream takes time to respond, a slower rhythm (every 5 minutes) fits naturally.

- **Feedback Style:** The system communicates in a friendly, non-judgmental tone to encourage reflection rather than enforcement.

- **Error Handling:** If Moondream returns unrelated or unclear descriptions, the system simply outputs “Not sure how it looks.”


### Part C
### Test the interaction prototype

<details><summary>Instuction</summary>
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

### Experiments

I tested the system in three different scenarios:

**Clean desk:** only a laptop and one cup on the table.

**Messy desk:** many objects scattered around (papers, cables, snacks).

**Dark lighting:** same messy desk but with low illumination.

### Observations

In the clean condition, Moondream often described the scene as “a tidy desk with a laptop,” which correctly triggered the “✨ Nice and clean” message.

In the messy condition, the description included “many items on a cluttered desk,” producing the expected reminder message.

Under poor lighting, Moondream sometimes gave irrelevant descriptions (e.g., “a dark room with shadows”), resulting in the fallback “🤔 Not sure how it looks.”

### Failure Modes

Sensitive to lighting and camera angle – when the camera pointed slightly away, it misinterpreted the scene.

Long latency – responses could take up to 90 seconds, which is fine for this use case but unsuitable for real-time feedback.

Occasionally ambiguous language (“a busy workspace” vs “a productive desk”) made it hard to categorize.

### User Experience Reflection

From a user perspective, the system feels like a gentle companion rather than a strict monitor. The delays in response make it feel more reflective — as if it’s “thinking” before speaking.


### Part D

<details><summary>Instruction</summary>
    
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

</details>

| Question                               | Reflection                                                                                   |
| -------------------------------------- | -------------------------------------------------------------------------------------------- |
| **What can you use it for?**           | Monitoring workspace cleanliness and encouraging mindful habits over time.                   |
| **What is a good environment for it?** | Steady lighting, fixed camera position, clear view of the desk.                              |
| **What is a bad environment for it?**  | Low light, reflections, camera movement, or highly dynamic backgrounds.                      |
| **When will it break?**                | When Moondream misinterprets the image or returns irrelevant text.                           |
| **How will it break?**                 | Produces the “Not sure” message or gives an incorrect judgment.                              |
| **Other properties/behaviors**         | Slow but semantically rich; generates human-like textual reflections.                        |
| **How does it feel?**                  | Not mature enough                                                                            |

---

### Code
<details><summary><strong>Prompt and Keywords</strong></summary>
<pre>
# The specific prompt for Moondream
DESK_PROMPT = "Describe the state of the desk in this image. Is it clean, messy, or cluttered?"<br>
# Keywords to check in Moondream's (lowercase) response
MESSY_KEYWORDS = MESSY_KEYWORDS = [
    "messy", "cluttered", "disorganized", "untidy", "chaotic", 
    "jumbled", "sloppy", "unorganized", "scattered", "strewn", 
    "piles", "trash", "garbage", "disarray", "clutter"
]
CLEAN_KEYWORDS = [
    "clean", "organized", "tidy", "neat", "orderly", "uncluttered", 
    "clear", "minimal", "minimalist", "empty", "spacious", 
    "arranged", "spotless"
]
</pre>
</details>

<details><summary><strong>Action Function</strong></summary>

<pre>
def ask_moondream(image_path, prompt):
    """
    Ask Moondream about the image with streaming response.
    (Unchanged from TA's sample, but increased timeout)
    """
    
    # Encode image to base64
    try:
        with open(image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
    except FileNotFoundError:
        print(f"\n[ERROR] Image file not found: {image_path}")
        return None
    
    print(f"\nAsking Moondream: {prompt}")
    print("Moondream is thinking... ", end="", flush=True)
    
    try:
        # Query Moondream with streaming
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "moondream:latest",
                "prompt": prompt,
                "images": [image_data],
                "stream": True
            },
            timeout=300,  # 5 minute timeout for slow models
            stream=True
        )
        
        if response.status_code == 200:
            full_response = ""
            for line in response.iter_lines():
                if line:
                    chunk = json.loads(line)
                    token = chunk.get('response', '')
                    print(token, end="", flush=True)
                    full_response += token
            
            print("\n")  # New line after response
            return full_response.strip()
        else:
            print(f"\n[ERROR] Moondream API returned status: {response.status_code}")
            print(f"Details: {response.text}")
            return None
    except requests.exceptions.Timeout:
        print("\n[TIMEOUT] Moondream is taking too long.")
        return None
    except requests.exceptions.ConnectionError:
        print("\n[CONNECTION ERROR] Could not connect to Moondream server.")
        print("Please ensure Ollama is running at http://localhost:11434")
        return None
    except Exception as e:
        print(f"\n[UNEXPECTED ERROR] {e}")
        return None
</pre>
</details>

<details><summary><strong>Check if it is Messy</strong></summary>
<pre>
def analyze_description(description):
    """
    (NEW FUNCTION)
    Interprets Moondream's response based on your concept's logic.
    """
    
    if not description:
        return "Not sure how it looks. (Moondream gave no response)"

    desc_lower = description.lower()
    
    # Check for messy keywords
    if any(keyword in desc_lower for keyword in MESSY_KEYWORDS):
        return f"Looks messy :( maybe tidy up your desk?\n(Moondream said: \"{description}\")"
    
    # Check for clean keywords
    elif any(keyword in desc_lower for keyword in CLEAN_KEYWORDS):
        return f"Nice and clean today!\n(Moondream said: \"{description}\")"
    
    # Fallback
    else:
        return f"Not sure how it looks.\n(Moondream said: \"{description}\")"

</pre>
</details>

<details><summary><strong>Main Loop</strong></summary>
<pre>
def main():
    print("=" * 50)
    print("--- Desk Observer Activated ---")
    print(f"I will check your desk every {WAIT_TIME_SECONDS // 60} minutes.")
    print("Press Ctrl+C to stop.")
    print("=" * 50)

    try:
        while True:
            print(f"\n--- {time.ctime()} ---")
            
            # 1. Input: Capture image
            image_path = capture_image()
            
            if not image_path:
                print("Failed to capture image. Will try again next cycle.")
                time.sleep(WAIT_TIME_SECONDS)
                continue
            
            # 2. Processing: Get description from Moondream
            description = ask_moondream(image_path, DESK_PROMPT)
            
            # 3. Interpretation & 4. Output: Analyze and print feedback
            message = analyze_description(description)
            
            print("\n--- Desk Observer's Reflection ---")
            print(message)
            print("------------------------------------------")
            
            # 5. Wait for the next cycle
            print(f"\nSleeping for {WAIT_TIME_SECONDS // 60} minutes...")
            time.sleep(WAIT_TIME_SECONDS)

    except KeyboardInterrupt:
        print("\n\n--- Desk Observer Deactivated ---")
        print("Goodbye!")
        sys.exit(0)
</pre>
</details>

**\*\*\*Include a short video demonstrating the answers to these questions.\*\*\***

### Demo Video

https://github.com/user-attachments/assets/c3b75031-d1b6-427f-baca-531ab0b2e598

**Reflection**

During testing, I observed a consistent issue with the system's classification. Regardless of how clean or tidy I made my desk, Moondream's descriptions consistently led to a 'cluttered' or 'messy' result.

I hypothesize that this flaw is not in Moondream's description but in my simple, keyword-based analysis. This method is unreliable, or perhaps the prompt itself is encouraging these negative descriptions.

Therefore, for Part 2, I will try swtiching to google teachable machines to continue this projects. The Moondream approach relies on complex text parsing, which gets fragile (e.g., "key" vs. "keys" vs. "keyboard").

The Teachable Machine approach is much more direct and robust for this problem. You are training a model to directly classify the pixels into "messy" or "clean." It doesn't need to understand "what" a key is; it just learns that a certain pattern of pixels looks messy to you.

### Part 2.

After experimenting in Part 1, I aimed to build a system that observes the desk environment and provides real-time feedback about its condition.
This is part of a broader exploration of how machine learning models can enable environmental awareness in everyday spaces:

### System Flow

- Camera Capture → OpenCV continuously captures live video frames from the webcam

- Image Classification → Each frame is sent to a TensorFlow Lite model exported from Google Teachable Machine

- Prediction Display → The model predicts which class the frame belongs to (`default`, `cleaned`, or `messy`)

- Feedback Loop → The result is displayed both:

    - On the video feed (with text overlay)

    - In the terminal (for debugging and data observation)
  
---

### Example screenshots

**Default**

<img width="400" src="https://github.com/user-attachments/assets/f68c53ec-395a-49a6-8c83-82b5ae1cbed2" />

**Cleaned**

<img width="400" src="https://github.com/user-attachments/assets/f0b54b05-e4e4-4450-997c-41b1b22675e5" />

**Messy**

<img width="400" src="https://github.com/user-attachments/assets/b8959067-0605-4397-8ada-cbb3691c6b9f" />

### Code
<details>
    <summary><strong>Drop me</strong></summary>
    <pre>
from teachable_machine_lite import TeachableMachineLite
import cv2 as cv
import time

=== Setup paths ===
model_path = "v2_model.tflite"
labels_path = "v2_labels.txt"
image_file_name = "frame.jpg"

=== Initialize model ===
tm_model = TeachableMachineLite(model_path=model_path, labels_file_path=labels_path)

=== Start webcam ===
cap = cv.VideoCapture(0)

if not cap.isOpened():
    print("Cannot open camera")
    exit()

print("Camera opened. Press ESC to exit.")

=== Real-time loop ===
while True:
    ret, frame = cap.read()
    if not ret:
        print("Can't receive frame (stream end?). Exiting ...")
        break

    # Save a temporary frame for classification
    cv.imwrite(image_file_name, frame)

    # Run inference
    results = tm_model.classify_image(image_file_name)

    # Extract info safely
    label = results.get("label", "Unknown")
    confidence = results.get("confidence", 0.0)

    # Display label and confidence on screen
    text = f"{label} ({confidence:.2f}%)"
    cv.putText(frame, text, (20, 40),
               cv.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv.LINE_AA)

    # Print to terminal
    print(f"Prediction: {label} ({confidence:.2f}%)")

    # Show webcam window
    cv.imshow("Teachable Machine Cam", frame)

    # Press ESC (27) to exit
    k = cv.waitKey(1)
    if k % 255 == 27:
        print("ESC pressed, exiting.")
        break
    </pre>
</details>

### Video

https://github.com/user-attachments/assets/ab4c1a7e-8a56-4469-9904-758c2da67380


