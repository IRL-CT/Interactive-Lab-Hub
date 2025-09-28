import os, sys, csv, json, time, re, uuid, datetime, mimetypes, subprocess
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime as _dt
import textwrap
from enum import IntEnum
import threading
import urllib.request, urllib.error

ONLINE_MODE = any(a.lower() in ("online", "--online", "-o") for a in sys.argv[1:])
ONLINE_BASE = os.environ.get("VLT_ONLINE_BASE", "https://source-maps-train-training.trycloudflare.com").rstrip("/") # you can replace with your own CF temporary tunnel or local URL to PC server

PROJECT_DIR = Path(__file__).resolve().parent
LOG_DIR     = PROJECT_DIR / "vlt_logs"
IMG_DIR     = LOG_DIR / "images"
LOG_FILE    = LOG_DIR / "clock.log"
CSV_FILE    = LOG_DIR / "log.csv"
LOG_DIR.mkdir(parents=True, exist_ok=True)
IMG_DIR.mkdir(parents=True, exist_ok=True)

MAX_NEW_TOKENS  = int(os.environ.get("VLT_MAX_NEW_TOKENS", "50"))
INFER_TIMEOUT_S = int(os.environ.get("VLT_INFER_TIMEOUT",  "120"))

OLLAMA_BASE       = os.environ.get("OLLAMA_BASE", "http://127.0.0.1:11434").rstrip("/")
OLLAMA_MODEL      = os.environ.get("OLLAMA_MODEL", "qwen2.5:0.5b-instruct")
OLLAMA_TIMEOUT_S  = int(os.environ.get("OLLAMA_TIMEOUT_S", "20"))

CAPTURE_EVERY = int(os.environ.get("VLT_INTERVAL", "5"))
CAM_INDEX     = int(os.environ.get("VLT_CAM_INDEX", "0"))
FRAME_W       = int(os.environ.get("VLT_W", "640"))
FRAME_H       = int(os.environ.get("VLT_H", "480"))

CS_PIN_NAME   = os.environ.get("VLT_CS_PIN", "D5")
DC_PIN_NAME   = os.environ.get("VLT_DC_PIN", "D25")

SERVER_HOST   = "127.0.0.1"
SERVER_PORT   = int(os.environ.get("VLM_PORT", "17860"))
SERVER_BASE   = f"http://{SERVER_HOST}:{SERVER_PORT}"

VLT_PROMPT = ("Describe only observable lighting cues. Describe environment/sky/weather; natural light (direct vs diffuse, where it enters, sun patches/glare); shadows (presence, edge sharpness, relative length, direction); artificial lights (which sources are on, brightness low/medium/high, color warm/neutral/cool); overall brightness/exposure (very dark/dim/medium/bright, blown highlights, deep shadows, noise, motion blur); windows/openings and orientation hints; secondary clues (streetlights on, blinds/shades state, screen glow); brief caveats/confidence.")

def _ts() -> str:
    return _dt.utcnow().isoformat()

def log(msg: str) -> None:
    line = f"[{_ts()}] {msg}"
    print(line, flush=True)
    try:
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")
    except Exception:
        pass

def preempt_boot_screen() -> None:
    try:
        subprocess.run(["sudo", "-n", "systemctl", "stop", "pitft-boot-screen.service"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        log(f"systemctl stop attempt error (ignored): {e}")
    try:
        subprocess.run(["pkill", "-TERM", "-f", "python.*screen_boot_script.py"], check=False)
        time.sleep(0.8)
        subprocess.run(["pkill", "-KILL", "-f", "python.*screen_boot_script.py"], check=False)
    except Exception as e:
        log(f"pkill fallback error (ignored): {e}")

preempt_boot_screen()

import cv2  # type: ignore
import digitalio  # type: ignore
import board  # type: ignore
from PIL import Image, ImageDraw, ImageFont  # type: ignore
import adafruit_rgb_display.st7789 as st7789  # type: ignore

mode_str = "ONLINE" if ONLINE_MODE else "LOCAL"
log(f"Launching VLT ({mode_str}): interval={CAPTURE_EVERY}s cam_index={CAM_INDEX} size={FRAME_W}x{FRAME_H} CS={CS_PIN_NAME} DC={DC_PIN_NAME}")
log(f"Project: {PROJECT_DIR}  Logs: {LOG_DIR}")
if ONLINE_MODE: log(f"Online endpoint: {ONLINE_BASE}")
log(f"Ollama: base={OLLAMA_BASE} model={OLLAMA_MODEL}")

try:
    cs_pin = digitalio.DigitalInOut(getattr(board, CS_PIN_NAME))
    dc_pin = digitalio.DigitalInOut(getattr(board, DC_PIN_NAME))
    reset_pin = None
    BAUDRATE = 64_000_000
    spi = board.SPI()
    disp = st7789.ST7789(spi, cs=cs_pin, dc=dc_pin, rst=reset_pin, baudrate=BAUDRATE, width=135, height=240, x_offset=53, y_offset=40)
    height = disp.width
    width  = disp.height
    image = Image.new("RGB", (width, height))
    rotation = 90
    draw = ImageDraw.Draw(image)
    backlight = digitalio.DigitalInOut(board.D22); backlight.switch_to_output(value=True)
    FONT_SMALL = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
    MONO       = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 24)
    buttonA = digitalio.DigitalInOut(board.D23); buttonB = digitalio.DigitalInOut(board.D24)
    buttonA.switch_to_input(pull=digitalio.Pull.UP); buttonB.switch_to_input(pull=digitalio.Pull.UP)
    log("Display initialized.")
except Exception as e:
    log(f"FATAL: Display init failed: {e}")
    raise

def clear_screen(): draw.rectangle((0, 0, width, height), outline=0, fill=(0, 0, 0))
def put_text(x: int, y: int, text: str, font, color=(255,255,255)) -> int:
    draw.text((x, y), text, font=font, fill=color)
    bbox = draw.textbbox((x, y), text, font=font)
    return bbox[3] - bbox[1]

cap = cv2.VideoCapture(CAM_INDEX, cv2.CAP_V4L2)
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_W)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_H)
if not cap.isOpened():
    log("FATAL: Could not open webcam. Check /dev/video* and v4l2-ctl."); sys.exit(1)
else:
    log("Camera opened OK.")

def save_frame(img_bgr) -> Path:
    ts = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")[:-3]
    path = IMG_DIR / f"frame_{ts}.jpg"
    ok = cv2.imwrite(str(path), img_bgr)
    if not ok: log(f"WARNING: cv2.imwrite returned False for {path}")
    return path

server_proc = None
server_log_fp = None

if not ONLINE_MODE:
    SERVER_CMD = ["node", str(PROJECT_DIR / "fastvlm_server.mjs")]
    SERVER_LOG = LOG_DIR / "fastvlm_server.log"
    server_log_fp = open(SERVER_LOG, "a", buffering=1, encoding="utf-8")
    env = os.environ.copy(); env["VLM_PORT"] = str(SERVER_PORT)
    env.setdefault("VLM_THREADS","2"); env.setdefault("VLM_QUIET","1"); env.setdefault("VLM_PROGRESS","0"); env.setdefault("VLM_DEBUG","1")
    _preexec = (lambda: os.nice(10)) if hasattr(os, "nice") else None
    try:
        server_proc = subprocess.Popen(SERVER_CMD, cwd=str(PROJECT_DIR), stdin=subprocess.DEVNULL, stdout=server_log_fp, stderr=server_log_fp, text=True, bufsize=1, env=env, start_new_session=True, preexec_fn=_preexec)
        log(f"Started FastVLM server pid={server_proc.pid} cmd={' '.join(SERVER_CMD)}"); log(f"Server logs -> {SERVER_LOG}")
    except Exception as e:
        log(f"FATAL: Could not start FastVLM server: {e}"); raise

def _http_json(method: str, url: str, payload: Optional[dict]=None, timeout: float=10.0) -> Tuple[int, dict]:
    data = None
    if payload is not None: data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json; charset=utf-8"); req.add_header("Accept", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = resp.getcode(); body = resp.read().decode("utf-8", "ignore")
            try: return status, (json.loads(body) if body else {})
            except Exception: return status, {"ok": False, "error": "invalid json from server"}
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "ignore")
        try: return e.code, (json.loads(body) if body else {"ok": False})
        except Exception: return e.code, {"ok": False, "error": body or str(e)}
    except urllib.error.URLError as e:
        raise RuntimeError(f"HTTP error to {url}: {e}")

def _http_multipart(url: str, fields: dict, files: dict, timeout: float = 60.0) -> Tuple[int, dict]:
    boundary = "----VLTBoundary" + uuid.uuid4().hex; CRLF = b"\r\n"; body = bytearray()
    for name, value in (fields or {}).items():
        body.extend(b"--" + boundary.encode("ascii") + CRLF)
        body.extend(f'Content-Disposition: form-data; name="{name}"'.encode("utf-8") + CRLF + CRLF)
        body.extend(str(value).encode("utf-8") + CRLF)
    for name, (filename, blob, ctype) in (files or {}).items():
        ctype = ctype or mimetypes.guess_type(filename)[0] or "application/octet-stream"
        body.extend(b"--" + boundary.encode("ascii") + CRLF)
        headers = (f'Content-Disposition: form-data; name="{name}"; filename="{os.path.basename(filename)}"{CRLF.decode()}' f"Content-Type: {ctype}{CRLF.decode()}").encode("utf-8")
        body.extend(headers + CRLF); body.extend(blob + CRLF)
    body.extend(b"--" + boundary.encode("ascii") + b"--" + CRLF)
    req = urllib.request.Request(url, data=bytes(body), method="POST")
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}"); req.add_header("Accept", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = resp.getcode(); body_text = resp.read().decode("utf-8", "ignore")
            try: return status, (json.loads(body_text) if body_text else {})
            except Exception: return status, {"ok": False, "error": "invalid json"}
    except urllib.error.HTTPError as e:
        body_text = e.read().decode("utf-8", "ignore")
        try: return e.code, (json.loads(body_text) if body_text else {"ok": False})
        except Exception: return e.code, {"ok": False, "error": body_text or str(e)}
    except urllib.error.URLError as e:
        raise RuntimeError(f"HTTP error to {url}: {e}")

def wait_for_server_ready(deadline_s: int = 420) -> None:
    t0 = time.time()
    while True:
        if server_proc and (server_proc.poll() is not None): raise RuntimeError("FastVLM server exited early. Check fastvlm_server.log.")
        try:
            status, body = _http_json("GET", f"{SERVER_BASE}/health", None, timeout=2.5)
            if status == 200 and body.get("ok") and body.get("ready"):
                log(f"Server READY: model={body.get('model')} backend={body.get('backend')} device={body.get('device')}"); return
        except Exception: pass
        if (time.time() - t0) > deadline_s: raise RuntimeError("Timeout waiting for VLM server to become ready")
        time.sleep(0.5)

def check_online_ready(timeout_s: int = 5) -> None:
    url = f"{ONLINE_BASE}/health"
    try:
        status, body = _http_json("GET", url, None, timeout=timeout_s)
        if status == 200 and body.get("ready") in (True, 1):
            log(f"Online READY: model={body.get('model')} device={body.get('device')} dtype={body.get('dtype')} max_batch=64")
        else:
            log(f"Online health non-200 or not ready (status={status}): {body}")
    except Exception as e: log(f"Online health check failed (ignored): {e}")

if ONLINE_MODE: check_online_ready()
else: wait_for_server_ready()

def fastvlm_infer_local(p: Path, prompt: str, max_new_tokens: int = 24, timeout_s: int = 60) -> str:
    deadline = time.time() + timeout_s; payload = {"image": str(p), "prompt": prompt, "max_new_tokens": max_new_tokens}; tries = 0
    while True:
        if time.time() > deadline: raise RuntimeError("Timeout waiting for inference response")
        tries += 1
        status, body = _http_json("POST", f"{SERVER_BASE}/infer", payload, timeout=timeout_s)
        if status == 200 and body.get("ok"):
            dt_ms = body.get("dt_ms"); 
            if dt_ms is not None: log(f"Infer OK in {dt_ms} ms (try={tries})")
            return (body.get("text") or "").strip()
        if status in (503, 409): time.sleep(0.25); continue
        raise RuntimeError(f"Server error {status}: {body.get('error') or body}")

def fastvlm_infer_online(p: Path, prompt: str, max_new_tokens: int = 5, min_new_tokens: int = 1, timeout_s: int = 60) -> str:
    t0 = time.time()
    with open(p, "rb") as f: blob = f.read()
    fields = {"prompt": prompt, "max_new_tokens": str(int(max_new_tokens)), "min_new_tokens": str(int(min_new_tokens))}
    files = {"image": (p.name, blob, mimetypes.guess_type(p.name)[0] or "image/jpeg")}
    status, body = _http_multipart(f"{ONLINE_BASE}/caption", fields, files, timeout=timeout_s)
    if status == 200 and isinstance(body, dict) and ("caption" in body):
        log(f"Online infer OK in {int((time.time()-t0)*1000)} ms"); return str(body.get("caption") or "").strip()
    err = body.get("error") if isinstance(body, dict) else body
    raise RuntimeError(f"Online server error {status}: {err}")

def ollama_generate(prompt: str, model: Optional[str] = None, timeout_s: Optional[int] = None) -> str:
    model = model or OLLAMA_MODEL; timeout_s = timeout_s or OLLAMA_TIMEOUT_S
    status, body = _http_json("POST", f"{OLLAMA_BASE}/api/generate", {"model": model, "prompt": prompt, "stream": False}, timeout=float(timeout_s))
    if status == 200 and isinstance(body, dict):
        resp = body.get("response")
        if isinstance(resp, str): return resp.strip()
        raise RuntimeError(f"Ollama: missing 'response' in body: keys={list(body.keys())}")
    err = body.get("error") or body.get("message") if isinstance(body, dict) else None
    raise RuntimeError(f"Ollama error {status}: {err or body}")

TIME_24H_RE = re.compile(r"\b([01]?\d|2[0-3]):([0-5]\d)(?::[0-5]\d)?\b")
TIME_12H_RE = re.compile(r"\b(1[0-2]|0?[1-9]):([0-5]\d)\s*([AaPp][Mm])\b")
WORDS_TO_TIME = {"noon": "12:00", "midday": "12:00", "mid-night": "00:00", "midnight": "00:00"}

def parse_time_guess(text: str) -> Optional[str]:
    t = (text or "").strip()
    m = TIME_24H_RE.search(t)
    if m: hh = int(m.group(1)); mm = m.group(2); return f"{hh:02d}:{mm}"
    m = TIME_12H_RE.search(t)
    if m:
        h = int(m.group(1)); mm = m.group(2); ampm = m.group(3).lower()
        if ampm == "pm" and h != 12: h += 12
        if ampm == "am" and h == 12: h = 0
        return f"{h:02d}:{mm}"
    tl = t.lower()
    for k, v in WORDS_TO_TIME.items():
        if k in tl: return v
    return None

def now_local() -> datetime.datetime: return datetime.datetime.now()

state_lock = threading.Lock()
last_img_path: Optional[Path] = None
last_vlm_text: str = ""
vlm_raw = ""
llm_raw = ""
ai_parsed = ""
last_infer_ts = 0.0

def build_time_prompt(vlm_text: str) -> str:
    return ("You are a time estimator. Based ONLY on the following visual/lighting description, estimate the local clock time as HH:MM in 24-hour format. If uncertain, give your BEST plausible estimate. Output ONLY the time in the format HH:MM. No words, no seconds, no explanations.\n\nDescription:\n"
            f"{vlm_text.strip()}\n\nAnswer:\n")

class Screen(IntEnum):
    TIME = 0
    IMAGE = 1
    DESC  = 2

screen = Screen.TIME
_last_nav_ts = 0.0
_NAV_DEBOUNCE_S = 0.18

def _nav_read() -> Tuple[bool, bool]:
    return (buttonA.value == False, buttonB.value == False)

def _render_full_image_to_buffer(img: Image.Image) -> None:
    img_ratio = img.width / img.height; buf_ratio = width / height
    if buf_ratio < img_ratio:
        scaled_width  = int(height * img_ratio); scaled_height = height
    else:
        scaled_width  = width; scaled_height = int(width / img_ratio)
    img = img.resize((scaled_width, scaled_height), Image.BICUBIC)
    x = (scaled_width  - width)//2; y = (scaled_height - height)//2
    img = img.crop((x, y, x + width, y + height)); image.paste(img)

def draw_time_screen(sys_time_str: str, ai_age_s: int) -> None:
    clear_screen()
    y = 4
    with state_lock:
        ap = ai_parsed or "N/A"
    y += put_text(6, y, "VLT (AI):", FONT_SMALL, (255, 200, 0))
    y += put_text(6, y, ap, MONO, (255, 255, 255))
    y += 4
    y += put_text(6, y, "System:", FONT_SMALL, (0, 200, 255))
    y += put_text(6, y, sys_time_str.split(" ")[1], MONO, (180, 255, 255))
    put_text(6, height - 22, f"{ai_age_s}s ago", FONT_SMALL, (150, 150, 150))

def draw_image_screen() -> None:
    clear_screen()
    with state_lock:
        p = last_img_path
    if p and p.exists():
        try:
            with Image.open(p) as im:
                im = im.convert("RGB"); _render_full_image_to_buffer(im)
        except Exception as e:
            clear_screen(); put_text(6, 6, f"Image error: {e}", FONT_SMALL, (255, 80, 80))
    else:
        put_text(6, 6, "No image yet.", FONT_SMALL, (200, 200, 200))

def draw_desc_screen() -> None:
    clear_screen()
    with state_lock:
        desc = (last_vlm_text or "(none)").strip()
    put_text(6, 4, "VLM description:", FONT_SMALL, (255, 200, 0))
    max_chars = max(12, width // 11)
    wrapped = textwrap.wrap(desc, width=max_chars)
    lines = wrapped[:6]; y = 28
    for ln in lines:
        y += put_text(6, y, ln, FONT_SMALL, (230, 230, 230))
    if len(wrapped) > len(lines):
        put_text(6, height - 20, "… (truncated)", FONT_SMALL, (140, 140, 140))

def draw_screen(force: Optional[Screen] = None) -> None:
    s = force if force is not None else screen
    sys_time = now_local().strftime("%Y-%m-%d %H:%M:%S")
    with state_lock:
        age = int(time.time() - last_infer_ts) if last_infer_ts else 0
    if s == Screen.TIME: draw_time_screen(sys_time, age)
    elif s == Screen.IMAGE: draw_image_screen()
    else: draw_desc_screen()
    try: disp.image(image, rotation)
    except Exception as e: log(f"WARNING: disp.image failed: {e}")

def _handle_nav_and_redraw() -> None:
    global screen, _last_nav_ts
    a, b = _nav_read()
    now = time.time()
    if (now - _last_nav_ts) < _NAV_DEBOUNCE_S: return
    changed = False
    if a and not b:
        screen = Screen((screen - 1) % 3); changed = True
    elif b and not a:
        screen = Screen((screen + 1) % 3); changed = True
    if changed:
        _last_nav_ts = now
        draw_screen()

def worker_loop(stop_evt: threading.Event):
    global last_img_path, last_vlm_text, vlm_raw, llm_raw, ai_parsed, last_infer_ts
    if not CSV_FILE.exists():
        with open(CSV_FILE, "w", newline="") as f:
            csv.writer(f).writerow(["mode","utc_captured","system_time","vlm_raw","llm_raw","ai_parsed","image_path"])
    next_capture = 0.0
    while not stop_evt.is_set():
        if time.time() >= next_capture:
            ok, frame = cap.read()
            log(f"Camera read ok={ok} shape={None if not ok else frame.shape}")
            if ok:
                img_path = save_frame(frame)
                with state_lock:
                    last_img_path = img_path
                log(f"Saved frame to {img_path}")
                try:
                    log(f"Sending prompt to VLM: {VLT_PROMPT!r}")
                    if ONLINE_MODE:
                        vtxt = fastvlm_infer_online(img_path, VLT_PROMPT, max_new_tokens=256, min_new_tokens=196, timeout_s=INFER_TIMEOUT_S)
                    else:
                        vtxt = fastvlm_infer_local(img_path, VLT_PROMPT, max_new_tokens=MAX_NEW_TOKENS, timeout_s=INFER_TIMEOUT_S)
                    log(f"VLM raw: {vtxt}")
                    llm_prompt = build_time_prompt(vtxt or "")
                    log(f"Ollama prompt (truncated to 200 chars): {llm_prompt[:200].replace(os.linesep,' ')}...")
                    ltxt = ollama_generate(llm_prompt, model=OLLAMA_MODEL, timeout_s=OLLAMA_TIMEOUT_S)
                    log(f"Ollama raw: {ltxt}")
                    aparsed = parse_time_guess(ltxt) or "N/A"
                    log(f"Parsed: {aparserd}" if False else f"Parsed: {aparsed}")  # keep format; avoid linter
                    with state_lock:
                        vlm_raw = vtxt or ""
                        llm_raw = ltxt or ""
                        ai_parsed = aparsed
                        last_vlm_text = vlm_raw
                        last_infer_ts = time.time()
                    with open(CSV_FILE, "a", newline="") as f:
                        csv.writer(f).writerow([mode_str, datetime.datetime.utcnow().isoformat(timespec="seconds"), now_local().strftime("%Y-%m-%d %H:%M:%S"), vlm_raw, llm_raw, ai_parsed, str(img_path)])
                    if screen != Screen.TIME:
                        draw_screen()
                except Exception as e:
                    log(f"ERROR during infer: {e}")
                    with state_lock:
                        llm_raw = f"ERR: {e}"
                        ai_parsed = "N/A"
                        last_infer_ts = time.time()
            else:
                log("ERROR: camera returned no frame")
                with state_lock:
                    ai_parsed = "N/A"
                    last_infer_ts = time.time()
            next_capture = time.time() + CAPTURE_EVERY
        else:
            time.sleep(0.02)

stop_event = threading.Event()
worker = threading.Thread(target=worker_loop, args=(stop_event,), daemon=True)
worker.start()

try:
    while True:
        _handle_nav_and_redraw()
        if screen == Screen.TIME:
            draw_screen(Screen.TIME)
        time.sleep(0.02)
except KeyboardInterrupt:
    log("KeyboardInterrupt: exiting...")
except Exception as e:
    log(f"FATAL (main loop): {e}"); raise
finally:
    try:
        stop_event.set()
        worker.join(timeout=2.0)
    except Exception: pass
    try:
        cap.release(); log("Camera released.")
    except Exception as e:
        log(f"Camera release error (ignored): {e}")
    if not ONLINE_MODE:
        try: _http_json("POST", f"{SERVER_BASE}/shutdown", {}, timeout=2.5)
        except Exception: pass
        try:
            if server_proc and (server_proc.poll() is None):
                server_proc.terminate()
                try: server_proc.wait(3)
                except subprocess.TimeoutExpired: server_proc.kill()
            log("FastVLM server terminated.")
        except Exception as e: log(f"Server terminate error (ignored): {e}")
        try:
            if server_log_fp: server_log_fp.close()
        except Exception: pass
