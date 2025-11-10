# --- GESTURE PUBLISHER SCRIPT (Multi-Device Sync) ---
# Detects thumb direction (left or right) and publishes the corresponding 
# color command via MQTT using the SyncDisplay class.

import cv2
import mediapipe as mp
import time
import numpy as np
import sys
# Import the Synchronization class
from sync_display import SyncDisplay 

# --- Configuration ---
FRAME_WIDTH = 640
FRAME_HEIGHT = 480

# Define the colors in RGB format (SyncDisplay uses R, G, B order 0-255)
# Note: The original color values were BGR, they have been converted to RGB here.
# (255, 0, 0) BGR -> (0, 0, 255) RGB (Blue)
# (0, 255, 0) BGR -> (0, 255, 0) RGB (Green)

COLOR_RIGHT_THUMB_RGB = (0, 255, 0)    # Green (Thumb points Right)
COLOR_LEFT_THUMB_RGB = (0, 0, 255)     # Blue (Thumb points Left)
COLOR_DEFAULT_RGB = (50, 50, 50)       # Dark Gray (rest state)

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
    sys.exit(1) # Use sys.exit(1) for cleaner shutdown
    
cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
print(f"Webcam initialized successfully at index {camera_index}.")

# --- Initialize SyncDisplay in 'both' mode ---
# 'both' means it broadcasts the command AND renders it locally on its own PiTFT
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
    
    overlay = np.full((FRAME_HEIGHT, FRAME_WIDTH, 3), active_color_bgr, dtype=np.uint8)
    frame = cv2.addWeighted(frame, 0.5, overlay, 0.5, 0)

    # Add text on top
    text = f"THUMB: {color_name}"
    cv2.putText(frame, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(frame, "PiTFT/Sync: Showing this color. Press 'q' to quit.", (10, FRAME_HEIGHT - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, 
(255, 255, 255), 1, cv2.LINE_AA)
    
    return frame

# --- Main Execution Loop ---
try:
    sync.clear()
    
    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            time.sleep(0.05)
            continue

        frame = cv2.flip(frame, 1) # Flip for mirror view
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb_frame)

        color_name = "Neutral / Not Pointing"
        active_color_rgb = COLOR_DEFAULT_RGB

        if results.multi_hand_landmarks:
            hand_landmarks = results.multi_hand_landmarks[0]
            
            wrist_x = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST].x
            thumb_tip_x = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP].x
            
            # --- Thumb Direction Logic ---
            # If thumb tip is further right on the screen (smaller X value) than the wrist
            if thumb_tip_x < wrist_x:
                active_color_rgb = COLOR_RIGHT_THUMB_RGB
                color_name = "RIGHT (Green)"
            
            # If thumb tip is further left on the screen (larger X value) than the wrist
            elif thumb_tip_x > wrist_x:
                active_color_rgb = COLOR_LEFT_THUMB_RGB
                color_name = "LEFT (Blue)"

            # Draw the hand landmarks on the VNC frame
            mp.solutions.drawing_utils.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS,
                mp.solutions.drawing_styles.get_default_hand_landmarks_style(),
                mp.solutions.drawing_styles.get_default_hand_connections_style())

        
        # 1. Send Command to All Displays (Publish)
        # Use *active_color_rgb to unpack the (R, G, B) tuple
        sync.display_color(*active_color_rgb) 
        
        # 2. Draw Debug Info on VNC Desktop
        display_frame = draw_debug_info(frame, color_name, active_color_rgb)
        cv2.imshow('Gesture Publisher (VNC Debug)', display_frame)

        # Break the loop if the 'q' key is pressed
        if cv2.waitKey(5) & 0xFF == ord('q'):
            break

except Exception as e:
    print(f"An error occurred: {e}")
    
finally:
    # Cleanup resources
    sync.clear()
    sync.stop()
    cap.release()
    cv2.destroyAllWindows()