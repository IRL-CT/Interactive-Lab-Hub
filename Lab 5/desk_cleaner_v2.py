from teachable_machine_lite import TeachableMachineLite
import cv2 as cv
import time

# === Setup paths ===
model_path = "v2_model.tflite"
labels_path = "v2_labels.txt"
image_file_name = "frame.jpg"

# === Initialize model ===
tm_model = TeachableMachineLite(model_path=model_path, labels_file_path=labels_path)

# === Start webcam ===
cap = cv.VideoCapture(0)

if not cap.isOpened():
    print("Cannot open camera")
    exit()

print("Camera opened. Press ESC to exit.")

# === Real-time loop ===
while True:
    ret, frame = cap.read()
    if not ret:
        print("Can't receive frame (stream end?). Exiting ...")
        break

    # Save a temporary frame for classification
    cv.imwrite(image_file_name, frame)

    # Run inference
    results = tm_model.classify_image(image_file_name)

    # Extract info safely
    label = results.get("label", "Unknown")
    confidence = results.get("confidence", 0.0)

    # Display label and confidence on screen
    text = f"{label} ({confidence:.2f}%)"
    cv.putText(frame, text, (20, 40),
               cv.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv.LINE_AA)

    # Print to terminal
    print(f"Prediction: {label} ({confidence:.2f}%)")

    # Show webcam window
    cv.imshow("Teachable Machine Cam", frame)

    # Press ESC (27) to exit
    k = cv.waitKey(1)
    if k % 255 == 27:
        print("ESC pressed, exiting.")
        break


