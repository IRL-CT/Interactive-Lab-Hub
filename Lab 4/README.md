# Ph-UI!!!


## Lab Overview
Team: Yangchen Jin
Members: Yangchen Jin (yj645; MortalJin)
Project name: Spice Box



### Part D
### Sketches

<img width="500" alt="785eecd0fec2e76d6a9b7d6ee31be587" src="https://github.com/user-attachments/assets/e94e6492-7aa8-445d-861a-6b7273b97c12" />

**Sketch 1: Front sensor.** A proximity sensor is on the front of the box. When my hand comes close, the servo opens the lid. After my hand leaves, it waits 2 seconds and closes the lid.

<img width="500" alt="dc8c3138b5d95f7654261a454da91ca9" src="https://github.com/user-attachments/assets/408fc931-9f19-4842-81c0-d21f9e7b617e" />

**Sketch 2: Touch handle.** A strip of foil on the side of the box is connected to the MPR121. Touching the foil opens the lid, and letting go closes it.

<img width="500" alt="6a5f3d1ccf963df8c4cba63b32346ff5" src="https://github.com/user-attachments/assets/bf36dcbb-232c-4ee7-8030-1bb63e847375" />

**Sketch 3: Gesture sensor on the lid.** The APDS-9960 sits on top of the lid. Swipe up to open, swipe down to close. But once the lid flips up, the sensor turns to face the back, so it may not see the swipe down anymore.

<img width="500" alt="aa31bbe0a64a079f7162b031daf2a65b" src="https://github.com/user-attachments/assets/72b95691-7421-4e33-8da4-0cbcd6c8e983" />

**Sketch 4: Bottle detection.** This one uses two sensors. The APDS-9960 on the front sees my hand and opens the lid. The distance sensor under the bottle checks if the bottle is there. The lid stays open while the bottle is out, and closes 2 seconds after I put it back.

<img width="500" alt="3f83067813633e9fabca09ba67fa0b6d" src="https://github.com/user-attachments/assets/e2a63afc-e253-4096-b502-012bdd1029d4" />

**Sketch 5: Sensor under the cabinet.** The sensor is under the cabinet above the box, facing down. When I reach in, the lid opens. There is no sensor on the box itself.

### Questions raised by the sketches

- How close should my hand be before the lid opens? Will walking past open it by mistake?
- What happens if my hand is still in the box when the lid closes?
- Is the 9g servo strong enough to lift the lid? How light does the lid need to be?
- Will oily or wet hands mess up the touch sensor? (Sketch 2)
- If the sensor is on the lid, does it still work after the lid opens? (Sketch 3)
- Will the bottle always sit right on top of the bottom sensor? (Sketch 4)
- Is there enough room under the cabinet for the lid to fully open? (Sketch 5)

To answer some of these, I need a physical prototype: a box with a hinged lid and a spot for the bottle, so I can check how big the lid is, how far it needs to open, and where the sensors and servo should go.

### Which idea I picked and why

I picked Sketch 4. The idea came from the minibar in Las Vegas hotels, where a sensor under each item knows when you pick it up. Here the box knows if the bottle is taken out or put back. That way, the lid only closes after the bottle is back, and it won't close on me while I'm still cooking.

One thing I noticed is that if the lid needs to cover the bottle, maybe what's inside isn't fully sealed, or it needs to stay cool. For example, oyster sauce should be kept cold after opening, so this could become a small cold box for sauces. A fridge might still be a better choice for that, so this is just one possibility. A real version could also have one sensor for each bottle, like the minibar.


**Rough Prototype**

<img width="450" alt="6bbd9262f954c50de276f29b88c22670" src="https://github.com/user-attachments/assets/59dc8d62-7587-4262-bc29-245404ca459a" />

<img width="450" alt="abff1b1c52eec03dab5c357977cc4b2c" src="https://github.com/user-attachments/assets/42f5317a-98c1-4f0a-90d9-ebf55b9cb7d0" />

<img width="450" alt="f5e101467a9abb4c5f6e2f427bc93194" src="https://github.com/user-attachments/assets/20d59337-00e8-4d42-9df9-244211e8702c" />

<img width="450" alt="59e253b3f339539b9b74bcb4a87ddfed" src="https://github.com/user-attachments/assets/3e3890e5-d799-4083-b8b0-500be610f8e5" />

<img width="450" alt="82254854bb33c1e640b3dfa5c69fa230" src="https://github.com/user-attachments/assets/24e2306f-99a0-4b02-bcd9-d7657dc552ee" />

---

## Part 2


### Part E: Build & Integrate

I built a spice box that opens when my hand comes close, and only closes after the bottle is put back.

- An APDS-9960 on the front checks if my hand is near (I use its proximity mode, so any hand movement works, not just a gesture).
- A distance sensor at the bottom checks if the bottle is in the box.
- When my hand comes close, the servo turns to 140°, and the lid swings open.
- If I take the bottle out, the lid stays open.
- When I put the bottle back, it waits 2 seconds and then closes.
- If I open it but don't take the bottle, it closes by itself after 5 seconds.

**Code:** [spice_box.py](spice_box.py)

**First Try Video+Explain:** [Watch Video](https://youtube.com/shorts/qpb1k_-dz_Y?feature=share)

**Interaction Video:** [Watch Video](https://github.com/user-attachments/assets/0735185e-f6b8-4f8e-b814-ae11b4d5b282)

**Interaction diagram:**
<img width="1360" height="820" alt="interaction_diagram" src="https://github.com/user-attachments/assets/e6d9bba0-2d84-40d0-8313-c7ef9ed0f252" />




### Changes I made along the way

- At first the lid could not open. The servo arm was too short, the servo body was an awkward shape to mount, and it didn't have enough force to lift a flip-up lid.
- So I changed the lid from flipping up to swinging open sideways. I cut the box open so the lid turns on its side edge, and once the servo was fixed in place it worked.
- I set the open angle to 140°. It looked neat and kind of high-tech.
- I didn't get false triggers from my hand. But sometimes when I put the bottle back, it wasn't detected because I didn't put it right in the middle over the sensor.

### Reflection

The hardest part was not the code, it was the physical form. The sensors and servo worked quickly, but getting the lid to actually move took the most time. The servo is small and weak, so the way the lid moves had to fit what the servo can do, not the other way around. Changing from a flip-up lid to a side-swinging lid fixed it.

I also learned that where the sensor sits changes how well it works. The bottle sensor only works if the bottle is right above it, so a real version would need a small ring or guide in the bottom so the bottle always lands in the same spot.

What was fun was seeing the lid stay open while the bottle was out and then close by itself when I put it back. It felt like the box "knew" what I was doing


### Part F

- **Looks like:**

<img width="450" alt="3c8c46435763540ccbfe8165109d0c3d" src="https://github.com/user-attachments/assets/874c3ff1-327a-4c17-becf-3506a3958225" />

- **Works like:** see the video above
- **Acts like:** see the video above, showing how a person reaches in, takes the bottle, and puts it back
- **Progress:**

<img width="500" alt="a4ce592899beaef82f13f5a322811794" src="https://github.com/user-attachments/assets/81b53b0a-494d-40b6-ac4c-0964eee7c67d" />

<img width="500" alt="8c173def6a15e97d1cd31f5337096de4" src="https://github.com/user-attachments/assets/5dbf2971-117c-439a-ad50-9618d49fc631" />




