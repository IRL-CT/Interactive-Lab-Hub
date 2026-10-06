# Chatterboxes

## A. Text to Speech

Link to shell file: https://github.com/chonjessica23/Interactive-Lab-Hub/blob/Fall2026/Lab%203/speech-scripts/hijessica.sh 

\*\***Then answer: Is the same greeting, in these different voices, the same greeting? Describe one concrete way the voice changed what the utterance seemed to mean or who seemed to be speaking.**\*\*

I would say yes, the greeting is the same despite the voices changes. I noticed that when I went from US to Scottish English, the only changes were a very subtle difference in how and how long vowels were pronounced. 


## B. Speech to Text

\*\***Record a few seconds of your own speech (`arecord -d 5 -f cd -c 1 -r 16000 test.wav`) and transcribe it with at least two model sizes. Report the real-time factor for each. At what point does the accuracy improvement stop being worth the delay, for a system that has to answer you?**\*\*

The base.en model had a real-time factor of 0.43x, while the small.en model had a real-time factor of 1.24x.  During this test, I found that base.en was faster but made a small transcription error, while small.en was more accurate but slower. My recorded phrase was "Hello, it's the weekend and I'm currently testing this." The small.en model was able to accurately transcribe fully, while base.en transcribed "weekend" as “week and.” However, small.en took longer than the five-second recording itself to transcribe. While I'd prefer accuracy for this example, I'd imagine the extra time for processing would be a significant downside for much longer speeches since responsivity is, I'd argue, most important. 

\*\***Write your own script that verbally asks for a numerical input (a phone number, zipcode, number of pets) and records the answer the respondent provides.**\*\* Numbers are a good stress test — transcription systems make characteristic errors on digit strings, and you will want to know what they are before you design around them.

Link to file: https://github.com/chonjessica23/Interactive-Lab-Hub/blob/Fall2026/Lab%203/speech-scripts/askforzip.sh 

## C. Turn-taking: knowing when someone has stopped talking

\*\***Try both extremes, and something in between. Describe what each one feels like to talk to. Note specifically: at 0.2s, what kinds of normal speech get cut off? At 1.5s, what does the delay make the system seem like?**\*\* There is no correct value. A system that takes drink orders and a system that listens to someone think out loud want very different thresholds, and the right one depends on what your users are doing with their pauses.

I noticed that for the 0.2-second session, the beginning of my sentences were getting cut off more often, especially when I paused briefly before continuing. For the 1.5 seconds, I felt slightly frustrated because I had to wait longer before the system moved on to my next sentence, which made the interaction feel slower.

## D. Storyboard

**Fortune Telling Device**

<img width="281" height="224" alt="Screenshot 2026-09-26 at 3 23 28 PM" src="https://github.com/user-attachments/assets/a2e973e9-5d93-4bd4-9784-7bf1948d8159" />

I took inspiration from both fortune cookies and paper fortune tellers (picture above) for this project. While brainstorming, I wanted to utilize the echo_bot.py but wanted a more back-and-forth interaction than having the device simply repeat what users said. I also wanted the interactions to feel somewhat natural adn not obvious what I'd program was preprogrammed responses. I then thought fortune telling would offer more controlled/workable responses, but be able to feel organic enough where it didn't feel overtly structured. Below is the speech flow I anticipate: 

<img width="506" height="683" alt="Screenshot 2026-09-26 at 3 24 31 PM" src="https://github.com/user-attachments/assets/9d9805ad-095e-4414-81bb-3a2700f78e77" />

After coming up with the dialogue, I went to storyboards, and found I needed to consider how to prompt the conversation since the program can't be running continuously. So, I added a button to start the experience and also see if I could experiment working with buttons. I didn't want everything to be purely verbal since part of the fun in doing paper fortune telling is picking out the numbers yourself. So, I think I'll incorporate the Adafruit MPR121 12-Key Capacitive Touch Sensor. Below are the storyboards.  

<img width="460" height="634" alt="Screenshot 2026-09-26 at 3 24 46 PM" src="https://github.com/user-attachments/assets/c94c5868-dd7f-4d05-8f11-7925cbd5f19a" />

<img width="461" height="305" alt="Screenshot 2026-09-26 at 3 25 44 PM" src="https://github.com/user-attachments/assets/2508d89d-f349-4010-811a-554e65b8d5fa" />

Since the dialogue will be semi-structured, I anticipate the pauses won't be too long nor take too long because it'll be mostly one word/very short sentences. So when I get to coding, I'll probably have to make the program anticipate brief silences and responses.

## E. Acting out the dialogue

I found a partner during Wednesday's lab to go through my dialogue. Truthfully, the dialogue didn't diverge much from what I had anticipated, which is part of the reason why I chose a fortune theme since people will just be selecting from options. However, before I acted out the dialogue with my partner, I had to be very intentional about my quesiton wording so that I could avoid any dialogue deviations. 

---

# Lab 3 Part 2





## Prep for Part 2

For the part 2 of this lab, I didn't change much of what I initially wanted to do since my initial plans already included the touch sensor. However, when reflecting on more ways people interact with devices, I realized more visual and audio cues would be helpful for not only guiding users through the interactions, but making the experience more engaging. So, I added text to the screen in case users forgot or couldn't hear what the speaker was saying clearly, and also a "complete" sound for when the fortune was about to be told so that users weren't left waiting for an unknown amount of time (fortune_complete.wav). Also, while iterating through the project, I realized I needed output for when the system didn't hear one of the programmed responses, so I added in dialogue to address that. 

As a general overview, the way the program works is that the mic picks up audio and begins speaking asking what topic the user would like to focus on for their fortune. The majority of the program is just made with if/else and while statements, where users go through a topic, number to pick on the sensor board, and then a color of the rainbow.


<img width="609" height="322" alt="Screenshot 2026-10-04 at 7 51 42 PM" src="https://github.com/user-attachments/assets/47c1433b-b65c-40d5-888f-408b72665f72" />

After receiving all those inputs, the code picks a random fortune (shown below) and reads it out loud. 

<img width="496" height="486" alt="Screenshot 2026-10-04 at 7 51 28 PM" src="https://github.com/user-attachments/assets/ebf40907-5f74-49aa-acb4-86fa8ed1fd4c" />
<img width="593" height="609" alt="Screenshot 2026-10-04 at 7 51 55 PM" src="https://github.com/user-attachments/assets/c6c04bba-da31-4af4-925a-99f780ddec82" />

This is the video of the final result:

https://github.com/user-attachments/assets/347e24e5-0a6b-4696-a667-521b7435ce3d

What the terminal is showing:
<img width="679" height="171" alt="Screenshot 2026-10-04 at 7 39 29 PM" src="https://github.com/user-attachments/assets/e3ef2834-7c9a-4772-8675-6ceae6de6507" />

Final setup:
<img width="1006" height="653" alt="Screenshot 2026-10-04 at 7 50 18 PM" src="https://github.com/user-attachments/assets/bb8e3cea-af8a-4bb3-83b9-20653e9ded40" />

The full code file is here: https://github.com/chonjessica23/Interactive-Lab-Hub/blob/Fall2026/Lab%203/speech-scripts/ifortune.py 

### What worked well about the system and what didn't?

The speech recognition was probably the most difficult aspect of this project. I found that users had to articulate their words loudly and clearly in order for the system to process them correctly. Even within the video above, you can see that it heard random words at times. During trials, it would  often mistake "school" for "cool," which made it difficult for the system to recognize the user's intended response.

### What worked well about the controller and what didn't?

I found that the controller worked well for keeping the interaction organized and moving the user through each step of the fortune-telling experience. However, I think the biggest issue was how dependent it was on everything progressed. If the speech recognition misunderstood something or the user gave an answer that the program wasn't expecting, the controller didn't have much flexibility to work around it. This made me realize that even if the individual parts of the system work, connecting everything together can still be difficult when the system has to account for unexpected interactions.

### What lessons can you take away from the WoZ interactions for designing a more autonomous version of the system?

I learned that it's hard to not only anticipate how users will interact, but also take into account the technical limitations, whether that be my own abilities of the technology I'm working with. Basically, I believe the flexibility on both ends is something that I have to really account for and work around. For example, if the program is expecting the user to say "career," it should ideally also be able to understand something like "I want to know about my future job" is the same thing.

### How could you use your system to create a dataset of interaction? What other sensing modalities would make sense to capture?

If I iterated again, I would make the interaction a bit longer and more elaborate so that I could keep a record of each interaction and gather more data such as how long they took to respond, what they're speaking about, etc.. I'd also keep track of when the system misunderstood the user or had to ask them to try again so that I could learn how to understand users better.

For other sensing modalities, I think a camera would be useful for capturing things like facial expressions, where the user is looking, and whether they're paying attention to the system. I'd probably also work more on the microphone to pick up pauses, like I mentioned above, so that the entire fortune-telling experience can feel more personalized and natural.


