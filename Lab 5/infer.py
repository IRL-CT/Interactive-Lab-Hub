"""
AI Emotion Spectrum + Sound Feedback + Particle Glow
Dynamic brightness and particle effects only for recognized objects
"""

import cv2
import torch
import json
import time
import numpy as np
import pygame
from torchvision import models, transforms
from PIL import Image
import random

# ========================
# 1. Load labels
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
# 3. Initialize sound
# ========================
pygame.mixer.init()
sound_files = {
    "coffee mug": "sounds/warm.mp3",
    "projector": "sounds/digital.mp3",
    "iPod": "sounds/beat.mp3",
    "mouse, computer mouse": "sounds/click.mp3"
}

def play_sound_for_object(label):
    if label in sound_files:
        try:
            pygame.mixer.music.load(sound_files[label])
            pygame.mixer.music.play()
        except Exception as e:
            print(f"Error playing sound for {label}: {e}")

# ========================
# 4. Camera
# ========================
cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv2.CAP_PROP_FPS, 24)

# ========================
# 5. Preprocessing
# ========================
preprocess = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225])
])

# ========================
# 6. Color map
# ========================
object_colors = {
    "coffee mug": (255, 170, 100),
    "projector": (150, 200, 255),
    "iPod": (230, 160, 255),
    "mouse, computer mouse": (190, 255, 150),
    "default": (230, 230, 230)
}

# ========================
# 7. Transition helper
# ========================
def smooth_color_transition(current, target, rate=0.1):
    return tuple([
        int(current[i] + (target[i] - current[i]) * rate)
        for i in range(3)
    ])

# ========================
# 8. Particle system
# ========================
class Particle:
    def __init__(self, width, height, color):
        self.x = random.randint(0, width)
        self.y = random.randint(0, height)
        self.size = random.randint(2, 6)
        self.color = color
        self.speed_x = random.uniform(-1, 1)
        self.speed_y = random.uniform(-2, -0.5)
        self.alpha = 255

    def update(self):
        self.x += self.speed_x
        self.y += self.speed_y
        self.alpha -= 3
        return self.alpha > 0

    def draw(self, frame):
        if 0 < self.alpha <= 255:
            overlay = frame.copy()
            cv2.circle(overlay, (int(self.x), int(self.y)), self.size, self.color, -1)
            cv2.addWeighted(overlay, self.alpha / 255.0, frame, 1 - self.alpha / 255.0, 0, frame)

# ========================
# 9. Main loop
# ========================
last_label = None
current_color = object_colors["default"]
target_color = object_colors["default"]
particles = []

last_logged = time.time()
frame_count = 0

with torch.no_grad():
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to read from camera.")
            break

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb)

        input_tensor = preprocess(pil_img)
        input_batch = input_tensor.unsqueeze(0)

        output = model(input_batch)
        probs = torch.nn.functional.softmax(output[0], dim=0)
        top_prob, top_idx = torch.topk(probs, 1)
        top_label = classes[str(top_idx.item())]
        confidence = top_prob.item() * 100

        frame_count += 1
        now = time.time()
        fps = frame_count / (now - last_logged) if now - last_logged > 0 else 0
        if now - last_logged > 1:
            last_logged = now
            frame_count = 0

        # Detect label change
        if top_label != last_label:
            target_color = object_colors.get(top_label, object_colors["default"])
            print(f"Object changed to: {top_label}")

            if top_label in sound_files:
                play_sound_for_object(top_label)

            last_label = top_label

        # Dynamic glow + brightness
        current_color = smooth_color_transition(current_color, target_color, rate=0.12)
        overlay = np.full(frame.shape, current_color, dtype=np.uint8)
        glow = cv2.GaussianBlur(overlay, (55, 55), 0)

        brightness_factor = 1.2 if top_label in sound_files else 0.9
        glow = cv2.convertScaleAbs(glow, alpha=brightness_factor, beta=20)

        blended = cv2.addWeighted(frame, 0.6, glow, 0.4, 0)

        # Add particle effect for recognized objects
        if top_label in sound_files:
            if random.random() < 0.3:  # control density
                particles.append(Particle(blended.shape[1], blended.shape[0], current_color))
            new_particles = []
            for p in particles:
                if p.update():
                    p.draw(blended)
                    new_particles.append(p)
            particles = new_particles
        else:
            particles.clear()

        cv2.putText(blended, f"{top_label} ({confidence:.1f}%)", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
        cv2.putText(blended, f"FPS: {fps:.1f}", (20, 80),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (230, 230, 230), 2)
        cv2.putText(blended, "Press 'q' to quit", (20, 460),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)

        cv2.imshow("AI Emotion Spectrum + Sound + Particles", blended)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("Exiting.")
            break

cap.release()
cv2.destroyAllWindows()
pygame.mixer.quit()
