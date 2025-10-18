#!/usr/bin/env python3
"""
master.py
Realtime orchestrator: Mic -> Speech-to-Text (Vosk) -> Face ID (in background) -> Love LLM -> Piper TTS.

New behavior:
- Runs continuously and listens on the microphone.
- As soon as speech begins, we kick off a background face-capture+recognition job.
- When the user finishes speaking (end-of-utterance), we:
    * combine the recognized name (if available; else "unknown") and the transcribed text,
    * call the love_server (Ollama) for a reply,
    * speak the reply via Piper TTS (greet_name_piper.py).
- After TTS finishes, we go back to listening.

Prereqs on Raspberry Pi:
  sudo apt install -y alsa-utils
  python3 -m pip install sounddevice vosk opencv-python numpy

Also requires your previous pieces running/installed:
  - face_server.py started separately (default: http://127.0.0.1:7860/recognize)
  - love_server.py started separately (default: http://127.0.0.1:7861/reply)
  - greet_name_piper.py available and executable (or pass --greet-script path)

Usage:
  python master.py
  python master.py --debug

Common overrides:
  python master.py \
    --base-dir ~/facerecog \
    --server-url http://127.0.0.1:7860/recognize \
    --love-url   http://127.0.0.1:7861/reply \
    --stt-model  ~/facerecog/vosk-model-small-en-us-0.15 \
    --llm-message "" \
    --cam-index 0 --width 1280 --height 720
"""

import argparse
import datetime as _dt
import json
import logging as log
import os
import queue
import shlex
import subprocess
import sys
import threading
import time
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Optional, Tuple

# Optional imports for OpenCV capture fallback
try:
    import cv2  # type: ignore
    import numpy as np  # type: ignore
except Exception:
    cv2 = None
    np = None

# Mic + STT
try:
    import sounddevice as sd  # type: ignore
except Exception:
    sd = None

try:
    from vosk import Model as VoskModel, KaldiRecognizer  # type: ignore
except Exception:
    VoskModel = None
    KaldiRecognizer = None


# ---------------------------- Utilities ----------------------------

def which(cmd: str) -> bool:
    from shutil import which as _which
    return _which(cmd) is not None

def run_cmd(cmd: str, timeout: int = 30) -> int:
    log.debug("Running: %s", cmd)
    try:
        proc = subprocess.run(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
        if proc.returncode != 0:
            log.debug("Command stderr: %s", proc.stderr.decode(errors="ignore"))
        return proc.returncode
    except Exception as e:
        log.debug("Command failed to start: %s", e)
        return 127

def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)

def timestamp() -> str:
    return _dt.datetime.now().strftime("%Y%m%d_%H%M%S")

def http_post_json(url: str, payload: dict, timeout: int = 10) -> Optional[dict]:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="ignore")
            return json.loads(body)
    except urllib.error.URLError as e:
        log.debug("HTTP POST to %s failed: %s", url, e)
    except Exception as e:
        log.debug("HTTP POST parsing failed: %s", e)
    return None


# ---------------------------- Camera ----------------------------

def mean_brightness(frame) -> float:
    if cv2 is None or np is None or frame is None:
        return -1.0
    try:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return float(np.mean(gray))
    except Exception:
        return -1.0

def capture_with_libcamera_still(out_path: str, width: int, height: int, timeout_ms: int) -> bool:
    if not which("libcamera-still"):
        return False
    cmd = f"libcamera-still -n -t {timeout_ms} -o {shlex.quote(out_path)} --width {width} --height {height} --denoise cdn_fast"
    rc = run_cmd(cmd, timeout=max(5, timeout_ms // 1000 + 10))
    ok = (rc == 0 and os.path.isfile(out_path) and os.path.getsize(out_path) > 0)
    log.debug("libcamera-still rc=%s ok=%s", rc, ok)
    return ok

def capture_with_fswebcam(out_path: str, width: int, height: int, delay_s: int) -> bool:
    if not which("fswebcam"):
        return False
    cmd = f"fswebcam -D {delay_s} -r {width}x{height} --no-banner {shlex.quote(out_path)}"
    rc = run_cmd(cmd, timeout=delay_s + 15)
    ok = (rc == 0 and os.path.isfile(out_path) and os.path.getsize(out_path) > 0)
    log.debug("fswebcam rc=%s ok=%s", rc, ok)
    return ok

def capture_with_opencv(
    out_path: str,
    cam_index: int,
    width: int,
    height: int,
    warmup_frames: int,
    warmup_sleep_ms: int,
    retries: int,
    brightness_min: float,
    retry_sleep_ms: int,
    use_mjpg: bool,
    exp_high_seq: list[int],
    exp_low_seq: list[int],
) -> bool:
    if cv2 is None or np is None:
        log.error("OpenCV not available; install with: python3 -m pip install opencv-python numpy")
        return False

    cap = cv2.VideoCapture(cam_index, cv2.CAP_V4L2)
    if not cap.isOpened():
        cap = cv2.VideoCapture(cam_index)
        if not cap.isOpened():
            log.error("Could not open camera index %s", cam_index)
            return False

    if use_mjpg:
        try:
            fourcc = cv2.VideoWriter_fourcc(*"MJPG")
            cap.set(cv2.CAP_PROP_FOURCC, fourcc)
        except Exception:
            pass

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    try:
        cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.75)
    except Exception:
        pass
    try:
        cap.set(cv2.CAP_PROP_AUTO_WB, 1)
    except Exception:
        pass

    for _ in range(max(0, warmup_frames)):
        cap.read()
        if warmup_sleep_ms > 0:
            time.sleep(warmup_sleep_ms / 1000.0)

    ok, frame = cap.read()
    if not ok or frame is None:
        log.error("OpenCV: failed to read initial frame.")
        cap.release()
        return False

    b = mean_brightness(frame)
    log.debug("[capture] initial mean=%.1f", b)

    if b >= 220.0 and exp_high_seq:
        try:
            cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)
        except Exception:
            pass
        for ev in exp_high_seq:
            try:
                cap.set(cv2.CAP_PROP_EXPOSURE, float(ev))
            except Exception:
                pass
            time.sleep(0.08)
            ok, frame = cap.read()
            if not ok or frame is None:
                continue
            b = mean_brightness(frame)
            log.debug("[capture] manual exposure=%s mean=%.1f", ev, b)
            if b < 220.0:
                break
    elif b < brightness_min and exp_low_seq:
        try:
            cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)
        except Exception:
            pass
        for ev in exp_low_seq:
            try:
                cap.set(cv2.CAP_PROP_EXPOSURE, float(ev))
            except Exception:
                pass
            time.sleep(0.08)
            ok, frame = cap.read()
            if not ok or frame is None:
                continue
            b = mean_brightness(frame)
            log.debug("[capture] manual exposure=%s mean=%.1f", ev, b)
            if b >= brightness_min:
                break

    frame_ok = None
    last_mean = b
    for i in range(max(1, retries)):
        if frame is None:
            ok, frame = cap.read()
            if not ok:
                if retry_sleep_ms > 0:
                    time.sleep(retry_sleep_ms / 1000.0)
                continue
        last_mean = mean_brightness(frame)
        log.debug("[capture] try=%s/%s mean=%.1f", i + 1, retries, last_mean)
        if brightness_min <= last_mean <= 245.0:
            frame_ok = frame
            break
        ok, frame = cap.read()
        if not ok:
            if retry_sleep_ms > 0:
                time.sleep(retry_sleep_ms / 1000.0)
            frame = None

    cap.release()

    if frame_ok is None:
        frame_ok = frame if frame is not None else np.zeros((height, width, 3), dtype=np.uint8)
        log.warning("OpenCV: brightness out of bounds (mean=%.1f). Saving anyway.", last_mean)

    try:
        ok = cv2.imwrite(out_path, frame_ok)
        if not ok:
            log.error("cv2.imwrite failed for %s", out_path)
            return False
    except Exception as e:
        log.error("Failed to save image: %s", e)
        return False

    return True

def capture_image(
    out_path: str,
    cam_index: int,
    width: int,
    height: int,
    libcamera_timeout_ms: int,
    fswebcam_delay_s: int,
    warmup_frames: int,
    warmup_sleep_ms: int,
    retries: int,
    brightness_min: float,
    retry_sleep_ms: int,
    use_mjpg: bool,
    exp_high_seq: list[int],
    exp_low_seq: list[int],
) -> bool:
    log.info("Capturing image to: %s", out_path)
    if capture_with_libcamera_still(out_path, width, height, libcamera_timeout_ms):
        return True
    if capture_with_fswebcam(out_path, width, height, fswebcam_delay_s):
        return True
    return capture_with_opencv(
        out_path,
        cam_index,
        width,
        height,
        warmup_frames,
        warmup_sleep_ms,
        retries,
        brightness_min,
        retry_sleep_ms,
        use_mjpg,
        exp_high_seq,
        exp_low_seq,
    )


# ---------------------------- Face recognition glue ----------------------------

def recognize_via_server(server_url: str, image_path: str) -> Optional[Tuple[str, float]]:
    payload = {"image_path": image_path}
    log.debug("POST %s payload=%s", server_url, payload)
    resp = http_post_json(server_url, payload, timeout=15)
    log.debug("face_server response=%s", resp)
    if not resp:
        return None
    name = resp.get("name", "unknown") or "unknown"
    conf = float(resp.get("confidence", 0.0))
    return (name, conf)

def recognize_via_cli(face_recognize_py: str, image_path: str, headshots: str, model: str, det: int) -> Optional[Tuple[str, float]]:
    if not os.path.isfile(face_recognize_py):
        log.error("Fallback recognizer not found: %s", face_recognize_py)
        return None
    cmd = f"python3 {shlex.quote(face_recognize_py)} {shlex.quote(image_path)} --headshots {shlex.quote(headshots)} --model {model} --det {det}"
    log.debug("Fallback CLI: %s", cmd)
    try:
        proc = subprocess.run(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=45)
    except Exception as e:
        log.debug("Fallback CLI failed to execute: %s", e)
        return None
    out = proc.stdout.decode(errors="ignore").strip()
    log.debug("Fallback CLI stdout: %r", out)
    if not out:
        log.debug("Fallback CLI produced no output. stderr: %s", proc.stderr.decode(errors="ignore"))
        return None
    try:
        obj = json.loads(out)
    except Exception:
        log.debug("Fallback CLI output is not JSON: %r", out)
        return None
    name = obj.get("name", "unknown") or "unknown"
    conf = float(obj.get("confidence", 0.0)) if "confidence" in obj else 0.0
    return (name, conf)


# ---------------------------- Love LLM & TTS ----------------------------

def get_love_reply(love_url: str, name: str, message: str) -> Optional[str]:
    payload = {"name": name}
    if message:
        payload["message"] = message
    log.debug("POST %s payload=%s", love_url, payload)
    resp = http_post_json(love_url, payload, timeout=30)
    log.debug("love_server response=%s", resp)
    if not resp:
        return None
    text = (resp.get("reply") or "").strip()
    return text or None

def speak_text(greet_script: str, text: str) -> None:
    if os.path.isfile(greet_script) and os.access(greet_script, os.X_OK):
        cmd = f"{shlex.quote(greet_script)} {shlex.quote(text)}"
        log.info("Speaking via: %s", cmd)
        rc = run_cmd(cmd, timeout=max(60, 10 + len(text) // 4))
        if rc != 0:
            log.warning("TTS script returned non-zero exit code: %s", rc)
    else:
        log.warning("TTS script not executable or not found: %s", greet_script)
        log.info("TTS fallback text: %s", text)


# ---------------------------- STT (Vosk) ----------------------------

class LiveSTT:
    """
    Simple Vosk-based microphone listener.
    - Opens a sounddevice input stream at target sample rate.
    - Provides an iterator yielding finalized utterances (strings).
    - End-of-utterance is determined by recognizer.AcceptWaveform on chunked audio.
    """
    def __init__(self, model_dir: str, samplerate: int = 16000, device: Optional[int] = None, blocksize: int = 8000):
        if VoskModel is None or KaldiRecognizer is None:
            raise RuntimeError("Vosk not available. Install with: python3 -m pip install vosk")
        if sd is None:
            raise RuntimeError("sounddevice not available. Install with: python3 -m pip install sounddevice")

        self.model_dir = model_dir
        self.model = VoskModel(model_dir)
        self.samplerate = samplerate
        self.device = device
        self.blocksize = blocksize
        self.q: "queue.Queue[bytes]" = queue.Queue()
        self.stream: Optional[sd.InputStream] = None
        self._stopping = False

    def _callback(self, indata, frames, time_info, status):
        if status:
            log.debug("SD status: %s", status)
        # indata is float32; convert to 16-bit PCM bytes for Vosk
        data = (indata * 32767).astype("int16").tobytes()
        self.q.put(data)

    def start(self):
        self._stopping = False
        self.stream = sd.InputStream(
            samplerate=self.samplerate,
            channels=1,
            dtype="float32",
            callback=self._callback,
            blocksize=self.blocksize,
            device=self.device,
        )
        self.stream.start()
        log.info("Microphone stream started (rate=%d, blocksize=%d).", self.samplerate, self.blocksize)

    def stop(self):
        self._stopping = True
        if self.stream is not None:
            try:
                self.stream.stop()
                self.stream.close()
            except Exception:
                pass
            self.stream = None
        # drain queue
        with self.q.mutex:
            self.q.queue.clear()
        log.info("Microphone stream stopped.")

    def listen_loop(self):
        """
        Generator that yields finalized utterance strings.
        """
        rec = KaldiRecognizer(self.model, self.samplerate)
        rec.SetWords(True)

        speaking = False
        while not self._stopping:
            try:
                data = self.q.get(timeout=0.25)
            except queue.Empty:
                continue

            if not data:
                continue

            # As soon as recognizer has a partial (speech started), we mark speaking
            if not speaking:
                if rec.AcceptWaveform(b"\x00" * 0):  # nop, but we can query partial via Result JSON
                    pass
                # The recognizer provides partial via rec.PartialResult(), but
                # a simpler heuristic: once we feed any data, mark speaking True and let finalization happen.
                speaking = True

            if rec.AcceptWaveform(data):
                # End-of-utterance (Vosk finalized)
                try:
                    res = json.loads(rec.Result())
                except Exception:
                    res = {}
                text = (res.get("text") or "").strip()
                if text:
                    yield text
                # Reset recognizer for next utterance
                rec = KaldiRecognizer(self.model, self.samplerate)
                rec.SetWords(True)
                speaking = False
            else:
                # Optional: could inspect partial for VAD, but we rely on finalization above
                pass


# ---------------------------- Main orchestration (loop) ----------------------------

def main():
    ap = argparse.ArgumentParser(description="Realtime mic -> STT -> Face -> Love LLM -> Piper TTS")
    # Paths / modules
    ap.add_argument("--base-dir", default=os.path.expanduser("~/facerecog"), help="Project base dir (default: ~/facerecog)")
    ap.add_argument("--headshots", default=None, help="Headshots dir. Default: <base-dir>/headshots")
    ap.add_argument("--log-dir", default=None, help="Log dir for captured images. Default: <base-dir>/log")
    ap.add_argument("--greet-script", default=None, help="Path to Piper script (e.g., greet_name_piper.py). Default: <base-dir>/greet_name_piper.py")
    ap.add_argument("--fallback-cli", default=None, help="Path to face_recognize.py fallback. Default: <base-dir>/face_recognize.py")

    # Server endpoints
    ap.add_argument("--server-url", default="http://127.0.0.1:7860/recognize", help="Face server endpoint URL")
    ap.add_argument("--love-url",   default="http://127.0.0.1:7861/reply",     help="Love LLM server endpoint URL")

    # Optional extra message for love server, appended after the live transcript
    ap.add_argument("--llm-message", default="", help="Optional extra message for the love server")

    # Capture/camera settings
    ap.add_argument("--cam-index", type=int, default=0, help="Camera index (default: 0)")
    ap.add_argument("--width", type=int, default=1280, help="Capture width (default: 1280)")
    ap.add_argument("--height", type=int, default=720, help="Capture height (default: 720)")
    ap.add_argument("--libcamera-timeout-ms", type=int, default=2000, help="libcamera-still timeout ms (default: 2000)")
    ap.add_argument("--fswebcam-delay-s", type=int, default=2, help="fswebcam warm-up delay seconds (default: 2)")

    # OpenCV fallback tuning
    ap.add_argument("--warmup-frames", type=int, default=10, help="OpenCV warmup frames (default: 10)")
    ap.add_argument("--warmup-sleep-ms", type=int, default=50, help="Sleep between warmup frames ms (default: 50)")
    ap.add_argument("--retries", type=int, default=20, help="OpenCV capture retries (default: 20)")
    ap.add_argument("--brightness-min", type=float, default=30.0, help="Acceptable min mean brightness (0..255)")
    ap.add_argument("--retry-sleep-ms", type=int, default=60, help="Sleep between retries ms (default: 60)")
    ap.add_argument("--use-mjpg", action="store_true", default=True, help="Try MJPG fourcc for UVC cams")
    ap.add_argument("--no-mjpg", dest="use_mjpg", action="store_false", help="Disable MJPG fourcc")
    ap.add_argument("--exp-high-seq", default="200,100,50,25", help="Exposure sequence (if overexposed) comma-separated")
    ap.add_argument("--exp-low-seq", default="400,600,800", help="Exposure sequence (if underexposed) comma-separated")

    # STT settings
    ap.add_argument("--stt-model", default=os.path.expanduser("~/facerecog/vosk-model-small-en-us-0.15"),
                    help="Path to a Vosk model directory (default: small-en-us).")
    ap.add_argument("--stt-rate", type=int, default=16000, help="STT sample rate (default: 16000)")
    ap.add_argument("--stt-device", type=int, default=None, help="sounddevice input device index (default: system default)")
    ap.add_argument("--stt-blocksize", type=int, default=8000, help="sounddevice blocksize (default: 8000)")

    # Fallback face-recognizer CLI (only if face_server is unavailable)
    ap.add_argument("--model", default="buffalo_m", help="Fallback CLI: InsightFace model (default: buffalo_m)")
    ap.add_argument("--det", type=int, default=320, help="Fallback CLI: detector size (default: 320)")

    # Logging
    ap.add_argument("--debug", action="store_true", help="Enable debug logging")

    args = ap.parse_args()

    log.basicConfig(
        level=log.DEBUG if args.debug else log.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    base_dir = os.path.expanduser(args.base_dir)
    headshots = args.headshots or os.path.join(base_dir, "headshots")
    log_dir = args.log_dir or os.path.join(base_dir, "log")
    greet_script = args.greet_script or os.path.join(base_dir, "greet_name_piper.py")
    fallback_cli = args.fallback_cli or os.path.join(base_dir, "face_recognize.py")

    ensure_dir(log_dir)

    if not os.path.isdir(headshots):
        log.error("Headshots folder not found: %s", headshots)
        sys.exit(2)

    # Parse camera exposure sequences
    try:
        exp_high_seq = [int(x) for x in args.exp_high_seq.split(",") if x.strip()]
    except Exception:
        exp_high_seq = [200, 100, 50, 25]
    try:
        exp_low_seq = [int(x) for x in args.exp_low_seq.split(",") if x.strip()]
    except Exception:
        exp_low_seq = [400, 600, 800]

    # Init STT
    if VoskModel is None or KaldiRecognizer is None or sd is None:
        log.error("Missing STT deps. Install: python3 -m pip install sounddevice vosk")
        sys.exit(3)

    try:
        stt = LiveSTT(
            model_dir=args.stt_model,
            samplerate=args.stt_rate,
            device=args.stt_device,
            blocksize=args.stt_blocksize,
        )
    except Exception as e:
        log.error("Failed to init STT: %s", e)
        sys.exit(3)

    # Thread pool for background face capture/recognition
    pool = ThreadPoolExecutor(max_workers=2)
    face_lock = threading.Lock()
    face_future: Optional[Future] = None

    def start_face_job_if_needed():
        nonlocal face_future
        with face_lock:
            if face_future is None or face_future.done():
                # Build image path per utterance
                out_path = os.path.join(log_dir, f"capture_{timestamp()}.jpg")
                def job():
                    ok = capture_image(
                        out_path=out_path,
                        cam_index=args.cam_index,
                        width=args.width,
                        height=args.height,
                        libcamera_timeout_ms=args.libcamera_timeout_ms,
                        fswebcam_delay_s=args.fswebcam_delay_s,
                        warmup_frames=args.warmup_frames,
                        warmup_sleep_ms=args.warmup_sleep_ms,
                        retries=args.retries,
                        brightness_min=args.brightness_min,
                        retry_sleep_ms=args.retry_sleep_ms,
                        use_mjpg=args.use_mjpg,
                        exp_high_seq=exp_high_seq,
                        exp_low_seq=exp_low_seq,
                    )
                    if not ok or not os.path.isfile(out_path) or os.path.getsize(out_path) == 0:
                        log.warning("Background capture failed.")
                        return ("unknown", 0.0)
                    log.info("Saved capture: %s", out_path)
                    # Try server first
                    res = recognize_via_server(args.server_url, out_path)
                    if res is not None:
                        return res
                    # Fallback
                    log.warning("Face server unavailable; using fallback recognizer CLI.")
                    res = recognize_via_cli(fallback_cli, out_path, headshots, args.model, args.det)
                    if res is not None:
                        return res
                    return ("unknown", 0.0)

                face_future = pool.submit(job)

    # Start mic stream
    stt.start()
    log.info("Listening... (Ctrl+C to stop)")
    try:
        for utterance in stt.listen_loop():
            # We got a finished utterance. While listening to this utterance, we should have started face job.
            # If it didn't start (shouldn't happen), start now.
            if face_future is None or face_future.done():
                # Kick off face job ASAP
                start_face_job_if_needed()

            # Compose LLM message: user's live text + optional extra
            msg = utterance
            if args.llm_message:
                msg = f"{utterance}\n\n{args.llm_message}"

            # Wait for face result briefly; if not ready, block up to a short timeout (e.g., 3s)
            name, conf = "unknown", 0.0
            with face_lock:
                fut = face_future
            if fut is not None:
                try:
                    name, conf = fut.result(timeout=3.0)
                except Exception:
                    # Not ready or failed; we can wait a bit longer or proceed with unknown
                    log.debug("Face job not ready; proceeding with name='unknown' for now.")
                    name, conf = "unknown", 0.0

            # Query love_server
            reply_text = get_love_reply(args.love_url, name, msg)
            if not reply_text:
                reply_text = f"{name if name!='unknown' else 'friend'}, I'm wildly excited you spoke—tell me more!"

            log.info("User said: %r  -> LLM reply: %s", utterance, reply_text)

            # Pause mic while speaking to avoid feedback/false triggers
            stt.stop()
            try:
                speak_text(greet_script, reply_text)
            finally:
                # Reset background face job for next utterance
                with face_lock:
                    face_future = None
                # Resume listening
                stt.start()
                # As soon as we hear next speech chunk, we'll start a new face job

            # Small idle so audio device can settle
            time.sleep(0.05)

    except KeyboardInterrupt:
        log.info("Interrupted by user, shutting down...")
    finally:
        stt.stop()
        pool.shutdown(wait=False)


if __name__ == "__main__":
    main()
