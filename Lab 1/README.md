

# Staging Interaction

\*\***Hongyiming Cui - hc2259**, 

**Xiang Chang - xc529**, 

**Qingxuan Yan - qy264**\*\*

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

\*\***Setting**  
The interaction takes place in the kitchen, while someone is preparing and cooking steak. The main interactive device is integrated into the range hood above the stove.  

**Players**  
- **Primary cook**: the person cooking the steak.  
- **The interactive device**: a light-based feedback system built into the range hood, displaying real-time cooking guidance.  
- **Possible bystanders**: roommates, family members, or guests in the kitchen who may also notice the light signals (they could help prevent accidents).  

**Activity**  
The cook places a raw steak in the pan and uses the interactive device to monitor doneness and temperature.  
Before starting, the cook inputs the steak’s weight and desired doneness (e.g., medium rare, medium, well-done) via a small control panel on the range hood.  
During cooking, the device continuously tracks the pan’s temperature and the steak’s cooking progress, displaying color-coded light signals:  
- **Green** → pan is still heating up, not ready.  
- **Yellow** → pan is at the optimal temperature, steak should be placed.  
- **Red (steady)** → pan is too hot, risk of burning.  
- **Red (flashing)** → urgent warning, steak is burning or overcooked.  

After the steak is placed, the device continues to monitor cooking, signaling with subtle changes if the steak risks being undercooked or burnt.  

**Goals**
- Prepare the steak safely and to the desired doneness without over/undercooking.
- Provide intuitive light-based guidance for timing and temperature to improve cooking results.
\*\*

Storyboards are a tool for visually exploring a users interaction with a device. They are a fast and cheap method to understand user flow, and iterate on a design before attempting to build on it. Take some time to read through this explanation of [storyboarding in UX design](https://www.smashingmagazine.com/2017/10/storyboarding-ux-design/). Sketch seven storyboards of the interactions you are planning. **It does not need to be perfect**, but must get across the behavior of the interactive device and the other characters in the scene. 

\*\***[Storyboard 1](/Storyboard1.jpeg)**\*\*

Present your ideas to the other people in your breakout room (or in small groups). You can just get feedback from one another or you can work together on the other parts of the lab.

\*\***Feedback from Xiang Chang:**

Nice flow overall—the storyboard clearly communicates setup → add steak → monitor → warn → done, and the use of light fits the brief. I’d tighten a few things: make color semantics intuitive (e.g., Blue/White = preheat, Yellow = add steak, Orange = cooking, Red = too hot, Green = done)\*\*

\*\***After forming group, we decided to continue with the following design of smart lamp**

**Setting**  
A bedroom at night, as the user winds down for sleep.  

**Players**  
- **Main user**: an adult preparing to sleep.  

**Activity**  
- The user begins reading before bed under the smart bedside lamp’s *Reading Mode* (comfortable brightness, neutral/cooler white for legibility).  
- When the user says “Good night” or after a set wind-down timer starts while reading, the lamp transitions into *Sleep Mode*:  
  - Brightness gradually dims over the wind-down period.  
  - Color temperature gradually warms (cool → warm amber) to reduce blue light and promote drowsiness.  
- If the user gets out of bed during the night, a low, warm guiding light gently turns on for safe movement.  
- When the user is fully asleep, the lamp fades out completely (e.g., after the wind-down completes and there is no interaction/motion for a set interval).  

**Goals**  
- **Main user**: read comfortably, ease into drowsiness, move safely at night, and receive subtle notifications without disturbance.  
- **Device**: use light (dimming + warming) to support relaxation, provide unobtrusive feedback, and automatically power off once the user is asleep.  

**Storyboard**  
*[Storyboard](/Lamp%20Storyboard.jpg)*  

**Feedback**  
I like how the brightness changes along with the user's activity. But how would you define the brightness for different settings? How does the light detect the user's activities — through motion capture or voice control?\*\*

## Part B. Act out the Interaction

Try physically acting out the interaction you planned. For now, you can just pretend the device is doing the things you’ve scripted for it. 

\*\***Are there things that seemed better on paper than acted out?**

On paper the user’s state is obvious; in acting it’s hard to tell if the user is truly asleep.

Small sleep movements easily false-trigger the light.
\*\*

\*\***Are there new ideas that occur to you or your collaborator that come up from the acting?**

We define light by mode, not fixed numbers: Reading = brighter neutral; Wind-down = gradually dimmer and warmer; Asleep = off/very low; Night path = low warm path light (bedside → door); Morning = gradually brighter and cooler (sunrise-like).

Activities are detected primarily by explicit commands (voice or tap). For automation, we add low-privacy sensing (mmWave/PIR or a bed pressure strip) to tell turning over from getting out of bed—no cameras. Optional phone alarm/quiet hours can trigger Morning Mode and suppress late-night flashes.
\*\*


## Part C. Prototype the device

You will be using your smartphone as a stand-in for the device you are prototyping. You will use the browser of your smart phone to act as a “light” and use a remote control interface to remotely change the light on that device. 

Code for the "Tinkerbelle" tool, and instructions for setting up the server and your phone are [here](https://github.com/IRL-CT/tinkerbelle).

We invented this tool for this lab! 

If you run into technical issues with this tool, you can also use a light switch, dimmer, etc. that you can can manually or remotely control.

\*\***Give us feedback on Tinkerbelle.**

**Pros**  
- Using a smartphone browser as a “light” prototype is quick to set up, easy to demo remotely, and clearly shows color/brightness transitions.  

**Cons**  
- Color gamut mismatch: The phone’s display gamut differs from the computer/preview display, so colors on the phone may not match the design intent.  
- No remote brightness control: The computer cannot control the phone’s system screen brightness; only on-page (CSS) brightness can be altered.i\*\*


## Part D. Wizard the device
Take a little time to set up the wizarding set-up that allows for someone to remotely control the device while someone acts with it. Hint: You can use Zoom to record videos, and you can pin someone’s video feed if that is the scene which you want to record. 

\*\***Include your first attempts at recording the set-up video here.**
[Setup Video](/initialsetup.mp4)
\*\*

Now, hange the goal within the same setting, and update the interaction with the paper prototype. 

\*\***Show the follow-up work here.** 

[Storyboard Updated](/Storyboard%20after%20update.jpeg)

**Update to the paper prototype**  
I added colors to the storyboard to show each state:  

- **Reading**: neutral white  
- **Wind-down**: gradually warmer, dimmer  
- **Asleep**: very low / off  
- **Night path**: low warm strip toward the door  
- **Morning (new)**: gradient orange → yellow → neutral white to simulate sunrise  
\*\*


## Part E. Costume the device

Only now should you start worrying about what the device should look like. Develop three costumes so that you can use your phone as this device.

Think about the setting of the device: is the environment a place where the device could overheat? Is water a danger? Does it need to have bright colors in an emergency setting?

\*\***Include sketches of what your devices might look like here.**

[Sketch1](/Sketch1.png)
[Sketch2](/Sketch2.png)
[Sketch3](/Sketch3.jpeg) \*\*

\*\***What concerns or opportunitities are influencing the way you've designed the device to look?**

**What concerns or opportunities are influencing the way you've designed the device to look?**  

- **Concerns**:  
  - The lamp will be used in a bedroom environment where glare or overly bright colors could disturb relaxation.  
  - It needs to minimize blue light at night to avoid disrupting circadian rhythms.  
  - Safety at night is critical: the design must provide just enough illumination to guide movement without waking the user fully.  

- **Opportunities**:  
  - A bedside lamp is a familiar form factor, so embedding smart light behaviors feels natural and unobtrusive.  
  - The device can enhance the bedtime routine by visually signaling transitions (reading → winding down → asleep).  
  - Its aesthetic can be calming and modern, doubling as both décor and functional technology. \*\*


## Part F. Record

\*\***Take a video of your prototyped interaction.**

[Prototype interaction1](./prototypeinteraction1.mp4)

[Prototype interaction2](./prototypeinteraction2.mp4)

[Prototype interaction3](./prototypeinteraction3.mp4)\*\*

\*\***Please indicate who you collaborated with on this Lab.**

We worked in a group including Hongyiming Cui (Marina), Xiang Chang, and Qingxuan Yan\*\*
Be generous in acknowledging their contributions! And also recognizing any other influences (e.g. from YouTube, Github, Twitter) that informed your design. 



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
