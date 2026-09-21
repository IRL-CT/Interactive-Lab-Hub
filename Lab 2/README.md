# Interactive Prototyping: The Clock of Pi
**COLLABORATORS: Neeha Ravula (nr485), Gaurav Patel (gp438), Nishant Ray (nr487), Victor Radev (vr373)**

**Influences/inspiration:** Spider-Verse franchise

**AI Usage:** Used ChatGPT to generate clock face images

## Part A. 
### Connect to your Pi
Successfully SSHed into my pi and activated the virtual environment.

### Setup Personal Access Tokens on GitHub
Successfully set up GitHub credentials and token on the Pi!


## Part B. 
### Try out the Command Line Clock
Successfully cloned the Lab 2 repo and was able to view the CLI clock on my Pi:

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

<img width="2244" height="2904" alt="Piclock Spiderman-1" src="https://github.com/user-attachments/assets/7ad4ed6a-b4cb-4be0-a0f9-5f99353d6418" />


### Feedback we gave to other groups

**[Pallavi Khanna (pk633)](https://github.com/pk633-cu/Interactive-Lab-Hub/blob/Fall2026/Lab%202/README.md):**
Overall, I like the first idea, it seems like it is easy to tell time because the sunset is very recognizable. I like the idea that the sun's height will represent time. I am curious about the minutes thought will the sun only change per hour or will it slowly rise per minute. I think that is something that is probably an important distinction to make. The second idea is a little confusing. I don't understand fully what the buildings are representing? Like do they have any indication on the time or is it just the weather/sun? I like the last idea too where there is a step's associated with the clock. It tells you what time you need to have the steps done by. However it doesn't seem like a clock more like a goal that is needed to be achieved in that time-frame.

**[Ammar Syed (as4422)](https://github.com/ammarsyed/Interactive-Lab-Hub/blob/Fall2026/Lab%202/README.md):**
I like the idea of using an hourglass as a way to represent time. It’s something that everyone is familiar with so it’s very intuitive and gives a clear visual sense of time passing. Though I would say I always personally found hourglasses to be a little ambiguous in regard to how much time is left for it to finish ticking. I’d be interested in seeing how you could make the concept feel a little more unique or personal beyond a traditional hourglass.

**[Jovian Wang (jlw457)](https://github.com/jovianw/Interactive-Lab-Hub):**
Hello Jovian, your design is very straightforward and uses the natural time of a plant growing and the movement of the sun to denote time passing! Something missing from the sketch is what happens to the plant when night time occurs? From the storyboard it just looks like the plant disappears and there is no moon or anything to indicate that it's night time. Perhaps adding the moon and stars would be a important feature to add to help show the user what time it is at night. Perhaps the number of petals says how many minutes have passed. There is a lot of things you can do. Overall very good design!

**[Rohil Saraf (rs2685)](https://github.com/rohilsaraf97/Interactive-Lab-Hub/blob/Fall2026/Lab%202/README.md#part-e-read-part-2-sketch-and-brainstorm-further-interactions-and-features-you-would-like-for-your-clock):**
Snacks are the best! Your snack clock is very fun and very thought out and I can see the tie in between an animated characters body language to denote how much time has passed since the user last ate a snack. I think some fun metrics to add to the clock would be how many snacks you did eat throughout the day and perhaps changing how the character (physically, fatter, skinner, based on the amount of snacks it had during the week). Overall very good design, and you can go very far with it. The only feedback I have is perhaps adding interaction based on the amount of snacks eaten would also be interesting to implement


# Lab 2 Part 2

## Prep 

### Feedback we received

**From [Pallavi Khanna (pk633)](https://github.com/pk633-cu/Interactive-Lab-Hub/blob/Fall2026/Lab%202/README.md):**
Overall, I like the idea. It’s creative, fun, and doable! Something I would consider is that the Raspberry Pi’s screen is small, so fitting up to 12 food items or pies might get crowded. Instead, you could do something like a cake with up to 12 candles. It might also be helpful to use 12 suits instead of 24 since you plan to use a 12-hour clock. This could help users associate each suit with a specific hour more easily. For instance, at both 2 PM and 2 AM, Spider-Man would wear the same suit. This could also help users tell the time at a glance, especially when the screen is populated with multiple items. I think simplifying these elements could make the concept easier to read while still keeping the fun and playful parts of your original idea.

**From [Ammar Syed (as4422)](https://github.com/ammarsyed/Interactive-Lab-Hub/blob/Fall2026/Lab%202/README.md):**
The Spider Verse clock is a super creative way to represent time, far different than a traditional digital or analog display. I really like how each hour has a different Spider Man suit and a correlated food related to that suit. The quantity of that food is what correlates to the actual time. It is very playful and visually unique.

My only concern is that displaying that many items at a high numbered time like 12:00, which means 12 food items, might make this small screen very crowded. Maybe you can adjust that by using one food icon and then a number, either inside or to the side of that food item, to show the relevant time.

**From [Jovian Wang (jlw457)](https://github.com/jovianw/Interactive-Lab-Hub):**
I love the design! The spider man theme is a very fun take and shows a lot of creativity. While I like the idea of the number of foods showing the time, I am a little concerned about the readability of the clock! If they were somewhat randomly placed liked the current storyboard, I fear the user might have a difficult time interpreting the hour number. I think a good compromise could be the foods moving around in a predictable circle around the spiderman -- it's much more easier to tell when there are two, four, or eight objects around in a circle rather than randomly placed. You could probably find another compromise as well. Good job!

**From [Rohil Saraf (rs2685)](https://github.com/rohilsaraf97/Interactive-Lab-Hub/blob/Fall2026/Lab%202/README.md#part-e-read-part-2-sketch-and-brainstorm-further-interactions-and-features-you-would-like-for-your-clock):**
Great design! Simple and does the job, just wondering if using 8 cups of chai or 2 cups of coffee counts as numerical representation? Also, if it doesn't, then something like using the chai and coffee cups etc. could be useful to represent another dimension, like minutes, and maybe the Spiderman variant, the background, and the animation could represent the hour? I was just thinking that since you have 24 Spiderman variations, representing the hours with a different prop might be redundant. Is finding Spidermen that look considerably different on such a small screen easy? maybe even a spiderman going to bed could mean its night time, time to go to bed, like does it have to convey actual time? It could revolve around your activities for the day maybe? Also, super cute diagrams!!

## Our barebones clock

For our barebones clock, we modified images.py to allow for switching between two images on click: Spider-Man in the daytime and Spider-Man at night. This was the base functionality of our clock. We were surprised at how great the resolution is on the Adafruit screen!

https://github.com/user-attachments/assets/5d58c970-658b-4aca-bdf4-0fa92452afc4


## Final PiClock

After we were able to successfully display and switch between images on our bare-bones clock, we generated images for each hour of Spider-Man's day to display on the Pi. To avoid copyright issues, we prompted our own version of a masked hero and came up with scenarios/actions he does for each time of day (ex: waking up at 6am, fighting a villain at 9pm, sleeping from 2am to 7am). Our scenarios were inspired by the Spider-Verse franchise, though we added our own twists as well. To spruce it up, we generated multiple images for each hour to simulate animation sequences and make the time display more film-like. We took our user feedback into consideration and decided against adding food for each hour, and instead focused on updating the background image so the clock is readable and not crowded.

\*\*\***TODO: Add video**\*\*\*

