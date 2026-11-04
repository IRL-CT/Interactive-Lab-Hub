import subprocess

# Ask the question using Piper
subprocess.run([
    "python3", "-m", "piper",
    "--model", "en_US-lessac-medium",
    "--data-dir", "../voices",
    "--output-file", "question.wav",
    "--",
    "How old are you?"
])

# Play the question
subprocess.run(["aplay", "question.wav"])

# Record the answer for 5 seconds
subprocess.run([
    "arecord",
    "-d", "5",
    "-f", "cd",
    "-c", "1",
    "-r", "16000",
    "answer.wav"
])

print("Answer recorded to answer.wav")
