# mqtt_musicbox.py

import json
import time
import random
import paho.mqtt.client as mqtt

import os
import subprocess

# -------------------------
# Configuration
# -------------------------

BROKER_IP = "localhost"          # Pi talks to broker locally
BROKER_PORT = 1883
TOPIC_GENRE_REQUEST = "musicbox/genre/request"
TOPIC_STATUS = "musicbox/song/status"
TOPIC_ERROR = "musicbox/error"

# Year groups (decades) and genres
YEAR_GROUPS = [1950, 1960, 1970, 1980, 1990, 2000, 2010, 2020]
GENRES = ["chill", "energetic", "warm", "party"]
NUM_SONGS_PER_GENRE = 3          # 01, 02, 03
DEFAULT_GENRE = "chill"
DEFAULT_YEAR_GROUP = 1950

# Build SONG_MAP[year][genre] -> list of filenames
# e.g. SONG_MAP[1950]["chill"] = [
#   "1950_chill_01.mp3", "1950_chill_02.mp3", "1950_chill_03.mp3"
# ]
SONG_MAP: dict[int, dict[str, list[str]]] = {}
for year in YEAR_GROUPS:
    SONG_MAP[year] = {}
    for g in GENRES:
        SONG_MAP[year][g] = [
            f"{year}_{g}_{i:02d}.mp3" for i in range(1, NUM_SONGS_PER_GENRE + 1)
        ]

# variables
current_process: subprocess.Popen | None = None
last_request_user: str = ""

# -------------------------
# Audio
# -------------------------

MUSIC_DIR = "./music/"

def set_volume(volume: float):
    """
    volume: 0.0 to 1.0
    """
    percent = int(max(0.0, min(1.0, volume)) * 100)
    print(f"[AUDIO] Setting volume to {percent}%")
    subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{percent}%"])

def stop_current_song():
    global current_process

    if current_process is not None:
        if current_process.poll() is None:
            print("[AUDIO] Stopping current song...")
            try:
                current_process.terminate()
                current_process.wait(timeout=2)
            except Exception as e:
                print(f"[AUDIO] Error while terminating, killing process: {e}")
                try:
                    current_process.kill()
                except Exception as e2:
                    print(f"[AUDIO] Error while killing process: {e2}")
        current_process = None

def play_song(filename: str, volume: float | None = None):
    """
    Play an MP3 file through the default audio output.
    If another song is currently playing, stop it first.
    """
    global current_process

    song_path = os.path.join(MUSIC_DIR, filename)
    print(f"[AUDIO] Request to play: {song_path}, volume={volume}")

    # 1. Stop whatever is currently playing
    stop_current_song()

    # 2. Optionally set volume
    if volume is not None:
        set_volume(volume)

    # 3. Start new song in background
    try:
        current_process = subprocess.Popen(
            ["mpg123", "-q", song_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        print("[AUDIO] Now playing.")
    except Exception as e:
        print(f"[AUDIO ERROR] Could not play {song_path}: {e}")
        current_process = None

def play_fallback_playlist():
    """
    Fallback: randomly select year + DEFAULT_GENRE and play one of its songs.
    """
    print("[FALLBACK] Playing fallback playlist...")
    year = random.choice(YEAR_GROUPS)
    songs = SONG_MAP[year][DEFAULT_GENRE]
    song = random.choice(songs)
    play_song(song)

def speak(text: str):
    print(f"Pi says: {text}")
    subprocess.run(["espeak", "-s", "165", text])

def publish_status(client: mqtt.Client, status: dict):
    payload = json.dumps(status)
    client.publish(TOPIC_STATUS, payload)

def publish_error(client: mqtt.Client, message: str, raw_payload: bytes | None = None):
    error = {
        "error": message,
        "raw_payload": raw_payload.decode("utf-8", errors="ignore") if raw_payload else None,
        "timestamp": int(time.time()),
    }
    client.publish(TOPIC_ERROR, json.dumps(error))
    print("[ERROR]", message)

# -------------------------
# MQTT Handlers
# -------------------------

def handle_genre_request(client: mqtt.Client, data: dict):
    """
    Expected payload:
    {
      "type": "genre_request",
      "client_id": "Jessica",
      "genre": "chill",
      "year": 1950,          # decade group; must be one of YEAR_GROUPS
      "volume": 0.8,         # optional (0.0 - 1.0)
      "timestamp": 1733018912
    }
    """
    global last_request_user

    req_type = data.get("type")
    if req_type != "genre_request":
        print(f"[MQTT] Ignoring message with type={req_type}")
        return

    genre = (data.get("genre") or "").lower()
    if genre not in GENRES:
        print(f"[MQTT] Unknown genre '{genre}', using fallback playlist.")
        play_fallback_playlist()
        publish_status(client, {
            "status": "fallback_unknown_genre",
            "requested_genre": genre,
            "timestamp": int(time.time()),
        })
        return

    # Year/decade handling
    year = data.get("year")
    try:
        year = int(year)
    except (TypeError, ValueError):
        print(f"[MQTT] Invalid or missing year '{year}', using default {DEFAULT_YEAR_GROUP}.")
        year = DEFAULT_YEAR_GROUP

    if year not in YEAR_GROUPS:
        print(f"[MQTT] Year {year} not in allowed groups, using default {DEFAULT_YEAR_GROUP}.")
        year = DEFAULT_YEAR_GROUP

    client_id = data.get("client_id") or "unknown"
    volume = data.get("volume")    # may be None
    ts = data.get("timestamp", int(time.time()))

    last_request_user = client_id

    # Select random song from SONG_MAP[year][genre]
    songs = SONG_MAP[year][genre]
    song = random.choice(songs)

    print(
        f"[MQTT] Genre request from {client_id} at {ts}: "
        f"year={year}, genre={genre}, song={song}, volume={volume}"
    )
    play_song(song, volume)

    publish_status(client, {
        "status": "playing",
        "year": year,
        "genre": genre,
        "song": song,
        "client_id": client_id,
        "volume": volume,
        "timestamp": ts,
    })

def on_connect(client, userdata, flags, rc):
    print("[MQTT] Connected with result code", rc)
    client.subscribe(TOPIC_GENRE_REQUEST)
    print(f"[MQTT] Subscribed to {TOPIC_GENRE_REQUEST}")

def on_message(client, userdata, msg):
    print(f"[MQTT] Message received on {msg.topic}: {msg.payload}")

    if msg.topic != TOPIC_GENRE_REQUEST:
        print("[MQTT] Topic not handled, ignoring.")
        return

    try:
        data = json.loads(msg.payload.decode("utf-8"))
    except json.JSONDecodeError:
        publish_error(client, "Invalid JSON payload", msg.payload)
        play_fallback_playlist()
        return

    try:
        handle_genre_request(client, data)
    except Exception as e:
        publish_error(client, f"Exception while handling genre request: {e}", msg.payload)
        play_fallback_playlist()

# -------------------------
# Entry point
# -------------------------

def start_mqtt_loop():
    client = mqtt.Client(client_id="musicbox_pi")
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(BROKER_IP, BROKER_PORT, 60)
    print("[MQTT] Starting loop_forever()...")
    client.loop_forever()

if __name__ == "__main__":
    start_mqtt_loop()
