
from flask import Flask, Response
import threading
import time
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

print("System Started (Web Mode). Running Pygame in MAIN thread.")


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

    while True:
        # Sensor data
        data = sensors.update()

        element = data.get("element")
        gesture = data.get("gesture")
        cam_frame = data.get("frame")
        profile = data.get("profile")
        proximity = data.get("proximity")

        # Update animation engine
        engine.update(
            profile=profile,
            element=element,
            gesture=gesture,
            proximity=proximity,
            frame=cam_frame
        )

        # Handle 'R' key reset (triggered inside AnimationEngine)
        if getattr(engine, "request_reset", False):
            print("[Main] 'R' pressed to reset profile.")
            sensors.reset_profile()
            engine.reset_profile()
            engine.request_reset = False

        # Convert pygame surface → numpy RGB → BGR
        surf = engine.get_frame_surface()
        if surf is not None:
            try:
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
