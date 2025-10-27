"""
AI Emotion Spectrum
Real-time camera + object recognition + color filter art effect
"""

import cv2
import torch
import json
import time
import numpy as np
from torchvision import models, transforms
from PIL import Image

# ========================
# 1. Load label file
# ========================
with open('classes.json') as f:
    classes = json.load(f)

# ========================
# 2. Initialize model
# ========================
torch.backends.quantized.engine = 'qnnpack'
model = models.quantization.mobilenet_v2(pretrained=True, quantize=True)
model.eval()
model = torch.jit.script(model)

# ========================
# 3. Camera setup
# ========================
cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv2.CAP_PROP_FPS, 24)

# ========================
# 4. Preprocessing
# ========================
preprocess = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225])
])

# ========================
# 5. Color filters (AI emotion palette)
# ========================
colors = [
    (255, 120, 120),  # Red: Passion / Intensity
    (255, 200, 100),  # Orange: Energy / Creativity
    (255, 255, 150),  # Yellow: Joy / Optimism
    (150, 255, 150),  # Green: Calm / Balance
    (150, 200, 255),  # Blue: Peace / Coolness
    (200, 150, 255)   # Purple: Mystery / Dreamy
]

# ========================
# 6. Main loop
# ========================
last_logged = time.time()
frame_count = 0
last_label = None
current_color = colors[3]  # Start with green tone

with torch.no_grad():
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to read from camera.")
            break

        # Convert BGR → RGB (for PIL)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb)

        # Preprocess
        input_tensor = preprocess(pil_img)
        input_batch = input_tensor.unsqueeze(0)

        # Inference
        output = model(input_batch)
        probs = torch.nn.functional.softmax(output[0], dim=0)
        top_prob, top_idx = torch.topk(probs, 1)
        top_label = classes[str(top_idx.item())]
        confidence = top_prob.item() * 100

        # FPS calculation
        frame_count += 1
        now = time.time()
        fps = frame_count / (now - last_logged) if now - last_logged > 0 else 0
        if now - last_logged > 1:
            last_logged = now
            frame_count = 0

        # ========================
        # 7. Apply color filter (based on class, not confidence)
        # ========================
        # Change color only when the detected object changes
        if top_label != last_label:
            color_idx = hash(top_label) % len(colors)
            current_color = colors[color_idx]
            print(f"Object changed to: {top_label}")
            last_label = top_label

        overlay = np.full(frame.shape, current_color, dtype=np.uint8)
        alpha = 0.25  # Transparency
        blended = cv2.addWeighted(frame, 1 - alpha, overlay, alpha, 0)

        # ========================
        # 8. Display text info
        # ========================
        text = f"{top_label} ({confidence:.1f}%)"
        cv2.putText(blended, text, (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
        cv2.putText(blended, f"FPS: {fps:.1f}", (20, 80),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (230, 230, 230), 2)
        cv2.putText(blended, "Press 'q' to quit", (20, 460),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)

        # ========================
        # 9. Show the frame
        # ========================
        cv2.imshow("AI Emotion Spectrum", blended)

        # ========================
        # 10. Exit condition
# ========================
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("Exiting.")
            break

cap.release()
cv2.destroyAllWindows()
