from flask import Flask, Response, request
import threading
import time
import numpy as np
import cv2
import pygame  # for event/keyboard handling if needed

from animation.animation_engine import AnimationEngine
from sensors.sensor_manager import SensorManager

# ---------------------------------------------------------
# GLOBAL OBJECTS
# ---------------------------------------------------------
app = Flask(__name__)

engine = AnimationEngine()
sensors = SensorManager()

latest_frame = None
frame_lock = threading.Lock()

# Flag set by /reset endpoint
reset_requested = False

print("System Started (Web Mode). Pygame runs in MAIN thread.")

# ---------------------------------------------------------
# HTML PAGE
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
    #controls {
        position: fixed;
        bottom: 28px;
        left: 28px;
        z-index: 3;
        display: flex;
        gap: 12px;
    }
    .ctrl-btn {
        padding: 8px 14px;
        font-size: 14px;
        border-radius: 18px;
        border: none;
        cursor: pointer;
        background: rgba(0,0,0,0.55);
        color: #fff;
        font-family: "Segoe UI", "Helvetica Neue", sans-serif;
    }
    .ctrl-btn:hover {
        background: rgba(0,0,0,0.8);
    }
</style>
</head>
<body>

<img id="view" src="/frame">

<div id="hud">
    <h1>Inner Constellation</h1>
    <h2>Energy Field Active</h2>
</div>

<div id="controls">
    <button id="resetBtn" class="ctrl-btn">Re-select Elements</button>
    <button id="toggleHudBtn" class="ctrl-btn">Hide HUD</button>
</div>

<script>
    // Periodically refresh MJPEG image
    setInterval(() => {
        const img = document.getElementById("view");
        img.src = "/frame?" + new Date().getTime();
    }, 60);

    // Re-select Elements: call /reset endpoint
    const resetBtn = document.getElementById("resetBtn");
    resetBtn.addEventListener("click", () => {
        fetch("/reset", { method: "POST" })
            .then(res => res.text())
            .then(txt => {
                console.log("Reset response:", txt);
            })
            .catch(err => console.error("Reset error:", err));
    });

    // Toggle HUD visibility
    const hud = document.getElementById("hud");
    const toggleHudBtn = document.getElementById("toggleHudBtn");
    let hudVisible = true;

    toggleHudBtn.addEventListener("click", () => {
        hudVisible = !hudVisible;
        hud.style.display = hudVisible ? "block" : "none";
        toggleHudBtn.textContent = hudVisible ? "Hide HUD" : "Show HUD";
    });
</script>

</body>
</html>
"""


@app.route("/")
def index():
    """Return main web page."""
    return INDEX_HTML


# ---------------------------------------------------------
# RESET ENDPOINT (WEB BUTTON → RESET PROFILE)
# ---------------------------------------------------------
@app.route("/reset", methods=["POST"])
def reset_profile():
    """
    Web endpoint called when user clicks "Re-select Elements".
    It only sets a flag; actual reset is done in the pygame loop
    to keep all sensor and engine logic in the main thread.
    """
    global reset_requested
    reset_requested = True
    return "OK"


# ---------------------------------------------------------
# MJPEG STREAM ENDPOINT
# ---------------------------------------------------------
@app.route("/frame")
def frame_feed():
    """Stream MJPEG frames from pygame output."""

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
    """Run Flask server in background thread."""
    app.run(
        host="0.0.0.0",
        port=8080,
        debug=False,
        threaded=True,
        use_reloader=False
    )


# ---------------------------------------------------------
# MAIN PYGAME LOOP
# ---------------------------------------------------------
def pygame_loop():
    """
    Main loop that:
    1. Reads sensor data
    2. Updates animation engine
    3. Handles reset flag from /reset
    4. Copies current pygame frame for MJPEG streaming
    """
    global latest_frame, reset_requested

    print("[Main] Web mode running. Use the web 'Re-select Elements' button to reset.")

    while True:
        # 1) Sensor data
        data = sensors.update()
        element = data.get("element")
        gesture = data.get("gesture")          # still passed but unused now
        cam_frame = data.get("frame")
        profile = data.get("profile")
        proximity = data.get("proximity")      # may be None if not provided

        # 2) Check if web requested reset
        if reset_requested:
            print("[Main] Web reset requested → clearing profile.")
            try:
                sensors.reset_profile()
            except Exception as e:
                print("[Main] sensors.reset_profile() error:", e)
            try:
                engine.reset_profile()
            except Exception as e:
                print("[Main] engine.reset_profile() error:", e)
            reset_requested = False

        # 3) Update animation engine
        engine.update(
            profile=profile,
            element=element,
            gesture=gesture,
            proximity=proximity,
            frame=cam_frame,
        )

        # 4) Grab frame from pygame and convert to BGR for MJPEG
        surf = engine.get_frame_surface()
        if surf is not None:
            try:
                # surf: (width, height, 3) → (height, width, 3)
                frame_rgb = np.transpose(surf, (1, 0, 2))
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
    # Start Flask in a background thread
    flask_thread = threading.Thread(target=start_flask, daemon=True)
    flask_thread.start()

    # Run Pygame loop in main thread
    pygame_loop()
