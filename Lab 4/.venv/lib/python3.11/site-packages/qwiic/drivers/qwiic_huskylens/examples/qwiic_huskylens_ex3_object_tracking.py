#!/usr/bin/env python
#-------------------------------------------------------------------------------
# qwiic_huskylens_ex3_object_tracking.py
#
# This example shows how to set the Huskylens up for object tracking.
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
	print("\nQwiic Huskylens Example 3 - Object Tracking\n")

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
	myHuskylens.set_algorithm(myHuskylens.kAlgorithmObjectTracking) # The device has several algorithms, we want to use object tracking

	# Prompt user to learn the first object
	print("Lets teach the HuskyLens an object to track.")
	print("Place the object in front of the camera.")
	print("When the object is in view and in the square, enter anything to continue.")
	input()
	
	# When we've lined up with our object, let's learn it
	myHuskylens.learn_new()
	print("Object learned!")

	print("Continue moving The object around until the Huskylen can track it at different angles.")

	nScans = 0
	while True:
		# This function will return a list of objects of interest that the device sees
		# In object tracking mode, these objects will be the object we have learned
		myObjs = myHuskylens.get_objects_of_interest()

		if len(myObjs) == 0:
			print("No objects found")
		else:
			print("----------------------New Objects Scan #{}----------------------".format(nScans))

			for obj in myObjs:
				print ("object ID: " + str(obj.id))
				print ("object X: " + str(obj.xCenter))
				print ("object Y: " + str(obj.yCenter))
				print ("object Width: " + str(obj.width))
				print ("object Height: " + str(obj.height))
				print("\n")

				nScans += 1

		time.sleep(2)

if __name__ == '__main__':
	try:
		runExample()
	except (KeyboardInterrupt, SystemExit) as exErr:
		print("\nEnding Example")
		sys.exit(0)