"""
Gesture-Based Music Controller v2.0
Improved version based on Part C testing feedback

Key Improvements:
1. Visual feedback: Hand skeleton, finger highlights, distance warnings
2. Gesture confirmation: Requires holding gesture for 0.5s
3. Adaptive brightness adjustment
4. Better error recovery
5. Reduced false positives
"""

import cv2
import time
import numpy as np
import HandTrackingModule as htm
import math
import subprocess
from collections import deque

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
    print(f'Playing: {track_name}')
    return track_name

def play_pause():
    global audio_process
    if audio_process and audio_process.poll() is None:
        audio_process.terminate()
        audio_process = None
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
        print(f"Camera found at /dev/video{camera_id}")
        break
    cap.release()
else:
    print("Error: No camera found. Please check camera connection.")
    exit(1)

cap.set(cv2.CAP_PROP_FRAME_WIDTH, wCam)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, hCam)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

# ========== Initialize System ==========
set_volume(50)
current_song = play_current_track()

detector = htm.handDetector(detectionCon=0.7, minTrackCon=0.5)

# ========== Gesture State Variables ==========
gesture_cooldown = 0
cooldown_time = 1.0
current_gesture = "None"
prev_hand_center = None
pTime = 0

# NEW: Gesture confirmation system
gesture_history = deque(maxlen=15)  # Store last 15 frames (~0.5s at 30fps)
confirmation_threshold = 10  # Need 10/15 frames to confirm
last_confirmed_gesture = None
gesture_hold_start = None

# NEW: Distance tracking for warnings
hand_distance_history = deque(maxlen=30)

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
    # Use wrist to middle fingertip distance as reference
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

def adjust_brightness(img):
    """Auto-adjust brightness for low-light conditions"""
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    avg_brightness = np.mean(hsv[:, :, 2])
    
    if avg_brightness < 80:  # Low light
        hsv[:, :, 2] = cv2.add(hsv[:, :, 2], int(80 - avg_brightness))
        img = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
        return img, True
    return img, False

def draw_hand_skeleton(img, lmList):
    """Draw hand skeleton for visual feedback"""
    if len(lmList) == 0:
        return
    
    # Define hand connections
    connections = [
        (0, 1), (1, 2), (2, 3), (3, 4),  # Thumb
        (0, 5), (5, 6), (6, 7), (7, 8),  # Index
        (0, 9), (9, 10), (10, 11), (11, 12),  # Middle
        (0, 13), (13, 14), (14, 15), (15, 16),  # Ring
        (0, 17), (17, 18), (18, 19), (19, 20),  # Pinky
        (5, 9), (9, 13), (13, 17)  # Palm
    ]
    
    # Draw connections
    for connection in connections:
        x1, y1 = lmList[connection[0]][1], lmList[connection[0]][2]
        x2, y2 = lmList[connection[1]][1], lmList[connection[1]][2]
        cv2.line(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
    
    # Draw landmarks
    for lm in lmList:
        cv2.circle(img, (lm[1], lm[2]), 5, (255, 0, 255), cv2.FILLED)

def highlight_active_fingers(img, lmList, active_fingers):
    """Highlight fingers that are detected as extended"""
    if len(lmList) == 0:
        return
    
    finger_tips = [4, 8, 12, 16, 20]  # Thumb, Index, Middle, Ring, Pinky
    for i, tip_id in enumerate(finger_tips):
        if i < len(active_fingers) and active_fingers[i]:
            x, y = lmList[tip_id][1], lmList[tip_id][2]
            cv2.circle(img, (x, y), 15, (0, 255, 255), 3)

def count_fingers(lmList):
    """Count extended fingers"""
    if len(lmList) == 0:
        return 0, []
    
    fingers = []
    
    # Thumb (check x-coordinate)
    if lmList[4][1] < lmList[3][1]:
        fingers.append(True)
    else:
        fingers.append(False)
    
    # Other fingers (check y-coordinate)
    for id in [8, 12, 16, 20]:
        if lmList[id][2] < lmList[id-2][2]:
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
    
    # Improved FIST detection
    all_fingers_close = (dist_thumb_pointer < 50 and 
                         dist_pointer_middle < 30 and 
                         dist_middle_ring < 30 and 
                         dist_ring_pinky < 30 and
                         finger_count == 0)
    
    if all_fingers_close:
        return "fist", 0.9
    
    # Improved OPEN HAND detection
    all_fingers_open = (dist_thumb_pointer > 80 and 
                        dist_pointer_middle > 50 and 
                        dist_middle_ring > 50 and 
                        dist_ring_pinky > 50 and
                        finger_count >= 4)
    
    if all_fingers_open:
        return "open_hand", 0.9
    
    # VOLUME UP/DOWN - only index finger extended
    only_index = (active_fingers == [False, True, False, False, False])
    
    if only_index:
        pointer_dy = pointerY - wristY
        
        # More distinct threshold to avoid confusion
        if pointer_dy < -60:  # Pointing clearly UP
            return "volume_up", 0.8
        elif pointer_dy > -10:  # Pointing clearly DOWN
            return "volume_down", 0.8
    
    # NEXT/PREV TRACK - "7" gesture (thumb + index)
    thumb_and_index = (active_fingers == [True, True, False, False, False])
    
    if thumb_and_index:
        pointer_dx = pointerX - wristX
        thumb_dy = thumbY - wristY
        
        thumb_up = thumb_dy < -20
        
        if pointer_dx > 60 and thumb_up:  # Clearly pointing RIGHT
            return "next_track", 0.85
        elif pointer_dx < -60 and thumb_up:  # Clearly pointing LEFT
            return "prev_track", 0.85
    
    return None, 0

# ========== Main Loop ==========
print("Starting Gesture Remote Control v2.0")
print("Improvements: Visual feedback, gesture confirmation, adaptive lighting")

while True:
    success, img = cap.read()
    
    if not success or img is None:
        print("Error: Failed to read from camera")
        time.sleep(0.1)
        continue
    
    img = cv2.flip(img, 1)
    
    # Auto-adjust brightness
    img, brightness_adjusted = adjust_brightness(img)
    
    # Detect hands
    img = detector.findHands(img, draw=False)  # We'll draw custom skeleton
    lmList = detector.findPosition(img, draw=False)
    
    current_time = time.time()
    
    # Check if music track finished
    if audio_process and audio_process.poll() is not None:
        current_song = play_current_track()
    
    # Initialize status variables
    distance_status = "No hand detected"
    confirmed_gesture = None
    confidence = 0
    
    if len(lmList) != 0:
        # Draw hand skeleton for feedback
        draw_hand_skeleton(img, lmList)
        
        # Calculate and track hand distance
        hand_size = estimate_hand_distance(lmList)
        hand_distance_history.append(hand_size)
        distance_status = get_distance_status(hand_size)
        
        # Highlight active fingers
        _, active_fingers = count_fingers(lmList)
        highlight_active_fingers(img, lmList, active_fingers)
        
        # Detect gesture
        gesture, confidence = detect_gesture(lmList)
        
        # Add to gesture history for confirmation
        gesture_history.append(gesture)
        
        # Count occurrences of each gesture in history
        if gesture:
            gesture_count = gesture_history.count(gesture)
            
            # Confirm gesture if it appears enough times
            if gesture_count >= confirmation_threshold:
                confirmed_gesture = gesture
                
                # Execute action only if cooldown passed
                if current_time > gesture_cooldown:
                    
                    if confirmed_gesture == "fist":
                        current_gesture = "Stop Music (Fist)"
                        current_song = play_pause()
                        gesture_cooldown = current_time + cooldown_time
                        print(f"✓ Confirmed: {confirmed_gesture}")
                    
                    elif confirmed_gesture == "open_hand":
                        current_gesture = "Play Music (Open Hand)"
                        current_song = play_pause()
                        gesture_cooldown = current_time + cooldown_time
                        print(f"✓ Confirmed: {confirmed_gesture}")
                        
                    elif confirmed_gesture == "volume_up":
                        current_gesture = "Volume Up ↑"
                        volume_up()
                        gesture_cooldown = current_time + 0.3
                        
                    elif confirmed_gesture == "volume_down":
                        current_gesture = "Volume Down ↓"
                        volume_down()
                        gesture_cooldown = current_time + 0.3
                        
                    elif confirmed_gesture == "next_track":
                        current_gesture = "Next Track ⏭"
                        current_song = next_track()
                        gesture_cooldown = current_time + cooldown_time
                        print(f"✓ Confirmed: {confirmed_gesture}")
                        
                    elif confirmed_gesture == "prev_track":
                        current_gesture = "Previous Track ⏮"
                        current_song = previous_track()
                        gesture_cooldown = current_time + cooldown_time
                        print(f"✓ Confirmed: {confirmed_gesture}")
    else:
        # No hand detected - clear history
        gesture_history.clear()
        prev_hand_center = None
    
    # ========== UI Drawing ==========
    
    # Top status bar (darker, more visible)
    cv2.rectangle(img, (10, 10), (630, 140), (20, 20, 20), -1)
    cv2.rectangle(img, (10, 10), (630, 140), (0, 255, 0), 2)
    
    # Current gesture and confidence
    gesture_color = (0, 255, 0) if confidence > 0.7 else (0, 255, 255)
    cv2.putText(img, f'Gesture: {current_gesture}', (20, 50), 
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, gesture_color, 3)
    
    # Confirmation progress bar
    if len(gesture_history) > 0 and gesture_history[-1]:
        confirmation_progress = gesture_history.count(gesture_history[-1]) / confirmation_threshold
        bar_width = int(600 * confirmation_progress)
        cv2.rectangle(img, (15, 60), (15 + bar_width, 75), (0, 255, 255), -1)
        cv2.putText(img, f'Hold: {int(confirmation_progress*100)}%', (20, 95), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
    # Current track
    cv2.putText(img, f'Track: {current_song[:35]}', (20, 125), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
    
    # Distance warning
    warning_color = (0, 255, 0) if distance_status == "optimal" else (0, 165, 255)
    if distance_status == "too_close":
        warning_text = "⚠ Hand too close - move back"
        warning_color = (0, 0, 255)
    elif distance_status == "too_far":
        warning_text = "⚠ Hand too far - move closer"
        warning_color = (0, 165, 255)
    else:
        warning_text = "✓ Hand distance optimal"
    
    cv2.rectangle(img, (10, 150), (630, 185), (40, 40, 40), -1)
    cv2.putText(img, warning_text, (20, 175), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, warning_color, 2)
    
    # Brightness adjustment indicator
    if brightness_adjusted:
        cv2.putText(img, '💡 Low light - auto-adjusted', (20, 205), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 200, 255), 2)
    
    # Instructions panel
    cv2.rectangle(img, (10, 220), (630, 410), (50, 50, 50), -1)
    cv2.putText(img, 'Gesture Controls:', (20, 245), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
    cv2.putText(img, 'Index ↑ (others down) = Vol+', (30, 270), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    cv2.putText(img, 'Index ↓ (others down) = Vol-', (30, 295), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    cv2.putText(img, '7 → (Index+Thumb right) = Next', (30, 320), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    cv2.putText(img, '7 ← (Index+Thumb left) = Prev', (30, 345), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    cv2.putText(img, 'Fist (all fingers closed) = Stop', (30, 370), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    cv2.putText(img, 'Open Hand (all fingers open) = Play', (30, 395), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    # FPS counter
    cTime = time.time()
    fps = 1 / (cTime - pTime) if (cTime - pTime) > 0 else 0
    pTime = cTime
    cv2.putText(img, f'FPS: {int(fps)}', (20, 435), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
    
    # Show version
    cv2.putText(img, 'v2.0 - Improved', (520, 435), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)

    cv2.imshow("Gesture Remote Control v2.0", img)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        if audio_process:
            audio_process.terminate()
        break

cap.release()
cv2.destroyAllWindows()
print("System terminated. Goodbye!")
