from teachable_machine_lite import TeachableMachineLite
import cv2 as cv

# Initialize camera
cap = cv.VideoCapture(0)

# Paths to your model and labels
model_path = 'model.tflite'
labels_path = 'labels.txt'
image_file_name = "baseframe.png"

# Load Teachable Machine model
tm_model = TeachableMachineLite(model_path=model_path, labels_file_path=labels_path)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Save current frame for classification
    cv.imwrite(image_file_name, frame)

    # Get model predictions
    results = tm_model.classify_image(image_file_name)
    print("results:", results)

    # Extract top prediction
    if results:
        label, confidence = results[0]  # e.g. ('line for coffee', 0.95)

        # Check if the detected label indicates a coffee line
        if "line for coffee" in label.lower():
            cv.putText(frame, "There's a line for coffee!", (50, 100),
                       cv.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3, cv.LINE_AA)

    # Display camera feed
    cv.imshow('Cam', frame)

    # Press ESC to exit
    k = cv.waitKey(1)
    if k % 255 == 27:
        break

# Clean up
cap.release()
cv.destroyAllWindows()
