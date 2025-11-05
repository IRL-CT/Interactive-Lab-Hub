import pickle

import cv2
import mediapipe as mp
import numpy as np
import time

model_dict = pickle.load(open('./model.p', 'rb'))
model = model_dict['model']

window_name = "frame"
cv2.namedWindow(window_name)

# Run the camera and detect signs
# return the predicted sign for detected hand
def camera(duration=5):
    letter_counts = {}
    start_time = time.time()
    last_letter = None
    stable_start = None

    print(f"Show a sign to the camera... (recording for {duration}s)")

    cap = cv2.VideoCapture(0)

    mp_hands = mp.solutions.hands
    mp_drawing = mp.solutions.drawing_utils
    mp_drawing_styles = mp.solutions.drawing_styles

    hands = mp_hands.Hands(static_image_mode=True, min_detection_confidence=0.3)
    while True:

        data_aux = []
        x_ = []
        y_ = []

        ret, frame = cap.read()
        if not ret:
            continue
        H, W, _ = frame.shape

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        letter = None
        results = hands.process(frame_rgb)
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp_drawing.draw_landmarks(
                    frame,  # image to draw
                    hand_landmarks,  # model output
                    mp_hands.HAND_CONNECTIONS,  # hand connections
                    mp_drawing_styles.get_default_hand_landmarks_style(),
                    mp_drawing_styles.get_default_hand_connections_style())

            for hand_landmarks in results.multi_hand_landmarks:
                for i in range(len(hand_landmarks.landmark)):
                    x = hand_landmarks.landmark[i].x
                    y = hand_landmarks.landmark[i].y

                    x_.append(x)
                    y_.append(y)

                for i in range(len(hand_landmarks.landmark)):
                    x = hand_landmarks.landmark[i].x
                    y = hand_landmarks.landmark[i].y
                    data_aux.append(x - min(x_))
                    data_aux.append(y - min(y_))

            x1 = int(min(x_) * W) - 10
            y1 = int(min(y_) * H) - 10

            x2 = int(max(x_) * W) - 10
            y2 = int(max(y_) * H) - 10

            prediction = model.predict([np.asarray(data_aux)[:42]])
            letter = str(prediction[0])

            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 0), 4)
            cv2.putText(frame,letter, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 1.3, (0, 0, 0), 3,
                        cv2.LINE_AA)

        #print(letter)
        if letter and letter == last_letter:
            # continuing the same sign
            if stable_start is None:
                stable_start = time.time()
            elapsed = time.time() - stable_start
            if elapsed >= 0.3:  # consider stable for 0.3s
                letter_counts[letter] = letter_counts.get(letter, 0) + 1
        else:
            stable_start = None
        
        #print(letter_counts)
        last_letter = letter
        cv2.imshow('frame', frame)

        # Time or key exit
        if (time.time() - start_time) > duration:
            break
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break


    cap.release()

    if not letter_counts:
        return None

    # return the letter shown most consistently
    best_letter = max(letter_counts, key=letter_counts.get)
    #print(f"Detected letter: {best_letter}")
    return best_letter


if __name__ == "__main__":
    while True:
      camera()
