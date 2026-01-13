"""
Gesture-Based Music Controller v2.0 - Headless Mode
No GUI window - runs in terminal only
Perfect for SSH sessions without X11 forwarding

Key Improvements:
1. Terminal-based visual feedback with ASCII art
2. Gesture confirmation: Requires holding gesture for 0.5s
3. Better error recovery
4. Reduced false positives
"""

import cv2
import time
import numpy as np
import HandTrackingModule as htm
import math
import subprocess
from collections import deque
import os

# ========== Audio Control Functions ==========
def set_volume(percent):
    subprocess.run(
        ["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{int(percent)}%"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

def volume_up():
    subprocess.run(
        ["pactl", "set-sink-volume", "@DEFAULT_SINK@", "+5%"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

def volume_down():
    subprocess.run(
        ["pactl", "set-sink-volume", "@DEFAULT_SINK@", "-5%"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

# ========== Music Playback ==========
music_files = [
    "../Lab 4/music/spring-mood-wav-212731_fixed.wav",
    "../Lab 4/music/atlantic-lights-rain-402613_fixed.wav",
    "../Lab 4/music/hard-phonk-master-wav-262571_fixed.wav",
    "../Lab 4/music/we-wish-you-a-merry-christmas-short-version-wav-144068_fixed.wav"
]
current_track = 0
audio_process = None

def play_current_track():
    global audio_process, current_track
    if audio_process is not None:
        audio_process.terminate()
        time.sleep(0.1)
    
    music_path = music_files[current_track]
    command = ['aplay', '-D', 'pulse', music_path]
    audio_process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    track_name = music_path.split('/')[-1].replace('_fixed.wav', '').replace('-', ' ')
    print(f'[PLAY] {track_name}')
    return track_name

def play_pause():
    global audio_process
    if audio_process and audio_process.poll() is None:
        audio_process.terminate()
        audio_process = None
        print("[PAUSE] Music Stopped")
        return "Stopped"
    else:
        return play_current_track()

def next_track():
    global current_track
    current_track = (current_track + 1) % len(music_files)
    return play_current_track()

def previous_track():
    global current_track
    current_track = (current_track - 1) % len(music_files)
    return play_current_track()

# ========== Camera Setup ==========
wCam, hCam = 640, 480

for camera_id in [0, 1, 2]:
    cap = cv2.VideoCapture(camera_id)
    if cap.isOpened():
        print(f"[OK] Camera found at /dev/video{camera_id}")
        break
    cap.release()
else:
    print("[ERROR] No camera found. Please check camera connection.")
    exit(1)

cap.set(cv2.CAP_PROP_FRAME_WIDTH, wCam)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, hCam)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

# ========== Initialize System ==========
set_volume(50)
current_song = play_current_track()

detector = htm.handDetector(detectionCon=0.7, maxHands=1)

# ========== Gesture State Variables ==========
gesture_cooldown = 0
cooldown_time = 1.0
current_gesture = "None"
prev_hand_center = None
pTime = 0

# Gesture confirmation system
gesture_history = deque(maxlen=15)  # Store last 15 frames (~0.5s at 30fps)
confirmation_threshold = 10  # Need 10/15 frames to confirm
last_confirmed_gesture = None
gesture_hold_start = None

# Distance tracking for warnings
hand_distance_history = deque(maxlen=30)

# Terminal display update counter
display_counter = 0
last_status_print = 0

# ========== Helper Functions ==========
def calculate_distance(x1, y1, x2, y2):
    return math.hypot(x2 - x1, y2 - y1)

def get_hand_center(lmList):
    if len(lmList) == 0:
        return None, None
    x = sum([lm[1] for lm in lmList]) // len(lmList)
    y = sum([lm[2] for lm in lmList]) // len(lmList)
    return x, y

def estimate_hand_distance(lmList):
    """Estimate relative distance based on hand size in frame"""
    if len(lmList) == 0:
        return 0
    wrist = lmList[0]
    middle_tip = lmList[12]
    hand_size = calculate_distance(wrist[1], wrist[2], middle_tip[1], middle_tip[2])
    return hand_size

def get_distance_status(hand_size):
    """Return status: too_close, optimal, too_far"""
    if hand_size > 180:
        return "too_close"
    elif hand_size < 80:
        return "too_far"
    else:
        return "optimal"

def count_fingers(lmList):
    """Count extended fingers"""
    if len(lmList) == 0:
        return 0, []
    
    fingers = []
    
    # Thumb detection - compare thumb tip with thumb base
    thumb_tip_x = lmList[4][1]
    thumb_base_x = lmList[2][1]  # Thumb CMC joint
    wrist_x = lmList[0][1]
    
    # Thumb is extended if tip is far from base (horizontally)
    # Works for both left and right hand
    thumb_dist = abs(thumb_tip_x - thumb_base_x)
    if thumb_dist > 40:  # Thumb extended
        fingers.append(True)
    else:
        fingers.append(False)
    
    # Other fingers (check y-coordinate)
    for id in [8, 12, 16, 20]:
        if lmList[id][2] < lmList[id-2][2] - 15:  # Extended (fingertip higher than knuckle)
            fingers.append(True)
        else:
            fingers.append(False)
    
    return sum(fingers), fingers

def detect_gesture(lmList):
    """Detect gesture with confidence scoring"""
    if len(lmList) == 0:
        return None, 0
    
    center_x, center_y = get_hand_center(lmList)
    
    thumbX, thumbY = lmList[4][1], lmList[4][2]
    pointerX, pointerY = lmList[8][1], lmList[8][2]
    middleX, middleY = lmList[12][1], lmList[12][2]
    ringX, ringY = lmList[16][1], lmList[16][2]
    pinkyX, pinkyY = lmList[20][1], lmList[20][2]
    wristX, wristY = lmList[0][1], lmList[0][2]
    thumbBase = lmList[2]
    pointerBase = lmList[5]
    
    # Calculate distances
    dist_thumb_pointer = calculate_distance(thumbX, thumbY, pointerX, pointerY)
    dist_pointer_middle = calculate_distance(pointerX, pointerY, middleX, middleY)
    dist_middle_ring = calculate_distance(middleX, middleY, ringX, ringY)
    dist_ring_pinky = calculate_distance(ringX, ringY, pinkyX, pinkyY)
    
    # Count fingers for better detection
    finger_count, active_fingers = count_fingers(lmList)
    
    # NEXT/PREV TRACK - "7" gesture (thumb + index) - CHECK FIRST before fist/volume
    thumb_and_index = (active_fingers == [True, True, False, False, False])
    
    if thumb_and_index:
        pointer_dx = pointerX - wristX
        
        # Don't require thumb to be up - just check horizontal direction
        if pointer_dx > 60:  # Pointing RIGHT
            return "next_track", 0.85
        elif pointer_dx < -60:  # Pointing LEFT
            return "prev_track", 0.85
    
    # FIST detection - STRICT: require NO fingers extended
    # Just check if no fingers are extended
    if finger_count == 0:
        return "fist", 0.9
    
    # OPEN HAND detection - require ALL 5 fingers extended
    if finger_count == 5:
        return "open_hand", 0.9
    
    # VOLUME UP/DOWN - only index finger extended
    only_index = (active_fingers == [False, True, False, False, False])
    
    if only_index:
        pointer_base_y = lmList[5][2]  # Index finger base
        
        # Check if pointing UP or DOWN
        if pointerY < pointer_base_y - 80:  # Pointing clearly UP
            return "volume_up", 0.8
        elif pointerY > pointer_base_y - 20:  # Pointing clearly DOWN (relaxed)
            return "volume_down", 0.8
    
    return None, 0

def print_status(gesture, confidence, distance_status, fps, confirmation_progress):
    """Print status to terminal"""
    os.system('clear' if os.name == 'posix' else 'cls')
    
    print("=" * 70)
    print("GESTURE REMOTE CONTROL v2.0 - HEADLESS MODE")
    print("=" * 70)
    print()
    
    # Current gesture
    if gesture:
        print(f">> Current Gesture: {gesture.upper()} (Confidence: {confidence:.0%})")
    else:
        print(">> Current Gesture: None detected")
    
    # Confirmation progress
    if confirmation_progress > 0:
        bar_length = 40
        filled = int(bar_length * confirmation_progress)
        bar = "#" * filled + "-" * (bar_length - filled)
        print(f"[HOLD] Progress: [{bar}] {confirmation_progress:.0%}")
    
    print()
    
    # Distance status
    if distance_status == "optimal":
        print("[OK] Hand Distance: OPTIMAL")
    elif distance_status == "too_close":
        print("[WARN] Hand Distance: TOO CLOSE - Move back")
    elif distance_status == "too_far":
        print("[WARN] Hand Distance: TOO FAR - Move closer")
    else:
        print("[INFO] Hand Distance: No hand detected")
    
    print()
    print(f"[FPS] {int(fps)}")
    print(f"[NOW PLAYING] {current_song}")
    print()
    print("-" * 70)
    print("GESTURE CONTROLS:")
    print("-" * 70)
    print("Index UP (others down)        = Volume Up")
    print("Index DOWN (others down)      = Volume Down")
    print("7 -> (Index+Thumb right)      = Next Track")
    print("7 <- (Index+Thumb left)       = Previous Track")
    print("Fist (all fingers closed)     = Stop Music")
    print("Open Hand (all fingers open)  = Play Music")
    print("-" * 70)
    print("Press Ctrl+C to exit")
    print("=" * 70)

# ========== Main Loop ==========
print("\n" + "=" * 70)
print("Starting Gesture Remote Control v2.0 - Headless Mode")
print("=" * 70)
print("Features: Terminal feedback, gesture confirmation, no GUI needed")
print("=" * 70 + "\n")
time.sleep(2)

frame_count = 0

try:
    while True:
        success, img = cap.read()
        
        if not success or img is None:
            print("Error: Failed to read from camera")
            time.sleep(0.1)
            continue
        
        img = cv2.flip(img, 1)
        
        # Detect hands (no drawing needed for headless mode)
        img = detector.findHands(img, draw=False)
        lmList = detector.findPosition(img, draw=False)
        
        current_time = time.time()
        
        # Check if music track finished
        if audio_process and audio_process.poll() is not None:
            current_song = play_current_track()
        
        # Initialize status variables
        distance_status = "No hand detected"
        confirmed_gesture = None
        confidence = 0
        confirmation_progress = 0
        
        if len(lmList) != 0:
            # Calculate hand distance
            hand_size = estimate_hand_distance(lmList)
            hand_distance_history.append(hand_size)
            distance_status = get_distance_status(hand_size)
            
            # Detect gesture
            gesture, confidence = detect_gesture(lmList)
            
            # Add to gesture history for confirmation
            gesture_history.append(gesture)
            
            # Count occurrences of each gesture in history
            if gesture:
                gesture_count = gesture_history.count(gesture)
                confirmation_progress = min(gesture_count / confirmation_threshold, 1.0)
                
                # Confirm gesture if it appears enough times
                if gesture_count >= confirmation_threshold:
                    confirmed_gesture = gesture
                    
                    # Execute action only if cooldown passed
                    if current_time > gesture_cooldown:
                        
                        if confirmed_gesture == "fist":
                            current_gesture = "Stop Music (Fist)"
                            current_song = play_pause()
                            gesture_cooldown = current_time + cooldown_time
                            print(f"\n[OK] Confirmed: {confirmed_gesture}\n")
                        
                        elif confirmed_gesture == "open_hand":
                            current_gesture = "Play Music (Open Hand)"
                            current_song = play_pause()
                            gesture_cooldown = current_time + cooldown_time
                            print(f"\n[OK] Confirmed: {confirmed_gesture}\n")
                            
                        elif confirmed_gesture == "volume_up":
                            current_gesture = "Volume Up ^"
                            volume_up()
                            gesture_cooldown = current_time + 0.3
                            
                        elif confirmed_gesture == "volume_down":
                            current_gesture = "Volume Down v"
                            volume_down()
                            gesture_cooldown = current_time + 0.3
                            
                        elif confirmed_gesture == "next_track":
                            current_gesture = "Next Track >>"
                            current_song = next_track()
                            gesture_cooldown = current_time + cooldown_time
                            print(f"\n[OK] Confirmed: {confirmed_gesture}\n")
                            
                        elif confirmed_gesture == "prev_track":
                            current_gesture = "Previous Track <<"
                            current_song = previous_track()
                            gesture_cooldown = current_time + cooldown_time
                            print(f"\n[OK] Confirmed: {confirmed_gesture}\n")
        else:
            # No hand detected - clear history
            gesture_history.clear()
            prev_hand_center = None
        
        # Calculate FPS
        cTime = time.time()
        fps = 1 / (cTime - pTime) if (cTime - pTime) > 0 else 0
        pTime = cTime
        
        # Update terminal display every 10 frames (reduce flickering)
        frame_count += 1
        if frame_count % 10 == 0:
            if len(lmList) != 0:
                gesture_name = gesture if gesture else None
                print_status(gesture_name, confidence, distance_status, fps, confirmation_progress)

except KeyboardInterrupt:
    print("\n\n[STOP] Stopping Gesture Remote Control...")
    if audio_process:
        audio_process.terminate()
    cap.release()
    print("[OK] System terminated. Goodbye!\n")
