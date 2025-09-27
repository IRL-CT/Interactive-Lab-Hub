espeak "Please say your zip code. You have five seconds."

arecord -D plughw:2,0 -f cd -t wav -d 5 answer.wav

espeak "Recording complete. Thank you."
