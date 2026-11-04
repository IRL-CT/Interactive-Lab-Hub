import subprocess
import sys
from pathlib import Path

import numpy as np
import sherpa_onnx
import sounddevice as sd
from faster_whisper import WhisperModel


# --------------------------------------------------
# Configuration
# --------------------------------------------------

SAMPLE_RATE = 16000

# calendar-assistant/ -> Lab 3/
LAB3_DIR = Path(__file__).resolve().parent.parent

VAD_MODEL = LAB3_DIR / "models" / "silero_vad.onnx"
VOICES_DIR = LAB3_DIR / "voices"

WHISPER_MODEL = "base.en"

MIN_SILENCE = 1.0
MIN_SPEECH = 0.25

PIPER_MODEL = "en_US-lessac-medium"


# --------------------------------------------------
# Load Whisper once
# --------------------------------------------------

print("Loading speech recognition model...")

recognizer = WhisperModel(
    WHISPER_MODEL,
    device="cpu",
    compute_type="int8"
)


# --------------------------------------------------
# Voice Activity Detector
# --------------------------------------------------

def build_vad():
    config = sherpa_onnx.VadModelConfig()

    config.silero_vad.model = str(VAD_MODEL)
    config.silero_vad.min_silence_duration = MIN_SILENCE
    config.silero_vad.min_speech_duration = MIN_SPEECH
    config.sample_rate = SAMPLE_RATE

    detector = sherpa_onnx.VoiceActivityDetector(
        config,
        buffer_size_in_seconds=30
    )

    return detector, config.silero_vad.window_size


# --------------------------------------------------
# Listen for ONE utterance and return the transcript
# --------------------------------------------------

def listen(on_listening=None, on_processing=None):
    """Listen once, optionally reporting microphone and transcription states."""
    if not VAD_MODEL.is_file():
        raise FileNotFoundError(
            f"VAD model not found at {VAD_MODEL}"
        )

    vad, window = build_vad()

    buffer = np.empty(0, dtype=np.float32)

    # Read microphone in 100 ms chunks
    samples_per_read = int(0.1 * SAMPLE_RATE)

    print("Listening...")

    with sd.InputStream(
        channels=1,
        dtype="float32",
        samplerate=SAMPLE_RATE
    ) as stream:

        if on_listening is not None:
            on_listening()

        while True:
            chunk, _ = stream.read(samples_per_read)

            buffer = np.concatenate([
                buffer,
                chunk.reshape(-1)
            ])

            while len(buffer) >= window:
                vad.accept_waveform(buffer[:window])
                buffer = buffer[window:]

            # VAD found a complete utterance
            if not vad.empty():
                utterance = np.array(
                    vad.front.samples,
                    dtype=np.float32
                )

                vad.pop()
                break

    # Close the microphone before transcription and the assistant's reply.
    if on_processing is not None:
        on_processing()

    segments, _ = recognizer.transcribe(
        utterance,
        beam_size=1
    )

    return " ".join(
        segment.text.strip()
        for segment in segments
    ).strip()


# --------------------------------------------------
# Speak text using Piper
# --------------------------------------------------

def speak(text):
    if not text:
        return

    piper_command = [
        sys.executable,
        "-m",
        "piper",
        "--model",
        PIPER_MODEL,
        "--data-dir",
        str(VOICES_DIR),
        "--output-raw",
        "--",
        text,
    ]

    aplay_command = [
        "aplay",
        "-r",
        "22050",
        "-f",
        "S16_LE",
        "-t",
        "raw",
        "-"
    ]

    piper = subprocess.Popen(
        piper_command,
        stdout=subprocess.PIPE
    )

    aplay = subprocess.Popen(
        aplay_command,
        stdin=piper.stdout
    )

    if piper.stdout:
        piper.stdout.close()

    aplay.wait()
    piper.wait()
