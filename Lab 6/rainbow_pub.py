# --- RAINBOW GESTURE PUBLISHER SCRIPT (Discrete ROYGBIV Cycle) ---
# Detects a thumb-pointing gesture (Left or Right) as a single command 
# to cycle through the fixed ROYGBIV color sequence on all synchronized displays.

import cv2
import mediapipe as mp
import time
import numpy as np
import sys
import os
import colorsys 
import threading 

# --- CRITICAL FIX: Ensure current directory is in path for SyncDisplay ---
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.append(script_dir)
from sync_display import SyncDisplay 


# --- Configuration ---
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
COLOR_DEFAULT_RGB = (50, 50, 50)       # Dark Gray (rest state)
GESTURE_COOLDOWN_SEC = 0.5             # Time (in seconds) between acceptable gestures

# --- ROYGBIV Color Sequence (RGB 0-255) ---
ROYGBIV = [
    (255, 0, 0),        # R: Red
    (255, 165, 0),      # O: Orange
    (255, 255, 0),      # Y: Yellow
    (0, 128, 0),        # G: Green
    (0, 0, 255),        # B: Blue
    (75, 0, 130),       # I: Indigo
    (238, 130, 238)     # V: Violet
]

# --- State Variables for Cycling ---
color_index = 0
last_gesture_time = time.time()


# --- Initialize MediaPipe Hand Detector ---
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    model_complexity=0,
    min_detection_confidence=0.7, 
    min_tracking_confidence=0.5)

# --- Initialize Webcam with Camera Index Fallback ---
camera_index = 0
cap = cv2.VideoCapture(camera_index) 
if not cap.isOpened():
    camera_index = 1
    print("Warning: Index 0 failed. Trying index 1...")
    cap = cv2.VideoCapture(camera_index)

if not cap.isOpened():
    print("FATAL ERROR: Cannot open webcam at index 0 or 1. Check connection and permissions.")
    sys.exit(1)
    
cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
print(f"Webcam initialized successfully at index {camera_index}.")


# --- Initialize SyncDisplay in 'both' mode ---
try:
    sync = SyncDisplay(mode='both')
except Exception as e:
    print(f"FATAL ERROR: Could not initialize SyncDisplay. Check MQTT config/internet. Error: {e}")
    cap.release()
    sys.exit(1)


def draw_debug_info(frame, color_name, active_color_rgb):
    """Draws the instructional text and a colored overlay for the VNC desktop."""
    # Convert RGB color back to BGR for OpenCV display
    active_color_bgr = (active_color_rgb[2], active_color_rgb[1], active_color_rgb[0])
    
    # Create a subtle color overlay for debug view
    overlay = np.full((FRAME_HEIGHT, FRAME_WIDTH, 3), active_color_bgr, dtype=np.uint8)
    frame = cv2.addWeighted(frame, 0.7, overlay, 0.3, 0) # 70% frame, 30% overlay

    # Add text on top
    text = f"COLOR: {color_name}"
    cv2.putText(frame, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(frame, "Point Thumb Left/Right to cycle ROYGBIV. Press 'q' to quit.", 
                (10, FRAME_HEIGHT - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
    
    return frame

# --- Main Execution Loop ---
try:
    sync.clear()
    
    while cap.isOpened():
        current_time = time.time()
        success, frame = cap.read()
        if not success:
            time.sleep(0.05)
            continue

        frame = cv2.flip(frame, 1) # Flip for mirror view
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb_frame)

        color_name = "Neutral"
        active_color_rgb = ROYGBIV[color_index] # Always start with the current color

        # --- Gesture Detection and Cycling Logic ---
        gesture_detected = False
        
        if results.multi_hand_landmarks:
            hand_landmarks = results.multi_hand_landmarks[0]
            wrist_x = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST].x
            thumb_tip_x = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP].x
            
            # Check for pointing gesture (Left or Right)
            if thumb_tip_x != wrist_x: 
                gesture_detected = True
                color_name = "Pointing Detected"

                # Check if enough time has passed since the last successful gesture
                if (current_time - last_gesture_time) > GESTURE_COOLDOWN_SEC:
                    
                    # Advance the color index (cycle through 0, 1, 2, ..., len-1)
                    # Removed the 'global color_index' line which caused the SyntaxError
                    color_index = (color_index + 1) % len(ROYGBIV)
                    
                    active_color_rgb = ROYGBIV[color_index]
                    color_name = f"NEXT ({['R', 'O', 'Y', 'G', 'B', 'I', 'V'][color_index]})"
                    last_gesture_time = current_time # Reset cooldown timer

            # Draw the hand landmarks on the VNC frame
            mp.solutions.drawing_utils.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS,
                mp.solutions.drawing_styles.get_default_hand_landmarks_style(),
                mp.solutions.drawing_styles.get_default_hand_connections_style())

        
        # If no gesture was detected and the hand is invisible, use the default gray (rest state)
        if not gesture_detected and not results.multi_hand_landmarks:
             active_color_rgb = COLOR_DEFAULT_RGB
             color_name = "Resting"
        
        # 1. Send Command to All Displays (Publish)
        sync.display_color(*active_color_rgb) 
        
        # 2. Draw Debug Info on VNC Desktop
        display_frame = draw_debug_info(frame, color_name, active_color_rgb)
        cv2.imshow('Gesture Publisher (VNC Debug)', display_frame)

        # Break the loop if the 'q' key is pressed
        if cv2.waitKey(5) & 0xFF == ord('q'):
            break

except Exception as e:
    print(f"\nAn error occurred: {e}")
    
finally:
    # Cleanup resources
    if 'sync' in locals() and sync is not None:
        sync.clear()
        sync.stop()
        print("SyncDisplay stopped.")

    cap.release()
    cv2.destroyAllWindows()
    print("Webcam released. Program finished.")