import cv2
import time
import math
import subprocess
import os
import HandTrackingModule as htm

# === CONFIG ===
SONG_FOLDERS = ["WWIMF", "AFFECTION", "BORDERLINE", "RIBS", "BACKTOBLACK"]
STEMS = ["full", "vocals", "drums", "bass", "other"]

current_index = 0
current_song = SONG_FOLDERS[current_index]
active_tracks = {}
muted_states = {stem: True for stem in STEMS}

# --- Helper functions ---

def song_path(stem):
    """Get full path to stem inside the current song folder."""
    return os.path.join(current_song, f"{stem}.mp3")

def play_song():
    """Start all stems of the current song (muted by default)."""
    global active_tracks
    stop_all_tracks()
    print(f"\nStarting: {current_song}")
    active_tracks = {}
    for stem in STEMS:
        path = song_path(stem)
        if os.path.exists(path):
            # Start each stem quietly (looped)
            process = subprocess.Popen(
                ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", path],
                stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            active_tracks[stem] = process
        else:
            print(f"Missing file: {path}")
    print("All stems launched.\n")

def stop_all_tracks():
    """Stop all currently playing stems."""
    for stem, proc in active_tracks.items():
        if proc and proc.poll() is None:
            proc.terminate()
    active_tracks.clear()

def next_song():
    """Skip to the next song folder."""
    global current_index, current_song
    stop_all_tracks()
    current_index = (current_index + 1) % len(SONG_FOLDERS)
    current_song = SONG_FOLDERS[current_index]
    play_song()

# --- Start the first song ---
play_song()

# --- Camera and hand tracking setup ---
wCam, hCam = 640, 480
cap = cv2.VideoCapture(0)
cap.set(3, wCam)
cap.set(4, hCam)
pTime = 0
detector = htm.handDetector(detectionCon=0.7)

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

        # Determine which stems should be audible
        if open_palm:
            # Only "full" audible
            muted_states = {stem: True for stem in STEMS}
            muted_states["full"] = False
        else:
            # Mute full if any other finger combo is active
            has_any_combo = (
                d_index < TOUCH_DIST or
                d_middle < TOUCH_DIST or
                d_ring < TOUCH_DIST or
                d_pinky < TOUCH_DIST
            )

            muted_states["full"] = has_any_combo
            muted_states["vocals"] = d_index >= TOUCH_DIST
            muted_states["drums"] = d_middle >= TOUCH_DIST
            muted_states["bass"]  = d_ring >= TOUCH_DIST
            muted_states["other"] = d_pinky >= TOUCH_DIST

        if fist:
            print("Fist detected, skipping to next song.")
            next_song()
            time.sleep(1)  # prevent rapid skips

        # Draw hand markers
        for id in [4, 8, 12, 16, 20]:
            cv2.circle(img, (lmList[id][1], lmList[id][2]), 10, (255, 0, 255), cv2.FILLED)

        cv2.putText(img, f'Now Playing: {current_song}', (20, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
import cv2
import time
import math
import os
import pygame
import HandTrackingModule as htm

# ==== CONFIGURATION ====
SONG_FOLDERS = ["Song1", "Song2", "Song3", "Song4", "Song5"]
STEMS = ["full", "vocals", "drums", "bass", "other"]

current_index = 0
current_song = SONG_FOLDERS[current_index]

# Initialize mixer
pygame.mixer.init()

# Keep track of stem channels
channels = {}
muted_states = {stem: True for stem in STEMS}

def load_song(song_folder):
    """Load all stems for the given song into mixer channels."""
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
    """Mute or unmute a specific stem."""
    if stem in channels:
        volume = 0.0 if muted else 1.0
        channels[stem].set_volume(volume)
        muted_states[stem] = muted

def stop_all():
    """Stop all sounds."""
    for ch in channels.values():
        ch.stop()

def next_song():
    """Switch to next song."""
    global current_index, current_song
    stop_all()
    current_index = (current_index + 1) % len(SONG_FOLDERS)
    current_song = SONG_FOLDERS[current_index]
    load_song(current_song)

# ==== Start first song ====
load_song(current_song)

# ==== Camera / hand tracking ====
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
            for s in STEMS:
                set_mute_state(s, True)
            set_mute_state("full", False)

        else:
            any_combo = (
                d_index < TOUCH_DIST or
                d_middle < TOUCH_DIST or
                d_ring < TOUCH_DIST or
                d_pinky < TOUCH_DIST
            )
            set_mute_state("full", any_combo)
            set_mute_state("vocals", d_index >= TOUCH_DIST)
            set_mute_state("drums", d_middle >= TOUCH_DIST)
            set_mute_state("bass",  d_ring >= TOUCH_DIST)
            set_mute_state("other", d_pinky >= TOUCH_DIST)

        if fist:
            print("Fist detected - skipping to next song.")
            next_song()
            time.sleep(1)

        for id in [4, 8, 12, 16, 20]:
            cv2.circle(img, (lmList[id][1], lmList[id][2]), 10, (255, 0, 255), cv2.FILLED)

        y = 100
        for stem, muted in muted_states.items():
            color = (0, 255, 0) if not muted else (0, 0, 255)
            status = "ON" if not muted else "OFF"
            cv2.putText(img, f'{stem.upper()}: {status}', (20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
            y += 35

    cTime = time.time()
    fps = 1 / (cTime - pTime + 0.0001)
    pTime = cTime
    cv2.putText(img, f'FPS: {int(fps)}', (500, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
    cv2.imshow("Song Splitter", img)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        stop_all()
        break

cap.release()
cv2.destroyAllWindows()

        # Display muted/unmuted states visually
        y0 = 100
        for stem, muted in muted_states.items():
            color = (0, 255, 0) if not muted else (0, 0, 255)
            status = "ON" if not muted else "OFF"
            cv2.putText(img, f'{stem.upper()}: {status}', (20, y0),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
            y0 += 35

    # FPS display
    cTime = time.time()
    fps = 1 / (cTime - pTime) if cTime != pTime else 0
    pTime = cTime
    cv2.putText(img, f'FPS: {int(fps)}', (500, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

    cv2.imshow("Song Splitter", img)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        stop_all_tracks()
        break

cap.release()
cv2.destroyAll
