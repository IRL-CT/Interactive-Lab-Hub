import digitalio
import board

pin = digitalio.DigitalInOut(board.D25)
pin.direction = digitalio.Direction.OUTPUT
print("Blinka + digitalio working!")