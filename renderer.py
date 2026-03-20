"""
Keyboard renderer with dirty-region tracking.

Renders the keyboard to a persistent render-target texture.  Only keys whose
state changed since the last frame are re-drawn.  The full texture is then
blitted to the screen in a single SDL_RenderCopy call.
"""

from font import glyph_for
from sdl2 import SDL, Rect

# Screen dimensions
W, H = 640, 480

# ---------------------------------------------------------------------------
# Bitmap text helpers
# ---------------------------------------------------------------------------

def _draw_char(ren, ch, cx, cy, scale, col):
    """Draw a single bitmap character at (cx, cy)."""
    g = glyph_for(ch)
    if not g:
        return
    SDL.set_draw_color(ren, *col)
    for ri, bits in enumerate(g):
        for ci in range(5):
            if bits & (1 << (4 - ci)):
                SDL.fill_rect(ren, cx + ci * scale, cy + ri * scale, scale, scale)


def _draw_text(ren, text, cx, cy, scale, col):
    """Draw a string of bitmap characters."""
    for i, ch in enumerate(text):
        _draw_char(ren, ch, cx + i * (5 * scale + scale), cy, scale, col)


def _text_width(text, scale):
    """Pixel width of a bitmap string."""
    return len(text) * (5 * scale + scale) - scale if text else 0


# ---------------------------------------------------------------------------
# Key classification helpers
# ---------------------------------------------------------------------------

def _is_letter(key):
    return (key['c'] is not None and not key.get('a')
            and len(key['d']) == 1 and key['d'].isalpha())

def _is_number(key):
    return (key['c'] is not None and not key.get('a')
            and len(key['d']) == 1 and key['d'].isdigit())

def _is_special(key):
    return bool(key.get('a'))

def _is_shift_action(key):
    return key.get('a') in ('shift', 'unshift')


# ---------------------------------------------------------------------------
# Renderer
# ---------------------------------------------------------------------------

class Renderer:
    """Manages keyboard rendering with dirty-region tracking."""

    __slots__ = ('_ren', '_target', '_theme', '_prev_states')

    def __init__(self, ren, theme):
        self._ren = ren
        self._target = SDL.create_target_texture(ren, W, H)
        self._theme = theme
        self._prev_states = {}  # label → (pressed, shift_active)

    def set_theme(self, theme):
        """Switch theme — forces full redraw on next render."""
        self._theme = theme
        self._prev_states.clear()

    def render_full(self, rows, pressed_label=None, shift_active=False):
        """Full redraw of all keys to the target texture."""
        t = self._theme
        ren = self._ren

        # Draw onto target texture
        SDL.set_render_target(ren, self._target)
        SDL.set_draw_color(ren, *t['bg'])
        SDL.clear(ren)

        # Divider lines
        for row in rows:
            if row:
                SDL.set_draw_color(ren, *t['divider'])
                SDL.fill_rect(ren, 0, row[0]['rect'][1] - 1, W, 1)

        # Keys
        for row in rows:
            for key in row:
                is_pressed = (pressed_label and key['l'] == pressed_label)
                self._draw_key(key, is_pressed, shift_active)

        # Back to screen and blit
        SDL.set_render_target(ren, None)
        SDL.render_copy(ren, self._target)
        SDL.present(ren)

        # Cache state
        self._prev_states.clear()
        for row in rows:
            for key in row:
                self._prev_states[key['l']] = (
                    pressed_label and key['l'] == pressed_label,
                    shift_active
                )

    def render_dirty(self, rows, pressed_label=None, shift_active=False):
        """
        Re-draw only keys whose visual state changed.
        Returns True if anything was drawn, False if frame was skipped.
        """
        dirty_keys = []
        for row in rows:
            for key in row:
                is_pressed = bool(pressed_label and key['l'] == pressed_label)
                new_state = (is_pressed, shift_active)
                old_state = self._prev_states.get(key['l'])
                if old_state != new_state:
                    dirty_keys.append(key)

        if not dirty_keys:
            return False

        ren = self._ren
        t = self._theme

        # Render dirty keys onto target texture
        SDL.set_render_target(ren, self._target)
        for key in dirty_keys:
            is_pressed = bool(pressed_label and key['l'] == pressed_label)
            # Clear the key region with background first
            x, y, w, h = key['rect']
            SDL.set_draw_color(ren, *t['bg'])
            SDL.fill_rect(ren, x, y, w, h)
            self._draw_key(key, is_pressed, shift_active)

        # Blit full texture to screen
        SDL.set_render_target(ren, None)
        SDL.render_copy(ren, self._target)
        SDL.present(ren)

        # Update cache
        for row in rows:
            for key in row:
                self._prev_states[key['l']] = (
                    bool(pressed_label and key['l'] == pressed_label),
                    shift_active
                )
        return True

    def render_black(self):
        """Fill screen with black (keyboard hidden)."""
        ren = self._ren
        SDL.set_draw_color(ren, 0, 0, 0, 255)
        SDL.set_render_target(ren, None)
        SDL.clear(ren)
        SDL.present(ren)
        self._prev_states.clear()

    def _draw_key(self, key, pressed, shift_active):
        """Draw a single key onto the current render target."""
        t = self._theme
        ren = self._ren
        x, y, w, h = key['rect']

        il = _is_letter(key)
        isn = _is_number(key)
        isp = _is_special(key)
        ish = _is_shift_action(key)

        # Background
        if pressed:
            bg = t['key_press']
        elif ish and shift_active:
            bg = t['key_act']
        elif il:
            bg = t['key']
        elif isp:
            bg = t['key_sp']
        else:
            bg = t['key']

        SDL.set_draw_color(ren, *bg)
        SDL.fill_rect(ren, x, y, w, h)

        # Highlight strip on letter keys
        if il and not pressed:
            SDL.set_draw_color(ren, *t['key_hi'])
            SDL.fill_rect(ren, x + 1, y + 1, w - 2, 2)

        # Border
        SDL.set_draw_color(ren, *t['border'])
        SDL.draw_rect(ren, x, y, w, h)

        # Text
        d = key['d']
        if isp or ish:
            tc = t['text_sp']
        elif isn:
            tc = t['text_num']
        else:
            tc = t['text']

        # Scale: single letter=5, single char=4, short label=3, long=2
        if il and len(d) == 1:
            sc = 5
        elif len(d) == 1:
            sc = 4
        elif len(d) <= 3:
            sc = 3
        else:
            sc = 2

        tw = _text_width(d, sc)
        th = 7 * sc
        _draw_text(ren, d, x + (w - tw) // 2, y + (h - th) // 2, sc, tc)

    def destroy(self):
        """Free the render-target texture."""
        if self._target:
            SDL.destroy_texture(self._target)
            self._target = None
