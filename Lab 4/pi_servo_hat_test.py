import pi_servo_hat
import time

test = pi_servo_hat.PiServoHat()

test.restart()

test.move_servo_position(0, 0)

time.sleep(1)

test.move_servo_position(0, 90)

time.sleep(1)

while True:
    for i in range(0, 90):
        print(i)
        test.move_servo_position(0, i)
        time.sleep(.001)
    for i in range(90, 0, -1):
        print(i)
        test.move_servo_position(0, i)
        time.sleep(.001)

