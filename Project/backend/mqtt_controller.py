# mqtt_controller.py
"""
MQTTController: handles MQTT messages and controls the AudioEngine.

Listens to:
  - musicbox/genre/request

Publishes:
  - musicbox/song/status
  - musicbox/error
"""

from __future__ import annotations

import json
import time
from typing import Optional

import paho.mqtt.client as mqtt

from audio_engine import AudioEngine, YEAR_GROUPS, GENRES

BROKER_IP = "localhost"
BROKER_PORT = 1883

TOPIC_GENRE_REQUEST = "musicbox/genre/request"
TOPIC_STATUS = "musicbox/song/status"
TOPIC_ERROR = "musicbox/error"


class MQTTController:
    def __init__(
        self,
        engine: AudioEngine,
        broker_ip: str = BROKER_IP,
        broker_port: int = BROKER_PORT,
    ) -> None:
        self.engine = engine
        self.broker_ip = broker_ip
        self.broker_port = broker_port

        self.client = mqtt.Client(client_id="musicbox_pi")
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message

    # ---------- Public API ----------

    def start(self) -> None:
        """Connect and start the MQTT loop in a background thread."""
        self.client.connect(self.broker_ip, self.broker_port, 60)
        print(f"[MQTT] Connected to {self.broker_ip}:{self.broker_port}")
        self.client.loop_start()

    def stop(self) -> None:
        """Stop the MQTT loop."""
        self.client.loop_stop()
        self.client.disconnect()
        print("[MQTT] Disconnected")

    # ---------- Internal helpers ----------

    def _publish_status(self, extra: Optional[dict] = None) -> None:
        payload = self.engine.get_status()
        if extra:
            payload.update(extra)
        payload["timestamp"] = int(time.time())
        self.client.publish(TOPIC_STATUS, json.dumps(payload))

    def _publish_error(self, message: str, raw_payload: Optional[bytes] = None) -> None:
        error = {
            "error": message,
            "raw_payload": raw_payload.decode("utf-8", errors="ignore") if raw_payload else None,
            "timestamp": int(time.time()),
        }
        print("[MQTT ERROR]", message)
        self.client.publish(TOPIC_ERROR, json.dumps(error))

    def _handle_genre_request(self, data: dict) -> None:
        """
        Expected payload:
        {
          "type": "genre_request",
          "client_id": "Jessica",
          "genre": "chill",
          "year": 1950,
          "volume": 0.8,
          "timestamp": 1733018912
        }
        """
        if data.get("type") != "genre_request":
            print(f"[MQTT] Ignoring message with type={data.get('type')}")
            return

        client_id = data.get("client_id") or "unknown"

        # Year
        year = data.get("year")
        try:
            year = int(year)
        except (TypeError, ValueError):
            print(f"[MQTT] Invalid or missing year '{year}', using default {YEAR_GROUPS[0]}")
            year = YEAR_GROUPS[0]

        if year not in YEAR_GROUPS:
            print(f"[MQTT] Year {year} not allowed, using {YEAR_GROUPS[0]}")
            year = YEAR_GROUPS[0]

        # Genre
        genre = (data.get("genre") or "").lower()
        if genre not in GENRES:
            print(f"[MQTT] Unknown genre '{genre}', defaulting to '{GENRES[0]}'")
            genre = GENRES[0]

        # Volume (optional)
        volume = data.get("volume")
        if volume is not None:
            try:
                volume = float(volume)
                # 0–1
                volume = max(0.0, min(1.0, volume))
            except (TypeError, ValueError):
                print(f"[MQTT] Invalid volume '{volume}', ignoring")
                volume = None

        print(
            f"[MQTT] Request from {client_id}: year={year}, genre={genre}, volume={volume}"
        )

        # Apply to engine
        self.engine.set_mode(year, genre)
        if volume is not None:
            self.engine.set_volume(volume)
        self.engine.play_random()

        # Publish status
        self._publish_status({"client_id": client_id, "status": "playing"})

    # ---------- MQTT callbacks ----------

    def _on_connect(self, client, userdata, flags, rc):
        print("[MQTT] Connected with result code", rc)
        client.subscribe(TOPIC_GENRE_REQUEST)
        print(f"[MQTT] Subscribed to {TOPIC_GENRE_REQUEST}")

    def _on_message(self, client, userdata, msg):
        print(f"[MQTT] Message on {msg.topic}: {msg.payload}")

        if msg.topic != TOPIC_GENRE_REQUEST:
            print("[MQTT] Topic not handled, ignoring.")
            return

        try:
            data = json.loads(msg.payload.decode("utf-8"))
        except json.JSONDecodeError:
            self._publish_error("Invalid JSON payload", msg.payload)
            return

        try:
            self._handle_genre_request(data)
        except Exception as e:
            self._publish_error(f"Exception while handling genre request: {e}", msg.payload)
