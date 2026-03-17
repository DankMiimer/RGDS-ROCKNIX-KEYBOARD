#!/usr/bin/env python3
"""
RGDS Virtual Keyboard — Main Entry Point
=========================================
Phone-style touch keyboard for Anbernic RG DS / ROCKNIX.
Renders on DSI-1 (bottom screen), injects keystrokes via uinput.

Usage:
    python3 rgds_keyboard.py

Toggle keyboard visibility with R3 (right stick click).
"""

import sys

from rgds_kb.engine import run

if __name__ == '__main__':
    sys.exit(run() or 0)
