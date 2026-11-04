#This code was created based on the files pi_servo_hat_test.py, qwiic_distance.py, utilizes Piper for speech, and structured with the ChatGPT.

import time
import random
from pathlib import Path

import numpy as np
import sounddevice as sd
import qwiic_proximity
import pi_servo_hat
from piper import PiperVoice

# ==================================================
# CONFIGURATION
# ==================================================
SERVO_CH = 0

REST_ANGLE = 0
FOOD_ANGLE = 50

ARRIVAL_THRESHOLD = 4
LEAVING_THRESHOLD = 2

# Require the reading to remain low this long
LEAVING_DELAY = 2.0

# Require a stable high reading before detecting a return
ARRIVAL_DELAY = 0.5

VOICE_PATH = Path(
    "/home/pi/Interactive-Lab-Hub/Lab 3/voices/en_US-lessac-medium.onnx"
)

# ==================================================
# PHRASES
# ==================================================
ENCOURAGING_PHRASES = [
    "Yes, good! Keep taking some more!",
    "That's it! Have some more!",
    "Don't be shy, take whatever you like!",
    "Very good! Eat well!",
    "Go on, go on! There's plenty!",
    "Take some more, don't be shy!",
    "Good, good! Enjoy your food!",
    "You must eat more!",
]

COMEBACK_PHRASES = [
    "Eh! Come back and take some more!",
    "Where are you going? There's more food!",
    "Come, come! You haven't eaten enough!",
    "Wait! Come and get some more!",
    "Don't leave yet! Take some food!",
    "Come back! I made this for you!",
]

# ==================================================
# RANDOM PHRASE PICKER
# Uses each phrase once before reshuffling
# ==================================================
class PhrasePicker:
    def __init__(self, phrases):
        self.phrases = list(phrases)
        self.remaining = []

    def next(self):
        if not self.remaining:
            self.remaining = self.phrases.copy()
            random.shuffle(self.remaining)

        return self.remaining.pop()


# ==================================================
# SPEAKER
# ==================================================
class Speaker:
    def __init__(self, voice_path):
        self.voice = PiperVoice.load(str(voice_path))

    def say(self, text):
        print("Auntie says:", text)

        for chunk in self.voice.synthesize(text):
            audio_data = np.frombuffer(
                chunk.audio_int16_bytes,
                dtype=np.int16
            ).astype(np.float32)

            # Increase volume
            audio_data = audio_data * 2.5

            # Prevent audio clipping and distortion
            audio_data = np.clip(
                audio_data, -32768, 32767
            ).astype(np.int16)

            sd.play(
                audio_data,
                samplerate=chunk.sample_rate
            )
            sd.wait()

# ==================================================
# WAVE TOWARD FOOD
# ==================================================
def wave_toward_food(servo):
    for _ in range(2):
        servo.move_servo_position(SERVO_CH, FOOD_ANGLE)
        time.sleep(0.3)
        servo.move_servo_position(SERVO_CH, REST_ANGLE)
        time.sleep(0.3)


# ==================================================
# MAIN PROGRAM
# ==================================================
def main():
    print("Loading Auntie...")

    if not VOICE_PATH.is_file():
        raise FileNotFoundError(
            f"Piper voice model not found: {VOICE_PATH}"
        )

    speaker = Speaker(VOICE_PATH)

    encouragement_picker = PhrasePicker(ENCOURAGING_PHRASES)
    comeback_picker = PhrasePicker(COMEBACK_PHRASES)

    # Initialize sensor once
    sensor = qwiic_proximity.QwiicProximity()

    if not sensor.connected:
        print("VCN4040 sensor not connected!")
        return

    sensor.begin()

    # Initialize servo once
    servo = pi_servo_hat.PiServoHat()
    servo.restart()
    servo.move_servo_position(SERVO_CH, REST_ANGLE)

    state = "AWAY"
    low_since = None
    high_since = None

    print("Auntie is ready!")

    try:
        while True:
            proximity = sensor.get_proximity()
            now = time.monotonic()

            print(f"Proximity: {proximity} | State: {state}")

            # ------------------------------------------
            # PERSON IS AWAY: WAIT FOR APPROACH
            # ------------------------------------------
            if state == "AWAY":
                if proximity >= ARRIVAL_THRESHOLD:
                    if high_since is None:
                        high_since = now

                    elif now - high_since >= ARRIVAL_DELAY:
                        print("Someone is close!")

                        # Wave and say a random encouragement
                        wave_toward_food(servo)
                        speaker.say(encouragement_picker.next())

                        state = "PRESENT"
                        low_since = None
                        high_since = None
                else:
                    high_since = None

            # ------------------------------------------
            # PERSON IS CLOSE: WAIT FOR DEPARTURE
            # ------------------------------------------
            elif state == "PRESENT":
                if proximity <= LEAVING_THRESHOLD:
                    if low_since is None:
                        low_since = now

                    elif now - low_since >= LEAVING_DELAY:
                        print("Someone is leaving!")

                        # Say a random invitation to return
                        speaker.say(comeback_picker.next())

                        state = "AWAY"
                        low_since = None
                        high_since = None
                else:
                    # Cancel departure detection if reading rises
                    low_since = None

            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\nAuntie is shutting down.")

    finally:
        servo.move_servo_position(SERVO_CH, REST_ANGLE)


if __name__ == "__main__":
    main()
