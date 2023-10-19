#!/bin/bash

# Function to handle termination signals
cleanup() {
  kill $APLAY_PID 2>/dev/null  # Terminate the aplay process
  exit 0
}

trap cleanup TERM INT  # Set up signal handlers

while :
do
    aplay -D hw:3,0 Peaceful_Mind.wav &
    APLAY_PID=$!  # Store the PID of the aplay process
    wait $APLAY_PID  # Wait for the aplay process to complete
done
