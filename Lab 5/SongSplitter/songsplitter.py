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

# Audio settings
BASE_VOL = 0.5        # unmuted volume (50%)
FIST_HOLD_TIME = 0.6  # seconds to hold fist to trigger skip
SKIP_COOLDOWN = 1.5   # minimum seconds between skips

# Initialize pygame mixer (pre-init optional if you need custom params)
pygame.mixer.init()
channels = {}
muted_states = {stem: True for stem in STEMS}

# State for fist debounce
fist_start_time = None
last_skip_time = 0.0

# ==== HELPER FUNCTIONS ====
def load_song(song_folder):
    """Load all stems for the given song and start them once (not looped)."""
    global channels
    print(f"Loading stems for: {song_folder}")
    # stop and clear any existing channels
    stop_all()
    channels.clear()

    for i, stem in enumerate(STEMS):
        path = os.path.join(song_folder, f"{stem}.mp3")
        if os.path.exists(path):
            try:
                sound = pygame.mixer.Sound(path)
            except Exception as e:
                print(f"Error loading {path}: {e}")
                continue
            ch = pygame.mixer.Channel(i)
            # play once so check_auto_next can detect end of song
            ch.play(sound, loops=0)
            ch.set_volume(0.0)  # start muted
            channels[stem] = ch
        else:
            print(f"Missing file: {path}")

def set_mute_state(stem, muted):
    """Mute or unmute a specific stem (set volume to BASE_VOL when unmuted)."""
    if stem in channels:
        volume = 0.0 if muted else BASE_VOL
        try:
            channels[stem].set_volume(volume)
            muted_states[stem] = muted
        except Exception as e:
            print(f"Error setting volume for {stem}: {e}")

def stop_all():
    """Stop all current sounds."""
    for ch in list(channels.values()):
        try:
            ch.stop()
        except Exception:
            pass

def next_song():
    """Advance to the next song and load it."""
    global current_index, current_song, fist_start_time, last_skip_time
    stop_all()
    current_index = (current_index + 1) % len(SONG_FOLDERS)
    current_song = SONG_FOLDERS[current_index]
    load_song(current_song)
    fist_start_time = None
    last_skip_time = time.time()
    print(f"Now playing: {current_song}")

def check_auto_next():
    """Auto-skip to next song when all stems have finished playing."""
    # if channels is empty or any channel is busy, do nothing
    if not channels:
        return
    if not any(ch.get_busy() for ch in channels.values()):
        # all channels finished => advance
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

try:
    while True:
        success, img = cap.read()
        if not success:
            # small sleep to avoid busy loop if camera fails
            time.sleep(0.01)
            continue

        img = detector.findHands(img)
        lmList = detector.findPosition(img, draw=False)

        # default: show current song title
        cv2.putText(img, f'{current_song}', (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

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

            # Muting logic: full plays only when open palm and mutes when any combo active
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
                # note: set_muted = True means muted; we want stem ON when finger is touching -> muted False
                set_mute_state("vocals", not (d_index < TOUCH_DIST))
                set_mute_state("drums", not (d_middle < TOUCH_DIST))
                set_mute_state("bass",  not (d_ring < TOUCH_DIST))
                set_mute_state("other", not (d_pinky < TOUCH_DIST))

            # Fist skip: require hold + cooldown
            now = time.time()
            if fist:
                if fist_start_time is None:
                    fist_start_time = now
                else:
                    # held long enough?
                    if (now - fist_start_time) >= FIST_HOLD_TIME and (now - last_skip_time) >= SKIP_COOLDOWN:
                        print("Fist held - skipping to next song.")
                        next_song()
                        # reset fist start to avoid double skip in same hold
                        fist_start_time = None
            else:
                fist_start_time = None

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
        cv2.putText(img, f'FPS: {int(fps)}', (500, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

        cv2.imshow("Song Splitter", img)

        # Auto-advance if song ended
        check_auto_next()

        if cv2.waitKey(1) & 0xFF == ord('q'):
            stop_all()
            break

finally:
    cap.release()
    cv2.destroyAllWindows()
    stop_all()
    pygame.mixer.quit()
