import io
import os
import time
from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from PIL import Image

app = FastAPI(title="SDXL-Turbo Viewer", version="1.0")

VIDEOS_DIR = "videos"
BOUNDARY = "frameboundary0123456789"


def list_pngs(folder: str) -> List[str]:
    try:
        return sorted(
            [os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith(".png")],
            key=lambda p: os.path.getmtime(p),
        )
    except FileNotFoundError:
        return []


@app.get("/", response_class=HTMLResponse)
def index():
    return """<!doctype html>
<html>
  <head><meta charset="utf-8"><title>SDXL-Turbo Viewer</title></head>
  <body style="font-family: sans-serif;">
    <h2>SDXL-Turbo Viewer</h2>
    <p>Start a video session via the generation server, then open:</p>
    <pre>http://localhost:7986/view/&lt;uid&gt;</pre>
    <p>Example:</p>
    <pre>http://localhost:7986/view/abc123def456</pre>
  </body>
</html>"""


@app.get("/view/{uid}", response_class=HTMLResponse)
def view(uid: str):
    return f"""<!doctype html>
<html>
  <head><meta charset="utf-8"><title>Viewing {uid}</title></head>
  <body style="margin:0;background:#111;color:#eee;font-family:sans-serif;">
    <div style="padding:10px;position:fixed;top:0;left:0;right:0;background:#222;z-index:2;">
      <b>Viewing UID:</b> {uid} &nbsp; | &nbsp;
      <a style="color:#9cf" href="/mjpeg/{uid}">Raw MJPEG stream</a>
    </div>
    <div style="display:flex;align-items:center;justify-content:center;height:100vh;">
      <img id="stream" src="/mjpeg/{uid}" style="max-width:98vw;max-height:92vh;border:1px solid #333;">
    </div>
  </body>
</html>"""


@app.get("/mjpeg/{uid}")
def mjpeg(uid: str):
    folder = os.path.join(VIDEOS_DIR, uid)
    if not os.path.isdir(folder):
        raise HTTPException(status_code=404, detail=f"Folder not found: {folder}")

    def gen():
        last_path = None
        while True:
            images = list_pngs(folder)
            if images:
                latest = images[-1]
                if latest != last_path:
                    # Load latest PNG, convert to JPEG (MJPEG expects JPEG frames)
                    try:
                        with Image.open(latest) as im:
                            rgb = im.convert("RGB")
                            buf = io.BytesIO()
                            rgb.save(buf, format="JPEG", quality=85)
                            frame = buf.getvalue()
                    except Exception:
                        frame = None

                    if frame:
                        yield (b"--" + BOUNDARY.encode() + b"\r\n"
                               b"Content-Type: image/jpeg\r\n"
                               b"Cache-Control: no-cache\r\n"
                               b"Pragma: no-cache\r\n"
                               b"\r\n" + frame + b"\r\n")
                        last_path = latest

            # light polling; adjust as you like
            time.sleep(0.1)

    return StreamingResponse(
        gen(),
        media_type=f"multipart/x-mixed-replace; boundary={BOUNDARY}",
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7986, reload=False, workers=1)
