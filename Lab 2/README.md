# Interactive Prototyping: The Clock of Pi
**NAMES OF COLLABORATORS HERE**

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

I was able to properly set up my raspberry pi, and received the following MAC address
<img width="543" height="513" alt="Screenshot 2026-09-13 at 5 19 23 PM" src="https://github.com/user-attachments/assets/1fe30c92-ce97-4029-9f20-8ec8c2538c65" />

After setting everything up, I successfully implemented the screen test in my terminal, changing the color to pink when I pressed the button. 

<img width="624" height="62" alt="Screenshot 2026-09-13 at 4 26 11 PM" src="https://github.com/user-attachments/assets/fa2bf895-239c-4159-ad68-c963959f324a" />

<img width="545" height="572" alt="Screenshot 2026-09-13 at 5 18 58 PM" src="https://github.com/user-attachments/assets/149fdf58-482e-4d41-b284-39560cfabf76" />


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

**MY WORK**

After referencing the files described above, I was able to show the current time and date onto the raspberry pi, as shown below. 

<img width="531" height="331" alt="Screenshot 2026-09-13 at 5 21 57 PM" src="https://github.com/user-attachments/assets/0fbe54a9-9c79-4944-804f-22464a149b76" />

<img width="524" height="323" alt="Screenshot 2026-09-13 at 5 21 44 PM" src="https://github.com/user-attachments/assets/ed43bbf1-5e3c-40b7-9da9-386db8869ad2" />

<img width="568" height="201" alt="Screenshot 2026-09-13 at 5 21 49 PM" src="https://github.com/user-attachments/assets/5ab81e61-fe6a-4a1d-9ca8-fdb13d588843"/> 

## Part E. Read Part 2. Sketch and brainstorm further interactions and features you would like for your clock.

One potential source of ideas might be thinking about other clocks and timekeeping devices for inspiration.

Another might be novel units of time. How do you measure a year? [In daylights? In midnights? In cups of coffee?](https://www.youtube.com/watch?v=wsj15wPpjLY)

We strongly discourage literal digital or analog clock display: Be creative.

** Insert ideas, sketches, [Verplank diagrams](https://ccrma.stanford.edu/courses/250a-fall-2004/IDSketchbok.pdf)), storyboards for your ideas **

**MY BRAINSTORMING**

I generally have a very consistent eating/hunger schedule so I thought it'd be fun to use that as a point-of-reference for time telling. I brainstormed the interaction, as shown in the pictures below. Essentially, if I want to see what time it is, I rate my hunger on thee device with the 12-key touch sensor. Based on how hungry I am, the device is able to estimate when my next meal is, which is an indirect way of letting me know the time is since I regularly eat at the same times each day. 

<img width="529" height="292" alt="Screenshot 2026-09-13 at 5 23 15 PM" src="https://github.com/user-attachments/assets/467175bf-aadb-4bd5-aac8-0b0005752ac4" />

The rough sketch below illustrate an instance where I'd use this device, most likely when I can't access my phone or have forgotten my watch. 

<img width="538" height="656" alt="Screenshot 2026-09-13 at 5 23 30 PM" src="https://github.com/user-attachments/assets/adf29569-ad87-4d90-af6a-40c89661101e" />

**Put the names of the people you gave feedback to here. (Even better, add links to their repos here!)**

Jenny Li - https://github.com/jianingli189/Interactive-Lab-Hub/blob/Fall2026/Lab%202/README.md

Shifeng Hong - https://github.com/mado0512/Interactive-Lab-Hub/edit/Fall2026/Lab%202/README.md

Pallavi Khana - https://github.com/pk633-cu/Interactive-Lab-Hub/blob/Fall2026/Lab%202/README.md


# Lab 2 Part 2

## Prep 

1. Pick up remaining parts for kit on Wednesday lab class. Check the updated [parts list inventory](partslist.md) and let the TA know if there is any part missing.

2. Look at and give feedback on the Part E. for at least 3 other people in the class and get 3 people to comment on your Part E!)
**Put the feedback for your ideas here.**

Jenny Li - https://github.com/jianingli189/Interactive-Lab-Hub/blob/Fall2026/Lab%202/README.md

 "I love this way of measuring time by hunger! I think it's a philosophy of measuring your time by yourself, instead of by some rules or laws set up by nature or society. An interesting way to consider is that, maybe there are more interesting way to choose the level of your hunger than numbers, like, how much rice you wanna put in your bowl? How many chicken legs you wanna pick up? I think this kind of interaction will make your clock even more interesting and interactive."

Shifeng Hong - https://github.com/mado0512/Interactive-Lab-Hub/edit/Fall2026/Lab%202/README.md

"Love the connection with personal background, this could be a great project to explore how can one convery the subjective feeling of hungriness to a third person who might not have this subjective feeling of fullness vs hungriness. For example, make the reading go blur, or go wacky when it is close to eating time (to convey that you are REALLY HUNGRY)"

Pallavi Khana - https://github.com/pk633-cu/Interactive-Lab-Hub/blob/Fall2026/Lab%202/README.md

"I actually don't get hungry much and have to remind myself to eat. So I think it's a really nice idea to have a customizable clock and set "alarms" specifically for your own work day. Being able to get more bio signals would be nice so you could get more optimal eating times. But I think it'd be good for people who forget to eat."

## Update your Lab Hub

[Update your Lab Hub](pull_updates/README.md) to get the latest content and requirements for Part 2.

## Modify the barebones clock to make it your own

Start small, pick just one element of your overall idea, just to show you have a handle on the code and components.

\*\*\***Put a copy of your code in your Lab 2 Github repo.**\*\*\*

Link here as well: https://github.com/chonjessica23/Interactive-Lab-Hub/blob/Fall2026/Lab%202/barebones_mod.py 

## Make a short video of your modified barebones PiClock

Below is a video of the modified PiClock. Given my new project direction, I just wanted to play around with timing and image/text displays. So, I made it so that once it reached a specific time, after 30 seconds, a line of text appeared. After 30 more seconds passed, the text was able to disappear. 

\*\*\***Take a video of your barely modified PiClock.**\*\*\*

https://github.com/user-attachments/assets/3d80eff1-ce7b-42d0-a73b-7518e28a46f2

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

Based on the feedback, I definitely revised my initial idea a bit. Pallavi's comment about using this type of clock as a reminder for individuals who forget to eat, so I decided to get rid of the rating my hunger input since other user's wouldn't be able to utilize that form of interaction. From Jenny's feedback, I decided it would be much simpler and more intuitive for users to understand the flow of time via food with images. I really liked her input of going on how many chicken legs, or grains of rice there are to quantify time. I didn't want that representation of time to be so direct though. I wanted to maintain the personal aspect that Shifeng appreciated, so I decided to instead "build a meal". That way it's implicitly still a clock meant for me since the finished meal is still set to when I eat. Overall, I'd summarize that the project shifted to a much more adaptable way to keep time for others, rather than solely be tailored to me. Below is a sketch of my new plan:

<img width="460" height="718" alt="Screenshot 2026-09-20 at 10 31 46 PM" src="https://github.com/user-attachments/assets/2491e532-355a-437a-b7a3-7dbe04c16811" />

\*\*\***Put a copy of your code in your Lab 2 Github repo.**\*\*\*

Link to code here as well: https://github.com/chonjessica23/Interactive-Lab-Hub/blob/Fall2026/Lab%202/foodclock.py 

\*\*\***Take a video of your PiClock.**\*\*\*

https://github.com/user-attachments/assets/283b5c89-03b9-4fd6-8be7-e9cb258e3c30

The clock goes by real time, but for the sake of the demo, you can see how different phases of the food clock with a button clock. 

As always, make sure you document contributions and ideas from others (and AI) explicitly in your writeup.

You are permitted (but not required) to work in groups and share a turn in; you are expected to make equal contribution on any group work you do, and N people's group project should look like N times the work of a single person's lab.  Make sure the page for the group turn in is linked to your personal Interactive Lab Hub page. 


