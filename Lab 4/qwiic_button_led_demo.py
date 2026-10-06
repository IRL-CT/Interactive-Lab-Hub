import qwiic_button
import time
import sys

# Example: Use two Qwiic buttons and their LEDs interactively
# - Pressing button 1 toggles its own LED
# - Pressing button 2 toggles both LEDs

def run_example():
    print("\nQwiic Button + LED Demo: Two Buttons, Two LEDs")
    my_button1 = qwiic_button.QwiicButton()
    my_button2 = qwiic_button.QwiicButton(0x6E)

    if not my_button1.begin():
        print("\nThe Qwiic Button 1 isn't connected. Check your connection.", file=sys.stderr)
        return
    if not my_button2.begin():
        print("\nThe Qwiic Button 2 isn't connected. Check your connection.", file=sys.stderr)
        return
    print("\nButtons ready! Press to toggle LEDs.")

    led1_on = False
    led2_on = False
    while True:
        # Button 1 toggles its own LED
        if my_button1.is_button_pressed():
            led1_on = not led1_on
            my_button1.LED_on(led1_on)
            print(f"Button 1 pressed! LED 1 is now {'ON' if led1_on else 'OFF'}.")
            # Wait for release to avoid rapid toggling
            while my_button1.is_button_pressed():
                time.sleep(0.02)
        # Button 2 toggles both LEDs
        if my_button2.is_button_pressed():
            led1_on = not led1_on
            led2_on = not led2_on
            my_button1.LED_on(led1_on)
            my_button2.LED_on(led2_on)
            print(f"Button 2 pressed! LED 1: {'ON' if led1_on else 'OFF'}, LED 2: {'ON' if led2_on else 'OFF'}.")
            while my_button2.is_button_pressed():
                time.sleep(0.02)
        time.sleep(0.05)

if __name__ == '__main__':
    try:
        run_example()
    except (KeyboardInterrupt, SystemExit):
        print("\nEnding Qwiic Button + LED Demo")
        sys.exit(0)
