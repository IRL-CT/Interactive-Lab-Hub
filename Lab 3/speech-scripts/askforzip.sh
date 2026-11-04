
echo "Hello friend, please provide Cornell Tech's zipcode." | python3 -m piper -m en_US-lessac-medium

arecord -d 5 -f cd -c 1 -r 16000 zipanswer.wav
