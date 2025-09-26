import whisper
import sounddevice as sd
import numpy as np
import tempfile
import wavio
import os

# 1. 让 Pi 用 TTS 提问
os.system('espeak "Please say a number now"')

# 2. 录音设置
duration = 5  # 秒
samplerate = 16000

print("Recording... Speak now!")
recording = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype='int16')
sd.wait()
print("Recording finished!")

# 3. 临时保存 WAV 文件
with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
    wavio.write(f.name, recording, samplerate, sampwidth=2)
    wav_path = f.name

# 4. 使用 Whisper 转文字
model = whisper.load_model("tiny.en")  # tiny.en 模型轻量且速度快
result = model.transcribe(wav_path)
text = result.get("text", "")

# 5. 输出结果
print("你说的是：", text)
os.system(f'espeak "You said: {text}"')

# 6. 删除临时文件
os.remove(wav_path)
