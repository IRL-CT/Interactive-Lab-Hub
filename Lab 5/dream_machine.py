
import argparse
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import qwiic_button
from dream_display import DreamDisplay

# Configuration
BASE_DIR = Path(__file__).resolve().parent

PHOTO_DIR = BASE_DIR / "dream_photos"
LOG_FILE = BASE_DIR / "dream_log.jsonl"
STORY_FILE = BASE_DIR / "dream_story.txt"
AUDIO_FILE = BASE_DIR / "dream.wav"
STATE_FILE = BASE_DIR / "dream_state.json"

OVERNIGHT_SCRIPT = BASE_DIR / "dream_overnight.py"
MORNING_SCRIPT = BASE_DIR / "dream_morning.py"

VALID_PHOTOS = {".jpg", ".jpeg", ".png"}


def save_state(state):
    """Save the current state so it survives a restart."""
    STATE_FILE.write_text(
        json.dumps({
            "state": state,
            "updated_at": datetime.now().isoformat()
        }, indent=2),
        encoding="utf-8"
    )


def load_state():
    """Load the previous state."""
    if not STATE_FILE.exists():
        return "READY"

    try:
        data = json.loads(
            STATE_FILE.read_text(encoding="utf-8")
        )
        return data.get("state", "READY")
    except (json.JSONDecodeError, OSError):
        return "ERROR"


def show(message):
    print(f"[Dream Machine] {message}", flush=True)


def count_photos():
    if not PHOTO_DIR.exists():
        return 0

    return sum(
        1 for p in PHOTO_DIR.iterdir()
        if p.is_file()
        and p.suffix.lower() in VALID_PHOTOS
    )


def update_screen(screen, state):
    """Show visual feedback on the Mini PiTFT."""

    screens = {
        "READY": (
            "Dream Machine",
            "Press to start",
            "moon"
        ),
        "PROCESSING": (
            "Dreaming...",
            "Analyzing photos",
            "scan"
        ),
        "GENERATING": (
            "Creating Dream",
            "Qwen + Piper",
            "magic"
        ),
        "DREAM_READY": (
            "Good Morning!",
            "Your dream is ready\nPress to listen",
            "sun"
        ),
        "PLAYING": (
            "Your Dream",
            "Playing narration",
            "speaker"
        ),
        "FINISHED": (
            "Dream Finished",
            "Press to replay",
            "check"
        ),
        "ERROR": (
            "Error",
            "Check terminal\nand reset",
            "error"
        )
    }

    title, message, icon = screens.get(
        state, screens["ERROR"]
    )

    screen.show(title, message, icon=icon)


def set_state(screen, state):
    """Update the saved state and display."""
    save_state(state)
    update_screen(screen, state)
    show(f"State: {state}")
    return state


def launch(command):
    """Launch a script without blocking the controller."""
    return subprocess.Popen(
        command,
        cwd=BASE_DIR
    )


def start_processing():
    """Start analyzing the uploaded photos."""

    count = count_photos()

    if count == 0:
        show("No photos found in dream_photos/")
        return None

    if not OVERNIGHT_SCRIPT.exists():
        show("dream_overnight.py not found.")
        return None

    # Remove previous results to start a new session
    for path in (LOG_FILE, STORY_FILE, AUDIO_FILE):
        if path.exists():
            path.unlink()

    show("Good night! I'll dream about your day.")
    show(f"Processing {count} photos...")

    try:
        return launch([
            sys.executable,
            str(OVERNIGHT_SCRIPT)
        ])
    except OSError as exc:
        show(f"Could not start YOLO: {exc}")
        return None


def start_generation():
    """Generate the dream and audio without playing them."""

    show("YOLO finished. Generating your dream...")

    try:
        return launch([
            sys.executable,
            str(MORNING_SCRIPT),
            "--no-play"
        ])
    except OSError as exc:
        show(f"Could not start Qwen/Piper: {exc}")
        return None


def start_playback():
    """Play the saved dream without calling Qwen."""

    if not AUDIO_FILE.exists():
        show("Dream audio not found.")
        return None

    show("Good morning! Playing your dream...")

    try:
        return launch([
            "aplay",
            str(AUDIO_FILE)
        ])
    except OSError as exc:
        show(f"Audio playback error: {exc}")
        return None


def main():
    parser = argparse.ArgumentParser(
        description="AI Dream Machine controller."
    )

    parser.add_argument(
        "--reset",
        action="store_true",
        help="Prepare the device for a new night."
    )

    args = parser.parse_args()

    if args.reset:
        save_state("READY")
        show("Reset complete. Ready for a new night.")
        return

    # Initialize the Mini PiTFT
    screen = DreamDisplay()

    # Initialize Qwiic button
    button = qwiic_button.QwiicButton()

    if not button.begin():
        sys.exit(
            "Qwiic Button not found. Check I2C connection."
        )

    state = load_state()
    process = None

    # Recover completed sessions; reject interrupted ones
    if state in ("PROCESSING", "GENERATING", "PLAYING",
                 "REVEALING"):
        show("Previous session was interrupted.")
        state = set_state(screen, "ERROR")

    elif state in ("DREAM_READY", "FINISHED"):
        if not (
            STORY_FILE.exists()
            and STORY_FILE.stat().st_size > 0
            and AUDIO_FILE.exists()
            and AUDIO_FILE.stat().st_size > 0
        ):
            state = set_state(screen, "ERROR")

    update_screen(screen, state)

    show("AI Dream Machine started.")
    show(f"Current state: {state}")

    if state == "READY":
        show("Press button to start dreaming.")
    elif state == "DREAM_READY":
        show("Press button to hear your dream.")
    elif state == "FINISHED":
        show("Press button to replay your dream.")

    last_pressed = button.is_button_pressed()
    last_action = 0.0

    try:
        while True:

            # ---------------------------------
            # 1. Check background process
            # ---------------------------------
            if process is not None:
                result = process.poll()

                if result is not None:
                    process = None

                    if state == "PROCESSING":
                        if (
                            result == 0
                            and LOG_FILE.exists()
                            and LOG_FILE.stat().st_size > 0
                        ):
                            # Automatically start Qwen + Piper
                            state = set_state(
                                screen, "GENERATING"
                            )

                            process = start_generation()

                            if process is None:
                                state = set_state(
                                    screen, "ERROR"
                                )

                        else:
                            show("YOLO processing failed.")
                            state = set_state(
                                screen, "ERROR"
                            )

                    elif state == "GENERATING":
                        if (
                            result == 0
                            and STORY_FILE.exists()
                            and STORY_FILE.stat().st_size > 0
                            and AUDIO_FILE.exists()
                            and AUDIO_FILE.stat().st_size > 0
                        ):
                            show("Dream is ready for the morning!")
                            state = set_state(
                                screen, "DREAM_READY"
                            )

                        else:
                            show("Dream generation failed.")
                            state = set_state(
                                screen, "ERROR"
                            )

                    elif state == "PLAYING":
                        if result == 0:
                            show("Dream narration finished.")
                            state = set_state(
                                screen, "FINISHED"
                            )
                        else:
                            show("Audio playback failed.")
                            state = set_state(
                                screen, "ERROR"
                            )

            # ---------------------------------
            # 2. Read physical button
            # ---------------------------------
            pressed = button.is_button_pressed()
            now = time.monotonic()

            # React to a new press only
            if (
                pressed
                and not last_pressed
                and now - last_action > 0.3
            ):
                last_action = now

                if state == "READY":
                    process = start_processing()

                    if process is not None:
                        state = set_state(
                            screen, "PROCESSING"
                        )

                elif state == "PROCESSING":
                    show("Still analyzing photos...")

                elif state == "GENERATING":
                    show("Still generating your dream...")

                elif state in ("DREAM_READY", "FINISHED"):
                    process = start_playback()

                    if process is not None:
                        state = set_state(
                            screen, "PLAYING"
                        )
                    else:
                        state = set_state(
                            screen, "ERROR"
                        )

                elif state == "PLAYING":
                    show("Dream is currently playing.")

                elif state == "ERROR":
                    show("Run with --reset to try again.")

            last_pressed = pressed
            time.sleep(0.05)

    except KeyboardInterrupt:
        show("Controller stopped.")

        if process is not None and process.poll() is None:
            process.terminate()

            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


if __name__ == "__main__":
    main()
