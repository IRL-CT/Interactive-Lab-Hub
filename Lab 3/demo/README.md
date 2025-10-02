# Magic Ball WoZ

This is a Demo App for a Wizard of Oz interactive system where the wizard is playing a magic 8 ball

<img src='https://images-na.ssl-images-amazon.com/images/I/71729uRDw2L._AC_SY606_.jpg' width=200>

## Hardware Set-Up

For this demo, you will need: 
* your Raspberry Pi, 
* a Qwiic/Stemma Cable, 
* the display (we are just using it for the Qwiic/StemmaQT port. Feel free to use the display in your projects), 
* your accelerometer (LSM6DS3 or MSA311), and 
`* your Bluetooth speaker (paired)

**Note**: Different class years may have different hardware:
- **Fall 2026+**: Bluetooth speakers (Pi 5 has no audio jack), LSM6DS3 accelerometer
- **Fall 2025**: USB webcam with microphone, LSM6DS3 accelerometer  
- **Earlier years**: USB webcam with microphone, MSA311 or MPU6050 accelerometer

The demo supports different sensors - see app.py for easy sensor swapping.

**Audio Setup:**
- **Speech output**: Works with Bluetooth speakers via PulseAudio
- **Eavesdropping**: Requires a separate USB microphone (Bluetooth speakers typically don't have mics)

<p float="left"><img src="https://cdn-learn.adafruit.com/assets/assets/000/082/842/large1024/adafruit_products_4393_iso_ORIG_2019_10.jpg" height="200" />
<img src="https://github.com/adafruit/Adafruit_MPU6050/raw/master/assets/board.jpg?raw=true" height="200" />

Plug the display in and connect the accelerometer to the port underneath with your Qwiic connector cable. Plug the web camera into the raspberry pi. 

## Software Setup

Ssh on to your Raspberry Pi as we've done previously

`ssh pi@yourHostname.local`

Ensure audio is playing through the aux connector by typing

`sudo raspi-config`

on `system options` hit enter. Go down to `s2 Audio` and hit enter. Select `1 USB Audio` and hit enter. Then navigate to `<Finish>` and exit the config menu.

We will need one additional piece of software called VLC Media player. To install it type `sudo apt-get install vlc` 


I would suggest making a new virtual environment for this demo then navigating to this folder and installing the requirements.

```
pi@yourHostname:~ $ virtualenv woz
pi@yourHostname:~ $ source woz/bin/activate
(woz) pi@yourHostname:~ $ cd Interactive-Lab-Hub/Lab\ 3/demo
(woz) pi@yourHostname:~/Interactive-Lab-Hub/Lab 3/demo $ 
(woz) pi@yourHostname:~/Interactive-Lab-Hub/Lab 3/demo $ pip install -r requirements.txt
```

## Running

To run the app

`(woz) pi@yourHostname:~/Interactive-Lab-Hub/Lab 3/demo $ python app.py`

In the browser of a computer on the same network, navigate to http://yourHostname.local:5000/ where in my case my hostname is ixe00

![](./imgs/page.png)

The interface will immediately begin streaming the accelerometer to let you know if your participant shakes their Magic 8 ball. The "eavesdrop" button will begin streaming audio from the Pi to your browser (note there is a noticeable delay it is best to start eavesdropping right at the beginning). To have the Pi speak, you can write in the text box and hit send or press enter.

## Notes

## Audio Setup Notes

**For eavesdropping feature to work, you need a microphone:**

1. **USB Camera with Microphone**: Plug in your USB camera - the app will automatically detect it
2. **No Microphone**: If no microphone is detected, you'll see a message in the terminal. The Magic 8 ball will still work, but eavesdropping won't be available.

The app automatically detects available microphones and configures audio streaming. You no longer need to manually configure hardware devices.

**Speech Output**: Works automatically with your paired Bluetooth speaker via PulseAudio.

