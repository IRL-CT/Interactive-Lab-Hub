say() { local IFS=+;/usr/bin/mplayer -ao alsa -really-quiet -noconsolecontrols "http://translate.google.com/translate_tts?ie=UTF-8&client=tw-ob&q=$*&tl=en"; }
#say $*
say "What's your phone number?"
python test_microphone.py -m en > transcript.txt
say "Thank you! I have recorded your response in transcript dot text" 