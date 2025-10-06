# Chatterboxes
**Joy Sun (Jiayi Sun) and Sandy Zhan (Huiying Zhan)**

## Part 1.
### Text to Speech 

In this part of lab, we are going to start peeking into the world of audio on your Pi! 

\*\***Write your own shell file to use your favorite of these TTS engines to have your Pi greet you by name.**\*\*
(This shell file should be saved to your own repo for this lab.)  

<mark>See my implementation here: [greet_joy.sh](./speech-scripts/greet_joy.sh)</mark>

---
### Speech to Text

\*\***Write your own shell file that verbally asks for a numerical based input (such as a phone number, zipcode, number of pets, etc) and records the answer the respondent provides.**\*\*  

<mark>See my number speech detection script here: [ask_number.sh](./speech-scripts/ask_number.sh)</mark>

### Picture 1: Number Speech Record
<img src="speech number recording.jpg" alt="Interactive Speech AI" width="700">


### 🤖 NEW: AI-Powered Conversations with Ollama

\*\***Try creating a simple voice interaction that combines speech recognition, Ollama processing, and text-to-speech output. Document what you built and how users responded to it.**\*\*  

### Picture 2: Interactive Speech
<img src="interactive speech ai.jpg" alt="Interactive Speech AI" width="700">


## <mark>My System Components</mark>

### 1. Speech Recognition
- We use the Python [`speech_recognition`](https://pypi.org/project/SpeechRecognition/) library to capture audio from a microphone.
- The system supports selecting a preferred microphone (e.g., Logitech C270 HD Webcam) automatically, with fallback to the default device if the preferred one is unavailable.
- Listening mechanism configuration:
  - Listen for a maximum of **15 seconds** per input.
  - Automatically stop listening if the user is silent for **2 seconds**.
- This allows quick capture of short user queries while avoiding long idle recordings.


### 2. Ollama AI Processing
- Captured speech is converted to text via **Google Speech Recognition**.
- The text is sent as a prompt to the Ollama model (`phi3:mini`) via its REST API.
- Query timeout is **3 minutes** to allow for complex responses, with progress messages shown to the user.
- Ollama generates a textual response based on the user’s input.


### 3. Text-to-Speech (TTS) Output
- Response text is converted into speech using **espeak**.
- Special character handling:
  - Characters like `–` or `—` are replaced or removed to prevent TTS errors.
- Speech playback is fully completed before the next listening session begins, preventing the microphone from capturing the assistant’s own voice.


### 4. Concurrency and Flow Control
- Blocking calls are used for espeak, ensuring each TTS playback completes before listening starts again.
- Prevents overlapping input/output, ensuring only the user’s voice is recognized.


## <mark>User Experience and Feedback</mark>
- Users can speak naturally in English and receive almost immediate responses.
- Responses are read aloud in a clear voice, creating a conversational feel.
- Long or complex queries are handled gracefully, with a 3-minute timeout for AI responses.
- Special character handling ensures TTS errors do not interrupt the interaction.
- Users found the system intuitive, with quick response times and smooth audio feedback.


## <mark>Conclusion</mark>
This project demonstrates a fully functional voice interaction loop combining:

- **Speech recognition**  
- **AI processing via Ollama**  
- **Text-to-speech output**  

The system effectively handles microphone selection, ambient noise calibration, Unicode-safe TTS, and sequential listening/speaking, resulting in a responsive and user-friendly voice assistant prototype.


### Storyboard
\*\***Post your storyboard and diagram here.**\*\*

### <mark>Verplank diagram</mark>
We designed a **Smart Mirror Outfit Assistant** that recommends daily outfits based on **weather, temperature, and special occasions**. The interaction is through **voice input** and **speech + visual overlay** output.

1. **Morning Start**  
<img src="./storyboard1.jpg" alt="Storyboard Situation 1" width="500"/>  

2. **Special Occasion**  
<img src="./storyboard2.jpg" alt="Storyboard Situation 2" width="500"/>  

3. **Misunderstanding Branch**  
<img src="./storyboard3.jpg" alt="Storyboard Situation 3" width="500"/>  


\*\***Please describe and document your process.**\*\*
## <mark>🌳 Dialogue Tree: Smart Mirror Outfit Assistant</mark>
### Panel 1 – Morning Start (Weather-based Recommendation)

**User**: "Mirror, what should I wear today?"  
→ *System checks today’s weather*

#### If Rainy 🌧️
- **System**: "It’s rainy today. I recommend wearing a raincoat and waterproof shoes."  
- **User**: "Should I also bring an umbrella?"  
- **System**: "Yes, carrying an umbrella will keep you dry."

#### If Snowy ❄️
- **System**: "It’s snowing today. I suggest a down jacket, warm boots, and gloves."  
- **User**: "Can I wear sneakers instead?"  
- **System**: "Sneakers may get wet in the snow. Boots would be safer."

#### If Sunny & Hot ☀️
- **System**: "It’s sunny and warm, around 28 degrees. I recommend a T-shirt and shorts."  
- **User**: "Do I need sunglasses?"  
- **System**: "Yes, sunglasses will help protect your eyes from the bright sun."

#### If Cold but Clear 🌤️
- **System**: "It’s 12 degrees but clear. I suggest wearing long pants and a jacket."

---

### Panel 2 – Special Occasion (Context-based Recommendation)

**User**: "I have a job interview today."  
→ *System applies formal attire rules*

- **System**: "For a formal occasion, I recommend a dark suit with a white shirt. That will look more professional."  
- **User**: "Should I wear a tie?"  
  - If **Yes** → "A simple dark tie will make your outfit more polished."  
  - If **No** → "That’s fine, but with a tie you’ll look more formal."  

- **User**: "Can you show me how it looks?"  
- **System**: *[Overlay suit + tie on reflection]*

#### Alternative Occasions
- **If Dinner Date** → "A smart-casual outfit would be good, like a blazer with chinos."  
- **If Sports Event** → "Casual wear is fine — maybe a hoodie and sneakers."

---

### Panel 3 – Misunderstanding Branch (Error Handling)

**User**: "Recommend a pair of shoes."  
→ *ASR Misheard* → "Recommend a skirt."  

- **System (clarification strategy)**: "Did you mean skirt or shoes?"  
- **User**: "Shoes."  
- **System**: "Great. Do you want formal shoes or casual shoes?"  
  - If **Formal** → "Black leather shoes would match your suit perfectly."  
  - If **Casual** → "White sneakers would go well with a casual outfit."
  

### Acting out the dialogue

### <mark>🎧 Dialogue Audio Recording</mark>
You can listen to the acted-out dialogue here:  
[Dialogue performing.m4a](./Dialogue%20performing.m4a)   

\*\***Describe if the dialogue seemed different than what you imagined when it was acted out, and how.**\*\*
### <mark>Reflection: Differences Between Imagined and Real Dialogue</mark>

When we acted out the dialogue, it turned out to be quite different from the imagined dialogue tree.

#### Structured vs. Natural Flow
- **Imagined version**: Highly structured, with predefined conditions (rainy, snowy, sunny, cold).  
  - User asked short, direct questions like *“Should I also bring an umbrella?”* or *“Do I need sunglasses?”*.  
  - The flow assumed clear, logical branches.  

- **Real version**: User spoke more naturally and unpredictably.  
  - Example: *“Today I would like to go out. What kind of suit would you recommend?”*  
  - This shifted the topic toward **activity-based clothing** rather than just weather.  
  - System (played by partner) adapted by asking about the **occasion**, leading to discussions about **sportswear, tennis skirts, and even color preferences**.

#### Personalization and Context
- Real dialogue introduced **unexpected context and personalization**.  
  - Example: detecting closet inventory (*“blue and pink skirts”*) and giving **tailored recommendations**.  
- This personalization was **not considered** in the original dialogue flow.

#### Key Insights
- **Imagined script**: Useful as a starting point to structure logic.  
- **Real interaction**: Showed that actual users bring in:  
  - Personal preferences  
  - Casual, varied language  
  - Follow-up questions beyond the rigid tree  

**<mark>Conclusion</mark>**: The acting-out exercise highlighted the importance of **flexibility, personalization, and error-handling** in real system design, beyond what a fixed dialogue tree can capture.


# Lab 3 Part 2

For Part 2, you will redesign the interaction with the speech-enabled device using the data collected, as well as feedback from part 1.

## Prototype your system
### <mark>1.New Story Board</mark>
#### Situation 1: Choose the Type
<img src="choose the type.jpg" alt="Choose the Type" width="500">

#### Situation 2: Choose the Outfit
<img src="choose the outfit.jpg" alt="Choose the Outfit" width="500">

### <mark>2.Document how the system works</mark>
### System Documentation 1: Wizard of oz
#### 1.Overview

This project is an interactive demo that runs on a Raspberry Pi and connects a SparkFun Qwiic Joystick to a web interface. The system streams joystick data to a browser in real time and allows the user to convert typed text into spoken audio on the Pi. The implementation uses a lightweight Flask web server with Socket.IO for bi-directional messaging, and espeak for local text-to-speech output.

#### 2.What we achieved

- Provide a clean, low-latency demo of hardware → web interaction.

- Replace an accelerometer-based input with a Qwiic Joystick as the primary interaction device.

- Keep audio output stable and deterministic (avoid flaky real-time microphone streaming).

#### 3.How it works
This prototype demonstrates an interactive dialogue system between a user and a smart mirror, implemented on a Raspberry Pi.

The interaction is simulated through a hardware joystick and a web interface:

- The joystick acts as the user’s physical input device, representing gestures or presence in front of the mirror.
When the joystick is moved or pressed, its real-time position data are captured by the Raspberry Pi and transmitted to the browser via a lightweight Flask + Socket.IO server.
This simulates how the mirror might sense or respond to a user’s movements or actions.

- The web interface represents the mirror’s intelligence and speech output.
The browser allows text input, which mimics what the mirror would “say” in response to the user.
When a line of text is entered, it is sent to the Raspberry Pi through a WebSocket connection.
The Pi immediately converts the text into speech using the built-in text-to-speech engine (espeak), producing an audible reply through the speaker — just as a smart mirror might talk back to the user.

**Through this setup, the system forms a closed interaction loop:**

1.User gesture or presence → sensed by the joystick and visualized on the web page.

2.Mirror response → simulated by typed text, spoken aloud by the Raspberry Pi.

This prototype effectively recreates a two-way conversational experience between a user and an intelligent mirror, without relying on heavy machine-learning or cloud components. It provides a simple, tangible framework to explore timing, responsiveness, and interaction design in human-mirror communication.

### System Documentation 2: Joystick Interaction

The system is an interactive outfit recommendation device built with a Raspberry Pi and a SparkFun Qwiic Joystick. The joystick provides horizontal, vertical, and button inputs over the I²C interface, while the software interprets these signals to control theme navigation and trigger voice responses. When the program starts, it calibrates the joystick by sampling its center values and dynamically sets threshold ranges for motion detection. Pushing the joystick **up or down** changes the outfit theme (Sports, Social, Color, Interview, Daily) and automatically plays a voice line through Piper TTS. Moving **left or right** cycles through the options within that theme, and pressing the joystick button runs `voice_interaction_router.py`, which handles open-ended voice questions using the logic defined in `outfits.py`. Each spoken line follows the unified format:  
`recommend type: <Theme>. Option <Index>. <Sentence>`.

The main control loop continuously polls `joystick.horizontal`, `joystick.vertical`, and `joystick.button` at around 20 Hz. It applies hysteresis thresholds to avoid jitter and uses short cooldown timers to prevent rapid re-triggering. If the button hardware fails or is unavailable, the system automatically falls back to a “mid-hold” interaction—holding the joystick near its center for 1.2 seconds also starts voice Q&A. All audio is generated through Piper and played via `aplay`, with Espeak as a backup. Error handling ensures stable operation even when I²C reads intermittently fail, so users always experience smooth physical control and synchronized spoken feedback.


### <mark>3.Include videos or screencaptures of both the system and the controller.</mark>

[Watch the Mirror Interaction video here](https://youtu.be/myvbhKIoJT8)

[Watch the User Conversation video here](https://youtu.be/t43ZWVyX4Zk)




## Test the system

### What worked well about the system and what didn't?
The system successfully guided both participants through theme and outfit selection with clear audio feedback. The voice output was natural and the “recommend type” prefix helped them understand the context of each option. The participants found the up/down and left/right navigation intuitive once they heard the first few lines. However, there was occasional delay in audio playback, especially when Piper was generating longer sentences. One participant also noticed that quick joystick movements were sometimes ignored, suggesting that the input thresholds could be more responsive.

### What worked well about the controller and what didn't?
The Qwiic Joystick offered smooth analog control and provided a clear sense of directionality for switching between options. The physical form made it easy for users to remember which axis changed themes versus options. The press-to-speak action worked well for triggering the voice Q&A mode, but some users pressed too briefly, leading to missed triggers due to hardware debounce. The fallback “hold in the middle” interaction helped prevent deadlocks, but users didn’t always realize it was an intentional feature.

### What lessons can you take away from the WoZ interactions for designing a more autonomous version of the system?
From the Wizard-of-Oz sessions, it became clear that the system benefits from short, conversational feedback to keep users engaged. Participants tended to wait for confirmation after each action, implying that a fully autonomous version should generate quick acknowledgments such as “Got it” or “Switching to Social theme.” It also showed that adaptive timing—pausing slightly after playback before accepting new input—would make interactions feel smoother. A more autonomous version could combine user intent prediction (based on repeated joystick patterns) with contextual language responses for a more human-like experience.

### How could you use your system to create a dataset of interaction? What other sensing modalities would make sense to capture?
The system could log joystick positions, button states, timestamps, and recognized speech transcripts to create a dataset of multimodal interactions. Each session could store pairs of physical input sequences and spoken responses, enabling supervised learning of user intent patterns. Adding a small microphone array could capture tone and hesitation, while a camera could record facial expressions or gaze direction to analyze engagement. These additional sensing modalities would allow future models to learn richer mappings between gesture, voice, and emotional state, supporting more adaptive and autonomous dialogue behavior.

