import time
import pygame

from sensors.sensor_manager import SensorManager
from animation.animation_engine import AnimationEngine


def main():
    pygame.init()

    sensors = SensorManager()
    engine = AnimationEngine()

    print("System Started. Waiting for interactions...")
    print("Press 'R' on the keyboard to re-select elements.")
    print("Press 'ESC' or close the window to quit.")

    running = True
    while running:
        # ----------------------------
        # Handle global events
        # ----------------------------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    # ESC to quit
                    running = False

                elif event.key == pygame.K_r:
                    # R → reset profile selection
                    print("[Main] 'R' pressed → reset profile.")
                    sensors.reset_profile()
                    engine.reset_profile()

        # ----------------------------
        # Read sensors
        # ----------------------------
        data = sensors.update()

        profile = data["profile"]   # list or None
        element = data["element"]   # string
        gesture = data["gesture"]   # string or None
        frame = data["frame"]       # camera frame or None

        # ----------------------------
        # Update animation
        # ----------------------------
        engine.update(
            profile=profile,
            element=element,
            gesture=gesture,
            proximity=None,  # if you later add proximity, pass it here
            frame=frame,
        )

        # Small sleep to avoid burning CPU
        time.sleep(0.01)

    # Cleanup on exit
    try:
        if sensors.camera:
            sensors.camera.release()
    except Exception:
        pass

    pygame.quit()


if __name__ == "__main__":
    main()
