# Interactive Prototyping: The Clock of Pi

**No collaborators**

Does it feel like time is moving strangely during this semester?

For our first Pi project, we will pay homage to the [timekeeping devices of old](https://en.wikipedia.org/wiki/History_of_timekeeping_devices) by making simple clocks.

It is worth spending a little time thinking about how you mark time, and what would be useful in a clock of your own design.

**Please indicate anyone you collaborated with on this Lab here.**
Be generous in acknowledging their contributions! And also recognizing any other influences (e.g. from YouTube, Github, Twitter) that informed your design.
Lab Prep is extra long this week. Make sure to start this early for lab on Thursday.

1. ### Set up your Lab 2 Github

Before the start of lab Thursday, ensure you have the latest lab content by updating your forked repository.

**📖 [Follow the step-by-step guide for safely updating your fork](pull_updates/README.md)**

This guide covers how to pull updates without overwriting your completed work, handle merge conflicts, and recover if something goes wrong.

2. ### Get Kit and Inventory Parts

Prior to the lab session on Thursday, taken inventory of the kit parts that you have, and note anything that is missing:

***Update your [parts list inventory](partslist.md)***

3. ### Prepare your Pi for lab this week

[Follow these instructions](prep.md) to download and burn the image for your Raspberry Pi before lab Thursday.

## Overview

For this assignment, you are going to

A) [Connect to your Pi](#part-a)

B) [Try out cli_clock.py](#part-b)

C) [Set up your RGB display](#part-c)

D) [Try out clock_display_demo](#part-d)

E) [Modify the code to make the display your own](#part-e)

F) [Make a short video of your modified barebones PiClock](#part-f)

G) [Sketch and brainstorm further interactions and features you would like for your clock for Part 2.](#part-g)

## Part D.

### Set up the Display Clock Demo

Work on `screen_clock.py`, try to show the time by filling in the while loop (at the bottom of the script where we noted "TODO" for you). You can use the code in `cli_clock.py` and `stats.py` to figure this out.

<img src="interaction/media/partD.JPG" alt="Demo pic" width="250"/>

## Part G.

## Sketch and brainstorm further interactions and features you would like for your clock for Part 2.

1. I've explored several different ideas along quite different tracks:
   <img src="interaction/media/Sketch-2.jpg" alt="Sketch 2" width="250"/>
2. Of all the ideas I've decided to explore the "relaxation" clock idea and the "coding clock" idea more in depth.

#### coding clock

- Here's the storyboard for one of the more promising ideas - coding clock! This is entirely for developers like me who push commits on the daily (for the job!) and we experience time in terms of pull requests and github commits.

<img src="interaction/media/Sketch-1.jpg" alt="Sketch 1" width="600"/>

- Here's a more detailed view on the interaction design and user flow:

<img src="interaction/github/frame1.png" alt="frame 1" width="250"/>
<img src="interaction/github/frame2.png" alt="frame 2" width="250"/>
<img src="interaction/github/frame3.png" alt="frame 3" width="250"/>
<img src="interaction/github/frame4.png" alt="frame 4" width="250"/>

#### relaxation/wellness clock

- Here's the storyboard for the relaxation/wellness clock idea. This idea is for people who often lose track of time at work, and often end up having a lot of stress. The purposegit of this device is to increase the quality of life and try to provide a better work/life balance for people who are busy.

<img src="interaction/wellness/story1.png" alt="frame 1" width="500"/>
<img src="interaction/wellness/story2.png" alt="frame 1" width="500"/>


- Here's a more detailed view on the interaction design and user flow

<img src="interaction/wellness/frame1.png" alt="frame 1" width="250"/>
<img src="interaction/wellness/frame2.png" alt="frame 2" width="250"/>
<img src="interaction/wellness/frame3.png" alt="frame 3" width="250"/>
<img src="interaction/wellness/frame4.png" alt="frame 4" width="250"/>
<img src="interaction/wellness/frame5.png" alt="frame 5" width="250"/>

* Feedback from Zoe Tseng (yzt2):

```
I love how clear the user flow is and the simplicity of the UI, consider adding more colors and visuals if possible.
```

* Feedback from Jessica Hsiao (dh779):

```
It's clear to you as the designer but the user may not know how to start the clock. Consider adding instructions to the screen so the user knows how to interact with it.
```

* Image source - collaborated with Claude. Here's my prompt:

```
Generate image frame by frame

user has been working for a long time and wants a break
user looks at the device and is greeted by a warm, welcoming message
user looks at a menu that has a list of potential activities they can participate
user selects an activity and there's a clock that can show how much time they need to break before they should go back to working
user finishes the activity and sees a rewarding, cute message before heading back to work
for frame 3, don't show icon
change frame 4 into a "foot bath" activity and add a picture of foot bath please
for frame 1, just show someone who's super tired in front of a computer


```

# Lab 2 Part 2

## Assignment that was formerly Lab 2 Part E.

### Modify the barebones clock to make it your own

Does time have to be linear?  How do you measure a year? [In daylights? In midnights? In cups of coffee?](https://www.youtube.com/watch?v=wsj15wPpjLY)

Can you make time interactive? You can look in `screen_test.py` for examples for how to use the buttons.

Please sketch/diagram your clock idea. (Try using a [Verplank diagram](https://ccrma.stanford.edu/courses/250a-fall-2004/IDSketchbok.pdf))!

**We strongly discourage and will reject the results of literal digital or analog clock display.**

\*\*\***A copy of your code should be in your Lab 2 Github repo.**\*\*\*

## Assignment that was formerly Part F.

## Make a short video of your modified barebones PiClock

### Prototype process

#### User Flow & Features

Based on the feedback and the storyboards,

<img src="interaction/wellness2/userflow.png" alt="frame 1" width="250"/>

And from the flow, I derived several interaction points and features.

<img src="interaction/wellness2/feature.png" alt="frame 1" width="250"/>

Image source: Figma, designed


#### Iterative Design

1. Welcome message

- This is the entry point where the user interacts with the device.
- I explored some ideas for welcoming messages, and what kind of emotion will the user feel during the interaction

  - List of emotions that could work:

    - Gentle,Caring,Calming
    - Playful
    - Motivational
    - Time-aware
  - Some keywords that could work:

    - invitation - "let's refresh"
    - inquiry - "ready for it?"
- I modified my frame2 to include more color and welcoming feel.

<img src="interaction/wellness2/frame2.png" alt="frame 1" width="250"/>

<img src="interaction/prototype/screen_welcome.jpeg" alt="frame 1" width="250"/>

2. Menu/Selection

- The user can select one of the activities shown on the menu
- The menu can be controlled by button to move up (buttonA) and down (buttonB), and is wrapped around.
- When both buttons are pressed, user can select an activity
- I tried to include my favorite "decompressing" activities that I think many people will enjoy.
- I included an "offline" activity to go offline for one minute, partially to demonstrate the reward screen with only 1min of countdown time.

<img src="interaction/prototype/screen_menu.jpeg" alt="frame 1" width="250"/>

3. Activity Screen

- The user can see the selected activity and starts
- To address feedback, I included images and added instruction on how the user can **pause/resume** or **exit**. Although, the screen is too small for me to fit detail descriptions. I can only fit the clock below the image.

<img src="interaction/wellness2/frame4.png" alt="frame 1" width="250"/>

<img src="interaction/prototype/screen_footbath.jpeg" alt="frame 1" width="250"/>

4. Countdown screen

- The user can start the countdown by pressing any button.
- The user can pause and resume the countdown clock by pressing button A.
- The user can exit the activity at anytime by pressing button B.

<img src="interaction/prototype/screen_countdown1.jpeg" alt="frame 1" width="250"/>
<img src="interaction/prototype/screen_countdown2.jpeg" alt="frame 1" width="250"/>

5. Reward message

- When the countdown stops and user completes the activity ***without*** exiting, the reward message will be shown.
- Similar to the welcome message, I want this screen to be a little reward that gives the user certain emotions, including:
  - achievement
  - progress/streak/gamification
  - prep for returning to work/daily routine
  - inspirational
- I went with more inspiration or mindfulness in terms of messaging.

<img src="interaction/prototype/screen_reward.jpeg" alt="frame 1" width="250"/>

#### Video

\*\*\***Take a video of your PiClock.**\*\*\*

- [main flow](https://youtube.com/shorts/KIw8MMRg3pY)
- [completion screen](https://youtube.com/shorts/qZgC3zvTh3w?feature=share)
