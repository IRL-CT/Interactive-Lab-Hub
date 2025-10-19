import qwiic_proximity
import time
import sys
import statistics
import vlc
import yt_dlp
import os
import random
# Qwiic GPIO Expander Library
from __future__ import print_function
import qwiic_gpio

# --- CONFIGURATION ---
YOUTUBE_URL = "https://youtu.be/EPo5wWmKEaI?si=P4iQHYS6ml0Li500"
TEMP_FILE = "/tmp/video.mp4"
SAMPLE_WINDOW = 10      # Number of proximity readings to use for standard deviation
MOVEMENT_THRESHOLD = 5  # Standard deviation threshold to detect motion
CHECK_INTERVAL = 0.05   # Loop delay for responsiveness

# List of Qwiic GPIO pins used for active-low LEDs (connected 3.3V to Pin)
LED_PINS = [0, 1, 2, 3] 
# ---------------------

# Global Qwiic GPIO object
myGPIO = None

# --- UTILITY FUNCTIONS ---

def download_video(url):
    """Download YouTube video to a local MP4 file using yt_dlp."""
    print("Downloading video to /tmp/video.mp4 ... (this may take ~30s)")
    ydl_opts = {
        'quiet': True,
        'format': 'best[ext=mp4]/best',
        'outtmpl': TEMP_FILE,
        'noplaylist': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return TEMP_FILE

# -------------------------
# --- GPIO CONTROL FUNCTIONS ---
# -------------------------

def initialize_gpio():
    """Initializes
