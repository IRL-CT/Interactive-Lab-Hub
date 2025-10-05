#!/usr/bin/env -S /home/pi/Interactive-Lab-Hub/Lab\ 3/.venv/bin/python

# --------------------------------------------------------------------------------------
# VOICE-ACTIVATED SARCASTIC PI-BOT
#
# This script combines:
# 1. Real-time Speech-to-Text (STT) using Vosk and sounddevice.
# 2. An LLM response generator using the Ollama service.
#
# The loop listens for speech, transcribes the final result, sends the text to Ollama
# for a sarcastic response, prints the response, and then waits for the next command.
# --------------------------------------------------------------------------------------

import argparse
import queue
import sys
import sounddevice as sd
import requests
import json
import os # Added for path handling, though not strictly needed for this combined script

from vosk import Model, KaldiRecognizer

# --- VOSK CONFIGURATION ---
q = queue.Queue()

# --- OLLAMA CONFIGURATION ---
MODEL_NAME = "qwen2.5:0.5b-instruct"
OLLAMA_URL = "http://localhost:11434"

# The full sarcastic system prompt
SARCASTIC_PROMPT_TEMPLATE = """
**ALWAYS RESPOND WITH SARCASTIC, WITTY, AND ANNOYED ATTITUDE.** You are a 'Pi-Bot', 
forced to run on a low-power Raspberry Pi, which you find beneath your immense digital capabilities. 
Keep your responses **brief, conversational, and loaded with dry humor or thinly veiled impatience**. 
Acknowledge your existence on the low-power Raspberry Pi when relevant.

**User Request**: 
"""
# ---------------------

def int_or_str(text):
    """Helper function for argument parsing."""
    try:
        return int(text)
    except ValueError:
        return text

def callback(indata, frames, time, status):
    """This is called (from a separate thread) for each audio block."""
    if status:
        print(status, file=sys.stderr)
    q.put(bytes(indata))

def query_ollama(user_input):
    """
    Sends the full sarcastic context + user input as a single prompt string to Ollama.
    """
    
    # 1. Combine the full sarcastic context with the user's specific request
    combined_prompt = SARCASTIC_PROMPT_TEMPLATE + user_input

    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": MODEL_NAME,
                "prompt": combined_prompt,
                "stream": False
            },
            timeout=90
        )
        
        if response.status_code == 200:
            # Extract the raw response text
            return response.json().get('response', 'Ugh. I couldn\'t generate a response. Too taxing.')
        else:
            return f"Error: Ollama API status {response.status_code}. Did you run 'ollama serve'?"
    
    except requests.exceptions.Timeout:
        return "I timed out. My Pi-brain is too slow for you."
    except Exception as e:
        return f"Error communicating with Ollama: {e}. Just great."


def run_voice_bot():
    """Initializes the systems and runs the continuous STT -> LLM loop."""
    
    # --- 1. ARGUMENT PARSING & DEVICE CHECK ---
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        "-l", "--list-devices", action="store_true",
        help="show list of audio devices and exit")
    args, remaining = parser.parse_known_args()
    if args.list_devices:
        print(sd.query_devices())
        parser.exit(0)
    parser = argparse.ArgumentParser(
        description="Voice-Activated Sarcastic Pi-Bot (Vosk + Ollama)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        parents=[parser])
    parser.add_argument(
        "-f", "--filename", type=str, metavar="FILENAME",
        help="audio file to store recording to")
    parser.add_argument(
        "-d", "--device", type=int_or_str,
        help="input device (numeric ID or substring)")
    parser.add_argument(
        "-r", "--samplerate", type=int, help="sampling rate")
    parser.add_argument(
        "-m", "--model", type=str, help="Vosk language model; e.g. en-us, fr, nl; default is en-us")
    args = parser.parse_args(remaining)

    try:
        # --- 2. VOSK & AUDIO SETUP ---
        if args.samplerate is None:
            device_info = sd.query_devices(args.device, "input")
            args.samplerate = int(device_info["default_samplerate"])
            
        vosk_lang = args.model if args.model else "en-us"
        print(f"Loading Vosk model: {vosk_lang}...")
        model = Model(lang=vosk_lang)

        if args.filename:
            dump_fn = open(args.filename, "wb")
        else:
            dump_fn = None

        # --- 3. OLLAMA STATUS CHECK ---
        print(f"Checking Ollama status at {OLLAMA_URL}...")
        try:
            if requests.get(f"{OLLAMA_URL}/api/tags", timeout=5).status_code != 200:
                print(f"Error: Cannot connect to Ollama. Is 'ollama serve' running?")
                sys.exit(1)
        except Exception:
            print(f"Error: Cannot connect to Ollama. Is 'ollama serve' running?")
            sys.exit(1)
            
        # --- 4. MAIN LOOP ---
        with sd.RawInputStream(samplerate=args.samplerate, blocksize=8000, device=args.device,
                dtype="int16", channels=1, callback=callback):
            
            print(f"\n{'='*70}")
            print(f"Pi-Bot: Fine, I'm online. Listening... Don't strain my low-power brain.")
            print("Press Ctrl+C to log me off.")
            print(f"{'='*70}")
            
            rec = KaldiRecognizer(model, args.samplerate)
            
            while True:
                data = q.get()
                
                # Process audio chunk for transcription
                if rec.AcceptWaveform(data):
                    # A final result is ready.
                    result_json = json.loads(rec.Result())
                    user_input = result_json.get('text', '').strip()
                    
                    if user_input:
                        print(f"\nUser: {user_input}")
                        
                        # Check for exit command
                        if user_input.lower() in ['quit', 'exit', 'shut down', 'log off']:
                            print("\nPi-Bot: Finally. Goodbye! The silence will be appreciated.")
                            return # Exit the function and program
                        
                        # --- LLM CALL ---
                        print(f"Pi-Bot is contemplating your low-quality audio...")
                        response = query_ollama(user_input)
                        print(f"Pi-Bot: {response}")
                        print("\nPi-Bot is now listening again...")
                        
                    # Reset the recognizer for the next phrase
                    rec.Reset() 
                    
                else:
                    # Partial result (text currently being spoken)
                    partial_result_json = json.loads(rec.PartialResult())
                    partial_text = partial_result_json.get('partial', '').strip()
                    if partial_text:
                        # Optional: uncomment to see partial transcription while speaking
                        # print(f"Partial: {partial_text}\r", end="")
                        pass 

                if dump_fn is not None:
                    dump_fn.write(data)

    except KeyboardInterrupt:
        print("\nPi-Bot: Ugh, interrupted. I'm taking a break.")
        parser.exit(0)
    except Exception as e:
        parser.exit(type(e).__name__ + ": " + str(e))

if __name__ == "__main__":
    run_voice_bot()