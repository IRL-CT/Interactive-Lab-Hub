import adafruit_mpr121
import busio
import board
import time
import neopixel
import RPi.GPIO as GPIO
import math
import pygame

# --- NeoPixel Setup ---
PIXEL_PIN = board.D18
NUM_PIXELS = 24
pixels = neopixel.NeoPixel(PIXEL_PIN, NUM_PIXELS, brightness=0.3, auto_write=False)

# --- MPR121 Touch Sensor ---
i2c = busio.I2C(board.SCL, board.SDA)
mpr121 = adafruit_mpr121.MPR121(i2c)

# --- FSR Pressure Sensor ---
FSR_PIN = 4
GPIO.setmode(GPIO.BCM)
GPIO.setup(FSR_PIN, GPIO.IN)

# --- Vibration Motor ---
MOTOR_PIN = 12
GPIO.setup(MOTOR_PIN, GPIO.OUT)
pwm = GPIO.PWM(MOTOR_PIN, 100)  # 100Hz frequency
pwm.start(0)

# --- Audio Setup ---
pygame.mixer.init()
# Load your sound files here (you'll need to add actual sound files)
try:
    sound_touch1 = pygame.mixer.Sound('./sound/purr.wav')
    sound_touch2 = pygame.mixer.Sound('./sound/meow.wav')
    sound_squeeze = pygame.mixer.Sound('./sound/ES_MeowLowShort.wav')
    sound_hug = pygame.mixer.Sound('./sound/ES_MeowMidShort.wav')
    sound_tap = pygame.mixer.Sound('./sound/ES_MeowHighShort.wav')
except:
    print("Warning: Sound files not found. Sounds will be skipped.")
    sound_touch1 = sound_touch2 = sound_squeeze = sound_hug = sound_tap = None

# --- Breathing Pattern Variables ---
breathing_active = False
breath_phase = 0  # 0-1 representing the breathing cycle
breath_speed = 0.02  # Adjust for faster/slower breathing
last_time = time.time()

# --- Purring Variables ---
purring_active = False
purr_phase = 0
purr_duration = 30  # Default purr duration in seconds
purr_start_time = 0
active_purr_duration = 0  # Stores the current purr duration
purr_sound_channel = None  # For looping sound

# --- Touch Detection Variables ---
last_touch_state = False
last_touch1_state = False
last_touch2_state = False
touch_debounce_time = 0
touch1_debounce_time = 0
touch2_debounce_time = 0

# --- Pressure Detection Variables ---
pressure_count = 0
last_pressure_state = False
pressure_start_time = 0
squeeze_threshold = 5  # Consecutive high readings for squeeze
hug_threshold = 3      # Moderate sustained pressure
tap_threshold = 1      # Brief pressure spike

print("Interactive Breathing Plush Ready!")
print("Touch pad 0 = Start/Stop breathing")
print("Touch pad 1 = 60 second purr with looping sound")
print("Touch pad 2 = 20 second purr with looping sound")
print("FSR = Different sounds for squeeze/hug/tap")
print("Ctrl+C to exit")

def breathing_pattern(phase):
    """Calculate breathing intensity (0-1) based on therapeutic 4-7-8 breathing
    Inhale for 4 counts, hold for 7 counts, exhale for 8 counts
    Total cycle = 19 counts (~12 seconds at current speed for ~5 breaths/min)
    """
    # Normalize phases based on 4-7-8 ratio (total = 19 units)
    inhale_end = 4/19      # 0.211 (4 counts)
    hold_end = 11/19       # 0.579 (7 counts)
    exhale_end = 19/19     # 1.000 (8 counts)
    
    if phase < inhale_end:  # Inhale (4 counts) - smooth rise
        progress = phase / inhale_end
        intensity = 0.15 + (math.sin(progress * math.pi / 2) ** 0.7) * 0.85
    
    elif phase < hold_end:  # Hold (7 counts) - gentle plateau with slight pulse
        hold_progress = (phase - inhale_end) / (hold_end - inhale_end)
        pulse = math.sin(hold_progress * math.pi * 3) * 0.03  # Subtle pulse
        intensity = 1.0 + pulse
    
    else:  # Exhale (8 counts) - slow, extended release
        exhale_progress = (phase - hold_end) / (exhale_end - hold_end)
        # Longer, gentler exhale curve for relaxation
        intensity = 1.0 - (math.sin(exhale_progress * math.pi / 2) ** 0.5) * 0.85
    
    # Clamp to 0.0-1.0 range to prevent RGB overflow
    return max(0.0, min(1.0, intensity))
    
def set_breathing_leds(intensity):
    """Set LED color transition from blue to white based on breathing intensity
    Low intensity (exhale) = deep blue
    High intensity (inhale peak) = bright white
    """
    # Blue at low intensity: (0, 50, 255)
    # White at high intensity: (255, 255, 255)
    
    # Interpolate between blue and white based on intensity
    r = int(intensity * 255)  # Red increases from 0 to 255
    g = int(50 + intensity * 205)  # Green increases from 50 to 255
    b = 255  # Blue stays constant at 255
    
    pixels.fill((r, g, b))
    pixels.show()

def vibrate_breathing(intensity):
    """Set vibration motor based on breathing intensity"""
    duty_cycle = int(intensity * 70 + 10)  # 10-80% duty cycle
    pwm.ChangeDutyCycle(duty_cycle)

def vibrate_purr():
    """Create a purring vibration pattern like a cat
    Purrs have a rhythmic pattern around 25-150Hz with variations
    """
    global purr_phase
    
    # Create a gentle rhythmic pattern
    purr_phase += 0.15  # Speed of purr cycle
    if purr_phase >= 1.0:
        purr_phase = 0
    
    # Oscillating pattern: gentle pulses
    purr_intensity = 0.3 + 0.2 * math.sin(purr_phase * math.pi * 2)  # 30-50% range
    duty_cycle = int(purr_intensity * 100)
    pwm.ChangeDutyCycle(duty_cycle)

def check_purr_timer(current_time, duration):
    """Check if purr timer has expired and handle cleanup
    
    Args:
        current_time: The current timestamp
        duration: Duration in seconds for the purr timer
    
    Returns:
        bool: True if purring should continue, False if timer expired
    """
    global purring_active, purr_sound_channel
    
    if current_time - purr_start_time >= duration:
        purring_active = False
        print(f"Purring timer ended after {duration} seconds")
        
        # Stop looping sound
        if purr_sound_channel:
            purr_sound_channel.stop()
            purr_sound_channel = None
        
        if not breathing_active:
            pwm.ChangeDutyCycle(0)
        return False
    elif not breathing_active:
        # Only purr if not breathing (breathing takes priority)
        vibrate_purr()
        return True
    return True

def start_purr(duration, sound):
    """Start purring with specified duration and looping sound
    
    Args:
        duration: How long to purr in seconds
        sound: The pygame.mixer.Sound object to loop
    """
    global purring_active, purr_start_time, active_purr_duration, purr_sound_channel
    
    purring_active = True
    purr_start_time = time.time()
    active_purr_duration = duration
    
    # Start looping sound if available
    if sound:
        purr_sound_channel = sound.play(loops=-1)  # -1 means loop infinitely
    
    print(f"Purring started for {duration} seconds with looping sound")

def stop_purr():
    """Stop purring and clean up"""
    global purring_active, purr_sound_channel
    
    purring_active = False
    print("Purring stopped manually")
    
    # Stop looping sound
    if purr_sound_channel:
        purr_sound_channel.stop()
        purr_sound_channel = None
    
    if not breathing_active:
        pwm.ChangeDutyCycle(0)

def detect_pressure_type():
    """Analyze pressure pattern to determine squeeze/hug/tap"""
    global pressure_count, last_pressure_state, pressure_start_time
    
    current_pressure = GPIO.input(FSR_PIN)
    current_time = time.time()
    
    if current_pressure and not last_pressure_state:
        # Pressure started
        pressure_start_time = current_time
        pressure_count = 1
    elif current_pressure and last_pressure_state:
        # Pressure continuing
        pressure_count += 1
    elif not current_pressure and last_pressure_state:
        # Pressure released
        duration = current_time - pressure_start_time
        
        if pressure_count >= squeeze_threshold:
            if sound_squeeze:
                sound_squeeze.play()
            print("Squeeze detected!")
        elif pressure_count >= hug_threshold and duration > 0.5:
            if sound_hug:
                sound_hug.play()
            print("Gentle hug detected!")
        elif pressure_count <= tap_threshold and duration < 0.3:
            if sound_tap:
                sound_tap.play()
            print("Tap detected!")
        
        pressure_count = 0
    
    last_pressure_state = current_pressure

try:
    while True:
        current_time = time.time()
        dt = current_time - last_time
        last_time = current_time
        
        # --- Touch Sensor 0: Toggle Breathing ---
        try:
            # Use touched() method which returns the full touch state
            touched = mpr121.touched()
            
            # Check if pad 0 is touched (bit 0)
            if touched & (1 << 0):
                if not last_touch_state and (current_time - touch_debounce_time) > 0.3:
                    breathing_active = not breathing_active
                    print(f"Breathing {'started' if breathing_active else 'stopped'}")
                    if not breathing_active:
                        pixels.fill((0, 0, 0))
                        pixels.show()
                        if not purring_active:  # Only stop motor if not purring
                            pwm.ChangeDutyCycle(0)
                    last_touch_state = True
                    touch_debounce_time = current_time
            else:
                last_touch_state = False
            
            # Touch pad 1: 60 second purr with looping sound
            if touched & (1 << 1):
                if not last_touch1_state and (current_time - touch1_debounce_time) > 0.3:
                    if purring_active:
                        stop_purr()
                    else:
                        start_purr(60, sound_touch1)  # 60 seconds
                    last_touch1_state = True
                    touch1_debounce_time = current_time
            else:
                last_touch1_state = False
            
            # Touch pad 2: 20 second purr with looping sound
            if touched & (1 << 2):
                if not last_touch2_state and (current_time - touch2_debounce_time) > 0.3:
                    if purring_active:
                        stop_purr()
                    else:
                        start_purr(20, sound_touch2)  # 20 seconds
                    last_touch2_state = True
                    touch2_debounce_time = current_time
            else:
                last_touch2_state = False
                
        except Exception as e:
            print(f"MPR121 error: {e}")
            print("Check I2C connections!")
        
        # --- Breathing Pattern ---
        if breathing_active:
            breath_phase += breath_speed
            if breath_phase >= 1.0:
                breath_phase = 0
            
            intensity = breathing_pattern(breath_phase)
            set_breathing_leds(intensity)
            vibrate_breathing(intensity)
        
        # --- Purring Pattern ---
        if purring_active:
            check_purr_timer(current_time, active_purr_duration)
        
        # --- Pressure Sensor: Detect Type ---
        # Uncomment to enable pressure detection:
        # detect_pressure_type()
        
        time.sleep(0.05)

except KeyboardInterrupt:
    print("\nStopping...")

finally:
    try:
        pixels.fill((0, 0, 0))
        pixels.show()
    except:
        pass
    
    try:
        pwm.ChangeDutyCycle(0)
        time.sleep(0.1)  # Give PWM time to finish
        pwm.stop()
    except:
        pass
    
    try:
        GPIO.cleanup()
    except:
        pass
    
    try:
        pygame.mixer.quit()
    except:
        pass
    
    print("Done!")