"""
AI Emotion Spectrum Filter - Real-time Camera Visualizer
Based on image classification using OpenCV and PyTorch.
"""

import time
import os
import torch
import numpy as np
from torchvision import models, transforms
import cv2
import json

# -------------------------
# Load label dictionary
# -------------------------
with open('classes.json') as f:
    classes = json.load(f)

torch.backends.quantized.engine = 'qnnpack'

# -------------------------
# Video setup
# -------------------------
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 224)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 224)
cap.set(cv2.CAP_PROP_FPS, 30)

# -------------------------
# Preprocess
# -------------------------
preprocess = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225]),
])

# -------------------------
# Load model
# -------------------------
net = models.quantization.mobilenet_v2(pretrained=True, quantize=True)
net.eval()

# -------------------------
# Define emotion colors
# -------------------------
emotion_colors = {
    "person": (0, 180, 255),   # orange - warm
    "book": (255, 100, 0),     # blue - calm
    "cup": (0, 255, 200),      # aqua - refreshing
    "box": (200, 0, 200),      # purple - mysterious
    "mouse": (255, 255, 0),    # yellow - energetic
    "default": (128, 128, 128) # neutral gray
}

# -------------------------
# Start streaming
# -------------------------
last_logged = time.time()
frame_count = 0

with torch.no_grad():
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to read frame.")
            break

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        input_tensor = preprocess(rgb_frame)
        input_batch = input_tensor.unsqueeze(0)

        # inference
        output = net(input_batch)
        top = list(enumerate(output[0].softmax(dim=0)))
        top.sort(key=lambda x: x[1], reverse=True)
        top1_idx, top1_val = top[0]
        label = classes[str(top1_idx)]
        prob = top1_val.item() * 100

        # choose color
        color = emotion_colors.get(label, emotion_colors["default"])

        # overlay color filter
        overlay = np.full(frame.shape, color, dtype=np.uint8)
        alpha = 0.3  # transparency
        filtered_frame = cv2.addWeighted(frame, 1 - alpha, overlay, alpha, 0)

        # text overlay
        cv2.putText(filtered_frame, f"{label} ({prob:.1f}%)",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                    (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(filtered_frame, "Press 'q' to quit",
                    (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                    (255, 255, 255), 1, cv2.LINE_AA)

        # show frame
        cv2.imshow("AI Emotion Spectrum", filtered_frame)

        # quit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("Exiting...")
            break

cap.release()
cv2.destroyAllWindows()
