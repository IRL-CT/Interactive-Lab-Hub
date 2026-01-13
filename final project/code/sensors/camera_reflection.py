import cv2

class CameraFeed:
    def __init__(self, cam_index=0):
        self.cap = cv2.VideoCapture(cam_index)

        if not self.cap.isOpened():
            print(f"[Camera] Failed to open camera at index {cam_index}. Running without camera.")
            self.cap = None
            return

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        print("[Camera] Camera initialized successfully.")

    def get_frame(self):
        if self.cap is None:
            return None

        ret, frame = self.cap.read()
        if not ret or frame is None:
            return None

        frame = cv2.flip(frame, 1)
        return frame

    def release(self):
        if self.cap is not None:
            self.cap.release()
