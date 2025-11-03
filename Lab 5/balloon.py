import cv2
import time
import numpy as np
import HandTrackingModule as htm
import random

################################
wCam, hCam = 640, 480
################################

class Balloon:
    def __init__(self, x, y, color, radius=30):
        self.x = x
        self.y = y
        self.color = color
        self.radius = radius
        self.speed = random.uniform(0.5, 1.5)
        self.popped = False
        self.pop_timer = 0
    
    def update(self):
        """Move balloon upward"""
        if not self.popped:
            self.y -= self.speed
            # Reset balloon if it goes off screen
            if self.y < -self.radius:
                self.reset()
        else:
            # Handle pop animation timer
            self.pop_timer -= 1
            if self.pop_timer <= 0:
                self.reset()
    
    def reset(self):
        """Reset balloon to bottom of screen"""
        self.x = random.randint(self.radius + 50, wCam - self.radius - 50)
        self.y = hCam + random.randint(0, 100)  # Stagger starting positions
        self.speed = random.uniform(0.5, 1.5)
        self.popped = False
        self.pop_timer = 0
    
    def draw(self, img):
        """Draw balloon on image"""
        if not self.popped:
            # Draw balloon body
            cv2.circle(img, (int(self.x), int(self.y)), self.radius, self.color, -1)
            # Draw balloon shine
            cv2.circle(img, (int(self.x - 10), int(self.y - 10)), 8, (255, 255, 255), -1)
            # Draw balloon string
            string_end_y = min(int(self.y + self.radius + 40), hCam)
            cv2.line(img, (int(self.x), int(self.y + self.radius)), 
                    (int(self.x), string_end_y), (100, 100, 100), 2)
        elif self.pop_timer > 0:
            # Draw pop explosion effect
            cv2.circle(img, (int(self.x), int(self.y)), self.radius + (30 - self.pop_timer), 
                      self.color, 2)
            cv2.putText(img, "POP!", (int(self.x - 30), int(self.y)), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, self.color, 2)
    
    def check_collision(self, finger_x, finger_y):
        """Check if finger touches balloon"""
        if not self.popped:
            distance = np.sqrt((self.x - finger_x)**2 + (self.y - finger_y)**2)
            if distance < self.radius + 20:  # 20 is finger detection radius
                return True
        return False
    
    def pop(self):
        """Pop the balloon"""
        if not self.popped:  # Only pop once
            self.popped = True
            self.pop_timer = 30  # Show pop effect for 30 frames

# Initialize
print("Initializing camera...")
cap = cv2.VideoCapture(0)
cap.set(3, wCam)
cap.set(4, hCam)

if not cap.isOpened():
    print("ERROR: Could not open camera")
    exit()

print("Camera opened successfully!")
pTime = 0

print("Initializing hand detector...")
detector = htm.handDetector()
print("Hand detector ready!")

# Create balloons with better spacing
colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)]
balloons = []
num_balloons = 5

print("Creating balloons...")
for i in range(num_balloons):
    x = random.randint(80, wCam - 80)
    y = hCam + i * 100  # Space them out vertically
    color = colors[i % len(colors)]
    balloons.append(Balloon(x, y, color, radius=35))
    print(f"Balloon {i+1} created at ({x}, {y})")

score = 0
last_pop_time = 0
game_active = True

print("\nBalloon Popping Game!")
print("Point your index finger at balloons to pop them!")
print("Press 'q' to quit, 'r' to restart")
print("\nStarting game loop...")

frame_count = 0

while True:
    success, img = cap.read()
    if not success:
        print("Failed to read frame")
        continue
    
    frame_count += 1
    if frame_count % 100 == 0:
        print(f"Processed {frame_count} frames, Score: {score}")
        
    img = cv2.flip(img, 1)  # Mirror image for natural interaction
    
    # Find hands
    img = detector.findHands(img, draw=False)  # Don't draw hand landmarks
    lmList = detector.findPosition(img, draw=False)
    
    # Update and draw all balloons FIRST
    for balloon in balloons:
        balloon.update()
        balloon.draw(img)
    
    # Then check for collisions
    if len(lmList) != 0 and game_active:
        # Get index finger tip position (landmark 8)
        pointerX, pointerY = lmList[8][1], lmList[8][2]
        
        # Draw finger pointer clearly
        cv2.circle(img, (pointerX, pointerY), 20, (0, 255, 0), 3)
        cv2.circle(img, (pointerX, pointerY), 5, (255, 255, 255), -1)
        
        # Check collision with each balloon (with cooldown to prevent multiple pops)
        current_time = time.time()
        if current_time - last_pop_time > 0.3:  # 300ms cooldown between pops
            for balloon in balloons:
                if balloon.check_collision(pointerX, pointerY):
                    balloon.pop()
                    score += 1
                    last_pop_time = current_time
                    print(f"Pop! Score: {score}")
                    break  # Only pop one balloon at a time
    
    # Draw UI overlay
    # Score box
    cv2.rectangle(img, (10, 10), (220, 80), (0, 0, 0), -1)
    cv2.rectangle(img, (10, 10), (220, 80), (255, 255, 255), 2)
    cv2.putText(img, f'Score: {score}', (20, 55), cv2.FONT_HERSHEY_SIMPLEX,
                1.2, (0, 255, 0), 3)
    
    # Instructions
    cv2.putText(img, 'Point to pop!', (wCam - 200, 30), cv2.FONT_HERSHEY_SIMPLEX,
                0.6, (255, 255, 255), 2)
    
    # Calculate and display FPS
    cTime = time.time()
    fps = 1 / (cTime - pTime) if (cTime - pTime) > 0 else 0
    pTime = cTime
    cv2.putText(img, f'FPS: {int(fps)}', (20, hCam - 20), cv2.FONT_HERSHEY_SIMPLEX,
                0.6, (200, 200, 200), 2)
    
    # Show game window
    cv2.imshow("Balloon Pop Game", img)
    
    # Handle keyboard input
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):  # Quit
        print("\nQuitting game...")
        break
    elif key == ord('r'):  # Restart
        score = 0
        for i, balloon in enumerate(balloons):
            balloon.y = hCam + i * 100
            balloon.popped = False
            balloon.pop_timer = 0
        print("Game restarted!")

print("Cleaning up...")
cap.release()
cv2.destroyAllWindows()
print("Done!")