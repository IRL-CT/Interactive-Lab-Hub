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

Instead of a standard digital or analog clock, the Raspberry Pi 5 runs a small VLM (ex. Moondream/FastVLM scale) locally. Every second, it captures an image from its camera and asks the VLM: *“What time is it?”*. The model outputs its “perceived time,” which is displayed on the PiTFT screen along with the ground-truth system time.  

We also log:  
- The image frame  
- The VLM’s predicted time  
- The true time  

This enables post-hoc analysis of accuracy. We can later tag images as “indoors” vs. “outdoors” (or other contextual tags) to see if environment affects performance (like artificial vs. natural light).  

The questions we explore:  
- How accurate is the VLM at telling time?  
- Are we ready to replace traditional timekeepers with AI perception?  
- Could trust in such a clock be measured in user studies?  

**Sketch**  
![IMG_5302](https://github.com/user-attachments/assets/a8aa2600-d298-4a1c-8271-d537bce888ee)

---

# Prep for Part 2
Done!  

---

# Lab 2 Part 2

## Modify the barebones clock to make it your own
I modified `screen_clock.py` to integrate the **VLT pipeline**. Instead of just printing system time, the script captures an image via Pi Camera, passes it to the local VLM, and shows both the **predicted “AI time”** and the **real time** side by side.  

This aligns with the theme: *If we trust LLMs for everything else, why not for interpreting time itself?*  

**Code:**  
I will place the link to the code on here soon, it is currently just on Pi.  

---

## Make a short video of your modified barebones PiClock
Will upload this soon, haven't edited it yet

---

After editing and testing, I committed the changes and pushed them back to my repo. Done!
