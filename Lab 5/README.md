# Observant Systems

Sachin Jojode, Nikhil Gangaram, and Arya Prasad

### Part B
### Construct a simple interaction.

Our goal is to create a system that helps non-signers learn ASL through a customized, interactive experience. The ultimate vision is to accurately recognize the user’s hand gestures and, with the help of MoonDream, provide tailored feedback or responses. As an initial step, we built a basic gesture-recognition model using Teachable Machine. However, the model showed inconsistent results with significant variation. Below is an example of one of the better outcomes we achieved using Teachable Machine:
<img width="910" height="532" alt="Screen Shot 2025-10-26 at 9 34 48 PM" src="https://github.com/user-attachments/assets/4842138a-fee6-4e8e-92fe-e9e1eea096e5" />

We decided to shift our approach and use MoonDream, which aligned more closely with what we wanted to achieve. Our current plan for a basic interaction looks like this:

1) The TTS model asks the user to perform a specific sign.
2) The user signs it, and the gesture is sent to MoonDream.
3) MoonDream identifies the gesture and provides feedback.
4) The TTS model then reads this feedback aloud to the user.
5) This process can continue in a loop, allowing for repeated and interactive practice.

Our prototype:

<img width="754" height="674" alt="Screen Shot 2025-10-26 at 9 44 31 PM" src="https://github.com/user-attachments/assets/4b820e95-28e7-4e2f-ab3c-c33385c63d5f" />

### Part C
### Test the interaction prototype

During our prototype testing, we discovered that lighting conditions and the timing of when the image is captured greatly affected the system’s accuracy. If the photo was taken too early or the lighting was not ideal, MoonDream often had trouble recognizing the gesture. We also noticed that the interaction did not reflect natural human communication. In a real learning environment with a teacher, there would be more subtle variation and flow, while our current setup feels rigid and repetitive. The prototype code can be found in moondream_sign.py.

**\*\*\*Think about someone using the system. Describe how you think this will work.\*\*\***

We noticed that learning a new language can already be frustrating, so if the system gives wrong feedback even once, users quickly lose trust in it. When we tried other tools, Google AI Live worked much better than our first version. This seems to be because it looks at a full video of the user instead of just one picture, which makes the interaction feel more natural and realistic. We plan to explore this idea more in the next part of the lab. Still, we found that Google’s model sometimes had trouble with longer clips or full conversations, often assuming everything the user signed was correct even when it wasn’t.

Video: https://youtu.be/puvYo5_OJCY

### Part D
### Characterize your own Observant system

Now that you have experimented with one or more of these sense-making systems **characterize their behavior**.
During the lecture, we mentioned questions to help characterize a material:
* What can you use X for?
* What is a good environment for X?
* What is a bad environment for X?
* When will X break?
* When it breaks how will X break?
* What are other properties/behaviors of X?
* How does X feel?

**\*\*\*Include a short video demonstrating the answers to these questions.\*\*\***

### Part 2.

Following exploration and reflection from Part 1, finish building your interactive system, and demonstrate it in use with a video.

**\*\*\*Include a short video demonstrating the finished result.\*\*\***
