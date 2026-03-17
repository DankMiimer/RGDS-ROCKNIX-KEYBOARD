"""
layouts.py — Keyboard layout definitions for all five layers.

Layers: main (lowercase), shift (uppercase), symbols, nav, options.

Numbers are placed as the top row on main/shift/symbols layouts.
Main shows lowercase letters (a, b, c...), shift shows uppercase (A, B, C...).
Options layer has accent color swatches and brightness controls.
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
# Helpers
# =============================================================================

def _key(label, display, keycode, shift=False, width=1.0, action=None, **extra):
    """Build a key definition dict."""
    key = {'l': label, 'd': display, 'c': keycode, 's': shift, 'w': width}
    if action:
        key['a'] = action
    key.update(extra)
    return key


def _row(y, h, keys):
    """Build a row definition dict."""
    return {'y': y, 'h': h, 'keys': keys}


# =============================================================================
# Shared rows
# =============================================================================

def _number_row():
    """Number row — always at the top, y=0, h=48."""
    return _row(0, 48, [
        _key('1', '1', KEY_1), _key('2', '2', KEY_2), _key('3', '3', KEY_3),
        _key('4', '4', KEY_4), _key('5', '5', KEY_5), _key('6', '6', KEY_6),
        _key('7', '7', KEY_7), _key('8', '8', KEY_8), _key('9', '9', KEY_9),
        _key('0', '0', KEY_0),
    ])


# =============================================================================
# Main layout — lowercase display
# =============================================================================

def _build_main():
    return {'name': 'main', 'rows': [
        _number_row(),
        # QWERTY — lowercase display
        _row(51, 88, [
            _key('q', 'q', KEY_Q), _key('w', 'w', KEY_W), _key('e', 'e', KEY_E),
            _key('r', 'r', KEY_R), _key('t', 't', KEY_T), _key('y', 'y', KEY_Y),
            _key('u', 'u', KEY_U), _key('i', 'i', KEY_I), _key('o', 'o', KEY_O),
            _key('p', 'p', KEY_P),
        ]),
        # ASDF — lowercase
        _row(142, 88, [
            _key('a', 'a', KEY_A), _key('s2', 's', KEY_S), _key('d2', 'd', KEY_D),
            _key('f', 'f', KEY_F), _key('g', 'g', KEY_G), _key('h', 'h', KEY_H),
            _key('j', 'j', KEY_J), _key('k', 'k', KEY_K), _key('l2', 'l', KEY_L),
        ]),
        # SHIFT + ZXCV + BKSP — lowercase
        _row(233, 88, [
            _key('shift', 'SHIFT', None, action='shift', width=1.4),
            _key('z', 'z', KEY_Z), _key('x', 'x', KEY_X), _key('c2', 'c', KEY_C),
            _key('v', 'v', KEY_V), _key('b', 'b', KEY_B), _key('n', 'n', KEY_N),
            _key('m', 'm', KEY_M),
            _key('bksp', '\u232B', KEY_BACKSPACE, width=1.4),
        ]),
        # Utility: symbols, comma, SPACE, dot, ENTER
        _row(324, 64, [
            _key('sym', '#+', None, action='symbols', width=1.2),
            _key('comma', ',', KEY_COMMA, width=0.8),
            _key('space', 'SPACE', KEY_SPACE, width=4.0),
            _key('dot', '.', KEY_DOT, width=0.8),
            _key('enter', 'RET', KEY_ENTER, width=1.2),
        ]),
        # Bottom utility: TAB, ESC, NAV, punctuation, OPT
        _row(391, 52, [
            _key('tab', 'TAB', KEY_TAB),
            _key('esc', 'ESC', KEY_ESC),
            _key('nav', 'NAV', None, action='nav'),
            _key('dash', '-', KEY_MINUS, width=0.8),
            _key('qmark', '?', KEY_SLASH, shift=True, width=0.8),
            _key('excl', '!', KEY_1, shift=True, width=0.8),
            _key('opt', '\u2699', None, action='options', width=0.8),
        ]),
    ]}


# =============================================================================
# Shift layout — UPPERCASE display
# =============================================================================

def _build_shift(main_layout):
    rows = []

    # Number row (same)
    rows.append(_number_row())

    # Letter rows 1-2: uppercase display + shift=True for keycode
    for row in main_layout['rows'][1:3]:
        rows.append(_row(row['y'], row['h'], [
            {**k, 'd': k['d'].upper(), 's': True} for k in row['keys']
        ]))

    # Row 3: UNSHIFT + uppercase letters + backspace
    shift_row3_keys = []
    for k in main_layout['rows'][3]['keys']:
        nk = dict(k)
        if nk['l'] == 'shift':
            nk['a'] = 'unshift'
        elif nk['c'] is not None and nk['l'] != 'bksp':
            nk['d'] = nk['d'].upper()
            nk['s'] = True
        shift_row3_keys.append(nk)
    rows.append(_row(233, 88, shift_row3_keys))

    # Space row with ; and :
    rows.append(_row(324, 64, [
        _key('sym', '#+', None, action='symbols', width=1.2),
        _key('semi', ';', KEY_SEMICOLON, width=0.8),
        _key('space', 'SPACE', KEY_SPACE, width=4.0),
        _key('colon', ':', KEY_SEMICOLON, shift=True, width=0.8),
        _key('enter', 'RET', KEY_ENTER, width=1.2),
    ]))

    # Bottom utility (shifted)
    rows.append(_row(391, 52, [
        _key('tab', 'TAB', KEY_TAB),
        _key('esc', 'ESC', KEY_ESC),
        _key('nav', 'NAV', None, action='nav'),
        _key('under', '_', KEY_MINUS, shift=True, width=0.8),
        _key('apos', "'", KEY_APOSTROPHE, width=0.8),
        _key('quot', '"', KEY_APOSTROPHE, shift=True, width=0.8),
        _key('opt', '\u2699', None, action='options', width=0.8),
    ]))

    return {'name': 'shift', 'rows': rows}


# =============================================================================
# Symbols layout
# =============================================================================

def _build_symbols(main_layout):
    symbol_rows = [
        [('!', KEY_1, True), ('@', KEY_2, True), ('#', KEY_3, True),
         ('$', KEY_4, True), ('%', KEY_5, True), ('^', KEY_6, True),
         ('&', KEY_7, True), ('*', KEY_8, True), ('(', KEY_9, True),
         (')', KEY_0, True)],
        [('-', KEY_MINUS, False), ('_', KEY_MINUS, True), ('+', KEY_EQUAL, True),
         ('=', KEY_EQUAL, False), ('[', KEY_LEFTBRACE, False), (']', KEY_RIGHTBRACE, False),
         ('{', KEY_LEFTBRACE, True), ('}', KEY_RIGHTBRACE, True),
         ('|', KEY_BACKSLASH, True), ('\\', KEY_BACKSLASH, False)],
        [(':', KEY_SEMICOLON, True), (';', KEY_SEMICOLON, False),
         ("'", KEY_APOSTROPHE, False), ('"', KEY_APOSTROPHE, True),
         ('`', KEY_GRAVE, False), ('~', KEY_GRAVE, True),
         ('<', KEY_COMMA, True), ('>', KEY_DOT, True),
         ('/', KEY_SLASH, False), ('?', KEY_SLASH, True)],
    ]

    rows = [_number_row()]  # Numbers on top
    y_offsets = [51, 142, 233]
    for i, sym_keys in enumerate(symbol_rows):
        rows.append(_row(y_offsets[i], 88, [
            _key(d, d, c, shift=s) for d, c, s in sym_keys
        ]))

    rows.append(_row(324, 64, [
        _key('abc', 'ABC', None, action='main', width=1.5),
        _key('space', 'SPACE', KEY_SPACE, width=3.5),
        _key('bksp2', '\u232B', KEY_BACKSPACE, width=1.5),
        _key('enter2', 'RET', KEY_ENTER, width=1.5),
    ]))

    rows.append(_row(391, 52, [
        _key('tab', 'TAB', KEY_TAB),
        _key('esc', 'ESC', KEY_ESC),
        _key('nav', 'NAV', None, action='nav'),
        _key('opt', '\u2699', None, action='options', width=0.8),
    ]))

    return {'name': 'symbols', 'rows': rows}


# =============================================================================
# Navigation layout
# =============================================================================

def _build_nav():
    return {'name': 'nav', 'rows': [
        _row(0, 110, [
            _key('home', 'HOME', KEY_HOME), _key('up', '\u2191', KEY_UP),
            _key('end', 'END', KEY_END),    _key('del', 'DEL', KEY_DELETE),
        ]),
        _row(113, 110, [
            _key('left', '\u2190', KEY_LEFT), _key('down', '\u2193', KEY_DOWN),
            _key('right', '\u2192', KEY_RIGHT), _key('ins', 'INS', KEY_INSERT),
        ]),
        _row(226, 90, [
            _key('tab2', 'TAB', KEY_TAB),      _key('esc2', 'ESC', KEY_ESC),
            _key('bksp3', 'BKSP', KEY_BACKSPACE), _key('enter3', 'RET', KEY_ENTER),
        ]),
        _row(319, 68, [
            _key('space', 'SPACE', KEY_SPACE, width=3.0),
            _key('abc2', 'ABC', None, action='main'),
            _key('sym2', '#+', None, action='symbols'),
        ]),
        _row(390, 52, [
            _key('1', '1', KEY_1), _key('2', '2', KEY_2), _key('3', '3', KEY_3),
            _key('4', '4', KEY_4), _key('5', '5', KEY_5), _key('6', '6', KEY_6),
            _key('7', '7', KEY_7), _key('8', '8', KEY_8), _key('9', '9', KEY_9),
            _key('0', '0', KEY_0),
        ]),
    ]}


# =============================================================================
# Options layout — accent color picker + brightness control
# =============================================================================

def _build_options():
    """Options menu with color swatches and brightness controls.

    Key properties:
      - accent_idx: int — which ACCENT_PRESETS entry this swatch represents
      - action: 'accent_N' for color picks, 'bright_up'/'bright_down' for brightness
    """
    return {'name': 'options', 'rows': [
        # Header row: BACK button
        _row(5, 62, [
            _key('opt_back', 'BACK', None, action='main', width=1.5),
            _key('opt_title', 'COLOR', None, width=3.0),  # Non-interactive label
        ]),
        # Color row 1: first 4 presets
        _row(70, 95, [
            _key('accent_0', 'RUBY',   None, action='accent_0', width=1, accent_idx=0),
            _key('accent_1', 'OCEAN',  None, action='accent_1', width=1, accent_idx=1),
            _key('accent_2', 'MINT',   None, action='accent_2', width=1, accent_idx=2),
            _key('accent_3', 'SOLAR',  None, action='accent_3', width=1, accent_idx=3),
        ]),
        # Color row 2: next 4 presets
        _row(168, 95, [
            _key('accent_4', 'VIOLET', None, action='accent_4', width=1, accent_idx=4),
            _key('accent_5', 'LIME',   None, action='accent_5', width=1, accent_idx=5),
            _key('accent_6', 'CORAL',  None, action='accent_6', width=1, accent_idx=6),
            _key('accent_7', 'ICE',    None, action='accent_7', width=1, accent_idx=7),
        ]),
        # Brightness header
        _row(275, 50, [
            _key('br_label', 'BRIGHTNESS', None, width=1.0),
        ]),
        # Brightness controls
        _row(328, 80, [
            _key('br_down', '-', None, action='bright_down', width=1.5),
            _key('br_bar', 'LIGHT', None, width=4.0),  # Display-only brightness indicator
            _key('br_up', '+', None, action='bright_up', width=1.5),
        ]),
        # Bottom back
        _row(415, 55, [
            _key('opt_back2', 'BACK', None, action='main', width=1.0),
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
        'options': _build_options(),
    }
    return layouts
