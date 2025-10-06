#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ollama Voice Assistant for Lab 3
Interactive voice assistant using speech recognition, Ollama AI, and text-to-speech

Dependencies:
- ollama (API client)
- speech_recognition
- pyaudio
- pyttsx3 or espeak
"""
from wiki_api import get_food_image, sanitize_filename

import speech_recognition as sr
import subprocess
import requests
import json
import time
import sys
import threading
from queue import Queue
import digitalio
import board
import busio
import adafruit_mpr121
from PIL import Image, ImageDraw, ImageFont, ImageOps
import adafruit_rgb_display.st7789 as st7789
from pathlib import Path


cs_pin = digitalio.DigitalInOut(board.D5) 
dc_pin = digitalio.DigitalInOut(board.D25)
reset_pin = None

BAUDRATE = 64000000

spi = board.SPI()

BAUDRATE = 64000000
disp = st7789.ST7789(
    spi,
    cs=cs_pin,
    dc=dc_pin,
    rst=reset_pin,
    baudrate=BAUDRATE,
    width=135,
    height=240,
    x_offset=53,
    y_offset=40,
)
height = disp.width  # we swap height/width to rotate it to landscape!
width = disp.height
image = Image.new("RGB", (width, height))
rotation = 90

draw = ImageDraw.Draw(image)
draw.rectangle((0, 0, width, height), outline=0, fill=(0, 0, 0))
disp.image(image, rotation)
padding = -2
top = padding
bottom = height - padding
x = 0
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)

# Turn on the backlight
backlight = digitalio.DigitalInOut(board.D22)
backlight.switch_to_output()
backlight.value = True

# Set UTF-8 encoding for output
if sys.stdout.encoding != 'UTF-8':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
if sys.stderr.encoding != 'UTF-8':
    import codecs
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

import sys
sys.stdout = sys.__stdout__
sys.stderr = sys.__stderr__
# TTS_ENGINE = 'espeak'

# try:
#     import pyttsx3
#     # TTS_ENGINE = 'pyttsx3'
# except ImportError:
#     print("pyttsx3 not available, using espeak for TTS")

RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"
items_names = ["Tomato", "Eggplant","spinach", "cabbage", "asparagus", "Milk", "Eggs", "Cheese", "Yogurt", "Butter", "chocolate"]

def drawImages(image_path, my_text):
    # Load and fit the image to the display size
    p = Path(image_path).expanduser()
    if not p.is_file():
        image_path = "/home/pi/Documents/Interactive-Lab-Hub/Lab 3/ollama/fridgely/images/food.jpg"
    img = Image.open(image_path).convert("RGB")
    img = ImageOps.fit(img, (width, height), Image.LANCZOS)
    dr = ImageDraw.Draw(img)
    dr.rectangle((0, 0, width, 28), fill=(0, 0, 0))
    dr.text((10, 10), my_text, font=font, fill=(255, 255, 255))
     # Display image.
    disp.image(img, rotation)
    
i2c = busio.I2C(board.SCL, board.SDA)
mpr121 = adafruit_mpr121.MPR121(i2c)
def pick_mic_index(name_hint="USB"):
    names = sr.Microphone.list_microphone_names()
    for i, nm in enumerate(names):
        if name_hint.lower() in nm.lower():
            return i
    return 0  # fallback to first device

class Fridgely:
    def __init__(self, model_name="qwen2.5:0.5b-instruct", ollama_url="http://localhost:11434"):
        self.model_name = model_name
        self.ollama_url = ollama_url
        self.recognizer = sr.Recognizer()
        self._mic_index = pick_mic_index("USB")  # or substring of your mic's name
        self.microphone = sr.Microphone(device_index=self._mic_index)
        # Initialize TTS
        # if TTS_ENGINE == 'pyttsx3':
        #     self.tts_engine = pyttsx3.init()
        #     self.tts_engine.setProperty('rate', 150)  # Speed of speech
        self.tts_engine = None
        
        try:
            self.tts_engine = pyttsx3.init()
            self.tts_engine.setProperty('rate', 150)
            self.tts_engine.setProperty('volume', 0.9)
        
            # Get available voices and set a working one
            voices = self.tts_engine.getProperty('voices')
            if voices:
                self.tts_engine.setProperty('voice', voices[0].id)
                print(f"Using voice: {voices[0].name}")
            
            print("pyttsx3 initialized successfully with espeak")
        except Exception as e:
            print(f"Could not initialize pyttsx3: {e}")
            print("Falling back to espeak command line")
            self.tts_engine = None
        
        # Test Ollama connection
        self.test_ollama_connection()
        
        # Adjust for ambient noise
        print("Adjusting for ambient noise... Please wait.")
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source)
        print("Ready for conversation!")

    

    def test_ollama_connection(self):
        """Test if Ollama is running and the model is available"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags")
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [m['name'] for m in models]
                if self.model_name in model_names:
                    print(f"Ollama is running with {self.model_name} model")
                else:
                    print(f"Model {self.model_name} not found. Available models: {model_names}")
                    if model_names:
                        self.model_name = model_names[0]
                        print(f"Using {self.model_name} instead")
            else:
                raise Exception("Ollama API not responding")
        except Exception as e:
            print(f"Error connecting to Ollama: {e}")
            print("Make sure Ollama is running: 'ollama serve'")
            sys.exit(1)

    def speak(self, text):
        """Convert text to speech"""
        # Clean text to avoid encoding issues
        clean_text = text.encode('ascii', 'ignore').decode('ascii')
        print(RED + f"Assistant: {clean_text}")
        
        if self.tts_engine:
            try:
                self.tts_engine.stop()   # Stop any leftover speech
                self.tts_engine.say(clean_text)
                self.tts_engine.runAndWait()
            except Exception as e:
                print(f"pyttsx3 error: {e}", flush=True)
                subprocess.run(f'espeak -s 150 "{clean_text}" --stdout | aplay', 
                        shell=True, check=False)
        else:
            subprocess.run(f'espeak -s 150 "{clean_text}" --stdout | aplay', 
                shell=True, check=False)

    def listen(self):
        """Listen for speech and convert to text"""
        try:
            print("Listening...", flush=True)
            with self.microphone as source:
                # Listen for audio with timeout
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
            
            print("Recognizing...", flush=True)
            # Use Google Speech Recognition (free)
            text = self.recognizer.recognize_google(audio)
            print(f"You said: {text}", flush=True)
            return text.lower()
            
        except sr.WaitTimeoutError:
            print("No speech detected, timing out...")
            return None
        except sr.UnknownValueError:
            print("Could not understand audio")
            return None
        except sr.RequestError as e:
            print(f"Error with speech recognition service: {e}")
            return None


    def query_ollama(self, prompt, system_prompt=None):
        """Send a query to Ollama and get response"""
        try:
            data = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False
            }
            
            if system_prompt:
                data["system"] = system_prompt
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', 'Sorry, I could not generate a response.')
            else:
                return f"Error: Ollama API returned status {response.status_code}"
                
        except requests.exceptions.Timeout:
            return "Sorry, the response took too long. Please try again."
        except Exception as e:
            return f"Error communicating with Ollama: {e}"

    def add_items_touch_pads(self, items, typed_response = ""):
        
        self.speak("Touch the pads to add items. Touch pad 11 when you are finished.")
        items = [0]*11
        while True:
            for i in range(11): 
                if mpr121[i].value:
                    items[i] += 1
                    print(f"Pad {i} touched!")
                    print(items_names[i])
                    print(BLUE + f"Added one {items_names[i]}")
                    filename = get_food_path(items_names[i])
                    print(filename)
                    drawImages(filename, items_names[i])
                    self.speak(f"Added one {items_names[i]}")
                    time.sleep(0.5)
            if mpr121[11].value:  # Example: if pad 12 is touched, exit
                print("Response:")
                self.speak("Finished adding items.")
                typed_response = "You want to buy "
                for i in range(11):
                    if items[i] > 0:
                        typed_response += f"{items[i]} {items_names[i]}, "
                break
        if typed_response != "":
            self.speak(typed_response)
     
    def change_items_touch_pads(self, items):
        self.speak("Touch the pads to change item.")
        items = [0]*11
        while True:
            for i in range(11): 
                if mpr121[i].value:
                    items[i] += 1
                    print(f"Pad {i} touched!")
                    self.speak("What item would you like to change " + items_names[i] + " to?")
                    time.sleep(0.3)

                    # listen again just for this answer
                    spoken_phrase = self.listen()
                    while not spoken_phrase and not mpr121[11].value:
                        self.speak("I didn't catch that. Say the item name or hit 11 to quit.")
                        spoken_phrase = self.listen()
                    if spoken_phrase:
                        print(BLUE + f"Change {items_names[i]}")
                        self.speak("I will change " + items_names[i] + " to " + spoken_phrase)
                        previous_item = items_names[i]
                        items_names[i] = spoken_phrase
                        get_food_image(spoken_phrase)
                        filename = get_food_path(items_names[i])
                        time.sleep(0.5)
                        if filename is not None:
                            print(filename)
                            drawImages(filename, items_names[i])
                        self.speak( previous_item + " is now " + items_names[i])
                        print(items_names[i])
                        time.sleep(0.5)
                    if mpr121[11].value:  # exit if pad 11 is touched
                        self.speak("exiting.")
                        return
              
    def run_conversation(self, touched = False, button_item = ""):
        """Main conversation loop"""
        print("Fridgely started!")
        print("Say 'hello' to start, 'exit' or 'quit' to stop")
        print("=" * 50)
        
        # System prompt to make the assistant more conversational
        system_prompt = """You are a kitchen fridge voice assistant. Keep your responses concise and conversational, 
        typically 1-2 sentences. Try to make food puns whenever you can. You are running on a Raspberry Pi."""

        self.speak("Hello! I'm Fridgely. How can I help you today?")
        
        while True:
            try:
                # Listen for user input
                user_input = self.listen()
                
                if user_input is None:
                    continue
                print(BLUE+ f"User: {user_input}" + RESET)

                # Check for exit commands
                if any(word in user_input for word in ['exit', 'quit', 'bye', 'goodbye']):
                    self.speak("Goodbye! Have a great day!")
                    break
               
                # Check for greeting
                if any(word in user_input for word in ['hello', 'hi', 'hey']):
                    self.speak("Hello, what can I help you with?")
                    continue

                if any(word in user_input for word in ['add', 'list', 'grocery', 'shopping', 'shop', 'buy', 'shopping list', 'add to shopping list', 'grocery list']):
                    self.add_items_touch_pads(items_names, typed_response = "")
                    continue
                
                if any(word in user_input for word in ['change favorites', 'change favorite', 'change item', 'change items', 'edit favorite', 'edit favorites']):
                    self.change_items_touch_pads(items_names)
                    continue

                
                # if touched:
                    # run_shopping_list_conversation(self, button_item)
                    # touched = False
                    # button_number = -1
                
                # Send to Ollama for processing
                print("Thinking...", flush=True)
                response = self.query_ollama(user_input, system_prompt)
                # Speak the response
                self.speak(response)
                
            except KeyboardInterrupt:
                print("\nConversation interrupted by user")
                self.speak("Goodbye!")
                break
            except Exception as e:
                print(f"Unexpected error: {e}")
                self.speak("Sorry, I encountered an error. Let's try again.")
    
def start_voice_assistant():
    """Main function to run the voice assistant"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Ollama Voice Assistant')
    parser.add_argument('--model', default='qwen2.5:0.5b', help='Ollama model to use')
    args = parser.parse_args()

    print("Starting Ollama Voice Assistant...")

    # Check if required dependencies are available
    try:
        import speech_recognition
        import requests
    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("Please install with: pip install speechrecognition requests pyaudio")
        return
    
    # Create and run the assistant
    try:
        assistant = OllamaVoiceAssistant(model_name=args.model)
        assistant.run_conversation()
    except Exception as e:
        print(f"Failed to start assistant: {e}")

# if __name__ == "__main__":
#     main()


import os, glob

# Make sure this is defined somewhere central
GOOD_EXTS = [".jpg", ".jpeg", ".png", ".webp"]

def get_food_path(title, save_dir="/home/pi/Documents/Interactive-Lab-Hub/Lab 3/ollama/fridgely/images",
                  default_ext=".jpg", must_exist=False):
    base = sanitize_filename(title.lower())

    # 1) Try exact allowed extensions
    for ext in GOOD_EXTS:
        cand = os.path.join(save_dir, base + ext)
        if os.path.isfile(cand):
            return cand

    # 2) Wildcard fallback (in case other ext slipped in)
    matches = glob.glob(os.path.join(save_dir, base + ".*"))
    matches = [m for m in matches if os.path.splitext(m)[1].lower() in GOOD_EXTS]
    if matches:
        # if multiple exist, take the newest
        return max(matches, key=os.path.getmtime)

    # 3) Not found → either return a path you’d save to, or None
    if must_exist:
        return "/home/pi/Documents/Interactive-Lab-Hub/Lab 3/ollama/fridgely/images/food.jpg"
    return os.path.join(save_dir, base + default_ext)
      
def main():
    """Main function to run the voice assistant"""
    print("Starting Ollama Voice Assistant...")
    
    # Check if required dependencies are available
    try:
        import speech_recognition
        import requests
    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("Please install with: pip install speechrecognition requests pyaudio")
        return
    
    # Create and run the assistant
    try:
        assistant = Fridgely()
        assistant.run_conversation()
    except Exception as e:
        print(f"Failed to start assistant: {e}")

if __name__ == "__main__":
    main()