#!/usr/bin/env python3
"""
Simple Moondream Vision Demo
Captures image from webcam and asks Moondream to describe it
Uses OpenCV like other Lab 5 scripts
"""

import cv2
import requests
import base64
import time

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
    print("Smile! Capturing in 3...")
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

def ask_moondream(image_path, prompt="What do you see in this image? Describe it."):
    """Ask Moondream about the image with streaming response"""
    
    # Encode image to base64
    with open(image_path, 'rb') as f:
        image_data = base64.b64encode(f.read()).decode('utf-8')
    
    print(f"\nAsking Moondream: {prompt}")
    print("\nMoondream: ", end="", flush=True)
    
    # Query Moondream with streaming
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "moondream:latest",
            "prompt": prompt,
            "images": [image_data],
            "stream": True
        },
        timeout=300,  # Increased timeout to 5 minutes
        stream=True
    )
    
    if response.status_code == 200:
        full_response = ""
        for line in response.iter_lines():
            if line:
                import json
                chunk = json.loads(line)
                token = chunk.get('response', '')
                print(token, end="", flush=True)
                full_response += token
        
        print("\n")  # New line after response
        return full_response
    else:
        print(f"Error: {response.status_code}")
        return None

def main():
    print("Moondream Simple Vision Demo")
    print("=" * 50)
    
    # Capture image
    image_path = capture_image()
    
    if not image_path:
        print("Failed to capture image. Exiting.")
        return
    
    # Ask Moondream to describe it
    ask_moondream(image_path)
    
    # Allow follow-up questions
    print("\nAsk questions about the image (or 'quit' to exit):")
    while True:
        question = input("\nYou: ").strip()
        if question.lower() in ['quit', 'exit', 'q', '']:
            break
        ask_moondream(image_path, question)
    
    print("Done!")

if __name__ == "__main__":
    main()
