import time
import board
from adafruit_seesaw import seesaw, rotaryio, digitalio
from adafruit_lsm6ds.lsm6ds3 import LSM6DS3
import pi_servo_hat
import math
import os

# --- Setup ---
ss = seesaw.Seesaw(board.I2C(), addr=0x36)
ss.pin_mode(24, ss.INPUT_PULLUP)
button = digitalio.DigitalIO(ss, 24)
encoder = rotaryio.IncrementalEncoder(ss)
last_encoder = -999

# Accelerometer
sox = LSM6DS3(board.I2C(), address=0x6A)

# Servo
servo = pi_servo_hat.PiServoHat()
servo.restart()
SERVO_MIN = 0
SERVO_MAX = 120
SERVO_CH = 0

# --- Modes ---
MODES = ["Encoder Only", "Accelerometer Only", "Combined"]
mode = 0
mode_press = False

# --- State ---
base_angle = 60
enc_factor = 5

def clamp(val, minv, maxv):
    return max(minv, min(maxv, val))

def clear():
    os.system('clear')

# --- Main Loop ---
tilt_offset = 0
while True:
    # --- Read encoder/button ---
    enc_pos = -encoder.position
    if not button.value and not mode_press:
        mode = (mode + 1) % len(MODES)
        mode_press = True
    if button.value and mode_press:
        mode_press = False

    # --- Read accelerometer ---
    accel_x, accel_y, accel_z = sox.acceleration
    z_angle_rad = math.atan2(-accel_y, accel_x)
    z_angle_deg = math.degrees(z_angle_rad)
    raw_offset = -z_angle_deg * (40/90)
    tilt_offset = 0.8 * tilt_offset + 0.2 * raw_offset
    tilt_offset_int = int(tilt_offset)

    # --- Calculate servo angle ---
    if mode == 0:  # Encoder Only
        servo_angle = clamp(60 + enc_pos * enc_factor, SERVO_MIN, SERVO_MAX)
    elif mode == 1:  # Accelerometer Only
        servo_angle = clamp(60 + tilt_offset_int, SERVO_MIN, SERVO_MAX)
    else:  # Combined
        servo_angle = clamp(60 + enc_pos * enc_factor + tilt_offset_int, SERVO_MIN, SERVO_MAX)
    servo.move_servo_position(SERVO_CH, servo_angle)

    # --- Dashboard ---
    clear()
    print(f"=== Servo/Encoder/Accel Dashboard ===")
    print(f"Mode: {MODES[mode]} (press encoder button to switch)")
    print(f"Encoder position: {enc_pos}")
    print(f"Accel X: {accel_x:.2f}  Y: {accel_y:.2f}  Z: {accel_z:.2f}")
    print(f"Z angle: {z_angle_deg:.1f}°  Tilt offset: {tilt_offset_int}")
    print(f"Servo angle: {servo_angle}")
    print(f"\n[Encoder sets base, Accel tilts needle, Combined = both]")
    time.sleep(0.07)
