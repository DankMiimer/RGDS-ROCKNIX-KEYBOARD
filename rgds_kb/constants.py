"""
constants.py — All configuration values, keycodes, colors, and dimensions.

Edit this file to change colors, timing, screen resolution, device paths, etc.
"""

import struct

# =============================================================================
# Device paths (hardcoded for Anbernic RG DS / ROCKNIX)
# =============================================================================

TOUCH_DEVICE = "/dev/input/event2"    # Goodix capacitive touchscreen
JOYPAD_DEVICE = "/dev/input/event6"   # Gamepad (R3 stick click)

# =============================================================================
# Screen dimensions (bottom screen, DSI-1)
# =============================================================================

SCREEN_WIDTH = 640
SCREEN_HEIGHT = 480

# =============================================================================
# Window / Sway integration
# =============================================================================

# Title must contain "[Bottom]" for ROCKNIX sway rule to route to DSI-1
WINDOW_TITLE = "RGDS Keyboard [Bottom]"

# How often (seconds) to re-assert DSI-1 power and fullscreen placement.
# EmulationStation turns off DSI-1 when launching apps; this counters that.
REASSERT_INTERVAL = 1.5

# =============================================================================
# Input constants
# =============================================================================

BTN_THUMBR = 318  # R3 (right stick click) button code

# =============================================================================
# Key repeat timing
# =============================================================================

REPEAT_DELAY = 0.4   # Seconds before repeat starts
REPEAT_RATE = 0.05    # Seconds between repeated keystrokes

# Keys that support held-key repeat (identified by their label/ID)
REPEATABLE_KEYS = frozenset({
    'bksp', 'bksp2', 'bksp3',
    'space',
    'up', 'down', 'left', 'right',
    'del',
})

# =============================================================================
# Layout geometry
# =============================================================================

GAP = 3  # Pixel gap between keys and screen edge

# =============================================================================
# Colors — all (R, G, B, A) tuples
# =============================================================================

COLOR_BACKGROUND    = (15, 15, 25, 255)      # Dark blue-black canvas
COLOR_KEY_LETTER    = (48, 52, 82, 255)       # Letter key background
COLOR_KEY_LETTER_HL = (58, 63, 98, 255)       # Letter key top highlight strip
COLOR_KEY_DEFAULT   = (38, 40, 62, 255)       # Non-letter key background
COLOR_KEY_SPECIAL   = (30, 32, 50, 255)       # Special/action key background
COLOR_KEY_ACTIVE    = (65, 50, 90, 255)       # Shift key when active
COLOR_KEY_PRESSED   = (220, 65, 85, 255)      # Any key while finger is down
COLOR_TEXT_DEFAULT  = (215, 220, 235, 255)     # Default key label text
COLOR_TEXT_SPECIAL  = (130, 170, 245, 255)     # Special key label text (blue)
COLOR_TEXT_NUMBER   = (180, 185, 200, 255)     # Number key label text
COLOR_BORDER        = (55, 58, 88, 255)        # Key border outline
COLOR_BLACK         = (0, 0, 0, 255)           # Blank screen fill
COLOR_DIVIDER       = (25, 25, 40, 255)        # Row divider line

# =============================================================================
# evdev / input_event struct
# =============================================================================

INPUT_EVENT_FORMAT = 'llHHi'
INPUT_EVENT_SIZE = struct.calcsize(INPUT_EVENT_FORMAT)

EV_SYN = 0x00
EV_KEY = 0x01
EV_ABS = 0x03

ABS_MT_TRACKING_ID = 0x39
ABS_MT_POSITION_X = 0x35
ABS_MT_POSITION_Y = 0x36
BTN_TOUCH = 330

# ioctl codes
EVIOCGRAB = 0x40044590
UI_SET_EVBIT = 0x40045564
UI_SET_KEYBIT = 0x40045565
UI_DEV_CREATE = 0x5501
UI_DEV_DESTROY = 0x5502

# =============================================================================
# Linux keycodes (subset used by the keyboard)
# =============================================================================

KEY_ESC = 1
KEY_1 = 2;  KEY_2 = 3;  KEY_3 = 4;  KEY_4 = 5;  KEY_5 = 6
KEY_6 = 7;  KEY_7 = 8;  KEY_8 = 9;  KEY_9 = 10; KEY_0 = 11
KEY_MINUS = 12;   KEY_EQUAL = 13;     KEY_BACKSPACE = 14
KEY_TAB = 15
KEY_Q = 16; KEY_W = 17; KEY_E = 18; KEY_R = 19; KEY_T = 20
KEY_Y = 21; KEY_U = 22; KEY_I = 23; KEY_O = 24; KEY_P = 25
KEY_LEFTBRACE = 26; KEY_RIGHTBRACE = 27
KEY_ENTER = 28;     KEY_LEFTCTRL = 29
KEY_A = 30; KEY_S = 31; KEY_D = 32; KEY_F = 33; KEY_G = 34
KEY_H = 35; KEY_J = 36; KEY_K = 37; KEY_L = 38
KEY_SEMICOLON = 39; KEY_APOSTROPHE = 40; KEY_GRAVE = 41
KEY_LEFTSHIFT = 42; KEY_BACKSLASH = 43
KEY_Z = 44; KEY_X = 45; KEY_C = 46; KEY_V = 47; KEY_B = 48
KEY_N = 49; KEY_M = 50
KEY_COMMA = 51; KEY_DOT = 52; KEY_SLASH = 53
KEY_LEFTALT = 56;   KEY_SPACE = 57
KEY_UP = 103;   KEY_LEFT = 105; KEY_RIGHT = 106; KEY_DOWN = 108
KEY_HOME = 102; KEY_END = 107;  KEY_DELETE = 111; KEY_INSERT = 110

# All keycodes to register with uinput
ALL_KEYCODES = [
    KEY_ESC, KEY_1, KEY_2, KEY_3, KEY_4, KEY_5, KEY_6, KEY_7, KEY_8, KEY_9,
    KEY_0, KEY_MINUS, KEY_EQUAL, KEY_BACKSPACE, KEY_TAB,
    KEY_Q, KEY_W, KEY_E, KEY_R, KEY_T, KEY_Y, KEY_U, KEY_I, KEY_O, KEY_P,
    KEY_LEFTBRACE, KEY_RIGHTBRACE, KEY_ENTER, KEY_LEFTCTRL,
    KEY_A, KEY_S, KEY_D, KEY_F, KEY_G, KEY_H, KEY_J, KEY_K, KEY_L,
    KEY_SEMICOLON, KEY_APOSTROPHE, KEY_GRAVE, KEY_LEFTSHIFT, KEY_BACKSLASH,
    KEY_Z, KEY_X, KEY_C, KEY_V, KEY_B, KEY_N, KEY_M,
    KEY_COMMA, KEY_DOT, KEY_SLASH, KEY_LEFTALT, KEY_SPACE,
    KEY_LEFT, KEY_RIGHT, KEY_UP, KEY_DOWN, KEY_HOME, KEY_END,
    KEY_DELETE, KEY_INSERT,
]
