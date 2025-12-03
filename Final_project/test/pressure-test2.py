import RPi.GPIO as GPIO
import time

# Set the GPIO to BCM Mode
GPIO.setmode(GPIO.BCM)

# Set Pin 4 to be our Sniffer Pin
GPIO.setup(4, GPIO.IN)

# Pressure detection variables
prev_input = 0
press_start_time = 0
press_count = 0
last_press_time = 0

# Thresholds (adjust these based on your FSR behavior)
QUICK_PRESS_TIME = 0.3    # Quick tap = LOW pressure
MEDIUM_PRESS_TIME = 0.7   # Sustained press = MEDIUM pressure
# Anything longer = HIGH pressure (hug!)

def get_pressure_level(duration, intensity):
    """Determine pressure level based on press duration and frequency"""
    if duration < QUICK_PRESS_TIME:
        return "LOW"
    elif duration < MEDIUM_PRESS_TIME:
        return "MEDIUM"
    else:
        return "HIGH"

print("FSR Pressure Detector Started!")
print("Detecting: LOW (tap), MEDIUM (press), HIGH (hug)")
print("Press Ctrl+C to exit\n")

try:
    while True:
        # Take a reading from the pressure pad
        input = GPIO.input(4)
        current_time = time.time()
        
        # Pressure started (transition from not pressed to pressed)
        if ((not prev_input) and input):
            press_start_time = current_time
            print("Pressure detected...", end="", flush=True)
        
        # Pressure released (transition from pressed to not pressed)
        elif (prev_input and (not input)):
            press_duration = current_time - press_start_time
            
            # Calculate intensity based on how consistent the pressure was
            intensity = min(press_duration / MEDIUM_PRESS_TIME, 1.0)
            
            # Get pressure level
            level = get_pressure_level(press_duration, intensity)
            
            # Clear the "detecting..." message and print result
            print(f"\r{' ' * 50}", end="")  # Clear line
            print(f"\rPressure Level: {level:8s} (duration: {press_duration:.2f}s)")
            
            # Special message for hugs!
            if level == "HIGH":
                print("HUG DETECTED!")
            elif level == "MEDIUM":
                print("Nice firm press")
            elif level == "LOW":
                print("Gentle tap detected")
            
            print()  # New line for next detection
        
        # Continuous pressure feedback while pressed
        elif input and press_start_time > 0:
            press_duration = current_time - press_start_time
            
            # Show real-time feedback
            bar_length = min(int(press_duration / MEDIUM_PRESS_TIME * 20), 20)
            bar = "||||" * bar_length + ":::" * (20 - bar_length)
            print(f"\r[{bar}] {press_duration:.1f}s", end="", flush=True)
        
        # Update previous input
        prev_input = input
        
        # Slight pause to avoid spamming
        time.sleep(0.05)

except KeyboardInterrupt:
    print("\n\nCleaning up...")
    GPIO.cleanup()
    print("Program ended.")