# Interactive Prototyping: The Clock of Pi
**COLLABORATORS: Neeha Ravula (nr485), Gaurav Patel (gp438), Nishant Ray (nr487), Victor Radev (vr373)**

**TODO: Cite any influences/inspiration used**

## Part A. 
### Connect to your Pi
Successfully SSHed into my pi and activated the virtual environment as follows:
```
ssh pi@<your Pi's IP address>
...
pi@raspberrypi:~ $ python -m venv venv
pi@raspberrypi:~ $ source venv/bin/activate
(venv) pi@raspberrypi:~ $ 

```
### Setup Personal Access Tokens on GitHub
Successfully set up GitHub credentials and token on the pi!


## Part B. 
### Try out the Command Line Clock
Successfully cloned the Lab 2 repo and was able to view the CLI clock:

<img width="697" height="42" alt="Screenshot 2026-09-13 at 10 24 02 PM" src="https://github.com/user-attachments/assets/26de8b57-b076-46f8-94d7-1c92dc9d0ccc" />


## Part C. 
### Set up your RGB Display

Successfully displayed the piscreen.service:

<img width="3150" height="2363" alt="IMG_7255" src="https://github.com/user-attachments/assets/bc82216d-3595-4fdf-a23d-9f20c3646065" />

As well as the screen test (chose blue as my custom color):

<img width="3809" height="2857" alt="IMG_7256" src="https://github.com/user-attachments/assets/25fc0aa9-ddd2-4bee-b042-ea0c92bada92" />


## Part D. 
### Set up the Display Clock Demo

Updated screen_clock.py to display the time!

<img width="4032" height="3024" alt="IMG_7257" src="https://github.com/user-attachments/assets/fafa5175-d8d2-49f2-a36a-e091a1fa483c" />


## Part E. Read Part 2. Sketch and brainstorm further interactions and features you would like for your clock.

Below are some ideas for further improvements to the clock interface. I experimented with different font types/number formats to mimic a "retro" style alarm clock, as well as using moon/sun phases. I also think it would be cool to change the background color of the interface based on the time of day (black for night, soft orange for sunrise, light blue for daytime, pinkish orange for sunset, dusk blue for evening).

<img width="3417" height="1589" alt="part e" src="https://github.com/user-attachments/assets/1ed79a3b-d2f8-41b8-8074-af809cd4f256" />


**TODO: Put the names of the people you gave feedback to here. (Even better, add links to their repos here!)**

# Lab 2 Part 2

## Prep 

1. Pick up remaining parts for kit on Wednesday lab class. Check the updated [parts list inventory](partslist.md) and let the TA know if there is any part missing.

2. Look at and give feedback on the Part E. for at least 3 other people in the class and get 3 people to comment on your Part E!)
**Put the feedback for your ideas here.**

## Update your Lab Hub

[Update your Lab Hub](pull_updates/README.md) to get the latest content and requirements for Part 2.

## Modify the barebones clock to make it your own

Start small, pick just one element of your overall idea, just to show you have a handle on the code and components.

\*\*\***Put a copy of your code in your Lab 2 Github repo.**\*\*\*

## Make a short video of your modified barebones PiClock

\*\*\***Take a video of your barely modified PiClock.**\*\*\*

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


\*\*\***Put a copy of your code in your Lab 2 Github repo.**\*\*\*

\*\*\***Take a video of your PiClock.**\*\*\*


As always, make sure you document contributions and ideas from others (and AI) explicitly in your writeup.

You are permitted (but not required) to work in groups and share a turn in; you are expected to make equal contribution on any group work you do, and N people's group project should look like N times the work of a single person's lab.  Make sure the page for the group turn in is linked to your personal Interactive Lab Hub page. 


