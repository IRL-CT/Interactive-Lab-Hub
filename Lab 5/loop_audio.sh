#!/bin/bash

# Function to handle termination signals
cleanup() {
  kill $APLAY_PID 2>/dev/null  # Terminate the aplay process
  exit 0
}

trap cleanup TERM INT  # Set up signal handlers

while :
do
    aplay -D pulse ../Lab\ 4/music/spring-mood-wav-212731_fixed.wav &
    APLAY_PID=$!
    wait $APLAY_PID
done
