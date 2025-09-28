# ollama_voice_assistant.py

import speech_recognition as sr
import requests
import os
import time

# --- Configuration ---
MICROPHONE_INDEX = 2 
MODEL_NAME = "phi3:mini"
OLLAMA_URL = "http://localhost:11434/api/generate"

ENERGY_THRESHOLD = 150 

def speak(text):
    """Uses the espeak command line tool for Text-to-Speech with better parameters."""
    
    text = text.replace("'", "'\\''")
    # -v en+f3: Female English voice | -s 150: Speed 150 WPM | -k 15: Pitch/Inflection
    print(f"AI Speaking: {text}")
    os.system(f"espeak -v en+f3 -s 150 -k 15 '{text}' 2>/dev/null")

def transcribe_speech():
    """Listens for user input and converts it to text."""
    r = sr.Recognizer()
    try:
        with sr.Microphone(device_index=MICROPHONE_INDEX) as source:
            r.adjust_for_ambient_noise(source)
            r.energy_threshold = ENERGY_THRESHOLD 
            
            print("\nListening... Speak now.")
            speak("Ready. Ask me anything.")
            
            
            time.sleep(0.5) 
           
            audio = r.listen(source, timeout=8, phrase_time_limit=15)
            
    except Exception as e:
        print(f"Microphone error: {e}. Check MICROPHONE_INDEX ({MICROPHONE_INDEX}).")
        speak("I am having trouble accessing the microphone.")
        return None

    try:
        print("Transcribing via Google Speech Recognition...")
        text = r.recognize_google(audio) 
        print(f"User Said: {text}")
        return text
    except sr.UnknownValueError:
        print("Could not understand audio.")
        speak("I didn't catch that. Could you repeat it?")
        return None
    except sr.RequestError as e:
        print(f"Speech recognition service error: {e}")
        speak("My transcription service is currently unavailable.")
        return None

def ask_ai(question):
    """Sends the question to the local Ollama model."""
    print("Sending request to Ollama...")
    try:
        # Long timeout (120 seconds) for the RPi's slow processing
        response = requests.post(
            OLLAMA_URL,
            json={"model": MODEL_NAME, "prompt": question, "stream": False},
            timeout=120 
        )
        response.raise_for_status() 
        return response.json().get('response', 'No response received from the model.')
    except requests.exceptions.RequestException as e:
        print(f"Error communicating with Ollama: {e}")
        return "I seem to be having trouble connecting to the AI model on port 11434."

def main_assistant_loop():
    """Main loop for the voice assistant."""
    speak("Voice assistant is active. Say 'stop' to quit.")
    while True:
        user_text = transcribe_speech()
        
        if user_text:
            if "stop" in user_text.lower() or "exit" in user_text.lower() or "quit" in user_text.lower():
                speak("Goodbye.")
                print("Exiting assistant.")
                break
            
            ai_response = ask_ai(user_text)
            
            if ai_response:
                print(f"AI Response: {ai_response}")
                speak(ai_response)

if __name__ == "__main__":
    main_assistant_loop()
