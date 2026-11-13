#!/bin/bash
# Part G: the hand-off. Start the night shift with one command.
cd "$(dirname "$0")"
source .venv/bin/activate
if [ -f night_log.jsonl ]; then
    mv night_log.jsonl "night_log_$(date +%Y%m%d-%H%M).jsonl"
fi
echo "Shh... they're waking up. Good night."
python overnight.py --all --interval 10
