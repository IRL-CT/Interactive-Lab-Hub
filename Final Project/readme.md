
# Final Project

[Project Plan](#project-plan) 

[Functioning Project](#functioning-project) 

[Documentation of Design Process](#documentation-of-design-process) 

[Archive of All Code and Design Patterns](#archive-of-all-code-and-design-patterns) 

[Video Demo](#video-demo) 

[Reflections on Process](#reflections-on-process) 

[Group Work Distribution](#group-work-distribution) 

## Project Plan
Huiying Zhan (hz764), Joy Sun (js3888), Hester Li (ql382)

### Big Idea
Inner Constellation is an interactive art installation that visualizes a person’s inner energy as a living constellation made of light, color, and motion. It invites people to reflect on their emotions through simple, intuitive interactions.

When a participant begins, they choose one of six symbolic elements — Fire 🔥, Water 💧, Wind ❄️, Earth 🌍, Light 💡, or Shadow 🧍‍♀️🧍‍♂️ — each representing a different emotional tone or personality energy. This choice is made by tapping an NFC card or selecting on screen. The system, powered by a Raspberry Pi, then generates a real-time animation that moves and transforms based on that element’s characteristics — for example, Fire glows and flickers, Water flows smoothly, Wind drifts and spins, Earth pulses steadily, Light radiates softly, and Shadow creates shifting patterns.

A computer screen displays the animation blended with a live camera feed of the user, allowing them to see both their reflection and their personalized constellation at the same time. As they move their hands or adjust their posture, gesture and touch sensors detect these actions and feed them back into the system. The constellation reacts instantly — expanding, contracting, or changing colors — as if breathing together with the user.

Through these visual and sensory responses, Inner Constellation transforms abstract emotions into tangible experiences. It connects technology and self-awareness in a poetic way, turning each participant’s reflection on the screen into a unique portrait of their energy and mood in that moment. 

### Picture: Initial Prototpye
<img src="prototype.png" alt="Inner Constellation concept image" width="800">

### Timeline
| **Milestone** | **Date** | **Notes / Details** |
|:--|:--:|:--|
| **Concept Lock & Story Development** | Nov 10–11 | Finalize core interaction and six energy elements. Write story concept and plan MVP scope. |
| **Visual MVP** | Nov 15 | Design an interactive energy circle that expands or contracts with hand gestures. |
| **Input Integration** | Nov 20 | Add gesture detection for circle control. Test responsiveness and stability. |
| **Projection Interaction** | Nov 22 | Project visualization on a large screen. Enable full-screen gesture control and adjust brightness. |
| **Parameter Tuning & Visual Polish** | Nov 25 | Refine color, motion, and gesture sensitivity. Add an “Energy Fortune” line and save-image feature. |
| **Functional Check-off** | Dec 1 | Demonstrate full flow: gesture → real-time motion → image save. Record performance notes. |
| **User Testing** | Dec 5 | Test with non-team users. Gather feedback on usability, aesthetics, and response. |
| **Final Presentation Prep** | Dec 6 | Prepare short demo video and slides. Present motivation, technical design, and evolution. |
| **Final Write-up & Repository Submission** | Dec 8 | Complete README, diagrams, and documentation. Upload final materials. |

### Parts Needed
**The Device**
- 1× Raspberry Pi 4 Board  
- 1× 32GB MicroSD Card w/ Card Reader  
- 1× Computer Display / Monitor  
- 1× USB Camera (for live reflection feed)  
- 1× NFC Reader + NFC Cards (for element selection)  
- 1× Gesture or Touch Sensor (e.g., APDS-9960 or Capacitive Pad)  
- 1× HDMI Cable  
- 1× USB Powered Speaker *(optional, for ambient sound)*  
- 1× Power Supply for Raspberry Pi (5V 3A recommended)  
- 1× Dupont Wire Set *(for sensor connections)*  

**For Exhibition Setup (optional)**
- 1× Projector *(for large-scale projection display)*  
- 1× Tripod or Mounting Stand  
- 1× External Light Diffuser or Frame *(for aesthetic setup)*

### Fallback Plan

If any hardware or sensor components fail, the system can still demonstrate the core experience through simplified input and display modes.

### Challenges & Fall Back Plans

| Category | Risk / Challenge | Mitigation |
|-----------|------------------|-------------|
| **Hardware** | Sensor or camera failure due to wiring or power issues. | Test components early; add keyboard/mouse fallback. |
| **Gesture Detection** | Inaccurate or unstable hand tracking under different lighting. | Calibrate thresholds; add on-screen feedback. |
| **Performance** | Rendering + live camera feed may overload Raspberry Pi. | Lower resolution / particle count; optimize code. |
| **Integration** | Combining gesture, NFC, and camera may cause conflicts. | Build modular code; integrate step-by-step. |
| **Lighting / Projection** | Bright rooms may wash out visuals. | Adjust brightness; use diffuser or darker backdrop. |
| **User Experience** | Users may not understand how to interact. | Add quick on-screen hints; ensure immediate feedback. |
| **Timeline** | Tight schedule for testing and polishing. | Lock MVP early; layer extra features gradually. |

*These fallback modes ensure the installation remains functional and visually expressive, even if some hardware components are unavailable.*

