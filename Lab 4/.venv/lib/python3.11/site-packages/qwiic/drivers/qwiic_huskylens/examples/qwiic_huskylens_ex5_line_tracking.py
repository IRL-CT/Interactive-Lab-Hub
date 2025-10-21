#!/usr/bin/env python
#-------------------------------------------------------------------------------
# qwiic_huskylens_ex5_line_tracking.py
#
# This example shows how to set the Huskylens up for line tracking.
#-------------------------------------------------------------------------------
# Written by SparkFun Electronics, February 2025
#
# This python library supports the SparkFun Electroncis Qwiic ecosystem
#
# More information on Qwiic is at https://www.sparkfun.com/qwiic
#
# Do you like this library? Help support SparkFun. Buy a board!
#===============================================================================
# Copyright (c) 2024 SparkFun Electronics
#
# Permission is hereby granted, free of charge, to any person obtaining a copy 
# of this software and associated documentation files (the "Software"), to deal 
# in the Software without restriction, including without limitation the rights 
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell 
# copies of the Software, and to permit persons to whom the Software is 
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all 
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR 
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE 
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER 
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, 
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE 
# SOFTWARE.
#===============================================================================

import qwiic_huskylens 
import sys
import time

def runExample():
	print("\nQwiic Huskylens Example 5 - Line Tracking\n")

	# Create instance of device
	myHuskylens = qwiic_huskylens.QwiicHuskylens() 

	# Check if it's connected
	if myHuskylens.is_connected() == False:
		print("The device isn't connected to the system. Please check your connection",
			file=sys.stderr)
		return

	# Initialize the device
	if myHuskylens.begin() == False:
		print("Failed to initialize the device. Please check your connection", file=sys.stderr)
		return

	myHuskylens.forget() # Forget all the objects that the device has already learned
	myHuskylens.set_algorithm(myHuskylens.kAlgorithmLineTracking) # The device has several algorithms, we want to use line tracking

	# Prompt user to "learn" a line by assigning it an ID
	print("Lets teach the HuskyLens a line to track and assign it an ID of 1.")
	print("Please show a line on a solid background. Wait until an arrow appears somewhat steadily along your line and then enter anything to continue.")
	input()

	# 
	myHuskylens.wait_for_lines_of_interest()

	# When the device sees a line to track, let's learn it!
	myHuskylens.learn_new()
	print("Line learned!")
	
	# Now we should receive arrows giving us the direction of the line to follow
	nScans = 0
	while True:
		# This function will return a list of lines of interest that the device sees
		# In line tracking mode, the device will return "arrows" that show the direction of the line
		myArrows = myHuskylens.get_lines_of_interest()
		if len(myArrows) == 0:
			print("No arrows found")
		else:
			print("----------------------New Objects Scan #{}----------------------".format(nScans))

			for i, arrow in enumerate(myArrows):
				# Unfortunately, the device doesn't return the name of the object, but shows it on the screen
				# Since we trained it however, we know that the first object we trained is ID 1, and the second is ID 2
				# For example if you trained it on a cat for id1 and a car for id2 we know that all future blocks with id 1 are cats and all future blocks with id 2 are cars
				print ("Arrow ID: " + str(arrow.id))
				print ("Arrow X Start: " + str(arrow.xOrigin))
				print ("Arrow Y Start: " + str(arrow.yOrigin))
				print ("Arrow X Target: " + str(arrow.xTarget))
				print ("Arrow Y Target: " + str(arrow.yTarget))
				print("\n")

				nScans += 1

		time.sleep(2)

if __name__ == '__main__':
	try:
		runExample()
	except (KeyboardInterrupt, SystemExit) as exErr:
		print("\nEnding Example")
		sys.exit(0)


