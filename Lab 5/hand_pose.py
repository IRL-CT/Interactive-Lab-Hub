import cv2
import time
import numpy as np
import HandTrackingModule as htm
import math
from ctypes import cast, POINTER
import alsaaudio
m = alsaaudio.Mixer(control='Speaker', cardindex=3)
m.setvolume(5) 
import subprocess

def play_audio():
    command = ['./loop_audio.sh']
    process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print('Looping audio playback - press q to quit')
    return process  # Return the process object

audio_process = play_audio()

################################
wCam, hCam = 640, 480
################################
 
cap = cv2.VideoCapture(0)
cap.set(3, wCam)
cap.set(4, hCam)
pTime = 0
 
detector = htm.handDetector(detectionCon=int(0.7))
minVol = 0
maxVol = 100
vol = 0
volBar = 400
volPer = 0
while True:
    success, img = cap.read()
    img = detector.findHands(img)
    lmList = detector.findPosition(img, draw=False)
    if len(lmList) != 0:
 
        thumbX, thumbY = lmList[4][1], lmList[4][2] #thumb
        pointerX, pointerY = lmList[8][1], lmList[8][2] #pointer

        middleX, middleY = lmList[12][1], lmList[12][2]
        ringX, ringY = lmList[16][1], lmList[16][2]
        pinkyX, pinkyY = lmList[20][1], lmList[20][2]
        
        cx, cy = (thumbX + pointerX) // 2, (thumbY + pointerY) // 2
 
        cv2.circle(img, (thumbX, thumbY), 15, (255, 0, 255), cv2.FILLED)
        cv2.circle(img, (pointerX, pointerY), 15, (255, 0, 255), cv2.FILLED)
        cv2.circle(img, (middleX, middleY), 15, (255, 0, 255), cv2.FILLED)
        cv2.circle(img, (ringX, ringY), 15, (255, 0, 255), cv2.FILLED)
        cv2.circle(img, (pinkyX, pinkyY), 15, (255, 0, 255), cv2.FILLED)
        cv2.line(img, (thumbX, thumbY), (pointerX, pointerY), (255, 0, 255), 3)
        cv2.circle(img, (cx, cy), 15, (255, 0, 255), cv2.FILLED)

        len_calc = lambda x1,y1,x2,y2: math.hypot(x2 - x1, y2 - y1)
        length = len_calc(thumbX,thumbY,pointerX,pointerY)
        length1 = len_calc(pointerX,pointerY,middleX,middleY)
        length2 = len_calc(middleX, middleY, ringX, ringY)
        length3 = len_calc(ringX, ringY, pinkyX, pinkyY)
        length4 = len_calc(thumbX,thumbY, ringX, ringY)
        print(length1,length2,length3)
        condition = length>100 and length1>100 and length2<100 and length3>100 and length4<100
        if condition:
            m.setvolume(0)
            volPer = 0
            volBar = 400
            print("CONDITION")
            cv2.putText(img, 'quiet coyote!', (40, 70), cv2.FONT_HERSHEY_COMPLEX,
                1, (255, 255, 255), 3)
        else:
 
            vol = np.interp(length, [50, 300], [minVol, maxVol])
            volBar = np.interp(length, [50, 300], [400, 150])
            volPer = np.interp(length, [50, 300], [0, 100])
            m.setvolume(int(vol))

        print(int(length), vol)

 
        if length < 50:
            cv2.circle(img, (cx, cy), 15, (0, 255, 0), cv2.FILLED)
 
    cv2.rectangle(img, (50, 150), (85, 400), (255, 0, 0), 3)
    cv2.rectangle(img, (50, int(volBar)), (85, 400), (255, 0, 0), cv2.FILLED)
    cv2.putText(img, f'{int(volPer)} %', (40, 450), cv2.FONT_HERSHEY_COMPLEX,
                1, (255, 0, 0), 3)
 
 
    cTime = time.time()
    fps = 1 / (cTime - pTime)
    pTime = cTime
    cv2.putText(img, f'FPS: {int(fps)}', (40, 50), cv2.FONT_HERSHEY_COMPLEX,
                1, (255, 0, 0), 3)

    cv2.imshow("Img", img)
    if cv2.waitKey(1) & 0xFF == ord('q'):  # Press 'q' to quit
        audio_process.terminate()  #
        break

cap.release()
cv2.destroyAllWindows()