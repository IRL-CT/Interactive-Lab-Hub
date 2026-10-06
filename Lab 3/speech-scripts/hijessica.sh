#!/bin/bash

echo "Hi Jessica! I'm speaking to you right now in lab 3." | python3 -m piper -m en_US-lessac-medium --output-raw | aplay -D plughw:UACDemoV10,0 -f S16_LE -r 22050 -c 1

