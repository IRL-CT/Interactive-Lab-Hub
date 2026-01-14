import cv2
import time
import HandTrackingModule as htm
import math
import sys

# --- Configuration ---
wCam, hCam = 640, 480
# Center of the hand (based on typical hand detection frame)
CENTER_X = wCam // 2
CENTER_Y = hCam // 2
# Thresholds for direction detection (adjust these based on testing)
X_THRESHOLD = 50
Y_THRESHOLD = 50
# ---------------------

def get_direction(lmList):
    """
    Analyzes the position of the index finger (landmark 8)
    relative to the camera's center to determine pointing direction.
    """
    # Index finger tip is landmark 8
    _, pointerX, pointerY = lmList[8]

    # Calculate position relative to the center of the frame
    diff_x = pointerX - CENTER_X
    diff_y = pointerY - CENTER_Y

    # --- Direction Logic ---
    # Check for left/right (X-axis)
    if diff_x > X_THRESHOLD:
        horizontal = "RIGHT"
    elif diff_x < -X_THRESHOLD:
        horizontal = "LEFT"
    else:
        horizontal = ""

    # Check for up/down (Y-axis - Note: Y-axis is inverted in OpenCV)
    if diff_y < -Y_THRESHOLD:
        vertical = "UP"  # Lower Y-value is visually higher
    elif diff_y > Y_THRESHOLD:
        vertical = "DOWN"
    else:
        vertical = ""

    # Combine directions (e.g., "UP-LEFT", or just "UP")
    if horizontal and vertical:
        return f"{vertical}-{horizontal}"
    elif horizontal:
        return horizontal
    elif vertical:
        return vertical
    else:
        return "CENTER/NEUTRAL"

# --- Main Program ---
def run_gesture_detector():
    """Initializes camera and runs the detection loop."""
    # Remove all cv2 window and audio control calls
    # The original script had audio-related imports and functions. These are removed.

    cap = cv2.VideoCapture(0)
    cap.set(3, wCam)
    cap.set(4, hCam)

    # Exit if camera is not opened
    if not cap.isOpened():
        print("[ERROR] Could not open video stream or file.")
        sys.exit(1)

    detector = htm.handDetector(detectionCon=0.7)
    
    pTime = 0
    current_direction = "NO HAND DETECTED"
    
    print("--- Gesture Direction Detector Started ---")
    print("Press Ctrl+C to stop the script.")
    
    try:
        while True:
            success, img = cap.read()
            if not success:
                print("[WARNING] Ignoring empty camera frame.")
                time.sleep(0.1)
                continue

            img = detector.findHands(img, draw=False) # No drawing
            lmList = detector.findPosition(img, draw=False)
            
            new_direction = "NO HAND DETECTED"
            
            if len(lmList) != 0:
                new_direction = get_direction(lmList)

            # Only print when the direction changes
            if new_direction != current_direction:
                current_direction = new_direction
                
                # Calculate FPS for monitoring performance
                cTime = time.time()
                fps = 1 / (cTime - pTime) if pTime else 0
                pTime = cTime
                
                print(f"[{time.strftime('%H:%M:%S')}] FPS: {int(fps):<3} | Direction: {current_direction}")
            
            time.sleep(0.05) # Small sleep to prevent 100% CPU usage

    except KeyboardInterrupt:
        print("\n--- Script stopped by user (Ctrl+C) ---")
    finally:
        cap.release()
        # No cv2.destroyAllWindows() needed as no windows were opened

if __name__ == '__main__':
    run_gesture_detector()