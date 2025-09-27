#!/usr/bin/env python3
"""
Ollama Voice Assistant for Lab 3
- Speech input via microphone
- Query Ollama
- Speak response using espeak
"""

import speech_recognition as sr
import requests
import subprocess
import os
import time
import sys
sys.stdout.reconfigure(encoding='utf-8')

# -------------------------------
# Safe print wrapper
# -------------------------------
def safe_print(text):
    """Print safely with UTF-8 encoding fallback."""
    try:
        print(text)
    except UnicodeEncodeError:
        # Replace problematic characters to avoid crash
        print(text.encode("utf-8", errors="replace").decode("utf-8"))


# Ollama configuration
OLLAMA_URL = "http://localhost:11434"
DEFAULT_MODEL = "phi3:mini"


def get_microphone_index():
    """Find and return the index of the preferred microphone."""
    mic_list = sr.Microphone.list_microphone_names()
    safe_print("Detected microphones:")
    for idx, name in enumerate(mic_list):
        safe_print(f"{idx}: {name}")

    # Prefer Logitech C270 HD Webcam
    for i, name in enumerate(mic_list):
        if "C270 HD WEBCAM" in name:
            safe_print(f"Using preferred device: {name} (index={i})")
            return i

    # Fallback to default
    safe_print("C270 microphone not found, using default device")
    return 0


def query_ollama(prompt, model=DEFAULT_MODEL):
    """Send prompt to Ollama and return response."""
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=30
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
    """Convert text to speech using espeak."""
    try:
        subprocess.run(['espeak', text], check=False)
    except Exception as e:
        safe_print(f"TTS Error: {e}")


def main():
    """Main loop: listen → recognize → query → speak."""
    device_index = get_microphone_index()
    r = sr.Recognizer()

    with sr.Microphone(device_index=device_index) as source:
        safe_print("Calibrating microphone for ambient noise...")
        r.adjust_for_ambient_noise(source, duration=1)
        safe_print("Calibration complete")

        safe_print("Voice assistant ready. Speak into the microphone.")
        safe_print("Press Ctrl+C to stop.")

        while True:
            try:
                safe_print("\nListening...")
                audio = r.listen(source, timeout=None, phrase_time_limit=5)

                safe_print("Recognizing speech...")
                user_text = r.recognize_google(audio, language="en-US")
                safe_print(f"You said: {user_text}")

                # Query Ollama
                ai_response = query_ollama(user_text)
                safe_print(f"Ollama: {ai_response}")

                # Speak response
                speak_text(ai_response)

            except sr.UnknownValueError:
                safe_print("Could not understand audio")
            except sr.RequestError as e:
                safe_print(f"Speech Recognition service error: {e}")
            except KeyboardInterrupt:
                safe_print("\n Exiting voice assistant...")
                break
            except Exception as e:
                safe_print(f"Error: {e}")
                time.sleep(1)


if __name__ == "__main__":
    main()
