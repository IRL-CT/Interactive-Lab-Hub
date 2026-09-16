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

### Concept: Spider-Verse Clock

Instead of showing literal time, a chibi Spider-Man mascot swaps suits every hour (24 suits total, one per hour). Each suit has a signature food, and the number of food items shown scales with the hour.

| Hour | Suit | Food (qty = hour) |
|---|---|---|
| 8am | Spider-Man India (Pavitr) | 8 cups of chai |
| 12pm | Spider-Ham (Peter Porker) | 12 mini pies |
| 3pm | Miles Morales | 3 pizza slices |
| 6pm | Peter Parker (classic) | 6 of Aunt May's pies |
| 12am | Spider-Gwen | 12 donuts |
| 2am | Spider-Man Noir | 2 cups of coffee |

**Interaction loop:** clock ticks → pick suit for current hour → render mascot + food count → repeat every hour.

**Extension ideas:**
- Button press = "spider-sense" easter egg, flashes a random alt suit
- Midnight = full-screen suit montage
- 
<img width="2244" height="2904" alt="Piclock Spiderman-1" src="https://github.com/user-attachments/assets/7ad4ed6a-b4cb-4be0-a0f9-5f99353d6418" />


### Feedback we gave to other groups

**[Pallavi Khanna](https://github.com/pk633-cu/Interactive-Lab-Hub/blob/Fall2026/Lab%202/README.md):**
Overall, I like the first idea, it seems like it is easy to tell time because the sunset is very recognizable. I like the idea that the sun's height will represent time. I am curious about the minutes thought will the sun only change per hour or will it slowly rise per minute. I think that is something that is probably an important distinction to make. The second idea is a little confusing. I don't understand fully what the buildings are representing? Like do they have any indication on the time or is it just the weather/sun? I like the last idea too where there is a step's associated with the clock. It tells you what time you need to have the steps done by. However it doesn't seem like a clock more like a goal that is needed to be achieved in that time-frame.

**[Ammarsyed](https://github.com/ammarsyed/Interactive-Lab-Hub/blob/Fall2026/Lab%202/README.md):**
I like the idea of using an hourglass as a way to represent time. It’s something that everyone is familiar with so it’s very intuitive and gives a clear visual sense of time passing. Though I would say I always personally found hourglasses to be a little ambiguous in regard to how much time is left for it to finish ticking. I’d be interested in seeing how you could make the concept feel a little more unique or personal beyond a traditional hourglass.

**[Jovian Wang](https://github.com/jovianw/Interactive-Lab-Hub):**
I love the design! The spider man theme is a very fun take and shows a lot of creativity. While I like the idea of the number of foods showing the time, I am a little concerned about the readability of the clock! If they were somewhat randomly placed liked the current storyboard, I fear the user might have a difficult time interpreting the hour number. I think a good compromise could be the foods moving around in a predictable circle around the spiderman -- it's much more easier to tell when there are two, four, or eight objects around in a circle rather than randomly placed. You could probably find another compromise as well. Good job!

**[Rohil Saraf](https://github.com/rohilsaraf97/Interactive-Lab-Hub/blob/Fall2026/Lab%202/README.md#part-e-read-part-2-sketch-and-brainstorm-further-interactions-and-features-you-would-like-for-your-clock):**
Snacks are the best! Your snack clock is very fun and very thought out and I can see the tie in between an animated characters body language to denote how much time has passed since the user last ate a snack. I think some fun metrics to add to the clock would be how many snacks you did eat throughout the day and perhaps changing how the character (physically, fatter, skinner, based on the amount of snacks it had during the week). Overall very good design, and you can go very far with it. The only feedback I have is perhaps adding interaction based on the amount of snacks eaten would also be interesting to implement


# Lab 2 Part 2

## Prep 

### Feedback from other groups

**From [Pallavi Khanna](https://github.com/pk633-cu/Interactive-Lab-Hub/blob/Fall2026/Lab%202/README.md):**
Overall, I like the idea. It’s creative, fun, and doable! Something I would consider is that the Raspberry Pi’s screen is small, so fitting up to 12 food items or pies might get crowded. Instead, you could do something like a cake with up to 12 candles. It might also be helpful to use 12 suits instead of 24 since you plan to use a 12-hour clock. This could help users associate each suit with a specific hour more easily. For instance, at both 2 PM and 2 AM, Spider-Man would wear the same suit. This could also help users tell the time at a glance, especially when the screen is populated with multiple items. I think simplifying these elements could make the concept easier to read while still keeping the fun and playful parts of your original idea.

**From [Ammarsyed](https://github.com/ammarsyed/Interactive-Lab-Hub/blob/Fall2026/Lab%202/README.md):**
The Spider Verse clock is a super creative way to represent time, far different than a traditional digital or analog display. I really like how each hour has a different Spider Man suit and a correlated food related to that suit. The quantity of that food is what correlates to the actual time. It is very playful and visually unique.

My only concern is that displaying that many items at a high numbered time like 12:00, which means 12 food items, might make this small screen very crowded. Maybe you can adjust that by using one food icon and then a number, either inside or to the side of that food item, to show the relevant time.

**From [Jovian Wang](https://github.com/jovianw/Interactive-Lab-Hub):**
Hello Jovian, your design is very straightforward and uses the natural time of a plant growing and the movement of the sun to denote time passing! Something missing from the sketch is what happens to the plant when night time occurs? From the storyboard it just looks like the plant disappears and there is no moon or anything to indicate that it's night time. Perhaps adding the moon and stars would be a important feature to add to help show the user what time it is at night. Perhaps the number of petals says how many minutes have passed. There is a lot of things you can do. Overall very good design!

**From [Rohil Saraf](https://github.com/rohilsaraf97/Interactive-Lab-Hub/blob/Fall2026/Lab%202/README.md#part-e-read-part-2-sketch-and-brainstorm-further-interactions-and-features-you-would-like-for-your-clock):**
Great design! Simple and does the job, just wondering if using 8 cups of chai or 2 cups of coffee counts as numerical representation? Also, if it doesn't, then something like using the chai and coffee cups etc. could be useful to represent another dimension, like minutes, and maybe the Spiderman variant, the background, and the animation could represent the hour? I was just thinking that since you have 24 Spiderman variations, representing the hours with a different prop might be redundant. Is finding Spidermen that look considerably different on such a small screen easy? maybe even a spiderman going to bed could mean its night time, time to go to bed, like does it have to convey actual time? It could revolve around your activities for the day maybe? Also, super cute diagrams!!

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


