import pyaudio

audio = pyaudio.PyAudio()

for ii in range(audio.get_device_count()):
    print(ii, audio.get_device_info_by_index(ii).get('name'))
