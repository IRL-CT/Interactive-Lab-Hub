"""
Simple camera test script to verify webcam is working
"""

import cv2

# Open camera (0 is the first camera device)
cap = cv2.VideoCapture(0)

# Check if camera opened successfully
if not cap.isOpened():
    print("Error: Cannot open camera")
    exit()

print("Camera opened successfully")
print("Press 'q' to quit")

# Create window
cv2.namedWindow('Camera Test', cv2.WINDOW_NORMAL)

while True:
    # Read frame
    ret, frame = cap.read()
    
    # Check if frame was read successfully
    if not ret:
        print("Error: Cannot read frame")
        break
    
    # Add text to frame
    cv2.putText(frame, "Camera Working! Press 'q' to quit", 
                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 
                0.7, (0, 255, 0), 2)
    
    # Display frame
    cv2.imshow('Camera Test', frame)
    
    # Press 'q' to exit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release resources
cap.release()
cv2.destroyAllWindows()
print("Camera closed")