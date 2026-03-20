#!/bin/bash
# RGDS Virtual Keyboard — CLI Launcher
PIDFILE="/tmp/rgds_keyboard.pid"
KB_DIR="/storage/rgds-keyboard"

start_keyboard() {
    if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
        echo "Already running (PID $(cat "$PIDFILE"))"; return
    fi
    swaymsg 'output DSI-1 power on' 2>/dev/null
    sleep 0.5
    export SDL_VIDEODRIVER=wayland
    nohup python3 "$KB_DIR/main.py" > /tmp/rgds_keyboard.log 2>&1 &
    echo $! > "$PIDFILE"
    echo "Keyboard started (PID $!) — press R3 to toggle"
}

stop_keyboard() {
    if [ -f "$PIDFILE" ]; then
        kill "$(cat "$PIDFILE")" 2>/dev/null; sleep 0.3
        kill -9 "$(cat "$PIDFILE")" 2>/dev/null; rm -f "$PIDFILE"
    else
        pkill -f "rgds-keyboard/main.py" 2>/dev/null
    fi
    echo "Keyboard stopped"
}

show_keyboard() {
    if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
        kill -USR2 "$(cat "$PIDFILE")" 2>/dev/null
        echo "Keyboard shown"
    else
        echo "Keyboard not running"
    fi
}

hide_keyboard() {
    if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
        kill -USR1 "$(cat "$PIDFILE")" 2>/dev/null
        echo "Keyboard hidden"
    else
        echo "Keyboard not running"
    fi
}

toggle_keyboard() {
    if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
        kill -RTMIN "$(cat "$PIDFILE")" 2>/dev/null
        echo "Keyboard toggled"
    else
        echo "Keyboard not running"
    fi
}

case "${1:-start}" in
    start)   start_keyboard ;;
    stop)    stop_keyboard ;;
    restart) stop_keyboard; sleep 0.5; start_keyboard ;;
    show)    show_keyboard ;;
    hide)    hide_keyboard ;;
    toggle)  toggle_keyboard ;;
    *)       echo "Usage: $0 {start|stop|restart|show|hide|toggle}" ;;
esac
