# Readme file for how to run cry model

```bash 
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

sudo systemctl stop piscreen.service --now

python cry_analyzer_color.py

# to test if the cry analyzer is working or not
python cry_analyzer_model_only.py *"filename"*
```