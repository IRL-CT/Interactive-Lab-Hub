# Readme file for how to run cry model

```bash 
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

sudo systemctl stop piscreen.service --now

#check if the microphone is running 
arecord -l

python baby_monitor.py

# to test if the cry analyzer is working or not
python test/cry_analyzer_model_only.py *"filename"*
```
