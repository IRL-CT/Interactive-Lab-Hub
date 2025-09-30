#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pi Voice Assistant using Vosk + Ollama + espeak
- Pre-scripted responses for greetings and exit commands
- Dynamic AI-generated responses using Ollama
- Fully offline speech recognition with Vosk (blocking)
- Speaks responses with espeak
"""

import subprocess
import requests
import sys
import json
import sounddevice as sd
import vosk
import numpy as np

# TTS engine
TTS_ENGINE = 'espeak'
OLLAMA_URL = "http://localhost:11434"
MODEL_NAME = "phi3:mini"  # You can change this to "tinyllama" for faster responses

# Load Vosk model
try:
    vosk_model = vosk.Model("vosk-model-small-en-us-0.15")
except Exception as e:
    print(f"Error loading Vosk model: {e}")
    sys.exit(1)

def speak(text):
    """Text-to-speech using espeak"""
    print(f"Assistant: {text}")
    subprocess.run(f'espeak "{text}"', shell=True, check=False)

def listen(duration=5, fs=16000):
    """Record audio and return recognized text using Vosk (blocking)"""
    try:
        print("Listening...")
        # Record audio for fixed duration
        audio = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
        sd.wait()  # Wait until recording is finished

        # Flatten audio and convert to bytes
        audio_bytes = audio.tobytes()

        # Recognize with Vosk
        rec = vosk.KaldiRecognizer(vosk_model, fs)
        if rec.AcceptWaveform(audio_bytes):
            result = json.loads(rec.Result())
        else:
            result = json.loads(rec.FinalResult())

        recognized_text = result.get("text", "").strip()
        print(f"You said: {recognized_text}")
        return recognized_text.lower() if recognized_text else None

    except Exception as e:
        print(f"Error recording audio: {e}")
        return None

def query_ollama(prompt):
    """Send input to Ollama and get AI response"""
    try:
        payload = {"model": MODEL_NAME, "prompt": prompt, "stream": False}
        response = requests.post(f"{OLLAMA_URL}/api/generate", json=payload, timeout=10)
        if response.status_code == 200:
            try:
                result_json = response.json()
                ai_text = result_json.get("response") or result_json.get("text")
                if ai_text:
                    return ai_text
                else:
                    return "Sorry, I did not get a response from the AI."
            except Exception as e:
                return f"Error parsing AI response: {e}"
        else:
            return f"Error: Ollama returned status {response.status_code}"
    except requests.exceptions.ConnectionError:
        return "Error: Cannot connect to Ollama. Make sure 'ollama serve' is running."
    except requests.exceptions.Timeout:
        return "Sorry, the AI is taking too long to respond. Please try a shorter question."
    except Exception as e:
        return f"Unexpected error communicating with Ollama: {e}"

def main():
    speak("Hello Charlotte! I am your offline voice assistant. Say 'exit' to quit.")

    while True:
        user_input = listen(duration=5)
        if user_input is None:
            continue

        # Pre-scripted exit commands
        if any(word in user_input for word in ['exit', 'quit', 'bye']):
            speak("Goodbye! Have a great day!")
            break

        # Pre-scripted greetings
        if any(word in user_input for word in ['hello', 'hi', 'hey']):
            speak("Hello! What would you like to talk about?")
            continue

        # Anything else → AI-generated response
        speak("Thinking...")
        response = query_ollama(user_input)
        
        # If Ollama times out or fails, provide a simple fallback response
        if "taking too long" in response or "Error" in response:
            speak("I'm having trouble with the AI right now. Let me give you a simple response instead.")
            if "weather" in user_input:
                response = "I can't check the weather right now, but you can check a weather app or website."
            elif "time" in user_input:
                response = "I can't tell you the exact time right now, but you can check your device's clock."
            else:
                response = "That's an interesting question! I'm having some technical difficulties right now, but I'd be happy to help with something else."
        
        speak(response)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting...")
        speak("Goodbye!")
