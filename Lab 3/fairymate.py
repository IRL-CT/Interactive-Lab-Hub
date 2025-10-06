import time
import board
import busio
import adafruit_mpr121
import speech_recognition as sr
import subprocess

# --- Setup hardware ---
i2c = busio.I2C(board.SCL, board.SDA)
mpr121 = adafruit_mpr121.MPR121(i2c)

import digitalio
from PIL import Image, ImageDraw, ImageFont
import adafruit_rgb_display.st7789 as st7789

# --- ST7789 setup (adjust pins if needed) ---
cs_pin = digitalio.DigitalInOut(board.D5)
dc_pin = digitalio.DigitalInOut(board.D25)
reset_pin = None

BAUDRATE = 64000000

spi = board.SPI()

DISPLAY_WIDTH  = 135
DISPLAY_HEIGHT = 240
disp = st7789.ST7789(
    spi,
    cs=cs_pin,
    dc=dc_pin,
    rst=reset_pin,
    baudrate=BAUDRATE,
    width=DISPLAY_WIDTH,
    height=DISPLAY_HEIGHT,
    x_offset=53,
    y_offset=40,   # adjust depending on your display orientation
)

# --- Create image buffer ---
image = Image.new("RGB", (disp.width, disp.height))
draw = ImageDraw.Draw(image)
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)

def update_mode_display(mode):
    # Clear the screen
    draw.rectangle((0, 0, disp.width, disp.height), outline=0, fill=(0, 0, 0))
    
    # Choose text and color
    if mode == "emotional":
        text = "Emotional\nSupport <3"
        color = (255, 100, 150)
    else:
        text = "Solution\nSupport :)"
        color = (100, 180, 255)
    
    # Measure text size (Pillow ≥10 uses textbbox)
    try:
        bbox = draw.textbbox((0, 0), text, font=font)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    except AttributeError:
        w, h = font.getsize(text)
    
    # Draw centered text
    draw.text(
        ((disp.width - w) // 2, (disp.height - h) // 2),
        text,
        font=font,
        fill=color,
        align="center"
    )
    
    disp.image(image)


# --- Speech recognition ---
recognizer = sr.Recognizer()

# --- System state ---
mode = "solution"   # default mode
print("System ready! Default mode: Solution Support.")

# --- Speak using espeak ---
def speak(text):
    print(f"Pi says: {text}")
    subprocess.run(["espeak", "-s", "165", text])

# --- Listen for voice input ---
def listen():
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        print("🎤 Listening...")
        audio = recognizer.listen(source)
    try:
        text = recognizer.recognize_google(audio, language="en-US")
        print(f"User said: {text}")
        return text
    except Exception:
        print("Could not understand speech.")
        return ""

# --- Simple keyword-based mood detection ---
def analyze_mood(user_text):
    if not user_text:
        return "neutral"
    text = user_text.lower()
    if any(w in text for w in ["good", "great", "happy", "awesome", "amazing"]):
        return "positive"
    elif any(w in text for w in ["bad", "sad", "tired", "angry", "terrible"]):
        return "negative"
    else:
        return "neutral"

def emotional_response(mood):
    responses = {
        "positive": "That’s wonderful to hear! I’m so glad you’re feeling good today.",
        "neutral":  "I see. It sounds like a calm day. I’m here if you’d like to share more.",
        "negative": "I’m really sorry it’s been a tough day. Remember, it’s okay to rest and take things slow."
    }
    return responses[mood]

def solution_response(mood):
    responses = {
        "positive": "Awesome! Maybe keep that momentum going with something you enjoy.",
        "neutral":  "Alright. Maybe you could set a small goal to make the day more productive.",
        "negative": "Sounds like you’ve had a rough day. Maybe try writing down one thing you can solve step by step."
    }
    return responses[mood]

# --- Main loop ---
while True:
    for i in range(12):
        if mpr121[i].value:
            if i < 6:
                mode = "emotional"
                speak("Switched to emotional support mode.")
            else:
                mode = "solution"
                speak("Switched to solution support mode.")
            
            update_mode_display(mode)
            time.sleep(1)
            speak("How’s your day?")
            user_text = listen()
            mood = analyze_mood(user_text)

            if mode == "emotional":
                speak(emotional_response(mood))
            else:
                speak(solution_response(mood))

            print(f"Mode: {mode}, Mood: {mood}\n")
            time.sleep(3)  # debounce
    time.sleep(0.1)
