"""
AI Emotion Spectrum
Real-time camera + object recognition + artistic color glow
(Special version with dynamic brightness + particle effects)
"""

import cv2
import torch
import json
import time
import numpy as np
from torchvision import models, transforms
from PIL import Image
from playsound import playsound
import threading

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
# 5. Define artistic colors & sounds
# ========================
object_colors = {
    "coffee mug": (255, 170, 100),   # Warm orange – cozy
    "projector": (150, 200, 255),    # Cool blue – digital calm
    "iPod": (230, 160, 255),         # Dreamy purple – creative
    "mouse, computer mouse": (190, 255, 150),  # Focus green
    "modem": (190, 255, 150),
    "default": (230, 230, 230)
}

object_sounds = {
    "coffee mug": "sounds/warm.mp3",
    "projector": "sounds/digital.mp3",
    "iPod": "sounds/beat.mp3",
    "mouse, computer mouse": "sounds/click.mp3"
}

# ========================
# 6. Helper functions
# ========================
def smooth_color_transition(current, target, rate=0.1):
    return tuple([
        int(current[i] + (target[i] - current[i]) * rate)
        for i in range(3)
    ])

def play_sound(sound_path):
    threading.Thread(target=playsound, args=(sound_path,), daemon=True).start()

# ========================
# 7. Main loop
# ========================
last_logged = time.time()
frame_count = 0
last_label = None
current_color = object_colors["default"]
target_color = object_colors["default"]

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
        # 8. Update color & sound when object changes
        # ========================
        if top_label != last_label:
            target_color = object_colors.get(top_label, object_colors["default"])
            print(f"Object changed to: {top_label}")
            last_label = top_label

            if top_label in object_sounds:
                play_sound(object_sounds[top_label])

        # Smooth transition to target color
        current_color = smooth_color_transition(current_color, target_color, rate=0.15)

        # ========================
        # 9. Artistic filter with breathing light + particles
        # ========================
        # Base overlay
        overlay = np.full(frame.shape, current_color, dtype=np.uint8)
        glow = cv2.GaussianBlur(overlay, (41, 41), 0)

        # Dynamic brightness ("breathing" effect)
        breath = (np.sin(time.time() * 2) + 1) / 2  # oscillates 0–1
        brightness_factor = 0.7 + 0.3 * breath
        glow = np.clip(glow * brightness_factor, 0, 255).astype(np.uint8)

        # Vivid saturation
        hsv = cv2.cvtColor(glow, cv2.COLOR_BGR2HSV)
        hsv[:, :, 1] = np.clip(hsv[:, :, 1] * 1.8, 0, 255)
        vivid_glow = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

        # Blend with frame
        alpha = 0.65
        blended = cv2.addWeighted(frame, 1 - alpha, vivid_glow, alpha, 0)

        # Add sparkle particles ✨
        sparkle = np.zeros_like(frame)
        for _ in range(20):
            x, y = np.random.randint(0, frame.shape[1]), np.random.randint(0, frame.shape[0])
            size = np.random.randint(2, 6)
            intensity = np.random.randint(180, 255)
            cv2.circle(sparkle, (x, y), size, (intensity, intensity, intensity), -1)
        sparkle = cv2.GaussianBlur(sparkle, (9, 9), 0)
        blended = cv2.addWeighted(blended, 0.9, sparkle, 0.2, 0)

        # ========================
        # 10. Display text info
        # ========================
        text = f"{top_label} ({confidence:.1f}%)"
        cv2.putText(blended, text, (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
        cv2.putText(blended, f"FPS: {fps:.1f}", (20, 80),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (230, 230, 230), 2)
        cv2.putText(blended, "Press 'q' to quit", (20, 460),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)

        # ========================
        # 11. Show the frame
        # ========================
        cv2.imshow("AI Emotion Spectrum", blended)

        # ========================
        # 12. Exit condition
        # ========================
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("Exiting.")
            break

cap.release()
cv2.destroyAllWindows()
