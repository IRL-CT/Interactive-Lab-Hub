import threading
import time
import os

from flask import Flask, Response, send_from_directory
import numpy as np
import cv2

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

# NEW: web reset flag
reset_flag = False

print("System Started (Web Mode). Running Pygame in MAIN thread.")

@app.route("/hide_labels", methods=["POST"])
def hide_labels():
    engine.show_labels = False
    print("[Server] Labels hidden.")
    return "OK"

@app.route("/show_labels", methods=["POST"])
def show_labels():
    engine.show_labels = True
    print("[Server] Labels shown.")
    return "OK"


# ---------------------------------------------------------
# HOME PAGE: serve index.html
# ---------------------------------------------------------
@app.route("/")
def index():
    """
    Serve the main Inner Constellation web page.
    index.html must be in the same folder as server.py.
    """
    base_dir = os.path.dirname(__file__)
    return send_from_directory(base_dir, "index.html")


# ---------------------------------------------------------
# WEB RESET ENDPOINT
# ---------------------------------------------------------
@app.route("/reset", methods=["POST"])
def reset_profile_web():
    """
    Web endpoint to request profile reset.
    Called from the browser (Reset button).
    """
    global reset_flag
    reset_flag = True
    print("[Server] Web reset requested via /reset")
    return "OK"


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

            # Yield a multipart frame
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" +
                jpeg.tobytes() +
                b"\r\n"
            )

            time.sleep(0.02)  # ~50 FPS max

    return Response(
        generate(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )


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
        use_reloader=False,
    )


# ---------------------------------------------------------
# MAIN PYGAME LOOP (runs in main thread)
# ---------------------------------------------------------
def pygame_loop():
    global latest_frame, reset_flag

    while True:
        # Sensor data
        data = sensors.update()

        element = data.get("element")
        gesture = data.get("gesture")
        cam_frame = data.get("frame")
        profile = data.get("profile")
        proximity = data.get("proximity")  # may be None

        # Update animation engine
        engine.update(
            profile=profile,
            element=element,
            gesture=gesture,
            proximity=proximity,
            frame=cam_frame,
        )

        # Handle reset from either:
        # - R key inside pygame window (if you ever run with a real display)
        # - Web /reset endpoint (reset_flag)
        if getattr(engine, "request_reset", False) or reset_flag:
            print("[Main] Reset requested (R key or web).")
            sensors.reset_profile()
            engine.reset_profile()
            engine.request_reset = False
            reset_flag = False

        # Convert pygame surface → numpy RGB → BGR
        surf = engine.get_frame_surface()
        if surf is not None:
            try:
                # surf shape: (width, height, 3) → transpose to (height, width, 3)
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
    # Start Flask in background thread
    flask_thread = threading.Thread(target=start_flask, daemon=True)
    flask_thread.start()

    # Run Pygame loop in main thread
    pygame_loop()
