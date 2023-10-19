from teachable_machine_lite import TeachableMachineLite
import cv2 as cv

cap = cv.VideoCapture(0)

model_path = 'model.tflite'
image_file_name = "frame.jpg"
labels_path = "labels.txt"

tm_model = TeachableMachineLite(model_path=model_path, labels_file_path=labels_path)

while True:
    ret, frame = cap.read()
    cv.imshow('Cam', frame)
    cv.imwrite(image_file_name, frame)
    
    results = tm_model.classify_frame(image_file_name)
    print("results:",results)
    
    k = cv.waitKey(1)
    if k% 255 == 27:
        # press ESC to close camera view.
        break