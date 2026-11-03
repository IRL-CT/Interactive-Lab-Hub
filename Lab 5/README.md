# Observant Systems: Overnight Sensation

**NAMES OF COLLABORATORS HERE**
Partner: Shifeng Hong (Sh2769) https://github.com/mado0512/Interactive-Lab-Hub 

**Please indicate anyone that helped with this Lab here.**
Be generous in acknowledging their contributions! And also recognizing any other influences (e.g. from YouTube, Github, Twitter) that informed your design. 

# Part 1

## Part A. 
### Set up your Pi for on-device AI

***Include a screenshot of ollama list showing your models.***

Ollama list:
<img width="548" height="79" alt="Screenshot 2026-10-21 at 10 40 26 AM" src="https://github.com/user-attachments/assets/e987d627-b7b4-45aa-b767-cf0f3f769425" />


## Part B. 
### See: recognize people in real time with YOLO

***Include a short video or screenshots of your experiments with the person detection. Write down three situations where it did not see you, or saw a person who was not there, and what you think the cause was.***

I actually had more trouble getting YOLO to not detect me than I expected. I was surprised by how sensitive it was, as it could detect a person sitting pretty far behind me who appeared very small in the camera frame. This made me assume that YOLO doesn't necessarily need to see a person's entire face or body to classify them as a “person.” Instead, it seems capable of identifying partial visual features associated with a person. For example, my hand was still detected as a person even when I was holding up my phone case.

<img width="616" height="484" alt="Screenshot 2026-10-22 at 10 36 18 AM" src="https://github.com/user-attachments/assets/1b52f6f3-de3f-4371-b0aa-c07b1da7fe74" />
<img width="643" height="534" alt="Screenshot 2026-10-22 at 10 34 15 AM" src="https://github.com/user-attachments/assets/c8bc0e77-3244-43bb-a3c3-38f0dab38679" />

What surprised me most, however, was that YOLO could still recognize me when only my torso was in the frame. I had assumed that wearing a large, solid-colored sweater would make it harder for the model to identify me, since there were fewer visible details. Although the detection occasionally flickered, YOLO was still able to recognize me as a person. This showed me how capable the model is of detecting people even when only part of the body is visible or when clothing obscures some of the usual visual features.

<img width="648" height="561" alt="Screenshot 2026-10-22 at 10 29 54 AM" src="https://github.com/user-attachments/assets/91e31627-a7af-4842-b147-ccb64c432f57" />
<img width="645" height="566" alt="Screenshot 2026-10-22 at 10 31 53 AM" src="https://github.com/user-attachments/assets/c0ecebfd-efe9-4805-92f4-ed19d4f48732" />

## Part C. 
### See more: hands and pose with MediaPipe

\*\*\***Include a screenshot or short video of the hand pose demo, and write how you might use face, hand or body pose tracking in your observant system.**\*\*\*

<img width="701" height="612" alt="Screenshot 2026-10-21 at 6 40 45 PM" src="https://github.com/user-attachments/assets/894dff6d-c25c-4223-8c6e-26f66d19d331" />

My partner and I were thinking of using facial movements as the focus of our project. More specifically, we want to explore whether a computer vision system can detect when a user's eyes and mouth are open or closed in real time. The system would analyze facial features captured by a camera and classify their states based on visible movements. For example, it could identify when a user blinks, keeps their eyes closed for an extended period, or opens and closes their mouth.

## Part D. 
### Reason: run Qwen on the Pi with Ollama

***Ask Qwen three questions to answer. Paste the questions, the answers and how long each took. Try one of them with qwen3:0.6b and compare.***

Below are the three questions I asked. My last two questions were comparing how using the model would effect the responses. I found that using qwen3:0.6B made the response time shorter, probably because its responses were briefer and less detailed than when I used the other model. 

1.  python ask_qwen.py --image snap.jpg "What is in this photo?"
A close-up selfie of a young woman with dark hair, wearing a gold ring on her index finger and making a peace sign.

2. python ask_qwen.py --model qwen3:0.6b "Tell me briefly about TikTok."
TikTok is a social media platform where users share short, creativevideos, often called "tiktoks." It's popular for people who want toexpress themselves or connect with others. The platform has a largeuser base and a wide range of content, from music and dance to foodand lifestyle. It's known for being a hub for trends and trends.
	
[qwen3:0.6b, 12.2 s]

3. python ask_qwen.py "Tell me briefly about TikTok."
TikTok is a social media platform that allows users to create and share videos, primarily focusing on music, trends, and entertainment.nIt has grown into one of the largest digital ecosystems by enablingcreators to reach millions of people instantly through short-form content. The service connects users with each other via comments, likes, shares, and stories to foster community engagement and discovery.
	
[qwen3.5:0.8b, 14.3 s]

---

# Lab 5 Part 2: Overnight Sensation

## Part F. 
### Read Part 2 and storyboard your night-time interaction

Storyboard a night-time interaction built on your observant system, in three panels:

1. **Before bed.** How does the person hand the night over, and how does the device acknowledge it?
2. **While asleep.** What does the device watch or work through?
3. **When awake.** What is the one thing the person learns, and in what medium?

\*\*\***Insert ideas, sketches, Verplank diagrams and storyboards for your night-time interaction here.**\*\*\*

For our project, my partner and I are planning on making a sleep monitoring device that detects snoring and potential signs of sleep apnea. The device will log how often these instances occur so that users can better understand their sleep patterns and improve their sleep hygiene.

We currently plan to set up a camera on the headboard of the bed, angled so that it can see the user's face. Users will turn on the device by pressing a button before going to sleep. Once the system detects that the user's eyes have been closed for five consecutive minutes, it will assume that the user has fallen asleep and move on to the second phase, which focuses on detecting snoring and possible signs of sleep apnea.

We plan to achieve this by detecting when the user's mouth is open and, if time permits, analyzing audio to identify snoring sounds. If the system detects both an open mouth and snoring, it will record the event in a log, including the time it occurred and a short video clip of the event. In the morning, users will be able to review the log to see how frequently these events occurred throughout the night. This could help users recognize patterns in their snoring and become more aware of their sleep habits.

Storyboard: 

<img width="1385" height="771" alt="Screenshot 2026-10-22 at 11 12 04 AM" src="https://github.com/user-attachments/assets/8549331c-9eab-461f-b441-c802a357e9b7" />

## Prep for Part 2
\*\*\***Post your revised storyboard here.**\*\*\*

We received feedback from one of our classmates who said that the snoring aspect seems interesting. They noted that there may be instances of confusion where the user may trigger another event so audio cues may help. They also made comments that some more interactive elements would be nice. 

With this feedback in mind we made the following revisions:

	1. Instead of a button to activate, we decided on triggering the system with Quiet Coyote.  We thought Quiet Coyote was appropriate, since it was often used to signal children to calm down and be quiet. 
	
	2. We also added more audio elements, such as "good night", "good morning", and a verbal sleep quality report so that users would know when the system was working/processing, and it'd offer more convenient, natural interaction. 
Having music play to let users know its time to sleep is also a subtle way users know to care more about their sleep.

<img width="956" height="721" alt="Screenshot 2026-11-01 at 10 22 34 AM" src="https://github.com/user-attachments/assets/337fe215-3c88-4e50-9357-f2ecca8ebb4f" />

***Describe the interaction before.***

Users will give the system a bedtime, such as 11pm. 15 minutes before the bedtime (in this case, 10:45pm), calming music will begin playing to let users know its time to go to bed. Users will be able to stop the music/let the system know they're about to sleep by signaling Quiet Coyote.Once the system processes the Quiet Coyote, a LED slowly pulses red and the system says "Good Night". 

I was responsible for programming the before bedtime portion of the project. I utilized ChatGPT, Piper for the speech, and mediapipe for the camera vision. Below is a video showing how the program works. 

Code Link: https://github.com/chonjessica23/Interactive-Lab-Hub/blob/Fall2026/Lab%205/quiet_coyote_p1.py

https://drive.google.com/file/d/1TRhDM_q4PxSXFP7iWNiHiMuxS9sRXQ5v/view?usp=drive_link

***Screenshots or videos of the running system.***

**Bedtime Interaction**

Once the system went into "sleep mode", the camera would detect 3 events: mouth open, instances of snoring, and instances when the user left the screen, perhaps to go to the bathroom, get a late night snack, etc. We believed these elements would help determine the user's sleep quality, discussed later in this documentation. Snoring was marked when sound was detected above a certain decibel threshold, while the mouth being open was detected by determining the distance between the points on the upper and lower lip, and setting a trigger threshold. The bedtime portion ends when the user signals Quiet Coyote again. All these instances were tracked in a separately created log file that will be used for the morning portion. 

This portion was handled by Shifeng. A video demonstration is below. 

https://drive.google.com/file/d/1FJmmQnf50g7aOtpMr3x_jOTYo-hQbLKE/view?usp=drive_link

**Morning Interaction**

Once we both finished our parts, we sat together using AI to combine both our files and help create the morning report. The system compiles all the information created during the bedtime interaction that then writes a report on the minipi screen, rating your sleep quality and giving percentage of your time either snoring, having your mouth open, or disappearing. This report is also read out loud to users as well. 

Link to full code: https://github.com/chonjessica23/Interactive-Lab-Hub/blob/Fall2026/Lab%205/quiet_coyote_night.py

[Video of it all working together:](https://drive.google.com/file/d/135YGaPZvVVAInZDiwK7Yw9aRUJEGCDgq/view?usp=drive_link) 

**Real testing**

<img width="1920" height="1440" alt="IMG_20261030_232847" src="https://github.com/user-attachments/assets/3235317b-99cc-4e30-896b-5c275616994c" />

Shifeng tested the program in his dorm and found the following matters comeup:

	1. Because of the bedframe, he was limited in how he could set up the camera which impacted how close the camera was to the face. This in turn impacted the amount of room a user had to signal Quiet Coyote, and changed our mouth distance threshold. 
	
	2. We thought having the LED shine brightly would be enough to illuminate the face for the camera to detect features, but found that more light was needed instead. So this system would only work if users slept with a night light as well. 

If we had to iterate this project again or anyone else wanted to try, I would recommend getting the exact dimensions of the bed frame and camera height so you could anticipate those thresholds and positioning better. I would also look for alternative equipment that could perhaps capture imaging in the dark better, or alternative directions such as incorporating a soothing light. 
