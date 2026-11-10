# Lab 4 - AI Interaction Log

## [2026-10-07 18:44:22] - Session Entry
**AI Assistant**: GitHub Copilot Chat (WendyTA)

### Code Changes
- **Files Modified**: `WendyTA/logs/Lab4_ai_interaction_log.md` (interaction record only; no sensor code changed).
- **AI-Generated Code**: None.
- **Student Modifications**: None yet.

### Interaction Summary
- **Questions Asked**: Shared a traceback from `cap_test.py` where the Adafruit MPR121 could not be found at I2C address `0x5a` (`OSError: [Errno 121] Remote I/O error`).
- **Answers Provided**: Explained that the Pi's I2C requests received no acknowledgment from a device at the expected address. Recommended scanning the bus first, checking the sensor's power/connection and I2C enablement, then checking alternate MPR121 addresses or reducing I2C baud rate if scan results suggest communication instability. Interpreted `blinkatest.py` as confirming Blinka's general GPIO/I2C/SPI setup, then ran the I2C scanner using the Lab 4 virtual environment; it reported no devices (`[]`). After the student confirmed the sensor was plugged in, clarified that the empty scan means no I2C device is electrically responding and recommended checking power and reseating/testing the cable and port.
- **Learning Objectives**: Use an I2C scan to separate wiring/address discovery problems from sensor-library or touch-reading problems.

### Next Steps
- Check MPR121 power and Qwiic cable/port connections, then scan again; the latest scan found no I2C devices.
- Commit this interaction log with the lab work.

---
