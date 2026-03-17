#!/bin/bash
# RGDS Virtual Keyboard — Installer
# Run this ON the RG DS device via SSH:
#   bash install.sh
set -e

echo "╔══════════════════════════════════════════════╗"
echo "║  RGDS Virtual Keyboard — Installer           ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "[1/3] Installing keyboard app to /storage/ ..."
cp "$SCRIPT_DIR/rgds_keyboard.py" /storage/rgds_keyboard.py
cp "$SCRIPT_DIR/rgds-keyboard.sh" /storage/rgds-keyboard.sh
chmod +x /storage/rgds_keyboard.py /storage/rgds-keyboard.sh

echo "[2/3] Installing EmulationStation shortcut ..."
cp "$SCRIPT_DIR/Keyboard.sh" /storage/roms/ports/Keyboard.sh
chmod +x /storage/roms/ports/Keyboard.sh

echo "[3/3] Done!"
echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║  How to use:                                  ║"
echo "║                                               ║"
echo "║  1. Open EmulationStation                     ║"
echo "║  2. Go to Ports                               ║"
echo "║  3. Select 'Keyboard' to start                ║"
echo "║  4. Press R3 to show/hide the keyboard        ║"
echo "║  5. Select 'Keyboard' again to stop           ║"
echo "║                                               ║"
echo "║  Or from SSH:                                 ║"
echo "║    bash /storage/rgds-keyboard.sh start       ║"
echo "║    bash /storage/rgds-keyboard.sh stop        ║"
echo "╚══════════════════════════════════════════════╝"
