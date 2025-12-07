# main_musicbox.py
"""
Main entry point for LumiTune backend.

- Creates shared AudioEngine
- Starts MQTTController (mobile/web control)
- Starts SensorController (environment + gestures + servo)
"""

from audio_engine import AudioEngine
from mqtt_controller import MQTTController
from sensor_controller import SensorController


def main():
    # Shared audio engine
    engine = AudioEngine()

    # Start MQTT in background thread
    mqtt_ctrl = MQTTController(engine)
    mqtt_ctrl.start()

    # Start sensors (blocking loop)
    sensor_ctrl = SensorController(engine)
    sensor_ctrl.run_forever()


if __name__ == "__main__":
    main()
