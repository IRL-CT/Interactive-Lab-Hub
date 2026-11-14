"""Dog-only inference and conservative state filtering. No hardware imports at import time."""
from pathlib import Path

PRESENT = 'dog_detected_in_area'
ABSENT = 'dog_not_detected_in_area'
UNKNOWN = 'unknown'


class ConfirmationFilter:
    def __init__(self, threshold=3):
        if threshold < 1:
            raise ValueError('threshold must be positive')
        self.threshold = threshold
        self.state = self.candidate = UNKNOWN
        self.count = 0

    def update(self, raw):
        if raw not in (PRESENT, ABSENT):
            self.state = self.candidate = UNKNOWN
            self.count = 0
            return self.state
        self.count = self.count + 1 if raw == self.candidate else 1
        self.candidate = raw
        if self.count >= self.threshold:
            self.state = raw
        return self.state


def overlap_fraction(box, roi):
    """Intersection area / dog box area, all coordinates normalized to the image."""
    x1, y1, x2, y2 = box
    area = max(0, x2-x1) * max(0, y2-y1)
    intersection = max(0, min(x2, roi[2])-max(x1, roi[0])) * max(0, min(y2, roi[3])-max(y1, roi[1]))
    return intersection / area if area else 0.0


class DogDetector:
    def __init__(self, config):
        import cv2
        from ultralytics import YOLO
        self.cv2, self.config = cv2, config
        if not Path(config['model']).is_dir():
            raise FileNotFoundError('NCNN model directory missing: ' + config['model'])
        self.model = YOLO(config['model'], task='detect')

    def sample(self):
        # Reopen each sample: no frames buffered during the ten-second pause.
        cv2, cfg = self.cv2, self.config
        cap = cv2.VideoCapture(cfg['camera'])
        try:
            if not cap.isOpened():
                raise RuntimeError('Cannot open webcam')
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            for _ in range(4):
                if not cap.grab():
                    raise RuntimeError('Camera warm-up failed')
            ok, frame = cap.read()
            if not ok or frame is None:
                raise RuntimeError('Camera frame unavailable')
        finally:
            cap.release()
        from datetime import datetime
        captured_at = datetime.now().astimezone().isoformat(timespec='milliseconds')
        result = self.model.predict(frame, imgsz=320, conf=cfg['conf'], classes=[16], verbose=False)[0]
        h, w = frame.shape[:2]
        dogs = []
        for box in result.boxes:
            if int(box.cls.item()) != 16:
                continue
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            normalized = [x1/w, y1/h, x2/w, y2/h]
            overlap = overlap_fraction(normalized, cfg['roi'])
            dogs.append({'box': normalized, 'confidence': float(box.conf.item()),
                         'roi_overlap': overlap, 'in_roi': overlap >= cfg['overlap']})
        inside = [d for d in dogs if d['in_roi']]
        return {'raw': PRESENT if inside else ABSENT, 'in_roi': bool(inside),
                'confidence': max((d['confidence'] for d in inside), default=None),
                'dogs': dogs, 'captured_at': captured_at}


def detector_worker(connection, config):
    """Isolate native camera/inference calls so a hang cannot block the buttons."""
    try:
        detector = DogDetector(config)
        connection.send({'ready': True})
        while connection.recv() == 'sample':
            try:
                connection.send(detector.sample())
            except Exception as error:
                connection.send({'raw': UNKNOWN, 'in_roi': None, 'confidence': None,
                                 'error': str(error)})
    except (EOFError, BrokenPipeError):
        pass
    except Exception as error:
        connection.send({'fatal': str(error)})
    finally:
        connection.close()
