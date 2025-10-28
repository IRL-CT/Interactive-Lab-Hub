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

# 创建显示窗口
cv2.namedWindow('Object Detection', cv2.WINDOW_NORMAL)

with torch.no_grad():
    while True:
        # read frame
        ret, image = cap.read()
        if not ret:
            raise RuntimeError("failed to read frame")

        # 保存原始图像用于显示
        display_image = image.copy()

        # convert opencv output from BGR to RGB
        image = image[:, :, [2, 1, 0]]
        
        # preprocess
        input_tensor = preprocess(image)

        # create a mini-batch as expected by the model
        input_batch = input_tensor.unsqueeze(0)

        # run model
        output = net(input_batch)
        top = list(enumerate(output[0].softmax(dim=0)))
        top.sort(key=lambda x: x[1], reverse=True)
        
        # 在图像上绘制识别结果
        y_offset = 30
        for idx, val in top[:3]:  # 显示前3个结果
            label = f"{classes[str(idx)]}: {val.item()*100:.1f}%"
            cv2.putText(display_image, label, (10, y_offset), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            y_offset += 30
            print(f"{val.item()*100:.2f}% {classes[str(idx)]}")

        # log model performance
        frame_count += 1
        now = time.time()
        if now - last_logged > 1:
            fps = frame_count / (now-last_logged)
            print(f"{fps:.1f} fps")
            # 在图像上显示FPS
            cv2.putText(display_image, f"FPS: {fps:.1f}", (10, display_image.shape[0] - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
            last_logged = now
            frame_count = 0

        # 显示图像
        cv2.imshow('Object Detection', display_image)
        
        # 按 'q' 退出
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("Exiting...")
            break

# 清理
cap.release()
cv2.destroyAllWindows()