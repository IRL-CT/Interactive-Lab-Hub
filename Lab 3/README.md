# Chatterboxes
**Sean Hardesty Lewis (Solo)**

## Prep for Part 1: Get the Latest Content and Pick up Additional Parts 

Done!

## Part 1.
### Setup 

Done!

### Text to Speech 

Done!

My script is `speech-scripts/greet_shawn.sh`. I like the emphasis on the h so I made it say "Shawn" instead of "Sean".
  
### Speech to Text

Done! 

My script is `speech-scripts/check_words_example/number_input.sh`. I re-used the test_words.py from the vosk demo and it saves the answer to `number_input.txt`.

### 🤖 NEW: AI-Powered Conversations with Ollama

My simple voice interaction is a "voice calculator". I have always found TI-84s and similar calculators to be nightmares to use since they have so many buttons- and I often find myself able to articulate what I want in my head, but it will take minutes to find each button and press them in the right order on the calculator. To this extent, my voice interaction aims to solve that. You ask your questions similarly to our numeric input system from earlier, we can then perform simple calculations in the backend (or in this case, utilize Ollama's trained knowledge, and hope that it is correct), then use text to speech to give the result back to the user.

### Serving Pages

Done!

### Storyboard

Done!

![IMG_5662](https://github.com/user-attachments/assets/b3aebdce-016e-46e7-bdda-9751e7c3cce2)

**Imagined Dialogue:**

User: "What is fifty divided by five?"

System: "Fifty divided by five is ten."

User: "What is nine times eight?"

System: "Nine times eight is seventy two."

User: "What is ten percent of two hundred?"

System: "Ten percent of two hundred is twenty."

### Acting out the dialogue

My interaction was done with Benthan Vu but I did not record it. However, I did write down the transcript, and have re-recorded his exact questions below.

It is important to note that his integral question was not answered correctly by Ollama.

https://github.com/user-attachments/assets/3330cb21-fc17-4547-b27f-a5998e017719

The dialogue was a bit different due to understandable impatience due to pacing, and limits of using Ollama for mathematics.

For the pacing, it was quickly realized that the restatement of the response was unnecessary. User preferred shortened answers, and full restatements (“Fifty divided by five is ten”) worked for the first turn but were repetitive by the second question. The user got impatient to listen to it repeat the entire problem again before giving the answer and expressed this after the the dialogue concluded.

For the limits of using Ollama, since the model is rather a text-generation model and not performing any background scripts, it became very clear as soon as more complex math was asked (e.g. derivatives, integrals, etc.) that it was not well-suited for the task.

# Lab 3 Part 2

## Prep for Part 2

I feel like the text to speech model could be swapped out to a higher quality one.
   
I would love to integrate some kind of sensor, like vision of the surrounding environment or actors through a camera, or kinetic motion through the gyro sensors similar to the example WoZ eight-ball.

Based on my above reflections, I have decided to create a Personalized Robot. This project will have heavy similarities to the [below Harvard project](https://lil.law.harvard.edu/events/i-xray-lunch/). This idea is not that original and has been in many different contexts throghout the years (ex. [Clearview AI](https://www.forbes.com/sites/roberthart/2024/09/03/clearview-ai-controversial-facial-recognition-firm-fined-33-million-for-illegal-database/)). Relating to myself, I came up with my own version of this idea two years ago during undergrad and working with traffic cameras when the newest python facial landmark detection library came out but never did anything with it. So like how MIT has its slogan "demo or die" I never demo'd or built my idea for this two years ago, and have subsequently been outdone (to great extent!) by these Harvard students. Their project is well recorded and has some good videos of interaction with it- I recommend you check out the following video, and support their privacy safety efforts.

https://github.com/user-attachments/assets/e7b0a26d-7fb8-4843-81f1-5763f8280f30

## Prototype your system

Below are some of my sketches for the system prototype.

![IMG_5663](https://github.com/user-attachments/assets/d5c179c4-424c-4281-bc8b-9651a92601a9)

As well as my Verplank diagram.

![IMG_5664](https://github.com/user-attachments/assets/2b2f3549-7e14-438d-8e45-494d0c324e92)

As much as I love wizarding, I wanted to go for a completely continuous live experience for my interaction. So I completely removed the need for a controller / wizarding by just having the interaction loop continuously run on the Raspberry PI 5 infinitely.

My interaction loop:

1.) Listens for user input, once user input has stopped being detected, uses STT to record what the user said.

2.) Once it has recorded what the user said, it takes a temporary picture with the webcam of the user.

3.) This temporary picture is used in a precomputed facial landmark database for similarity to other faces.

4.) Finds the most similar face (no threshold was implemented in my version), then returns the name associated with the face.

5.) The name associated with the face is fed into a system prompt which guides the system in responding to

  * the user prompt
  * details of the user's name according to the landmark database
  * using TTS to respond to user with a personalized response including their name

6.) Repeats to Step 1 again, infinitely.

Here is a picture of the device (with webcam attached):

![IMG_5667](https://github.com/user-attachments/assets/4ad3289d-ab45-4851-acce-8c8230b6c2a1)

<details>
  <summary><strong>Submission Cleanup Reminder (Click to Expand)</strong></summary>
  
  **Before submitting your README.md:**
  - This readme.md file has a lot of extra text for guidance.
  - Remove all instructional text and example prompts from this file.
  - You may either delete these sections or use the toggle/hide feature in VS Code to collapse them for a cleaner look.
  - Your final submission should be neat, focused on your own work, and easy to read for grading.
  
  This helps ensure your README.md is clear professional and uniquely yours!
</details>

## Test the system
Try to get at least two people to interact with your system. (Ideally, you would inform them that there is a wizard _after_ the interaction, but we recognize that can be hard.)

Answer the following:

### What worked well about the system and what didn't?
\*\**your answer here*\*\*

### What worked well about the controller and what didn't?

\*\**your answer here*\*\*

### What lessons can you take away from the WoZ interactions for designing a more autonomous version of the system?

\*\**your answer here*\*\*


### How could you use your system to create a dataset of interaction? What other sensing modalities would make sense to capture?

\*\**your answer here*\*\*














