import queue
import sys
import time
import sounddevice as sd
import numpy as np
import json
from vosk import Model, KaldiRecognizer


def record_and_recognize(
    model_lang="en-us",
    device=None,
    samplerate=None,
    filename=None,
    blocksize=8000,
    silence_threshold=500,   # Adjust depending on mic sensitivity
    silence_duration=1.5,    # seconds of silence before auto-stop
    max_duration=5.0         # hard limit (optional)
):
    """
    Record user's speech and stop automatically after a few seconds of silence.
    Returns a list of recognized phrases (strings).
    """

    q = queue.Queue()

    def callback(indata, frames, time_info, status):
        if status:
            print(status, file=sys.stderr)
        q.put(bytes(indata))

    # Initialize device and sample rate
    if samplerate is None:
        device_info = sd.query_devices(device, "input")
        samplerate = int(device_info["default_samplerate"])

    # Load Vosk model
    model = Model(lang=model_lang)
    rec = KaldiRecognizer(model, samplerate)

    # Optional file to dump raw audio
    dump_fn = open(filename, "wb") if filename else None

    results = []
    silence_start = None
    start_time = time.time()

    print("#" * 80)
    print("🎙️  Listening... Speak now.")
    print("Auto-stops after a pause.")
    print("#" * 80)

    try:
        with sd.RawInputStream(
            samplerate=samplerate,
            blocksize=blocksize,
            device=device,
            dtype="int16",
            channels=1,
            callback=callback,
        ):
            rec = KaldiRecognizer(model, samplerate)
            while True:
                data = q.get()
                if rec.AcceptWaveform(data):
                    print(rec.Result())
                else:
                    print(rec.PartialResult())
                if dump_fn is not None:
                    dump_fn.write(data)

                if time.time() - start_time > max_duration:
                    print("\n⏰ Max duration reached. Stopping.")
                    # assign to results and return as list of strings
                    last_result = json.loads(rec.FinalResult()).get("text", "").strip()
                    if last_result:
                        results.append(last_result)
                    break

    except KeyboardInterrupt:
        print("\n🛑 Stopped by user.")
    finally:
        if dump_fn:
            dump_fn.close()

    return results