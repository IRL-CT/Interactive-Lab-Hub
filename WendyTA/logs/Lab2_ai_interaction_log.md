# Lab 2 - AI Interaction Log

## [2026-09-13 17:50:00] - Session Entry
**AI Assistant**: GitHub Copilot Chat (WendyTA)

### Code Changes
- **Files Modified**: `Lab 2/screen_clock.py`
- **AI-Generated Code**: Filled in the Part D TODO in the main while loop — clears the display each frame and draws the current date/time (via `time.strftime("%m/%d/%Y %H:%M:%S")`) using the existing `draw`/`font` objects, following the pattern from `cli_clock.py` (time formatting) and `stats.py` (drawing text to the display).
- **Student Modifications**: Ran the script on hardware to verify the clock renders correctly.

### Interaction Summary
- **Questions Asked**: How to implement the Part D clock display; how to fix `ModuleNotFoundError: No module named 'digitalio'`; how to fix `lgpio.error: 'GPIO busy'`; how to push code to personal GitHub fork.
- **Answers Provided**: Implemented the clock-drawing loop; identified the venv was not activated as the cause of the missing `digitalio` module; identified `piscreen.service` was holding the display's GPIO pins and stopped/disabled the service; provided `git add`/`commit`/`push` steps for the existing `origin` remote (personal fork) on the `Fall2026` branch.
- **Learning Outcomes**: Understands how the ST7789 display draw loop works, how Python virtual environments isolate dependencies, how systemd services can conflict with GPIO hardware access, and the git workflow for submitting lab work to a personal fork.

### Next Steps
- Complete Part E (brainstorm/sketch further clock interactions).
- Continue into Lab 2 Part 2 (modify the barebones clock).

---
