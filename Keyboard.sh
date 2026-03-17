#!/bin/bash
# RGDS Virtual Keyboard — EmulationStation Ports Toggle

PIDFILE="/tmp/rgds_keyboard.pid"

if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
    kill "$(cat "$PIDFILE")" 2>/dev/null
    sleep 0.3
    kill -9 "$(cat "$PIDFILE")" 2>/dev/null
    rm -f "$PIDFILE"
    swaymsg 'output DSI-1 power off' 2>/dev/null
    echo "Keyboard stopped"
    sleep 1
else
    swaymsg 'output DSI-1 power on' 2>/dev/null
    sleep 0.5
    export SDL_VIDEODRIVER=wayland
    nohup python3 /storage/rgds_keyboard.py > /tmp/rgds_keyboard.log 2>&1 &
    echo $! > "$PIDFILE"
    echo "Keyboard started — press R3 to toggle"
    sleep 2
fi
