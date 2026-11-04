import json
import signal
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import board
import digitalio as pi_digitalio
import qwiic_button

from PIL import Image, ImageDraw, ImageFont
from adafruit_rgb_display import st7789
from adafruit_seesaw import seesaw, rotaryio
from adafruit_seesaw import digitalio as seesaw_digitalio
from faster_whisper import WhisperModel

from echo_bot import Speaker, DEFAULT_VOICE
from wizard_controller import transcribe_audio, choose_question


try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass


# ---------- Session settings ----------

OPTIONS = ["TOMORROW", "ONE MONTH", "ONE YEAR"]

WAKE_LINE = (
    "Sator Square is awake. "
    "Choose when this message should return: tomorrow, one month, or one year. "
    "Turn the dial, then press it to confirm."
)

SELECTION_LINES = {
    "TOMORROW": (
        "Tomorrow selected. "
        "Hold the green button and tell me about a decision you keep avoiding. "
        "Release the button when you are finished."
    ),
    "ONE MONTH": (
        "One month selected. "
        "Hold the green button and tell me about a decision you keep avoiding. "
        "Release the button when you are finished."
    ),
    "ONE YEAR": (
        "One year selected. "
        "Hold the green button and tell me about a decision you keep avoiding. "
        "Release the button when you are finished."
    ),
}

DECISION_RECEIVED_LINE = (
    "Your words have been received. "
    "I am opening a channel to your future self."
)

CONNECTED_LINE = "Future self connected."

ANSWER_READY_LINE = (
    "Hold the green button when you are ready to answer. "
    "Release the button when you are finished."
)

CLOSING_LINES = {
    "TOMORROW": (
        "Your answer has been sealed inside Sator Square. "
        "The channel will reopen tomorrow. "
        "You will hear your own voice and be asked what has changed. "
        "Connection closed."
    ),
    "ONE MONTH": (
        "Your answer has been sealed inside Sator Square. "
        "The channel will reopen in one month. "
        "You will hear your own voice and be asked what has changed. "
        "Connection closed."
    ),
    "ONE YEAR": (
        "Your answer has been sealed inside Sator Square. "
        "The channel will reopen in one year. "
        "You will hear your own voice and be asked what has changed. "
        "Connection closed."
    ),
}

session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
session_dir = Path("sessions") / session_id
session_dir.mkdir(parents=True, exist_ok=True)

decision_file = session_dir / "decision.wav"
reflection_file = session_dir / "reflection.wav"
session_file = session_dir / "session.json"


# ---------- Colors ----------

BLACK = (3, 3, 3)
AMBER = (225, 151, 45)
DIM_AMBER = (105, 69, 23)


# ---------- Screen setup ----------

cs_pin = pi_digitalio.DigitalInOut(board.D5)
dc_pin = pi_digitalio.DigitalInOut(board.D25)
reset_pin = pi_digitalio.DigitalInOut(board.D24)

spi = board.SPI()

display = st7789.ST7789(
    spi,
    cs=cs_pin,
    dc=dc_pin,
    rst=reset_pin,
    baudrate=24000000,
    width=135,
    height=240,
    x_offset=53,
    y_offset=40,
)

backlight = pi_digitalio.DigitalInOut(board.D22)
backlight.switch_to_output()
backlight.value = True

WIDTH = display.width
HEIGHT = display.height

image = Image.new("RGB", (WIDTH, HEIGHT))
draw = ImageDraw.Draw(image)

FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
BOLD_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"


def load_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()


large_font = load_font(BOLD_PATH, 20)
medium_font = load_font(BOLD_PATH, 13)
small_font = load_font(FONT_PATH, 9)


def centered_text(text, y, font, color):
    box = draw.textbbox((0, 0), text, font=font)
    text_width = box[2] - box[0]
    x = (WIDTH - text_width) // 2
    draw.text((x, y), text, font=font, fill=color)


def frame():
    draw.rectangle((0, 0, WIDTH, HEIGHT), fill=BLACK)
    draw.rectangle(
        (3, 3, WIDTH - 4, HEIGHT - 4),
        outline=AMBER,
        width=2,
    )
    centered_text("SATOR SQUARE", 13, small_font, AMBER)
    draw.line((15, 34, WIDTH - 16, 34), fill=DIM_AMBER)


def send_to_screen():
    display.image(image)


def show_initializing():
    frame()
    centered_text("INITIALIZING", 91, medium_font, AMBER)
    centered_text("TEMPORAL", 119, medium_font, AMBER)
    centered_text("CHANNEL", 140, medium_font, AMBER)
    send_to_screen()


def show_intro():
    frame()
    centered_text("A DECISION", 62, medium_font, AMBER)
    centered_text("YOU KEEP", 88, large_font, AMBER)
    centered_text("AVOIDING?", 116, large_font, AMBER)
    centered_text("TURN KNOB", 181, medium_font, AMBER)
    centered_text("TO AWAKEN", 202, small_font, DIM_AMBER)
    send_to_screen()


def show_menu(selected):
    frame()
    centered_text("SELECT RETURN", 45, medium_font, AMBER)
    centered_text("POINT", 62, medium_font, AMBER)

    option_y = [94, 132, 170]

    for index, option in enumerate(OPTIONS):
        y = option_y[index]

        if index == selected:
            draw.rectangle(
                (12, y - 5, WIDTH - 13, y + 24),
                fill=AMBER,
            )
            centered_text(option, y + 1, medium_font, BLACK)
        else:
            draw.rectangle(
                (12, y - 5, WIDTH - 13, y + 24),
                outline=DIM_AMBER,
                width=1,
            )
            centered_text(option, y + 1, medium_font, AMBER)

    centered_text("TURN / PRESS", 215, small_font, DIM_AMBER)
    send_to_screen()


def show_decision_ready(selected):
    frame()
    centered_text("RETURN POINT", 47, small_font, DIM_AMBER)

    draw.rectangle(
        (12, 65, WIDTH - 13, 96),
        outline=AMBER,
        width=2,
    )
    centered_text(OPTIONS[selected], 74, medium_font, AMBER)

    centered_text("TELL ME ABOUT", 116, small_font, AMBER)
    centered_text("THE DECISION", 132, medium_font, AMBER)
    centered_text("HOLD GREEN", 169, medium_font, AMBER)
    centered_text("BUTTON TO SPEAK", 190, small_font, AMBER)
    centered_text("KNOB: BACK", 218, small_font, DIM_AMBER)

    send_to_screen()


def show_listening(label):
    frame()
    centered_text(label, 48, small_font, DIM_AMBER)
    centered_text("LISTENING", 70, large_font, AMBER)

    draw.rectangle(
        (44, 111, WIDTH - 45, 157),
        outline=AMBER,
        width=2,
    )
    draw.rectangle(
        (53, 120, WIDTH - 54, 148),
        outline=DIM_AMBER,
        width=1,
    )

    centered_text("RELEASE BUTTON", 182, small_font, AMBER)
    centered_text("WHEN FINISHED", 199, small_font, AMBER)

    send_to_screen()


def show_question_received():
    frame()
    centered_text("QUESTION", 70, large_font, AMBER)
    centered_text("RECEIVED", 100, large_font, AMBER)
    centered_text("INTERPRETING", 157, small_font, DIM_AMBER)
    centered_text("YOUR DECISION", 176, small_font, AMBER)
    send_to_screen()


def show_connected():
    frame()
    centered_text("FUTURE SELF", 72, medium_font, AMBER)
    centered_text("CONNECTED", 103, large_font, AMBER)

    draw.rectangle(
        (49, 147, WIDTH - 50, 183),
        outline=AMBER,
        width=2,
    )

    centered_text("CHANNEL OPEN", 205, small_font, DIM_AMBER)
    send_to_screen()


def show_answer_ready():
    frame()
    centered_text("FUTURE SELF", 56, medium_font, AMBER)
    centered_text("IS LISTENING", 80, medium_font, AMBER)

    draw.line((27, 111, WIDTH - 28, 111), fill=DIM_AMBER)

    centered_text("HOLD GREEN", 143, medium_font, AMBER)
    centered_text("BUTTON TO ANSWER", 166, small_font, AMBER)
    centered_text("RELEASE TO SEAL", 199, small_font, DIM_AMBER)
    send_to_screen()


def show_sealed():
    frame()
    centered_text("MESSAGE", 75, large_font, AMBER)
    centered_text("SEALED", 106, large_font, AMBER)

    draw.rectangle(
        (48, 151, WIDTH - 49, 188),
        outline=AMBER,
        width=2,
    )

    centered_text("CONNECTION CLOSED", 210, small_font, DIM_AMBER)
    send_to_screen()


# ---------- Hardware inputs ----------

i2c = board.I2C()

rotary_device = seesaw.Seesaw(i2c, addr=0x36)
rotary_device.pin_mode(24, rotary_device.INPUT_PULLUP)

knob_button = seesaw_digitalio.DigitalIO(
    rotary_device,
    24,
)

encoder = rotaryio.IncrementalEncoder(rotary_device)

green_button = qwiic_button.QwiicButton()

if not green_button.begin():
    raise RuntimeError("Qwiic Button not found")

green_button.LED_off()


# ---------- Recording helpers ----------

def start_recording(output_file):
    return subprocess.Popen(
        [
            "arecord",
            "-q",
            "-f", "S16_LE",
            "-c", "1",
            "-r", "16000",
            str(output_file),
        ],
        stderr=subprocess.DEVNULL,
    )


def stop_recording(recorder):
    if recorder is not None and recorder.poll() is None:
        recorder.send_signal(signal.SIGINT)
        recorder.wait()


def flash_green_button(times=2):
    for _ in range(times):
        green_button.LED_on(180)
        time.sleep(0.18)
        green_button.LED_off()
        time.sleep(0.15)


# ---------- Load speech models ----------

show_initializing()

print("Loading Whisper base.en and Piper voice...")

recognizer = WhisperModel(
    "base.en",
    device="cpu",
    compute_type="int8",
)

speaker = Speaker(DEFAULT_VOICE)

print("Models ready.")


# ---------- Main interaction ----------

state = "intro"
selected = 0
recorder = None

decision_transcript = ""
reflection_transcript = ""
selected_question = ""

last_position = -encoder.position
last_knob_pressed = not knob_button.value
last_green_pressed = green_button.is_button_pressed()

show_intro()

print()
print("SATOR SQUARE PROTOTYPE")
print("Session:", session_id)
print("Turn the knob to awaken the device.")
print()

try:
    running = True

    while running:
        position = -encoder.position
        knob_pressed = not knob_button.value
        green_pressed = green_button.is_button_pressed()

        knob_just_pressed = (
            knob_pressed and not last_knob_pressed
        )

        green_just_pressed = (
            green_pressed and not last_green_pressed
        )

        green_just_released = (
            not green_pressed and last_green_pressed
        )

        # The first turn or press wakes the device. The movement is consumed,
        # so the menu still begins on TOMORROW.
        if state == "intro" and (
            position != last_position or knob_just_pressed
        ):
            state = "menu"
            show_menu(selected)
            print("Temporal channel awakened.")

            speaker.say(WAKE_LINE)

            last_position = -encoder.position
            last_knob_pressed = not knob_button.value
            last_green_pressed = green_button.is_button_pressed()
            time.sleep(0.02)
            continue

        # Rotate through return points.
        if state == "menu" and position != last_position:
            movement = position - last_position
            selected = (selected + movement) % len(OPTIONS)
            last_position = position

            show_menu(selected)
            print("Selected:", OPTIONS[selected])

        # Handle knob presses.
        if knob_just_pressed:
            if state == "menu":
                state = "decision_ready"
                show_decision_ready(selected)

                print("Return point:", OPTIONS[selected])
                speaker.say(SELECTION_LINES[OPTIONS[selected]])

                green_button.LED_on(35)
                green_pressed = green_button.is_button_pressed()
                last_green_pressed = green_pressed

                print("Waiting for the user's decision.")

            elif state == "decision_ready":
                state = "menu"
                green_button.LED_off()
                last_position = position
                show_menu(selected)

        # Record the original decision.
        if state == "decision_ready" and green_just_pressed:
            state = "decision_recording"
            green_button.LED_on(255)
            show_listening("YOUR DECISION")

            recorder = start_recording(decision_file)
            print("Recording decision...")

        elif state == "decision_recording" and green_just_released:
            stop_recording(recorder)
            recorder = None
            green_button.LED_off()

            show_question_received()
            print("Decision saved:", decision_file)

            speaker.say(DECISION_RECEIVED_LINE)

            print("Transcribing...")
            decision_transcript, decision_duration = transcribe_audio(
                recognizer,
                decision_file,
            )

            print("Transcript:", decision_transcript)

            selected_question = choose_question(
                decision_transcript,
                OPTIONS[selected],
            )

            show_connected()
            speaker.say(CONNECTED_LINE)
            speaker.say(selected_question)

            show_answer_ready()
            speaker.say(ANSWER_READY_LINE)

            state = "answer_ready"
            green_button.LED_on(35)

            green_pressed = green_button.is_button_pressed()
            last_green_pressed = green_pressed

            print("Waiting for the user's answer.")

        # Record the answer to the future-self question.
        elif state == "answer_ready" and green_just_pressed:
            state = "answer_recording"
            green_button.LED_on(255)
            show_listening("YOUR ANSWER")

            recorder = start_recording(reflection_file)
            print("Recording answer...")

        elif state == "answer_recording" and green_just_released:
            stop_recording(recorder)
            recorder = None
            green_button.LED_off()

            show_sealed()
            flash_green_button(times=2)

            speaker.say(CLOSING_LINES[OPTIONS[selected]])

            print("Answer saved:", reflection_file)
            print("Creating session record...")

            reflection_transcript, reflection_duration = transcribe_audio(
                recognizer,
                reflection_file,
            )

            session_data = {
                "session_id": session_id,
                "created_at": datetime.now().astimezone().isoformat(),
                "return_point": OPTIONS[selected],
                "decision_audio": str(decision_file),
                "decision_transcript": decision_transcript,
                "future_self_question": selected_question,
                "reflection_audio": str(reflection_file),
                "reflection_transcript": reflection_transcript,
            }

            session_file.write_text(
                json.dumps(
                    session_data,
                    indent=2,
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            print()
            print("MESSAGE SEALED")
            print("Session data:", session_file)
            print("Reflection:", reflection_transcript)
            print()

            running = False

        last_knob_pressed = knob_pressed
        last_green_pressed = green_pressed

        time.sleep(0.02)

finally:
    stop_recording(recorder)
    green_button.LED_off()
