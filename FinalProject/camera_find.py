import cv2

print("Testing video devices 0 through 40...")
for index in range(40):
    cap = cv2.VideoCapture(index, cv2.CAP_V4L2)
    if cap.isOpened():
        ret, frame = cap.read()
        if ret:
            print(f"Working camera found at index {index}")
        else:
            print(f"Camera opened but no frames at index {index}")
        cap.release()
