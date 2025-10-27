"""
AI 情绪光谱（Emotion Spectrum）
实时摄像头 + 物体识别 + 颜色滤镜艺术效果
"""

import cv2
import torch
import json
import time
import numpy as np
from torchvision import models, transforms
from PIL import Image

# ========================
# 1. 加载标签文件
# ========================
with open('classes.json') as f:
    classes = json.load(f)

# ========================
# 2. 初始化模型
# ========================
torch.backends.quantized.engine = 'qnnpack'
model = models.quantization.mobilenet_v2(pretrained=True, quantize=True)
model.eval()
model = torch.jit.script(model)

# ========================
# 3. 摄像头设置
# ========================
cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv2.CAP_PROP_FPS, 24)

# ========================
# 4. 预处理定义
# ========================
preprocess = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225])
])

# ========================
# 5. 滤镜映射（AI情绪色彩）
# ========================
colors = [
    (255, 120, 120),  # 红：激情 / 强烈
    (255, 200, 100),  # 橙：活力 / 创造
    (255, 255, 150),  # 黄：愉悦 / 乐观
    (150, 255, 150),  # 绿：平静 / 平衡
    (150, 200, 255),  # 蓝：宁静 / 冷静
    (200, 150, 255)   # 紫：神秘 / 梦幻
]

# ========================
# 6. 主循环
# ========================
last_logged = time.time()
frame_count = 0

with torch.no_grad():
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Can not read the scene")
            break

        # BGR → RGB (for PIL)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb)

        # 预处理
        input_tensor = preprocess(pil_img)
        input_batch = input_tensor.unsqueeze(0)

        # 模型推理
        output = model(input_batch)
        probs = torch.nn.functional.softmax(output[0], dim=0)
        top_prob, top_idx = torch.topk(probs, 1)
        top_label = classes[str(top_idx.item())]
        confidence = top_prob.item() * 100

        # FPS计算
        frame_count += 1
        now = time.time()
        fps = frame_count / (now - last_logged) if now - last_logged > 0 else 0
        if now - last_logged > 1:
            last_logged = now
            frame_count = 0

        # ========================
        # 7. 应用滤镜（根据置信度映射颜色）
        # ========================
        color_idx = int((confidence / 100) * (len(colors) - 1))
        color = colors[color_idx]
        overlay = np.full(frame.shape, color, dtype=np.uint8)
        alpha = 0.25  # 滤镜透明度
        blended = cv2.addWeighted(frame, 1 - alpha, overlay, alpha, 0)

        # ========================
        # 8. 显示结果文字
        # ========================
        text = f"{top_label} ({confidence:.1f}%)"
        cv2.putText(blended, text, (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
        cv2.putText(blended, f"FPS: {fps:.1f}", (20, 80),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (230, 230, 230), 2)
        cv2.putText(blended, "Press 'q' to quit", (20, 460),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)

        # ========================
        # 9. 展示画面
        # ========================
        cv2.imshow("AI Emotion Spectrum", blended)

        # ========================
        # 10. 退出条件
        # ========================
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("exit")
            break

cap.release()
cv2.destroyAllWindows()

