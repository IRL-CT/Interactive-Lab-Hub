#!/usr/bin/env python
#-------------------------------------------------------------------------------
# qwiic_huskylens_ex4_object_recognition.py
#
# This example shows how to set the Huskylens up for object recognition.
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
	print("\nQwiic Huskylens Example 4 - Object Recognition\n")

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
	myHuskylens.set_algorithm(myHuskylens.kAlgorithmObjectRecognition) # The device has several algorithms, we want to use object recognition

	# Prompt user to "learn" an object by assigning it an ID
	# The Huskylens has 20 preset objects that it can detect:
	# airplane, bicylce, bird, boat, bottle, bus, car, cat, chair, cow, table
	# dog, horse, motorbike, person, potted plant, sheep, sofa, train, TV
	# Point at one of these objects and learn it to assign it an id
	# Then, other objects of this type should return blocks with the same ID
	print("Lets teach the HuskyLens the first object and assign it an ID of 1.")
	print("Please show one of the 20 allowed objects to the camera and then enter anything to continue.")
	input()
	print("Will attempt to learn the object in 3 seconds.")
	time.sleep(3)

	# Wait for the device to see an object
	myHuskylens.wait_for_objects_of_interest()

	# When the device sees an object, let's learn it!
	myHuskylens.learn_new()
	print("Object learned and assigned ID 1!")

	# Prompt user to learn the second Object
	print("Lets teach the HuskyLens the second object and assign it an ID of 2.")
	print("Please show one of the 20 allowed objects to the camera and then enter anything to continue.")
	input()
	print("Will attempt to learn the object in 3 seconds.")
	time.sleep(3)

	myHuskylens.wait_for_objects_of_interest()

	myHuskylens.learn_new()
	print("Object learned!")

	nScans = 0
	print("Now look at any different objects of the same type as the two objects we have just learned.")
	print("They should have the expected IDs.")

	while True:
		# This function will return a list of objects of interest that the device sees
		# In object recognition mode, these objects will be one of the 20 preset objects if they are recognized
		myObjects = myHuskylens.get_objects_of_interest()
		if len(myObjects) == 0:
			print("No objects found")
		else:
			print("----------------------New Objects Scan #{}----------------------".format(nScans))
			myObjects = myHuskylens.blocks # Each recognized object will be stored in a "block" object containing the object's information

			for i, obj in enumerate(myObjects):
				# Unfortunately, the device doesn't return the name of the object, but shows it on the screen
				# Since we trained it however, we know that the first object we trained is ID 1, and the second is ID 2
				# For example if you trained it on a cat for id1 and a car for id2 we know that all future blocks with id 1 are cats and all future blocks with id 2 are cars
				print ("Object ID: " + str(obj.id))
				print ("Object X: " + str(obj.xCenter))
				print ("Object Y: " + str(obj.yCenter))
				print ("Object Width: " + str(obj.width))
				print ("Object Height: " + str(obj.height))
				print("\n")

				nScans += 1

		time.sleep(2)

if __name__ == '__main__':
	try:
		runExample()
	except (KeyboardInterrupt, SystemExit) as exErr:
		print("\nEnding Example")
		sys.exit(0)


