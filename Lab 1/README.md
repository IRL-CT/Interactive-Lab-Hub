We decided to have our light interaction be part of a club. When someone enters, the light will flash white. When someone exits, the light with flash black. We have different conditions. If there are 0-5 people in the club, the light falls back to a certain color, same thing with 5-10, 10-15, and 15-20. We also have special conditions. Once the amount of people reaches 20 inside the club, the light's default will be a strobe between red, green, and blue. Additionally, if people inside the club are raising their hands, the vibrancy of the light will adjust.

# Staging Interaction

\*\***Akashu Batu, Benthan Vu, Carrie Wang, Evan Fang, Sean Lewis, Xuesi Chen**\*\*

In the original stage production of Peter Pan, Tinker Bell was represented by a darting light created by a small handheld mirror off-stage, reflecting a little circle of light from a powerful lamp. Tinkerbell communicates her presence through this light to the other characters. See more info [here](https://en.wikipedia.org/wiki/Tinker_Bell). 

There is no actor that plays Tinkerbell--her existence in the play comes from the interactions that the other characters have with her.

For lab this week, we draw on this and other inspirations from theatre to stage interactions with a device where the main mode of display/output for the interactive device you are designing is lighting. You will plot the interaction with a storyboard, and use your computer and a smartphone to experiment with what the interactions will look and feel like. 

_Make sure you read all the instructions and understand the whole of the laboratory activity before starting!_



## Prep

### To start the semester, you will need:
1. Read about Git [here](https://git-scm.com/book/en/v2/Getting-Started-What-is-Git%3F).
2. Set up your own Github "Lab Hub" repository by forking the [Interactive-Lab-Hub repository](https://github.com/FAR-Lab/Interactive-Lab-Hub). To get lab updates, simply [use GitHub's "Sync fork" button when new content is available](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/syncing-a-fork).

3. Set up the README.md for your Hub repository (for instance, so that it has your name and points to your own Lab 1). You can [learn how to organize and format your README.md here](https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax). Make sure to include links to your submissions so they are easy to find.


### For this lab, you will need:
1. Paper
2. Markers/ Pens
3. Scissors
4. Smart Phone -- The main required feature is that the phone needs to have a browser and display a webpage.
5. Computer -- We will use your computer to host a webpage which also features controls.
6. Found objects and materials -- You will have to costume your phone so that it looks like some other devices. These materials can include doll clothes, a paper lantern, a bottle, human clothes, a pillow case, etc. Be creative!

### Deliverables for this lab are: 
1. 7 Storyboards
1. 3 Sketches/photos of costumed devices
1. Any reflections you have on the process
1. Video sketch of 3 prototyped interactions
1. Submit the items above in the lab1 folder of your class [Github page], either as links or uploaded files. Each group member should post their own copy of the work to their own Lab Hub, even if some of the work is the same from each person in the group.

### The Report
This README.md page in your own repository should be edited to include the work you have done (the deliverables mentioned above). Following the format below, you can delete everything but the headers and the sections between the **stars**. Write the answers to the questions under the starred sentences. Include any material that explains what you did in this lab hub folder, and link it in your README.md for the lab.

## Lab Overview
For this assignment, you are going to:

A) [Plan](#part-a-plan) 

B) [Act out the interaction](#part-b-act-out-the-interaction) 

C) [Prototype the device](#part-c-prototype-the-device)

D) [Wizard the device](#part-d-wizard-the-device) 

E) [Costume the device](#part-e-costume-the-device)

F) [Record the interaction](#part-f-record)

Labs are due on Mondays. Make sure this page is linked to on your main class hub page.

## Part A. Plan 

To stage an interaction with your interactive device, think about:

_Setting:_ Where is this interaction happening? (e.g., a jungle, the kitchen) When is it happening?

_Players:_ Who is involved in the interaction? Who else is there? If you reflect on the design of current day interactive devices like the Amazon Alexa, it’s clear they didn’t take into account people who had roommates, or the presence of children. Think through all the people who are in the setting.

_Activity:_ What is happening between the actors?

_Goals:_ What are the goals of each player? (e.g., jumping to a tree, opening the fridge). 

The interactive device can be anything *except* a computer, a tablet computer or a smart phone, but the main way it interacts needs to be using light.

\*\***Describe your setting, players, activity and goals here.**\*\*

Setting: This interaction is happening at the entrance to a club. It is happening at night-time since this is when clubs are generally active and lights are more conspicious. The club entrance/lobby and main floor, at night. Lighting cues must be legible outdoors at the door and indoors under show lighting.

Players: Visitors (primary), door staff/security (secondary), floor staff/DJ (secondary), occasional third parties (delivery, first responders).

Those who are involved in the interaction are the visitors of the club. Other people may include the security guard and staff of the club. However, the intention for the device is to be used by the visitors. Here is a list of the potential players in the setting:

1.) The visitors/general audience (intended audience for interactive device)

2.) The staff/security of the club who keep the club's operations running

3.) Any third party (first responders, delivery workers, etc.)

Activity: Entering/exiting triggers a flash cue at the entrance beacon; once inside, an ambient “default” color communicates occupancy. A “hands-up” gesture in the crowd increases vibrancy (brightness/saturation) of the current look.

Goals:

Visitors: immediate feedback that they’ve entered/exited; a fun ambient light that reflects crowd energy.

Staff: glanceable read on occupancy and hype level; safe, non-blocking signals.

Device: remain legible, avoid rapid flicker, fail safely.

Light logic (spec for prototype + show bible):

Entry: flash white (300 ms on, 200 ms off, 300 ms on), then return to default.

Exit: flash black (turn off 250 ms, on 250 ms, off 250 ms), then return to default.

Default color by occupancy (debounce counter with 1 s cooldown to prevent multiple beams on one person):

0–5: no light — calm/space available.

5–10: green — warming up.

10–15: yellow — party energy.

15–20: red — near capacity.

≥20 (capacity mode): 1 Hz strobe cycling red → green → blue (RGB every 1 s; 50% duty). Post signage or provide a Staff Override (see Safety).

Hands-up vibrancy: Let raised_ratio = (# hands up) / (estimated people inside).

Brightness maps from 35% → 100% as raised_ratio goes 0 → 0.6 (clamp at 100%).

Saturation maps from 70% → 100% over the same range.

Smooth with EMA: vibrancy_t = 0.8 * vibrancy_{t-1} + 0.2 * vibrancy_target.

Safety/overrides:
Quiet mode: long-press staff button → freeze current hue @ 25% brightness (no strobe).
Emergency: double-press staff button → solid red @ 100%, no animations, until cleared.

Storyboards are a tool for visually exploring a users interaction with a device. They are a fast and cheap method to understand user flow, and iterate on a design before attempting to build on it. Take some time to read through this explanation of [storyboarding in UX design](https://www.smashingmagazine.com/2017/10/storyboarding-ux-design/). Sketch seven storyboards of the interactions you are planning. **It does not need to be perfect**, but must get across the behavior of the interactive device and the other characters in the scene. 

\*\***Include pictures of your storyboards here**\*\*

<img width="1714" height="704" alt="image" src="https://github.com/user-attachments/assets/b2fcddae-702f-472b-8558-106215ff28e1" />
<img width="1805" height="636" alt="image" src="https://github.com/user-attachments/assets/85860e62-f682-4aeb-b9e0-24ed4c87cef8" />
<img width="573" height="624" alt="image" src="https://github.com/user-attachments/assets/22b364ca-e9b9-4008-91db-697dcf8ae0e6" />
<img width="1702" height="639" alt="image" src="https://github.com/user-attachments/assets/740e4637-4564-4f8c-9bc3-3eec49e66fd8" />
<img width="1695" height="661" alt="image" src="https://github.com/user-attachments/assets/0b1bd720-431d-4646-bee3-e2c5fbfc8e8c" />
<img width="907" height="443" alt="image" src="https://github.com/user-attachments/assets/41881384-79f8-405c-b0d7-a330b3f69d99" />
<img width="907" height="448" alt="image" src="https://github.com/user-attachments/assets/d5f715b2-225b-4dd1-be4f-7a24b9303ed1" />
<img width="2360" height="1640" alt="sb8" src="https://github.com/user-attachments/assets/cd54290b-7383-450c-89a5-eabdcb64a4d7" />

Present your ideas to the other people in your breakout room (or in small groups). You can just get feedback from one another or you can work together on the other parts of the lab.

\*\***Summarize feedback you got here.**\*\*

One feedback question was how the device worked or was activated. We illustrate some kind of "laser tripwire" from spy movies / kid's toy sections as the trigger for how the light knows when to activate. They then asked how the device knows enter vs. exit, and we suggested using two IR break beams (A then B = enter, B then A = exit) instead of one “laser tripwire,” plus debounce to avoid tailgating double-counts. We had some accessibility feedback comments about some color-only states are hard for some users (color vision deficiencies) and they suggested to pick high-contrast palettes, pair hues with temporal patterns (steady vs. breathing), and keep a legend at the door (we really liked this idea!). There was another comment about strobe safety due to epilepsy concerns. So, we propose both a non-strobing RGB step/rotate alternative and a “No-Strobe” venue mode. The last, but very insightful feedback, was about detection for the hands-up sensing. People liked the idea but flagged privacy if we used cameras. So we came up with some alternatives: manual “Hype” slider for staff/DJ, coarse overhead silhouette count, or letting the crowd tap the rope/rail to register hype.


## Part B. Act out the Interaction

Try physically acting out the interaction you planned. For now, you can just pretend the device is doing the things you’ve scripted for it. 

\*\***Are there things that seemed better on paper than acted out?**\*\*

Yes, we realized quickly that the entry/exit flashes were getting swallowed by ambient lobby light and felt too brief to notice in a crowd. We increased the white flash to a two-pulse pattern and added a short 200 ms black gap so it reads as “arrival” vs. “departure.” We also learned the occupancy color shifted too frequently during rushes; adding a 1 s debounce and a 5 s minimum dwell per range made the looks feel intentional rather than twitchy.

\*\***Are there new ideas that occur to you or your collaborator that come up from the acting?**\*\*

Yes, we decided that we needed either more creative interactions or more creative responses. We decided to take this both ways. For a more creative interaction, we decided that we should keep the base interactions but add that if visitors to the club raise their arms inside of the club, the vibrancy of the colors being displayed at the moment should adjust. For a more creative response, we added that if there are 20 or more people in the club, then the light should start a "strobe" effect that changes between red green and blue every second.


## Part C. Prototype the device

You will be using your smartphone as a stand-in for the device you are prototyping. You will use the browser of your smart phone to act as a “light” and use a remote control interface to remotely change the light on that device. 

Code for the "Tinkerbelle" tool, and instructions for setting up the server and your phone are [here](https://github.com/IRL-CT/tinkerbelle).

We invented this tool for this lab! 

If you run into technical issues with this tool, you can also use a light switch, dimmer, etc. that you can can manually or remotely control.

\*\***Give us feedback on Tinkerbelle.**\*\*

Tinkerbelle is great, and congratulations to whoever developed it, but coming at this from a developer who used to love building things in Flask, I would recommend that you just shift it to a Github or CFPages webapp since 90% of the students probably aren't changing the source code of it. You can still keep the source code available and encourage students to play with it, however, you shouldn't need to make them setup any sort of Python venvs etc. (even if the reqs are minimal) to run your app. For our group, we ended up poking a hole thru the firewall with a temporary CF tunnel to have it be accessible to everyone else (since the school WiFi is pretty restrictive to what local webapps you can run). Can easily extend it to have some kind "rooms" functionality so that multiple different groups can use the app at same time.

TLDR:

Accessibility: Update outdated do-it-yourself Flask implementation to an instantly usable static Cloudflare Pages or Github webapp

Rooms/multi-session: Add a “Create Room” flow with a 6-digit code so multiple groups can test simultaneously.


## Part D. Wizard the device
Take a little time to set up the wizarding set-up that allows for someone to remotely control the device while someone acts with it. Hint: You can use Zoom to record videos, and you can pin someone’s video feed if that is the scene which you want to record. 

\*\***Include your first attempts at recording the set-up video here.**\*\*

https://github.com/user-attachments/assets/0a4e45ad-4c9e-4194-9104-17312157bcc3

Now, change the goal within the same setting, and update the interaction with the paper prototype. 

\*\***Show the follow-up work here.**\*\*

https://github.com/user-attachments/assets/aa5b5205-edee-4be1-b460-c9f10be24fb1

## Part E. Costume the device

Only now should you start worrying about what the device should look like. Develop three costumes so that you can use your phone as this device.

Think about the setting of the device: is the environment a place where the device could overheat? Is water a danger? Does it need to have bright colors in an emergency setting?

\*\***Include sketches of what your devices might look like here.**\*\*

<img width="1551" height="1201" alt="image (37)" src="https://github.com/user-attachments/assets/dee812fb-445b-4d1b-abc3-ce9eb3ef025b" />

![IMG_20250828_212524007](https://github.com/user-attachments/assets/e64f7ed3-08d0-483a-95ad-54278cf13744)

<img width="2360" height="1640" alt="sketch_2" src="https://github.com/user-attachments/assets/f7fbf28c-ce7a-405e-8462-122a1eb9da04" />

![IMG_0119](https://github.com/user-attachments/assets/f0cb90a9-5420-42c4-a5f4-39ce5c470666)

![IMG_0120 (1)](https://github.com/user-attachments/assets/92946a66-4e85-4f0c-9814-bbf8113b9b92)

<img width="1007" height="730" alt="image" src="https://github.com/user-attachments/assets/120beb67-9c36-4841-b505-c11693c0ba40" />

![IMG_6649](https://github.com/user-attachments/assets/d4c68b1a-939e-47ac-8d1e-53b62bbcf5be)

![IMG_6659](https://github.com/user-attachments/assets/dd83f6b0-fd44-4647-9959-54e2dd3740c5)


\*\***What concerns or opportunitities are influencing the way you've designed the device to look?**\*\*

Some concerns we had when making the look of the device were how much of the light we wanted to show. We did some research into how lighting works at clubs and how these lights are setup. We ended up with different designs for how to block direct view of the LEDs but still keep the light readable (without blinding passerbys). We added a cardboard sleeve to diffuse the light into three bars, and also a aluminum foil wrapper (the light diffusion on the foil had quite the effect). We also created an acrylic glass prototype to really see how the light can influence the scene. We came up with some mounting prototypes as well so that it can mount to an eye-level surface. For aesthetics, we researched into modern clubs and tried to emulate that grunge dark, sleek, yet vibrant aesthetic.


## Part F. Record

\*\***Take a video of your prototyped interaction.**\*\*

(Full video)

https://github.com/user-attachments/assets/e651a4b7-4b95-41df-b12a-889222807931

**Click on the below image to play the video on YouTube**
**Interaction 1**
[![Interaction 1](https://img.youtube.com/vi/8-qJKf9TseE/maxresdefault.jpg)](https://youtu.be/8-qJKf9TseE)
**Interaction 2**
[![Interaction 2](https://img.youtube.com/vi/hpOWgV1T7n8/maxresdefault.jpg)](https://youtu.be/hpOWgV1T7n8)
**Interaction 8**
[![Interaction 8](https://img.youtube.com/vi/70Q2abh3BmU/maxresdefault.jpg)](https://youtu.be/70Q2abh3BmU)
**Music Credit: Seize the Day by Andrey Rossi**

\*\***Please indicate who you collaborated with on this Lab.**\*\*
Be generous in acknowledging their contributions! And also recognizing any other influences (e.g. from YouTube, Github, Twitter) that informed your design. 

\*\***The collaborators for this lab and their contributions are listed below**\*\*

\*\***Akash Batu: Storyboards #1, #2, #3, #4, #5, Wizarding Tinkerbelle**\*\*

\*\***Benthan Vu: Costume #1, Paper Prototype #1, Research & Feedback**\*\*

\*\***Carrie Wang: Wizarding the Device, Research & Feedback**\*\*

\*\***Evan Fang: Costume #2, Paper Prototype #2, Storyboard #8**\*\*

\*\***Sean Lewis: Storyboards #6, #7, Setting up Tinkerbelle**\*\*

\*\***Xuesi Chen: Costume #3, Paper Prototype #3, Demo Video Recording and Editing**\*\*

\*\***All: Ideating, Research, Video Enactment, Communication

# Staging Interaction, Part 2 

This describes the second week's work for this lab activity.


## Prep (to be done before Lab on Wednesday)

You will be assigned three partners from other groups. Go to their github pages, view their videos, and provide them with reactions, suggestions & feedback: explain to them what you saw happening in their video. Guess the scene and the goals of the character. Ask them about anything that wasn’t clear. 

\*\***Summarize feedback from your partners here.**\*\*

## Make it your own

Do last week’s assignment again, but this time: 
1) It doesn’t have to (just) use light, 
2) You can use any modality (e.g., vibration, sound) to prototype the behaviors! Again, be creative! Feel free to fork and modify the tinkerbell code! 
3) We will be grading with an emphasis on creativity. 

\*\***Document everything here. (Particularly, we would like to see the storyboard and video, although photos of the prototype are also great.)**\*\*

We decided to have our light interaction be part of a park and our creativity is adding computer vision for input. When someone enters, the light will flash white. When someone exits, the light with flash black. We have different conditions. If a fight breaks out inside of the park, the lights will flash red. If an unattended child leaves the park, the lights will flash red. We also have an alert sound occurring when there is a red light flashing event, to better notify others.

Storyboards are a tool for visually exploring a users interaction with a device. They are a fast and cheap method to understand user flow, and iterate on a design before attempting to build on it. Take some time to read through this explanation of [storyboarding in UX design](https://www.smashingmagazine.com/2017/10/storyboarding-ux-design/). Sketch seven storyboards of the interactions you are planning. **It does not need to be perfect**, but must get across the behavior of the interactive device and the other characters in the scene. 

\*\***Include pictures of your storyboards here**\*\*
<img width="2480" height="3508" alt="image" src="https://github.com/user-attachments/assets/f11b668f-a6c2-4a75-825e-dd9dadb15843" />
<img width="2480" height="3508" alt="image (1)" src="https://github.com/user-attachments/assets/94e97eaa-a790-48e2-a38c-1b7751270596" />

**\*\*Product Sketch & Physical Prototype:**\*\*

Pillar Design
<img width="3259" height="2027" alt="Pillar" src="https://github.com/user-attachments/assets/b18b7897-40bb-4933-a3fa-4f79d764e125" />

Ground Light Design
<img width="3259" height="1162" alt="Ground Light" src="https://github.com/user-attachments/assets/1751697f-1b58-47ed-8c6a-a851cdf0354f" />

Other Design
<img width="3259" height="1426" alt="Other Design" src="https://github.com/user-attachments/assets/381432eb-5fdf-40f4-bdee-ec834f774a1e" />



\*\***Videos:**\*\*


https://github.com/user-attachments/assets/e3c67663-537a-460a-9344-a8d08dc73841


https://github.com/user-attachments/assets/1bf9b39f-38d7-4608-a86c-87f9ff9026ba


https://github.com/user-attachments/assets/d5f1902b-a91f-428e-a49e-90341c0f0cea





