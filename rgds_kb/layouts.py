"""
layouts.py — Keyboard layout definitions for all four layers.

Each layout is a dict with:
  - name: str — layer identifier ('main', 'shift', 'symbols', 'nav')
  - rows: list of row dicts

Each row dict:
  - y: int — vertical pixel offset from top of screen
  - h: int — row height in pixels
  - keys: list of key dicts

Each key dict:
  - l: str — unique label/ID (used for press tracking and repeat identification)
  - d: str — display string (rendered on the key face)
  - c: int|None — Linux keycode to emit (None for action-only keys)
  - s: bool — whether to hold Shift when emitting this keycode
  - w: float — relative width weight (keys are proportionally sized within the row)
  - a: str|None — (optional) action: 'shift', 'unshift', 'symbols', 'main', 'nav'

To add a new key: append a key dict to the appropriate row's 'keys' list.
To add a new layer: create a new layout dict and return it from build_layouts().
"""

from .constants import (
    KEY_ESC, KEY_1, KEY_2, KEY_3, KEY_4, KEY_5, KEY_6, KEY_7, KEY_8, KEY_9, KEY_0,
    KEY_MINUS, KEY_EQUAL, KEY_BACKSPACE, KEY_TAB,
    KEY_Q, KEY_W, KEY_E, KEY_R, KEY_T, KEY_Y, KEY_U, KEY_I, KEY_O, KEY_P,
    KEY_LEFTBRACE, KEY_RIGHTBRACE, KEY_ENTER,
    KEY_A, KEY_S, KEY_D, KEY_F, KEY_G, KEY_H, KEY_J, KEY_K, KEY_L,
    KEY_SEMICOLON, KEY_APOSTROPHE, KEY_GRAVE, KEY_BACKSLASH,
    KEY_Z, KEY_X, KEY_C, KEY_V, KEY_B, KEY_N, KEY_M,
    KEY_COMMA, KEY_DOT, KEY_SLASH, KEY_SPACE,
    KEY_UP, KEY_DOWN, KEY_LEFT, KEY_RIGHT,
    KEY_HOME, KEY_END, KEY_DELETE, KEY_INSERT,
)

# =============================================================================
# Helper to build a key dict concisely
# =============================================================================

def _key(label, display, keycode, shift=False, width=1.0, action=None):
    """Build a key definition dict.

    Args:
        label:   Unique ID string for this key
        display: Text drawn on the key face
        keycode: Linux KEY_* code, or None for action-only keys
        shift:   If True, Shift is held when emitting the keycode
        width:   Relative width weight (1.0 = standard key)
        action:  Layer-switch action string, or None
    """
    key = {'l': label, 'd': display, 'c': keycode, 's': shift, 'w': width}
    if action:
        key['a'] = action
    return key


def _row(y, h, keys):
    """Build a row definition dict."""
    return {'y': y, 'h': h, 'keys': keys}


# =============================================================================
# Main layout (lowercase QWERTY)
# =============================================================================

def _build_main():
    return {'name': 'main', 'rows': [
        # Row 0: QWERTY top row
        _row(0, 95, [
            _key('q', 'Q', KEY_Q), _key('w', 'W', KEY_W), _key('e', 'E', KEY_E),
            _key('r', 'R', KEY_R), _key('t', 'T', KEY_T), _key('y', 'Y', KEY_Y),
            _key('u', 'U', KEY_U), _key('i', 'I', KEY_I), _key('o', 'O', KEY_O),
            _key('p', 'P', KEY_P),
        ]),
        # Row 1: ASDF middle row
        _row(98, 95, [
            _key('a', 'A', KEY_A), _key('s2', 'S', KEY_S), _key('d2', 'D', KEY_D),
            _key('f', 'F', KEY_F), _key('g', 'G', KEY_G), _key('h', 'H', KEY_H),
            _key('j', 'J', KEY_J), _key('k', 'K', KEY_K), _key('l2', 'L', KEY_L),
        ]),
        # Row 2: SHIFT + ZXCV + BACKSPACE
        _row(196, 95, [
            _key('shift', 'SHIFT', None, action='shift', width=1.4),
            _key('z', 'Z', KEY_Z), _key('x', 'X', KEY_X), _key('c2', 'C', KEY_C),
            _key('v', 'V', KEY_V), _key('b', 'B', KEY_B), _key('n', 'N', KEY_N),
            _key('m', 'M', KEY_M),
            _key('bksp', '\u232B', KEY_BACKSPACE, width=1.4),
        ]),
        # Row 3: Symbols toggle, comma, SPACE, dot, ENTER
        _row(294, 75, [
            _key('sym', '#+', None, action='symbols', width=1.2),
            _key('comma', ',', KEY_COMMA, width=0.8),
            _key('space', 'SPACE', KEY_SPACE, width=4.5),
            _key('dot', '.', KEY_DOT, width=0.8),
            _key('enter', 'RET', KEY_ENTER, width=1.2),
        ]),
        # Row 4: Number row
        _row(372, 50, [
            _key('1', '1', KEY_1), _key('2', '2', KEY_2), _key('3', '3', KEY_3),
            _key('4', '4', KEY_4), _key('5', '5', KEY_5), _key('6', '6', KEY_6),
            _key('7', '7', KEY_7), _key('8', '8', KEY_8), _key('9', '9', KEY_9),
            _key('0', '0', KEY_0),
        ]),
        # Row 5: Utility row
        _row(425, 52, [
            _key('tab', 'TAB', KEY_TAB),
            _key('esc', 'ESC', KEY_ESC),
            _key('nav', 'NAV', None, action='nav'),
            _key('dash', '-', KEY_MINUS, width=0.8),
            _key('qmark', '?', KEY_SLASH, shift=True, width=0.8),
            _key('excl', '!', KEY_1, shift=True, width=0.8),
            _key('at', '@', KEY_2, shift=True, width=0.8),
        ]),
    ]}


# =============================================================================
# Shift layout (uppercase + shifted symbols)
# =============================================================================

def _build_shift(main_layout):
    rows = []

    # Rows 0-1: same letter keys but with shift=True
    for row in main_layout['rows'][:2]:
        rows.append(_row(row['y'], row['h'], [
            {**k, 's': True} for k in row['keys']
        ]))

    # Row 2: UNSHIFT + shifted letters + backspace
    shift_row2_keys = []
    for k in main_layout['rows'][2]['keys']:
        nk = dict(k)
        if nk['l'] == 'shift':
            nk['a'] = 'unshift'
        elif nk['c'] is not None and nk['l'] != 'bksp':
            nk['s'] = True
        shift_row2_keys.append(nk)
    rows.append(_row(196, 95, shift_row2_keys))

    # Row 3: Symbols toggle, semicolon, SPACE, colon, ENTER
    rows.append(_row(294, 75, [
        _key('sym', '#+', None, action='symbols', width=1.2),
        _key('semi', ';', KEY_SEMICOLON, width=0.8),
        _key('space', 'SPACE', KEY_SPACE, width=4.5),
        _key('colon', ':', KEY_SEMICOLON, shift=True, width=0.8),
        _key('enter', 'RET', KEY_ENTER, width=1.2),
    ]))

    # Row 4: Shifted number row → ! @ # $ % ^ & * ( )
    shifted_symbols = ['!', '@', '#', '$', '%', '^', '&', '*', '(', ')']
    rows.append(_row(372, 50, [
        {**dict(k), 'd': shifted_symbols[i], 's': True}
        for i, k in enumerate(main_layout['rows'][4]['keys'])
    ]))

    # Row 5: Shifted utility row
    rows.append(_row(425, 52, [
        _key('tab', 'TAB', KEY_TAB),
        _key('esc', 'ESC', KEY_ESC),
        _key('nav', 'NAV', None, action='nav'),
        _key('under', '_', KEY_MINUS, shift=True, width=0.8),
        _key('apos', "'", KEY_APOSTROPHE, width=0.8),
        _key('quot', '"', KEY_APOSTROPHE, shift=True, width=0.8),
        _key('hash', '#', KEY_3, shift=True, width=0.8),
    ]))

    return {'name': 'shift', 'rows': rows}


# =============================================================================
# Symbols layout (brackets, punctuation, operators)
# =============================================================================

def _build_symbols(main_layout):
    # Three rows of symbol pairs: (display_char, keycode, shift_required)
    symbol_rows = [
        # Row 0
        [('!', KEY_1, True), ('@', KEY_2, True), ('#', KEY_3, True),
         ('$', KEY_4, True), ('%', KEY_5, True), ('^', KEY_6, True),
         ('&', KEY_7, True), ('*', KEY_8, True), ('(', KEY_9, True),
         (')', KEY_0, True)],
        # Row 1
        [('-', KEY_MINUS, False), ('_', KEY_MINUS, True), ('+', KEY_EQUAL, True),
         ('=', KEY_EQUAL, False), ('[', KEY_LEFTBRACE, False), (']', KEY_RIGHTBRACE, False),
         ('{', KEY_LEFTBRACE, True), ('}', KEY_RIGHTBRACE, True),
         ('|', KEY_BACKSLASH, True), ('\\', KEY_BACKSLASH, False)],
        # Row 2
        [(':', KEY_SEMICOLON, True), (';', KEY_SEMICOLON, False),
         ("'", KEY_APOSTROPHE, False), ('"', KEY_APOSTROPHE, True),
         ('`', KEY_GRAVE, False), ('~', KEY_GRAVE, True),
         ('<', KEY_COMMA, True), ('>', KEY_DOT, True),
         ('/', KEY_SLASH, False), ('?', KEY_SLASH, True)],
    ]

    rows = []
    y_positions = [0, 98, 196]
    for i, sym_keys in enumerate(symbol_rows):
        rows.append(_row(y_positions[i], 95, [
            _key(d, d, c, shift=s) for d, c, s in sym_keys
        ]))

    # Row 3: ABC return, SPACE, BKSP, ENTER
    rows.append(_row(294, 75, [
        _key('abc', 'ABC', None, action='main', width=1.5),
        _key('space', 'SPACE', KEY_SPACE, width=4.0),
        _key('bksp2', '\u232B', KEY_BACKSPACE, width=1.5),
        _key('enter2', 'RET', KEY_ENTER, width=1.5),
    ]))

    # Row 4: Number row (same as main)
    rows.append(dict(main_layout['rows'][4]))

    # Row 5: Minimal utility
    rows.append(_row(425, 52, [
        _key('tab', 'TAB', KEY_TAB),
        _key('esc', 'ESC', KEY_ESC),
        _key('nav', 'NAV', None, action='nav'),
    ]))

    return {'name': 'symbols', 'rows': rows}


# =============================================================================
# Navigation layout (arrows, home/end, insert/delete)
# =============================================================================

def _build_nav():
    return {'name': 'nav', 'rows': [
        _row(0, 120, [
            _key('home', 'HOME', KEY_HOME), _key('up', '\u2191', KEY_UP),
            _key('end', 'END', KEY_END),    _key('del', 'DEL', KEY_DELETE),
        ]),
        _row(123, 120, [
            _key('left', '\u2190', KEY_LEFT), _key('down', '\u2193', KEY_DOWN),
            _key('right', '\u2192', KEY_RIGHT), _key('ins', 'INS', KEY_INSERT),
        ]),
        _row(246, 100, [
            _key('tab2', 'TAB', KEY_TAB),      _key('esc2', 'ESC', KEY_ESC),
            _key('bksp3', 'BKSP', KEY_BACKSPACE), _key('enter3', 'RET', KEY_ENTER),
        ]),
        _row(349, 68, [
            _key('space', 'SPACE', KEY_SPACE, width=3.0),
            _key('abc2', 'ABC', None, action='main'),
            _key('sym2', '#+', None, action='symbols'),
        ]),
        _row(420, 57, [
            _key('1', '1', KEY_1), _key('2', '2', KEY_2), _key('3', '3', KEY_3),
            _key('4', '4', KEY_4), _key('5', '5', KEY_5), _key('6', '6', KEY_6),
            _key('7', '7', KEY_7), _key('8', '8', KEY_8), _key('9', '9', KEY_9),
            _key('0', '0', KEY_0),
        ]),
    ]}


# =============================================================================
# Public API
# =============================================================================

def build_layouts():
    """Build and return all keyboard layouts.

    Returns:
        dict mapping layout name → layout dict
    """
    main = _build_main()
    layouts = {
        'main': main,
        'shift': _build_shift(main),
        'symbols': _build_symbols(main),
        'nav': _build_nav(),
    }
    return layouts
