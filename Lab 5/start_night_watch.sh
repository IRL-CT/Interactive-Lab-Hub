#!/usr/bin/env bash
set -eu
export LANG=C.UTF-8 LC_ALL=C.UTF-8 PYTHONIOENCODING=utf-8
lab_dir=$(cd -- "$(dirname -- "$0")" && pwd)
speech_python="$lab_dir/../Lab 3/.venv/bin/python"
restore_screen=0
handoff_pid=''
if systemctl is-active --quiet piscreen.service; then
    sudo -n systemctl stop piscreen.service
    restore_screen=1
fi
forward_stop() {
    if [ -n "$handoff_pid" ] && kill -0 "$handoff_pid" 2>/dev/null; then
        kill -TERM "$handoff_pid" 2>/dev/null || true
    fi
}
restore_display() {
    forward_stop
    if [ -n "$handoff_pid" ]; then
        wait "$handoff_pid" 2>/dev/null || true
    fi
    if [ "$restore_screen" = 1 ]; then
        sudo -n systemctl start piscreen.service || true
    fi
}
trap restore_display EXIT
trap forward_stop INT TERM HUP
cd "$lab_dir"
"$speech_python" -u "$lab_dir/night_handoff.py" "$@" &
handoff_pid=$!
result=0
wait "$handoff_pid" || result=$?
# A trapped signal interrupts wait before Python has finished its cleanup.
if kill -0 "$handoff_pid" 2>/dev/null; then
    wait "$handoff_pid" || result=$?
fi
exit "$result"
