Create a new virtualenvironment
``````
python -m venv .venv 
source .venv/bin/activate
``````

Install dependencies in it
``````
(.venv) pip install -r requirements.txt
``````

### Mediapipe
For the media pipe example 

Run outside the .venv environment with ```sudo``

``````
(.venv) deactivate
sudo apt update
sudo apt install -y libasound2-dev build-essential python3-dev
Make the loop_audio shell script executable
``````
source back to your .venv

``````
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
pip install pyalsaaudio
``````
Make the loop_audio shell script executable 
```
sudo chmod +x ./loop_audio.sh
```
