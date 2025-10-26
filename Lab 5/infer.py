"""
Real-time image classification using OpenCV and PyTorch.
Improved version: cleaner output and limited printing frequency.
"""

import time
import os
import torch
import numpy as np
from torchvision import models, transforms
import cv2
from PIL import Image
import json

# open classes as dict
with open('classes.json') as f:
    classes = json.load(f)

torch.backends.quantized.engine = 'qnnpack'

# video capture setup
cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 224)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 224)
cap.set(cv2.CAP_PROP_FPS, 36)

# preprocess
preprocess = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225]),
])

# load model
net = models.quantization.mobilenet_v2(pretrained=True, quantize=True)
net = torch.jit.script(net)

started = time.time()
last_logged = time.time()
frame_count = 0

with torch.no_grad():
    while True:
        # read frame
        ret, image = cap.read()
        if not ret:
            print("Failed to read frame.")
            break

        # convert opencv output from BGR to RGB
        image = image[:, :, [2, 1, 0]]

        # preprocess
        input_tensor = preprocess(image)
        input_batch = input_tensor.unsqueeze(0)

        # run model
        output = net(input_batch)
        top = list(enumerate(output[0].softmax(dim=0)))
        top.sort(key=lambda x: x[1], reverse=True)

        # count frame
        frame_count += 1
        now = time.time()

        # only print every second
        if now - last_logged > 1:
            os.system('clear')  # clear terminal each time for cleaner view
            top1_idx, top1_val = top[0]
            fps = frame_count / (now - last_logged)
            print(f"Top prediction: {classes[str(top1_idx)]} ({top1_val.item()*100:.2f}%)")
            print(f"FPS: {fps:.2f}")
            print("Press 'q' to quit.")
            last_logged = now
            frame_count = 0

        # check for quit key (q)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("Exiting...")
            break

cap.release()
cv2.destroyAllWindows()

