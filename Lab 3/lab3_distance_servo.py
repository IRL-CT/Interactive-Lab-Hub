# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

import pi_servo_hat
import time
import board
from adafruit_apds9960.apds9960 import APDS9960
import cv2
import pyaudio
import wave
import pygame
import os

def speak_text_festival(text):
    command = f'echo "{text}" | festival --tts'
    os.system(command)

prototxt = "camera_models/MobileNetSSD_deploy.prototxt"
model = "camera_models/MobileNetSSD_deploy.caffemodel"

net = cv2.dnn.readNetFromCaffe(prototxt, model)

# Set up person detection model, reference: https://medium.com/@tauseefahmad12/object-detection-using-mobilenet-ssd-e75b177567ee
PERSON_CLASS_ID = 15
CONF_THRESH = 0.5

# Set up servo: For most 9g micro servos (like SG90, MS18, SER0048), safe range is 0-120 degrees
SERVO_MIN = 0
SERVO_MAX = 90
SERVO_CH = 0  # Channel 0 by default

servo = pi_servo_hat.PiServoHat()
servo.restart()

# Set up proximity sensor
i2c = board.I2C()
apds = APDS9960(i2c)

apds.enable_proximity = True

print(f"Sweeping servo on channel {SERVO_CH} from {SERVO_MIN} to {SERVO_MAX} degrees...")
keys_taken = False

cap = cv2.VideoCapture(0)
while True:
    ret, frame = cap.read()
    if not ret:
        break
    h, w = frame.shape[:2]
    blob = cv2.dnn.blobFromImage(frame, 0.007843, (300,300), 127.5)
    net.setInput(blob)
    detections = net.forward()

    person_found = False
    for i in range(detections.shape[2]):
        conf = float(detections[0,0,i,2])
        cls  = int(detections[0,0,i,1])
        if conf > CONF_THRESH and cls == PERSON_CLASS_ID:
            person_found = True
            box = detections[0,0,i,3:7]*[w,h,w,h]
            (startX, startY, endX, endY) = box.astype("int")
            cv2.rectangle(frame, (startX,startY), (endX,endY), (0,255,0), 2)
            break
      
    cv2.putText(frame, f"Person: {person_found}", (10,30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
    cv2.imshow("frame", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

    # shake keys if person detected and not too close
    if person_found and apds.proximity > 5:
        servo.move_servo_position(SERVO_CH, 0)
        break
    elif person_found:
       speak_text_festival("Don't forget your keys!")
       if apds.proximity > 5:
            servo.move_servo_position(SERVO_CH, 0)
            break
       for i in range(3):  # Shake keys 3 times
            # Sweep up
            for angle in range(SERVO_MIN, SERVO_MAX + 1, 1):
                servo.move_servo_position(SERVO_CH, angle)
                time.sleep(0.001)
            # Sweep down
            for angle in range(SERVO_MAX, SERVO_MIN - 1, -1):
                servo.move_servo_position(SERVO_CH, angle)
                time.sleep(0.001)
            if apds.proximity > 5:
                servo.move_servo_position(SERVO_CH, 0)
                break
            

cap.release()
cv2.destroyAllWindows()
# prompt user for further interaction
time.sleep(0.5)
speak_text_festival("Is there anything else I can help you with? You can ask me about the weather, reminders, or your day")

# take in input for tts
while (True):
    text = input("Enter text to speak (or 'exit' to quit): ")
    if text.lower() == 'exit':
        break

    if(text == "bye"):
        speak_text_festival("Have a good day!")
        for i in range(3):  # Shake keys 3 times
            # Sweep up
            for angle in range(SERVO_MIN, SERVO_MAX + 1, 1):
                servo.move_servo_position(SERVO_CH, angle)
                time.sleep(0.001)
            # Sweep down
            for angle in range(SERVO_MAX, SERVO_MIN - 1, -1):
                servo.move_servo_position(SERVO_CH, angle)
                time.sleep(0.001)
    elif(text=="weather"):
        speak_text_festival("The weather today is 70 degrees and sunny. It's a little chilly so don't forget your jacket!")
    elif(text=="idk"):
        speak_text_festival("Sorry, I can't help you with that.")
    elif(text=="prompt"):
        speak_text_festival("Is there anything else I can help you with?")
    elif(text=="forget"):
        speak_text_festival("Don't forget your phone, wallet, and jacket!")
    elif(text=="yw"):
        speak_text_festival("You're welcome!")
    else:
        speak_text_festival(text)

'''
Potential Responses:

The weather today is 65 degrees and sunny. It's a little chilly so don't forget your jacket!
Don't forget your phone, wallet, and jacket!
You have a Product Studio meeting at 10pm today.
Have an amazing day!

'''
