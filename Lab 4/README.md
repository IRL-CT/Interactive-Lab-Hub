# Ph-UI!!!


---

Jessica Chon (jc3932)
Asian Auntie Machine

## Part 1 Lab Preparation

I decided to create an “Asian Auntie Machine,” for this lab. I was inspired by the common trope of aunties who try to feed you more food, scold you for eating more, but then continue to offer you more anyway. Using a cardboard figure, servos, a proximity sensor, and a small OLED display, I want to recreate this contradictory behavior through beckoning and swatting motions, along with changing facial expressions and/or or sentences on the screen. The goal is to capture the humor and absurdity of this interaction in a playful, physical way.

**\*\*\*Draw 5 sketches that explore different physical arrangements for your sensing and actuation.\*\*\***

Below are my five sketches exploring different physical arrangements for my sensing and actuation components. I tried to consider how the components could be housed without getting in the way of the interaction. For example, many of the sensors and actuators are hidden inside or underneath boxes, with wires concealed within structures such as arms.

<img width="1010" height="763" alt="Screenshot 2026-10-11 at 4 21 48 PM" src="https://github.com/user-attachments/assets/df91ce91-389f-4c89-a6b7-5da19f59b107" />

As I continued sketching, I also started thinking more about how the physical form could contribute to the interaction itself. My designs gradually progressed from a literal, human-like figures to more abstract arrangements. This change came from the useless box inspiration, which I believe is able to convey playfulness and even frustration  without using any literal representations or people.

<img width="1102" height="678" alt="image" src="https://github.com/user-attachments/assets/6caa51b5-d536-4ad3-891d-6e64540a503d" />

**\*\*\*What questions do these sketches raise? What do you need to physically prototype to answer them?\*\*\***

I found the sketching process useful because it made me think more deeply about how I would disguise and house the components, as well as the physical limitations of the items I plan to use. I started considering how much space the servos would need to move the arms, where the sensor should be placed, and how I could hide the wiring without restricting where I could position the components.

The rough cardboard prototype will be helpful in figuring out the auntie's overall form and how the different components could fit together. In particular, I want to test how the arms could hold the snack jar while still allowing enough room for the beckoning and swatting motions. I'll also need to consider where the OLED screen could fit into the face and where the sensor could be positioned to detect the user's gestures without being obstructed by the cardboard. 

I also started thinking more about how to make the machine feel immersive. I hadn't initially thought about adding a screen, but I realized that using a small OLED display as the mouth could help communicate the auntie's reactions and reinforce whether the user should continue taking snacks or stop.

**\*\*\*Pick one design to prototype and explain why.\*\*\***

I decided to go with Sketch 1. Initially, I liked Sketch 4 because I wanted to explore more indirect ways of signaling the interaction to the user. However, I worried that if I made the design too abstract, it could be misconstrued as diet-related commentary rather than poking fun at the absurdity and contradictory nature of this type of Asian auntie interaction. I liked Sketch 1 because I think the cardboard human figure is literal enough to establish that this is an auntie who behaves in a recognizable way, and we generally dismiss more controversial behavior to older figures. I did consider Sketch 2, but as I was acting our the interactions, I believed having the figure hold the jar would add too much intimidation, making users not think they could grab the snacks. 

For the prototype, I'm planning to have the auntie beckon the user to take snacks, then switch to a swatting motion after the user has taken snacks a certain number of times. The OLED mouth will display expressions that reinforce these actions. If the user leaves the machine alone for a while, it will start beckoning them to take snacks again.

**\*\*\*Document your rough prototype with photos and/or video.\*\*\***

As I started working on the physical prototype, I began thinking more seriously about balancing, sizing, and weight. I realized that the auntie couldn't be too small or too big, since that would affect how realistic and comfortable the interaction felt. I wanted her to be large enough to feel like a character the user is interacting with, but not so large that the interaction becomes overwhelming or difficult to approach.

<img width="421" height="539" alt="Screenshot 2026-10-11 at 4 21 27 PM" src="https://github.com/user-attachments/assets/322b405d-7dbe-4baf-8a8a-00062505df4b" />

I also started considering the weight of the arms more carefully. The servos are small and weaker, so I realized I needed to keep the arms as lightweight as possible. Originally, I was thinking of having the hand or wrist rotate to create the beckoning motion more realistically. However, I realized that placing a servo at the end of the arm would add too much weight and make it harder for the main servo to lift the arm. Because of this, I decided to simplify the movements instead. Rather than rotating the wrist, I'm exploring smaller tapping movements against the plate to encourage the user to take more snacks, followed by a larger up-and-down arm movement to imitate a swatting motion or placing a hand over the snacks to tell the user to stop.

<img width="581" height="742" alt="Screenshot 2026-10-11 at 4 21 42 PM" src="https://github.com/user-attachments/assets/b6536d00-4b18-49a5-a3c5-d36baf1cf912" /><img width="585" height="659" alt="Screenshot 2026-10-11 at 4 21 35 PM" src="https://github.com/user-attachments/assets/3cfc805f-cb1d-48be-8605-ecd67059479e" />

I still need to test how fast the servo can move and how that affects the interaction. I want the swatting motion to feel distinct enough to communicate that the auntie is telling the user to stop, but I also don't want it to look too aggressive. Depending on the speed and range of movement, it could come across more as a playful swat or a gentle gesture of disapproval.

**USER TESTING**: I went back home for the weekend, so I was thankfully able to find a friend to user test. My main concern was whether the arm-swinging motion could convey enough emotion and cues to signal when to take or stop taking food. To test this, I asked my friend to go through the interaction with little explanation of the project background so I could see how they would respond naturally.

During testing, I noticed that the arm movements alone weren’t clear enough to communicate when to take more or when to stop, which was what I was concerned with. I also  that the arm didn’t have enough time to react before my friend grabbed the food, making it difficult to use the swinging motion to signal them to stop. More importantly, my friend seemed ready to stop after taking the first piece, rather than continue taking more. She only took more when  I intervened with verbal cues like “take some more!” while mimicing how an Auntie would speak. This made me realize that the interaction was becoming more confusing and burdensome than fun or playful, partly because I was trying to communicate two opposing actions: encouraging the user to take food while also telling them when to stop.

Based on this, I think it would be better to pivot toward encouraging the user to keep taking food rather than adding an element that tells them to stop. I actually feel more confident about this direction because it connects to a real-life experience: my Asian mom wouldn’t stop offering my friend food, even when she protested, haha. I think leaning into this familiar dynamic could make the interaction feel more natural, playful, and relatable. Thsi is further supported by my friend laughing when I kept encouraging her to take food.

For my next iteration, I don’t think I need to change much about the physical prototype, since my friend was amused by its appearance. Instead, I plan to focus on improving the interaction by incorporating the speech element from the last lab and using a sensor to trigger the interaction when the user approaches. When the user tries to leave, the figure will tell them they should take more, while the arm will reinforce this through gentle tapping on the food. All the wiring, raspberry pi, and servos will remain positioned behind the figure, and the arm will be made of paper so it can move quickly and easily without putting too much weight on the servos.

---

## Part 2

Following exploration and reflection from Part 1, complete the "looks like," "works like" and "acts like" prototypes for your design, reiterated below.

---

#### Build & Integrate: Sensing + Actuation

Parts:
	- Cardboard, colored paper, tape, glue, pens
	- 1x servo
	- 1x SparkFun Proximity Sensor
	- Raspberry Pi
	
**Link to code**: https://github.com/chonjessica23/Interactive-Lab-Hub/blob/Fall2026/Lab%204/asian_auntie_machine.py 

The coding program was based on pi_servo_hat_test.py (https://github.com/IRL-CT/Interactive-Lab-Hub/blob/Fall2026/Lab%204/pi_servo_hat_test.py) & qwiic_distance.py (https://github.com/IRL-CT/Interactive-Lab-Hub/blob/Fall2026/Lab%204/qwiic_distance.py). Last lab's Piper speech program was also reused.

The program runs dependent on the set distance threshold for the sensor. When a user is far away, Auntie speaks to the user, saying random phrases to bring them back. When the user is close to Auntie, she says a random phrase of encourage and begins tapping the food to cue the user to take the food. The tapping is controlled by the servo. Below is a sketch diagram of the interaction:

<img width="4032" height="3024" alt="IMG_9675" src="https://github.com/user-attachments/assets/30831806-d0f7-4d30-bbc5-4d3b395acc17" />

<img width="420" height="379" alt="Screenshot 2026-10-17 at 1 49 09 PM" src="https://github.com/user-attachments/assets/ffd74109-a548-4615-a229-8e904a0d3407" />
<img width="417" height="408" alt="Screenshot 2026-10-17 at 1 49 17 PM" src="https://github.com/user-attachments/assets/5e4a8167-0755-4be9-88e0-3356b9d8d4d6" />

* "Looks like": shows how the device should look, feel, sit, weigh, etc.

**Building the Prototype**

For building Auntie, I found a free file to use on Vecteezy and edited the file to include just the top half on Illustrator. I then laser cut the file onto cardboard, also included two triangles to help prop up and keep Auntie standing. The rest of the process was cutting out hands, arms, and "dressing" Auntie with her clothes and adding her. This was all done with cutting and gluing printed colored paper.

<img width="3024" height="4032" alt="IMG_9661" src="https://github.com/user-attachments/assets/da16ad29-e9e9-4aed-887d-163b7331e322" />
<img width="3024" height="4032" alt="IMG_9662" src="https://github.com/user-attachments/assets/7b350f10-776c-4dba-aabb-d58373a7d2a1" />
<img width="3024" height="4032" alt="IMG_9663" src="https://github.com/user-attachments/assets/e8e57795-b6ee-417d-b5e7-ca9c5de44eb7" />

* "Works like": shows what the device can do

Below is a video of me combining the code and pi set up with the cardboard cutouts:

https://github.com/user-attachments/assets/705d5dff-0ee3-4fe1-8f2f-5ac1f691231d


* "Acts like": shows how a person would interact with the device

Below is the final working interaction. It's a bit difficult to hear on lower volume, but Auntie is speaking when the user approaches/leaves.

https://github.com/user-attachments/assets/0c3bfecb-df06-416e-80e8-4f5514b9404e

https://github.com/user-attachments/assets/39cf670b-b5f1-4349-8faa-9ca116b57774

**Reflection**

I found movement to be the most challenging aspect of this project. Based on my initial prototype, movement was difficult because it wasn't articulating the intention of the project clearly enough, and people were getting either confused or misinterpreting the interaction process. The other reason movement was challenging was because I found myself limited by technical factors, such as the servos limited range of movement and ability to bear weight. As for the sensors, it didn't come up as a challenge for this project, but I did find sensor's detection ability amusing. It turned out that my thresholds had only a 2 unit difference. 

Building the actual prototype was the most fun and rewarding. I received several comments from passerbys asking what I was doing, looking on in curiosity. It was gratifying seeing their reactions light up with understanding and amusement once I explained the project premise. Though the building process was time consuming, the conversations reminded me that the effort is worth it because it allows users to resonate/immediately understand what the project intentions are without them even interacting with the project yet.

