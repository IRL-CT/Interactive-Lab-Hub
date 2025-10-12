#!/usr/bin/env python3
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import os, subprocess, time, json, requests, sys, io
from datetime import datetime
from pathlib import Path
from faster_whisper import WhisperModel
from outfits import rule_answer  # new rules

REC_CARD = "2,0"
REC_SECS = 8
WHISPER_MODEL = "tiny.en"
OLLAMA_MODEL  = "phi3:mini"
PIPER_BIN   = str(Path.home() / "bin/piper/piper")
PIPER_MODEL = str(Path.home() / "bin/piper/en_US-lessac-medium.onnx")
MAX_TTS_CHARS = 220
DATA_DIR = Path("data"); DATA_DIR.mkdir(exist_ok=True)

try:
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
except Exception:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

print(f"[Whisper] Loading model: {WHISPER_MODEL}", flush=True)
model = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")

def record_wav(out_wav: Path, secs=REC_SECS):
    print(f"[REC] will record {secs}s to {out_wav}", flush=True)
    cmd = ["arecord", "-D", f"plughw:{REC_CARD}", "-f", "S16_LE", "-r", "16000", "-d", str(secs), str(out_wav)]
    print("[REC] cmd:", " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True)

def stt_with_whisper(wav_path: Path) -> str:
    print("[STT] transcribing:", wav_path, flush=True)
    segments, _ = model.transcribe(str(wav_path), language="en")
    text = "".join(seg.text for seg in segments).strip()
    print("[STT] text:", text, flush=True)
    return text

def ask_ollama(prompt: str) -> str:
    url = "http://localhost:11434/api/generate"
    sys_prompt = "You are concise. Reply in one short sentence (<=25 words)."
    payload = {"model": OLLAMA_MODEL, "prompt": sys_prompt + "\n\n" + prompt, "stream": False}
    try:
        print("[LLM] requesting…", flush=True)
        r = requests.post(url, json=payload, timeout=120)
        r.raise_for_status()
        resp = r.json().get("response", "").strip()
        print("[LLM] reply:", resp, flush=True)
        return resp or "Sorry, I have no response."
    except Exception as e:
        print("[LLM] error:", e, flush=True)
        return "Sorry, the local AI service seems unavailable."

def tts_with_piper(text: str, out_wav: Path):
    if not Path(PIPER_BIN).exists(): raise FileNotFoundError(f"Piper binary not found: {PIPER_BIN}")
    if not Path(PIPER_MODEL).exists(): raise FileNotFoundError(f"Piper model not found: {PIPER_MODEL}")
    spoken = text.strip().replace("\n", " ")
    if len(spoken) > MAX_TTS_CHARS: spoken = spoken[:MAX_TTS_CHARS].rsplit(" ", 1)[0] + "…"
    print(f"[TTS] synth len={len(spoken)} chars -> {out_wav}", flush=True)
    cmd = [PIPER_BIN, "-m", PIPER_MODEL, "-f", str(out_wav)]
    subprocess.run(cmd, input=spoken.encode("utf-8"), check=True)
    print("[TTS] playing…", flush=True)
    subprocess.run(["aplay", str(out_wav)], check=True)

def main():
    print("=== Voice Router: Rules → (fallback) Ollama ===", flush=True)
    while True:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        wav_in  = DATA_DIR / f"input_{ts}.wav"
        wav_out = DATA_DIR / f"reply_{ts}.wav"
        try:
            record_wav(wav_in)
            user_text = stt_with_whisper(wav_in)
            if not user_text:
                print("[WARN] empty STT; retry", flush=True)
                continue

            # NEW: rule-based outfit answers first
            # (You can pass a real temp in Celsius; using None means default rule.)
            reply = rule_answer(user_text, temp_c=None)
            if reply is None:
                reply = ask_ollama(f"User said: {user_text}")

            tts_with_piper(reply, wav_out)
            with open(DATA_DIR / "session_log.csv", "a", encoding="utf-8") as f:
                f.write(f"{ts},{json.dumps({'user': user_text, 'ai': reply}, ensure_ascii=False)}\n")
        except KeyboardInterrupt:
            print("\n[EXIT] bye", flush=True)
            break
        except Exception as e:
            print("[ERR]", e, flush=True)
            time.sleep(1)

if __name__ == "__main__":
    main()
