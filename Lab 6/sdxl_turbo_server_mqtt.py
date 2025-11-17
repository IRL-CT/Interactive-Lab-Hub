# sdxl_turbo_server_mqtt.py
import os
import io
import time
import uuid
import json
import base64
import threading
from datetime import datetime
from typing import Optional, Dict, Any

import torch
from fastapi import FastAPI
from pydantic import BaseModel
from PIL import Image
from diffusers import AutoPipelineForText2Image

# --- MQTT (optional, enable with MQTT_ENABLE=1) ---
# --- MQTT (single broker via URL) ---
MQTT_ENABLE = os.environ.get("MQTT_ENABLE", "1") == "1"
MQTT_URL = os.environ.get("MQTT_URL", "mqtt://127.0.0.1:1883")  # e.g. mqtt://127.0.0.1:1883  or  wss://mqtt-yourhost.trycloudflare.com/
MQTT_TOPIC_BASE = os.environ.get("MQTT_TOPIC_BASE", "sdxl/frames")
MQTT_QOS = int(os.environ.get("MQTT_QOS", "0"))

mqtt_client = None
def _build_mqtt_client_from_url(url: str):
    from urllib.parse import urlparse
    from paho.mqtt import client as mqtt
    u = urlparse(url)
    transport = "websockets" if u.scheme in ("ws","wss") else "tcp"
    host = u.hostname or "127.0.0.1"
    port = u.port or (443 if u.scheme=="wss" else 80 if u.scheme=="ws" else 1883)
    c = mqtt.Client(
        client_id=f"sdxl-{uuid.uuid4().hex[:6]}",
        transport=transport,
        protocol=mqtt.MQTTv311,
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
    )
    if transport == "websockets":
        c.ws_set_options(path=u.path or "/")
        if u.scheme == "wss":
            c.tls_set()  # use system CAs
    c.reconnect_delay_set(1, 30)
    c.connect_async(host, port, 60)
    c.loop_start()
    print(f"[MQTT] connecting -> {url}")
    return c

if MQTT_ENABLE and MQTT_URL:
    try:
        mqtt_client = _build_mqtt_client_from_url(MQTT_URL)
    except Exception as e:
        print(f"[MQTT] init failed (disabled): {e}")
        mqtt_client = None
else:
    print("[MQTT] disabled or no MQTT_URL; skipping MQTT.")


MODEL_ID = "stabilityai/sdxl-turbo"
print("Loading pipeline...")
pipe = AutoPipelineForText2Image.from_pretrained(
    MODEL_ID, torch_dtype=torch.float16, variant="fp16"
)

if torch.cuda.is_available():
    pipe.to("cuda")

for fn in ("enable_attention_slicing", "enable_vae_slicing", "enable_xformers_memory_efficient_attention"):
    try:
        getattr(pipe, fn)()
    except Exception:
        pass

try:
    torch.backends.cuda.matmul.allow_tf32 = True  # type: ignore
except Exception:
    pass

os.makedirs("images", exist_ok=True)
os.makedirs("videos", exist_ok=True)

app = FastAPI(title="SDXL-Turbo Server", version="1.2-mqtt-preempt")

# video_sessions[uid] = {"running": bool, "thread": Thread, "params": dict}
video_sessions: Dict[str, Dict[str, Any]] = {}


class GenerateRequest(BaseModel):
    prompt: str
    seed: Optional[int] = None
    width: Optional[int] = 512
    height: Optional[int] = 512
    steps: Optional[int] = 1
    guidance_scale: Optional[float] = 0.0
    negative_prompt: Optional[str] = None

    video: Optional[bool] = False
    video_uid: Optional[str] = None
    video_fps: Optional[float] = 0.0
    max_frames: Optional[int] = None

    # NEW: let callers flush/replace any running session with same uid
    preempt: Optional[bool] = False
    # Optional per-request override of MQTT topic (rarely needed)
    mqtt_topic: Optional[str] = None


@app.get("/")
def health():
    return {
        "ok": True,
        "model": MODEL_ID,
        "device": "cuda" if torch.cuda.is_available() else "cpu",
        "mqtt": bool(mqtt_client),
        "video_sessions": list(video_sessions.keys()),
    }


def _safe_dims(v: Optional[int], default: int) -> int:
    x = int(v or default)
    x = max(64, min(x, 1024))
    return x - (x % 8)


def _make_image(prompt: str,
                negative_prompt: Optional[str],
                steps: int,
                guidance_scale: float,
                width: int,
                height: int,
                seed: int) -> Image.Image:
    generator = torch.Generator(device="cuda" if torch.cuda.is_available() else "cpu").manual_seed(seed)
    with torch.inference_mode():
        out = pipe(
            prompt=prompt,
            negative_prompt=negative_prompt,
            num_inference_steps=steps,
            guidance_scale=guidance_scale,
            width=width,
            height=height,
            generator=generator,
        )
    return out.images[0]


def _video_worker(uid: str, params: Dict[str, Any]) -> None:
    """Continuously generate frames into videos/<uid>/ and publish over MQTT."""
    folder = os.path.join("videos", uid)
    os.makedirs(folder, exist_ok=True)

    prompt = params["prompt"]
    negative_prompt = params["negative_prompt"]
    width = params["width"]
    height = params["height"]
    steps = params["steps"]
    guidance_scale = params["guidance_scale"]
    base_seed = params["seed"]
    fps = params["video_fps"]
    max_frames = params["max_frames"]
    mqtt_topic = params.get("mqtt_topic") or f"{MQTT_TOPIC_BASE}/{uid}"

    frame_idx = 0
    last_tick = time.perf_counter()

    while video_sessions.get(uid, {}).get("running", False):
        seed = (base_seed + frame_idx) & 0xFFFFFFFF
        try:
            img = _make_image(
                prompt=prompt,
                negative_prompt=negative_prompt,
                steps=steps,
                guidance_scale=guidance_scale,
                width=width,
                height=height,
                seed=seed,
            )
            fname = os.path.join(folder, f"frame_{frame_idx:06d}_seed{seed}_{width}x{height}.png")
            img.save(fname)

            # --- MQTT publish (JPEG base64 for compactness) ---
            if mqtt_client is not None:
                try:
                    buf = io.BytesIO()
                    img.save(buf, format="JPEG", quality=85)
                    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
                    payload = {
                        "uid": uid,
                        "i": frame_idx,
                        "seed": seed,
                        "w": width,
                        "h": height,
                        "ts": time.time(),
                        "b64": b64,
                    }
                    mqtt_client.publish(mqtt_topic, json.dumps(payload), qos=MQTT_QOS, retain=False)
                except Exception as me:
                    # Don't crash the worker if MQTT fails
                    try:
                        with open(os.path.join(folder, f"mqtt_error_{frame_idx:06d}.txt"), "w", encoding="utf-8") as f:
                            f.write(str(me))
                    except Exception:
                        pass

        except Exception as e:
            try:
                with open(os.path.join(folder, f"error_{frame_idx:06d}.txt"), "w", encoding="utf-8") as f:
                    f.write(str(e))
            except Exception:
                pass

        frame_idx += 1
        if max_frames is not None and frame_idx >= max_frames:
            break

        if fps and fps > 0:
            target_dt = 1.0 / float(fps)
            now = time.perf_counter()
            elapsed = now - last_tick
            if elapsed < target_dt:
                time.sleep(target_dt - elapsed)
            last_tick = time.perf_counter()

    sess = video_sessions.get(uid)
    if sess:
        sess["running"] = False


@app.post("/generate")
def generate(req: GenerateRequest):
    w = _safe_dims(req.width, 512)
    h = _safe_dims(req.height, 512)
    steps = max(1, int(req.steps or 1))
    gs = float(req.guidance_scale if req.guidance_scale is not None else 0.0)
    seed = int(req.seed) if req.seed is not None else int.from_bytes(os.urandom(2), "little")

    if not req.video:
        t0 = time.time()
        try:
            img = _make_image(
                prompt=req.prompt,
                negative_prompt=req.negative_prompt,
                steps=steps,
                guidance_scale=gs,
                width=w,
                height=h,
                seed=seed,
            )
            ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = os.path.join("images", f"sdxl_turbo_{ts}_seed{seed}_{w}x{h}.png")
            img.save(filename)
            latency = time.time() - t0
            return {
                "ok": True,
                "mode": "single",
                "path": filename,
                "seed": seed,
                "width": w,
                "height": h,
                "steps": steps,
                "guidance_scale": gs,
                "latency_sec": round(latency, 3),
            }
        except Exception as e:
            return {"ok": False, "error": str(e), "mode": "single"}

    # ---- Video mode ----
    uid = (req.video_uid or uuid.uuid4().hex[:12].lower()).strip()
    folder = os.path.join("videos", uid)
    os.makedirs(folder, exist_ok=True)

    existing = video_sessions.get(uid)
    preempted = False
    if existing and existing.get("running") and req.preempt:
        # Stop the old session and wait briefly
        existing["running"] = False
        th = existing.get("thread")
        if th:
            try:
                th.join(timeout=2.0)
            except Exception:
                pass
        preempted = True

    # If a session is running and not preempting, just report it
    existing = video_sessions.get(uid)
    if existing and existing.get("running"):
        return {
            "ok": True,
            "mode": "video",
            "message": "Session already running",
            "uid": uid,
            "folder": folder,
        }

    params = {
        "prompt": req.prompt,
        "negative_prompt": req.negative_prompt,
        "width": w,
        "height": h,
        "steps": steps,
        "guidance_scale": gs,
        "seed": seed,
        "video_fps": float(req.video_fps or 0.0),
        "max_frames": req.max_frames,
        "mqtt_topic": req.mqtt_topic,
    }

    video_sessions[uid] = {"running": True, "params": params, "thread": None}
    th = threading.Thread(target=_video_worker, args=(uid, params), daemon=True)
    video_sessions[uid]["thread"] = th
    th.start()

    return {
        "ok": True,
        "mode": "video",
        "uid": uid,
        "folder": folder,
        "preempted": preempted,
        "message": "Video generation started",
        "params": {
            "width": w, "height": h, "steps": steps, "guidance_scale": gs,
            "seed": seed, "video_fps": params["video_fps"], "max_frames": req.max_frames,
        },
    }


@app.post("/stop_video/{uid}")
def stop_video(uid: str):
    sess = video_sessions.get(uid)
    if not sess:
        return {"ok": False, "message": f"No session found for uid={uid}"}
    sess["running"] = False
    th = sess.get("thread")
    if th:
        try:
            th.join(timeout=2.0)
        except Exception:
            pass
    return {"ok": True, "message": f"Stopped uid={uid}"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7985, reload=False, workers=1)
