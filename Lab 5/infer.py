"""
Real-time image classification using OpenCV and PyTorch.

Loads a PyTorch image classification model and quantizes it for efficient 
inference. Opens a webcam feed, runs images through model to predict top classes.

from https://pytorch.org/tutorials/intermediate/realtime_rpi.html
"""




import time

import torch
import numpy as np
from torchvision import models, transforms

import cv2
from PIL import Image

import json

#open classes as dict
with open('classes.json') as f:
  classes = json.load(f)


torch.backends.quantized.engine = 'qnnpack'
#video capture setup
cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 224)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 224)
cap.set(cv2.CAP_PROP_FPS, 36)

#preprocess
preprocess = transforms.Compose([
    # convert the frame to a CHW torch tensor for training
    transforms.ToTensor(),
    # normalize the colors to the range that mobilenet_v2/3 expect
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])


#get model - others can be found here https://pytorch.org/tutorials/intermediate/realtime_rpi.html
net = models.quantization.mobilenet_v2(pretrained=True, quantize=True)
# jit model to take it from ~20fps to ~30fps
net = torch.jit.script(net)


started = time.time()
last_logged = time.time()
frame_count = 0

with torch.no_grad():
    while True:
        # read frame
        ret, image = cap.read()
        print('read')
        if not ret:
            raise RuntimeError("failed to read frame")

        # convert opencv output from BGR to RGB
        image = image[:, :, [2, 1, 0]]
        print('image', image.shape)
        permuted = image

        # preprocess
        input_tensor = preprocess(image)
        print('preprocessing finished')

        # create a mini-batch as expected by the model
        # The model can handle multiple images simultaneously so we need to add an
	# empty dimension for the batch.
	# [3, 224, 224] -> [1, 3, 224, 224]
        input_batch = input_tensor.unsqueeze(0)

        # run model
        output = net(input_batch)
        top = list(enumerate(output[0].softmax(dim=0)))
        top.sort(key=lambda x: x[1], reverse=True)
        for idx, val in top[:2]:
            print(f"{val.item()*100:.2f}% {classes[str(idx)]}")


        # log model performance
        frame_count += 1
        now = time.time()
        if now - last_logged > 1:
            print(f"{frame_count / (now-last_logged)} fps")
            last_logged = now
            frame_count = 0

