#!/usr/bin/env python
#-------------------------------------------------------------------------------
# qwiic_huskylens_ex6_color_recognition.py
#
# This example shows how to set the Huskylens up for color recognition.
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
	print("\nQwiic Huskylens Example 6 - Color Recognition\n")

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
	myHuskylens.set_algorithm(myHuskylens.kAlgorithmColorRecognition) # The device has several algorithms, we want to use color recognition

	# Prompt user to learn the first color
	print("Lets teach the HuskyLens the first color and assign it an ID of 1.")
	print("Please show a color to the camera until it is outlined in a square, and then enter anything to continue.")
	input()
	print("Will attempt to learn the color in 3 seconds.")
	time.sleep(3)

	# This function will return when it sees a chunk of color while in color recognition mode
	myHuskylens.wait_for_objects_of_interest()

	# When the device sees the color, let's learn it!
	myHuskylens.learn_new()
	print("Color learned and assigned ID 1!")

	# Prompt user to learn the second Color, and ask for the name
	print("Lets teach the HuskyLens the second color and assign it an ID of 2.")
	print("Please show another color to the camera and then enter anything to continue. ")
	print("NOTE: We won't see a square around the color we're learning this time, so try to keep the color in the center of the camera.")
	input()
	print("Will attempt to learn the color in 3 seconds.")
	time.sleep(3)

	# Note how we don't wait for objects of interest this time, as we're not looking for a square around the color

	myHuskylens.learn_new()
	print("Color learned!")

	nScans = 0
	print("Now look at any different colors of the same type as the two colors we have just learned.")
	print("They should have the expected IDs.")

	while True:
		# This function will return a list of objects of interest that the device sees
		# In color recognition mode, these objects will be squares around matches to the colors we have learned
		myColors = myHuskylens.get_objects_of_interest()
		if len(myColors) == 0:
			print("No colors found")
		else:
			print("----------------------New Colors Scan #{}----------------------".format(nScans))
			for i, color in enumerate(myColors):
				print ("Color ID: " + str(color.id))
				print ("Color X: " + str(color.xCenter))
				print ("Color Y: " + str(color.yCenter))
				print ("Color Width: " + str(color.width))
				print ("Color Height: " + str(color.height))
				print("\n")

				nScans += 1

		time.sleep(2)

if __name__ == '__main__':
	try:
		runExample()
	except (KeyboardInterrupt, SystemExit) as exErr:
		print("\nEnding Example")
		sys.exit(0)


