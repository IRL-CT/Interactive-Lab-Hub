#!/usr/bin/env python
#-------------------------------------------------------------------------------
# qwiic_huskylens_ex7_tag_recognition.py
#
# This example shows how to set the Huskylens up for tag recognition.
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
	print("\nQwiic Huskylens Example 7 - Tag Recognition\n")

	# Create instance of device
	myHuskylens = qwiic_huskylens.QwiicHuskylens() 

	# Check if it's connected
	if myHuskylens.is_connected() == False:
		print("The device isn't connected to the system. Please check your connection",
			file=sys.stderr)
		return

	# Initialize the device
	if myHuskylens.begin() 	== False:
		print("Failed to initialize the device. Please check your connection", file=sys.stderr)
		return

	myHuskylens.forget() # Forget all the objects that the device has already learned
	myHuskylens.set_algorithm(myHuskylens.kAlgorithmTagRecognition) # The device has several algorithms, we want to use tag recognition

	# Prompt user to "learn" a tag by assigning it an ID
	print("Lets teach the HuskyLens the first tag and assign it an ID of 1.")
	print("Please show a tag to the camera until it is outlined in a square, and then enter anything to continue.")
	input()
	print("Will attempt to learn the tag in 3 seconds.")
	time.sleep(3)

	# This function will return when it sees a tag while in tag recognition mode
	myHuskylens.wait_for_objects_of_interest()

	# When the device sees the tag, let's learn it!
	myHuskylens.learn_new()
	print("Tag learned and assigned ID 1!")

	# Prompt user to learn the second tag, and ask for the name
	print("Lets teach the HuskyLens the second tag and assign it an ID of 2.")
	print("Please show another tag to the camera until it is outlined in a square, and then enter anything to continue. ")
	print("NOTE: We won't see the crosshair/+ symbol while learning this time,")
	print("so try to keep the tag in the center of the camera.")
	input()
	print("Will attempt to learn the tag in 3 seconds.")
	time.sleep(3)

	myHuskylens.wait_for_objects_of_interest()

	myHuskylens.learn_new()
	print("tag learned!")

	nScans = 0
	print("Now look at any different tags of the same type as the two tags we have just learned.")
	print("They should have the expected IDs.")

	while True:
		# This function will return a list of objects of interest that the device sees
		# In tag recognition mode, these objects will be tags
		myTags = myHuskylens.get_objects_of_interest()
		if len(myTags) == 0:
			print("No tags found")
		else:
			print("----------------------New tags Scan #{}----------------------".format(nScans))

			for i, tag in enumerate(myTags):
				print ("tag ID: " + str(tag.id))
				print ("tag X: " + str(tag.xCenter))
				print ("tag Y: " + str(tag.yCenter))
				print ("tag Width: " + str(tag.width))
				print ("tag Height: " + str(tag.height))
				print("\n")

				nScans += 1

		time.sleep(2)

if __name__ == '__main__':
	try:
		runExample()
	except (KeyboardInterrupt, SystemExit) as exErr:
		print("\nEnding Example")
		sys.exit(0)


