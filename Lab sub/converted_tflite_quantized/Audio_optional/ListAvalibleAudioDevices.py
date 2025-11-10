import pyaudio

pyaudio_instance = pyaudio.PyAudio()

print("--- Starting audio device survey! ---")
for i in range(pyaudio_instance.get_device_count()):
    dev = pyaudio_instance.get_device_info_by_index(i)
    name = dev['name'].encode('utf-8')
    print(i, name, dev['maxInputChannels'], dev['maxOutputChannels'])

