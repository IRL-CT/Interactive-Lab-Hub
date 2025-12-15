#!/usr/bin/env python
#-------------------------------------------------------------------------------
# qwiic_huskylens_ex8_object_classification.py
#
# This example shows how to set the Huskylens up for object classification.
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

# Provide platform-dependent way to get current time in milliseconds
if hasattr(time, "monotonic_ns"):
	def millis():
		return time.monotonic_ns() // 1000000 # works in CircuitPython and Linux/Raspberry Pi
else:
	def millis():
		return time.time_ns() // 1000000 #only works in MicroPython
	
def runExample():
	print("\nQwiic Huskylens Example 8 - Object Classification\n")

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
	if myHuskylens.set_algorithm(myHuskylens.kAlgorithmObjectClassification) == False: # The device has several algorithms, we want to use object classification
		print("Failed to set algorithm. Please try running again.", file=sys.stderr)

	# Prompt user to learn the first object
	print("Lets teach the HuskyLens an object to learn.")
	print("Place the object in front of the camera.")
	print("When the object is in view and in the square, enter anything to continue.")
	input()
	
	# When we've lined up with our object, let's learn it
	myHuskylens.learn_new()
	print("Object learned!")

	print("Continue moving The object around until the Huskylen can track it at different angles.")
	print("Will train for 15 seconds")

	startTime = millis()
	while (millis() - startTime < 15000):
		# Wait for the device to see the object
		myHuskylens.wait_for_objects_of_interest()

		# Learn the object at the new angle
		myHuskylens.learn_same()
		time.sleep(0.1)
	
	# Prompt user to learn the second object
	print("Lets teach the HuskyLens a second object to learn.")
	print("Place the object in front of the camera.")
	print("When the object is in view and in the square, enter anything to continue.")
	input()

	# When we've lined up with our object, let's learn it
	myHuskylens.learn_new()
	print("Object learned!")

	print("Continue moving The object around until the Huskylen can track it at different angles.")
	print("Will train for 15 seconds")

	startTime = millis()
	while (millis() - startTime < 15000):
		# Wait for the device to see the object
		myHuskylens.wait_for_objects_of_interest()

		# Learn the object at the new angle
		myHuskylens.learn_same()
		time.sleep(0.1)
	
	# Classification simply tries to fit objects into the categories we have taught it
	# The block will not move with the object, but the ID will be the closest match the algorithm can make to an ID we have taught it
	nScans = 0
	while True:
		# This function will return a list of objects of interest that the device sees
		# In object classification mode, these objects will have the ID of one of the objects we have learned
		myClassifications = myHuskylens.get_objects_of_interest()
		if len(myClassifications) == 0:
			print("No objects found")
		else:
			print("----------------------New Objects Scan #{}----------------------".format(nScans))

			for classification in myClassifications:
				print ("object ID: " + str(classification.id))
				# Note: The below values have less meaning in classification mode, as the returned block will not move with the object
				print ("object X: " + str(classification.xCenter))
				print ("object Y: " + str(classification.yCenter))
				print ("object Width: " + str(classification.width))
				print ("object Height: " + str(classification.height))
				print("\n")

				nScans += 1

		time.sleep(2)

if __name__ == '__main__':
	try:
		runExample()
	except (KeyboardInterrupt, SystemExit) as exErr:
		print("\nEnding Example")
		sys.exit(0)