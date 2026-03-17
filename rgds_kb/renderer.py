"""
renderer.py — Pixel-art keyboard rendering.

Draws chunky beveled keys with corner notches for a retro pixel-art feel.
Supports accent-color-aware rendering and special options menu drawing.
"""

from .constants import (
    SCREEN_WIDTH, GAP, BEVEL, NOTCH,
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
# Layout geometry computation
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
            key_width = int(key['w'] * unit_width)
            computed.append({
                **key,
                'rect': (int(cursor_x), y + 1, key_width, h - 2),
            })
            cursor_x += key_width + GAP

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
    """Draw a single character glyph at (x, y) with the given scale and color."""
    glyph = get_glyph(char)
    if not glyph:
        return
    sdl.set_draw_color(renderer, *color)
    for row_idx, bits in enumerate(glyph):
        for col_idx in range(5):
            if bits & (1 << (4 - col_idx)):
                sdl.fill_rect(renderer, x + col_idx * scale, y + row_idx * scale, scale, scale)


def draw_text(sdl, renderer, text, x, y, scale, color):
    """Draw a string of text, character by character."""
    char_advance = 5 * scale + scale
    for i, char in enumerate(text):
        draw_char(sdl, renderer, char, x + i * char_advance, y, scale, color)


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
    """Non-interactive labels in options (title, brightness label, bar)."""
    return key['l'] in ('opt_title', 'br_label', 'br_bar')


# =============================================================================
# Pixel-art beveled key drawing
# =============================================================================

def _draw_bevel_box(sdl, ren, x, y, w, h, face, light, dark):
    """Draw a pixel-art beveled rectangle with corner notches.

    Creates a chunky 3D raised button effect:
    - Light color on top and left edges (BEVEL px thick)
    - Dark color on bottom and right edges
    - Corner notches cut for pixel-rounded look
    - Face color fills the center
    """
    b = BEVEL
    n = NOTCH

    # Face (full rect, then bevel paints over edges)
    sdl.set_draw_color(ren, *face)
    sdl.fill_rect(ren, x, y, w, h)

    # Top bevel (light) — with corner notch insets
    sdl.set_draw_color(ren, *light)
    sdl.fill_rect(ren, x + n, y, w - 2 * n, b)           # Top edge
    sdl.fill_rect(ren, x, y + n, b, h - 2 * n)           # Left edge
    # Top-left corner fill (diagonal pixel notch)
    sdl.fill_rect(ren, x + n, y, b, n)
    sdl.fill_rect(ren, x, y + n, n, b)

    # Bottom bevel (dark) — with corner notch insets
    sdl.set_draw_color(ren, *dark)
    sdl.fill_rect(ren, x + n, y + h - b, w - 2 * n, b)   # Bottom edge
    sdl.fill_rect(ren, x + w - b, y + n, b, h - 2 * n)   # Right edge
    # Bottom-right corner fill
    sdl.fill_rect(ren, x + w - b - n, y + h - b, b + n, b)
    sdl.fill_rect(ren, x + w - b, y + h - b - n, b, b + n)

    # Cut corner notches (background color peeks through)
    sdl.set_draw_color(ren, *COLOR_BACKGROUND)
    # Top-left notch
    sdl.fill_rect(ren, x, y, n, n)
    # Top-right notch
    sdl.fill_rect(ren, x + w - n, y, n, n)
    # Bottom-left notch
    sdl.fill_rect(ren, x, y + h - n, n, n)
    # Bottom-right notch
    sdl.fill_rect(ren, x + w - n, y + h - n, n, n)


def draw_key(sdl, ren, key, pressed=False, shift_active=False, accent=None):
    """Draw a single pixel-art key.

    Args:
        accent: Current accent preset dict with 'color' and 'hl' keys, or None.
    """
    x, y, w, h = key['rect']
    is_letter = _is_letter_key(key)
    is_number = _is_number_key(key)
    is_special = _is_special_key(key)
    is_shift = _is_shift_key(key)
    is_swatch = _is_accent_swatch(key)
    is_label = _is_options_label(key)

    # ── Determine colors ──────────────────────────────────────────────────

    if is_swatch:
        # Color swatch: fill with the accent color
        idx = key['accent_idx']
        preset = ACCENT_PRESETS[idx]
        face = preset['color']
        light = preset['hl']
        # Darken for shadow edge
        dark = tuple(max(0, c - 60) for c in preset['color'][:3]) + (255,)
    elif is_label:
        # Non-interactive label: flat dark
        face = COLOR_BACKGROUND
        light = COLOR_DIVIDER
        dark = COLOR_BACKGROUND
    elif pressed:
        # Sunken pressed state — use accent color for face glow
        if accent:
            ac = accent['color']
            face = (ac[0] // 3, ac[1] // 3, ac[2] // 3, 255)
        else:
            face = COLOR_PRESS_FACE
        light = COLOR_PRESS_LIGHT
        dark = COLOR_PRESS_DARK
    elif is_shift and shift_active and accent:
        # Active shift: accent-colored
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

    # ── Draw the beveled box ──────────────────────────────────────────────

    if is_label:
        # Flat label, no bevel
        sdl.set_draw_color(ren, *face)
        sdl.fill_rect(ren, x, y, w, h)
    else:
        _draw_bevel_box(sdl, ren, x, y, w, h, face, light, dark)

    # ── Inner shadow line on letter keys (extra depth) ────────────────────

    if is_letter and not pressed and not is_swatch:
        sdl.set_draw_color(ren, *COLOR_BEVEL_DARK)
        sdl.fill_rect(ren, x + BEVEL + 1, y + h - BEVEL - 1, w - 2 * BEVEL - 2, 1)

    # ── Draw text label ───────────────────────────────────────────────────

    display = key['d']

    if is_swatch:
        # Swatch: white text, small
        text_color = COLOR_TEXT_DEFAULT
        scale = 2
    elif is_label:
        text_color = COLOR_TEXT_DIM
        scale = 3
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

    # Auto-scale based on content
    if not is_swatch and not is_label:
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

    # Pressed keys: shift text down+right 1px for depth effect
    if pressed:
        text_x += 1
        text_y += 1

    draw_text(sdl, ren, display, text_x, text_y, scale, text_color)

    # ── Selection indicator for accent swatches ───────────────────────────

    if is_swatch and accent and key['accent_idx'] == _find_accent_index(accent):
        # Draw a small check/dot indicator
        ic = COLOR_TEXT_DEFAULT
        sdl.set_draw_color(ren, *ic)
        # Bottom-center dot cluster (3x3)
        cx = x + w // 2 - 2
        cy = y + h - BEVEL - 8
        sdl.fill_rect(ren, cx, cy, 5, 5)
        # Inner dot darker
        sdl.set_draw_color(ren, *face)
        sdl.fill_rect(ren, cx + 1, cy + 1, 3, 3)
        sdl.set_draw_color(ren, *ic)
        sdl.fill_rect(ren, cx + 2, cy + 2, 1, 1)


def _find_accent_index(accent):
    """Find the index of the current accent in ACCENT_PRESETS."""
    for i, p in enumerate(ACCENT_PRESETS):
        if p['color'] == accent['color']:
            return i
    return -1


# =============================================================================
# Brightness bar (special rendering for the options brightness indicator)
# =============================================================================

def _draw_brightness_bar(sdl, ren, key, brightness_pct, accent):
    """Draw a brightness progress bar inside the br_bar key rect."""
    x, y, w, h = key['rect']

    # Background
    sdl.set_draw_color(ren, *COLOR_BACKGROUND)
    sdl.fill_rect(ren, x, y, w, h)

    # Track
    track_x = x + 12
    track_y = y + h // 2 - 8
    track_w = w - 24
    track_h = 16
    sdl.set_draw_color(ren, *COLOR_BEVEL_DARK)
    sdl.fill_rect(ren, track_x, track_y, track_w, track_h)

    # Filled portion
    fill_w = int(track_w * brightness_pct)
    if accent:
        sdl.set_draw_color(ren, *accent['color'])
    else:
        sdl.set_draw_color(ren, 130, 170, 245, 255)
    if fill_w > 0:
        sdl.fill_rect(ren, track_x, track_y, fill_w, track_h)

    # Border around track
    sdl.set_draw_color(ren, *COLOR_TEXT_DIM)
    sdl.fill_rect(ren, track_x, track_y, track_w, 2)
    sdl.fill_rect(ren, track_x, track_y + track_h - 2, track_w, 2)
    sdl.fill_rect(ren, track_x, track_y, 2, track_h)
    sdl.fill_rect(ren, track_x + track_w - 2, track_y, 2, track_h)

    # Percentage text
    pct_text = str(int(brightness_pct * 100))
    scale = 2
    tw = measure_text(pct_text, scale)
    draw_text(sdl, ren, pct_text, x + (w - tw) // 2, y + 4, scale, COLOR_TEXT_DIM)


# =============================================================================
# Full keyboard rendering
# =============================================================================

def draw_keyboard(sdl, ren, rows, pressed_label=None, shift_active=False,
                  accent=None, brightness_pct=0.5):
    """Draw the entire keyboard with pixel-art styling.

    Args:
        accent: Current accent preset dict, or None for default.
        brightness_pct: 0.0–1.0 for brightness bar in options view.
    """
    sdl.set_draw_color(ren, *COLOR_BACKGROUND)
    sdl.clear(ren)

    for row in rows:
        for key in row:
            is_pressed = (pressed_label is not None and key['l'] == pressed_label)

            # Special: brightness bar
            if key['l'] == 'br_bar':
                _draw_brightness_bar(sdl, ren, key, brightness_pct, accent)
                continue

            draw_key(sdl, ren, key, pressed=is_pressed,
                     shift_active=shift_active, accent=accent)

    sdl.present(ren)


def draw_blank(sdl, ren):
    """Fill the screen with black."""
    sdl.set_draw_color(ren, *COLOR_BLACK)
    sdl.clear(ren)
    sdl.present(ren)
