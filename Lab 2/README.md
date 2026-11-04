# Interactive Prototyping: The Clock of Pi
**NAMES OF COLLABORATORS HERE**

Yangchen Jin yj645

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

\*\*\***Include a picture of your own Raspberry Pi displaying the piscreen.service with your unique MAC address. Additionally, please provide another picture showing the successful completion of the screen test.**\*\*\*

<img width="480" height="640" alt="73eaf842d0733d6ee88e9602ccb74820" src="https://github.com/user-attachments/assets/9762b01c-72b9-4136-95b9-4e98f32beff2" />
<img width="480" height="640" alt="d0d85bb57d07285271ae0f0c744d5fb6" src="https://github.com/user-attachments/assets/7cbc80fe-ffc1-4442-9463-0dd02e1861d7" />
<img width="320" height="426.75" alt="288006e01200f1555a0aa3f747d92913" src="https://github.com/user-attachments/assets/6335e1eb-8776-46eb-bf24-0afd9720c9ef" />

*The Pi displaying its IP address and unique MAC address.*

*Successful screen and button tests.*



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

## Part E. Read Part 2. Sketch and brainstorm further interactions and features you would like for your clock.

One potential source of ideas might be thinking about other clocks and timekeeping devices for inspiration.

Another might be novel units of time. How do you measure a year? [In daylights? In midnights? In cups of coffee?](https://www.youtube.com/watch?v=wsj15wPpjLY)

We strongly discourage literal digital or analog clock display: Be creative.


** Insert ideas, sketches, [Verplank diagrams](https://ccrma.stanford.edu/courses/250a-fall-2004/IDSketchbok.pdf)), storyboards for your ideas **

<img width="500" height="500" alt="2ee049cd4f079473daf0af819ff3d5f0" src="https://github.com/user-attachments/assets/d551673e-116d-4c5d-beeb-c8dabb70de5b" />



**Each large block represents six hours and contains 24 mini-blocks. Each mini-block represents 15 minutes. As time passes, completed mini-blocks gradually fill with the color associated with that period of the day.**

**My clock prioritizes awareness of time over precise timekeeping. The block display divides the day into four meaningful phases and makes the passage of time visually tangible. Users can understand their position within the day at a glance, while pressing a button reveals the exact remaining time when precision is needed.**

**Pressing a button switches between time elapsed and time remaining. The abstract block display provides ambient awareness of time. 
Pressing a button temporarily reveals the exact time remaining, creating a stronger sense of urgency without turning the default display into a conventional digital clock.**

**Put the names of the people you gave feedback to here. (Even better, add links to their repos here!)**


**Shenye Wang** https://github.com/bh654-dev/Interactive-Lab-Hub/blob/Fall2026/Lab%202/README.md

**Tony Wang** https://github.com/TonyW755/Interactive-Lab-Hub/blob/Fall2026/Lab%202/README.md

**Yanshen** https://github.com/ys2473/Interactive-Lab-Hub/tree/Fall2026/Lab%202

**Zhimeng Zhang** https://github.com/Flora130/Interactive-Lab-Hub/tree/Fall2026/Lab%202

**Simin Xu** https://github.com/Simonehina/Interactive-Lab-Hub/blob/Fall2026/Lab%202/README.md

# Lab 2 Part 2

## Prep 

1. Pick up remaining parts for kit on Wednesday lab class. Check the updated [parts list inventory](partslist.md) and let the TA know if there is any part missing.

2. Look at and give feedback on the Part E. for at least 3 other people in the class and get 3 people to comment on your Part E!)
**Put the feedback for your ideas here.**

**Recorded Feedback**

**Yanshen**: She felt that my original block-based concept was somewhat plain and did not create a particularly engaging or memorable experience.

**Zhimeng Zhang**: She pointed out that the button interaction was too limited because it only revealed the remaining time. As a result, the project still functioned mainly as a conventional clock rather than offering a meaningful interaction.

**Simin Xu**: She suggested that the abstract block display might require too much interpretation. A more recognizable visual transformation could make the passage of time easier to understand at a glance.

**Feedback Summary**

My initial idea for the clock was very simple and straightforward. The main feedback I received was that it was still just a visual clock, and the function triggered by pressing the button was very dull and limited—it simply displayed the time remaining in the day. Further feedback indicated that the design and interaction were too boring and that relying solely on an image composed of multiple squares might require a great deal of time and effort to determine the current time. Therefore, I plan to iterate and modify the design to make it more creative and easier to understand. Also, I'd like to see more natural elements related to consumption or growth.

## Update your Lab Hub

[Update your Lab Hub](pull_updates/README.md) to get the latest content and requirements for Part 2.

## Modify the barebones clock to make it your own

Start small, pick just one element of your overall idea, just to show you have a handle on the code and components.

\*\*\***Put a copy of your code in your Lab 2 Github repo.**\*\*\*

[Prototype code](plant_clock.py)  

## Make a short video of your modified barebones PiClock

\*\*\***Take a video of your barely modified PiClock.**\*\*\*

[Prototype video](https://youtube.com/shorts/nwxGnN7v8eA)

## Now, make your own PiClock

** Insert any updates ideas, sketches, [Verplank diagrams](https://ccrma.stanford.edu/courses/250a-fall-2004/IDSketchbok.pdf))!, storyboards for your ideas **

<img width="428" height="428" alt="8b93e9bfe081351fbbf2a03c2a765891" src="https://github.com/user-attachments/assets/9b5cfcec-984b-453a-872a-9b466b8f98a1" />

<img width="428" height="428" alt="574b9f2a8688d56c16b5523b4c15bfc8" src="https://github.com/user-attachments/assets/c87f8311-9e8d-4b2d-91fb-5f138b7f0d8f" />



After receiving feedback from several peers and discussing the matter with them, I drew inspiration from designs such as a gradually burning incense stick, a continuously melting ice cube, and a slowly ripening banana. These objects all express the passage of time through their own transformations. At first, I considered designing an ever-evolving organism, perhaps drawing on the process of human evolution; I also thought about using the human lifespan, from birth to old age, to symbolize time. However, I felt that the overall atmosphere of these concepts was somewhat heavy and pessimistic.

Ultimately, I chose to use flowers as a symbol of time and redesigned the clock around five visual stages: a seed buried in the soil, a sprout breaking through the earth, a growing plant, a blooming flower, and finally, the flower being picked. For me, picking a flower isn’t merely the end of a day; it also evokes the continuation of the seed and the beginning of the next cycle of life. Therefore, this cycle not only represents the passage of time but also embodies the dual meanings of “ending” and “new life.” Compared to my earlier concepts, this design is easier to understand and conveys a more positive sentiment.

\*\*\***Put a copy of your code in your Lab 2 Github repo.**\*\*\*

[Final PiClock code](refined_plant_clock.py)  

\*\*\***Take a video of your PiClock.**\*\*\*

[Final PiClock video](https://youtu.be/MgH_5LoQb20)

The demo video is sped up, showing the flower's changes over the course of a day in 60 seconds. Pressing the top button lets you water the flower, causing its appearance to change. Pressing the bottom button shows or hides the time.


I developed the core concept, interaction design, and visual direction of the project. Feedback from my classmates helped me move from the original abstract block display toward a more natural and understandable growth cycle. ChatGPT assisted with generating, organizing, and debugging portions of the Python code, as well as refining the flower-picking animation. I reviewed, adapted, and tested the final implementation on the Raspberry Pi.
