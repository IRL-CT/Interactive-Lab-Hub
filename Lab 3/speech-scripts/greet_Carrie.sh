#https://elinux.org/RPi_Text_to_Speech_(Speech_Synthesis)

#!/bin/bash
espeak -ven+f2 -k5 -s150 --stdout  "Hi Carrie! How are you today?" | aplay


 
