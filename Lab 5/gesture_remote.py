import cv2
import time
import numpy as np
import HandTrackingModule as htm
import math
import subprocess

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
    else:
        play_current_track()

def next_track():
    global current_track
    current_track = (current_track + 1) % len(music_files)
    return play_current_track()

def previous_track():
    global current_track
    current_track = (current_track - 1) % len(music_files)
    return play_current_track()

set_volume(50)
current_song = play_current_track()

wCam, hCam = 640, 480

for camera_id in [0, 1, 2]:
    cap = cv2.VideoCapture(camera_id)
    if cap.isOpened():
        print(f"Camera found at /dev/video{camera_id}")
        break
    cap.release()
else:
    print("Error: No camera found. Please check camera connection.")
    audio_process.terminate()
    exit(1)

cap.set(cv2.CAP_PROP_FRAME_WIDTH, wCam)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, hCam)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
pTime = 0

detector = htm.handDetector(detectionCon=int(0.7))

gesture_cooldown = 0
cooldown_time = 1.0
current_gesture = "None"
current_song = ""
prev_hand_center = None

def is_finger_extended(lmList, finger_tip, finger_pip):
    if len(lmList) == 0:
        return False
    tip_y = lmList[finger_tip][2]
    pip_y = lmList[finger_pip][2]
    return tip_y < pip_y - 15

def count_fingers(lmList):
    if len(lmList) == 0:
        return 0, []
    
    fingers = []
    
    # Thumb detection - use distance
    thumb_tip_x = lmList[4][1]
    thumb_base_x = lmList[2][1]
    thumb_dist = abs(thumb_tip_x - thumb_base_x)
    fingers.append(thumb_dist > 40)
    
    # Other fingers - check if tip is above knuckle
    for id in [8, 12, 16, 20]:
        fingers.append(lmList[id][2] < lmList[id-2][2] - 15)
    
    return sum(fingers), fingers

def is_fist(lmList):
    count, _ = count_fingers(lmList)
    return count == 0

def get_hand_center(lmList):
    if len(lmList) == 0:
        return None, None
    x = sum([lm[1] for lm in lmList]) // len(lmList)
    y = sum([lm[2] for lm in lmList]) // len(lmList)
    return x, y

def calculate_distance(x1, y1, x2, y2):
    return math.hypot(x2 - x1, y2 - y1)

def get_finger_angle(point1, point2):
    dx = point2[0] - point1[0]
    dy = point2[1] - point1[1]
    angle = math.degrees(math.atan2(dy, dx))
    return angle

def detect_gesture(lmList, prev_center):
    if len(lmList) == 0:
        return None, None
    
    center_x, center_y = get_hand_center(lmList)
    
    thumbX, thumbY = lmList[4][1], lmList[4][2]
    pointerX, pointerY = lmList[8][1], lmList[8][2]
    middleX, middleY = lmList[12][1], lmList[12][2]
    ringX, ringY = lmList[16][1], lmList[16][2]
    pinkyX, pinkyY = lmList[20][1], lmList[20][2]
    wristX, wristY = lmList[0][1], lmList[0][2]
    pointerBase = lmList[5]
    
    # Get finger states
    finger_count, active_fingers = count_fingers(lmList)
    
    # PRIORITY 1: "7" gesture (thumb + index) - CHECK FIRST to avoid false fist detection
    thumb_and_index = (active_fingers == [True, True, False, False, False])
    
    if thumb_and_index:
        pointer_dx = pointerX - wristX
        
        # Just check horizontal direction - don't require thumb position
        if pointer_dx > 60:  # Pointing RIGHT
            return "next_track", (center_x, center_y)
        elif pointer_dx < -60:  # Pointing LEFT
            return "prev_track", (center_x, center_y)
    
    # PRIORITY 2: Fist - all fingers closed
    if finger_count == 0:
        return "fist", (center_x, center_y)
    
    # PRIORITY 3: Open hand - all fingers extended
    if finger_count == 5:
        return "open_hand", (center_x, center_y)
    
    # PRIORITY 4: Volume control - only index finger extended
    only_index = (active_fingers == [False, True, False, False, False])
    
    if only_index:
        pointer_base_y = pointerBase[2]
        
        # Check if pointing UP or DOWN relative to base
        if pointerY < pointer_base_y - 80:  # Pointing UP
            return "volume_up", (center_x, center_y)
        elif pointerY > pointer_base_y - 20:  # Pointing DOWN (relaxed threshold)
            return "volume_down", (center_x, center_y)
    
    return None, (center_x, center_y)

while True:
    success, img = cap.read()
    
    if not success or img is None:
        print("Error: Failed to read from camera")
        time.sleep(0.1)
        continue
    
    img = cv2.flip(img, 1)
    img = detector.findHands(img)
    lmList = detector.findPosition(img, draw=False)
    
    current_time = time.time()
    
    if audio_process and audio_process.poll() is not None:
        current_song = play_current_track()
    
    if len(lmList) != 0:
        
        gesture, new_center = detect_gesture(lmList, prev_hand_center)
        prev_hand_center = new_center
        
        if gesture and current_time > gesture_cooldown:
            
            if gesture == "fist":
                current_gesture = "Stop Music (Fist)"
                play_pause()
                gesture_cooldown = current_time + cooldown_time
            
            elif gesture == "open_hand":
                current_gesture = "Play Music (Open Hand)"
                play_pause()
                gesture_cooldown = current_time + cooldown_time
                
            elif gesture == "volume_up":
                current_gesture = "Volume Up (Index Only Up)"
                volume_up()
                gesture_cooldown = current_time + 0.3
                
            elif gesture == "volume_down":
                current_gesture = "Volume Down (Index Only Down)"
                volume_down()
                gesture_cooldown = current_time + 0.3
                
            elif gesture == "next_track":
                current_gesture = "Next Track (7 Right)"
                current_song = next_track()
                gesture_cooldown = current_time + cooldown_time
                
            elif gesture == "prev_track":
                current_gesture = "Previous Track (7 Left)"
                current_song = previous_track()
                gesture_cooldown = current_time + cooldown_time
    else:
        prev_hand_center = None
    
    cv2.rectangle(img, (10, 10), (630, 120), (0, 0, 0), -1)
    cv2.putText(img, f'Gesture: {current_gesture}', (20, 50), 
                cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)
    cv2.putText(img, f'Track: {current_song[:40]}', (20, 100), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
    
    cv2.rectangle(img, (10, 130), (630, 290), (50, 50, 50), -1)
    cv2.putText(img, 'Only Index Up (others folded) = Vol+', (20, 160), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)
    cv2.putText(img, 'Only Index Down (others folded) = Vol-', (20, 190), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)
    cv2.putText(img, '7 Right (Index right + Thumb up) = Next', (20, 220), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)
    cv2.putText(img, '7 Left (Index left + Thumb up) = Prev', (20, 250), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)
    cv2.putText(img, 'Fist = Stop  |  Open Hand = Play', (20, 280), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)
    
    cTime = time.time()
    fps = 1 / (cTime - pTime)
    pTime = cTime
    cv2.putText(img, f'FPS: {int(fps)}', (20, 320), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)

    cv2.imshow("Gesture Remote Control", img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        if audio_process:
            audio_process.terminate()
        break

cap.release()
cv2.destroyAllWindows()
