#!/usr/bin/env python3
"""
Optimized Ollama Voice Assistant for Lab 3
- Speech input via microphone
- Query Ollama asynchronously
- Speak response using pyttsx3 (Unicode safe)
- Split long responses into smaller chunks for faster TTS
"""

import speech_recognition as sr
import requests
import pyttsx3
import asyncio
import threading
import time
import sys

# Ensure stdout can print Unicode
sys.stdout.reconfigure(encoding='utf-8')

# Ollama configuration
OLLAMA_URL = "http://localhost:11434"
DEFAULT_MODEL = "phi3:mini"

# TTS engine initialization
engine = pyttsx3.init()
engine.setProperty('rate', 150)  # Speech rate

def speak_text(text):
    """Convert text to speech using pyttsx3, splitting into chunks."""
    # Replace problematic characters
    safe_text = text.replace("–", "-").replace("…", "...")

    # Split text into chunks for faster playback
    chunks = []
    max_len = 150
    while safe_text:
        chunk = safe_text[:max_len]
        # Try to split at sentence end
        if len(safe_text) > max_len:
            last_dot = chunk.rfind('.')
            last_q = chunk.rfind('?')
            last_ex = chunk.rfind('!')
            split_idx = max(last_dot, last_q, last_ex)
            if split_idx > 50:
                chunk = safe_text[:split_idx+1]
        chunks.append(chunk.strip())
        safe_text = safe_text[len(chunk):]

    for c in chunks:
        engine.say(c)
        engine.runAndWait()

def get_microphone_index():
    """Find and return the index of the preferred microphone."""
    mic_list = sr.Microphone.list_microphone_names()
    print("Detected microphones:")
    for idx, name in enumerate(mic_list):
        print(f"{idx}: {name}")

    # Prefer Logitech C270 HD Webcam
    for i, name in enumerate(mic_list):
        if "C270 HD WEBCAM" in name:
            print(f"Using preferred device: {name} (index={i})")
            return i
    # Fallback to default
    print("C270 microphone not found, using default device")
    return 0

def query_ollama(prompt, model=DEFAULT_MODEL):
    """Send prompt to Ollama and return response."""
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=180  # up to 3 minutes
        )
        if response.status_code == 200:
            return response.json().get("response", "No response generated")
        else:
            return f"Error: Ollama returned status {response.status_code}"
    except requests.exceptions.Timeout:
        return "Sorry, the response took too long. Please try again."
    except Exception as e:
        return f"Error: {str(e)}"

def async_query_and_speak(user_text):
    """Thread target: query Ollama and speak response."""
    print(f"Querying Ollama (this may take some time)...")
    ai_response = query_ollama(user_text)
    print(f"Ollama: {ai_response}")
    speak_text(ai_response)

def main():
    """Main loop: listen → recognize → async query → speak."""
    device_index = get_microphone_index()
    r = sr.Recognizer()

    with sr.Microphone(device_index=device_index) as source:
        print("Calibrating microphone for ambient noise...")
        r.adjust_for_ambient_noise(source, duration=1)
        print("Calibration complete")

        print("Voice assistant ready. Speak into the microphone.")
        print("Press Ctrl+C to stop.")

        while True:
            try:
                print("\nListening...")
                audio = r.listen(source, timeout=None, phrase_time_limit=15)

                print("Recognizing speech...")
                user_text = r.recognize_google(audio, language="en-US")
                print(f"You said: {user_text}")

                # Run Ollama query and TTS in separate thread
                threading.Thread(target=async_query_and_speak, args=(user_text,), daemon=True).start()

            except sr.UnknownValueError:
                print("Could not understand audio")
            except sr.RequestError as e:
                print(f"Speech Recognition service error: {e}")
            except KeyboardInterrupt:
                print("\nExiting voice assistant...")
                break
            except Exception as e:
                print(f"Error: {e}")
                time.sleep(1)

if __name__ == "__main__":
    main()
