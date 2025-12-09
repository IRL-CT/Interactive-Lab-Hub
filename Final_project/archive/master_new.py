import adafruit_mpr121
import busio
import board
import time
import os
import subprocess
import neopixel
import RPi.GPIO as GPIO
from threading import Thread, Event

# ==================== HARDWARE SETUP ====================

# --- NeoPixel Setup ---
PIXEL_PIN = board.D18
NUM_PIXELS = 24
BRIGHTNESS = 0.3
pixels = neopixel.NeoPixel(
    PIXEL_PIN, NUM_PIXELS, brightness=BRIGHTNESS, auto_write=False
)

# --- MPR121 Capacitive Touch Setup ---
i2c = busio.I2C(board.SCL, board.SDA)
mpr121 = adafruit_mpr121.MPR121(i2c)

# --- FSR Pressure Sensor Setup ---
FSR_PIN = 4
GPIO.setmode(GPIO.BCM)
GPIO.setup(FSR_PIN, GPIO.IN)

# --- Vibration Motor Setup ---
MOTOR_PIN = 12  # Changed to avoid conflict with NeoPixel on D12
GPIO.setup(MOTOR_PIN, GPIO.OUT)
motor_pwm = GPIO.PWM(MOTOR_PIN, 200)
motor_pwm.start(0)

# ==================== THRESHOLDS ====================

QUICK_PRESS_TIME = 0.3      # Tap
MEDIUM_PRESS_TIME = 0.7     # Press
LONG_PRESS_TIME = 2.0       # Hug!
IDLE_TIMEOUT = 3.0          # Seconds before going idle

# ==================== STATE MANAGEMENT ====================

class PlushState:
    def __init__(self):
        self.purr_process = None
        self.meow_process = None
        self.current_mode = "idle"  # idle, pet, hug, play
        self.last_interaction = time.time()
        self.motor_running = Event()
        
plush = PlushState()

# ==================== SOUND FUNCTIONS ====================

def stop_all_sounds():
    os.system("pkill -9 aplay 2>/dev/null")
    plush.purr_process = None
    plush.meow_process = None

def play_sound(sound_file, loop=False):
    """Play a sound file, optionally looping"""
    stop_all_sounds()
    if loop:
        # Loop using aplay's built-in loop or bash loop
        return subprocess.Popen(
            f"while true; do aplay -q {sound_file}; done",
            shell=True
        )
    else:
        return subprocess.Popen(["aplay", "-q", sound_file])

def play_purr():
    if plush.purr_process is None:
        plush.purr_process = play_sound("sound/purr.wav", loop=True)

def play_meow():
    if plush.meow_process is None:
        plush.meow_process = play_sound("sound/meow.wav", loop=False)

# ==================== MOTOR FUNCTIONS ====================

def motor_stop():
    plush.motor_running.clear()
    motor_pwm.ChangeDutyCycle(0)

def motor_purr(intensity=30):
    """Gentle vibration like a purring cat"""
    for duty in range(0, intensity, 2):
        if not plush.motor_running.is_set():
            return
        motor_pwm.ChangeDutyCycle(duty)
        time.sleep(0.03)
    for duty in range(intensity, 0, -2):
        if not plush.motor_running.is_set():
            return
        motor_pwm.ChangeDutyCycle(duty)
        time.sleep(0.03)

def motor_heartbeat(intensity=50):
    """Double pulse like a heartbeat for hugs"""
    for _ in range(2):  # Double beat
        motor_pwm.ChangeDutyCycle(intensity)
        time.sleep(0.1)
        motor_pwm.ChangeDutyCycle(0)
        time.sleep(0.1)
    time.sleep(0.3)  # Pause between beats

def motor_excited(intensity=60):
    """Quick vibrations for playful interactions"""
    for _ in range(3):
        motor_pwm.ChangeDutyCycle(intensity)
        time.sleep(0.05)
        motor_pwm.ChangeDutyCycle(0)
        time.sleep(0.05)

# ==================== LED ANIMATIONS ====================

def led_off():
    pixels.fill((0, 0, 0))
    pixels.show()

def led_breathing(color, steps=20, speed=0.04):
    """Smooth breathing animation"""
    r, g, b = color
    # Breathe in
    for i in range(steps):
        level = i / steps
        pixels.fill((int(r * level), int(g * level), int(b * level)))
        pixels.show()
        time.sleep(speed)
    # Breathe out
    for i in range(steps, -1, -1):
        level = i / steps
        pixels.fill((int(r * level), int(g * level), int(b * level)))
        pixels.show()
        time.sleep(speed)

def led_warm_glow(color, duration=0.5):
    """Steady warm glow for hugs"""
    pixels.fill(color)
    pixels.show()
    time.sleep(duration)

def led_sparkle(color, count=5):
    """Sparkle effect for playful moments"""
    import random
    for _ in range(count):
        pixels.fill((0, 0, 0))
        for _ in range(6):
            idx = random.randint(0, NUM_PIXELS - 1)
            pixels[idx] = color
        pixels.show()
        time.sleep(0.1)

def led_rainbow_chase(speed=0.05):
    """Rainbow chase for excited state"""
    for offset in range(NUM_PIXELS):
        for i in range(NUM_PIXELS):
            hue = ((i + offset) % NUM_PIXELS) / NUM_PIXELS
            # Simple HSV to RGB (hue only)
            if hue < 1/3:
                r, g, b = int(255 * (1 - 3*hue)), int(255 * 3*hue), 0
            elif hue < 2/3:
                hue -= 1/3
                r, g, b = 0, int(255 * (1 - 3*hue)), int(255 * 3*hue)
            else:
                hue -= 2/3
                r, g, b = int(255 * 3*hue), 0, int(255 * (1 - 3*hue))
            pixels[i] = (r, g, b)
        pixels.show()
        time.sleep(speed)

# ==================== REACTION BEHAVIORS ====================

# Color palette
COLOR_PURR = (80, 40, 150)      # Soft purple
COLOR_MEOW = (255, 80, 10)      # Warm orange
COLOR_HUG = (255, 100, 50)      # Cozy amber
COLOR_TAP = (100, 200, 255)     # Light blue
COLOR_PLAY = (50, 255, 100)     # Playful green

def react_to_pet(touch_pad):
    """Reaction when capacitive touch detected (petting)"""
    plush.current_mode = "pet"
    plush.last_interaction = time.time()
    plush.motor_running.set()
    
    if touch_pad == 1:
        # Gentle pet - purr
        play_purr()
        led_breathing(COLOR_PURR, steps=15, speed=0.05)
        motor_purr(25)
    elif touch_pad == 2:
        # Different spot - meow
        play_meow()
        led_breathing(COLOR_MEOW, steps=15, speed=0.05)
        motor_excited(40)

def react_to_pressure(level, duration):
    """Reaction based on FSR pressure level"""
    plush.last_interaction = time.time()
    plush.motor_running.set()
    
    if level == "LOW":
        # Quick tap - playful chirp
        plush.current_mode = "play"
        play_meow()
        led_sparkle(COLOR_TAP, count=3)
        motor_excited(30)
        print("Tap detected - playful response!")
        
    elif level == "MEDIUM":
        # Firm press - content purr
        plush.current_mode = "pet"
        play_purr()
        led_breathing(COLOR_PURR, steps=10, speed=0.06)
        motor_purr(35)
        print("Press detected - contented purr!")
        
    elif level == "HIGH":
        # Hug! - warmest response
        plush.current_mode = "hug"
        play_purr()
        print("HUG DETECTED! Maximum warmth!")
        
        # Extended warm response for hugs
        for _ in range(int(duration)):
            led_warm_glow(COLOR_HUG, 0.3)
            motor_heartbeat(45)
            led_breathing(COLOR_HUG, steps=10, speed=0.04)

def react_idle():
    """Gentle idle animation when no interaction"""
    plush.current_mode = "idle"
    stop_all_sounds()
    motor_stop()
    
    # Soft breathing to show it's "alive"
    led_breathing((20, 10, 30), steps=30, speed=0.08)

# ==================== PRESSURE DETECTION ====================

def get_pressure_level(duration):
    """Determine pressure level based on duration"""
    if duration < QUICK_PRESS_TIME:
        return "LOW"
    elif duration < MEDIUM_PRESS_TIME:
        return "MEDIUM"
    else:
        return "HIGH"

# ==================== MAIN LOOP ====================

def main():
    print("=" * 50)
    print("Smart Plush Started!")
    print("Touch pads 1 & 2 for petting")
    print("FSR sensor for pressure (tap/press/hug)")
    print("Press Ctrl+C to exit")
    print("=" * 50)
    
    # FSR state tracking
    fsr_prev_input = False
    fsr_press_start = 0
    
    # Idle timer
    last_interaction = time.time()
    
    try:
        while True:
            current_time = time.time()
            
            # --- Check Capacitive Touch (MPR121) ---
            touched_1 = mpr121[1].value
            touched_2 = mpr121[2].value
            
            if touched_1:
                react_to_pet(1)
                last_interaction = current_time
                
            elif touched_2:
                react_to_pet(2)
                last_interaction = current_time
            
            # --- Check FSR Pressure Sensor ---
            fsr_input = GPIO.input(FSR_PIN)
            
            # Pressure started
            if not fsr_prev_input and fsr_input:
                fsr_press_start = current_time
                print("Pressure detected...", end="", flush=True)
            
            # Pressure released
            elif fsr_prev_input and not fsr_input:
                press_duration = current_time - fsr_press_start
                level = get_pressure_level(press_duration)
                
                print(f"\rPressure: {level} ({press_duration:.2f}s)")
                react_to_pressure(level, press_duration)
                last_interaction = current_time
            
            # Continuous pressure (potential hug in progress)
            elif fsr_input and fsr_press_start > 0:
                press_duration = current_time - fsr_press_start
                
                # If held long enough, start hug response while still pressing
                if press_duration > LONG_PRESS_TIME and plush.current_mode != "hug":
                    print("\rHug in progress...")
                    plush.current_mode = "hug"
                    play_purr()
                    led_warm_glow(COLOR_HUG, 0.1)
                    motor_heartbeat(40)
                    last_interaction = current_time
            
            fsr_prev_input = fsr_input
            
            # --- Check for Idle State ---
            if current_time - last_interaction > IDLE_TIMEOUT:
                if plush.current_mode != "idle":
                    print("Going idle...")
                    react_idle()
            
            time.sleep(0.05)  # 50ms loop delay
            
    except KeyboardInterrupt:
        print("\n\nShutting down...")
    
    finally:
        # Cleanup
        stop_all_sounds()
        motor_pwm.stop()
        led_off()
        GPIO.cleanup()
        print("Smart plush stopped. Goodbye!")

if __name__ == "__main__":
    main()