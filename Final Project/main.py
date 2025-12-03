# main.py

from sensors.sensor_manager import SensorManager
from animation.animation_engine import AnimationEngine
import time


def main():
    sensors = SensorManager()
    engine = AnimationEngine()

    print("System Started. Waiting for interactions...")

    while True:
        data = sensors.update()

        profile = data["profile"]
        element = data["element"]
        gesture = data["gesture"]
        proximity = data["proximity"]
        frame = data["frame"]

        # Send to animation engine
        engine.update(
            profile=profile,
            element=element,
            gesture=gesture,
            proximity=proximity,
            frame=frame,
        )

        time.sleep(0.01)


if __name__ == "__main__":
    main()
