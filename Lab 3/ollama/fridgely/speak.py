
import speech_recognition as sr
import subprocess
clean_text = "hello"
subprocess.run(f'pico2wave -w temp.wav "{clean_text}" && aplay temp.wav', shell=True)
