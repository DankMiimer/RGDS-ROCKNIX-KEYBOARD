"""
layouts.py — Keyboard layout definitions for all five layers.

Rows fill the entire 480px screen height with no black bar:
  Numbers (top):  y=0,   h=56  — slightly taller for easy tapping
  QWERTY:         y=58,  h=86
  ASDF:           y=146, h=86
  ZXCV:           y=234, h=86
  Space row:      y=322, h=78  — taller for thumb comfort
  Utility:        y=402, h=78  — fills to bottom edge (480)
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


def _key(label, display, keycode, shift=False, width=1.0, action=None, **extra):
    key = {'l': label, 'd': display, 'c': keycode, 's': shift, 'w': width}
    if action:
        key['a'] = action
    key.update(extra)
    return key


def _row(y, h, keys):
    return {'y': y, 'h': h, 'keys': keys}


# Row Y/H constants (shared across main/shift/symbols)
_NUM_Y, _NUM_H     = 0, 56      # Numbers — taller
_QW_Y,  _QW_H      = 58, 86     # QWERTY
_AS_Y,  _AS_H      = 146, 86    # ASDF
_ZX_Y,  _ZX_H      = 234, 86    # ZXCV
_SP_Y,  _SP_H      = 322, 78    # Space — taller
_UT_Y,  _UT_H      = 402, 78    # Utility — fills to 480


def _number_row():
    return _row(_NUM_Y, _NUM_H, [
        _key('1', '1', KEY_1), _key('2', '2', KEY_2), _key('3', '3', KEY_3),
        _key('4', '4', KEY_4), _key('5', '5', KEY_5), _key('6', '6', KEY_6),
        _key('7', '7', KEY_7), _key('8', '8', KEY_8), _key('9', '9', KEY_9),
        _key('0', '0', KEY_0),
    ])


# =============================================================================
# Main — lowercase
# =============================================================================

def _build_main():
    return {'name': 'main', 'rows': [
        _number_row(),
        _row(_QW_Y, _QW_H, [
            _key('q', 'q', KEY_Q), _key('w', 'w', KEY_W), _key('e', 'e', KEY_E),
            _key('r', 'r', KEY_R), _key('t', 't', KEY_T), _key('y', 'y', KEY_Y),
            _key('u', 'u', KEY_U), _key('i', 'i', KEY_I), _key('o', 'o', KEY_O),
            _key('p', 'p', KEY_P),
        ]),
        _row(_AS_Y, _AS_H, [
            _key('a', 'a', KEY_A), _key('s2', 's', KEY_S), _key('d2', 'd', KEY_D),
            _key('f', 'f', KEY_F), _key('g', 'g', KEY_G), _key('h', 'h', KEY_H),
            _key('j', 'j', KEY_J), _key('k', 'k', KEY_K), _key('l2', 'l', KEY_L),
        ]),
        _row(_ZX_Y, _ZX_H, [
            _key('shift', 'SHIFT', None, action='shift', width=1.4),
            _key('z', 'z', KEY_Z), _key('x', 'x', KEY_X), _key('c2', 'c', KEY_C),
            _key('v', 'v', KEY_V), _key('b', 'b', KEY_B), _key('n', 'n', KEY_N),
            _key('m', 'm', KEY_M),
            _key('bksp', '\u232B', KEY_BACKSPACE, width=1.4),
        ]),
        _row(_SP_Y, _SP_H, [
            _key('sym', '#+', None, action='symbols', width=1.2),
            _key('comma', ',', KEY_COMMA, width=0.8),
            _key('space', 'SPACE', KEY_SPACE, width=4.0),
            _key('dot', '.', KEY_DOT, width=0.8),
            _key('enter', 'RET', KEY_ENTER, width=1.2),
        ]),
        _row(_UT_Y, _UT_H, [
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
# Shift — UPPERCASE
# =============================================================================

def _build_shift(main_layout):
    rows = [_number_row()]

    # Letter rows: uppercase display + shift=True
    for row in main_layout['rows'][1:3]:
        rows.append(_row(row['y'], row['h'], [
            {**k, 'd': k['d'].upper(), 's': True} for k in row['keys']
        ]))

    # UNSHIFT + uppercase + backspace
    shift_row3 = []
    for k in main_layout['rows'][3]['keys']:
        nk = dict(k)
        if nk['l'] == 'shift':
            nk['a'] = 'unshift'
        elif nk['c'] is not None and nk['l'] != 'bksp':
            nk['d'] = nk['d'].upper()
            nk['s'] = True
        shift_row3.append(nk)
    rows.append(_row(_ZX_Y, _ZX_H, shift_row3))

    rows.append(_row(_SP_Y, _SP_H, [
        _key('sym', '#+', None, action='symbols', width=1.2),
        _key('semi', ';', KEY_SEMICOLON, width=0.8),
        _key('space', 'SPACE', KEY_SPACE, width=4.0),
        _key('colon', ':', KEY_SEMICOLON, shift=True, width=0.8),
        _key('enter', 'RET', KEY_ENTER, width=1.2),
    ]))

    rows.append(_row(_UT_Y, _UT_H, [
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
# Symbols
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

    rows = [_number_row()]
    y_offsets = [_QW_Y, _AS_Y, _ZX_Y]
    h_vals = [_QW_H, _AS_H, _ZX_H]
    for i, sym_keys in enumerate(symbol_rows):
        rows.append(_row(y_offsets[i], h_vals[i], [
            _key(d, d, c, shift=s) for d, c, s in sym_keys
        ]))

    rows.append(_row(_SP_Y, _SP_H, [
        _key('abc', 'ABC', None, action='main', width=1.5),
        _key('space', 'SPACE', KEY_SPACE, width=3.5),
        _key('bksp2', '\u232B', KEY_BACKSPACE, width=1.5),
        _key('enter2', 'RET', KEY_ENTER, width=1.5),
    ]))

    rows.append(_row(_UT_Y, _UT_H, [
        _key('tab', 'TAB', KEY_TAB),
        _key('esc', 'ESC', KEY_ESC),
        _key('nav', 'NAV', None, action='nav'),
        _key('opt', '\u2699', None, action='options', width=0.8),
    ]))

    return {'name': 'symbols', 'rows': rows}


# =============================================================================
# Navigation (fills 480px)
# =============================================================================

def _build_nav():
    return {'name': 'nav', 'rows': [
        _row(0, 110, [
            _key('home', 'HOME', KEY_HOME), _key('up', '\u2191', KEY_UP),
            _key('end', 'END', KEY_END),    _key('del', 'DEL', KEY_DELETE),
        ]),
        _row(112, 110, [
            _key('left', '\u2190', KEY_LEFT), _key('down', '\u2193', KEY_DOWN),
            _key('right', '\u2192', KEY_RIGHT), _key('ins', 'INS', KEY_INSERT),
        ]),
        _row(224, 90, [
            _key('tab2', 'TAB', KEY_TAB),      _key('esc2', 'ESC', KEY_ESC),
            _key('bksp3', 'BKSP', KEY_BACKSPACE), _key('enter3', 'RET', KEY_ENTER),
        ]),
        _row(316, 76, [
            _key('space', 'SPACE', KEY_SPACE, width=3.0),
            _key('abc2', 'ABC', None, action='main'),
            _key('sym2', '#+', None, action='symbols'),
        ]),
        _row(394, 86, [
            _key('1', '1', KEY_1), _key('2', '2', KEY_2), _key('3', '3', KEY_3),
            _key('4', '4', KEY_4), _key('5', '5', KEY_5), _key('6', '6', KEY_6),
            _key('7', '7', KEY_7), _key('8', '8', KEY_8), _key('9', '9', KEY_9),
            _key('0', '0', KEY_0),
        ]),
    ]}


# =============================================================================
# Options (fills 480px)
# =============================================================================

def _build_options():
    return {'name': 'options', 'rows': [
        _row(0, 66, [
            _key('opt_back', 'BACK', None, action='main', width=1.5),
            _key('opt_title', 'COLOR', None, width=3.0),
        ]),
        _row(68, 96, [
            _key('accent_0', 'RUBY',   None, action='accent_0', width=1, accent_idx=0),
            _key('accent_1', 'OCEAN',  None, action='accent_1', width=1, accent_idx=1),
            _key('accent_2', 'MINT',   None, action='accent_2', width=1, accent_idx=2),
            _key('accent_3', 'SOLAR',  None, action='accent_3', width=1, accent_idx=3),
        ]),
        _row(166, 96, [
            _key('accent_4', 'VIOLET', None, action='accent_4', width=1, accent_idx=4),
            _key('accent_5', 'LIME',   None, action='accent_5', width=1, accent_idx=5),
            _key('accent_6', 'CORAL',  None, action='accent_6', width=1, accent_idx=6),
            _key('accent_7', 'ICE',    None, action='accent_7', width=1, accent_idx=7),
        ]),
        _row(270, 50, [
            _key('br_label', 'BRIGHTNESS', None, width=1.0),
        ]),
        _row(322, 80, [
            _key('br_down', '-', None, action='bright_down', width=1.5),
            _key('br_bar', 'LIGHT', None, width=4.0),
            _key('br_up', '+', None, action='bright_up', width=1.5),
        ]),
        _row(404, 76, [
            _key('opt_back2', 'BACK', None, action='main', width=1.0),
        ]),
    ]}


# =============================================================================
# Public API
# =============================================================================

def build_layouts():
    main = _build_main()
    return {
        'main': main,
        'shift': _build_shift(main),
        'symbols': _build_symbols(main),
        'nav': _build_nav(),
        'options': _build_options(),
    }
