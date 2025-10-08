# Greetings script

#!/bin/bash
say() { local IFS=+;/usr/bin/mplayer -ao alsa -really-quiet -noconsolecontrols "http://translate.google.com/translate_tts?ie=UTF-8&client=tw-ob&q=$*&tl=en"; }
#say $*
TIME=$(date +"%H:%M")
say "Hello, right now is $TIME. Welcome to the Raspberry Pi world."

