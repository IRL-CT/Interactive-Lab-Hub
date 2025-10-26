from teachable_machine_lite import TeachableMachineLite
import cv2 as cv

# Initialize camera
cap = cv.VideoCapture(0)

# Paths to your model and labels
model_path = 'model.tflite'
labels_path = 'labels.txt'
image_file_name = "frame.jpg"

# Load Teachable Machine model
tm_model = TeachableMachineLite(model_path=model_path, labels_file_path=labels_path)

print("Model loaded. Starting camera...")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Save current frame for classification
    cv.imwrite(image_file_name, frame)

    # Get model predictions
    results = tm_model.classify_image(image_file_name)
    print("results:", results)

    # Extract the predicted label and confidence from the dictionary
    label = results.get("label", "").lower()
    confidence = results.get("confidence", 0)

    # Check if the prediction indicates a line for coffee
    if "line for coffee" in label:
        cv.putText(frame, "There's a line for coffee!", (50, 100),
                   cv.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3, cv.LINE_AA)

        # Optionally display confidence
        cv.putText(frame, f"{confidence:.2f}% sure", (50, 150),
                   cv.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv.LINE_AA)

    # Show camera feed
    cv.imshow('Cam', frame)

    # Press ESC to exit
    k = cv.waitKey(1)
    if k % 255 == 27:
        break

# Clean up
cap.release()
cv.destroyAllWindows()
