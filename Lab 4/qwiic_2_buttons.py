import qwiic_button
import time
import sys


def run_example():

	# Default button (0x6F)
	button1 = qwiic_button.QwiicButton() # green
	# Button with A0 soldered (0x6E)
	button2 = qwiic_button.QwiicButton(0x6E) # red

	button1.begin()
	button2.begin()

	print("\nButtons ready!")

	while True:
		if button1.is_button_pressed() and button2.is_button_pressed():
			print("Both Button 1 and 2 are pressed!")

		elif button1.is_button_pressed():
			print("Button 1 pressed!")

		elif button2.is_button_pressed():
			print("Button 2 pressed!")
	
		time.sleep(0.3)

if __name__ == '__main__':
    try:
        run_example()
    except (KeyboardInterrupt, SystemExit) as exErr:
        print("\nEnding Example")
        sys.exit(0)

