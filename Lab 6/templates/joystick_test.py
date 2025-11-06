import time
import sys
import qwiic_joystick

class JoystickEvent:
    def __init__(self):
        self.js = None
        self.x = 0
        self.y = 0
        self.button = False
        self.prev_js_btn = False
        self.setup_joystick()
    
    def setup_joystick(self):
        """Initialize the Qwiic Joystick hardware"""
        self.js = qwiic_joystick.QwiicJoystick()
        if not self.js.connected:
            print("Qwiic Joystick not found.", file=sys.stderr)
            sys.exit(1)
        self.js.begin()
        print("Joystick connected successfully!")
    
    def normalize_value(self, raw_value):
        """Convert 0-1024 range to -1 to 1"""
        return (raw_value / 512) - 1
    
    def update(self):
        """Read current joystick state"""
        raw_x = self.js.horizontal
        raw_y = self.js.vertical
        
        self.x = self.normalize_value(raw_x)
        self.y = self.normalize_value(raw_y)
        
        self.prev_js_btn = self.button
        self.button = (self.js.button == 0)
    
    def shoot(self):
        if not self.prev_js_btn and self.button:
            print("shoot")
            return True
        return False
    
    def move(self):
        return self.x, self.y


def test_joystick():
    """Test the joystick functionality"""
    print("=== Joystick Test Program ===")
    print("Move the joystick around and press the button")
    print("Press Ctrl+C to exit\n")
    
    joystick = JoystickEvent()
    
    try:
        while True:
            joystick.update()
            
            # Check for shooting
            joystick.shoot()
            
            # Display joystick position
            x, y = joystick.move()
            button_status = "PRESSED" if joystick.button else "released"
            
            # Clear line and print (overwrite previous line)
            print(f"\rX: {x:+.2f} | Y: {y:+.2f} | Button: {button_status}    ", end="", flush=True)
            
            time.sleep(0.1)  # Update 10 times per second
            
    except KeyboardInterrupt:
        print("\n\nTest ended.")


if __name__ == "__main__":
    test_joystick()