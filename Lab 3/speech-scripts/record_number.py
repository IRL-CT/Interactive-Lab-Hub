import whisper
import sounddevice as sd
import numpy as np
import tempfile
import wavio
import os
import re

# 1. 用 TTS 提示用户
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
model = whisper.load_model("tiny.en")  # 小模型
result = model.transcribe(wav_path)
text = result.get("text", "")

# 5. 只保留数字
numbers_only = "".join(re.findall(r'\d+', text))

# 6. 输出并播报结果
if numbers_only:
    print("You said (numbers only):", numbers_only)
    os.system(f'espeak "You said {numbers_only}"')
else:
    print("No numbers detected.")
    os.system('espeak "No numbers detected"')

# 7. 删除临时文件
os.remove(wav_path)
