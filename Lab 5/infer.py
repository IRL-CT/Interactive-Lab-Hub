import cv2
from ultralytics import YOLO
import random

# Load YOLOv8 model (make sure model file is in your directory)
model = YOLO("yolov8n.pt")

# Open webcam (0 = default camera)
cap = cv2.VideoCapture(0)

# Initialize variables
prev_class = None
current_color = (0, 255, 0)  # Default color: green

def random_color():
    """Generate a random RGB color"""
    return (random.randint(50, 255), random.randint(50, 255), random.randint(50, 255))

while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to grab frame")
        break

    # Run YOLO detection
    results = model(frame, stream=True)

    # Process detection results
    for r in results:
        for box in r.boxes:
            cls = int(box.cls[0])  # class ID
            conf = float(box.conf[0])  # confidence
            label = model.names[cls]  # class name

            # Change color only when the detected class changes
            if cls != prev_class:
                current_color = random_color()
                print(f"Class changed to: {label}")
                prev_class = cls

            # Get bounding box coordinates
            x1, y1, x2, y2 = map(int, box.xyxy[0])

            # Draw bounding box and label
            cv2.rectangle(frame, (x1, y1), (x2, y2), current_color, 3)
            cv2.putText(frame, f"{label} {conf:.2f}",
                        (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX,
                        0.8, current_color, 2)

    # Display the frame
    cv2.imshow("YOLO Object Detection", frame)

    # Press 'q' to quit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release resources
cap.release()
cv2.destroyAllWindows()
