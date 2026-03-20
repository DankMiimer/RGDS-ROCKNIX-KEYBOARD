"""
Keyboard layout definitions.
Each layout is a dict with 'name' and 'rows'.
Each row has 'y', 'h', and 'keys' (list of key dicts).
Key dict: l=label, d=display, c=keycode, s=shift, w=weight, a=action.
"""

# ---------------------------------------------------------------------------
# Linux keycodes (from <linux/input-event-codes.h>)
# ---------------------------------------------------------------------------

KEY_ESC = 1;  KEY_1 = 2;  KEY_2 = 3;  KEY_3 = 4;  KEY_4 = 5
KEY_5 = 6;  KEY_6 = 7;  KEY_7 = 8;  KEY_8 = 9;  KEY_9 = 10
KEY_0 = 11;  KEY_MINUS = 12;  KEY_EQUAL = 13;  KEY_BACKSPACE = 14
KEY_TAB = 15;  KEY_Q = 16;  KEY_W = 17;  KEY_E = 18;  KEY_R = 19
KEY_T = 20;  KEY_Y = 21;  KEY_U = 22;  KEY_I = 23;  KEY_O = 24
KEY_P = 25;  KEY_LEFTBRACE = 26;  KEY_RIGHTBRACE = 27;  KEY_ENTER = 28
KEY_LEFTCTRL = 29;  KEY_A = 30;  KEY_S = 31;  KEY_D = 32;  KEY_F = 33
KEY_G = 34;  KEY_H = 35;  KEY_J = 36;  KEY_K = 37;  KEY_L = 38
KEY_SEMICOLON = 39;  KEY_APOSTROPHE = 40;  KEY_GRAVE = 41
KEY_LEFTSHIFT = 42;  KEY_BACKSLASH = 43
KEY_Z = 44;  KEY_X = 45;  KEY_C = 46;  KEY_V = 47;  KEY_B = 48
KEY_N = 49;  KEY_M = 50;  KEY_COMMA = 51;  KEY_DOT = 52;  KEY_SLASH = 53
KEY_LEFTALT = 56;  KEY_SPACE = 57
KEY_UP = 103;  KEY_LEFT = 105;  KEY_RIGHT = 106;  KEY_DOWN = 108
KEY_HOME = 102;  KEY_END = 107;  KEY_DELETE = 111;  KEY_INSERT = 110

# All keycodes needed for uinput registration
ALL_KEYCODES = [
    KEY_ESC, KEY_1, KEY_2, KEY_3, KEY_4, KEY_5, KEY_6, KEY_7, KEY_8, KEY_9,
    KEY_0, KEY_MINUS, KEY_EQUAL, KEY_BACKSPACE, KEY_TAB, KEY_Q, KEY_W, KEY_E,
    KEY_R, KEY_T, KEY_Y, KEY_U, KEY_I, KEY_O, KEY_P, KEY_LEFTBRACE,
    KEY_RIGHTBRACE, KEY_ENTER, KEY_LEFTCTRL, KEY_A, KEY_S, KEY_D, KEY_F,
    KEY_G, KEY_H, KEY_J, KEY_K, KEY_L, KEY_SEMICOLON, KEY_APOSTROPHE,
    KEY_GRAVE, KEY_LEFTSHIFT, KEY_BACKSLASH, KEY_Z, KEY_X, KEY_C, KEY_V,
    KEY_B, KEY_N, KEY_M, KEY_COMMA, KEY_DOT, KEY_SLASH, KEY_LEFTALT,
    KEY_SPACE, KEY_LEFT, KEY_RIGHT, KEY_UP, KEY_DOWN, KEY_HOME, KEY_END,
    KEY_DELETE, KEY_INSERT,
]

# Keys that support held-repeat
REPEATABLE_LABELS = frozenset({
    'bksp', 'space', 'up', 'down', 'left', 'right',
    'del', 'bksp2', 'bksp3',
})

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _k(label, display, code, shift=False, weight=1, action=None):
    """Shorthand key constructor."""
    d = {'l': label, 'd': display, 'c': code, 's': shift, 'w': weight}
    if action:
        d['a'] = action
    return d

# ---------------------------------------------------------------------------
# Layout builders
# ---------------------------------------------------------------------------

def _build_main():
    return {'name': 'main', 'rows': [
        # Row 0 — QWERTY top
        {'y': 0, 'h': 95, 'keys': [
            _k('q','q',KEY_Q), _k('w','w',KEY_W), _k('e','e',KEY_E),
            _k('r','r',KEY_R), _k('t','t',KEY_T), _k('y','y',KEY_Y),
            _k('u','u',KEY_U), _k('i','i',KEY_I), _k('o','o',KEY_O),
            _k('p','p',KEY_P),
        ]},
        # Row 1 — ASDF
        {'y': 98, 'h': 95, 'keys': [
            _k('a','a',KEY_A), _k('s2','s',KEY_S), _k('d2','d',KEY_D),
            _k('f','f',KEY_F), _k('g','g',KEY_G), _k('h','h',KEY_H),
            _k('j','j',KEY_J), _k('k','k',KEY_K), _k('l2','l',KEY_L),
        ]},
        # Row 2 — SHIFT ZXCVBNM BKSP
        {'y': 196, 'h': 95, 'keys': [
            _k('shift','\u21E7',None,weight=1.4,action='shift'),
            _k('z','z',KEY_Z), _k('x','x',KEY_X), _k('c2','c',KEY_C),
            _k('v','v',KEY_V), _k('b','b',KEY_B), _k('n','n',KEY_N),
            _k('m','m',KEY_M),
            _k('bksp','\u232B',KEY_BACKSPACE,weight=1.4),
        ]},
        # Row 3 — utility (sym, comma, space, dot, enter)
        {'y': 294, 'h': 75, 'keys': [
            _k('sym','#+',None,weight=1.2,action='symbols'),
            _k('comma',',',KEY_COMMA,weight=0.8),
            _k('space','SPACE',KEY_SPACE,weight=4.5),
            _k('dot','.',KEY_DOT,weight=0.8),
            _k('enter','RET',KEY_ENTER,weight=1.2),
        ]},
        # Row 4 — number row
        {'y': 372, 'h': 50, 'keys': [
            _k('1','1',KEY_1), _k('2','2',KEY_2), _k('3','3',KEY_3),
            _k('4','4',KEY_4), _k('5','5',KEY_5), _k('6','6',KEY_6),
            _k('7','7',KEY_7), _k('8','8',KEY_8), _k('9','9',KEY_9),
            _k('0','0',KEY_0),
        ]},
        # Row 5 — small utility
        {'y': 425, 'h': 52, 'keys': [
            _k('tab','TAB',KEY_TAB), _k('esc','ESC',KEY_ESC),
            _k('nav','NAV',None,action='nav'),
            _k('dash','-',KEY_MINUS,weight=0.8),
            _k('qmark','?',KEY_SLASH,shift=True,weight=0.8),
            _k('excl','!',KEY_1,shift=True,weight=0.8),
            _k('at','@',KEY_2,shift=True,weight=0.8),
        ]},
    ]}


def _build_shift(main):
    rows = []
    # Rows 0-1: uppercase letters
    for row in main['rows'][:2]:
        rows.append({'y': row['y'], 'h': row['h'],
                     'keys': [{**k, 's': True, 'd': k['d'].upper()} for k in row['keys']]})
    # Row 2: shift key becomes unshift, letters uppercase
    sr = {'y': 196, 'h': 95, 'keys': []}
    for k in main['rows'][2]['keys']:
        nk = dict(k)
        if nk['l'] == 'shift':
            nk['a'] = 'unshift'
        elif nk['c'] and nk['l'] != 'bksp':
            nk['s'] = True
            nk['d'] = nk['d'].upper()
        sr['keys'].append(nk)
    rows.append(sr)
    # Row 3: shifted utility
    rows.append({'y': 294, 'h': 75, 'keys': [
        _k('sym','#+',None,weight=1.2,action='symbols'),
        _k('semi',';',KEY_SEMICOLON,weight=0.8),
        _k('space','SPACE',KEY_SPACE,weight=4.5),
        _k('colon',':',KEY_SEMICOLON,shift=True,weight=0.8),
        _k('enter','RET',KEY_ENTER,weight=1.2),
    ]})
    # Row 4: shifted numbers → symbols
    shift_syms = ['!','@','#','$','%','^','&','*','(',')']
    rows.append({'y': 372, 'h': 50, 'keys': [
        {**dict(k), 'd': shift_syms[i], 's': True}
        for i, k in enumerate(main['rows'][4]['keys'])
    ]})
    # Row 5: shifted small utility
    rows.append({'y': 425, 'h': 52, 'keys': [
        _k('tab','TAB',KEY_TAB), _k('esc','ESC',KEY_ESC),
        _k('nav','NAV',None,action='nav'),
        _k('under','_',KEY_MINUS,shift=True,weight=0.8),
        _k('apos',"'",KEY_APOSTROPHE,weight=0.8),
        _k('quot','"',KEY_APOSTROPHE,shift=True,weight=0.8),
        _k('hash','#',KEY_3,shift=True,weight=0.8),
    ]})
    return {'name': 'shift', 'rows': rows}


def _build_symbols():
    sym_rows = [
        [('!',KEY_1,True),('@',KEY_2,True),('#',KEY_3,True),('$',KEY_4,True),
         ('%',KEY_5,True),('^',KEY_6,True),('&',KEY_7,True),('*',KEY_8,True),
         ('(',KEY_9,True),(')',KEY_0,True)],
        [('-',KEY_MINUS,False),('_',KEY_MINUS,True),('+',KEY_EQUAL,True),
         ('=',KEY_EQUAL,False),('[',KEY_LEFTBRACE,False),(']',KEY_RIGHTBRACE,False),
         ('{',KEY_LEFTBRACE,True),('}',KEY_RIGHTBRACE,True),
         ('|',KEY_BACKSLASH,True),('\\',KEY_BACKSLASH,False)],
        [(':',KEY_SEMICOLON,True),(';',KEY_SEMICOLON,False),
         ("'",KEY_APOSTROPHE,False),('"',KEY_APOSTROPHE,True),
         ('`',KEY_GRAVE,False),('~',KEY_GRAVE,True),
         ('<',KEY_COMMA,True),('>',KEY_DOT,True),
         ('/',KEY_SLASH,False),('?',KEY_SLASH,True)],
    ]
    rows = []
    for ri, keys in enumerate(sym_rows):
        rows.append({
            'y': [0, 98, 196][ri], 'h': 95,
            'keys': [_k(d, d, c, shift=s) for d, c, s in keys],
        })
    # ABC / space / bksp / enter
    rows.append({'y': 294, 'h': 75, 'keys': [
        _k('abc','ABC',None,weight=1.5,action='main'),
        _k('space','SPACE',KEY_SPACE,weight=4.0),
        _k('bksp2','\u232B',KEY_BACKSPACE,weight=1.5),
        _k('enter2','RET',KEY_ENTER,weight=1.5),
    ]})
    # Number row
    rows.append({'y': 372, 'h': 50, 'keys': [
        _k('1','1',KEY_1), _k('2','2',KEY_2), _k('3','3',KEY_3),
        _k('4','4',KEY_4), _k('5','5',KEY_5), _k('6','6',KEY_6),
        _k('7','7',KEY_7), _k('8','8',KEY_8), _k('9','9',KEY_9),
        _k('0','0',KEY_0),
    ]})
    # Small utility
    rows.append({'y': 425, 'h': 52, 'keys': [
        _k('tab','TAB',KEY_TAB), _k('esc','ESC',KEY_ESC),
        _k('nav','NAV',None,action='nav'),
    ]})
    return {'name': 'symbols', 'rows': rows}


def _build_nav():
    return {'name': 'nav', 'rows': [
        {'y': 0, 'h': 120, 'keys': [
            _k('home','HOME',KEY_HOME), _k('up','\u2191',KEY_UP),
            _k('end','END',KEY_END), _k('del','DEL',KEY_DELETE),
        ]},
        {'y': 123, 'h': 120, 'keys': [
            _k('left','\u2190',KEY_LEFT), _k('down','\u2193',KEY_DOWN),
            _k('right','\u2192',KEY_RIGHT), _k('ins','INS',KEY_INSERT),
        ]},
        {'y': 246, 'h': 100, 'keys': [
            _k('tab2','TAB',KEY_TAB), _k('esc2','ESC',KEY_ESC),
            _k('bksp3','BKSP',KEY_BACKSPACE), _k('enter3','RET',KEY_ENTER),
        ]},
        {'y': 349, 'h': 68, 'keys': [
            _k('space','SPACE',KEY_SPACE,weight=3),
            _k('abc2','ABC',None,action='main'),
            _k('sym2','#+',None,action='symbols'),
        ]},
        {'y': 420, 'h': 57, 'keys': [
            _k('1','1',KEY_1), _k('2','2',KEY_2), _k('3','3',KEY_3),
            _k('4','4',KEY_4), _k('5','5',KEY_5), _k('6','6',KEY_6),
            _k('7','7',KEY_7), _k('8','8',KEY_8), _k('9','9',KEY_9),
            _k('0','0',KEY_0),
        ]},
    ]}


# ---------------------------------------------------------------------------
# Rect computation
# ---------------------------------------------------------------------------

def compute_rects(layout, screen_w=640, gap=3):
    """Compute pixel rects for every key in a layout.  Returns list of rows."""
    rows = []
    for row in layout['rows']:
        y = row['y']; h = row['h']; keys = row['keys']
        total_w = sum(k['w'] for k in keys)
        avail = screen_w - 2 * gap - gap * (len(keys) - 1)
        unit = avail / total_w
        computed = []; cx = gap
        for k in keys:
            kw = int(k['w'] * unit)
            computed.append({**k, 'rect': (int(cx), y + 1, kw, h - 2)})
            cx += kw + gap
        # Stretch last key to fill remaining space
        if computed:
            last = computed[-1]
            rx, ry, _, rh = last['rect']
            last['rect'] = (rx, ry, screen_w - gap - rx, rh)
        rows.append(computed)
    return rows


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_all():
    """Build all keyboard layouts and their computed rects."""
    main = _build_main()
    layouts = {
        'main':    main,
        'shift':   _build_shift(main),
        'symbols': _build_symbols(),
        'nav':     _build_nav(),
    }
    rects = {name: compute_rects(lay) for name, lay in layouts.items()}
    return layouts, rects
