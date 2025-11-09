import os
import sys
import time
import threading
from collections import deque
from typing import Optional, Deque, Dict

import cv2
from aiohttp import web
import asyncio

# =========================
# Config (override via env)
# =========================
DEVICE_INDEX = int(os.getenv("DEVICE_INDEX", "0"))
VIDEO_WIDTH  = int(os.getenv("VIDEO_WIDTH", "1280"))
VIDEO_HEIGHT = int(os.getenv("VIDEO_HEIGHT", "720"))
VIDEO_FPS    = int(os.getenv("VIDEO_FPS", "30"))
HOST         = os.getenv("HOST", "127.0.0.1")   # localhost only
PORT         = int(os.getenv("PORT", "7965"))
PROBE_MAX    = int(os.getenv("PROBE_MAX", "10"))  # fill dropdown only (no probing)
RAW_IDLE_SECONDS = int(os.getenv("RAW_IDLE_SECONDS", "60"))  # stop per-index sources after idle

# On Windows use DirectShow; on Linux prefer V4L2 (falls back to ANY if unavailable)
if sys.platform.startswith("win"):
    CAPTURE_BACKEND = cv2.CAP_DSHOW
else:
    CAPTURE_BACKEND = getattr(cv2, "CAP_V4L2", cv2.CAP_ANY)

# =========================
# Latest-frame buffer
# =========================
class LatestFrameBuffer:
    """Keep only the newest frame to minimize latency."""
    def __init__(self):
        self._q: Deque = deque(maxlen=1)
        self._lock = threading.Lock()
        self._cond = threading.Condition(self._lock)
        self._closed = False

    def push(self, item):
        with self._cond:
            self._q.clear()
            self._q.append(item)
            self._cond.notify_all()

    def get(self, timeout: float = 1.0):
        end = time.time() + timeout
        with self._cond:
            while not self._q and not self._closed:
                remaining = end - time.time()
                if remaining <= 0:
                    return None
                self._cond.wait(remaining)
            if self._closed:
                return None
            return self._q[-1]

    def close(self):
        with self._cond:
            self._closed = True
            self._cond.notify_all()

# =========================
# Camera source (DSHOW/V4L2 by index)
# =========================
class CameraSource:
    def __init__(self, index=0, width=1280, height=720, fps=30, backend=CAPTURE_BACKEND):
        self.index = index
        self.width = width
        self.height = height
        self.fps = fps
        self.backend = backend
        self.cap: Optional[cv2.VideoCapture] = None
        self.thread: Optional[threading.Thread] = None
        self.running = False
        self.latest = LatestFrameBuffer()
        self.last_access = time.time()

    def start(self):
        self.cap = cv2.VideoCapture(self.index, self.backend)
        if not self.cap.isOpened():
            raise RuntimeError(f"Could not open video device index={self.index}")

        # Configure for low latency
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH,  self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self.cap.set(cv2.CAP_PROP_FPS,          self.fps)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE,   1)

        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def _loop(self):
        while self.running:
            ok, frame = self.cap.read()
            if not ok:
                time.sleep(0.005)
                continue
            self.latest.push(frame)

    def read_latest(self, timeout: float = 0.5):
        self.last_access = time.time()
        return self.latest.get(timeout=timeout)

    def stop(self):
        self.running = False
        self.latest.close()
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)
        if self.cap:
            self.cap.release()

# =========================
# Main current camera (UI-controlled)
# =========================
camera_lock = threading.RLock()
camera: Optional[CameraSource] = None
current_index: Optional[int] = None
last_error: Optional[str] = None

def _get_current_if_matches(idx: int) -> Optional["CameraSource"]:
    """Return the current camera source if it's the same index and running."""
    with camera_lock:
        if current_index == idx and camera is not None and camera.running:
            return camera
    return None

def start_camera(index: int):
    global camera, current_index, last_error
    with camera_lock:
        # Stop existing
        if camera is not None:
            try:
                camera.stop()
            except Exception:
                pass
            camera = None
        # Start new
        cs = CameraSource(
            index=index,
            width=VIDEO_WIDTH,
            height=VIDEO_HEIGHT,
            fps=VIDEO_FPS,
            backend=CAPTURE_BACKEND
        )
        try:
            cs.start()
            camera = cs
            current_index = index
            last_error = None
        except Exception as e:
            last_error = str(e)
            current_index = None

# =========================
# Per-index raw sources (lazy, auto-gc)
# =========================
raw_lock = threading.RLock()
raw_sources: Dict[int, CameraSource] = {}  # index -> CameraSource

def get_or_start_raw(index: int) -> CameraSource:
    """Return an active source for this index, starting it if needed.

    IMPORTANT: If the requested index matches the currently open "current" camera,
    reuse it instead of opening the device a second time (Linux V4L2 often forbids
    concurrent opens for the same /dev/video*).
    """
    cur = _get_current_if_matches(index)
    if cur is not None:
        return cur
    with raw_lock:
        cs = raw_sources.get(index)
        if cs and cs.running:
            return cs
        # Start a new source
        cs = CameraSource(
            index=index,
            width=VIDEO_WIDTH,
            height=VIDEO_HEIGHT,
            fps=VIDEO_FPS,
            backend=CAPTURE_BACKEND
        )
        cs.start()
        raw_sources[index] = cs
        return cs

async def reap_idle_sources():
    """Background task: stop per-index sources that haven't been used recently."""
    while True:
        await asyncio.sleep(10)
        now = time.time()
        to_stop = []
        with raw_lock:
            for idx, src in list(raw_sources.items()):
                if not src.running:
                    to_stop.append(idx)
                    continue
                idle = now - src.last_access
                if idle > RAW_IDLE_SECONDS:
                    to_stop.append(idx)
            for idx in to_stop:
                try:
                    raw_sources[idx].stop()
                except Exception:
                    pass
                raw_sources.pop(idx, None)

# =========================
# HTML (simple selector + Raw buttons)
# =========================
HTML = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Local Drone Feed (MJPEG)</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    :root {{ color-scheme: dark; }}
    html, body {{ background:#0b0b0b; color:#eaeaea; font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;
                 height:100%; margin:0; }}
    header {{ display:flex; gap:.5rem; align-items:center; padding:12px 16px; background:#121212; border-bottom:1px solid #222; }}
    main {{ display:grid; place-items:center; padding:18px; }}
    img {{ width:95vw; max-width:1280px; height:auto; background:#000; border-radius:12px; }}
    select, button, a.button {{ background:#1c1c1c; color:#eaeaea; border:1px solid #333; border-radius:8px; padding:8px 10px; text-decoration:none; display:inline-block; }}
    small code {{ opacity:.8; }}
    .spacer {{ flex:1; }}
  </style>
</head>
<body>
  <header>
    <label for="cam">Camera index:</label>
    <select id="cam"></select>
    <button id="apply">Use</button>
    <a class="button" id="rawCur" href="/raw" target="_blank" rel="noopener">Raw (current)</a>
    <a class="button" id="rawIdx" href="#" target="_blank" rel="noopener">Raw(/idx)</a>
    <div class="spacer"></div>
    <small>Status: <code id="status">loading…</code></small>
  </header>
  <main>
    <img id="stream" src="/mjpeg" alt="Live stream" />
  </main>
  <script>
    const sel = document.getElementById('cam');
    const btn = document.getElementById('apply');
    const img = document.getElementById('stream');
    const statusEl = document.getElementById('status');
    const rawIdx = document.getElementById('rawIdx');

    const PROBE_MAX = {PROBE_MAX};
    for (let i=0; i<PROBE_MAX; i++) {{
      const o = document.createElement('option');
      o.value = i; o.textContent = 'Index ' + i;
      sel.appendChild(o);
    }}

    async function j(url, opts) {{
      const r = await fetch(url, opts);
      if (!r.ok) throw new Error(await r.text());
      return r.json();
    }}

    async function refresh() {{
      try {{
        const data = await j('/current');
        statusEl.textContent = JSON.stringify(data);
        if (typeof data.current_index === 'number') {{
          sel.value = String(data.current_index);
        }}
        rawIdx.href = '/raw/' + sel.value;
      }} catch (e) {{
        statusEl.textContent = 'unavailable';
      }}
    }}

    function bust() {{
      img.src = '/mjpeg?ts=' + Date.now();
      refresh();
    }}

    btn.addEventListener('click', async () => {{
      try {{
        const idx = Number(sel.value);
        await j('/switch', {{
          method: 'POST',
          headers: {{'Content-Type': 'application/json'}},
          body: JSON.stringify({{ index: idx }})
        }});
        bust();
      }} catch (e) {{
        alert('Switch failed: ' + e.message);
      }}
    }});

    sel.addEventListener('change', () => {{
      rawIdx.href = '/raw/' + sel.value;
    }});

    refresh();
  </script>
</body>
</html>
"""

# =========================
# RAW HTML (no chrome)
# =========================
RAW_HTML_CURRENT = """<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Raw</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    html, body { margin:0; height:100%; background:#000; display:grid; place-items:center; }
    img { width:100vw; height:100vh; object-fit:contain; background:#000; }
  </style>
</head>
<body>
  <img src="/mjpeg" alt="Live stream" />
</body>
</html>
"""

RAW_HTML_INDEX = """<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Raw Index</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    html, body { margin:0; height:100%; background:#000; display:grid; place-items:center; }
    img { width:100vw; height:100vh; object-fit:contain; background:#000; }
  </style>
</head>
<body>
  <img src="/mjpeg/{index}" alt="Live stream" />
</body>
</html>
"""

# =========================
# HTTP Handlers
# =========================
async def index(_request):
    return web.Response(text=HTML, content_type="text/html")

async def raw_current(_request):
    return web.Response(text=RAW_HTML_CURRENT, content_type="text/html")

async def raw_by_index(request):
    try:
        idx = int(request.match_info["index"])
    except Exception:
        return web.Response(status=400, text="Bad index")
    page = RAW_HTML_INDEX.replace("{index}", str(idx))
    return web.Response(text=page, content_type="text/html")

async def current_info(_request):
    with camera_lock:
        return web.json_response({
            "current_index": current_index,
            "open": camera is not None,
            "width": VIDEO_WIDTH,
            "height": VIDEO_HEIGHT,
            "fps": VIDEO_FPS,
            "last_error": last_error,
        })

async def switch_handler(request):
    data = await request.json()
    idx = int(data.get("index"))
    start_camera(idx)
    if last_error:
        return web.Response(status=500, text=f"Failed to open index {idx}: {last_error}")
    return web.json_response({"ok": True, "index": current_index})

async def snapshot_current(_request):
    with camera_lock:
        cam = camera
    if cam is None:
        return web.Response(status=503, text="No camera open")
    frame = cam.read_latest(timeout=1.0)
    if frame is None:
        return web.Response(status=503, text="No frame")
    ok, buf = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
    if not ok:
        return web.Response(status=500, text="Encode error")
    return web.Response(body=buf.tobytes(), content_type="image/jpeg")

async def snapshot_by_index(request):
    try:
        idx = int(request.match_info["index"])
    except Exception:
        return web.Response(status=400, text="Bad index")
    try:
        src = get_or_start_raw(idx)  # will reuse current if same index
    except Exception as e:
        return web.Response(status=500, text=f"Failed to start index {idx}: {e}")
    frame = src.read_latest(timeout=1.0)
    if frame is None:
        return web.Response(status=503, text="No frame")
    ok, buf = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
    if not ok:
        return web.Response(status=500, text="Encode error")
    return web.Response(body=buf.tobytes(), content_type="image/jpeg")

async def mjpeg_current(request):
    return await _mjpeg_stream_from_source(request, lambda: camera, use_lock=True)

async def mjpeg_by_index(request):
    try:
        idx = int(request.match_info["index"])
    except Exception:
        return web.Response(status=400, text="Bad index")
    try:
        src = get_or_start_raw(idx)  # ensure started or reuse current
    except Exception as e:
        return web.Response(status=500, text=f"Failed to start index {idx}: {e}")
    # capture object is stable for this request; no lock needed per iteration
    return await _mjpeg_stream_from_source(request, lambda: src, use_lock=False)

async def _mjpeg_stream_from_source(request, get_src, use_lock: bool):
    boundary = "frame"
    resp = web.StreamResponse(
        status=200,
        headers={
            "Content-Type": f"multipart/x-mixed-replace; boundary={boundary}",
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
        },
    )
    await resp.prepare(request)

    try:
        frame_interval = 1.0 / max(1, VIDEO_FPS)
        while True:
            if use_lock:
                with camera_lock:
                    src = get_src()
            else:
                src = get_src()
            if src is None or not src.running:
                await asyncio.sleep(0.1)
                continue
            frame = src.read_latest(timeout=1.0)
            if frame is None:
                await asyncio.sleep(0.01)
                continue
            ok, buf = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
            if not ok:
                continue
            part = (
                f"--{boundary}\r\n"
                "Content-Type: image/jpeg\r\n"
                f"Content-Length: {len(buf)}\r\n\r\n"
            ).encode("ascii") + buf.tobytes() + b"\r\n"
            await resp.write(part)
            await asyncio.sleep(frame_interval * 0.5)
    except (ConnectionResetError, asyncio.CancelledError, BrokenPipeError):
        pass
    finally:
        try:
            await resp.write_eof()
        except Exception:
            pass
    return resp

# =========================
# App lifecycle
# =========================
async def on_startup(app):
    # Start EXACTLY as your original: open DEVICE_INDEX right away
    start_camera(DEVICE_INDEX)
    # Launch idle reaper task for per-index sources
    app["reaper"] = asyncio.create_task(reap_idle_sources())
    print(f"Serving on http://{HOST}:{PORT}  (Ctrl+C to stop)")

async def on_shutdown(app):
    # Stop reaper
    try:
        app["reaper"].cancel()
    except Exception:
        pass
    with camera_lock:
        if camera is not None:
            try:
                camera.stop()
            except Exception:
                pass
    with raw_lock:
        for src in list(raw_sources.values()):
            try:
                src.stop()
            except Exception:
                pass
        raw_sources.clear()

def main():
    app = web.Application()
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    app.add_routes([
        # Main UI and "current" raw
        web.get("/", index),
        web.get("/raw", raw_current),
        web.get("/mjpeg", mjpeg_current),
        web.get("/snapshot.jpg", snapshot_current),

        # Per-index raw endpoints (do not change the "current" camera)
        web.get(r"/raw/{index:\d+}", raw_by_index),
        web.get(r"/mjpeg/{index:\d+}", mjpeg_by_index),
        web.get(r"/snapshot/{index:\d+}.jpg", snapshot_by_index),

        # Status + switching for main UI
        web.get("/current", current_info),
        web.post("/switch", switch_handler),
    ])
    web.run_app(app, host=HOST, port=PORT, access_log=None)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
