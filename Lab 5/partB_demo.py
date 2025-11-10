#!/usr/bin/env python3
# Minimal: show label text (small) + colored ring; parse {'label': '2 drink', 'confidence': 87.66}

from teachable_machine_lite import TeachableMachineLite
import cv2 as cv

cap = cv.VideoCapture(0)   # 没画面可改 1
model_path = 'model.tflite'
labels_path = 'labels.txt'
image_file_name = 'frame.jpg'

tm = TeachableMachineLite(model_path=model_path, labels_file_path=labels_path)
print("Model loaded. Press ESC to quit.")

# 环颜色（BGR）
COLOR_MAP = {
    "typing":  (0, 255, 0),     # 绿
    "writing": (0, 255, 0),     # 绿
    "phone":   (0, 165, 255),   # 橙
    "drink":   (255, 200, 0),   # 浅蓝
    "idle":    (180, 180, 180), # 灰
}
DEFAULT_COLOR = (128, 128, 128)

def parse_label_conf(res: dict):
    """
    示例：
    {'id': 2, 'label': '2 drink', 'time': None, 'confidence': 87.66, 'highest_class_id': 2, 'highest_class_prob': 87.66}
    """
    raw = str(res.get("label", "")).strip()
    parts = raw.split(maxsplit=1)
    cls = (parts[1] if len(parts) > 1 else parts[0]).strip().lower()  # '2 drink' -> 'drink'
    conf_pct = res.get("confidence", res.get("highest_class_prob", 0.0))
    try:
        conf_pct = float(conf_pct)
    except Exception:
        conf_pct = 0.0
    return cls, conf_pct, raw  # 同时返回原始字符串便于调试

while True:
    ok, frame = cap.read()
    if not ok:
        break

    # 分类
    cv.imwrite(image_file_name, frame)
    res = tm.classify_image(image_file_name)
    label_norm, conf_pct, label_raw = parse_label_conf(res)

    # —— 叠加当前分类到画面（小字号）——
    # 第一行：标准化标签 + 置信度
    text1 = f"{label_norm}  {int(conf_pct)}%"
    cv.putText(frame, text1, (14, 30), cv.FONT_HERSHEY_SIMPLEX, 0.6, (230, 230, 230), 1)
    # 第二行：原始返回（可注释掉）
    text2 = f"raw: {label_raw}"
    cv.putText(frame, text2, (14, 52), cv.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1)

    # 彩色圆环（中心）
    h, w = frame.shape[:2]
    color = COLOR_MAP.get(label_norm, DEFAULT_COLOR)
    radius = max(40, min(w, h)//5)
    cv.circle(frame, (w//2, h//2), radius, color, 8, lineType=cv.LINE_AA)

    # 显示
    cv.imshow("Cam", frame)

    # 同时在终端打印一行
    print("results:", res)

    # ESC 退出
    if (cv.waitKey(1) & 0xFF) == 27:
        break

cap.release()
cv.destroyAllWindows()
