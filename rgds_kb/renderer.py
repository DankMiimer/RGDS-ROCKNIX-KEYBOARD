"""
renderer.py — Keyboard rendering: key drawing, text layout, and screen painting.

Handles computing pixel rectangles for keys (proportional sizing), drawing
individual keys with labels, and painting the full keyboard to the SDL renderer.
"""

from .constants import (
    SCREEN_WIDTH, GAP,
    COLOR_BACKGROUND, COLOR_KEY_LETTER, COLOR_KEY_LETTER_HL,
    COLOR_KEY_DEFAULT, COLOR_KEY_SPECIAL, COLOR_KEY_ACTIVE,
    COLOR_KEY_PRESSED, COLOR_TEXT_DEFAULT, COLOR_TEXT_SPECIAL,
    COLOR_TEXT_NUMBER, COLOR_BORDER, COLOR_BLACK, COLOR_DIVIDER,
)
from .font import FONT, measure_text, get_glyph


# =============================================================================
# Layout geometry computation
# =============================================================================

def compute_key_rects(layout):
    """Compute pixel rectangles for every key in a layout.

    Keys within a row are sized proportionally based on their 'w' weight.
    Each key gets an added 'rect' field: (x, y, width, height).

    Args:
        layout: A layout dict with 'rows' containing key dicts with 'w' weights.

    Returns:
        List of rows, where each row is a list of key dicts with 'rect' added.
    """
    rows = []
    for row in layout['rows']:
        y = row['y']
        h = row['h']
        keys = row['keys']

        total_weight = sum(k['w'] for k in keys)
        available_width = SCREEN_WIDTH - 2 * GAP - GAP * (len(keys) - 1)
        unit_width = available_width / total_weight

        computed = []
        cursor_x = GAP

        for key in keys:
            key_width = int(key['w'] * unit_width)
            computed.append({
                **key,
                'rect': (int(cursor_x), y + 1, key_width, h - 2),
            })
            cursor_x += key_width + GAP

        # Stretch last key to fill remaining space (avoids rounding gaps)
        if computed:
            last = computed[-1]
            rx, ry, rw, rh = last['rect']
            last['rect'] = (rx, ry, SCREEN_WIDTH - GAP - rx, rh)

        rows.append(computed)
    return rows


# =============================================================================
# Text / glyph drawing
# =============================================================================

def draw_char(sdl, renderer, char, x, y, scale, color):
    """Draw a single character glyph at (x, y) with the given scale and color.

    Args:
        sdl: SDL wrapper instance
        renderer: SDL renderer pointer
        char: Single character string
        x, y: Top-left pixel position
        scale: Pixel size of each glyph "dot" (e.g. 3 = 3×3 pixels per dot)
        color: (R, G, B, A) tuple
    """
    glyph = get_glyph(char)
    if not glyph:
        return

    sdl.set_draw_color(renderer, *color)
    for row_idx, bits in enumerate(glyph):
        for col_idx in range(5):
            if bits & (1 << (4 - col_idx)):
                sdl.fill_rect(
                    renderer,
                    x + col_idx * scale,
                    y + row_idx * scale,
                    scale, scale,
                )


def draw_text(sdl, renderer, text, x, y, scale, color):
    """Draw a string of text, character by character.

    Args:
        sdl: SDL wrapper instance
        renderer: SDL renderer pointer
        text: String to draw
        x, y: Top-left pixel position of the first character
        scale: Glyph dot size in pixels
        color: (R, G, B, A) tuple
    """
    char_advance = 5 * scale + scale  # 5 columns + 1 column spacing
    for i, char in enumerate(text):
        draw_char(sdl, renderer, char, x + i * char_advance, y, scale, color)


# =============================================================================
# Key classification helpers
# =============================================================================

def _is_letter_key(key):
    """True if this is a single-letter alphabetic key (not an action key)."""
    return (
        key['c'] is not None
        and not key.get('a')
        and len(key['d']) == 1
        and key['d'].isalpha()
    )


def _is_number_key(key):
    """True if this is a single-digit number key."""
    return (
        key['c'] is not None
        and not key.get('a')
        and len(key['d']) == 1
        and key['d'].isdigit()
    )


def _is_special_key(key):
    """True if this is a special/action key (shift, symbols, nav, etc.)."""
    return bool(key.get('a'))


def _is_shift_key(key):
    """True if this is a shift or unshift action key."""
    return key.get('a') in ('shift', 'unshift')


# =============================================================================
# Individual key rendering
# =============================================================================

def draw_key(sdl, renderer, key, pressed=False, shift_active=False):
    """Draw a single key with background, highlight, border, and label.

    Args:
        sdl: SDL wrapper instance
        renderer: SDL renderer pointer
        key: Key dict with 'rect', 'd', etc.
        pressed: Whether the key is currently pressed (finger down)
        shift_active: Whether shift mode is visually active (highlights shift keys)
    """
    x, y, w, h = key['rect']
    is_letter = _is_letter_key(key)
    is_number = _is_number_key(key)
    is_special = _is_special_key(key)
    is_shift = _is_shift_key(key)

    # Background color
    if pressed:
        bg = COLOR_KEY_PRESSED
    elif is_shift and shift_active:
        bg = COLOR_KEY_ACTIVE
    elif is_letter:
        bg = COLOR_KEY_LETTER
    elif is_special:
        bg = COLOR_KEY_SPECIAL
    else:
        bg = COLOR_KEY_DEFAULT

    sdl.set_draw_color(renderer, *bg)
    sdl.fill_rect(renderer, x, y, w, h)

    # Top highlight strip for letter keys (subtle 3D effect)
    if is_letter and not pressed:
        sdl.set_draw_color(renderer, *COLOR_KEY_LETTER_HL)
        sdl.fill_rect(renderer, x + 1, y + 1, w - 2, 2)

    # Border
    sdl.set_draw_color(renderer, *COLOR_BORDER)
    sdl.draw_rect(renderer, x, y, w, h)

    # Label text
    display = key['d']
    if is_special or is_shift:
        text_color = COLOR_TEXT_SPECIAL
    elif is_number:
        text_color = COLOR_TEXT_NUMBER
    else:
        text_color = COLOR_TEXT_DEFAULT

    # Scale: larger for single letters, smaller for longer labels
    if is_letter and len(display) == 1:
        scale = 5
    elif len(display) == 1:
        scale = 4
    elif len(display) <= 3:
        scale = 3
    else:
        scale = 2

    text_w = measure_text(display, scale)
    text_h = 7 * scale
    text_x = x + (w - text_w) // 2
    text_y = y + (h - text_h) // 2
    draw_text(sdl, renderer, display, text_x, text_y, scale, text_color)


# =============================================================================
# Full keyboard rendering
# =============================================================================

def draw_keyboard(sdl, renderer, rows, pressed_label=None, shift_active=False):
    """Draw the entire keyboard (background + all keys).

    Args:
        sdl: SDL wrapper instance
        renderer: SDL renderer pointer
        rows: List of rows from compute_key_rects()
        pressed_label: Label string of the currently pressed key, or None
        shift_active: Whether shift is visually active
    """
    # Background
    sdl.set_draw_color(renderer, *COLOR_BACKGROUND)
    sdl.clear(renderer)

    # Row divider lines
    for row in rows:
        if row:
            sdl.set_draw_color(renderer, *COLOR_DIVIDER)
            sdl.fill_rect(renderer, 0, row[0]['rect'][1] - 1, SCREEN_WIDTH, 1)

    # Keys
    for row in rows:
        for key in row:
            is_pressed = (pressed_label is not None and key['l'] == pressed_label)
            draw_key(sdl, renderer, key, pressed=is_pressed, shift_active=shift_active)

    sdl.present(renderer)


def draw_blank(sdl, renderer):
    """Fill the screen with black (used when keyboard is hidden)."""
    sdl.set_draw_color(renderer, *COLOR_BLACK)
    sdl.clear(renderer)
    sdl.present(renderer)
