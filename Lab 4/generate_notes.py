import numpy as np
from pydub import AudioSegment
from pydub.playback import play

def make_bell(freq, duration_ms=1000, volume=-6.0):
    # Simple bell-ish envelope: fast attack, exponential decay + some overtones
    sample_rate = 44100
    t = np.linspace(0, duration_ms/1000, int(sample_rate * duration_ms/1000), False)
    # base sine
    wave = np.sin(2 * np.pi * freq * t)
    # add a harmonic overtone
    wave += 0.5 * np.sin(2 * np.pi * freq * 2 * t)
    # apply an exponential decay envelope
    envelope = np.exp(-3 * t)  # adjust decay rate
    wave = wave * envelope
    # normalize to int16
    audio = np.int16(wave / np.max(np.abs(wave)) * (2**15 - 1))
    segment = AudioSegment(
        audio.tobytes(),
        frame_rate=sample_rate,
        sample_width=2,
        channels=1
    )
    segment = segment + volume  # reduce gain
    return segment

# Example: notes frequencies (A4 = 440 Hz)
note_freq = {
    "A4": 440.0,
    "B4": 493.88,
    "C5": 523.25,
    "D5": 587.33,
    "E5": 659.25,
    "F5": 698.46,
    "G5": 783.99,
}

bells = {note: make_bell(freq, duration_ms=1000) for note, freq in note_freq.items()}

# To export to mp3/wav:
for note, bell in bells.items():
    bell.export(f"notes/bell_{note}.mp3", format="mp3")
    # bell.export(f"bell_{note}.wav", format="wav")
# bells["A4"].export("bell_A4.wav", format="wav")
