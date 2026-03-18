"""
renderer.py — Pixel-art keyboard rendering on a 2×2 big-pixel grid.

Every visual element aligns to the PX=2 grid:
  - Bevels: 3 big pixels (6 screen px) thick
  - Corner notches: 2 big pixels (4 screen px) cut
  - Font dots: minimum 2×2 screen pixels (scale is always even)
  - Press offset: 1 big pixel (2 screen px)
  - Inner shadow: 1 big pixel (2 screen px) thick
"""

from .constants import (
    SCREEN_WIDTH, GAP, BEVEL, NOTCH, PX,
    COLOR_BACKGROUND, COLOR_KEY_LETTER, COLOR_KEY_DEFAULT,
    COLOR_KEY_SPECIAL, COLOR_KEY_NUMBER,
    COLOR_BEVEL_LIGHT, COLOR_BEVEL_DARK,
    COLOR_PRESS_FACE, COLOR_PRESS_LIGHT, COLOR_PRESS_DARK,
    COLOR_TEXT_DEFAULT, COLOR_TEXT_SPECIAL, COLOR_TEXT_NUMBER, COLOR_TEXT_DIM,
    COLOR_BLACK, COLOR_DIVIDER,
    ACCENT_PRESETS,
)
from .font import measure_text, get_glyph


# =============================================================================
# Layout geometry
# =============================================================================

def compute_key_rects(layout):
    """Compute pixel rectangles for every key in a layout."""
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
            # Snap width to PX grid
            key_width = int(key['w'] * unit_width) // PX * PX
            snapped_x = int(cursor_x) // PX * PX
            computed.append({
                **key,
                'rect': (snapped_x, y, key_width, h),
            })
            cursor_x += key_width + GAP

        # Stretch last key to fill (snap to PX grid)
        if computed:
            last = computed[-1]
            rx, ry, rw, rh = last['rect']
            last['rect'] = (rx, ry, (SCREEN_WIDTH - GAP - rx) // PX * PX, rh)

        rows.append(computed)
    return rows


# =============================================================================
# Text / glyph drawing — each dot is scale×scale, scale always ≥ PX and even
# =============================================================================

def draw_char(sdl, ren, char, x, y, scale, color):
    """Draw a single 5×7 bitmap character. scale must be even (PX-aligned)."""
    glyph = get_glyph(char)
    if not glyph:
        return
    sdl.set_draw_color(ren, *color)
    for row_idx, bits in enumerate(glyph):
        for col_idx in range(5):
            if bits & (1 << (4 - col_idx)):
                sdl.fill_rect(ren, x + col_idx * scale, y + row_idx * scale,
                              scale, scale)


def draw_text(sdl, ren, text, x, y, scale, color):
    """Draw a string. scale must be even."""
    char_advance = 5 * scale + scale
    for i, char in enumerate(text):
        draw_char(sdl, ren, char, x + i * char_advance, y, scale, color)


# =============================================================================
# Key classification
# =============================================================================

def _is_letter_key(key):
    return (key['c'] is not None and not key.get('a')
            and len(key['d']) == 1 and key['d'].isalpha())

def _is_number_key(key):
    return (key['c'] is not None and not key.get('a')
            and len(key['d']) == 1 and key['d'].isdigit())

def _is_special_key(key):
    return bool(key.get('a'))

def _is_shift_key(key):
    return key.get('a') in ('shift', 'unshift')

def _is_accent_swatch(key):
    return 'accent_idx' in key

def _is_options_label(key):
    return key['l'] in ('opt_title', 'br_label', 'br_bar')


# =============================================================================
# Pixel-art beveled box (all sizes are PX-aligned)
# =============================================================================

def _draw_bevel_box(sdl, ren, x, y, w, h, face, light, dark):
    """Draw a chunky beveled button with corner notch cuts.

    BEVEL = 6 screen px (3 big px) on each edge.
    NOTCH = 4 screen px (2 big px) cut at each corner.
    """
    b = BEVEL  # 6
    n = NOTCH  # 4

    # Face fill
    sdl.set_draw_color(ren, *face)
    sdl.fill_rect(ren, x, y, w, h)

    # Top bevel (light)
    sdl.set_draw_color(ren, *light)
    sdl.fill_rect(ren, x + n, y, w - 2 * n, b)         # Top edge
    sdl.fill_rect(ren, x, y + n, b, h - 2 * n)         # Left edge
    # Top-left corner step
    sdl.fill_rect(ren, x + n, y, b, n)
    sdl.fill_rect(ren, x, y + n, n, b)

    # Bottom bevel (dark)
    sdl.set_draw_color(ren, *dark)
    sdl.fill_rect(ren, x + n, y + h - b, w - 2 * n, b)   # Bottom edge
    sdl.fill_rect(ren, x + w - b, y + n, b, h - 2 * n)   # Right edge
    # Bottom-right corner step
    sdl.fill_rect(ren, x + w - b - n, y + h - b, b + n, b)
    sdl.fill_rect(ren, x + w - b, y + h - b - n, b, b + n)

    # Cut corner notches (background shows through)
    sdl.set_draw_color(ren, *COLOR_BACKGROUND)
    sdl.fill_rect(ren, x, y, n, n)               # Top-left
    sdl.fill_rect(ren, x + w - n, y, n, n)       # Top-right
    sdl.fill_rect(ren, x, y + h - n, n, n)       # Bottom-left
    sdl.fill_rect(ren, x + w - n, y + h - n, n, n)  # Bottom-right


def draw_key(sdl, ren, key, pressed=False, shift_active=False, accent=None):
    """Draw a single pixel-art key on the 2×2 grid."""
    x, y, w, h = key['rect']
    is_letter = _is_letter_key(key)
    is_number = _is_number_key(key)
    is_special = _is_special_key(key)
    is_shift = _is_shift_key(key)
    is_swatch = _is_accent_swatch(key)
    is_label = _is_options_label(key)

    # ── Colors ────────────────────────────────────────────────────────────

    if is_swatch:
        idx = key['accent_idx']
        preset = ACCENT_PRESETS[idx]
        face = preset['color']
        light = preset['hl']
        dark = tuple(max(0, c - 60) for c in preset['color'][:3]) + (255,)
    elif is_label:
        face = COLOR_BACKGROUND
        light = COLOR_DIVIDER
        dark = COLOR_BACKGROUND
    elif pressed:
        if accent:
            ac = accent['color']
            face = (ac[0] // 3, ac[1] // 3, ac[2] // 3, 255)
        else:
            face = COLOR_PRESS_FACE
        light = COLOR_PRESS_LIGHT
        dark = COLOR_PRESS_DARK
    elif is_shift and shift_active and accent:
        face = accent['color']
        light = accent['hl']
        dark = tuple(max(0, c - 60) for c in accent['color'][:3]) + (255,)
    elif is_letter:
        face = COLOR_KEY_LETTER
        light = COLOR_BEVEL_LIGHT
        dark = COLOR_BEVEL_DARK
    elif is_number:
        face = COLOR_KEY_NUMBER
        light = COLOR_BEVEL_LIGHT
        dark = COLOR_BEVEL_DARK
    elif is_special:
        face = COLOR_KEY_SPECIAL
        light = (55, 58, 82, 255)
        dark = (18, 20, 35, 255)
    else:
        face = COLOR_KEY_DEFAULT
        light = COLOR_BEVEL_LIGHT
        dark = COLOR_BEVEL_DARK

    # ── Draw box ──────────────────────────────────────────────────────────

    if is_label:
        sdl.set_draw_color(ren, *face)
        sdl.fill_rect(ren, x, y, w, h)
    else:
        _draw_bevel_box(sdl, ren, x, y, w, h, face, light, dark)

    # Inner shadow line on letter keys (1 big pixel = PX thick)
    if is_letter and not pressed and not is_swatch:
        sdl.set_draw_color(ren, *COLOR_BEVEL_DARK)
        sdl.fill_rect(ren, x + BEVEL + PX, y + h - BEVEL - PX,
                       w - 2 * BEVEL - 2 * PX, PX)

    # ── Text ──────────────────────────────────────────────────────────────

    display = key['d']

    # Determine text color
    if is_swatch:
        text_color = COLOR_TEXT_DEFAULT
    elif is_label:
        text_color = COLOR_TEXT_DIM
    elif pressed and accent:
        text_color = accent['hl']
    elif is_special or is_shift:
        if is_shift and shift_active and accent:
            text_color = COLOR_TEXT_DEFAULT
        else:
            text_color = COLOR_TEXT_SPECIAL
    elif is_number:
        text_color = COLOR_TEXT_NUMBER
    else:
        text_color = COLOR_TEXT_DEFAULT

    # Scale: always even (PX-aligned). Single letters get big chunky dots.
    if is_swatch:
        scale = 2       # 2×2 dots — small label on color swatch
    elif is_label:
        scale = 4       # 4×4 dots
    elif is_letter and len(display) == 1:
        scale = 6       # 6×6 dots — big chunky letter (3 big px per dot)
    elif len(display) == 1:
        scale = 4       # 4×4 dots — single symbol/digit
    elif len(display) <= 3:
        scale = 4       # 4×4 dots — short label
    else:
        scale = 2       # 2×2 dots — long label (1 big px per dot)

    text_w = measure_text(display, scale)
    text_h = 7 * scale
    # Center text, snap to PX grid
    text_x = (x + (w - text_w) // 2) // PX * PX
    text_y = (y + (h - text_h) // 2) // PX * PX

    # Pressed: shift text down+right by 1 big pixel
    if pressed:
        text_x += PX
        text_y += PX

    draw_text(sdl, ren, display, text_x, text_y, scale, text_color)

    # ── Selection dot on active accent swatch ─────────────────────────────

    if is_swatch and accent and key['accent_idx'] == _find_accent_index(accent):
        sdl.set_draw_color(ren, *COLOR_TEXT_DEFAULT)
        cx = x + w // 2 - 2 * PX
        cy = y + h - BEVEL - 4 * PX
        # 3×3 big-pixel dot cluster
        dot = 3 * PX
        sdl.fill_rect(ren, cx, cy, dot, dot)
        sdl.set_draw_color(ren, *face)
        sdl.fill_rect(ren, cx + PX, cy + PX, PX, PX)


def _find_accent_index(accent):
    for i, p in enumerate(ACCENT_PRESETS):
        if p['color'] == accent['color']:
            return i
    return -1


# =============================================================================
# Brightness bar (PX-aligned)
# =============================================================================

def _draw_brightness_bar(sdl, ren, key, brightness_pct, accent):
    x, y, w, h = key['rect']

    sdl.set_draw_color(ren, *COLOR_BACKGROUND)
    sdl.fill_rect(ren, x, y, w, h)

    # Track
    margin = 6 * PX
    track_x = x + margin
    track_y = (y + h // 2 - 4 * PX) // PX * PX
    track_w = w - 2 * margin
    track_h = 8 * PX
    sdl.set_draw_color(ren, *COLOR_BEVEL_DARK)
    sdl.fill_rect(ren, track_x, track_y, track_w, track_h)

    # Filled portion (snap to PX)
    fill_w = int(track_w * brightness_pct) // PX * PX
    if accent:
        sdl.set_draw_color(ren, *accent['color'])
    else:
        sdl.set_draw_color(ren, 130, 170, 245, 255)
    if fill_w > 0:
        sdl.fill_rect(ren, track_x, track_y, fill_w, track_h)

    # Border (PX thick edges)
    sdl.set_draw_color(ren, *COLOR_TEXT_DIM)
    sdl.fill_rect(ren, track_x, track_y, track_w, PX)
    sdl.fill_rect(ren, track_x, track_y + track_h - PX, track_w, PX)
    sdl.fill_rect(ren, track_x, track_y, PX, track_h)
    sdl.fill_rect(ren, track_x + track_w - PX, track_y, PX, track_h)

    # Percentage text
    pct_text = str(int(brightness_pct * 100))
    scale = 2
    tw = measure_text(pct_text, scale)
    tx = (x + (w - tw) // 2) // PX * PX
    ty = (y + PX * 2) // PX * PX
    draw_text(sdl, ren, pct_text, tx, ty, scale, COLOR_TEXT_DIM)


# =============================================================================
# Full keyboard
# =============================================================================

def draw_keyboard(sdl, ren, rows, pressed_label=None, shift_active=False,
                  accent=None, brightness_pct=0.5):
    sdl.set_draw_color(ren, *COLOR_BACKGROUND)
    sdl.clear(ren)

    for row in rows:
        for key in row:
            is_pressed = (pressed_label is not None and key['l'] == pressed_label)

            if key['l'] == 'br_bar':
                _draw_brightness_bar(sdl, ren, key, brightness_pct, accent)
                continue

            draw_key(sdl, ren, key, pressed=is_pressed,
                     shift_active=shift_active, accent=accent)

    sdl.present(ren)


def draw_blank(sdl, ren):
    sdl.set_draw_color(ren, *COLOR_BLACK)
    sdl.clear(ren)
    sdl.present(ren)
