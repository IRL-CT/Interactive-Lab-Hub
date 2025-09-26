#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ollama Voice Assistant (Raspberry Pi version)
Simplified to always use espeak for TTS (no pyttsx3).
Suppresses ALSA warnings for cleaner logs.
"""

import os
import sys
import subprocess
import requests
import speech_recognition as sr

# 🔇 Suppress ALSA warnings
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
os.environ["SDL_AUDIODRIVER"] = "dsp"
sys.stderr = open(os.devnull, "w")  # hide ALSA/JACK spam

# Ollama configuration
OLLAMA_URL = "http://localhost:11434"
DEFAULT_MODEL = "phi3:mini"


class OllamaVoiceAssistant:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()

        # Adjust for ambient noise
        print("Adjusting for ambient noise... Please wait.")
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source)
        print("Ready for conversation!")

    def speak(self, text):
        """Use espeak for text-to-speech"""
        clean_text = text.replace('"', '')  # avoid shell injection
        print(f"Assistant: {clean_text}")
        subprocess.run(["espeak", clean_text], check=False)

    def listen(self):
        """Listen for speech and return text"""
        try:
            print("Listening...")
            with self.microphone as source:
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
            print("Recognizing...")
            text = self.recognizer.recognize_google(audio)
            print(f"You said: {text}")
            return text.lower()
        except Exception:
            return None

    def query_ollama(self, prompt):
        """Send prompt to Ollama and return response"""
        try:
            response = requests.post(
                f"{OLLAMA_URL}/api/generate",
                json={"model": DEFAULT_MODEL, "prompt": prompt, "stream": False},
                timeout=30,
            )
            if response.status_code == 200:
                return response.json().get("response", "No response.")
            else:
                return f"Error: Ollama returned {response.status_code}"
        except Exception as e:
            return f"Ollama error: {e}"

    def run(self):
        """Main loop"""
        self.speak("Hello! I am your voice assistant.")
        while True:
            user_input = self.listen()
            if not user_input:
                continue
            if any(word in user_input for word in ["exit", "quit", "bye"]):
                self.speak("Goodbye!")
                break
            response = self.query_ollama(user_input)
            self.speak(response)


def main():
    print("Starting Ollama Voice Assistant (espeak only)...")
    assistant = OllamaVoiceAssistant()
    assistant.run()


if __name__ == "__main__":
    main()
