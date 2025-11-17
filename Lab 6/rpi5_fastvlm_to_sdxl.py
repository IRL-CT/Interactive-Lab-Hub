#!/usr/bin/env python3
# Full Raspberry Pi 5 client:
# - Captures camera frames
# - Runs FastVLM (local or --online via VLT_ONLINE_BASE) with a *normal* descriptive prompt
# - Prints the FULL FastVLM caption
# - Transforms that caption using a local Qwen 0.5B instruct model via Ollama
#   (style depends on selected mode 1–5)
# - Calls SDXL /generate (preempt) with the *transformed* caption as prompt
# - Subscribes to MQTT frames (WSS or TCP) and displays on PiTFT (if available)
# - Supports 5 style modes, switchable via PiTFT buttons:
#   Mode 1: Normal (no stylistic change, just clean rewrite)
#   Mode 2: Anime comics style
#   Mode 3: Medieval age style
#   Mode 4: Pixel RPG style
#   Mode 5: Cyberpunk (super modern technology) style
#
# Buttons:
#   - "Up"  button: previous mode (wraps 1 <- 5)
#   - "Down" button: next mode (wraps 5 -> 1)
#
# Qwen / Ollama config (env, with defaults):
#   OLLAMA_BASE  = http://127.0.0.1:11434
#   OLLAMA_MODEL = qwen:0.5b

import os, sys, time, json, uuid, mimetypes, threading, io, base64, textwrap, subprocess
from pathlib import Path
from typing import Optional, Tuple
import urllib.request, urllib.error

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# -------------------- Config / env --------------------
ONLINE_MODE     = any(a.lower() in ("online", "--online", "-o") for a in sys.argv[1:])
VLT_ONLINE_BASE = os.environ.get("VLT_ONLINE_BASE", "https://lamp-hint-documents-shortly.trycloudflare.com")

VLM_PORT        = int(os.environ.get("VLM_PORT", "17860"))
SERVER_BASE     = f"http://127.0.0.1:{VLM_PORT}"  # local FastVLM server if not ONLINE_MODE

# SDXL API base (prefer Cloudflare URL via SDXL_BASE)
# SDXL_BASE = os.environ.get("SDXL_BASE")
SDXL_BASE = os.environ.get("SDXL_BASE", "https://academic-connectors-quizzes-hip.trycloudflare.com")
# if not SDXL_BASE:
#     SDXL_HOST = os.environ.get("SDXL_HOST", "192.168.1.100").strip()
#     SDXL_PORT = int(os.environ.get("SDXL_PORT", "7985"))
#     SDXL_BASE = f"http://{SDXL_HOST}:{SDXL_PORT}"

# MQTT (subscribe) — can be mqtt://host:1883 or wss://host[:port]/path via MQTT_URL
VIDEO_UID   = os.environ.get("VIDEO_UID", "rpi5-one").strip()  # unique per device
MQTT_URL    = os.environ.get("MQTT_URL", "wss://cpu-databases-trees-andreas.trycloudflare.com/") # e.g. wss://cpu-...trycloudflare.com/  (path "/" by default)
MQTT_HOST   = os.environ.get("MQTT_HOST", "127.0.0.1")
MQTT_PORT   = int(os.environ.get("MQTT_PORT", "1883"))
MQTT_TOPIC  = os.environ.get("MQTT_TOPIC", f"sdxl/frames/{VIDEO_UID}")

# Camera + cadence
CAPTURE_EVERY = float(os.environ.get("ACTORS_INTERVAL", "2.0"))  # seconds between prompts
FRAME_W       = int(os.environ.get("VLT_W", "640"))
FRAME_H       = int(os.environ.get("VLT_H", "480"))
CAM_INDEX     = int(os.environ.get("VLT_CAM_INDEX", "0"))

# Base prompt to “describe any actors” — ALWAYS used for FastVLM (no style here)
BASE_ACTORS_PROMPT = os.environ.get(
    "ACTORS_PROMPT",
    "Describe what you see in detail. "
    "Include count, clothing, poses, gaze, and emotions."
)

# -------------------- Ollama / Qwen config --------------------
OLLAMA_BASE   = os.environ.get("OLLAMA_BASE", "http://127.0.0.1:11434").rstrip("/")
OLLAMA_MODEL  = os.environ.get("OLLAMA_MODEL", "qwen2.5:0.5b-instruct")
OLLAMA_TIMEOUT = float(os.environ.get("OLLAMA_TIMEOUT", "30.0"))

# -------------------- Mode definitions --------------------
# 5 modes:
# 1 = normal (neutral rewrite)
# 2 = anime comics style
# 3 = medieval age style
# 4 = pixel RPG style
# 5 = cyberpunk style
#
# These instructions are given to Qwen to *rewrite* the FastVLM caption.
MODE_DEFS = [
    {
        "name": "Normal",
        "instruction": (
            "You will receive a plain description of a scene. "
            "Rewrite it in clear, natural English without changing the meaning or adding new details. "
            "Keep the tone neutral and descriptive.\n"
        ),
    },
    {
        "name": "Anime comics",
        "instruction": (
            "You are a writer of anime comic panels. "
            "Rewrite the scene description as if it were an anime comic caption. "
            "Use energetic anime style language, dynamic action, sound effects, and stylized expressions. "
            "Keep all factual details (counts, clothing, poses) but make it feel like a page from a manga.\n"
        ),
    },
    {
        "name": "Medieval age",
        "instruction": (
            "You are a medieval bard describing a scene from a fantasy tale. "
            "Rewrite the scene description in a medieval style, with language that evokes knights, peasants, "
            "taverns, castles, scrolls, and old legends. "
            "Keep the factual details but present them as if told in the medieval ages.\n"
        ),
    },
    {
        "name": "Pixel RPG",
        "instruction": (
            "You are narrating a retro pixel-art RPG game. "
            "Rewrite the scene description as if it were describing a pixel RPG screen. "
            "Mention sprites, tiles, stats, inventory, and 16-bit game vibes where appropriate. "
            "Keep the facts, but frame them as a game scene.\n"
        ),
    },
    {
        "name": "Cyberpunk",
        "instruction": (
            "You are narrating a cyberpunk scene in a high-tech neon future. "
            "Rewrite the scene description with references to neon lights, holograms, chrome, implants, "
            "augmented reality, and futuristic cityscapes. "
            "Keep all factual details but present them in a cyberpunk style.\n"
        ),
    },
]

# Index into MODE_DEFS (0-based; 0 = mode 1, ..., 4 = mode 5)
# Start in cyberpunk mode if you like; adjust as desired.
CURRENT_MODE_INDEX = 4

# Paths / logs
PROJECT_DIR = Path(__file__).resolve().parent
LOG_DIR     = PROJECT_DIR / "vlt_logs"
IMG_DIR     = LOG_DIR / "images"
LOG_DIR.mkdir(parents=True, exist_ok=True)
IMG_DIR.mkdir(parents=True, exist_ok=True)

def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)

def get_mode_label() -> str:
    """Human-readable label for the current mode."""
    idx = CURRENT_MODE_INDEX
    mode = MODE_DEFS[idx]
    return f"Mode {idx+1}: {mode['name']}"

def get_mode_prompt(index: Optional[int] = None) -> str:
    """
    Return the instruction text for a given mode index (or current mode if index is None).
    This is fed to Qwen to control the rewrite style.
    """
    if index is None:
        index = CURRENT_MODE_INDEX
    return MODE_DEFS[index]["instruction"]

# Try to stop PiTFT boot screen (if present)
def preempt_boot_screen() -> None:
    try:
        subprocess.run(
            ["sudo", "-n", "systemctl", "stop", "pitft-boot-screen.service"],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception as e:
        log(f"systemctl stop attempt error (ignored): {e}")
    try:
        subprocess.run(["pkill", "-TERM", "-f", "python.*screen_boot_script.py"], check=False)
        time.sleep(0.8)
        subprocess.run(["pkill", "-KILL", "-f", "python.*screen_boot_script.py"], check=False)
    except Exception as e:
        log(f"pkill fallback error (ignored): {e}")

preempt_boot_screen()

# -------------------- HTTP helpers --------------------
def _http_json(method: str, url: str, payload: Optional[dict]=None, timeout: float=10.0) -> Tuple[int, dict]:
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json; charset=utf-8")
    req.add_header("Accept", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = resp.getcode()
            body = resp.read().decode("utf-8", "ignore")
            return status, (json.loads(body) if body else {})
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "ignore")
        try:
            return e.code, (json.loads(body) if body else {"ok": False})
        except Exception:
            return e.code, {"ok": False, "error": body or str(e)}
    except urllib.error.URLError as e:
        raise RuntimeError(f"HTTP error to {url}: {e}")

def _http_multipart(url: str, fields: dict, files: dict, timeout: float = 60.0) -> Tuple[int, dict]:
    boundary = "----VLTBoundary" + uuid.uuid4().hex
    CRLF = b"\r\n"
    body = bytearray()
    for name, value in (fields or {}).items():
        body.extend(b"--" + boundary.encode("ascii") + CRLF)
        body.extend(f'Content-Disposition: form-data; name="{name}"'.encode("utf-8") + CRLF + CRLF)
        body.extend(str(value).encode("utf-8") + CRLF)
    for name, (filename, blob, ctype) in (files or {}).items():
        ctype = ctype or mimetypes.guess_type(filename)[0] or "application/octet-stream"
        body.extend(b"--" + boundary.encode("ascii") + CRLF)
        headers = (
            f'Content-Disposition: form-data; name="{name}"; filename="{os.path.basename(filename)}"{CRLF.decode()}'
            f"Content-Type: {ctype}{CRLF.decode()}"
        ).encode("utf-8")
        body.extend(headers + CRLF)
        body.extend(blob + CRLF)
    body.extend(b"--" + boundary.encode("ascii") + b"--" + CRLF)
    req = urllib.request.Request(url, data=bytes(body), method="POST")
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    req.add_header("Accept", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = resp.getcode()
            body_text = resp.read().decode("utf-8", "ignore")
            try:
                return status, (json.loads(body_text) if body_text else {})
            except Exception:
                return status, {"ok": False, "error": "invalid json"}
    except urllib.error.HTTPError as e:
        body_text = e.read().decode("utf-8", "ignore")
        try:
            return e.code, (json.loads(body_text) if body_text else {"ok": False})
        except Exception:
            return e.code, {"ok": False, "error": body_text or str(e)}
    except urllib.error.URLError as e:
        raise RuntimeError(f"HTTP error to {url}: {e}")

# -------------------- FastVLM (local or online) --------------------
def fastvlm_infer_local(path: Path, prompt: str, max_new_tokens: int = 96, timeout_s: float = 60.0) -> str:
    payload = {"image": str(path), "prompt": prompt, "max_new_tokens": max_new_tokens}
    status, body = _http_json("POST", f"{SERVER_BASE}/infer", payload, timeout=timeout_s)
    if status == 200 and body.get("ok"):
        return (body.get("text") or "").strip()
    raise RuntimeError(f"FastVLM local error {status}: {body}")

def fastvlm_infer_online(path: Path, prompt: str, max_new_tokens: int = 128, timeout_s: float = 60.0) -> str:
    with open(path, "rb") as f:
        blob = f.read()
    fields = {"prompt": prompt, "max_new_tokens": str(int(max_new_tokens))}
    files = {"image": (path.name, blob, mimetypes.guess_type(path.name)[0] or "image/jpeg")}
    status, body = _http_multipart(f"{VLT_ONLINE_BASE}/caption", fields, files, timeout=timeout_s)
    if status == 200 and isinstance(body, dict) and ("caption" in body):
        return str(body.get("caption") or "").strip()
    raise RuntimeError(f"FastVLM online error {status}: {body}")

# -------------------- Ollama: transform caption with Qwen --------------------
def transform_caption_with_ollama(caption: str, mode_index: int) -> str:
    """
    Send the FastVLM caption + mode-specific instruction to a local Qwen via Ollama,
    and get back a styled caption. On failure, returns the original caption.
    """
    caption = (caption or "").strip()
    if not caption:
        return caption

    instruction = get_mode_prompt(mode_index)
    prompt_text = (
        f"{instruction}\n"
        "Original scene description:\n"
        f"{caption}\n\n"
        "Rewritten description:\n"
    )

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt_text,
        "stream": False,
    }

    try:
        url = f"{OLLAMA_BASE}/api/generate"
        status, body = _http_json("POST", url, payload, timeout=OLLAMA_TIMEOUT)
        if status == 200 and isinstance(body, dict):
            resp = (body.get("response") or "").strip()
            if resp:
                return resp
            else:
                log("Ollama returned empty response; falling back to original caption.")
        else:
            log(f"Ollama error {status}: {body}")
    except Exception as e:
        log(f"Ollama transform error: {e}")

    return caption

# -------------------- Camera --------------------
import cv2  # type: ignore

cap = cv2.VideoCapture(CAM_INDEX, cv2.CAP_V4L2)
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_W)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_H)
# Try to keep the driver from buffering lots of old frames so we always get the freshest one
try:
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
except Exception:
    pass
if not cap.isOpened():
    print("FATAL: Could not open webcam.")
    sys.exit(1)

def save_frame(img_bgr) -> Path:
    ts = time.strftime("%Y%m%d_%H%M%S")
    p = IMG_DIR / f"frame_{ts}.jpg"
    ok = cv2.imwrite(str(p), img_bgr)
    if not ok:
        print("WARN: cv2.imwrite returned False")
    return p

# -------------------- PiTFT display (optional) + buttons --------------------
DISP_OK = True
btn_up = None     # "Up" button DigitalInOut (if available)
btn_down = None   # "Down" button DigitalInOut (if available)

try:
    import digitalio  # type: ignore
    import board      # type: ignore
    from PIL import Image, ImageDraw, ImageFont  # type: ignore
    import adafruit_rgb_display.st7789 as st7789  # type: ignore

    cs_pin = digitalio.DigitalInOut(getattr(board, os.environ.get("VLT_CS_PIN", "D5")))
    dc_pin = digitalio.DigitalInOut(getattr(board, os.environ.get("VLT_DC_PIN", "D25")))
    reset_pin = None
    BAUDRATE = 64_000_000
    spi = board.SPI()
    disp = st7789.ST7789(
        spi,
        cs=cs_pin,
        dc=dc_pin,
        rst=reset_pin,
        baudrate=BAUDRATE,
        width=135,
        height=240,
        x_offset=53,
        y_offset=40,
    )
    height = disp.width
    width  = disp.height
    rotation = 90
    image_buf = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(image_buf)
    try:
        FONT_SMALL = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18
        )
    except Exception:
        from PIL import ImageFont as _ImageFont
        FONT_SMALL = _ImageFont.load_default()

    # Button pins: default to BCM 23 (up) and BCM 24 (down) via board.D23 / board.D24
    # Override via env vars VLT_BTN_UP_PIN / VLT_BTN_DOWN_PIN if needed.
    btn_up_pin_name = os.environ.get("VLT_BTN_UP_PIN", "D23")
    btn_down_pin_name = os.environ.get("VLT_BTN_DOWN_PIN", "D24")
    try:
        btn_up = digitalio.DigitalInOut(getattr(board, btn_up_pin_name))
        btn_up.direction = digitalio.Direction.INPUT
        btn_up.pull = digitalio.Pull.UP  # pressed -> False

        btn_down = digitalio.DigitalInOut(getattr(board, btn_down_pin_name))
        btn_down.direction = digitalio.Direction.INPUT
        btn_down.pull = digitalio.Pull.UP  # pressed -> False

        log(f"Buttons initialized on {btn_up_pin_name} (up), {btn_down_pin_name} (down)")
    except Exception as e:
        log(f"Button init failed (continuing without mode buttons): {e}")
        btn_up = None
        btn_down = None

except Exception as e:
    log(f"Display init failed (continuing headless): {e}")
    DISP_OK = False
    from PIL import Image, ImageDraw, ImageFont  # still needed for MQTT render
    height, width, rotation = 135, 240, 0
    image_buf = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(image_buf)
    try:
        FONT_SMALL = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18
        )
    except Exception:
        FONT_SMALL = ImageFont.load_default()

def _render_to_buf(img: Image.Image) -> None:
    img_ratio = img.width / img.height
    buf_ratio = width / height
    if buf_ratio < img_ratio:
        scaled_width, scaled_height = int(height * img_ratio), height
    else:
        scaled_width, scaled_height = width, int(width / img_ratio)
    img = img.resize((scaled_width, scaled_height), Image.BICUBIC)
    x = (scaled_width - width)//2
    y = (scaled_height - height)//2
    img = img.crop((x, y, x + width, y + height))
    image_buf.paste(img)

def show_text(lines):
    draw.rectangle((0, 0, width, height), fill=(0, 0, 0))
    y = 6
    for ln in lines:
        draw.text((6, y), ln, font=FONT_SMALL, fill=(255, 255, 255))
        y += 18
    if DISP_OK:
        try:
            disp.image(image_buf, rotation)
        except Exception as e:
            log(f"disp.image failed: {e}")

def show_mode_banner():
    """Display a small banner showing the current mode and button usage."""
    lines = [
        get_mode_label(),
        "",
        "UP: previous mode",
        "DOWN: next mode",
    ]
    show_text(lines)

# -------------------- MQTT subscribe to generated frames --------------------
last_frame_ts = 0.0

def mqtt_thread():
    from paho.mqtt import client as mqtt  # pip install paho-mqtt
    from urllib.parse import urlparse

    # Parse MQTT_URL if provided (supports mqtt://, ws://, wss://)
    if MQTT_URL:
        u = urlparse(MQTT_URL)
        transport = "websockets" if u.scheme in ("ws", "wss") else "tcp"
        host = u.hostname or MQTT_HOST
        port = u.port or (443 if u.scheme == "wss" else 80 if u.scheme == "ws" else MQTT_PORT)
        path = u.path if (u.path and u.path != "") else "/"  # default "/" for mosquitto websockets
        use_tls = (u.scheme == "wss")
    else:
        transport = "tcp"
        host = MQTT_HOST
        port = MQTT_PORT
        path = "/"
        use_tls = False

    client = mqtt.Client(
        client_id=f"pi5-subscriber-{uuid.uuid4().hex[:6]}",
        transport=transport,
        protocol=mqtt.MQTTv311,
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
    )
    if transport == "websockets":
        client.ws_set_options(path=path)
        if use_tls:
            client.tls_set()  # use system CAs
    client.reconnect_delay_set(min_delay=1, max_delay=30)

    def on_connect(client, userdata, flags, reason_code, properties=None):
        if reason_code == 0:
            log(f"MQTT connected; subscribing to {MQTT_TOPIC}")
            client.subscribe(MQTT_TOPIC, qos=0)
        else:
            log(f"MQTT connect failed: {reason_code}")

    def on_message(client, userdata, msg):
        global last_frame_ts
        try:
            data = json.loads(msg.payload.decode("utf-8"))
            b = base64.b64decode(data["b64"])
            from PIL import Image  # local import to avoid PiTFT import issues
            im = Image.open(io.BytesIO(b)).convert("RGB")
            _render_to_buf(im)
            if DISP_OK:
                disp.image(image_buf, rotation)
            last_frame_ts = time.time()
        except Exception as e:
            log(f"MQTT frame error: {e}")

    client.on_connect = on_connect
    client.on_message = on_message

    # Robust connect loop
    while True:
        try:
            log(f"MQTT connecting to {host}:{port} ({transport}{path})")
            client.connect(host, port, keepalive=60)
            client.loop_forever()
        except Exception as e:
            log(f"MQTT connect error to {host}:{port}: {e}; retrying in 3s")
            time.sleep(3)

# -------------------- Mode button polling thread --------------------
def mode_button_thread():
    global CURRENT_MODE_INDEX
    if (btn_up is None) or (btn_down is None):
        log("Mode button thread not started (buttons not available).")
        return

    # Initial states
    last_up = btn_up.value
    last_down = btn_down.value
    log(f"Mode buttons active. Starting at {get_mode_label()}")
    show_mode_banner()

    while True:
        try:
            val_up = btn_up.value
            val_down = btn_down.value

            # Buttons are wired with pull-ups: pressed => False
            # Detect falling edges (released -> pressed)
            if last_up and not val_up:
                # UP: previous mode (wrap-around)
                CURRENT_MODE_INDEX = (CURRENT_MODE_INDEX - 1) % len(MODE_DEFS)
                log(f"Mode changed (UP) -> {get_mode_label()}")
                show_mode_banner()

            if last_down and not val_down:
                # DOWN: next mode (wrap-around)
                CURRENT_MODE_INDEX = (CURRENT_MODE_INDEX + 1) % len(MODE_DEFS)
                log(f"Mode changed (DOWN) -> {get_mode_label()}")
                show_mode_banner()

            last_up = val_up
            last_down = val_down
            time.sleep(0.05)
        except Exception as e:
            log(f"Mode button thread error: {e}")
            time.sleep(0.5)

# -------------------- Main loop: capture -> FastVLM -> Qwen -> /generate --------------------
def main_loop():
    show_text([
        "Starting...",
        f"SDXL: {SDXL_BASE}",
        f"MQTT: {MQTT_URL or (MQTT_HOST+':'+str(MQTT_PORT))}",
        f"Topic: {MQTT_TOPIC}",
        get_mode_label(),
    ])
    time.sleep(0.5)

    # Optional SDXL health
    try:
        st, body = _http_json("GET", f"{SDXL_BASE}/", None, timeout=4.0)
        if st == 200 and body.get("ok"):
            log(f"SDXL ready: device={body.get('device')} mqtt={body.get('mqtt')}")
    except Exception as e:
        log(f"SDXL health check (ignored): {e}")

    # Strictly sequential loop:
    # - Capture ONE fresh frame
    # - FastVLM caption with BASE_ACTORS_PROMPT
    # - Transform caption via local Qwen (Ollama) using current mode style
    # - POST /generate to SDXL with transformed caption
    # - Sleep CAPTURE_EVERY and repeat
    while True:
        # Flush any stale frames from the driver buffer so we don't build up a backlog.
        flush_start = time.time()
        flushed = 0
        while True:
            # grab() throws away a frame without decoding it
            if not cap.grab():
                break
            flushed += 1
            # Don't spend more than ~100ms flushing
            if time.time() - flush_start > 0.1:
                break

        ok, frame = cap.read()
        if not ok:
            show_text(["Camera read failed", "Retrying..."])
            time.sleep(0.25)
            continue
        p = save_frame(frame)

        # Snapshot the mode at the time of capture
        mode_index_for_frame = CURRENT_MODE_INDEX
        mode_label_for_frame = f"Mode {mode_index_for_frame+1}: {MODE_DEFS[mode_index_for_frame]['name']}"

        try:
            # 1) Get plain caption from FastVLM using the *normal* base prompt
            if ONLINE_MODE:
                desc = fastvlm_infer_online(
                    p,
                    BASE_ACTORS_PROMPT,
                    max_new_tokens=128,
                    timeout_s=60.0,
                )
            else:
                desc = fastvlm_infer_local(
                    p,
                    BASE_ACTORS_PROMPT,
                    max_new_tokens=96,
                    timeout_s=60.0,
                )

            actors_last = (desc or "").strip()

            # Print FastVLM caption
            print(
                f"\n=== FastVLM caption (base) ===\n"
                + actors_last
                + "\n=== end FastVLM caption ===\n",
                flush=True,
            )

            # 2) Transform caption via Ollama/Qwen using current mode style
            styled_caption = transform_caption_with_ollama(actors_last, mode_index_for_frame)
            print(
                f"\n=== Stylized caption ({mode_label_for_frame}) ===\n"
                + styled_caption
                + "\n=== end stylized caption ===\n",
                flush=True,
            )

            # 3) Preempt/start video on SDXL with the *stylized* prompt
            payload = {
                "prompt": styled_caption or (actors_last or "no actors"),
                "negative_prompt": None,
                "steps": 1,
                "guidance_scale": 0.0,
                "width": 512,
                "height": 512,
                "video": True,
                "video_uid": VIDEO_UID,
                "preempt": True,
                "video_fps": 0.0,
                "max_frames": None,
            }
            st, body = _http_json(
                "POST",
                f"{SDXL_BASE}/generate",
                payload,
                timeout=6.0,
            )
            if st == 200 and body.get("ok"):
                pre = " (preempted)" if body.get("preempted") else ""
                log(f"SDXL video started{pre}: uid={body.get('uid')}")
            else:
                log(f"SDXL generate error {st}: {body}")

            # If frames haven't started arriving yet, show stylized text on screen
            if (time.time() - last_frame_ts) > 1.5:
                lines = [mode_label_for_frame]
                lines.extend(textwrap.wrap(styled_caption, width=22)[:5])
                show_text(lines)

        except Exception as e:
            log(f"Infer/POST error: {e}")
            # Small backoff on error so we don't hammer the services
            time.sleep(max(1.0, CAPTURE_EVERY))
            continue

        # Wait *after* the whole cycle so we never queue up screenshots
        if CAPTURE_EVERY > 0:
            time.sleep(CAPTURE_EVERY)

if __name__ == "__main__":
    # Start MQTT subscriber thread first so you see frames as soon as they come
    th_mqtt = threading.Thread(target=mqtt_thread, daemon=True)
    th_mqtt.start()

    # Start mode button polling thread (if buttons available)
    th_mode = threading.Thread(target=mode_button_thread, daemon=True)
    th_mode.start()

    try:
        main_loop()
    except KeyboardInterrupt:
        pass
