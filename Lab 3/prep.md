
# Prep your Pi


### To prepare lab 3, you will need:

- Raspberry Pi 5
- Active Cooler for Pi 5
- Stacking Header 40 pin
- Bluetooth Speaker
- Logitech Webcam w/camera 


### Install Active Cooler

- Unpack the preassembled Active Cooler from its box.
- Remove the backing paper from the thermal pads on the underside of the product.
- Make sure your Raspberry Pi 5 is powered off. Position the Active Cooler carefully in the correct space on Raspberry Pi 5, making sure not to hit any of the connectors. Please refer to the diagram on the front of the box which shows the correct position and orientation of the product.
- Align the two white push pins with the two dedicated heatsink holes.
- When correctly positioned, press evenly on the tops of the two push pins simultaneously until they click, indicating that they are clipped onto the board.
- Once the Active Cooler is mounted, connect its fan cable to the connector labelled‘FAN’ on Raspberry Pi 5. Take care to ensure the cable’s connector is the correct way round when inserting it. If you feel any resistance, stop immediately, remove the fan cable connector, and make sure that both it and the connector on Raspberry Pi 5 are undamaged before proceeding. Make sure that the connector on the cable is pushed down fully onto the connector on Raspberry Pi 5.
- We recommend that the Active Cooler is not removed once it is fitted to Raspberry Pi 5. Removal of the Active Cooler will cause the push pins and thermal pads to degrade and is likely to lead to product damage.
- Ensure the push pins are undamaged and can clip on to the Raspberry Pi board
securely before use. Discontinue use of the Active Cooler and replace the push pins
if they are damaged or deformed, or if they do not clip securely

See the [User Manual](https://datasheets.raspberrypi.com/cooling/raspberry-pi-active-cooler-product-brief.pdf)
See the [Video Walkthrough](https://www.youtube.com/shorts/e1CtdqeT3o0)


### Set up and connect bluetooth speaker

1. Charge the Bluetooth speaker with the paired USB type C cable.
2. Disconnect the speaker from charging. Long press the power icon on the speaker body, until the small white LED flashes.
3. Open VNC viewer and connect your Pi5. On the top right corner, click the Bluetooth icon, and on the dropdown menu, select "Make Discoverable". Meanwhile, select "Add Device". Once you find the 'X1', pair and connect with it. You should hear a "beep" if the connection is successful
<img src="https://github.com/IRL-CT/Interactive-Lab-Hub/blob/Fall2025-shadow/Lab%203/Bluetooth.png" alt="choose os" height="400" />

### Set up the Web camera

1. stay in the VNC, open terminal and run this commandline:

	```
	$ sudo apt install pavucontrol
	```
2. open pavucontrol through this commandline. You should see an GUI open.

 	```
	$ pavucontrol
	```
<img src="https://github.com/IRL-CT/Interactive-Lab-Hub/blob/Fall2025-shadow/Lab%203/pavucontrol.png" alt="choose os" height="400" />
3. Navigate to the Configuration, make sure the profile of the C270 Webcam is Mono Input
4. Navigate to the Input Devices, you should see a bar moving as you speak - which means you have set up correctly
	
