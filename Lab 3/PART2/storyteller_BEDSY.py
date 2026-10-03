import os
import subprocess
import tempfile
import time

import board
import digitalio
from gpiozero import Button
from PIL import Image, ImageDraw, ImageFont
import adafruit_rgb_display.st7789 as st7789
from faster_whisper import WhisperModel


# Button: physical pin 40 = GPIO21, physical pin 39 = GND
button = Button(21, pull_up=True)


# OLED
cs_pin = digitalio.DigitalInOut(board.D5)
dc_pin = digitalio.DigitalInOut(board.D25)
spi = board.SPI()

display = st7789.ST7789(
    spi,
    cs=cs_pin,
    dc=dc_pin,
    rst=None,
    baudrate=64000000,
    width=135,
    height=240,
    x_offset=53,
    y_offset=40,
)

font = ImageFont.truetype(
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    17,
)


def show_face(mode, mouth_open=False):
    image = Image.new("RGB", (240, 135), "black")
    draw = ImageDraw.Draw(image)

    if mode == "SPEAKING":
        color = "green"
    elif mode == "LISTENING":
        color = "cyan"
    elif mode == "THINKING":
        color = "yellow"
    else:
        color = "red"

    draw.ellipse((45, 15, 195, 125), outline=color, width=4)
    draw.ellipse((78, 50, 92, 64), fill=color)
    draw.ellipse((148, 50, 162, 64), fill=color)

    if mouth_open:
        draw.ellipse((96, 82, 144, 110), outline=color, width=4)
    else:
        draw.arc((92, 78, 148, 108), 0, 180, fill=color, width=4)

    draw.text((5, 5), mode, font=font, fill=color)
    display.image(image, rotation=90)


def make_audio(text):
    file_object = tempfile.NamedTemporaryFile(
        suffix=".raw",
        delete=False,
    )

    filename = file_object.name
    file_object.close()

    process = subprocess.Popen(
        [
            "python3",
            "-m",
            "piper",
            "--model",
            "en_US-lessac-medium",
            "--output-raw",
            "--length-scale",
            "1.15",
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    audio, error = process.communicate(text.encode())

    if process.returncode != 0:
        print(error.decode())
        raise RuntimeError("Piper error")

    with open(filename, "wb") as file:
        file.write(audio)

    return filename


def speak(text):
    print("STORYTELLER:", text)

    subprocess.run(
        [
            "wpctl",
            "set-volume",
            "@DEFAULT_AUDIO_SINK@",
            "1.0",
        ],
        check=False,
    )

    audio_file = make_audio(text)

    speaker = subprocess.Popen(
        [
            "aplay",
            "-r",
            "22050",
            "-f",
            "S16_LE",
            "-c",
            "1",
            audio_file,
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    mouth_open = False

    while speaker.poll() is None:
        mouth_open = not mouth_open
        show_face("SPEAKING", mouth_open)
        time.sleep(0.18)

    show_face("SPEAKING", False)
    os.remove(audio_file)


def speak_story_sentence(text):
    print("STORYTELLER:", text)

    audio_file = make_audio(text)

    speaker = subprocess.Popen(
        [
            "aplay",
            "-r",
            "22050",
            "-f",
            "S16_LE",
            "-c",
            "1",
            audio_file,
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    interrupted = False
    mouth_open = False
    time.sleep(0.3)

    while speaker.poll() is None:
        mouth_open = not mouth_open
        show_face("SPEAKING", mouth_open)

        if button.is_pressed:
            print("BUTTON PRESSED")
            speaker.terminate()
            interrupted = True
            show_face("LISTENING", False)

            while button.is_pressed:
                time.sleep(0.05)

            break

        time.sleep(0.18)

    if speaker.poll() is None:
        speaker.terminate()

    os.remove(audio_file)
    return interrupted


def record_speech(seconds=2):
    show_face("LISTENING", False)
    print("Listening... Speak now.")

    file_object = tempfile.NamedTemporaryFile(
        suffix=".wav",
        delete=False,
    )

    filename = file_object.name
    file_object.close()

    subprocess.run(
        [
            "arecord",
            "-d",
            str(seconds),
            "-f",
            "S16_LE",
            "-c",
            "1",
            "-r",
            "16000",
            filename,
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    return filename


def transcribe(filename):
    show_face("THINKING", False)
    print("Thinking...")

    segments, information = whisper_model.transcribe(
        filename,
        beam_size=1,
    )

    text = " ".join(
        segment.text.strip()
        for segment in segments
    )

    os.remove(filename)
    return text.strip()


# Speaker says ONLY the fixed answer.
# The question is printed in the terminal, not spoken.
def answer_interruption(number):
    if number == 1:
        speak(
            "The girls' names are Afroza, K.M., "
            "Cici, and Lamiah."
        )

    elif number == 2:
        speak(
            "They are working late at night because "
            "they have several assignments to finish."
        )

    else:
        speak(
            "Please stop interrupting me while "
            "I am telling the story."
        )


story = [
    "I will tell you a HORROR story about Cornell Tech.",
    "There were four girls who used to study at Cornell Tech: Afroza, K.M., Lamiah, and Cici.",
    "One night, they were working on a project for their Interactive Devices class.",
    "It was very late, and the entire building was almost empty.",
    "Suddenly, all the lights went out.",
    "The girls stopped typing and looked around the dark room.",
    "At the end of the hallway, they saw Professor Wendy Ju and Professor Albert walking toward them.",
    "Their faces looked unusually serious and frightening in the darkness.",
    "The four girls became terrified.",
    "Professor Wendy Ju slowly walked closer and said in a threatening voice:",
    "If you do not finish your homework, all of you will receive zero!",
    "The students became overwhelmed by homework pressure, and they fainted one by one.",
    "When the lights came back on, the room was empty.",
    "Only the Raspberry Pi was still running.",
    "There was a message on the Raspberry Pi screen:",
    "Your homework is still due tomorrow!",
    "This is the end of the horror story about Cornell Tech.",
]


print("Loading Whisper model...")

whisper_model = WhisperModel(
    "tiny.en",
    device="cpu",
    compute_type="int8",
)


try:
    show_face("LISTENING", False)

    speak(
        "I am your bedtime storyteller, Bedsy. "
        "What kind of story would you like to hear?"
    )

    genre_file = record_speech(2)
    genre = transcribe(genre_file)

    if genre == "":
        genre = "horror"

    print("You said:", genre)
    print("I heard you said:", genre)

    speak(
        "Okay. I will tell you a horror story "
        "about Cornell Tech."
    )

    time.sleep(3)

    interruption_number = 0

    for sentence in story:
        interrupted = speak_story_sentence(sentence)

        if interrupted:
            interruption_number += 1

            question_file = record_speech(2)
            question = transcribe(question_file)

            if question == "":
                question = "nothing"

            # Question appears only on the laptop terminal
            print("You said:", question)
            print("I heard you said:", question)
            print("Interruption number:", interruption_number)

            # Speaker does not repeat question
            answer_interruption(interruption_number)

            print("Returning to the story.")
            print()

        time.sleep(0.2)

    show_face("STOPPED", False)
    speak(
        "This is the end of the horror story "
        "about Cornell Tech. Good night."
    )
    show_face("STOPPED", False)


except KeyboardInterrupt:
    print("\nStoryteller stopped.")
    show_face("STOPPED", False)

except Exception as error:
    print("\nPROGRAM ERROR:")
    print(error)
    show_face("STOPPED", False)
