# How to run this code

## Hardware setup 

- Make sure to connec the LED Ring 
    - 5G to Pin 2
    - GN to Pin 6
    - DIN to GPIO18 (PIN 18) - 6th on the right row

- FOr the pressure sensor, left 4 


## How to run 
```bash
source .venv/bin/activate
python master.py
```


When you are not sure if capacitor is working. 
```bash
sudo i2cdetect -y 1
```