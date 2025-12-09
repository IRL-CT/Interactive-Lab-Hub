<!-- Put all of this information on your project Github, and submit the link to the Github.

1. Project plan: Big idea, timeline, parts needed, fall-back plan. (Can be same as previous turn-in, but updated if you changed your plan)

2. Functioning project: The finished project should be a device, system, interface, etc. that people can interact with.

3. Documentation of design process

4. Archive of all code, design patterns, etc. used in the final design. (As with labs, the standard should be that the documentation would allow you to recreate your project if you woke up with amnesia.)

5. Video of someone using your project -->

# Project Plan: 

## Big Idea: 
A soothing plushie that replaces harmful stims (e.g., head banging) with comforting light, sound, and touch feedback to support emotional regulation.
- Input: When/where/how the user touches the plush
- Output: Soothing lights pattern, haptic feedback, and/or voice  
We will test and update the input/output based on the user feedbacks

## Materials we need
- Raspberry Pi 5
- Woven Conductive Fabric - 20cm square
- Stainless Thin Conductive Thread - 2 ply - 23 meter/76 ft
- Adafruit DRV2605L Haptic Motor Controller - STEMMA QT / Qwiic
- Vibrating Mini Motor Disc
- 1N4001 power diode or a level converter chip 74AHCT125 (USB microphone & Mini speaker (Logitech))

## Testing  plan
- Functional Testing 
    - Haptic Response
    - LED lightin
    - Microphone Input & Response 
- Usability Testing with two people
    - Ease-of-use
    - Feedback preference
    - Emotional Effectiveness

## Fallback Plan
For all types of feedback, we can conduct a Wizard-of-Oz study to control when and how the feedback is delivered. For example, for haptic feedback, the wizard can manually trigger the vibration when the user touches the plushie
Choose 1 type of feedback to focus on
- haptics fail - add small manual massager
- color change problems- use  reversible sequin fabric
- audio issues - hard code some soothing phrases for responses


# Functioning project

**MewoPow**

A soothing smart plushie that provides comforting light, sound, and haptic feedback to support emotional regulation.

<img src="img/final_pic.jpg" width=200>

[Demo video](https://drive.google.com/file/d/1ILqqUDU1AAwQOzUwiy2DEs0eBlaDfm7g/view?usp=drive_link)

- **LED lights** – Calming light patterns
- **Haptic feedback** – Gentle vibrations
- **Audio responses** – Meows and purring sounds

### Interaction Design

| Interaction | Location | Detection | Response |
|-------------|----------|-----------|----------|
| **Petting** | Head (conductive fabric) | Capacitive touch sensor | 8-sec purring mode: looping purr sound + slow pastel color transitions (purple → lavender → pink → peach) + gentle vibration |
| **Patting** | Back (conductive fabric) | Capacitive touch sensor | 7-sec purring mode: meow sound + orange flash + pastel color transitions + gentle vibration |
| **Quick Tap** | Body (pressure sensor) | Press < 0.3 sec | Short meow + sparkle LED effect + burst vibration |
| **Squeeze** | Body (pressure sensor) | Press 0.3–1 sec | Meow + yellow chase LED pattern + vibration |
| **Long Hug** | Body (pressure sensor) | Press > 1 sec | Toggles **breathing mode** (4-7-8 pattern): blue↔white LEDs + rhythmic vibration to guide calm breathing |

#### Breathing Mode (4-7-8 Pattern)

When activated by a long hug, the plushie guides the user through a calming breathing exercise:

- **Inhale (4 counts):** LEDs gradually brighten, vibration increases
- **Hold (7 counts):** Full brightness with gentle pulse
- **Exhale (8 counts):** LEDs slowly dim, vibration decreases

# Documentatoin of Process

## 0. Our first ideation 

We created storyboards envisioning how users would interact with the plushie at home—hugging, petting, or simply looking at it for comfort.

<img src="img/storyboard.jpg" width=300>

We explored different areas to incorporate lighting: belly, clothing, tail, and cheeks.

<img src="img/design.jpg" width=300>

## 1. Test with Haptic Motor and Touch System 

We tested haptic motors and touch sensors. 

### Haptic Motor 

We tested the vibration motor using the [haptic test script](test/test_inhale.py), initially with the Adafruit DRV2605L haptic motor controller.

[Test Haptic Motor](https://drive.google.com/file/d/1jeg4uBKiy9n-tyOyDO9NiWyAg44exAlF/view?usp=drive_link)

### Conductive Fabric + Capacitive Sensor 

We created a simple prototype plushie with conductive fabric on top, connected via conductive thread to a capacitive touch sensor.

<img src="img/initial_pic.jpg" width="300">

[Touch sensor test code](test/touch-sensor-test.py)

[Test Touch Sensor](https://drive.google.com/file/d/1ToM1HJ9TXLMcaa0mjYVwpd-h35VXzcin/view?usp=drive_link)

## 2. Ask for Feedback on our First Plushy 

As we finished prototyping the intial version of the plushy, we asked 2 Cornell Tech students, Nana's sister, and her husband to give us the feedback on the size and sensors we were thinking to use. 

Some intial feedbacks we got:
- They liked the haptic motor but they thoght it was too strong and not very steady
- They liked the size of the plushy but could be bigger but not smaller. It's a good size to hug 
- One of them wants a bit more heavy. It's too light
- Everyone thought it's a bit too little of the inteactoin that there is no sound or other things to give us feedback. They want a bit more inteaction. 

## 3. Add Additional Inputs + Outputs

Given the feedback, we decided to add more sensros as well as output forms. 

### Pressure Sensor

We tested with the [pressure sensor test code](test/pressure-test2.py).

[Test Pressure Sensor](https://drive.google.com/file/d/1hq4O5mBmDS_iIKmoONX1ANE9k0dyZU5d/view?usp=drive_link)

### Led Ring 

We tested with the [led ring](test/led_test.py)
For LED, we learned to run the led ring, it has to be connected with GPIO12. 

### Speaker 

For speaker, we just tested with 
```bash 
aplay lookdave/wav
```

## 4. Test with All Sensors at the Same Time

After each of them is working successfully seaparetely, we tested with multiple sensors at the same time. 

At this time, we encountered the issues.

Firstly, we encountered the issue of hapric motor controller not compatiblly working with teh capacitive sensor. 
Since both haptic motor controller and capacitive sensor use i2c, when we tried to run both at the same time, we got error of 0x5A not found. 

To encounter this issue, we decided not to use the haptic motor controller but  connects haptic motor with rasberry pi through the breadboard. 

Also, we tried to use the Qwiic SHIM; however, althoug we solder them together, the soldering was very difficult given the small region to solder, we ended up not suing the Qwiic. 

[Test All Sensors](https://drive.google.com/file/d/1V0iHdGeFqw7xdqrPQZ9Vq-6pxtXVIfxY/view?usp=drive_link)

## 5. Make the Outer Look

We increased the overall size to accommodate components and improve comfort based on user feedback.

<img src="img/final_pic.jpg" width=300>

## 6. Final Code for Interaction 

[Final Code](master.py)


There are two main modes for this code. 

**Breathing Mode**
Activated by a long hug (>1 second press). Implements the 4-7-8 breathing technique used in anxiety management:
- LEDs transition from blue to white following the breath cycle
- Vibration intensity syncs with the breathing pattern
- Stays active until another long hug toggles it off

**Purring Mode**
Activated by touching the conductive fabric (head or back). Runs for a set duration (7-8 seconds):
- LEDs slowly cycle through calming pastel colors (purple → lavender → pink → peach)
- Vibration oscillates to mimic a cat's purr
- Looping audio plays until the timer ends

```mermaid
flowchart TD
    subgraph Inputs["👆 INPUTS"]
        HEAD["🐱 Head Touch(Conductive Fabric)"]
        BACK["🐱 Back Touch(Conductive Fabric)"]
        PRESSURE["💪 Pressure Sensor(Body)"]
    end

    subgraph Detection["⚙️ DETECTION"]
        CAP["Capacitive TouchSensor (MPR121)"]
        FSR["Force SensitiveResistor"]
    end

    subgraph Processing["🧠 PROCESSING (Raspberry Pi)"]
        TOUCH_LOGIC["Touch Logic"]
        PRESSURE_LOGIC["Pressure Logic"]
        
        subgraph Modes["Active Modes"]
            PURR_MODE["😺 Purring Mode(7-8 sec timer)"]
            BREATH_MODE["🌬️ Breathing Mode(4-7-8 pattern)"]
        end
    end

    subgraph Outputs["✨ OUTPUTS"]
        LED["💡 LED Ring(24 NeoPixels)"]
        MOTOR["📳 Vibration Motor"]
        SPEAKER["🔊 Speaker"]
    end

    HEAD --> CAP
    BACK --> CAP
    PRESSURE --> FSR
    
    CAP --> TOUCH_LOGIC
    FSR --> PRESSURE_LOGIC
    
    TOUCH_LOGIC --> PURR_MODE
    PRESSURE_LOGIC -->|"> 1 sec"| BREATH_MODE
    PRESSURE_LOGIC -->|"< 1 sec"| LED
    PRESSURE_LOGIC -->|"< 1 sec"| MOTOR
    PRESSURE_LOGIC -->|"< 1 sec"| SPEAKER
    
    PURR_MODE --> LED
    PURR_MODE --> MOTOR
    PURR_MODE --> SPEAKER
    
    BREATH_MODE --> LED
    BREATH_MODE --> MOTOR

    style HEAD fill:#FFB6C1,stroke:#FF69B4
    style BACK fill:#FFB6C1,stroke:#FF69B4
    style PRESSURE fill:#87CEEB,stroke:#4169E1
    style PURR_MODE fill:#DDA0DD,stroke:#9932CC
    style BREATH_MODE fill:#98FB98,stroke:#228B22
    style LED fill:#FFD700,stroke:#FFA500
    style MOTOR fill:#FFA07A,stroke:#FF6347
    style SPEAKER fill:#87CEFA,stroke:#1E90FF
```

#### Pressure Detection Flow

```mermaid
flowchart LR
    PRESS["Press Detected"] --> DURATION{"Duration?"}
    
    DURATION -->|"< 0.3s"| TAP["⚡ TAP"]
    DURATION -->|"0.3s - 1s"| SQUEEZE["🤏 SQUEEZE"]
    DURATION -->|"> 1s"| HUG["🤗 HUG"]
    
    TAP --> TAP_OUT["Sparkle LEDs+ Burst Vibration+ Short Meow"]
    SQUEEZE --> SQUEEZE_OUT["Chase LEDs+ Vibration+ Meow"]
    HUG --> HUG_OUT["Toggle BreathingMode (4-7-8)"]
    
    style TAP fill:#FFD700,stroke:#FFA500
    style SQUEEZE fill:#FFA500,stroke:#FF8C00
    style HUG fill:#FF6347,stroke:#DC143C
```

## Some feedbacks from Demo Day 


# Final Code/Setup 

## Code 

### How to run
```bash
source .venv/bin/activate
pip install -r requirements.txt
python master.py
```

If the code does not work or give an error, please try to run below: 

```bash 
cd test

# Test led 
python led_test.py 

# Test speaker 
aplay lookdave.wav 

#Test pressure sensor 
python pressure-test2.py 

#Test haptic motor 
python test_inhale.py 

#Test capactive sensor
python touch-sensor-test.py

#if this does not work, then ru 
sudo i2cdetect -y 1

#This should show 0x5A. If this does not print 0x5A, double check the hardware setup. 
```

## Hardware

### Hardware We used 

| Component | Purpose |
|-----------|---------|
| Raspberry Pi 5 | Main controller |
| Woven Conductive Fabric (20cm²) | Touch-sensitive surface |
| Stainless Conductive Thread (2-ply, 23m) | Connecting fabric to sensors |
| MPR121 Capacitive Touch Sensor | Detecting light touch/petting |
| Pressure Sensor | Detecting hugs/squeezes |
| Vibrating Mini Motor Disc | Haptic feedback |
| NeoPixel LED Ring | Visual feedback |
| Mini Speaker | Audio output (meows, purring) |
| 1N4001 Power Diode | Circuit protection |

### How to set 
<img src="img/1.jpg" width=400>
<img src="img/2.jpg" width=400>
<img src="img/3.jpg" width=400>
<img src="img/4.jpg" width=400>
<img src="img/5.jpg" width=400>



# Video