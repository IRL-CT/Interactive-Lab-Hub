
import time

start_time = time.perf_counter()

import whisper

model = whisper.load_model("tiny")
result = model.transcribe("lookdave.wav")

print(result["text"])

end_time = time.perf_counter()

elapsed_time = end_time - start_time
print(f"Program executed in {elapsed_time:.6f} seconds")
