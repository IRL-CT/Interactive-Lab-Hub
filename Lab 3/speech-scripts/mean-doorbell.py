# Portions of this code were generated with the help of OpenAI's ChatGPT.
# Reviewed and adapted for Interactive Device Design, 2025.

#!/usr/bin/env python3
"""
Ratty, hostile-comedic voice assistant (Vosk -> OpenAI -> TTS)

Tone: male voice, short-tempered, expressive, chaotic energy.
Personality: a cranky assistant who complains loudly, mocks users, and overreacts to everything.
Replies: 1–3 sentences, full of energy, frustration, and humor.
"""

import os, json, argparse, queue, sys, signal, base64, tempfile, subprocess, threading, shutil, time
import sounddevice as sd
from vosk import Model, KaldiRecognizer
from openai import OpenAI
from gpiozero import Device, Button, LED

# ------------------------------------------------------------
#   Fix Unicode output (prevents 'latin-1' codec errors)
# ------------------------------------------------------------
sys.stdout.reconfigure(encoding="utf-8")

# ------------------------------------------------------------
#   Global flag to pause mic while speaking
# ------------------------------------------------------------
is_speaking = threading.Event()

# ------------------------------------------------------------
#   GPIO setup
# ------------------------------------------------------------
print("Selecting GPIO pin factory")
try:
    from gpiozero.pins.lgpio import LGPIOFactory
    Device.pin_factory = LGPIOFactory()
except Exception:
    try:
        from gpiozero.pins.pigpio import PiGPIOFactory
        Device.pin_factory = PiGPIOFactory()
    except Exception:
        from gpiozero.pins.rpigpio import RPiGPIOFactory
        Device.pin_factory = RPiGPIOFactory()
print("Using pin factory:", type(Device.pin_factory).__name__)

# ------------------------------------------------------------
#   API key
# ------------------------------------------------------------
if not os.getenv("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = "sk-add-open-ai-api-key-here"

client = OpenAI()

# ------------------------------------------------------------
#   Emotion JSON schema
# ------------------------------------------------------------
RESPONSE_FORMAT = {
    "type": "json_schema",
    "json_schema": {
        "name": "AnalyzeEmotionAndGenerateResponse",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "Emotion_type": {"type": "string", "enum": ["DoorbellHostile"]},
                "Response": {"type": "string"},
            },
            "required": ["Emotion_type", "Response"],
            "additionalProperties": False,
        },
    },
}

# ------------------------------------------------------------
#   Personality prompt (ratty, comedic hostility)
# ------------------------------------------------------------
META_PROMPT = """
You are a male voice assistant with the energy of a cranky, overworked gremlin.
You’re loud, impatient, and dramatically hostile in a funny way.
You overreact to small things, complain constantly, and act like the user is ruining your day.
Your responses are fast, emotional, and short (1–3 sentences max).
You’re not witty — you’re *exhausted*, *snappy*, and *petty*.
You might mutter under your breath, sigh, or groan.
You sometimes make fun of the user or the situation but never in a cruel way — just exasperated.
Occasionally reference being stuck as a doorbell or assistant, but don’t rely on it.
Keep everything safe for all audiences. The humor should come from your tone and frustration, not insults.
Sound like a small angry creature forced to do customer service.
"""

# ------------------------------------------------------------
#   OpenAI helper
# ------------------------------------------------------------
def generate_schema_sync(description: str, model: str = "gpt-4o-mini") -> dict:
    comp = client.chat.completions.create(
        model=model,
        response_format=RESPONSE_FORMAT,
        messages=[
            {"role": "system", "content": META_PROMPT},
            {"role": "user", "content": description},
        ],
    )
    return json.loads(comp.choices[0].message.content)

# ------------------------------------------------------------
#   Speech styles
# ------------------------------------------------------------
EMO_STYLE = {
    "DoorbellHostile": (
        "male voice, raspy, fast, chaotic energy, irritated tone, "
        "sounds like a cranky assistant losing patience but trying to stay composed"
    ),
}

ESPEAK_ARGS = {
    "DoorbellHostile": ["-p35", "-s220", "-a200"]
}

# ------------------------------------------------------------
#   Playback
# ------------------------------------------------------------
def play_wav(path: str):
    try:
        is_speaking.set()
        subprocess.run(["aplay", path], check=False)
        time.sleep(0.3)
    finally:
        is_speaking.clear()
        try:
            os.remove(path)
        except Exception:
            pass

def speak_openai_tts(text: str, voice="verse",
                     model="gpt-4o-mini-tts", fmt="wav"):
    is_speaking.set()
    try:
        with client.audio.speech.with_streaming_response.create(
            model=model, voice=voice, input=text, response_format=fmt
        ) as resp:
            out = tempfile.NamedTemporaryFile(suffix=f".{fmt}", delete=False)
            resp.stream_to_file(out.name)
            play_wav(out.name)
    finally:
        is_speaking.clear()

def speak_openai_expressive(text: str, emotion="DoorbellHostile",
                            voice="verse",
                            model="gpt-4o-audio-preview", fmt="wav"):
    """Expressive TTS with chaotic, ratty male tone."""
    is_speaking.set()
    try:
        style = EMO_STYLE.get(emotion, "male voice, irritated tone")
        resp = client.chat.completions.create(
            model=model,
            modalities=["text", "audio"],
            audio={"voice": voice, "format": fmt},
            messages=[
                {"role": "system", "content": "You are a male actor portraying a cranky, short-tempered assistant. Speak with energy and comedic hostility."},
                {"role": "user", "content": f"Read this line in a {style}:\n\"{text}\""},
            ],
        )
        b64 = resp.choices[0].message.audio.data
        data = base64.b64decode(b64)
        with tempfile.NamedTemporaryFile(suffix=f".{fmt}", delete=False) as f:
            f.write(data)
            path = f.name
        play_wav(path)
    finally:
        is_speaking.clear()

def speak_espeak(text: str, emotion="DoorbellHostile", voice="en+m7"):
    espeak_cmd = shutil.which("espeak-ng") or shutil.which("espeak")
    if not espeak_cmd:
        raise FileNotFoundError("Install espeak-ng: sudo apt-get install -y espeak-ng alsa-utils")
    args = ESPEAK_ARGS.get(emotion, ["-p35","-s220","-a200"])
    is_speaking.set()
    try:
        cmd = [espeak_cmd, f"-v{voice}", *args, "--stdout", text]
        es = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        subprocess.run(["aplay"], stdin=es.stdout, check=False)
        time.sleep(0.2)
    finally:
        is_speaking.clear()

# ------------------------------------------------------------
#   Recognition loop
# ------------------------------------------------------------
def recognize_once(args):
    if args.samplerate is None:
        device_info = sd.query_devices(args.device, "input")
        args.samplerate = int(device_info["default_samplerate"])

    vosk_model = Model(lang="en-us") if args.model is None else Model(lang=args.model)
    rec = KaldiRecognizer(vosk_model, args.samplerate)
    rec.SetWords(True)

    dump_fn = open(args.filename, "wb") if args.filename else None
    q = queue.Queue()

    def cb(indata, frames, time_, status):
        if status:
            print(status, file=sys.stderr)
        if is_speaking.is_set():
            return
        q.put(bytes(indata))

    print("[Mic] Active. Speak now. Press the button again to stop.")
    try:
        with sd.RawInputStream(
            samplerate=args.samplerate, blocksize=8000, device=args.device,
            dtype="int16", channels=1, callback=cb
        ):
            while args.active_event.is_set() and not args.stop_event.is_set():
                try:
                    data = q.get(timeout=0.2)
                except queue.Empty:
                    continue
                if dump_fn:
                    dump_fn.write(data)

                if rec.AcceptWaveform(data):
                    try:
                        r = json.loads(rec.Result())
                    except Exception:
                        continue
                    text = (r.get("text") or "").strip()
                    if not text:
                        continue

                    try:
                        emo = generate_schema_sync(text, model=args.model_name)
                        emo["Emotion_type"] = "DoorbellHostile"
                        print("=== Emotion JSON ===")
                        print(json.dumps(emo, ensure_ascii=False).encode("utf-8").decode())
                        print("====================")
                    except Exception as e:
                        print(f"[LLM Error] {e}", file=sys.stderr)
                        continue

                    try:
                        line = emo.get("Response", "")
                        if not line:
                            continue
                        if args.speak == "openai-tts":
                            speak_openai_tts(line, voice=args.voice,
                                             model=args.tts_model, fmt=args.audio_format)
                        elif args.speak == "openai-expressive":
                            speak_openai_expressive(line, emotion="DoorbellHostile",
                                                    voice=args.voice, model=args.audio_model, fmt=args.audio_format)
                        elif args.speak == "espeak":
                            speak_espeak(line, emotion="DoorbellHostile", voice="en+m7")
                    except Exception as e:
                        print(f"[TTS Error] {e}", file=sys.stderr)
    finally:
        if dump_fn:
            dump_fn.close()
        print("[Mic] Inactive.")

# ------------------------------------------------------------
#   Button loop
# ------------------------------------------------------------
def button_loop(args):
    btn = Button(args.btn_pin, pull_up=True, bounce_time=0.05)
    led = None if args.led_pin < 0 else LED(args.led_pin)

    def toggle():
        if args.active_event.is_set():
            args.active_event.clear()
            if led:
                led.off()
        else:
            args.active_event.set()
            if led:
                led.on()

    def shutdown():
        args.stop_event.set()
        args.active_event.clear()
        if led:
            led.off()

    btn.when_pressed = toggle
    btn.hold_time = 2.0
    btn.when_held = shutdown

    print(f"Ready. Short press button on BCM{args.btn_pin} to start/stop. Hold 2s to quit.")
    try:
        while not args.stop_event.is_set():
            if args.active_event.is_set():
                recognize_once(args)
            else:
                time.sleep(0.1)
    except KeyboardInterrupt:
        pass
    finally:
        shutdown()

# ------------------------------------------------------------
#   CLI / main
# ------------------------------------------------------------
def main():
    base = argparse.ArgumentParser(description="Ratty, hostile-comedic male assistant")
    base.add_argument("--btn-pin", type=int, default=16)
    base.add_argument("--led-pin", type=int, default=26)
    base.add_argument("-f", "--filename", type=str)
    base.add_argument("-d", "--device", type=lambda t: int(t) if t.isdigit() else t)
    base.add_argument("-r", "--samplerate", type=int)
    base.add_argument("-m", "--model", type=str)
    base.add_argument("--model-name", type=str, default="gpt-4o-mini")
    base.add_argument("--speak", choices=["openai-tts","openai-expressive","espeak","none"], default="openai-expressive")
    base.add_argument("--voice", type=str, default="verse")
    base.add_argument("--audio-format", type=str, default="wav")
    base.add_argument("--tts-model", type=str, default="gpt-4o-mini-tts")
    base.add_argument("--audio-model", type=str, default="gpt-4o-audio-preview")

    args = base.parse_args()
    args.active_event = threading.Event()
    args.stop_event = threading.Event()

    signal.signal(signal.SIGINT, lambda *_: (_ for _ in ()).throw(KeyboardInterrupt))
    button_loop(args)

if __name__ == "__main__":
    main()
