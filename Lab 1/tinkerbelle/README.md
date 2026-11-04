# Tinkerbelle

Tinkerbelle is a multi-device interaction prototype where phones act as synchronized fireflies. The server keeps shared simulation parameters, and each connected device can take on a role such as controller, male firefly, female firefly, or idle device. As phones flash and listen to each other, their rhythms adapt over time through phase coupling and period matching.

## What changed in this version

This version moves beyond the original color-picker demo and adds:

- multi-phone synchronization between connected devices
- male/female firefly roles with delayed female responses
- a shared controller panel for tuning coupling, rhythm, delay, and flash behavior
- pause/resume, scatter, and force-sync controls
- decorative forest and label options
- a retained classic control panel for older color/audio interactions

## Installation

This project uses Flask and Flask-SocketIO.

Make sure you have Python 3 installed, then create a virtual environment if you want a clean setup:

```bash
cd "Lab 1/tinkerbelle"
python3 -m venv .venv
source .venv/bin/activate   # on Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

If you hit dependency issues, you can also install the required packages directly:

```bash
pip install Flask Flask-SocketIO
```

## Getting started

Start the server:

```bash
python3 tinker.py
```

You should see output similar to:

```text
access at http://<your-local-ip>:5001
```

Then open that URL on the devices that should act as fireflies.

## Using the app

### On a phone or browser

1. Connect all devices to the same Wi-Fi network.
2. Open `http://<your-laptop-ip>:5001` in each browser.
3. Choose a role from the controls:
   - Jane Wren (controller)
   - Male Firefly
   - Female Firefly
4. Keep the screen awake and brightness high so the flash behavior remains visible.

The controller can adjust phase coupling, rhythm adaptation, flash duration, sound, labels, and the title card that is pushed to all firefly screens.

### Controller behavior

When a device takes the controller role, it can:

- pause or resume the full system
- scatter rhythms apart to reset the pattern
- force a manual sync
- flash all devices at once
- toggle sound, forest background, and labels
- tune the shared firefly parameters in real time

## Notes on the simulation

The app is designed to create emergent synchrony rather than force it instantly. The system uses:

- phase coupling to nudge nearby flashes together
- period adaptation so different fireflies gradually converge in timing
- a response delay for female fireflies to imitate a biological rhythm

This makes the interaction feel more like a live collective behavior than a static lighting demo.

## Classic controls

The original Tinkerbelle color-and-audio tools remain available in the collapsible "Classic Tinkerbelle" section. This includes the color picker and the free-sound audio input for quick experiments and older demonstrations.

## Troubleshooting

If you see `ModuleNotFoundError: No module named 'flask_socketio'`, run:

```bash
pip install flask-socketio
```

If the page does not connect across devices, confirm that:

- all phones are on the same Wi-Fi network
- the server is still running
- the laptop firewall is not blocking the local port
- the phone is using the laptop's local network IP rather than a remote address

## Summary

This project is best understood as a live group interaction prototype: each browser becomes a participant in a shared rhythmic system. It is still useful as a light-control experiment, but the main behavior now is the synchronization of multiple devices in space and time.
