#!/usr/bin/env python
#-------------------------------------------------------------------------------
# qwiic_huskylens_ex1_face_recognition_2d.py
#
# This example shows how to set the Huskylens up for facial recognition and teach it two 2-D faces.
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
	print("\nQwiic Huskylens Example 1 - 2D Face Recognition\n")

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

	myHuskylens.forget() # Forget all the faces that the device has already learned
	myHuskylens.set_algorithm(myHuskylens.kAlgorithmFaceRecognition) # The device has several algorithms, we want to use face recognition

	# Prompt user to learn the first face, and ask for the name
	print("Lets teach the HuskyLens the first 2D face.")
	newName = input("Enter the name of the 2D face you are about to teach the lens: ")
	print("Please show the face to the camera. Will attempt to learn the face in 3 seconds.")
	time.sleep(3)

	# Wait for the device to see a face
	myHuskylens.wait_for_objects_of_interest()

	# When the device sees a face, let's learn it and name it!
	myHuskylens.learn_new()
	myHuskylens.name_last(newName)
	print("Face learned!")

	# Prompt user to learn the second face, and ask for the name
	print("Lets teach the HuskyLens the second 2D face.")
	newName = input("Enter the name of the 2D face you are about to teach the lens: ")
	print("Please show the face to the camera. Will attempt to learn the face in 3 seconds.")
	time.sleep(3)

	myHuskylens.wait_for_objects_of_interest()

	myHuskylens.learn_new()
	myHuskylens.name_last(newName)
	print("Face learned!")

	nScans = 0
	while True:
		# This function will return a list of objects of interest that the device sees
		# In face recognition mode, these objects will be faces
		myFaces = myHuskylens.get_objects_of_interest()
		if len(myFaces) == 0:
			print("No faces found")
		else:
			print("----------------------New Faces Scan #{}----------------------".format(nScans))

			for face in myFaces:
				name = myHuskylens.get_name_for_id(face.id) # The myHuskylens object keeps track of the names we have assigned this program run
				if name:
					print("Face Name: " + name)
				print ("Face ID: " + str(face.id))
				print ("Face X: " + str(face.xCenter))
				print ("Face Y: " + str(face.yCenter))
				print ("Face Width: " + str(face.width))
				print ("Face Height: " + str(face.height))
				print("\n")

				nScans += 1

		time.sleep(2)

if __name__ == '__main__':
	try:
		runExample()
	except (KeyboardInterrupt, SystemExit) as exErr:
		print("\nEnding Example")
		sys.exit(0)