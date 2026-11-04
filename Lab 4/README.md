# Ph-UI!!!

<details>
	<summary><strong>Instructions for Students (Click to Expand)</strong></summary>
  
	**Submission Cleanup Reminder:**
	- This README.md contains extra instructional text for guidance.
	- Before submitting, remove all instructional text and example prompts from this file.
	- You may delete these sections or use the toggle/hide feature in VS Code to collapse them for a cleaner look.
	- Your final submission should be neat, focused on your own work, and easy to read for grading.
  
	This helps ensure your README.md is clear, professional, and uniquely yours!
</details>

---

---

## Lab Overview
Team: <canvas group name>  
Members: David Zhang (xz2229, davidzhanggg), ...  
Clock name: <name>


For lab this week, we focus on both sensing and actuation, bringing new modes of input and output into your devices, while also prototyping the physical structure and overall look of the device. You will consider how the physical form supports sensing and actuation, and how these elements come together to shape the interaction and aesthetics of the device.

--- 

## Part 1

As you develop your Feast Automata concept, consider where the sensor and actuator need to be placed, what parts move, how electronics are housed, and how the overall form and aesthetics support the interaction.

**\*\*\*Draw 5 sketches that explore different physical arrangements for your sensing and actuation.\*\*\***
1. Tea Bag Lifter: A button activates a servo connected to the tea bag string, lifting the tea bag out of the mug when the user is ready.
2. Instant Noodle Cooler: A proximity sensor detects when a bowl of noodles is placed nearby and activates a small fan to cool the food.
3. Food Guardian: A proximity sensor detects when a hand approaches the food and triggers a servo-controlled arm to move in front of it and protect 
4. Joystick Vending Machine: The user selects one of four snacks using the joystick directions, then presses the joystick to confirm and dispense the chosen item.
5. Rotating Sushi Carousel: A button controls a servo that rotates a platform between three sushi serving positions, bringing the next piece toward the user.


<img width="2823" height="2233" alt="IMG_1022" src="https://github.com/user-attachments/assets/88581c8a-bcca-416a-bcfd-6c281d56f3a5" />
<img width="2354" height="2145" alt="IMG_1023" src="https://github.com/user-attachments/assets/7e3dd1f9-f211-40b2-ab3b-62682de259e8" />



**\*\*\*What questions do these sketches raise? What do you need to physically prototype to answer them?\*\*\***

These sketches raise similar questions about the placement of the sensors and actuators, and the size and weight of the moving parts. Moreover, we are not sure whether the servo motor is strong enough to perform each action reliably. We also need to consider how far the servo can rotate, where the electronics shouls be housed, and how the user will interact with them without interfering with the mechanism.
Hence, we would need to build some simple prototypes using lightweight materials, such as cardboard, tape and string. For example, for the Rotating Sushi Carousel idea, we would need a cross-shaped platform.

**\*\*\*Pick one design to prototype and explain why.\*\*\***

We pick the Rotating Sushi Carousel because it conbines a simple and intuitive interaction with a clear physical response. We also considered the limitation of the servo's movement (180 degree), making this the best and most realistic idea out of the five.  Last and most important, WE LOVE SUSHI!


Build a cardboard or other low-fidelity physical prototype of your design.

A demo video of our prototype can be seen in:
https://drive.google.com/file/d/107zFRFPnj3CcGJ7PWsL-9535d5mnNfVf/view?usp=sharing

For our low-fi prototype, we cut out a cardboard and used as the cross shape platform that turn every time user press the buttom. We cut out 4 paper circle as plate and used rice cake to mock the sushi.

<img width="1279" height="1706" alt="image" src="https://github.com/user-attachments/assets/b3ffa979-5529-48cc-97be-4132ceb3336f" />
<img width="3024" height="4032" alt="image" src="https://github.com/user-attachments/assets/e9ccc0cd-2dd9-4e79-9acf-858ed7acf3c5" />
<img width="4032" height="3024" alt="image" src="https://github.com/user-attachments/assets/4e28671e-f446-43af-bf40-ff6661156121" />




---

## Part 2

Following exploration and reflection from Part 1, complete the "looks like," "works like" and "acts like" prototypes for your design, reiterated below.

---

### Part E

#### Build & Integrate: Sensing + Actuation

For Part 2, build the Feast Automata interaction you developed in Part D by connecting sensing/input to physical actuation.

**Document your system with:**
- Code for your sensing + actuation prototype
- Photos and/or video of the working prototype in action
- A simple interaction diagram or sketch showing how sensing and actuation are connected
- Written reflection: What did you learn about connecting sensing, movement, and physical form? What was fun, surprising, or challenging?


Iterate on the sensing, movement, and physical form, and document what you discover.


For our final prototype, we built the Rotating Sushi Carousel using a laser-cut support structure for the servo motor and a laser-cut rotating platform for the food. We also 3D-printed some plates to simulate the real scenario. We used a button connected to the Raspberry Pi as the input, and the servo motor to provide the physical actuation by rotating the platform. 

Our first working version used two opposite serving positions, with the servo rotating 180° each time the button was pressed. This worked well with the 180° movement limitation of our servo, but during testing we realized that the interaction could be improved further. We therefore iterated on the platform design by adding an additional arm and reducing the servo movement to 90°. This allowed the carousel to serve two people sitting on opposite sides at the same time while still keeping the movement within the servo’s available range. We also adjusted the servo movement speed after noticing that sudden rotations caused the snacks to slide or fall from the plates. By slowing down the movement and adding higher edges to the 3D-printed plates, the final interaction became more stable and controlled. These iterations showed us how changes in software, mechanical structure, and physical form all influenced the final behavior of the device.

##### Reflection

In this project we learned that connecting sensing, movement, and physical form is not just about making each component work independently, but about making the whole interaction feel natural. In our design, the button sends a signal to the Raspberry Pi, which then controls the servo motor and rotates the sushi platform. The movement needed to be clear and predictable so the user could easily understand what was happening.

The physical arrangement also affected the interaction more than we expected. The servo had to be placed directly under the center of the platform so that the rotation would remain balanced, and the platform had to be light enough for the servo to move it reliably. We also found that the size and shape of the platform mattered, because a heavier or uneven structure could make the movement unstable.

The timing and amount of rotation were also important. Since our servo motor can only rotate about 180 degrees, it was difficult to achieve our initial idea of a continuous rotating sushi carousel (360 degree). So instead, we used this limitation as part of the design process. We first created a two-position system using 180° rotations, and later improved the design by adding another arm and using 90° movements. We also tested smaller movements, but they were less noticeable and made the interaction feel less clear. Fast rotations were more visually clear, but they also caused the snacks to fall from the platform.

The most fun part was seeing a simple button press create a visible physical action. The most challenging part was designing the mechanical structure around the limits of the servo, especially its range of motion. Overall, we learned that the electronics, motion, and physical form all need to be designed together rather than separately.

Here is a simple interaction diagram of how sensing and actuation are connected for our Rotating Sushi Carousel, along with the iterative process we followed to build the mechanical structure. We used TinkerCAD to design the .svg files for laser cutting:
<img width="3233" height="2327" alt="IMG_1231" src="https://github.com/user-attachments/assets/899e4c09-1bc5-47ea-8469-4b8453bce025" />
<img width="1024" height="752" alt="image" src="https://github.com/user-attachments/assets/e4165f69-d57a-4889-9a3a-8ad637152e14" />
<img width="1555" height="877" alt="image" src="https://github.com/user-attachments/assets/ce220a5d-0a07-427a-8817-50b75bfa185c" />
<img width="1280" height="1707" alt="image" src="https://github.com/user-attachments/assets/98d00746-6d8a-4288-b1fa-b66d78803555" />
<img width="930" height="1424" alt="image" src="https://github.com/user-attachments/assets/57336d0b-d4d4-4419-af2d-4aa4b51f7575" />


### Part F

### Final Documentation

- **Looks like**: The final prototype consists of a laser-cut support structure containing the servo motor, with a cross-shaped rotating platform mounted above it. The button is placed next to the device so the user can easily control the carousel. The structure is lightweight and compact so the servo can rotate the platform reliably.

- **Works like**: When the user presses the button, the Raspberry Pi detects the input and sends a command to the servo motor through the Servo pHAT. The servo rotates the platform 180 degrees, bringing the next sushi serving to the user.

- **Acts like**: The carousel acts like a small automated sushi server. The user presses the button when they want the next serving, and the platform immediately rotates to bring food toward them. The interaction is intentionally simple and playful, with one clear input producing one visible physical response.

A final demo of our product can be seen here:
<img width="1702" height="1276" alt="image" src="https://github.com/user-attachments/assets/f7935314-703b-4237-a71c-ca23c35975d8" />
https://drive.google.com/file/d/1a9rUbpS7RJNq2u2ESoLvqGxZuvJmz5cW/view?usp=sharing
---

## Deliverables \& Submission for Lab 4

The deliverables for this lab are, writings, sketches, photos, and videos that show what your prototype:
* "Looks like": shows how the device should look, feel, sit, weigh, etc.
* "Works like": shows what the device can do.
* "Acts like": shows how a person would interact with the device.

For submission, the readme.md page for this lab should be edited to include the work you have done:
* Upload any materials that explain what you did, into your lab 4 repository, and link them in your lab 4 readme.md.
* Link your Lab 4 readme.md in your main Interactive-Lab-Hub readme.md. 
* Labs are due on Mondays, make sure to submit your Lab 4 readme.md to Canvas.
