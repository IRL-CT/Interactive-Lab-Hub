import pi_servo_hat
import time

# Servo configuration
SERVO_MIN = 0
SERVO_MAX = 120
SERVO_NEUTRAL = 60

# Servo channels
SERVO_MIDDLE = 0
SERVO_LEFT = 1
SERVO_RIGHT = 2

# Initialize servo hat
servo = pi_servo_hat.PiServoHat()
servo.restart()

# Placeholder RGB value ranges for color detection
# Modify these thresholds later based on your actual sensor readings
RED_MIN = [200, 0, 0]
RED_MAX = [255, 80, 80]

ORANGE_MIN = [200, 80, 0]
ORANGE_MAX = [255, 160, 80]

YELLOW_MIN = [180, 150, 0]
YELLOW_MAX = [255, 255, 80]

GREEN_MIN = [0, 150, 0]
GREEN_MAX = [120, 255, 120]

def is_color(rgb, color_min, color_max):
    """
    Check if RGB values fall within a color range.
    
    Args:
        rgb: List or tuple [r, g, b]
        color_min: List [r_min, g_min, b_min]
        color_max: List [r_max, g_max, b_max]
    
    Returns:
        bool: True if rgb is within range
    """
    r, g, b = rgb
    r_min, g_min, b_min = color_min
    r_max, g_max, b_max = color_max
    return (r_min <= r <= r_max and 
            g_min <= g <= g_max and 
            b_min <= b <= b_max)

def get_color(rgb):
    """
    Determine color category from RGB values.
    Returns: 'red', 'orange', 'yellow', 'green', or 'unknown'
    """
    if is_color(rgb, RED_MIN, RED_MAX):
        return 'red'
    elif is_color(rgb, ORANGE_MIN, ORANGE_MAX):
        return 'orange'
    elif is_color(rgb, YELLOW_MIN, YELLOW_MAX):
        return 'yellow'
    elif is_color(rgb, GREEN_MIN, GREEN_MAX):
        return 'green'
    else:
        return 'unknown'

def sort_by_color(rgb):
    """
    Rotate motors based on RGB color input.
    
    Middle motor acts as a funnel:
    - Rotates LEFT to send skittle down LEFT chute (red/orange)
    - Rotates RIGHT to send skittle down RIGHT chute (green/yellow)
    
    Only the motor on the selected chute runs afterwards.
    """
    color = get_color(rgb)
    print(f"Detected color: {color} (RGB: {rgb})")

    if color == 'red':
        # Send down LEFT chute, then sort with LEFT motor
        print("Middle motor: LEFT -> directing to left chute")
        servo.move_servo_position(SERVO_MIDDLE, SERVO_MAX)
        time.sleep(0.8)  # Give time for skittle to move onto left motor

        print("Left motor: LEFT -> sorting red")
        servo.move_servo_position(SERVO_LEFT, SERVO_MIN)
        time.sleep(0.8)

        # Return to neutral
        servo.move_servo_position(SERVO_LEFT, SERVO_NEUTRAL)
        servo.move_servo_position(SERVO_MIDDLE, SERVO_NEUTRAL)

    elif color == 'orange':
        # Send down LEFT chute, then sort with LEFT motor
        print("Middle motor: LEFT -> directing to left chute")
        servo.move_servo_position(SERVO_MIDDLE, SERVO_MAX)
        time.sleep(0.8)  # Give time for skittle to move onto left motor

        print("Left motor: RIGHT -> sorting orange")
        servo.move_servo_position(SERVO_LEFT, SERVO_MAX)
        time.sleep(0.8)

        # Return to neutral
        servo.move_servo_position(SERVO_LEFT, SERVO_NEUTRAL)
        servo.move_servo_position(SERVO_MIDDLE, SERVO_NEUTRAL)

    elif color == 'green':
        # Send down RIGHT chute, then sort with RIGHT motor
        print("Middle motor: RIGHT -> directing to right chute")
        servo.move_servo_position(SERVO_MIDDLE, SERVO_MIN)
        time.sleep(0.8)  # Give time for skittle to move onto right motor

        print("Right motor: RIGHT -> sorting green")
        servo.move_servo_position(SERVO_RIGHT, SERVO_MAX)
        time.sleep(0.8)

        # Return to neutral
        servo.move_servo_position(SERVO_RIGHT, SERVO_NEUTRAL)
        servo.move_servo_position(SERVO_MIDDLE, SERVO_NEUTRAL)

    elif color == 'yellow':
        # Send down RIGHT chute, then sort with RIGHT motor
        print("Middle motor: RIGHT -> directing to right chute")
        servo.move_servo_position(SERVO_MIDDLE, SERVO_MIN)
        time.sleep(0.8)  # Give time for skittle to move onto right motor

        print("Right motor: LEFT -> sorting yellow")
        servo.move_servo_position(SERVO_RIGHT, SERVO_MIN)
        time.sleep(0.8)

        # Return to neutral
        servo.move_servo_position(SERVO_RIGHT, SERVO_NEUTRAL)
        servo.move_servo_position(SERVO_MIDDLE, SERVO_NEUTRAL)

    else:
        # Unknown color - keep all motors at neutral
        print("Color not recognized -> holding at neutral")
        servo.move_servo_position(SERVO_MIDDLE, SERVO_NEUTRAL)
        servo.move_servo_position(SERVO_LEFT, SERVO_NEUTRAL)
        servo.move_servo_position(SERVO_RIGHT, SERVO_NEUTRAL)

if __name__ == "__main__":
    print("Skittle sorting servo test - press Ctrl+C to stop")
    print("Using placeholder RGB ranges - update them as needed")
    
    try:
        # Example test cases - replace with actual sensor input
        test_colors = [
            [255, 0, 0],      # Red
            [255, 128, 0],    # Orange
            [255, 255, 0],    # Yellow
            [0, 255, 0],      # Green
            [128, 128, 128],  # Unknown
        ]
        
        while True:
            for rgb in test_colors:
                sort_by_color(rgb)
                time.sleep(2)
    
    except KeyboardInterrupt:
        print("\nTest stopped.")
        servo.move_servo_position(SERVO_MIDDLE, SERVO_NEUTRAL)
        servo.move_servo_position(SERVO_LEFT, SERVO_NEUTRAL)
        servo.move_servo_position(SERVO_RIGHT, SERVO_NEUTRAL)