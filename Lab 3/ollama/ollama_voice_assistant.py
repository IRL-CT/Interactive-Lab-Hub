#!/usr/bin/env python3
"""
Ollama Voice Assistant for Lab 3
- Speech input via microphone
- Query Ollama (up to 3 minutes)
- Speak response using espeak (Unicode safe, BLOCKING)
"""

import speech_recognition as sr
import requests
import subprocess
import time
import sys

# Ensure stdout uses utf-8 to avoid encoding errors
sys.stdout.reconfigure(encoding='utf-8')

# Ollama configuration
OLLAMA_URL = "http://localhost:11434"
DEFAULT_MODEL = "phi3:mini"

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

def query_ollama(prompt, model=DEFAULT_MODEL, timeout=180):
    """Send prompt to Ollama and return response (up to 3 minutes)."""
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=timeout
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
    """Convert text to speech using espeak (BLOCKING, safe Unicode)."""
    try:
        # Replace problematic characters
        safe_text = text.replace('–', '-').replace('—', '-').replace('…', '...')

        safe_text = ''.join(c if ord(c) < 128 else ' ' for c in safe_text)

        subprocess.run(['espeak', '-v', 'en', safe_text], check=False, encoding='utf-8', timeout=120)
    except subprocess.TimeoutExpired:
        print("TTS timeout exceeded")
    except Exception as e:
        print(f"TTS Error: {e}")


def main():
    """Main loop: listen → recognize → query → speak."""
    device_index = get_microphone_index()
    r = sr.Recognizer()

    try:
        with sr.Microphone(device_index=device_index) as source:
            print("Calibrating microphone for ambient noise...")
            r.adjust_for_ambient_noise(source, duration=1)
            print("Calibration complete")

            print("Voice assistant ready. Speak into the microphone.")
            print("Press Ctrl+C to stop.")

            while True:
                try:
                    print("\nListening...")
                    # Listen for up to 15 seconds, end after 2s silence
                    audio = r.listen(source, timeout=15, phrase_time_limit=15)

                    print("Recognizing speech...")
                    user_text = r.recognize_google(audio, language="en-US")
                    print(f"You said: {user_text}")

                    print("Querying Ollama (this may take up to 3 minutes)...")
                    ai_response = query_ollama(user_text)
                    print(f"Ollama: {ai_response}")

                    # BLOCKING speak: next listen starts only after TTS finishes
                    speak_text(ai_response)

                except sr.WaitTimeoutError:
                    print("No speech detected in time.")
                except sr.UnknownValueError:
                    print("Could not understand audio.")
                except sr.RequestError as e:
                    print(f"Speech Recognition service error: {e}")
                except Exception as e:
                    print(f"Error: {e}")
                    time.sleep(1)

    except KeyboardInterrupt:
        print("\nExiting voice assistant...")

if __name__ == "__main__":
    main()
