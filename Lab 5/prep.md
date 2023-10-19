### Pytorch
For the use of Pytorch, you can create a new virtualenvironment
``````
python -m venv venv-pyt 
source venv-pyt/bin/activate
``````

Install dependencies in it
``````
(venv-pyt) pip install torch===1.10.2 torchaudio===0.10.2 torchvision===0.11.3 opencv-python
(venv-pyt) pip install numpy --upgrade
``````

### Mediapipe
For the media pipe example create a new virtualenvironment
``````
python -m venv venv-mp 
source venv-mp/bin/activate
``````

Install dependencies in it

In case you did not do last labs optional parts run this command: ```sudo apt-get install libasound2-dev```

``````
(venv-mp) pip install mediapipe pyalsaaudio opencv-python
``````
Make the loop_audio shell script executable 

```
sudo chmod +x ./loop_audio.sh
```
### Teachable Machines
Create another virtual machine for the teachable machines example
``````
python -m venv venv-tml
source venv-tml/bin/activate
``````
Install dependencies in it
``````
(venv-tm) pip install teachable-machine-lite opencv-python
``````
