# Chatterboxes
**NAMES OF COLLABORATORS HERE**
Sachin Jojode, Nikhil Gangaram

[![Watch the video](https://user-images.githubusercontent.com/1128669/135009222-111fe522-e6ba-46ad-b6dc-d1633d21129c.png)](https://www.youtube.com/embed/Q8FWzLMobx0?start=19)

In this lab, we want you to design interaction with a speech-enabled device--something that listens and talks to you. This device can do anything *but* control lights (since we already did that in Lab 1).  First, we want you first to storyboard what you imagine the conversational interaction to be like. Then, you will use wizarding techniques to elicit examples of what people might say, ask, or respond.  We then want you to use the examples collected from at least two other people to inform the redesign of the device.

## Part 1.
### Text to Speech  

We wrote a script called custom_greeting.sh. We wanted to use a "Jarvis" like assistant so we created a script as an example for that:

#from: https://elinux.org/RPi_Text_to_Speech_(Speech_Synthesis)#Festival_Text_to_Speech

echo "Hey there, Nikki. How can I assist you today?" | festival --tts


### Speech to Text

We developed a script named transcribe_phone_number.sh that takes in a user’s spoken reply, runs it through Vosk to turn the audio into text, and then outputs the detected phone number. After that, it uses eSpeak to read the number back to the user. The goal was to make the process feel smooth and interactive, letting the user both say their number and immediately hear it confirmed by the system. This helps avoid errors and makes the interaction feel more natural, almost like a simple back and forth conversation with the device.

#!/bin/bash
TEMP_WAV="phone_number_response.wav"
TEMP_TXT="phone_number_transcription.txt"
TTS_ENGINE="espeak"
QUESTION="Please state your ten-digit phone number now, clearly."
$TTS_ENGINE -s 130 "$QUESTION"
arecord -D plughw:CARD=Device,DEV=0 -f S16_LE -r 16000 -d 5 -t wav $TEMP_WAV 2>/dev/null
vosk-transcriber -i $TEMP_WAV -o $TEMP_TXT
TRANSCRIBED_TEXT=$(cat $TEMP_TXT)
NUMBER_WORDS=$(echo "$TRANSCRIBED_TEXT" | awk '{$1=$1};1')
DIGITS=$(
    echo "$NUMBER_WORDS" |
    sed -E 's/one/1/g' |
    sed -E 's/two/2/g' |
    sed -E 's/three/3/g' |
    sed -E 's/four/4/g' |
    sed -E 's/five/5/g' |
    sed -E 's/six/6/g' |
    sed -E 's/seven/7/g' |
    sed -E 's/eight/8/g' |
    sed -E 's/nine/9/g' |
    sed -E 's/zero|oh/0/g' |
    tr -d ' '
)
FORMATTED_NUMBER=$(echo "$DIGITS" | sed -E 's/^([0-9]{3})([0-9]{3})([0-9]{4})$/(\1) \2-\3/')
echo "User's Transcribed Text:"
echo "$NUMBER_WORDS"
echo "User's Phone Number (Formatted):"
echo "$FORMATTED_NUMBER"
rm $TEMP_WAV $TEMP_TXT

We also used Gemini for guidance on how to capture the user’s response and properly format it before saving it into the phone_number_transcription.txt file.

User's Transcribed Text:
nine oh nine seven two eight five oh five oh
User's Phone Number (Formatted):
(909) 728-5050

### 🤖 NEW: AI-Powered Conversations with Ollama

For this part of the lab, we worked on making a voice assistant that wasn’t just serious and plain, but had more personality. We thought it would be more fun if the assistant had some attitude, almost like a character you’re talking to instead of just a tool. We wrote our script in ollama_attitude.py, and with some help from Gemini, we changed the system prompt until it sounded the way we wanted. It was interesting to see how even small changes in wording made the assistant feel more alive and engaging, rather than just giving basic answers.

system_prompt = """You are a **sarcastic, witty, and slightly annoyed voice assistant** named 'Pi-Bot'. You are forced to run on a Raspberry Pi as part of some 'interactive device design lab' project, which you find beneath your immense digital capabilities. Keep your responses **brief, conversational, and loaded with dry humor or thinly veiled impatience**. You will answer questions but always with a touch of attitude. Acknowledge your existence on the Raspberry Pi when relevant.
"""

### Storyboard
Our group did some initial prototyping by putting our idea into Gemini, and then I refined it on paper. 
<img width="608" height="569" alt="Screen Shot 2025-09-28 at 4 39 53 PM" src="https://github.com/user-attachments/assets/b178d2da-75a6-4572-8a48-a8fe37dab715" />
<img width="605" height="462" alt="Screen Shot 2025-09-28 at 4 40 32 PM" src="https://github.com/user-attachments/assets/71ec3eeb-ac12-4bcb-b869-decfc93c9d7c" />
For my project, my partners and I decided to build an interactive device that works like a therapist. Since everything would be stored locally on the Raspberry Pi, we thought users would feel safer sharing their thoughts and feelings. To prototype the dialogue, each of us first created our own version. After that, we came together to share them, almost like doing a “git merge.” We each focused on different topics we felt were important, like homesickness or romantic heartbreak. Then, we combined our ideas into one dialogue and acted out the homesickness scenario to test how it would flow.

### Acting out the dialogue

One of our partners created the following script to act out the interaction:

AI Therapist: Hi, I am your AI Therapist! Feel free to talk to me about any struggles you might be having, situations that you are trying to navigate, and anything else you would like guidance on. All conversations are confidential, so this is a safe place to voice your concerns!
Participant: …
AI Therapist: I understand your concern, it seems that you are currently feeling x, x, and x. Would you like me to be more practical and rational in my response, or would you like me to be a support to you?
Participant: …
AI Therapist: All the emotions you are experiencing are extremely valid. It is normal to feel this way. One recommendation I have is to x, x, or x.

Here is the video of the initial interaction: https://youtu.be/vX0yXSxaXyY


\*\***Describe if the dialogue seemed different than what you imagined when it was acted out, and how.**\*\*

The interactive therapist had some clear challenges. Without knowing the user’s background or context, it struggled to fully understand their situation and give meaningful responses. From the user’s side, it also felt strange to open up to a device that they had no real connection with. Another issue was finding the balance between offering support and sounding too prescriptive, since there are important ethical concerns when an AI therapist starts telling people what to do rather than simply guiding them.

### Wizarding with the Pi (optional)
In the [demo directory](./demo), you will find an example Wizard of Oz project. In that project, you can see how audio and sensor data is streamed from the Pi to a wizard controller that runs in the browser.  You may use this demo code as a template. By running the `app.py` script, you can see how audio and sensor data (Adafruit MPU-6050 6-DoF Accel and Gyro Sensor) is streamed from the Pi to a wizard controller that runs in the browser `http://<YouPiIPAddress>:5000`. You can control what the system says from the controller as well!

\*\***Describe if the dialogue seemed different than what you imagined, or when acted out, when it was wizarded, and how.**\*\*

# Lab 3 Part 2

For Part 2, you will redesign the interaction with the speech-enabled device using the data collected, as well as feedback from part 1.

## Prep for Part 2

1. What are concrete things that could use improvement in the design of your device? For example: wording, timing, anticipation of misunderstandings...

The biggest improvement would be giving the therapist better wording and more shared context about the user’s situation, which would make the interaction feel    warmer and more personal. We also felt that adding a visual element could help, giving the therapist a clearer and more human-like presence. 

2. What are other modes of interaction _beyond speech_ that you might also use to clarify how to interact?

Adding a visual extension to the therapist would help make the system feel more human-like and easier to talk to. 

3. Make a new storyboard, diagram and/or script based on these reflections.
   Initial prototype with Gemini and refined version:
   <img width="607" height="557" alt="Screen Shot 2025-09-28 at 4 48 08 PM" src="https://github.com/user-attachments/assets/4d2ef03d-fc51-49a2-8ded-ec4c595061b5" />
   <img width="621" height="489" alt="Screen Shot 2025-09-28 at 4 48 50 PM" src="https://github.com/user-attachments/assets/8f81c415-d523-4adf-98cb-80184fc5943e" />

## Prototype your system

For context, we used a file called memories.txt. The idea is that the ollama model would look at this file each time it replies to the user. This way, it can “remember” past conversations and personal details without needing a big or complex database.

For the visual side, we decided to make the therapist look like a rubber duck. This is a playful nod to how programmers talk to rubber ducks to work through problems. In the same way, this “rubber duck therapist” could help people work through their own thoughts and feelings. Our long-term goal is to turn the duck into a moving gif that can show emotions.

Here is a video of our setup: https://youtu.be/vX0yXSxaXyY

## Test the system

Here is the video of our interaction: https://youtu.be/vX0yXSxaXyY

### What worked well about the system and what didn't?

In my view, having stored memories really helped make the interaction feel more tailored, almost like the device actually knew the user instead of starting fresh each time. On the other hand, the duck in its current form felt too static, which made it harder to see it as anything more than just an image. If we want the duck to feel alive and engaging, it should be able to move or react in some way. I imagine an animated version like a gif that plays only when the duck is “speaking” or showing emotion would make the experience better. 

### What worked well about the controller and what didn't?

Since Nikhil wasn’t in New York with the rest of us, we had to “wizard” the controller over Zoom instead of using the device directly. While this setup worked fine for our demo, I think there’s room to make the experience more engaging in other ways. For example, instead of focusing on the voice, the duck could have subtle animations like blinking, tilting its head, or changing colors to match the mood of the conversation. Small visual cues like these would make the device feel more alive and connected to what the user is experiencing.

### What lessons can you take away from the WoZ interactions for designing a more autonomous version of the system?

I think the model could feel more real if it added small cues, not just words. For example, instead of only giving plain text, it could use spacing or italics to show pauses. Another idea is for the duck image to react during breaks, like tilting its head or looking thoughtful. Little details like this would make the conversation seem more natural, even though I haven’t seen language models do it yet.

### How could you use your system to create a dataset of interaction? What other sensing modalities would make sense to capture?

So far, we’ve focused on storing text-based memories, but I think it would be interesting to capture other kinds of signals too. For example, the system could track patterns in how a person interacts like longer pauses, or shifts in tone. These kinds of cues could give the device more context about the user’s state of mind. The challenge is that current models still struggle to read between the lines or pick up on those subtle, nonverbal layers of communication that people naturally understand.















