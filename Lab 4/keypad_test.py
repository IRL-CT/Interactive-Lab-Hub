# Make sure to have everything set up
# https://github.com/sparkfun/Qwiic_Keypad_Py 
# `pip install sparkfun-qwiic-keypad`

# From https://github.com/sparkfun/Qwiic_Keypad_Py/blob/main/examples/qwiic_keypad_ex2.py


from __future__ import print_function
import qwiic_keypad
import time
import sys

def runExample():

	print("\nSparkFun qwiic Keypad   Example 1\n")
	myKeypad = qwiic_keypad.QwiicKeypad()

	if myKeypad.connected == False:
		print("The Qwiic Keypad device isn't connected to the system. Please check your connection", \
			file=sys.stderr)
		return

	myKeypad.begin()

	print("Initialized. Firmware Version: %s" % myKeypad.version)
	print("Press a button: * to do a space. # to go to next line.")

	button = 0
	while True:

		# necessary for keypad to pull button from stack to readable register
		myKeypad.update_fifo()  
		button = myKeypad.get_button()

		if button == -1:
			print("No keypad detected")
			time.sleep(1)

		elif button != 0:

			# Get the character version of this char
			charButton = chr(button)
			if charButton == '#':
				print()
			elif charButton == '*':
				print(" ", end="")
			else: 
				print(charButton, end="")

			# Flush the stdout buffer to give immediate user feedback
			sys.stdout.flush()

		time.sleep(.25)

if __name__ == '__main__':
	try:
		runExample()
	except (KeyboardInterrupt, SystemExit) as exErr:
		print("\nEnding Example 1")
		sys.exit(0)