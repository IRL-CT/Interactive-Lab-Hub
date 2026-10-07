# Interactive Prototyping: The Clock of Pi

Ziqiao Gao

Does it feel like time is moving strangely during this semester?

For our first Pi project, we will pay homage to the [timekeeping devices of old](https://en.wikipedia.org/wiki/History_of_timekeeping_devices) by making simple clocks.

It is worth spending a little time thinking about how you mark time, and what would be useful in a clock of your own design.

**Please indicate anyone you collaborated with on this Lab here.**
Be generous in acknowledging their contributions! And also recognizing any other influences (e.g. from YouTube, Github, Twitter) that informed your design. 

## Prep

1. ### Set up your Lab 2 Github

At the start of lab Wednesday, ensure you have the latest lab content by updating your forked repository. 

**📖 [Follow the step-by-step guide for safely updating your fork](pull_updates/README.md)**

This guide covers how to pull updates without overwriting your completed work, handle merge conflicts, and recover if something goes wrong.


2. ### Get Kit and Inventory Parts
Take inventory of the kit parts that you have, and note anything that is missing:

***Update your [parts list inventory](partslist.md)***

3. ### Prepare your Pi for lab this week
[Follow these instructions](prep.md) to download and burn the image for your Raspberry Pi before lab Wednesday.




## Overview
For this assignment, you are going to 

A) [Connect to your Pi](#part-a)  

B) [Try out cli_clock.py](#part-b) 

C) [Set up your RGB display](#part-c)

D) [Try out clock_display_demo](#part-d) 

E) [Modify the code to make the display your own](#part-e)

F) [Make a short video of your modified barebones PiClock](#part-f)

G) [Sketch and brainstorm further interactions and features you would like for your clock for Part 2.](#part-g)

## The Report
This readme.md page in your own repository should be edited to include the work you have done. You can delete everything but the headers and the sections between the \*\*\***stars**\*\*\*. Write the answers to the questions under the starred sentences. Include any material that explains what you did in this lab hub folder, and link it in the readme.

Labs are due on Sunday midnight. Make sure this page is linked to on your main class hub page.

## Part A. 
### Connect to your Pi
Just like you did in the lab prep, ssh on to your pi. Once you get there, create a Python environment (named venv) by typing the following commands.

```
ssh pi@<your Pi's IP address>
...
pi@raspberrypi:~ $ python -m venv venv
pi@raspberrypi:~ $ source venv/bin/activate
(venv) pi@raspberrypi:~ $ 

```
### Setup Personal Access Tokens on GitHub
Set your git name and email so that commits appear under your name.
```
git config --global user.name "Your Name"
git config --global user.email "yourNetID@cornell.edu"
```

The support for password authentication of GitHub was removed on August 13, 2021. That is, in order to link and sync your own lab-hub repo with your Pi, you will have to set up a "Personal Access Tokens" to act as the password for your GitHub account on your Pi when using git command, such as `git clone` and `git push`.

Following the steps listed [here](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens) from GitHub to set up a token. Depends on your preference, you can set up and select the scopes, or permissions, you would like to grant the token. This token will act as your GitHub password later when you use the terminal on your Pi to sync files with your lab-hub repo.


## Part B. 
### Try out the Command Line Clock
Clone your own lab-hub repo for this assignment to your Pi and change the directory to Lab 2 folder (remember to replace the following command line with your own GitHub ID):

```
(venv) pi@raspberrypi:~$ git clone https://github.com/<YOURGITID>/Interactive-Lab-Hub.git
(venv) pi@raspberrypi:~$ cd Interactive-Lab-Hub/Lab\ 2/
```
Depends on the setting, you might be asked to provide your GitHub user name and password. Remember to use the "Personal Access Tokens" you just set up as the password instead of your account one!

Check if the directory has clone sucessfully, you should see the Interactive-Lab-Hub under the home directory listed:
```
(venv) pi@raspberrypi:~ $ ls
Bookshelf      Documents            Music     Public                 venv
create_img.sh  Downloads            pi-apps   screen_boot_script.py  Videos
Desktop        Interactive-Lab-Hub  Pictures  Templates
(venv) pi@raspberrypi:~ $
```


Install the packages from the requirements.txt and run the example script `cli_clock.py`:

```
(venv) pi@raspberrypi:~/Interactive-Lab-Hub/Lab 2 $ pip install -r requirements.txt
(venv) pi@raspberrypi:~/Interactive-Lab-Hub/Lab 2 $ python cli_clock.py 
02/24/2021 11:20:49
```

The terminal should show the time, you can press `ctrl-c` to exit the script.
If you are unfamiliar with the Python code in `cli_clock.py`, have a look at [this Python refresher](https://hackernoon.com/intermediate-python-refresher-tutorial-project-ideas-and-tips-i28s320p). If you are still concerned, please reach out to the teaching staff!


## Part C. 
### Set up your RGB Display
We have asked you to equip the [Adafruit MiniPiTFT](https://www.adafruit.com/product/4393) on your Pi in the Lab 2 prep already. Here, we will introduce you to the MiniPiTFT and Python scripts on the Pi with more details.

<img src="https://cdn-learn.adafruit.com/assets/assets/000/082/842/large1024/adafruit_products_4393_iso_ORIG_2019_10.jpg" height="200" />

The Raspberry Pi 5 has a variety of interfacing options. When you plug the pi in the red power LED turns on. Any time the SD card is accessed the green LED flashes. It has standard USB ports and HDMI ports. Less familiar it has a set of 20x2 pin headers that allow you to connect a various peripherals.

<img src="https://maker.pro/storage/g9KLAxU/g9KLAxUiJb9e4Zp1xcxrMhbCDyc3QWPdSunYAoew.png" height="400" />

To learn more about any individual pin and what it is for go to [pinout.xyz](https://pinout.xyz/pinout/3v3_power) and click on the pin. Some terms may be unfamiliar but we will go over the relevant ones as they come up.

### Hardware (you have already done this in the prep)

From your kit take out the display and the [Raspberry Pi 5](https://www.google.com/url?sa=i&url=https%3A%2F%2Fwww.raspberrypi.com%2Fproducts%2Fraspberry-pi-5%2F&psig=AOvVaw330s4wIQWfHou2Vk3-0jUN&ust=1757611779758000&source=images&cd=vfe&opi=89978449&ved=0CBMQjRxqFwoTCPi1-5_czo8DFQAAAAAdAAAAABAE)

Line up the screen and press it on the headers. The hole in the screen should match up with the hole on the raspberry pi.

<p float="left">
<img src="https://cdn-learn.adafruit.com/assets/assets/000/087/539/medium640/adafruit_products_4393_quarter_ORIG_2019_10.jpg?1579991932" height="200" />
<img src="https://cdn-learn.adafruit.com/assets/assets/000/082/861/original/adafruit_products_image.png" height="200">
</p>

### Testing your Screen

The display uses a communication protocol called [SPI](https://www.circuitbasics.com/basics-of-the-spi-communication-protocol/) to speak with the raspberry pi. We won't go in depth in this course over how SPI works. The port on the bottom of the display connects to the SDA and SCL pins used for the I2C communication protocol which we will cover later. GPIO (General Purpose Input/Output) pins 23 and 24 are connected to the two buttons on the left. GPIO 22 controls the display backlight.

To show you the IP and Mac address of the Pi to allow connecting remotely we created a service that launches a python script that runs on boot. For the following steps stop the service by typing ``` sudo systemctl stop piscreen.service --now```. Othwerise two scripts will try to use the screen at once. You may start it again by typing ``` sudo systemctl start piscreen.service --now```

We can test it by typing 
```
(venv) pi@raspberrypi:~/Interactive-Lab-Hub/Lab 2 $ python screen_test.py
```

You can type the name of a color then press either of the buttons on the MiniPiTFT to see what happens on the display! You can press `ctrl-c` to exit the script. Take a look at the code with
```
(venv) pi@raspberrypi:~/Interactive-Lab-Hub/Lab 2 $ cat screen_test.py
```

#### Displaying Info with Texts
You can look in `screen_boot_script.py` for how to display text on the screen!

#### Displaying an image

You can look in `image.py` for an example of how to display an image on the screen. Can you make it switch to another image when you push one of the buttons?

<img width="1279" height="2275" alt="image" src="https://github.com/user-attachments/assets/8d04df0d-6d1b-46e7-93fc-42b6bc127b11" />
<img width="2268" height="4032" alt="image" src="https://github.com/user-attachments/assets/49f5a5b8-b8cb-4457-bd3c-1e2d44210b51" />
<img width="2268" height="4032" alt="image" src="https://github.com/user-attachments/assets/954b8620-7b69-4dc6-bff3-334a04244f19" />



## Part D. 
### Set up the Display Clock Demo
Work on `screen_clock.py`, try to show the time by filling in the while loop (at the bottom of the script where we noted "TODO" for you). You can use the code in `cli_clock.py` and `stats.py` to figure this out.

### How to Edit Scripts on Pi
Option 1. One of the ways for you to edit scripts on Pi through terminal is using [`nano`](https://linuxize.com/post/how-to-use-nano-text-editor/) command. You can go into the `screen_clock.py` by typing the follow command line:
```
(venv) pi@raspberrypi:~/Interactive-Lab-Hub/Lab 2 $ nano screen_clock.py
```
You can make changes to the script this way, remember to save the changes by pressing `ctrl-o` and press enter again. You can press `ctrl-x` to exit the nano mode. There are more options listed down in the terminal you can use in nano.

Option 2. Another way for you to edit scripts is to use VNC on your laptop to remotely connect your Pi. Try to open the files directly like what you will do with your laptop and edit them. Since the default OS we have for you does not come up a python programmer, you will have to install one yourself otherwise you will have to edit the codes with text editor. [Thonny IDE](https://thonny.org/) is a good option for you to install, try run the following command lines in your Pi's ternimal:

  ```
  pi@raspberrypi:~ $ sudo apt install thonny
  pi@raspberrypi:~ $ sudo apt update && sudo apt upgrade -y
  ```

Now you should be able to edit python scripts with Thonny on your Pi.

Option 3. A nowadays often preferred method is to use Microsoft [VS code to remote connect to the Pi](https://www.raspberrypi.com/news/coding-on-raspberry-pi-remotely-with-visual-studio-code/). This gives you access to a fullly equipped and responsive code editor with terminal and file browser.  

Pro Tip: Using tools like [code-server](https://coder.com/docs/code-server/latest) you can even setup a VS Code coding environment hosted on your raspberry pi and code through a web browser on your tablet or smartphone! 

<img width="2268" height="4032" alt="image" src="https://github.com/user-attachments/assets/1380159f-f9eb-4255-b41f-4f0b8f066f24" />


## Part E. Read Part 2. Sketch and brainstorm further interactions and features you would like for your clock.

Instead of representing a fixed 24-hour day, one ice cube represents the user's personal waking day. The ice starts melting when the user wakes up and gradually melts toward their expected bedtime. When the user goes to sleep, the current day ends, and a new ice cube appears when they wake up the next day. This makes the clock represent how much of the user's own day has passed rather than simply showing the time of day.

1. Press Button B — Wake Up: A new personal day begins with a full ice cube.

2. During the Day: The ice continuously melts and the water around it increases as the day progresses.

3. Press Button A — Check Time: Press and hold Button A to temporarily show the numerical time. Release the button to return to the ice cube display.

4. Approaching Bedtime: Most of the ice has melted, visually showing that most of the user's waking day has passed.

5. Press Button B — Sleep: When the user is ready to sleep, pressing Button B enters sleep mode and stops the melting process.

6. Next Morning: Press Button B again to wake the clock and start a new personal day with a new full ice cube.

<img width="1000" height="366" alt="image" src="https://github.com/user-attachments/assets/bb6dcf88-f253-412c-8352-1f763ccd9f25" />

Button A – Check Exact Time: The clock normally does not display numerical time. The user can press and hold Button A to temporarily see the exact time. When the button is released, the display returns to the melting ice cube. This keeps the main experience focused on feeling the passage of time while still allowing the user to check the exact time when needed.

Button B – Sleep / Start a New Day: Button B controls the user's personal day. When the user is ready to sleep, pressing Button B ends the current day and stops the ice from melting. When the user wakes up, pressing Button B again starts a new personal day with a new full ice cube. This allows the clock to represent the user's waking day instead of a fixed 24-hour day.

**Put the names of the people you gave feedback to here. (Even better, add links to their repos here!)**

David Zhang Chen - I find the idea of the ice cube quite innovative! It gives a very intuitive sense of how much of the day has passed. I also like the idea of having different functions for each button on the Raspberry Pi, especially the sleep mode on Button B, since it feels similar to a real phone feature. One thing to think about is what happens if the user forgets to press Button B, since that could make the melting progress inaccurate. Maybe there could be a default bedtime or a visual reminder if the clock has been active for longer than usual. 
https://github.com/davidzhanggg/Interactive-Lab-Hub/tree/Fall2026/Lab%202

Sina Liu - I really like the idea of one ice cube representing your personal day—it feels much more personal than a normal 24-hour clock! I was just wondering how the melting speed would be decided. Would the user set an expected bedtime, and what happens if they stay up much later or go to sleep earlier than planned? Maybe the clock could adjust based on the user’s previous sleep schedule. Also, what happens if someone forgets to press Button B when they wake up or go to sleep? It might be helpful to have a way to correct the start or end time later. And maybe holding Button B instead of just pressing it could prevent someone from accidentally ending their day.
https://github.com/SinaL0123/Interactive-Lab-Hub/tree/Fall2026/Lab%202

Jindi Chen - I really like the visual idea of using melting ice to represent the passage of time. People can look at how much the ice has melted and get a sense of how much of their day has passed. I also really like the idea of using a personal waking day, because everyone has different daily routines, so it feels more personal than using a fixed 24-hour day.

One question I have is how the clock knows each person's expected bedtime. Would the user set it manually, or would there be some way for the clock to detect it? Also, what happens if the user goes to sleep earlier or later than expected? For example, if the ice has already completely melted but the user is still awake, how would the clock show that extra time? I'm also curious about what the screen would show after the user goes to sleep. And if the user wants to take a nap in the afternoon, would pressing the sleep button end the whole day?
https://github.com/JindiChai/Interactive-Lab-Hub/blob/Fall2026/Lab%202/README.md

# Lab 2 Part 2

## Prep 

1. Pick up remaining parts for kit on Wednesday lab class. Check the updated [parts list inventory](partslist.md) and let the TA know if there is any part missing.

2. Look at and give feedback on the Part E. for at least 3 other people in the class and get 3 people to comment on your Part E!)
**Put the feedback for your ideas here.**

I received feedback from three classmates:
  1. Sina: Liked the ice-melting concept, but pointed out that users might forget to press Button B. Suggested having a default schedule or reminder.
  2. David: Asked how the clock would handle different bedtimes, sleeping earlier or later than expected, and accidentally pressing Button B. Suggested making the button interaction more intentional.
  3. Jindi: Asked what would happen if the user forgot to start the clock, took a nap, or stayed awake after the ice completely melted.

Based on this feedback, I changed Button B to a 2-second hold to prevent accidental presses and added a default 8 AM–12 AM schedule. If the user forgets to start the clock in the morning, the ice now automatically catches up to the current time instead of starting as a full ice cube.

## Update your Lab Hub

[Update your Lab Hub](pull_updates/README.md) to get the latest content and requirements for Part 2.

## Modify the barebones clock to make it your own

Start small, pick just one element of your overall idea, just to show you have a handle on the code and components.

\*\*\***Put a copy of your code in your Lab 2 Github repo.**\*\*\*

## Make a short video of your modified barebones PiClock

\*\*\***Take a video of your barely modified PiClock.**\*\*\*

This is a testing barely modified ice clock: I just upload all image on the pi and tested the core visualization. The video shows  the ice cube progress from fully frozen to fully melted.

https://youtube.com/shorts/7202EMKcjmo?feature=share


After you edit and work on the scripts for Lab 2, the files should be upload back to your own GitHub repo! You can push to your personal github repo by adding the files here, commiting and pushing.

```
(venv) pi@raspberrypi:~/Interactive-Lab-Hub/Lab 2 $ git add .
(venv) pi@raspberrypi:~/Interactive-Lab-Hub/Lab 2 $ git commit -m 'your commit message here'
(venv) pi@raspberrypi:~/Interactive-Lab-Hub/Lab 2 $ git push
```

After that, Git will ask you to login to your GitHub account to push the updates online, you will be asked to provide your GitHub user name and password. Remember to use the "Personal Access Tokens" you set up in Part A as the password instead of your account one! Go on your GitHub repo with your laptop, you should be able to see the updated files from your Pi!

## Now, make your own PiClock

Do take advantage of having done the previous iteration to refine and simplify your design.

** Insert any updates ideas, sketches, [Verplank diagrams](https://ccrma.stanford.edu/courses/250a-fall-2004/IDSketchbok.pdf))!, storyboards for your ideas **

Design Iteration:
Based on the feedback I received, I made several changes to the Ice Cube Clock. One concern was accidentally pressing Button B, so I changed it from a single press to a 2-second hold to start or end the day. Another important concern was what would happen if the user forgot to start the clock after waking up. In my original idea, pressing Button B would always start with a full ice cube. In the final version, the clock uses an expected day from 8 AM to midnight instead. This allows the ice to reflect the actual time of day even if the user starts the clock late. For example, if the user forgets to press Button B in the morning and remembers later in the day, the clock will start with a partially melted ice cube instead of a full one.


Here is the updated verplank diagram:
<img width="3508" height="2480" alt="未命名作品 9" src="https://github.com/user-attachments/assets/267d7864-6668-400f-92a1-c6f353dbd7f3" />

Here is the updated storyboard:
<img width="1556" height="970" alt="image" src="https://github.com/user-attachments/assets/c11897ee-4a5a-4d51-94de-9556d03ee8a7" />

\*\*\***Put a copy of your code in your Lab 2 Github repo.**\*\*\*

The final implementation can be found called Lab 2/ice_clock.py , and the six images are named ice_0.png , ice_10.png, ice_25.png, ice_50.png , ice_75.png , ice_100.png . 
The final Ice Cube Clock represents the progress of the day through six stages of melting ice: 100%, 75%, 50%, 25%, 10%, and 0% remaining. From 8 AM to midnight, the ice gradually moves through these stages until it becomes a puddle. Holding Button A temporarily shows the exact numerical time, while releasing it returns to the ice visualization. Holding Button B for two seconds starts or ends the day.


\*\*\***Take a video of your PiClock.**\*\*\*

https://youtube.com/shorts/m28dsskoR7c?feature=share

The video demonstrates two situations. In the first part, the user starts the clock in the morning and the ice begins as a full ice cube, then melts as the day progresses. In the second part, the user forgets to start the clock in the morning and presses Button B later in the day. Instead of restarting with a full ice cube, the clock immediately displays a partially melted stage based on the current time.


As always, make sure you document contributions and ideas from others (and AI) explicitly in your writeup.

The final design was iterated based on feedback from Sina, David, and Jindi, especially around accidental button presses, forgetting to start the clock, and how the clock should behave around bedtime. I used ChatGPT to help brainstorm solutions to these edge cases, troubleshoot and debug the Raspberry Pi code, and create the updated storyboard. I made the final design decisions and implemented and tested the prototype on the Raspberry Pi.

You are permitted (but not required) to work in groups and share a turn in; you are expected to make equal contribution on any group work you do, and N people's group project should look like N times the work of a single person's lab.  Make sure the page for the group turn in is linked to your personal Interactive Lab Hub page. 


