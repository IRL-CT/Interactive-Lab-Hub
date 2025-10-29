import cv2
import time
import math
import os
import pygame
import HandTrackingModule as htm

# ==== CONFIG ====
SONG_FOLDERS = ["WWIMF", "AFFECTION", "BORDERLINE", "RIBS", "BACKTOBLACK"]
STEMS = ["full", "vocals", "drums", "bass", "other"]

current_index = 0
current_song = SONG_FOLDERS[current_index]

# Initialize pygame mixer
pygame.mixer.init()
channels = {}
muted_states = {stem: True for stem in STEMS}

# ==== HELPER FUNCTIONS ====
def load_song(song_folder):
    """Load all stems for the given song and start them (looped)."""
    global channels
    print(f"Loading stems for: {song_folder}")
    channels.clear()
    for i, stem in enumerate(STEMS):
        path = os.path.join(song_folder, f"{stem}.mp3")
        if os.path.exists(path):
            sound = pygame.mixer.Sound(path)
            ch = pygame.mixer.Channel(i)
            ch.play(sound, loops=-1)
            ch.set_volume(0.0)
            channels[stem] = ch
        else:
            print(f"Missing file: {path}")

def set_mute_state(stem, muted):
    """Mute or unmute specific stem."""
    if stem in channels:
        volume = 0.0 if muted else 1.0
        channels[stem].set_volume(volume)
        muted_states[stem] = muted

def stop_all():
    """Stop all current sounds."""
    for ch in channels.values():
        ch.stop()

def next_song():
    """Advance to the next song."""
    global current_index, current_song
    stop_all()
    current_index = (current_index + 1) % len(SONG_FOLDERS)
    current_song = SONG_FOLDERS[current_index]
    load_song(current_song)
    print(f"Now playing: {current_song}")

def check_auto_next():
    """Auto-skip to the next song if all stems stop (song finished)."""
    if not any(ch.get_busy() for ch in channels.values()):
        next_song()

# ==== START FIRST SONG ====
load_song(current_song)

# ==== CAMERA + HAND TRACKING ====
cap = cv2.VideoCapture(0)
cap.set(3, 640)
cap.set(4, 480)
detector = htm.handDetector(detectionCon=0.7)
pTime = 0

def distance(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])

while True:
    success, img = cap.read()
    img = detector.findHands(img)
    lmList = detector.findPosition(img, draw=False)

    if len(lmList) != 0:
        thumb = lmList[4][1:3]
        index = lmList[8][1:3]
        middle = lmList[12][1:3]
        ring = lmList[16][1:3]
        pinky = lmList[20][1:3]

        d_index = distance(thumb, index)
        d_middle = distance(thumb, middle)
        d_ring = distance(thumb, ring)
        d_pinky = distance(thumb, pinky)

        TOUCH_DIST = 40
        OPEN_DIST = 100
        FIST_DIST = 50

        open_palm = all(d > OPEN_DIST for d in [d_index, d_middle, d_ring, d_pinky])
        fist = all(d < FIST_DIST for d in [d_index, d_middle, d_ring, d_pinky])

        if open_palm:
            # Only "full" audible
            for s in STEMS:
                set_mute_state(s, True)
            set_mute_state("full", False)
        else:
            # Mute full when any other combo is active
            any_combo = (
                d_index < TOUCH_DIST or
                d_middle < TOUCH_DIST or
                d_ring < TOUCH_DIST or
                d_pinky < TOUCH_DIST
            )
            set_mute_state("full", any_combo)
            set_mute_state("vocals", d_index >= TOUCH_DIST)
            set_mute_state("drums", d_middle >= TOUCH_DIST)
            set_mute_state("bass", d_ring >= TOUCH_DIST)
            set_mute_state("other", d_pinky >= TOUCH_DIST)

        if fist:
            print("Fist detected - skipping to next song.")
            next_song()
            time.sleep(1)

        # Draw finger markers
        for id in [4, 8, 12, 16, 20]:
            cv2.circle(img, (lmList[id][1], lmList[id][2]), 10, (255, 0, 255), cv2.FILLED)

        # Display mute/unmute states
        y = 100
        for stem, muted in muted_states.items():
            color = (0, 255, 0) if not muted else (0, 0, 255)
            status = "ON" if not muted else "OFF"
            cv2.putText(img, f'{stem.upper()}: {status}', (20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
            y += 35

    # FPS display
    cTime = time.time()
    fps = 1 / (cTime - pTime + 0.0001)
    pTime = cTime
    cv2.putText(img, f'{current_song}', (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    cv2.putText(img, f'FPS: {int(fps)}', (500, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

    cv2.imshow("Song Splitter", img)

    check_auto_next()

    if cv2.waitKey(1) & 0xFF == ord('q'):
        stop_all()
        break

cap.release()
cv2.destroyAllWindows()
