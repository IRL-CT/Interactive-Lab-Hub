#!/usr/bin/env python3
"""The whole loop, once: listen, find where your turn ended, answer out loud.

This is deliberately the dumbest possible dialogue policy: it repeats what you
said back to you, once, and then exits. That is the point. With the content held
constant, everything you notice about the interaction is a property of the
*timing* and the *voice*, not of what the system says. Get this working, then
replace `respond()` with something of your own.

    python echo_bot.py
    python echo_bot.py --min-silence 1.0

Things worth trying:
  - Set --min-silence to 0.2, then to 1.5. Which one feels like it is listening?
  - Add a deliberate 2-second delay before it replies. Does it feel broken, or
    thoughtful?
"""

import argparse
import sys
import time
import threading
from pathlib import Path

import numpy as np
import sherpa_onnx
import sounddevice as sd
from faster_whisper import WhisperModel
from flask import Flask, request, jsonify
from piper import PiperVoice

SAMPLE_RATE = 16000
LAB_DIR = Path(__file__).resolve().parent.parent
DEFAULT_VAD = LAB_DIR / "models" / "silero_vad.onnx"
app = Flask(__name__)
latest = {"status": "idle", "message": "", "reply": ""}
DEFAULT_VOICE = LAB_DIR / "voices" / "en_US-lessac-medium.onnx"
speaker = recognizer = vad = window = None


def respond(heard: str) -> str:
      return "Thank you for your response. I will inform your family."


class Speaker:
    """Synthesizes with Piper and plays through the default output device."""

    def __init__(self, voice_path: Path) -> None:
        self.voice = PiperVoice.load(str(voice_path))

    def say(self, text: str) -> float:
        """Speaks the text. Returns seconds until the first audio was ready."""
        # to debug w/o speaker: print text speaker would say
        #print(f" [speaker] {text}", flush=True)
        t0 = time.perf_counter()
        first_audio_at = None
        for chunk in self.voice.synthesize(text):
            audio = np.frombuffer(chunk.audio_int16_bytes, dtype=np.int16)
            if first_audio_at is None:
                first_audio_at = time.perf_counter() - t0
            sd.play(audio, samplerate=chunk.sample_rate)
            sd.wait()
        return first_audio_at or 0.0

def main() -> None:
    global speaker, recognizer, vad, window
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--model", default="tiny.en",
                        help="whisper model size (default: tiny.en)")
    parser.add_argument("--vad-model", type=Path, default=DEFAULT_VAD)
    parser.add_argument("--voice", type=Path, default=DEFAULT_VOICE)
    parser.add_argument("--min-silence", type=float, default=1.2,
                        help="seconds of silence that end your turn (default: 1.2)")
    args = parser.parse_args()

    for path, what in [(args.vad_model, "VAD model"), (args.voice, "Piper voice")]:
        if not path.is_file():
            sys.exit(f"{what} not found at {path}. Run ./setup.sh first.")

    print("Loading models...", flush=True)
    recognizer = WhisperModel(args.model, device="cpu", compute_type="int8")
    speaker = Speaker(args.voice)

    config = sherpa_onnx.VadModelConfig()
    config.silero_vad.model = str(args.vad_model)
    config.silero_vad.min_silence_duration = args.min_silence
    config.sample_rate = SAMPLE_RATE
    vad = sherpa_onnx.VoiceActivityDetector(config, buffer_size_in_seconds=30)
    window = config.silero_vad.window_size

    #print(ask("Have you taken your medication today?"))
    app.run(host="0.0.0.0", port=5000)


def ask(message: str) -> str:
  # medication check - user answers
    speaker.say(message)
    time.sleep(0.5)
    vad.reset()
    deadline = time.time() + 30

    buffer = np.empty(0, dtype=np.float32)
    samples_per_read = int(0.1 * SAMPLE_RATE)

    with sd.InputStream(channels=1, dtype="float32", samplerate=SAMPLE_RATE) as stream:
        while True:
            chunk, _ = stream.read(samples_per_read)
            buffer = np.concatenate([buffer, chunk.reshape(-1)])

            while len(buffer) > window:
                vad.accept_waveform(buffer[:window])
                buffer = buffer[window:]

            if time.time() > deadline and not vad.is_speech_detected():
                print("No response from user...")
                speaker.say("I will check in again later.")
                return "No response from user..."

            while not vad.empty():
                utterance = np.array(vad.front.samples, dtype=np.float32)
                vad.pop()
                turn_ended = time.perf_counter()

                segments, _ = recognizer.transcribe(utterance, beam_size=1)
                heard = " ".join(s.text.strip() for s in segments)
                if not heard:
                    continue  # noise, not words: keep listening
                asr_done = time.perf_counter()

                speaker.say(respond(heard))
                return heard

# to faciliate "texting" mechanism, using flask to create a webpage
def run_check(message: str) -> str:
  latest["reply"] = ask(message)
  latest["status"] = "done"

@app.post("/send")
def send():
  if latest["status"] == "listening":
    return jsonify(error = "Still waiting for your response..."), 409
  message = request.json["message"]
  latest.update(status = "listening", message = message, reply = "")
  threading.Thread(target=run_check, args=(message,), daemon=True).start()
  return jsonify(ok = True)

@app.get("/status")
def status():
  return jsonify(latest)

@app.get("/")
def index():
  return PAGE

# w/ help from cursor: to help create the webpage to faciliate "texting" communication
PAGE = """
<h1>Medicine check</h1>
<textarea id="msg">Have you taken your medication today?</textarea>
<button onclick="send()">Send</button>
<p id="status"></p>
<p id="reply"></p>
<script>
async function send() {
  await fetch("/send", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({message: document.getElementById("msg").value})
  });
  poll();
}
async function poll() {
  const data = await (await fetch("/status")).json();
  document.getElementById("status").textContent = data.status;
  document.getElementById("reply").textContent = data.reply;
  if (data.status === "listening") setTimeout(poll, 1000);
}
</script>
"""

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped.")
