
# Prep your Pi


### To prepare lab 3, you will need:

- Raspberry Pi 5
- USB Speaker
- USB Microphone


### Install Active Cooler (optional)

- Disconnect the Mini screen on pi just for now
- Unpack the preassembled Active Cooler from its box.
- Remove the backing paper from the thermal pads on the underside of the product.
- Make sure your Raspberry Pi 5 is powered off. Position the Active Cooler carefully in the correct space on Raspberry Pi 5, making sure not to hit any of the connectors. Please refer to the diagram on the front of the box which shows the correct position and orientation of the product.
- Align the two white push pins with the two dedicated heatsink holes.
- When correctly positioned, press evenly on the tops of the two push pins simultaneously until they click, indicating that they are clipped onto the board.
- Once the Active Cooler is mounted, connect its fan cable to the connector labelled‘FAN’ on Raspberry Pi 5. Take care to ensure the cable’s connector is the correct way round when inserting it. If you feel any resistance, stop immediately, remove the fan cable connector, and make sure that both it and the connector on Raspberry Pi 5 are undamaged before proceeding. Make sure that the connector on the cable is pushed down fully onto the connector on Raspberry Pi 5.
- We recommend that the Active Cooler is not removed once it is fitted to Raspberry Pi 5. Removal of the Active Cooler will cause the push pins and thermal pads to degrade and is likely to lead to product damage.
- Ensure the push pins are undamaged and can clip on to the Raspberry Pi board securely before use. Discontinue use of the Active Cooler and replace the push pins if they are damaged or deformed, or if they do not clip securely
- Connect the stacking header 40 pin to the 40-pin GPIO of RaspberryPi5
- Reinstall the mini pi screen


See the [User Manual](https://datasheets.raspberrypi.com/cooling/raspberry-pi-active-cooler-product-brief.pdf)
See the [Video Walkthrough](https://www.youtube.com/shorts/e1CtdqeT3o0)


### Set up and connect speaker

1. Connect the speaker to the Raspberry Pi5 through the USB port.

#### Option 1: GUI Method (VNC)
1. Open VNC viewer and connect your Pi5. On the top right corner, click the Speaker icon, and de-select "mute"

#### Option 2: Command Line Method
Alternatively, you can pair the speaker from the terminal:

1. **Confirmed if the USB speaker is connected:**
   ```bash
   lsusb

   # you should see something like
   # Bus 003 Device 002: ID 08bb:2902 Texas Instruments PCM2902 Audio Codec
   ```

2. **Unmute the speaker:**
   ```bash
   wpctl set-mute @DEFAULT_AUDIO_SINK@ 0

   # if you want to unmute it, wpctl set-mute @DEFAULT_AUDIO_SINK@ 1

   wpctl set-volume @DEFAULT_AUDIO_SINK@ 80%
   # change the volume of the speaker
   ```

### Set up the USB Microphone

#### Option 1: GUI Method (VNC)
1. Open VNC viewer and connect your Pi5. On the top right corner, click the Microphone icon, and de-select "mute"

#### Option 2: Command Line Method
Alternatively, you can pair the speaker from the terminal:

1. **Confirmed if the USB speaker is connected:**
   ```bash
   lsusb

   # you should see something like
   # Bus 001 Device 002: ID 4c4a:4155 Jieli Technology UACDemoV1.0
   ```

2. **Unmute the speaker:**
   ```bash
   wpctl set-mute @DEFAULT_AUDIO_SOURCE@ 0 

   # if you want to unmute it, wpctl set-mute @DEFAULT_AUDIO_SOURCE@ 1

   wpctl set-volume @DEFAULT_AUDIO_SOURCE@ 80%
   # change the microphone volume
   ```


### Test the Microphone and the Speaker

1. **Find your microphone's card number:**
```bash
   arecord -l

   # you should see something like
   # **** List of CAPTURE Hardware Devices ****
   # card 3: Device [USB PnP Sound Device], device 0: USB Audio [USB Audio]
   #   Subdevices: 1/1
   #   Subdevice #0: subdevice #0
```
   Note the number after `card` (here it is `3`). Yours may be different.

2. **Create the recording script:**

   Copy and paste the whole block below into the terminal. It writes a script called `record.sh` in your home folder.
```bash
   cat > ~/record.sh << 'EOF'
   #!/bin/bash
   # Records 5 seconds from the USB microphone and saves it as a .wav file

   # Uses the first capture card found; to override, run: ./record.sh 3
   MIC_CARD=${1:-$(arecord -l | awk -F'[ :]' '/^card/{print $2; exit}')}
   OUT="$HOME/recording_$(date +%Y%m%d_%H%M%S).wav"

   if [ -z "$MIC_CARD" ]; then
       echo "No microphone found. Check the connection with: arecord -l"
       exit 1
   fi

   echo "Recording 5 seconds from card $MIC_CARD... speak now!"
   if arecord -D plughw:${MIC_CARD},0 -f S16_LE -r 16000 -c 1 -d 5 "$OUT"; then
       echo "Saved to $OUT"
   else
       echo "Recording failed. Check the card number with: arecord -l"
   fi
   EOF
```

3. **Make the script executable and run it:**
```bash
   chmod +x ~/record.sh
   ~/record.sh

   # now speak, or sing a song you like, for 5 seconds
```

4. **Check that the file was saved:**
```bash
   ls ~/recording_*.wav

   # you should see something like
   # /home/pi/recording_20260922_192145.wav
```

5. **Play back your recording:**
```bash
   aplay "$(ls -t ~/recording_*.wav | head -1)"

   # this plays your most recent recording
   # you should hear what you just said or sang
```

#### Troubleshooting
- **`audio open error: No such file or directory`**: the card number is wrong. Run `arecord -l` again and pass the right number, e.g. `~/record.sh 3`.
- **The recording is silent or very quiet**: run `alsamixer`, press `F6` to select your USB microphone, press `F4` for capture, and raise the level. `MM` means muted; press `M` to unmute.
- **You can't hear the playback**: check that the speaker is unmuted and set as the default output with `wpctl status`.
