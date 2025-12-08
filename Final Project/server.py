from flask import Flask, Response
import threading
import time
import numpy as np
import cv2
import pygame  # needed for keyboard input (R to reset)

from animation.animation_engine import AnimationEngine
from sensors.sensor_manager import SensorManager

# ---------------------------------------------------------
# INITIALIZE GLOBAL OBJECTS
# ---------------------------------------------------------
app = Flask(__name__)

engine = AnimationEngine()
sensors = SensorManager()

latest_frame = None
frame_lock = threading.Lock()

print("System Started (Web Mode). Running Pygame in MAIN thread.")

# ---------------------------------------------------------
# SIMPLE HTML PAGE (WEB VIEW)
# ---------------------------------------------------------

INDEX_HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Inner Constellation</title>
<style>
    html, body {
        margin: 0;
        padding: 0;
        width: 100%;
        height: 100%;
        background: black;
        overflow: hidden;
        font-family: "Arial", sans-serif;
    }
    #view {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        object-fit: cover;
        object-position: center;
        z-index: 1;
        display: block;
    }
    #hud {
        position: fixed;
        top: 40px;
        right: 40px;
        z-index: 2;
        text-align: right;
        color: white;
        font-family: "Segoe UI", "Helvetica Neue", sans-serif;
        text-shadow: 0 0 6px rgba(0,0,0,0.8);
    }
    #hud h1 {
        margin: 0;
        font-size: 36px;
        font-weight: 600;
        line-height: 1.2;
    }
    #hud h2 {
        margin: 8px 0 0;
        font-size: 22px;
        font-weight: 400;
    }
    #toggleBtn {
        position: fixed;
        top: 20px;
        left: 20px;
        z-index: 3;
        padding: 8px 14px;
        font-size: 14px;
        border-radius: 18px;
        border: none;
        cursor: pointer;
        background: rgba(0,0,0,0.5);
        color: #fff;
    }
</style>
</head>
<body>

<img id="view" src="/frame">

<div id="hud">
    <h1>Inner Constellation</h1>
    <h2>Energy Field Active</h2>
</div>

<button id="toggleBtn">Hide HUD</button>

<script>
    // Periodically refresh MJPEG image
    setInterval(() => {
        const img = document.getElementById("view");
        img.src = "/frame?" + new Date().getTime();
    }, 60);

    // Toggle HUD visibility
    const hud = document.getElementById("hud");
    const btn = document.getElementById("toggleBtn");
    let hudVisible = true;

    btn.addEventListener("click", () => {
        hudVisible = !hudVisible;
        hud.style.display = hudVisible ? "block" : "none";
        btn.textContent = hudVisible ? "Hide HUD" : "Show HUD";
    });
</script>

</body>
</html>
"""


@app.route("/")
def index():
    """Return simple web page streaming the energy field."""
    return INDEX_HTML


# ---------------------------------------------------------
# MJPEG STREAM ENDPOINT
# ---------------------------------------------------------
@app.route("/frame")
def frame_feed():
    """Stream MJPEG frames from pygame render output."""

    def generate():
        global latest_frame
        while True:
            with frame_lock:
                frame = latest_frame.copy() if latest_frame is not None else None

            if frame is None:
                time.sleep(0.03)
                continue

            # Encode JPEG
            ret, jpeg = cv2.imencode(".jpg", frame)
            if not ret:
                continue

            # Multipart MJPEG frame
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" +
                jpeg.tobytes() +
                b"\r\n"
            )

            time.sleep(0.02)  # ~50 FPS max

    return Response(generate(),
                    mimetype="multipart/x-mixed-replace; boundary=frame")


# ---------------------------------------------------------
# FLASK THREAD
# ---------------------------------------------------------
def start_flask():
    """Run Flask server in background."""
    app.run(
        host="0.0.0.0",
        port=8080,
        debug=False,
        threaded=True,
        use_reloader=False
    )


# ---------------------------------------------------------
# MAIN PYGAME LOOP (runs in main thread)
# ---------------------------------------------------------
def pygame_loop():
    global latest_frame

    print("Press 'R' in the Pygame window to reset element selection.")
    print("Close the Pygame window or press ESC to quit (if you handle it in engine).")

    while True:
        # 1) Read sensor data
        data = sensors.update()

        element = data.get("element")
        gesture = data.get("gesture")
        cam_frame = data.get("frame")
        profile = data.get("profile")
        proximity = data.get("proximity")

        # 2) Update animation engine
        engine.update(
            profile=profile,
            element=element,
            gesture=gesture,
            proximity=proximity,
            frame=cam_frame,
        )

        # 3) Handle keyboard shortcut 'R' to reset profile
        keys = pygame.key.get_pressed()
        if keys[pygame.K_r]:
            print("[Main] 'R' pressed to reset profile.")
            sensors.reset_profile()
            engine.reset_profile()
            # Small delay so holding 'R' does not trigger multiple resets at once
            time.sleep(0.25)

        # 4) Grab frame from pygame and convert to BGR for MJPEG
        surf = engine.get_frame_surface()
        if surf is not None:
            try:
                frame_rgb = np.transpose(surf, (1, 0, 2))  # (width,height,3) → (h,w,3)
                frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)

                with frame_lock:
                    latest_frame = frame_bgr
            except Exception as e:
                print("[Server] Frame conversion error:", e)

        time.sleep(0.01)


# ---------------------------------------------------------
# ENTRY POINT
# ---------------------------------------------------------
if __name__ == "__main__":
    # Start Flask in background thread
    flask_thread = threading.Thread(target=start_flask, daemon=True)
    flask_thread.start()

    # Run Pygame loop in main thread
    pygame_loop()
