import cv2
import time
import numpy as np
import HandTrackingModule as htm
import random

################################
wCam, hCam = 640, 480
################################

class Balloon:
    def __init__(self, x, y, balloon_type):
        self.x = x
        self.y = y
        self.balloon_type = balloon_type
        self.popped = False
        self.pop_timer = 0
        
        # Set properties based on balloon type
        if balloon_type == "red":
            self.color = (0, 0, 255)  # Red in BGR
            self.points = 1
            self.speed = random.uniform(1.0, 2.0)
            self.radius = 35
        elif balloon_type == "blue":
            self.color = (255, 0, 0)  # Blue in BGR
            self.points = 5
            self.speed = random.uniform(3.5, 5.0)  # Much faster
            self.radius = 30
        elif balloon_type == "purple":
            self.color = (255, 0, 255)  # Purple in BGR
            self.points = 10
            self.speed = random.uniform(1.5, 2.5)
            self.radius = 40
        elif balloon_type == "black":
            self.color = (0, 0, 0)  # Black in BGR
            self.points = -5
            self.speed = random.uniform(2.0, 3.0)
            self.radius = 35
    
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
        """Reset balloon to bottom of screen with random type"""
        self.x = random.randint(self.radius + 50, wCam - self.radius - 50)
        self.y = hCam + random.randint(0, 200)
        self.popped = False
        self.pop_timer = 0
        
        # Randomly assign new type with weighted probabilities
        rand = random.random()
        if rand < 0.60:  # 60% chance - red (common)
            self.balloon_type = "red"
            self.color = (0, 0, 255)
            self.points = 1
            self.speed = random.uniform(1.0, 2.0)
            self.radius = 25
        elif rand < 0.80:  # 20% chance - blue (uncommon, fast)
            self.balloon_type = "blue"
            self.color = (255, 0, 0)
            self.points = 5
            self.speed = random.uniform(5, 6.0)
            self.radius = 10
        elif rand < 0.90:  # 7% chance - purple (rare)
            self.balloon_type = "purple"
            self.color = (255, 0, 255)
            self.points = 10
            self.speed = random.uniform(1.5, 2.5)
            self.radius = 20
        else:  # 10% chance - black (penalty)
            self.balloon_type = "black"
            self.color = (0, 0, 0)
            self.points = -15
            self.speed = random.uniform(2.0, 3.0)
            self.radius = 35
    
    def draw(self, img):
        """Draw balloon on image"""
        if not self.popped:
            # Draw balloon body
            cv2.circle(img, (int(self.x), int(self.y)), self.radius, self.color, -1)
            
            # Draw X on black balloons
            if self.balloon_type == "black":
                x_size = 20
                cv2.line(img, 
                        (int(self.x - x_size), int(self.y - x_size)),
                        (int(self.x + x_size), int(self.y + x_size)),
                        (255, 255, 255), 4)
                cv2.line(img, 
                        (int(self.x + x_size), int(self.y - x_size)),
                        (int(self.x - x_size), int(self.y + x_size)),
                        (255, 255, 255), 4)
            else:
                # Draw balloon shine (not for black balloons)
                cv2.circle(img, (int(self.x - 10), int(self.y - 10)), 8, (255, 255, 255), -1)
            
            # Draw balloon string
            string_end_y = min(int(self.y + self.radius + 40), hCam)
            cv2.line(img, (int(self.x), int(self.y + self.radius)), 
                    (int(self.x), string_end_y), (100, 100, 100), 2)
            
            # Draw point value on balloon
            point_text = f"+{self.points}" if self.points > 0 else str(self.points)
            cv2.putText(img, point_text, (int(self.x - 15), int(self.y + 5)), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
            
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
            if distance < self.radius + 20:
                return True
        return False
    
    def pop(self):
        """Pop the balloon"""
        if not self.popped:
            self.popped = True
            self.pop_timer = 30

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

# Create initial balloons with weighted distribution
balloon_types = ["red", "red", "red", "red", "red", "red", "blue", "blue", "purple", "black"]
balloons = []
num_balloons = 8  # More balloons for better gameplay

print("Creating balloons...")
for i in range(num_balloons):
    x = random.randint(80, wCam - 80)
    y = hCam + i * 100
    balloon_type = random.choice(balloon_types)
    balloons.append(Balloon(x, y, balloon_type))
    print(f"Balloon {i+1} created: {balloon_type}")

score = 0
last_pop_time = 0
game_active = True
game_over = False

print("\nBalloon Popping Game!")
print("Red balloons = 1 point")
print("Blue balloons = 5 points (fast!)")
print("Purple balloons = 10 points (rare!)")
print("Black balloons = -5 points (avoid!)")
print("Game over at 0 points!")
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
        
    img = cv2.flip(img, 1)
    
    if not game_over:
        # Find hands
        img = detector.findHands(img, draw=False)
        lmList = detector.findPosition(img, draw=False)
        
        # Update and draw all balloons
        for balloon in balloons:
            balloon.update()
            balloon.draw(img)
        
        # Check for collisions
        if len(lmList) != 0 and game_active:
            pointerX, pointerY = lmList[8][1], lmList[8][2]
            
            # Draw finger pointer
            cv2.circle(img, (pointerX, pointerY), 20, (0, 255, 0), 3)
            cv2.circle(img, (pointerX, pointerY), 5, (255, 255, 255), -1)
            
            # Check collision with cooldown
            current_time = time.time()
            if current_time - last_pop_time > 0.3:
                for balloon in balloons:
                    if balloon.check_collision(pointerX, pointerY):
                        balloon.pop()
                        score += balloon.points
                        last_pop_time = current_time
                        
                        # Check for game over
                        if score <= 0:
                            score = 0
                            game_over = True
                            print("GAME OVER!")
                        else:
                            print(f"Pop! Points: {balloon.points:+d}, Score: {score}")
                        break
        
        # Draw score box
        cv2.rectangle(img, (10, 10), (220, 80), (0, 0, 0), -1)
        cv2.rectangle(img, (10, 10), (220, 80), (255, 255, 255), 2)
        cv2.putText(img, f'Score: {score}', (20, 55), cv2.FONT_HERSHEY_SIMPLEX,
                    1.2, (0, 255, 0), 3)
        
        # Instructions
        cv2.putText(img, 'Point to pop!', (wCam - 200, 30), cv2.FONT_HERSHEY_SIMPLEX,
                    0.6, (255, 255, 255), 2)
    
    else:
        # Game Over screen
        # Draw semi-transparent overlay
        overlay = img.copy()
        cv2.rectangle(overlay, (0, 0), (wCam, hCam), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, img, 0.3, 0, img)
        
        # Draw GAME OVER text
        cv2.putText(img, 'GAME OVER!', (wCam//2 - 180, hCam//2 - 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 5)
        cv2.putText(img, f'Final Score: {score}', (wCam//2 - 150, hCam//2 + 20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 3)
        cv2.putText(img, "Press 'R' to restart", (wCam//2 - 150, hCam//2 + 70), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        cv2.putText(img, "Press 'Q' to quit", (wCam//2 - 130, hCam//2 + 110), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    
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
    if key == ord('q'):
        print("\nQuitting game...")
        break
    elif key == ord('r'):
        score = 5  # Start with 5 points to give a buffer
        game_over = False
        for i, balloon in enumerate(balloons):
            balloon.y = hCam + i * 100
            balloon.reset()
        print("Game restarted! Starting score: 5")

print("Cleaning up...")
cap.release()
cv2.destroyAllWindows()
print("Done!")