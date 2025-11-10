# Distributed Interaction

Viha Srinivas (me), Nikhil Gangaram, Sachin Jojode, Arya Prasad

For submission, replace this section with your documentation!

---

## Prep

1. Pull the new changes
2. Read: [The Presence Table](https://dl.acm.org/doi/10.1145/1935701.1935800) ([video](https://vimeo.com/15932020))

## Overview

Build interactive systems where **multiple devices communicate over a network** using MQTT messaging. Work in teams of 3+ with Raspberry Pis.

**Parts:**
- A: Learn MQTT messaging
- B: Try collaborative pixel grid demo  
- C: Build your own distributed system

---

## Part A: MQTT Messaging

1. **Party Lights:** Each Pi senses sound or light and sends colorful flashes to a shared web grid that reacts like a disco.
2. Mood Wall: Each Pi sends a color based on room lighting or emotion, forming a shared “mood board.”
3. Distributed Band: Each Pi plays a different sound when triggered, together they form live music.
4. Presence Mirror: Each Pi lights up when someone is nearby, showing who’s “present” across locations.
5. Fortune Machine: Each Pi sends a random value that combines into one group-generated “fortune” message.

## Part B: Collaborative Pixel Grid
![IMG_7852](https://github.com/user-attachments/assets/8ef8b5a9-216d-4727-a011-1c21fc465287)
![IMG_7853](https://github.com/user-attachments/assets/2648c689-1285-4f56-8af0-898bd2f2f76f)

## Part C: Make Your Own

1. Project Description

For our final project, we’re developing gesture-controlled modules that serve as the foundation of our system. The concept involves using low-cost computers, like Raspberry Pis, to communicate with a central computer (our laptops) and collectively maintain an accessible global state. We designed two gestures inspired by American Sign Language (ASL) that allow users to modify this shared state across all connected devices. In our prototype, these gestures let users cycle through the colors of the rainbow in opposite directions.

2. Architecture Diagram
<img width="626" height="621" alt="Screen Shot 2025-11-10 at 9 39 33 AM" src="https://github.com/user-attachments/assets/f08ec067-4430-4169-bee3-fe4878c2ff6e" />
<img width="637" height="644" alt="Screen Shot 2025-11-10 at 9 39 54 AM" src="https://github.com/user-attachments/assets/5177aa9d-8656-4a83-9425-c7ab4b644523" />

3. Build Documentation
We broke our process down into 3 steps:
pi-pi communication: https://www.youtube.com/watch?v=l3sK-Un6r_g
gesture control: youtube.com/shorts/ilUMCtHcV4I?feature=share
integration: https://www.youtube.com/shorts/WWuHhcyBsaM?feature=share

4. User Testing
- Sachin’s girlfriend, Thirandi, tested the system while visiting.
- She preferred not to be on camera but thought the concept was fun and creative.
- She noted that the latency made the system feel unfinished, since the response wasn’t instantaneous.
- She also mentioned that having only a few gestures made the interaction feel less intuitive.

Stephanie: 

**5. Reflection**
- The software modules were stable and reliable, thanks to using well-tested and proven technologies.
- The computer vision pipeline in its early stages was jumpy and occasionally misread user gestures.
- Arya refined the vision pipeline, greatly improving accuracy and responsiveness.
- Sensor events from the camera act as triggers, which are sent through the MQTT network to update other Raspberry Pis.
- Gemini assisted during the ideation phase, helping refine the written content, generate visuals for the sketch and control flow diagram, and support parts of the code development.
- All team members contributed to both idea generation and software development throughout the project.

