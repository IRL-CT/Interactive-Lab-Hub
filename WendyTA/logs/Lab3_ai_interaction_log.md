# Lab 3 - AI Interaction Log

## [2026-10-02 00:00:00] - Session Entry
**AI Assistant**: GitHub Copilot Chat (WendyTA)

### Code Changes
- **Files Modified**: `WendyTA/logs/Lab3_ai_interaction_log.md` (interaction record only; no greeting scripts changed).
- **AI-Generated Code**: None.
- **Student Modifications**: None yet.

### Interaction Summary
- **Questions Asked**: How to test whether the Piper greeting scripts still work after a Raspberry Pi reset.
- **Answers Provided**: Identified that the English and Swahili wrappers use local ONNX voice models, the Piper Python package, and `aplay`; each generates/overwrites `greeting.wav` in the current directory and plays it. The user-requested system check was skipped, so no runtime test has been performed.
- **Learning Objectives**: Know the scripts' prerequisites and that testing them will synthesize speech and play it through the default audio output.

### Next Steps
- Activate the Lab 3 `.venv`, go to `Lab 3/speech-scripts`, and run `./piper_greet_en.sh` and `./piper_greet_sw.sh`; check for an existing `greeting.wav` first because each run overwrites it.
- Commit the AI interaction log with the lab work.

---

## [2026-10-02 08:55:05] - Session Entry
**AI Assistant**: GitHub Copilot Chat (WendyTA)

### Code Changes
- **Files Modified**: `Lab 3/README.md`, `WendyTA/logs/Lab3_ai_interaction_log.md`.
- **AI-Generated Code**: Embedded the existing oven storyboard and system diagram images under labeled README sections.
- **Student Modifications**: Requested that `oven_diagram.jpg` and `oven_scernio.jpg` be included in the README. The storyboard asset in the repository is named `oven_scernio .jpg` (contains a space), so its image link URL-encodes that space.

### Interaction Summary
- **Questions Asked**: Include the oven diagram and storyboard in the README.
- **Answers Provided**: Added Markdown image embeds and checked the updated README section.
- **Learning Objectives**: Present the oven interaction concept and storyboard alongside the lab documentation.

### Next Steps
- Review the rendered README images and commit the README and interaction log.

---

## [2026-10-02 08:51:30] - Session Entry
**AI Assistant**: GitHub Copilot Chat (WendyTA)

### Code Changes
- **Files Modified**: `Lab 3/README.md`, `WendyTA/logs/Lab3_ai_interaction_log.md`.
- **AI-Generated Code**: Expanded the prototype documentation with the display dependency install step and a clearer description of the animated loaf, countdown, and reminder. Clarified that the illustration is timer-driven, not a sensor view of actual food.
- **Student Modifications**: Requested that the screen-animation portion be included in the README.

### Interaction Summary
- **Questions Asked**: Document the food-growth display animation in the README.
- **Answers Provided**: Updated the prototype instructions and screen-animation explanation.
- **Learning Objectives**: Document how the spoken oven interaction and visual timer feedback work together.

### Next Steps
- Review the README wording and commit it together with the display implementation.

---

## [2026-10-02 08:49:48] - Session Entry
**AI Assistant**: GitHub Copilot Chat (WendyTA)

### Code Changes
- **Files Modified**: `Lab 3/speech-scripts/oven_bot.py`, `Lab 3/requirements.txt`, `Lab 3/README.md`, `WendyTA/logs/Lab3_ai_interaction_log.md`.
- **AI-Generated Code**: Added an ST7789/PiTFT display with an oven scene, a loaf illustration that grows and browns according to elapsed timer progress, an mm:ss countdown, and a completed/cancelled visual state. Added the display dependencies and documented setup/behavior.
- **Student Modifications**: Requested a food-growth animation on the Pi screen as the timer counts down.

### Interaction Summary
- **Questions Asked**: Add an animated food display tied to the oven timer.
- **Answers Provided**: Implemented the display drawing and connected it to timer start/progress/completion; syntax and timer-progress tests passed. The physical display could not be exercised in this environment.
- **Learning Objectives**: Connect software timer state to a visual feedback loop and use the Raspberry Pi's ST7789 display for a multimodal prototype.

### Next Steps
- On the Pi, install the updated Lab 3 requirements, then run `python speech-scripts/oven_bot.py` with the ST7789 display connected. If the display is unavailable or held by another service, test audio-only with `--no-screen` and resolve the GPIO/display conflict.
- Check whether the loaf growth and countdown are visible and revise the illustration based on feedback.
- Commit the script, requirements, README, and interaction log.

---

## [2026-10-02 08:44:31] - Session Entry
**AI Assistant**: GitHub Copilot Chat (WendyTA)

### Code Changes
- **Files Modified**: `Lab 3/README.md`, `WendyTA/logs/Lab3_ai_interaction_log.md`.
- **AI-Generated Code**: Replaced four Lab 3 Part 2 reflection placeholders with draft responses about system/controller strengths and limits, WoZ design lessons, and ethical interaction-data capture/sensors.
- **Student Modifications**: Review and revise the reflections to ensure they accurately represent actual participant testing.

### Interaction Summary
- **Questions Asked**: Complete the four Lab 3 system-testing reflection prompts.
- **Answers Provided**: Drafted responses based on the documented cornbread scenario, the student's WoZ reflection, the oven prototype's actual capabilities, and its known speech-recognition/turn-taking limitations. Avoided claiming that the required two-person test has been completed.
- **Learning Objectives**: Reflect on usability, conversational timing, limitations of autonomous speech interaction, and consent-aware multimodal data collection.

### Next Steps
- Review the draft and add actual observations after testing with at least two participants.
- Commit the updated README and interaction log.

---

## [2026-10-02 08:36:57] - Session Entry
**AI Assistant**: GitHub Copilot Chat (WendyTA)

### Code Changes
- **Files Modified**: `Lab 3/speech-scripts/oven_bot.py`, `WendyTA/logs/Lab3_ai_interaction_log.md`.
- **AI-Generated Code**: Slowed Piper speech using a longer synthesis length scale. Paused microphone capture while the assistant speaks, drained the short audio tail, and reset VAD so the assistant's own voice is not transcribed as the next user turn.
- **Student Modifications**: Reported that the oven assistant sounded too fast and repeated itself before the user spoke; suspected acoustic self-listening.

### Interaction Summary
- **Questions Asked**: Diagnose and fix fast, repeated responses in the voice oven prototype.
- **Answers Provided**: Explained that the input stream remained open during TTS playback and applied half-duplex turn-taking plus slower TTS. Syntax and basic dialogue checks passed in the Lab 3 virtual environment; hardware microphone/speaker behavior still needs testing.
- **Learning Objectives**: Understand how speaker audio can feed back through an always-open microphone and how pausing capture enforces clearer conversational turns.

### Next Steps
- Run `python speech-scripts/oven_bot.py` and test whether it waits quietly while speaking and whether the slower pace feels comfortable; adjust Piper's `length_scale` if needed.
- Commit the code and interaction log with the lab work.

---

## [2026-10-02 08:32:42] - Session Entry
**AI Assistant**: GitHub Copilot Chat (WendyTA)

### Code Changes
- **Files Modified**: `Lab 3/speech-scripts/oven_bot.py`, `WendyTA/logs/Lab3_ai_interaction_log.md`.
- **AI-Generated Code**: Added an offline, voice-driven oven helper using the Lab 3 microphone/VAD/Whisper/Piper pattern. It lists the saved recipes, reads the available cornbread ingredients and timing note, starts/checks/cancels timers, and announces timer completion. It does not control or sense the oven.
- **Student Modifications**: None yet.

### Interaction Summary
- **Questions Asked**: Create a Python script based on `echo_bot.py` and the oven dialogue template.
- **Answers Provided**: Inspected the Lab 3 speech examples and Cornbread Script scenario, implemented the assistant, and checked syntax plus the saved-recipe, cornbread timer, remaining-time, and timer-completion dialogue offline.
- **Learning Objectives**: See how the echo bot's speech pipeline connects to a dialogue policy, and how countdown state can support a multi-turn cooking interaction.

### Next Steps
- Activate the Lab 3 `.venv` and run `python speech-scripts/oven_bot.py` to test with the Pi microphone and speaker.
- Follow the recipe/package for oven temperature and check doneness directly; this prototype is a reminder, not an oven controller or food-safety sensor.
- Commit the script and interaction log with the lab work.

---