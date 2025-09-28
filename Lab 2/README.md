# Interactive Prototyping: The Clock of Pi
**Sean Hardesty Lewis (Solo)**

Inspiration for my core project idea came from discussions around LLMs as “decision engines” and recent research papers that were using LLM-as-judge I reviewed as part of a conference.
I also referenced GitHub repos on Raspberry Pi display clocks and various YouTube demos of PiTFT usage.

---

## Prep

### 1. Set up your Lab 2 Github  
Done!  

### 2. Get Kit and Inventory Parts  
Done!  

### 3. Prepare your Pi for lab this week  
Done!  

---

## Overview
For this assignment, I connected to my Pi, ran the sample clock code, set up the RGB display, tested the demos, and then modified them. In Part 2, I created a conceptual and working prototype of a new clock: **VLT (Vision-Language-Time)**, where time itself is interpreted by a vision-language model running on the Raspberry Pi.

---

## Part A. Connect to your Pi
Done!  

---

## Part B. Try out the Command Line Clock
Done!  

---

## Part C. Set up your RGB Display
Done!  

---

## Part D. Set up the Display Clock Demo
Done!  

---

## Part E. (Now moved to Lab 2 Part 2)
Done!  

---

## Part F. (Now moved to Lab 2 Part 2)
Done!  

---

## Part G. Sketch and brainstorm further interactions and features

For Part 2, I propose **Vision-Language-Time (VLT)**:  

Instead of a standard digital or analog clock, the Raspberry Pi 5 runs a small VLM (ex. Moondream/FastVLM scale) locally. As often as it can (due to compute limitations), it captures an image from its camera and asks the VLM: *“What time is it?”*. The model outputs its “perceived time,” which is displayed on the PiTFT screen along with the ground-truth system time.  

We also log:  
- The image frame  
- The VLM’s predicted time  
- The true time  

This gives us the ability to perform an analysis of accuracy afterwards. We can tag images as “indoors” vs. “outdoors” (or other contextual tags) to see if environment affects performance (like artificial vs. natural light), etc.

The questions we can explore:  
- How accurate is the VLM at telling time?  
- Are we ready to replace traditional timekeepers with AI perception?  
- Could trust in such a clock be measured in user studies?  

**Sketch**  
![IMG_5302](https://github.com/user-attachments/assets/a8aa2600-d298-4a1c-8271-d537bce888ee)

The above image was made with AI as a double-meaning joke for "We trust AI for everything..."

Here is my (hand-drawn!) image:

![WIN_20250928_16_33_52_Pro](https://github.com/user-attachments/assets/603c93f9-2102-4eba-97c1-d920b15ff1bb)

---

# Prep for Part 2
Done!  

---

# Lab 2 Part 2

## Modify the barebones clock to make it your own

I created `screen_clock_vlm.py` based on `screen_clock.py` to for our **VLT pipeline**. Instead of just printing system time, the script captures an image via connected webcam, passes it to the local VLM, and shows both the **predicted “AI time”** and the **real time** side by side.  

=======
## Assignment that was formerly Lab 2 Part E.
### Modify the barebones clock to make it your own

Does time have to be linear?  How do you measure a year? [In daylights? In midnights? In cups of coffee?](https://www.youtube.com/watch?v=wsj15wPpjLY)

Time is measured based on the compute speed of our VLM/LLM. So about once every ~10-20 seconds. We measure the time with the current image's lighting conditions. Obviously this is fed into the VLM/LLM so we are only getting the "scraps" or downstream of whatever the quality/training of the models we use are. But- that is the point of the project in itself, yielding control over something relatively simple (like calculating time) to a trained program.

### Notice:
**I had to modify the idea slightly since VLMs tend to be trained on lots of images of clocks with "10:10" or "12:12". This led to prompts that ask the VLM for time nearly always resulting in these times. So, to fix this, I instead ask the VLM for what it is good at: a description of the image, specifically the lighting conditions. Then, I pass the VLM's description of the image to a local Qwen 0.5B Instruct model running via Ollama on the RPI5 and it guesses the time for us.**

Some examples of VLM failure (asking directly for time):

| Image | VLM Time | Actual Time |
|-------|-----------------|----------------|
| ![Image 2](https://github.com/user-attachments/assets/c3caf0ba-c712-407f-b692-6c8125ba0d07) | 10:10 | 16:11 |
| ![Image 1](https://github.com/user-attachments/assets/6d38ada6-72fa-4ad6-9881-12e08d596064) | 10:10 | 16:11 |

The exact prompt used on the VLM is:
```
Describe only observable lighting cues. Describe environment/sky/weather; natural light (direct vs diffuse, where it enters, sun patches/glare); shadows (presence, edge sharpness, relative length, direction); artificial lights (which sources are on, brightness low/medium/high, color warm/neutral/cool); overall brightness/exposure (very dark/dim/medium/bright, blown highlights, deep shadows, noise, motion blur); windows/openings and orientation hints; secondary clues (streetlights on, blinds/shades state, screen glow); brief caveats/confidence.
```

The exact prompt used on the Instruct model is:
```
You are a time estimator. Based ONLY on the following visual/lighting description, "
        "estimate the local clock time as HH:MM in 24-hour format. "
        "If uncertain, give your BEST plausible estimate. "
        "Output ONLY the time in the format HH:MM. No words, no seconds, no explanations.\n\n"
        "Description:\n"
        f"{vlm_text.strip()}\n\n"
        "Answer:\n"
```

Can you make time interactive? You can look in `screen_test.py` for examples for how to use the buttons.

When you click on the buttons it will cycle (forward or back) through the time screen, the last image taken, and the last VLM description of the image (truncated for space).


Please sketch/diagram your clock idea. (Try using a [Verplank diagram](https://ccrma.stanford.edu/courses/250a-fall-2004/IDSketchbok.pdf))!

My Verplank diagram:
![WIN_20250928_16_34_38_Pro](https://github.com/user-attachments/assets/0af36c34-d86c-4091-ac76-0c2da1e47799)

*If we trust LLMs for everything else, why not for interpreting time itself?*  

:)

**Code:**  
The following code files were added for this project:
- **screen_clock_vlm.py**: inference for program, will run our app that takes an image, captions it, passes it to local LLM, and then shows the predicted time and real time (as well as saving the image, times, etc. in bg)
- **fastvlm_server.mjs**: local FastVLM server for RPI5

To run, I recommend a venv for installing the reqs to inference the HF model. All you need to do is run `python screen_clock_vlm.py`. You can add an optional -o argument if you are running the VLM somewhere else (it is very slow on RPI5, about ~15s per request, I ended up using a CF tunnel and my PC to get this much faster- see code for where you can input your tunnel URL).

Note about AI usage: Copilot was used to help make the script for the clock. While I already had an example script from the official HF page, I used Copilot to draft up the filter functions, drawing to screen (with some help from the screen_test.py script), and logging.
An early issue I encountered was the screen_boot.py constantly running in the background, so in this script this is some preempting of it to effectively remove its control over the pitft screen.

Please see videos below for the usage.

---

## Make a short video of your modified barebones PiClock

Video of VLT pipeline working:

https://github.com/user-attachments/assets/7b9f53a8-2b60-4965-a5ec-6f75ebe499de

Video of VLT interaction with last image, last VLM output, time screen:

https://github.com/user-attachments/assets/8d9d3851-ec70-4a5a-9037-bad438787a62

Some examples of usage:


| Image | VLM Description | Perceived Time | Actual Time |
|-------|-----------------|----------------|-------------|
| ![Image 2](https://github.com/user-attachments/assets/89d06a83-db95-43e2-ac32-0c44428fd44f) | does not provide clear evidence of natural light sources like windows or outdoor elements, but the lack of brightness suggests it might be either an overexposed photograph or a room with minimal natural light. The overall impression is one of tranquility and stillness. As for the second part of your question, there are no discernible natural light indicators such as sunbeams, shadows, or glare that would confirm the presence of direct or indirect natural light in the room at the time the photo is taken. | 01:00 | 16:52 |
| ![Image 1](https://github.com/user-attachments/assets/40698baa-ed94-41ae-a73e-978cbfa695f6) | lighting being on, as there are no visible lights turned on. The windows are open, as evidenced by the visible curtain and the way the light is entering the room, but the curtains are drawn back, allowing for unobstructed light to enter. The sky outside is clear, with no visible clouds, suggesting fair weather conditions. | 15:00 | 16:52 |
| ![Image 3](https://github.com/user-attachments/assets/5a359655-fe5a-4cc0-aaa7-9e64967a99e8) | high-rise buildings and smaller structures, possibly a downtown area. The orientation of the buildings and the angle of the shot suggest that this is a view from a high vantage point, such as a skyscraper or a tall building. The lack of any visible movement or activity in the scene implies a moment of stillness, perhaps early morning or late afternoon. | 06:00 | 16:54 |
| ![Image 1](https://github.com/user-attachments/assets/d0dc26be-2e6a-40f1-8cb1-56d3a2723be8) | sun provides ample light. The image does not show any motion blur, indicating that the camera was still when the photo is being taken. The windows' state is not entirely clear due to the angle and focus of the shot, but they do not appear to be open, as there is no visible gap between the window and the frame. | 09:30 | 16:55 |
| ![Image 4](https://github.com/user-attachments/assets/114ef6d3-80ee-4ac7-a68f-8fe288b86424) | with ambient indoor lighting. The lack of sharp shadows and the presence of soft edges throughout the image contribute to a calm and serene atmosphere. There is no indication of motion blur or other photographic effects, and the image does not provide any clues about the time of day beyond the general impression of daytime. The simplicity of the composition focuses attention on the texture of the material, rather than any specific environmental details. | 09:00 | 16:58 |
| ![Image 1](https://github.com/user-attachments/assets/27cae21b-c109-4bad-9702-8aebb17685e6) | Not appear to be outdoors, given the lack of natural elements like trees or sky. The decor, including the posters, is consistent with a personal space, possibly a living room or a bedroom, where one might relax and enjoy the ambiance created by the lighting. The presence of the lamp and the style of the posters suggest a preference for a certain aesthetic or thematic decor, which could be reflective of the occupant's personal taste or interests. | 08:30 | 17:06 |


---

