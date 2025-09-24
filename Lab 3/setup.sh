#!/bin/bash

# Function to print a message and install a package
install_package() {
    echo "Installing $1..."
    shift  # Shift to get the rest of the arguments
    echo "Y" | "$@"  # Run the command, piping 'Y' for approval
    echo "$1 installed!"
}

# Install pip package
# echo "Installing piper-tts via pip for local user..."
# pip install piper-tts --user
# echo "piper-tts installed!"

# Install packages using apt-get
install_package "festival" sudo apt-get install festival
install_package "espeak" sudo apt-get install espeak
install_package "mplayer" sudo apt-get install mplayer
install_package "mpg123" sudo apt-get install mpg123
install_package "libttspico-utils" sudo apt-get install libttspico-utils

# Change all scripts in the subfolder 'speech-scripts' to be executable
echo "Making all scripts in the 'speech-scripts' subfolder executable..."
chmod u+x ./speech-scripts/*
echo "Scripts are now executable!"

echo "All tasks completed!"
