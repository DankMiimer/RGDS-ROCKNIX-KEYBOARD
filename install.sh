#!/bin/bash
# RGDS Virtual Keyboard — Installer
# Run this ON the RG DS device via SSH:
#   bash install.sh
set -e

echo "╔══════════════════════════════════════════════╗"
echo "║  RGDS Virtual Keyboard v5 — Installer         ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
KB_DIR="/storage/rgds-keyboard"

# Stop existing instance if running
PIDFILE="/tmp/rgds_keyboard.pid"
if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
    echo "[0/4] Stopping existing keyboard..."
    kill "$(cat "$PIDFILE")" 2>/dev/null; sleep 0.3
    kill -9 "$(cat "$PIDFILE")" 2>/dev/null; rm -f "$PIDFILE"
fi

echo "[1/4] Installing keyboard app to $KB_DIR ..."
mkdir -p "$KB_DIR"
cp "$SCRIPT_DIR/main.py"      "$KB_DIR/main.py"
cp "$SCRIPT_DIR/config.py"    "$KB_DIR/config.py"
cp "$SCRIPT_DIR/devices.py"   "$KB_DIR/devices.py"
cp "$SCRIPT_DIR/font.py"      "$KB_DIR/font.py"
cp "$SCRIPT_DIR/layouts.py"   "$KB_DIR/layouts.py"
cp "$SCRIPT_DIR/renderer.py"  "$KB_DIR/renderer.py"
cp "$SCRIPT_DIR/sdl2.py"      "$KB_DIR/sdl2.py"
cp "$SCRIPT_DIR/uinput_kb.py" "$KB_DIR/uinput_kb.py"
chmod +x "$KB_DIR/main.py"

echo "[2/4] Installing CLI launcher..."
cp "$SCRIPT_DIR/rgds-keyboard.sh" /storage/rgds-keyboard.sh
chmod +x /storage/rgds-keyboard.sh

echo "[3/4] Installing EmulationStation shortcut..."
cp "$SCRIPT_DIR/Keyboard.sh" /storage/roms/ports/Keyboard.sh
chmod +x /storage/roms/ports/Keyboard.sh

echo "[4/4] Done!"
echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║  How to use:                                  ║"
echo "║                                               ║"
echo "║  1. Open EmulationStation                     ║"
echo "║  2. Go to Ports → select 'Keyboard'           ║"
echo "║  3. Press R3 to show/hide the keyboard        ║"
echo "║  4. Select 'Keyboard' again to stop           ║"
echo "║                                               ║"
echo "║  From SSH:                                    ║"
echo "║    bash /storage/rgds-keyboard.sh start       ║"
echo "║    bash /storage/rgds-keyboard.sh stop        ║"
echo "║    bash /storage/rgds-keyboard.sh show        ║"
echo "║    bash /storage/rgds-keyboard.sh hide        ║"
echo "║    bash /storage/rgds-keyboard.sh toggle      ║"
echo "║                                               ║"
echo "║  Signal control (wvkbd-compatible):           ║"
echo "║    kill -USR1 <pid>  → hide                   ║"
echo "║    kill -USR2 <pid>  → show                   ║"
echo "║    kill -RTMIN <pid> → toggle                  ║"
echo "║                                               ║"
echo "║  Themes:                                      ║"
echo "║    Config: /storage/.config/rgds-keyboard/    ║"
echo "║    8 themes: tokyonight, catppuccin, dracula, ║"
echo "║    nord, gruvbox, onedark, solarized, midnight║"
echo "╚══════════════════════════════════════════════╝"
