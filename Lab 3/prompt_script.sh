#!/bin/bash

# This script prompts the user for a numerical input and records the response.

echo "Hello! I am ready to record a numerical value from you."
echo "Please enter a numerical value (e.g., your phone number, number of pets, etc.) and press Enter:"

read user_input

echo "Thank you. I have recorded the following value: $user_input"
echo "$user_input" >> recorded_data.txt
exit 0
