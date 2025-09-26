#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ollama Voice Assistant for Lab 3 (English version)
Raspberry Pi optimized:
- Uses webcam mic (card 2, device 0)
- Uses HDMI audio (card 0, device 0)
- English speech recognition and TTS
"""

import speech_recognition as sr
import subprocess
import requests
import sys
import time

# TTS setup: prefer pyttsx3, fallback to espeak
try:
    import pyttsx3
    TTS_ENGINE = 'pyttsx3'
except ImportError:
    TTS_ENGINE = 'espeak'
    print("pyttsx3 not available, using espeak for TTS")

class OllamaVoiceAssistant:
    def __init__(self, model_name="phi3:mini", ollama_url="http://localhost:11434"):
        self.model_name = model_name
        self.ollama_url = ollama_url

        # Specify microphone (card 2: C270 webcam)
        self.microphone = sr.Microphone(device_index=2)
        self.recognizer = sr.Recognizer()

        # Initialize TTS
        if TTS_ENGINE == 'pyttsx3':
            self.tts_engine = pyttsx3.init()
            self.tts_engine.setProperty('rate', 150)  # Speech speed

        # Check Ollama server and model
        self.check_ollama()

        # Ambient noise calibration
        print("Adjusting for ambient noise... Please wait.")
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source)
        print("Ready for conversation!")

    def check_ollama(self):
        """Check if Ollama server is running and model is available"""
        try:
            r = requests.get(f"{self.ollama_url}/api/tags")
            if r.status_code != 200:
                raise Exception("Ollama API not responding")
            models = [m['name'] for m in r.json().get('models', [])]
            if self.model_name not in models:
                print(f"Specified model {self.model_name} not found, using {models[0]} instead")
                self.model_name = models[0]
            print(f"Ollama is running, using model: {self.model_name}")
        except Exception as e:
            print(f"Error connecting to Ollama: {e}")
            sys.exit(1)

    def speak(self, text):
        """Convert text to speech in English"""
        print(f"Assistant: {text}")
        if TTS_ENGINE == 'pyttsx3':
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
        else:
            # Use espeak with English voice
            subprocess.run(['espeak', text, '-ven+m3', '-s150', '-a200'], check=False)

    def listen(self):
        """Listen for English audio and convert to text"""
        try:
            print("Listening...")
            with self.microphone as source:
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
            print("Recognizing...")
            # Use Google Speech Recognition in English
            text = self.recognizer.recognize_google(audio, language="en-US")
            print(f"You said: {text}")
            return text.lower()
        except sr.WaitTimeoutError:
            print("No speech detected")
            return None
        except sr.UnknownValueError:
            print("Could not understand audio")
            return None
        except sr.RequestError as e:
            print(f"Error with speech recognition service: {e}")
            return None

    def query_ollama(self, prompt, system_prompt=None):
        """Send a prompt to Ollama and get a response"""
        try:
            data = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False
            }
            if system_prompt:
                data["system"] = system_prompt
            response = requests.post(f"{self.ollama_url}/api/generate", json=data, timeout=30)
            if response.status_code == 200:
                result = response.json()
                return result.get('response', "Sorry, I couldn't generate a response.")
            else:
                return f"Error: Ollama API returned status {response.status_code}"
        except requests.exceptions.Timeout:
            return "Sorry, the response took too long. Please try again."
        except Exception as e:
            return f"Error communicating with Ollama: {e}"

    def run_conversation(self):
        """Main conversation loop"""
        print("\nOllama Voice Assistant Started (English)!")
        print("Say 'hello' to start, 'exit' or 'quit' to stop")
        print("=" * 50)

        system_prompt = """You are a helpful English-speaking voice assistant. Keep responses concise and conversational,
typically 1-2 sentences. Be friendly and engaging. You are running on a Raspberry Pi as part
of an interactive device design lab."""

        self.speak("Hello! I'm your Ollama voice assistant. How can I help you today?")

        while True:
            try:
                user_input = self.listen()
                if user_input is None:
                    continue
                # Exit commands
                if any(word in user_input for word in ['exit', 'quit', 'bye', 'goodbye']):
                    self.speak("Goodbye! Have a great day!")
                    break
                # Greeting
                if any(word in user_input for word in ['hello', 'hi', 'hey']):
                    self.speak("Hello! What would you like to talk about?")
                    continue
                # Query Ollama
                print("Thinking...")
                response = self.query_ollama(user_input, system_prompt)
                self.speak(response)
            except KeyboardInterrupt:
                print("\nConversation interrupted by user")
                self.speak("Goodbye!")
                break
            except Exception as e:
                print(f"Unexpected error: {e}")
                self.speak("Sorry, I encountered an error. Let's try again.")

def main():
    """Main entry point"""
    print("Starting Ollama Voice Assistant (English)...")
    # Check dependencies
    try:
        import speech_recognition
        import requests
    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("Install via: pip install speechrecognition requests pyaudio")
        return
    # Run assistant
    try:
        assistant = OllamaVoiceAssistant()
        assistant.run_conversation()
    except Exception as e:
        print(f"Failed to start assistant: {e}")

if __name__ == "__main__":
    main()
