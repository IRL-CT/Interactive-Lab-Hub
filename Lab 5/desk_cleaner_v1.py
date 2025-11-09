#!/usr/bin/env python3
"""
Desk Observer Concept
Based on the TA's Simple Moondream Vision Demo.

This script implements the "Desk Observer":
- It runs in a continuous loop.
- Every 5 minutes, it captures an image from the webcam.
- It asks Moondream to describe the desk.
- It analyzes the description for keywords ("messy", "clean", etc.).
- It prints a gentle reminder or a compliment.
"""

import cv2
import requests
import base64
import time
import json
import sys

# --- Configuration for Desk Observer ---

# How long to wait between checks (in seconds)
WAIT_TIME_SECONDS = 300  # 5 minutes


# The specific prompt for Moondream
DESK_PROMPT = "Describe the state of the desk in this image. Is it clean, messy, or cluttered?"

# Keywords to check in Moondream's (lowercase) response
MESSY_KEYWORDS = MESSY_KEYWORDS = [
    "messy", "cluttered", "disorganized", "untidy", "chaotic", 
    "jumbled", "sloppy", "unorganized", "scattered", "strewn", 
    "piles", "trash", "garbage", "disarray", "clutter"
]
CLEAN_KEYWORDS = [
    "clean", "organized", "tidy", "neat", "orderly", "uncluttered", 
    "clear", "minimal", "minimalist", "empty", "spacious", 
    "arranged", "spotless"
]

# --- End Configuration ---


def capture_image(filename="captured_image.jpg"):
    """Capture image from webcam using OpenCV"""
    print("Opening camera...")
    
    # Open webcam (same as infer.py and hand_pose.py)
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    if not cap.isOpened():
        print("Error: Could not open camera")
        return None
    
    print("Camera warming up...")
    # Let camera warm up - need more time for proper exposure
    time.sleep(2)
    for i in range(30):
        cap.read()
    
    # Capture frame
    print("Capturing in 3...")
    time.sleep(1)
    print("2...")
    time.sleep(1)
    print("1...")
    time.sleep(1)
    print("*CLICK*")
    
    ret, frame = cap.read()
    cap.release()
    
    if not ret:
        print("Error: Could not capture image")
        return None
    
    # Save image
    cv2.imwrite(filename, frame)
    print(f"Image saved as: {filename}")
    return filename

def ask_moondream(image_path, prompt):
    """
    Ask Moondream about the image with streaming response.
    (Unchanged from TA's sample, but increased timeout)
    """
    
    # Encode image to base64
    try:
        with open(image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
    except FileNotFoundError:
        print(f"\n[ERROR] Image file not found: {image_path}")
        return None
    
    print(f"\nAsking Moondream: {prompt}")
    print("Moondream is thinking... ", end="", flush=True)
    
    try:
        # Query Moondream with streaming
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "moondream:latest",
                "prompt": prompt,
                "images": [image_data],
                "stream": True
            },
            timeout=300,  # 5 minute timeout for slow models
            stream=True
        )
        
        if response.status_code == 200:
            full_response = ""
            for line in response.iter_lines():
                if line:
                    chunk = json.loads(line)
                    token = chunk.get('response', '')
                    print(token, end="", flush=True)
                    full_response += token
            
            print("\n")  # New line after response
            return full_response.strip()
        else:
            print(f"\n[ERROR] Moondream API returned status: {response.status_code}")
            print(f"Details: {response.text}")
            return None
    except requests.exceptions.Timeout:
        print("\n[TIMEOUT] Moondream is taking too long.")
        return None
    except requests.exceptions.ConnectionError:
        print("\n[CONNECTION ERROR] Could not connect to Moondream server.")
        print("Please ensure Ollama is running at http://localhost:11434")
        return None
    except Exception as e:
        print(f"\n[UNEXPECTED ERROR] {e}")
        return None

def analyze_description(description):
    """
    (NEW FUNCTION)
    Interprets Moondream's response based on your concept's logic.
    """
    
    if not description:
        return "Not sure how it looks. (Moondream gave no response)"

    desc_lower = description.lower()
    
    # Check for messy keywords
    if any(keyword in desc_lower for keyword in MESSY_KEYWORDS):
        return f"Looks messy :( maybe tidy up your desk?\n(Moondream said: \"{description}\")"
    
    # Check for clean keywords
    elif any(keyword in desc_lower for keyword in CLEAN_KEYWORDS):
        return f"Nice and clean today!\n(Moondream said: \"{description}\")"
    
    # Fallback
    else:
        return f"Not sure how it looks.\n(Moondream said: \"{description}\")"

def main():
    """
    (COMPLETELY REWRITTEN)
    Main loop for the Desk Observer.
    """
    print("=" * 50)
    print("--- Desk Observer Activated ---")
    print(f"I will check your desk every {WAIT_TIME_SECONDS // 60} minutes.")
    print("Press Ctrl+C to stop.")
    print("=" * 50)

    try:
        while True:
            print(f"\n--- {time.ctime()} ---")
            
            # 1. Input: Capture image
            image_path = capture_image()
            
            if not image_path:
                print("Failed to capture image. Will try again next cycle.")
                time.sleep(WAIT_TIME_SECONDS)
                continue
            
            # 2. Processing: Get description from Moondream
            description = ask_moondream(image_path, DESK_PROMPT)
            
            # 3. Interpretation & 4. Output: Analyze and print feedback
            message = analyze_description(description)
            
            print("\n--- Desk Observer's Reflection ---")
            print(message)
            print("------------------------------------------")
            
            # 5. Wait for the next cycle
            print(f"\nSleeping for {WAIT_TIME_SECONDS // 60} minutes...")
            time.sleep(WAIT_TIME_SECONDS)

    except KeyboardInterrupt:
        print("\n\n--- Desk Observer Deactivated ---")
        print("Goodbye!")
        sys.exit(0)

if __name__ == "__main__":
    main()