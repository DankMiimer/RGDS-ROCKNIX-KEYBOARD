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

WINDOW_TITLE = "RGDS Keyboard [Bottom]"
REASSERT_INTERVAL = 1.5

# =============================================================================
# Input constants
# =============================================================================

BTN_THUMBR = 318  # R3 (right stick click) button code

# =============================================================================
# Key repeat timing
# =============================================================================

REPEAT_DELAY = 0.4
REPEAT_RATE = 0.05

REPEATABLE_KEYS = frozenset({
    'bksp', 'bksp2', 'bksp3',
    'space',
    'up', 'down', 'left', 'right',
    'del',
})

# =============================================================================
# Layout geometry
# =============================================================================

GAP = 3
BEVEL = 3   # Pixel-art bevel thickness (chunky 3D edges)
NOTCH = 2   # Corner notch size for pixel-rounded look

# =============================================================================
# Base colors — all (R, G, B, A) tuples
# =============================================================================

COLOR_BACKGROUND    = (12, 12, 20, 255)
COLOR_BLACK         = (0, 0, 0, 255)
COLOR_DIVIDER       = (20, 20, 32, 255)

# Key face colors
COLOR_KEY_LETTER    = (50, 54, 82, 255)       # Letter key face
COLOR_KEY_DEFAULT   = (40, 42, 65, 255)       # Non-letter key face
COLOR_KEY_SPECIAL   = (32, 34, 55, 255)       # Action key face
COLOR_KEY_NUMBER    = (35, 38, 58, 255)       # Number key face

# Pixel-art bevel colors (3D raised effect)
COLOR_BEVEL_LIGHT   = (78, 82, 115, 255)      # Top + left edges (highlight)
COLOR_BEVEL_DARK    = (22, 24, 40, 255)       # Bottom + right edges (shadow)

# Pressed state: inverted bevel (sunken)
COLOR_PRESS_FACE    = (30, 30, 50, 255)       # Sunken face
COLOR_PRESS_LIGHT   = (22, 24, 40, 255)       # Inner top (shadow when pressed)
COLOR_PRESS_DARK    = (60, 64, 90, 255)       # Inner bottom (light when pressed)

# Text colors
COLOR_TEXT_DEFAULT  = (220, 225, 240, 255)
COLOR_TEXT_SPECIAL  = (130, 170, 245, 255)
COLOR_TEXT_NUMBER   = (170, 178, 200, 255)
COLOR_TEXT_DIM      = (90, 95, 120, 255)       # Dimmed text (options labels)

# =============================================================================
# Accent color presets — used for shift-active, pressed highlight, options UI
# =============================================================================

ACCENT_PRESETS = [
    {'name': 'RUBY',    'color': (220, 65, 85, 255),   'hl': (255, 100, 120, 255)},
    {'name': 'OCEAN',   'color': (50, 120, 220, 255),  'hl': (80, 150, 255, 255)},
    {'name': 'MINT',    'color': (45, 185, 140, 255),  'hl': (70, 220, 170, 255)},
    {'name': 'SOLAR',   'color': (230, 160, 40, 255),  'hl': (255, 195, 70, 255)},
    {'name': 'VIOLET',  'color': (140, 70, 200, 255),  'hl': (175, 100, 240, 255)},
    {'name': 'LIME',    'color': (120, 200, 50, 255),  'hl': (155, 235, 80, 255)},
    {'name': 'CORAL',   'color': (240, 128, 100, 255), 'hl': (255, 165, 140, 255)},
    {'name': 'ICE',     'color': (100, 180, 230, 255), 'hl': (140, 210, 255, 255)},
]

DEFAULT_ACCENT_INDEX = 0  # RUBY

# =============================================================================
# Brightness
# =============================================================================

BRIGHTNESS_PATH = "/sys/class/backlight"
BRIGHTNESS_STEP = 15       # Change per tap (out of 255)
BRIGHTNESS_MIN = 5
BRIGHTNESS_MAX = 255

# =============================================================================
# Settings persistence
# =============================================================================

SETTINGS_FILE = "/storage/.rgds_keyboard_settings"

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

EVIOCGRAB = 0x40044590
UI_SET_EVBIT = 0x40045564
UI_SET_KEYBIT = 0x40045565
UI_DEV_CREATE = 0x5501
UI_DEV_DESTROY = 0x5502

# =============================================================================
# Linux keycodes
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
