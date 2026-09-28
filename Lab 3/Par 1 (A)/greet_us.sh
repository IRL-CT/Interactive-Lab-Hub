

#!/usr/bin/env bash
set -euo pipefail

# Work from the folder containing this script.
cd -- "$(dirname -- "$0")"
mkdir -p results

# Piper is the default. You can choose another engine when running.
ENGINE="${1:-piper}"
GREETING="Hello Afroza, KM, CICI, Lamiah, Welcome! I am so proud of you guys."

case "$ENGINE" in
    espeak)
        espeak -ven+f2 -k5 -s150 --stdout "$GREETING" | aplay
        ;;
    festival)
        printf '%s\n' "$GREETING" | festival --tts
        ;;
    piper)
        python3 -m piper \
            --model en_US-lessac-medium \
            --data-dir ../voices \
            --output-file results/greeting_afroza.wav \
            -- "$GREETING"

        aplay results/greeting_afroza.wav
        ;;
    *)
        echo "Choose an engine: espeak, festival, or piper"
        exit 1
        ;;
esac

