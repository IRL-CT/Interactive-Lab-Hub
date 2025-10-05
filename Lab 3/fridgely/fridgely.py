#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fridgely Voice Assistant for Lab 3
Interactive voice assistant using speech recognition, text-to-speech, and touch sensor

Dependencies:
- speech_recognition
- pyaudio
- pyttsx3 or espeak
"""

import speech_recognition as sr
import subprocess
import requests
import json
import time
import sys
import threading
from queue import Queue
import board
import busio
import adafruit_mpr121


RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

try:
    import pyttsx3
    TTS_ENGINE = 'pyttsx3'
except ImportError:
    TTS_ENGINE = 'espeak'
    print("pyttsx3 not available, using espeak for TTS")

class Fridgely:
    def __init__(self,):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        # Initialize TTS
        if TTS_ENGINE == 'pyttsx3':
            self.tts_engine = pyttsx3.init()
            self.tts_engine.setProperty('rate', 150)  # Speed of speech
        
        # Adjust for ambient noise
        print("Adjusting for ambient noise... Please wait.")
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source)
        print("Ready for conversation!")

    def speak(self, text):
        """Convert text to speech"""
        # Clean text to avoid encoding issues
        clean_text = text.encode('ascii', 'ignore').decode('ascii')
        print(RED + f"Assistant: {clean_text}" + RESET)
        
        if TTS_ENGINE == 'pyttsx3':
            self.tts_engine.say(clean_text)
            self.tts_engine.runAndWait()
        else:
            # Use espeak as fallback
            subprocess.run(['espeak', clean_text], check=False)

    def listen(self):
        """Listen for speech and convert to text"""
        try:
            print("Listening...")
            with self.microphone as source:
                # Listen for audio with timeout
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
            
            print("Recognizing...")
            # Use Google Speech Recognition (free)
            text = self.recognizer.recognize_google(audio)
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

    def run_conversation(self):
        """Main conversation loop"""
        print("Fridglly started!")
        print("Say 'hello' to start, 'exit' or 'quit' to stop")
        print("=" * 50)
        items_names = ["Tomato", "Eggplant","spinash", "cabbage", "asparagus", "Milk", "Eggs", "Cheese", "Yogurt", "Butter",]
        
        self.speak("Hello!")

        # i2c = busio.I2C(board.SCL, board.SDA)
        # mpr121 = adafruit_mpr121.MPR121(i2c)
        
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
                
                print("Response:")
                typed_response = input("> ") 

                if "add" in typed_response: 
                    self.speak("Touch the pads to add items. Touch pad 11 when you are finished.")
                    items = [0]*11 

                    while True:
                        for i in range(11): 
                            if mpr121[i].value:
                                items[i] += 1
                                print(f"Pad {i} touched!")
                                self.speak(f"Added one {items_names[i]}")
                                time.sleep(0.5)
                        if mpr121[11].value:  # Example: if pad 12 is touched, exit
                            print("Response:")
                            self.speak("Finished adding items.")
                            typed_response = "You want to buy "
                            for i in range(11):
                                if items[i] > 0:
                                    typed_response += f"{items[i]} {items_names[i]}, "
                            # self.speak(response)
                            break

                # Speak the response
                if typed_response:
                    self.speak(typed_response)
                
            except KeyboardInterrupt:
                print("\nConversation interrupted by user")
                self.speak("Goodbye!")
                break
            except Exception as e:
                print(f"Unexpected error: {e}")
                self.speak("Sorry, I encountered an error. Let's try again.")

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