# DeepSpeech
# ! We did not get this running for pi4 with 64Bit raspbian
# If YOU find a replicable method for getting DeepSpeech running please submit a PR

This uses [Mozilla DeepSpeech](https://github.com/mozilla/DeepSpeech) and works shockingly well even on the Pi. 

## Setup
Undering the virtual environment you created for this exercise, `cd` to the `dspeech` folder under Lab 3 and run the following command lines:

```
(dspeechexercise) pi@ixe00:~/Interactive-Lab-Hub/Lab 3/dspeech $ sudo apt-get install libatlas3-base
(dspeechexercise) pi@ixe00:~/Interactive-Lab-Hub/Lab 3/dspeech $ pip install -r requirements.txt
(dspeechexercise) pi@ixe00:~/Interactive-Lab-Hub/Lab 3/dspeech $ sh downloader.sh
```

## Running

```
(dspeechexercise) pi@ixe00:~/Interactive-Lab-Hub/Lab 3/dspeech $ python deepspeech_demo.py -m deepspeech-0.9.3-models.tflite -s deepspeech-0.9.3-models.scorer
```

The script should update and show what you are saying. Depneding on the level of background noise in your environment, you may want to change the VAD (Voice Activity Detection) parameter down given the quality of our microphones. VAD is set as an integer between 0 and 3, 0 being the least aggressive about filtering out non-speech, 3 the most aggressive. In the script, we have the VAD default = 3. Set aggressiveness of VAD by adding -v setting in the command line: 

```
(dspeechexercise) pi@ixe00:~/Interactive-Lab-Hub/Lab 3/dspeech $ python deepspeech_demo.py -m deepspeech-0.9.3-models.tflite -s deepspeech-0.9.3-models.scorer -v 2
```
