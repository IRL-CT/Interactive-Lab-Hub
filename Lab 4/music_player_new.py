#!/usr/bin/env python3
import os, sys, time, glob
import qwiic_gpio
import pygame
import subprocess

LED_PINS = [6, 7, 0, 5, 3, 4]
ENCODER_PINS = {'CLK': 1, 'DT': 2}
MIN_VOL, MAX_VOL = 0, 100
STEP = 10

def find_wav():
    base = os.path.dirname(__file__) if "__file__" in globals() else os.getcwd()
    files = sorted(glob.glob(os.path.join(base, "music", "*_fixed.wav")))
    return files[0] if files else None

def set_system_volume(volume):
    subprocess.run(["amixer", "sset", "Master", f"{volume}%"],
                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def update_leds(io, volume):
    num_leds = len(LED_PINS)
    led_step = MAX_VOL / num_leds
    led_count = int(volume / led_step)
    
    for i, pin in enumerate(LED_PINS):
        if i < led_count:
            io.digitalWrite(pin, io.GPIO_LO)  # Turn on LED
        else:
            io.digitalWrite(pin, io.GPIO_HI)  # Turn off LED

def main():
    wav_file = find_wav()
    if not wav_file:
        print("No _fixed.wav found")
        return

    io = qwiic_gpio.QwiicGPIO()
    if not io.isConnected():
        print("GPIO not connected")
        return
    
    io.begin()
    
    for pin in LED_PINS:
        io.pinMode(pin, io.GPIO_OUT)
        io.digitalWrite(pin, io.GPIO_HI)
    
    io.pinMode(ENCODER_PINS['CLK'], io.GPIO_IN)
    io.pinMode(ENCODER_PINS['DT'], io.GPIO_IN)
    
    pygame.mixer.init()
    pygame.mixer.music.load(wav_file)
    pygame.mixer.music.play(-1)
    
    volume = 50
    last_clk = io.digitalRead(ENCODER_PINS['CLK'])
    last_dt = io.digitalRead(ENCODER_PINS['DT'])
    
    pygame.mixer.music.set_volume(volume / 100.0)
    set_system_volume(volume)
    update_leds(io, volume)

    print("Running... Press Ctrl+C to exit")
    print(f"Initial volume: {volume}")
    
    try:
        while True:
            current_clk = io.digitalRead(ENCODER_PINS['CLK'])
            
            if current_clk != last_clk:
                current_dt = io.digitalRead(ENCODER_PINS['DT'])
                if last_clk == 0 and current_clk == 1:
                    if current_dt == 0:
                        volume = min(MAX_VOL, volume + STEP)
                    else:
                        volume = max(MIN_VOL, volume - STEP)
                    
                    print(f"Volume: {volume}")
                    pygame.mixer.music.set_volume(volume / 100.0)
                    set_system_volume(volume)
                    update_leds(io, volume)
            
            last_clk = current_clk
            time.sleep(0.001)
            
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        for pin in LED_PINS:
            io.digitalWrite(pin, io.GPIO_HI)

if __name__ == "__main__":
    main()