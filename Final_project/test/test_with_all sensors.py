import adafruit_mpr121
import busio
import board
import time
import neopixel
import RPi.GPIO as GPIO
import math
import pygame
import random

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
try:
    sound_touch1 = pygame.mixer.Sound('./sound/purr.wav')
    sound_touch1.set_volume(1.0)
    sound_touch2 = pygame.mixer.Sound('./sound/ES_MeowMidShort.wav')
    sound_touch2.set_volume(0.7)
    sound_squeeze = pygame.mixer.Sound('./sound/ES_MeowLowShort.wav')
    sound_hug = pygame.mixer.Sound('./sound/ES_MeowHighWithPurrs.wav')
    sound_tap = pygame.mixer.Sound('./sound/ES_MeowHighShort.wav')
except:
    print("Warning: Sound files not found. Sounds will be skipped.")
    sound_touch1 = sound_touch2 = sound_squeeze = sound_hug = sound_tap = None

# --- Breathing Pattern Variables ---
breathing_active = False
breath_phase = 0
breath_speed = 0.02
last_time = time.time()

# --- Purring Variables ---
purring_active = False
purr_phase = 0
purr_duration = 30
purr_start_time = 0
active_purr_duration = 0
purr_sound_channel = None
purr_light_phase = 0.0  # Changed to float for smoother transitions

# --- Touch Detection Variables ---
last_touch_state = False
last_touch1_state = False
last_touch2_state = False
touch_debounce_time = 0
touch1_debounce_time = 0
touch2_debounce_time = 0

# --- Sound Management ---
last_sound_time = 0
sound_cooldown = 1.0

# --- Sensor Priority Management ---
last_pressure_event_time = 0
pressure_lockout = 2.0

# --- Pressure Detection Variables ---
prev_pressure_input = 0
press_start_time = 0
press_duration = 0

QUICK_PRESS_TIME = 0.3
MEDIUM_PRESS_TIME = 1

stop_effect = False

print("Interactive Breathing Plush Ready!")
print("Long Press (Hug) = Start/Stop breathing")
print("Touch pad 1 (5) = 8 second purr with looping sound")
print("Touch pad 2 (11) = 7 second purr with looping sound")
print("Medium Press (Squeeze) = Squeeze sound")
print("Quick Press (Tap) = Tap sound")
print("Ctrl+C to exit")

def breathing_pattern(phase):
    """Calculate breathing intensity based on 4-7-8 breathing"""
    inhale_end = 4/19
    hold_end = 11/19
    exhale_end = 19/19
    
    if phase < inhale_end:
        progress = phase / inhale_end
        intensity = 0.15 + (math.sin(progress * math.pi / 2) ** 0.7) * 0.85
    elif phase < hold_end:
        hold_progress = (phase - inhale_end) / (hold_end - inhale_end)
        pulse = math.sin(hold_progress * math.pi * 3) * 0.03
        intensity = 1.0 + pulse
    else:
        exhale_progress = (phase - hold_end) / (exhale_end - hold_end)
        intensity = 1.0 - (math.sin(exhale_progress * math.pi / 2) ** 0.5) * 0.85
    
    return max(0.0, min(1.0, intensity))

def stop_all_effects():
    """Stop any running animation & clear LEDs"""
    global stop_effect
    stop_effect = True
    pixels.fill((0,0,0))
    pixels.show()
    print("LED stopped externally")

def set_breathing_leds(intensity):
    """Blue to white breathing pattern"""
    global stop_effect
    if stop_effect:
        return
    
    r = int(intensity * 255)
    g = int(50 + intensity * 205)
    b = 255
    
    pixels.fill((r, g, b))
    pixels.show()

def set_purr_leds():
    """Slow color transitions for purring mode - FIXED VERSION"""
    global purr_light_phase, stop_effect
    
    if stop_effect:
        return
    
    # SLOW increment - about 200 seconds for full cycle
    purr_light_phase += 0.02
    if purr_light_phase >= 4.0:
        purr_light_phase = 0.0
    
    # Define color stops
    colors = [
        (147, 112, 219),  # Soft purple
        (230, 230, 250),  # Lavender  
        (255, 182, 193),  # Soft pink
        (255, 218, 185),  # Warm peach
    ]
    
    # Determine which colors to blend between
    color_index = int(purr_light_phase)
    next_color_index = (color_index + 1) % len(colors)
    blend = purr_light_phase - color_index
    
    # Smooth interpolation
    r = int(colors[color_index][0] * (1 - blend) + colors[next_color_index][0] * blend)
    g = int(colors[color_index][1] * (1 - blend) + colors[next_color_index][1] * blend)
    b = int(colors[color_index][2] * (1 - blend) + colors[next_color_index][2] * blend)
    
    # Very gentle brightness pulse
    pulse = 0.75 + 0.15 * (math.sin(purr_light_phase * math.pi * 0.3) ** 2)
    
    r = int(r * pulse)
    g = int(g * pulse)
    b = int(b * pulse)
    
    pixels.fill((r, g, b))
    pixels.show()

def squeeze_light_effect():
    """Orange chase pattern with vibration"""
    global stop_effect
    stop_effect = False
    if stop_effect:
        return
    
    pwm.ChangeDutyCycle(50) 
    chase_leds((255, 255, 0), 0.05, 4)
    
    pixels.fill((0, 0, 0))
    pixels.show()
    time.sleep(1.0)
    pwm.ChangeDutyCycle(0)

def chase_leds(color, delay=0.05, cycles=2):
    """Chase pattern around the ring"""
    global stop_effect
    if stop_effect:
        return
    
    for _ in range(cycles):
        for i in range(NUM_PIXELS):
            pixels.fill((0, 0, 0))
            pixels[i] = color
            pixels.show()
            time.sleep(delay)

def orange_flash_led():
    """Quick orange flash effect"""
    global stop_effect
    if stop_effect:
        return

    for brightness in [0.3, 0.6, 1.0, 0.8, 0.5, 0.2]:
        r = int(255 * brightness)
        g = int(140 * brightness)
        b = int(0 * brightness)
        pixels.fill((r, g, b))
        pixels.show()
        time.sleep(0.02)
    
    pixels.fill((0, 0, 0))
    pixels.show()
               
def tap_light_effect():
    """Sparkle effect with vibration"""
    global stop_effect
    stop_effect = False
    if stop_effect:
        return
    
    # Start vibration immediately
    vibrate_burst(duration=1, intensity=0.6)
    # Sparkle runs concurrently
    sparkle_led()
    pixels.fill((0, 0, 0))
    pixels.show()

def sparkle_led(duration=5, background=(0,0,0), sparkle_color=(255,255,255),
                 max_sparkles=4, frame_delay=0.05):
    """Sparkle effect - will turn off vibration at end"""
    global stop_effect

    end_time = time.time() + duration
    while time.time() < end_time:
        if stop_effect:
            pwm.ChangeDutyCycle(0)  # Stop vibration
            return

        pixels.fill(background)

        for _ in range(random.randint(1, max_sparkles)):
            i = random.randrange(NUM_PIXELS)
            scale = random.random()**2
            pixels[i] = (
                int(sparkle_color[0]*scale),
                int(sparkle_color[1]*scale),
                int(sparkle_color[2]*scale)
            )

        pixels.show()
        time.sleep(frame_delay)
    
    # Turn off vibration when sparkle ends
    pwm.ChangeDutyCycle(0)
    
def vibrate_burst(duration=0.2, intensity=0.5):
    """Burst vibration effect - non-blocking start"""
    duty_cycle = int(intensity * 100)
    pwm.ChangeDutyCycle(duty_cycle)
    # Don't sleep here - let it run while other things happen
    # Will be stopped by caller or next vibration command
    
def vibrate_breathing(intensity):
    """Breathing vibration pattern"""
    duty_cycle = int(intensity * 70 + 10)
    pwm.ChangeDutyCycle(duty_cycle)

def vibrate_purr():
    """Cat purr vibration pattern"""
    global purr_phase
    
    purr_phase += 0.15
    if purr_phase >= 1.0:
        purr_phase = 0
    
    purr_intensity = 0.3 + 0.2 * math.sin(purr_phase * math.pi * 2)
    duty_cycle = int(purr_intensity * 100)
    pwm.ChangeDutyCycle(duty_cycle)

def check_purr_timer(current_time, duration):
    """Check purr timer and cleanup"""
    global purring_active, purr_sound_channel, purr_light_phase, stop_effect
    
    if current_time - purr_start_time >= duration:
        purring_active = False
        purr_light_phase = 0.0
        stop_effect = True  # Signal to stop any ongoing effects
        print(f"Purring timer ended after {duration} seconds")
        
        if purr_sound_channel:
            purr_sound_channel.stop()
            purr_sound_channel = None
        
        pixels.fill((0, 0, 0))
        pixels.show()
        
        if not breathing_active:
            pwm.ChangeDutyCycle(0)
        
        stop_effect = False  # Reset flag
        return False
    elif not breathing_active:
        vibrate_purr()
        return True
    return True

def start_purr(duration, sound, origin):
    """Start purring mode"""
    global purring_active, purr_start_time, active_purr_duration, purr_sound_channel, last_sound_time, purr_light_phase
    
    pygame.mixer.stop()
    
    purring_active = True
    purr_start_time = time.time()
    active_purr_duration = duration
    last_sound_time = time.time()
    purr_light_phase = 0.0  # Reset phase
    
    if sound:
        purr_sound_channel = sound.play(loops=-1)
    
    print(f"Purring started for {duration} seconds from {origin}")

def can_play_sound(current_time):
    """Check sound cooldown"""
    global last_sound_time
    
    if current_time - last_sound_time >= sound_cooldown:
        return True
    else:
        print(f"Sound cooldown active... ({sound_cooldown - (current_time - last_sound_time):.1f}s remaining)")
        return False

def play_sound_safe(sound, current_time, description="", max_duration=None):
    """Play sound with cooldown and optional duration limit
    
    Args:
        sound: The pygame.mixer.Sound object to play
        current_time: Current timestamp
        description: Description of the sound for logging
        max_duration: Maximum duration in milliseconds (None = play full sound)
    """
    global last_sound_time
    
    if can_play_sound(current_time):
        pygame.mixer.stop()
        
        if sound:
            if max_duration:
                # Play sound for specified duration in milliseconds
                sound.play(maxtime=max_duration)
            else:
                # Play full sound
                sound.play()
            last_sound_time = current_time
            if description:
                print(description)
        return True
    return False

def stop_purr():
    """Stop purring mode"""
    global purring_active, purr_sound_channel, purr_light_phase, stop_effect
    
    purring_active = False
    purr_light_phase = 0.0
    stop_effect = True  # Signal to stop effects
    print("Purring stopped manually")
    
    if purr_sound_channel:
        purr_sound_channel.stop()
        purr_sound_channel = None
    
    pixels.fill((0, 0, 0))
    pixels.show()
    
    if not breathing_active:
        pwm.ChangeDutyCycle(0)
    
    stop_effect = False  # Reset flag

def detect_pressure_type():
    """Detect pressure types: tap, squeeze, hug"""
    global prev_pressure_input, press_start_time, press_duration, breathing_active, breath_phase, last_pressure_event_time, purring_active, stop_effect
    
    current_pressure = GPIO.input(FSR_PIN)
    current_time = time.time()
    
    if (not prev_pressure_input) and current_pressure:
        press_start_time = current_time
    
    elif prev_pressure_input and (not current_pressure):
        press_duration = current_time - press_start_time
        last_pressure_event_time = current_time
        
        if press_duration < QUICK_PRESS_TIME:
            # Tap
            if purring_active:
                stop_purr()
                print("Purring stopped by tap")
            
            if breathing_active:
                stop_effect = True
            else:
                # Play sound FIRST, then lights
                play_sound_safe(sound_tap, current_time, 
                              f"Tap detected! (duration: {press_duration:.2f}s)", 
                              max_duration=2000)
                tap_light_effect()
        
        elif press_duration < MEDIUM_PRESS_TIME:
            # Squeeze
            if purring_active:
                stop_purr()
                print("Purring stopped by squeeze")
            
            if breathing_active:
                stop_effect = True
            else:
                # Play sound FIRST, then lights
                play_sound_safe(sound_squeeze, current_time, 
                              f"Squeeze detected! (duration: {press_duration:.2f}s)", 
                              max_duration=3000)
                squeeze_light_effect()
        
        else:
            # Hug - toggle breathing
            if purring_active:
                stop_purr()
                print("Purring stopped by hug")
            
            breathing_active = not breathing_active
            print(f"HUG DETECTED! Breathing {'started' if breathing_active else 'stopped'}")
            
            if not breathing_active:
                pixels.fill((0, 0, 0))
                pixels.show()
                pwm.ChangeDutyCycle(0)
            else:
                breath_phase = 0
                if sound_hug:
                    pygame.mixer.stop()
                    sound_hug.play()
        
        press_start_time = 0
    
    prev_pressure_input = current_pressure

try:
    while True:
        current_time = time.time()
        dt = current_time - last_time
        last_time = current_time
        
        try:
            touched = mpr121.touched()
            
            # Touch pad 1 (pin 5): 8 second purr
            if touched & (1 << 5):
                if not last_touch1_state and (current_time - touch1_debounce_time) > 0.5:
                    if can_play_sound(current_time):
                        start_purr(8, sound_touch1, 'touch1')
                    else:
                        print("Touch cooldown active, please wait...")
                    last_touch1_state = True
                    touch1_debounce_time = current_time
            else:
                last_touch1_state = False
            
            # Touch pad 2 (pin 11): 7 second purr
            if touched & (1 << 11):
                if not last_touch2_state and (current_time - touch2_debounce_time) > 0.5:
                    if can_play_sound(current_time):
                        start_purr(7, sound_touch2, 'touch2')
                        orange_flash_led()
                    else:
                        print("Touch cooldown active, please wait...")
                    last_touch2_state = True
                    touch2_debounce_time = current_time
            else:
                last_touch2_state = False
                
        except Exception as e:
            print(f"MPR121 error: {e}")
        
        # Breathing pattern
        if breathing_active:
            breath_phase += breath_speed
            if breath_phase >= 1.0:
                breath_phase = 0
            
            intensity = breathing_pattern(breath_phase)
            set_breathing_leds(intensity)
            vibrate_breathing(intensity)
        
        # Purring pattern
        if purring_active:
            if not check_purr_timer(current_time, active_purr_duration):
                # Timer expired, ensure lights are off
                pixels.fill((0, 0, 0))
                pixels.show()
            elif not breathing_active:
                set_purr_leds()
        
        # Pressure detection
        detect_pressure_type()
        
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
        time.sleep(0.1)
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