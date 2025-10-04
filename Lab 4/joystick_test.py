from __future__ import print_function
import qwiic_joystick
import time
import sys

def runExample():

	print("\nSparkFun qwiic Joystick   Example 1\n")
	myJoystick = qwiic_joystick.QwiicJoystick()

	if myJoystick.connected == False:
		print("The Qwiic Joystick device isn't connected to the system. Please check your connection", \
			file=sys.stderr)
		return

	myJoystick.begin()

	print("Initialized. Firmware Version: %s" % myJoystick.version)

	while True:

		print("X: %d, Y: %d, Button: %d" % ( \
					myJoystick.horizontal, \
					myJoystick.vertical, \
					myJoystick.button))

		time.sleep(.5)

if __name__ == '__main__':
	try:
		runExample()
	except (KeyboardInterrupt, SystemExit) as exErr:
		print("\nEnding Example 1")
		sys.exit(0)