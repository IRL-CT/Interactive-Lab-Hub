#!/usr/bin/env python3
"""Wizard-of-Oz voice cooking assistant for Lab 3.

On the Raspberry Pi:
    python cooking_assistant.py

For laptop/controller-only testing:
    python cooking_assistant.py --simulate

Open http://<pi-address>:5000 on the wizard's phone or laptop. In hardware
mode, touching electrode 0 on an MPR121 starts one spoken turn. The transcript
appears in the controller and the wizard chooses what the assistant says.
"""

from __future__ import annotations

import argparse
import queue
import threading
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional

from flask import Flask, jsonify, render_template, request


LAB_DIR = Path(__file__).resolve().parent
DEFAULT_VAD = LAB_DIR / "models" / "silero_vad.onnx"
DEFAULT_VOICE = LAB_DIR / "voices" / "en_US-lessac-medium.onnx"
SAMPLE_RATE = 16_000


@dataclass
class SessionState:
    status: str = "Starting"
    transcript: str = ""
    last_reply: str = ""
    current_step: int = 0
    history: list[dict[str, str]] = field(default_factory=list)


class SharedSession:
    """Thread-safe state shared by the device loop and Flask controller."""

    def __init__(self) -> None:
        self._state = SessionState()
        self._lock = threading.Lock()
        self.replies: queue.Queue[str] = queue.Queue()
        self.simulated_speech: queue.Queue[str] = queue.Queue()

    def snapshot(self) -> dict:
        with self._lock:
            return asdict(self._state)

    def update(self, **changes: object) -> None:
        with self._lock:
            for key, value in changes.items():
                if not hasattr(self._state, key):
                    raise KeyError(key)
                setattr(self._state, key, value)

    def log(self, speaker: str, text: str) -> None:
        with self._lock:
            self._state.history.append({"speaker": speaker, "text": text})
            self._state.history = self._state.history[-40:]


class SimulatedHardware:
    def __init__(self, session: SharedSession) -> None:
        self.session = session

    def wait_for_touch(self) -> None:
        self.session.update(status="Ready — submit simulated speech")

    def listen(self) -> str:
        return self.session.simulated_speech.get()

    def say(self, text: str) -> None:
        print(f"ASSISTANT: {text}", flush=True)


class PiHardware:
    """Lazy-load Pi-only dependencies so --simulate works on any computer."""

    def __init__(self, model: str, vad_path: Path, voice_path: Path,
                 min_silence: float) -> None:
        import board
        import busio
        import adafruit_mpr121
        import numpy as np
        import sherpa_onnx
        import sounddevice as sd
        from faster_whisper import WhisperModel
        from piper import PiperVoice

        for path, label in ((vad_path, "VAD model"), (voice_path, "Piper voice")):
            if not path.is_file():
                raise FileNotFoundError(f"{label} not found at {path}; run speech-scripts/setup.sh")

        self.np = np
        self.sd = sd
        self.recognizer = WhisperModel(model, device="cpu", compute_type="int8")
        self.voice = PiperVoice.load(str(voice_path))
        self.touch = adafruit_mpr121.MPR121(busio.I2C(board.SCL, board.SDA))

        config = sherpa_onnx.VadModelConfig()
        config.silero_vad.model = str(vad_path)
        config.silero_vad.min_silence_duration = min_silence
        config.silero_vad.min_speech_duration = 0.25
        config.sample_rate = SAMPLE_RATE
        self.config = config
        self.sherpa_onnx = sherpa_onnx

    def wait_for_touch(self) -> None:
        while not self.touch[0].value:
            time.sleep(0.03)
        while self.touch[0].value:  # do not record the user's touch noises
            time.sleep(0.03)

    def listen(self) -> str:
        detector = self.sherpa_onnx.VoiceActivityDetector(
            self.config, buffer_size_in_seconds=30
        )
        window = self.config.silero_vad.window_size
        buffer = self.np.empty(0, dtype=self.np.float32)
        samples_per_read = int(0.1 * SAMPLE_RATE)

        with self.sd.InputStream(channels=1, dtype="float32", samplerate=SAMPLE_RATE) as stream:
            while True:
                chunk, _ = stream.read(samples_per_read)
                buffer = self.np.concatenate([buffer, chunk.reshape(-1)])
                while len(buffer) >= window:
                    detector.accept_waveform(buffer[:window])
                    buffer = buffer[window:]
                if not detector.empty():
                    utterance = self.np.array(detector.front.samples, dtype=self.np.float32)
                    detector.pop()
                    segments, _ = self.recognizer.transcribe(utterance, beam_size=1)
                    return " ".join(segment.text.strip() for segment in segments).strip()

    def say(self, text: str) -> None:
        for chunk in self.voice.synthesize(text):
            audio = self.np.frombuffer(chunk.audio_int16_bytes, dtype=self.np.int16)
            self.sd.play(audio, samplerate=chunk.sample_rate)
            self.sd.wait()


def device_loop(session: SharedSession, hardware: SimulatedHardware | PiHardware) -> None:
    hardware.say("Cooking assistant ready. Touch the copper pad when you want to speak.")
    while True:
        session.update(status="Ready — touch pad 0 to speak")
        hardware.wait_for_touch()
        session.update(status="Listening")
        heard = hardware.listen()
        if not heard:
            session.update(status="I did not hear words — try again")
            time.sleep(1)
            continue

        session.update(status="Waiting for wizard", transcript=heard)
        session.log("User", heard)
        reply = session.replies.get()
        session.update(status="Speaking", last_reply=reply)
        session.log("Assistant", reply)
        hardware.say(reply)


def create_app(session: SharedSession, simulate: bool) -> Flask:
    app = Flask(__name__)

    @app.get("/")
    def controller():
        return render_template("controller.html", simulate=simulate)

    @app.get("/api/state")
    def get_state():
        return jsonify(session.snapshot())

    @app.post("/api/reply")
    def send_reply():
        text = str((request.get_json(silent=True) or {}).get("text", "")).strip()
        if not text:
            return jsonify(error="Reply cannot be empty"), 400
        if session.snapshot()["status"] != "Waiting for wizard":
            return jsonify(error="There is no participant turn waiting for a reply"), 409
        session.replies.put(text)
        return jsonify(ok=True)

    @app.post("/api/simulate-speech")
    def simulate_speech():
        if not simulate:
            return jsonify(error="Only available with --simulate"), 403
        text = str((request.get_json(silent=True) or {}).get("text", "")).strip()
        if not text:
            return jsonify(error="Speech cannot be empty"), 400
        session.simulated_speech.put(text)
        return jsonify(ok=True)

    return app


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--simulate", action="store_true", help="run without Pi/audio hardware")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--model", default="tiny.en")
    parser.add_argument("--vad-model", type=Path, default=DEFAULT_VAD)
    parser.add_argument("--voice", type=Path, default=DEFAULT_VOICE)
    parser.add_argument("--min-silence", type=float, default=1.0)
    args = parser.parse_args()

    session = SharedSession()
    hardware: SimulatedHardware | PiHardware
    if args.simulate:
        hardware = SimulatedHardware(session)
    else:
        hardware = PiHardware(args.model, args.vad_model, args.voice, args.min_silence)

    threading.Thread(target=device_loop, args=(session, hardware), daemon=True).start()
    create_app(session, args.simulate).run(
        host=args.host, port=args.port, debug=False, threaded=True
    )


if __name__ == "__main__":
    main()
