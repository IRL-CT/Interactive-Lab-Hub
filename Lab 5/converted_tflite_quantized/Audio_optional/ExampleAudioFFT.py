import pyaudio
import numpy as np
from scipy.fft import rfft, rfftfreq
from scipy.signal.windows import hann
from numpy_ringbuffer import RingBuffer

import queue
import time


## Please change the following number so that it matches to the microphone that you are using. 
DEVICE_INDEX = 1

## Compute the audio statistics every `UPDATE_INTERVAL` seconds.
UPDATE_INTERVAL = 1.0



### Things you probably don't need to change
FORMAT=np.float32
SAMPLING_RATE = 44100
CHANNELS=1


def main():
    ### Setting up all required software elements: 
    audioQueue = queue.Queue() #In this queue stores the incoming audio data before processing.
    pyaudio_instance = pyaudio.PyAudio() #This is the AudioDriver that connects to the microphone for us.

    def _callback(in_data, frame_count, time_info, status): # This "callbackfunction" stores the incoming audio data in the `audioQueue`
        audioQueue.put(in_data)
        return None, pyaudio.paContinue

    stream = pyaudio_instance.open(input=True,start=False,format=pyaudio.paFloat32,channels=CHANNELS,rate=SAMPLING_RATE,frames_per_buffer=int(SAMPLING_RATE/2),stream_callback=_callback,input_device_index=DEVICE_INDEX)
    
    
    # One essential way to keep track of variables overtime is with a ringbuffer. 
    # As an example the `AudioBuffer` it stores always the last second of audio data. 
    AudioBuffer = RingBuffer(capacity=SAMPLING_RATE*1, dtype=FORMAT) # 1 second long buffer.
    
    # Another example is the `VolumeHistory` ringbuffer. 
    VolumeHistory = RingBuffer(capacity=int(20/UPDATE_INTERVAL), dtype=FORMAT) ## This is how you can compute a history to record changes over time
    ### Here  is a good spot to extend other buffers  aswell that keeps track of varailbes over a certain period of time. 

    nextTimeStamp = time.time()
    stream.start_stream()
    if True:
        while True:
            frames = audioQueue.get() #Get DataFrom the audioDriver (see _callbackfunction how the data arrives)
            if not frames:
                continue

            framesData = np.frombuffer(frames, dtype=FORMAT) 
            AudioBuffer.extend(framesData[0::CHANNELS]) #Pick one audio channel and fill the ringbuffer. 
            
            if(AudioBuffer.is_full and  # Waiting for the ringbuffer to be full at the beginning.
                audioQueue.qsize()<2 and # Make sure there is not alot more new data that should be used. 
                time.time()>nextTimeStamp): # See `UPDATE_INTERVAL` above.

                buffer  = np.array(AudioBuffer) #Get the last second of audio. 


                volume = np.rint(np.sqrt(np.mean(buffer**2))*10000) # Compute the rms volume
                
                
                VolumeHistory.append(volume)
                volumneSlow = volume
                volumechange = 0.0
                if VolumeHistory.is_full:
                    HalfLength = int(np.round(VolumeHistory.maxlen/2)) 
                    vnew = np.array(VolumeHistory)[HalfLength:].mean()
                    vold = np.array(VolumeHistory)[:VolumeHistory.maxlen-HalfLength].mean()
                    volumechange =vnew-vold
                    volumneSlow = np.array(VolumeHistory).mean()
                
                ## Computes the Frequency Foruier analysis on the Audio Signal.
                N = buffer.shape[0] 
                window = hann(N) 
                amplitudes = np.abs(rfft(buffer*window))[25:] #Contains the volume for the different frequency bin.
                frequencies = (rfftfreq(N, 1/SAMPLING_RATE)[:N//2])[25:] #Contains the Hz frequency values. for the different frequency bin.
                '''
                Combining  the `amplitudes` and `frequencies` varialbes allows you to understand how loud a certain frequency is.

                e.g. If you'd like to know the volume for 500Hz you could do the following. 
                1. Find the frequency bin in which 500Hz belis closest to with:
                FrequencyBin = np.abs(frequencies - 500).argmin()
                
                2. Look up the volume in that bin:
                amplitudes[FrequencyBin]


                The example below does something similar, just in revers.
                It finds the loudest amplitued and its coresponding bin  with `argmax()`. 
                The uses the index to look up the Freqeucny value.
                '''


                LoudestFrequency = frequencies[amplitudes.argmax()]
                
                print("Loudest Frqeuncy:",LoudestFrequency)
                print("RMS volume:",volumneSlow)
                print("Volume Change:",volumechange)
                
                nextTimeStamp = UPDATE_INTERVAL+time.time() # See `UPDATE_INTERVAL` above


if __name__ == '__main__':
    main()
    print("Something happend with the audio example. Stopping!") 


