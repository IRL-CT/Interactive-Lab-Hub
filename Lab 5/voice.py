"""
The speaker, the way Lab 4 does it: Piper in Python, played with sounddevice.
Used by start_night.py (the hand-off) and morning.py (the report).
"""
import pathlib

VOICE_MODEL = pathlib.Path(__file__).resolve().parent.parent / "Lab 3" / "voices" / "en_US-lessac-medium.onnx"
SPEAKER_GAIN = 1.2     # same as Lab 4


def speak(text, voice_model=VOICE_MODEL):
    """Say `text` through the speaker. Returns False (and the screen still shows it) if something
    is missing, so the device never breaks over a silent speaker; the reason is printed."""
    try:
        import numpy as np
        import sounddevice as sd
        from piper import PiperVoice
        voice = PiperVoice.load(str(voice_model))
        for chunk in voice.synthesize(text):
            samples = np.frombuffer(chunk.audio_int16_bytes, dtype=np.int16)
            louder = np.clip(samples.astype(np.float32) * SPEAKER_GAIN, -32768, 32767).astype(np.int16)
            sd.play(louder, samplerate=chunk.sample_rate)
            sd.wait()
        return True
    except Exception as e:                              # missing package, voice file or sound device
        print(f"could not speak: {e!r}", flush=True)
        return False
