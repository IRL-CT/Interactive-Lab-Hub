# **Write your own shell file to use your favorite of these TTS engines to have your Pi greet you by name.** (This shell file should be saved to your own repo for this lab.)
#Edit the permission if you don't have it to add +x 
echo "What is your phone number?" | festival --tts
echo "Speak after the beep. We will record until we hear 10 digits." | festival --tts
echo "Beep!" | festival --tts
python ask_phone_number.py 
NUMBER=$(cat phone.txt)
echo "Your phone number is: $NUMBER" | festival --tts
echo "Thank you!" | festival --tts

#I also wrote only using bash script to do the similar thing

# arecord -D pulse -f S16_LE -r16000 -c1 -t wav -d 10 temp.wav
# vosk-transcriber -i temp.wav -o number_in_text.txt
# tr 'A-Z' 'a-z' < number_in_text.txt | \
# sed -E 's/zero/0/g; s/one/1/g; s/two/2/g; s/three/3/g; s/four/4/g; s/five/5/g; s/six/6/g; s/seven/7/g; s/eight/8/g; s/nine/9/g' | \
# tr -d ' ' > number.txt