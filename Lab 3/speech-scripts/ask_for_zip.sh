#!/bin/bash
set -e

echo "Asking for a number..."
espeak-ng "Please say your five-digit zip code." -w prompt.wav
aplay prompt.wav

arecord -d 5 -f cd -c 1 -r 16000 zip_answer.wav

echo "Transcribing..."
python transcribe.py zip_answer.wav --model tiny.en
python transcribe.py zip_answer.wav --model base.en
python transcribe.py zip_answer.wav --model small.en