import time


def run(bus, hat_factory, delay=time.sleep):
    try:
        bus.writeByte(0x40, 0x09, 0x10)  # Channel 0 FULL_OFF.
        servo = hat_factory()
        servo.PCA9685.set_invrt_bit(0)
        servo.PCA9685.set_outdrv_bit(1)
        servo.PCA9685.set_och_bit(0)
        servo.wake()
        for position in (45, 40, 50, 45):
            print(f"Channel 0: command {position}", flush=True)
            servo.move_servo_position(0, position, swing=90)
            delay(2)
    finally:
        bus.writeByte(0x40, 0x09, 0x10)
        print("Channel 0 PWM off.", flush=True)


if __name__ == "__main__":
    import pi_servo_hat
    import qwiic_i2c

    bus = qwiic_i2c.getI2CDriver()
    if bus is None or not bus.isDeviceConnected(0x40):
        raise RuntimeError("Servo pHAT not found at 0x40.")
    try:
        run(bus, pi_servo_hat.PiServoHat)
    except KeyboardInterrupt:
        print("Stopped.")
