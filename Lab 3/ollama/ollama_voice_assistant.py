#!/usr/bin/env python3
"""
Ollama Voice Assistant for Lab 3 (Raspberry Pi optimized)
- Speech input via microphone
- Query Ollama with up to 3-minute response timeout
- Speak response using espeak (Unicode-safe)
"""

import speech_recognition as sr
import requests
import subprocess
import time
import sys

# Ensure stdout supports UTF-8
sys.stdout.reconfigure(encoding='utf-8')

# Ollama configuration
OLLAMA_URL = "http://localhost:11434"
DEFAULT_MODEL = "phi3:mini"

# Maximum Ollama query timeout (in seconds)
OLLAMA_TIMEOUT = 180  # 3 minutes

# Microphone settings
MAX_LISTEN_TIME = 15       # maximum listening duration in seconds
SILENCE_TIMEOUT = 2        # seconds of silence to stop recording early


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
        print(f"Querying Ollama (this may take up to {OLLAMA_TIMEOUT // 60} minutes)...")
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=OLLAMA_TIMEOUT
        )

        if response.status_code == 200:
            return response.json().get("response", "No response generated")
        else:
            return f"Error: Ollama returned status {response.status_code}"

    except requests.exceptions.Timeout:
        return "Sorry, the response took too long. Please try again."
    except Exception as e:
        return f"Error: {str(e)}"


def speak_text(text):
    """Use espeak to speak text safely with Unicode handling."""
    try:
        # Replace problematic Unicode characters
        safe_text = text.replace("–", "-").replace("…", "...")
        # Split text into chunks to avoid very long lines for espeak
        max_chunk = 200
        for i in range(0, len(safe_text), max_chunk):
            chunk = safe_text[i:i + max_chunk]
            subprocess.run(['espeak', chunk], check=False)
    except Exception as e:
        print(f"TTS Error: {e}")


def main():
    """Main loop: listen → recognize → query → speak."""
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
                audio = r.listen(source, timeout=None, phrase_time_limit=MAX_LISTEN_TIME)

                print("Recognizing speech...")
                user_text = r.recognize_google(audio, language="en-US")
                print(f"You said: {user_text}")

                # Query Ollama
                ai_response = query_ollama(user_text)
                print(f"Ollama: {ai_response}")

                # Speak response
                speak_text(ai_response)

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
