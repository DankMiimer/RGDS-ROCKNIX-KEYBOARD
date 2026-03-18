"""
engine.py — Main application loop: event dispatch, state machine, key repeat.

Coordinates all subsystems and runs the frame loop at ~60fps. Handles:
  - R3 toggle (show/hide keyboard)
  - Touch hit-testing against key rects
  - Key press/release → uinput injection
  - Shift auto-return after one uppercase letter
  - Held-key repeat for backspace, space, arrows
  - Periodic DSI-1 power re-assertion
  - Options menu: accent color selection, brightness control
"""

import atexit
import os
import signal
import subprocess
import time

from .constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    WINDOW_TITLE, REASSERT_INTERVAL,
    TOUCH_DEVICE, JOYPAD_DEVICE, BTN_THUMBR,
    REPEAT_DELAY, REPEAT_RATE, REPEATABLE_KEYS,
    ACCENT_PRESETS,
)
from .sdl import SDL
from .uinput_device import UinputDevice
from .touch_input import TouchInput, cleanup_grabs
from .joypad import JoypadMonitor
from .layouts import build_layouts
from .renderer import compute_key_rects, draw_keyboard, draw_blank
from .settings import (
    load_settings, save_settings, apply_brightness,
    brightness_up, brightness_down,
)


# =============================================================================
# Sway helpers
# =============================================================================

def _sway_cmd(cmd):
    try:
        subprocess.run(['swaymsg', cmd], capture_output=True, timeout=2)
    except Exception:
        pass


def _place_window():
    _sway_cmd('output DSI-1 power on')
    _sway_cmd(f'[title="{WINDOW_TITLE}"] move to output DSI-1')
    _sway_cmd(f'[title="{WINDOW_TITLE}"] fullscreen enable')


# =============================================================================
# Hit testing
# =============================================================================

def _hit_test(rows, x, y):
    for row in rows:
        for key in row:
            kx, ky, kw, kh = key['rect']
            if kx <= x <= kx + kw and ky <= y <= ky + kh:
                return key
    return None


# =============================================================================
# Main application
# =============================================================================

def run():
    """Entry point: set up all subsystems and run the main loop."""

    atexit.register(cleanup_grabs)

    # ── SDL setup ──────────────────────────────────────────────────────────
    os.environ['SDL_VIDEODRIVER'] = 'wayland'
    sdl = SDL()
    if sdl.init() != 0:
        print(f"[sdl] Init failed: {sdl.get_error()}")
        return 1

    _sway_cmd('output DSI-1 power on')
    time.sleep(0.2)

    win = sdl.create_window(
        WINDOW_TITLE, 0x1FFF0000, 0x1FFF0000,
        SCREEN_WIDTH, SCREEN_HEIGHT, 0x04,
    )
    ren = sdl.create_renderer(win, -1, 0x06)

    sdl.set_draw_color(ren, 12, 12, 20, 255)
    sdl.clear(ren)
    sdl.present(ren)
    time.sleep(0.5)
    _place_window()
    time.sleep(0.3)
    draw_blank(sdl, ren)

    # ── Build layouts ──────────────────────────────────────────────────────
    layouts = build_layouts()
    rects = {name: compute_key_rects(layout) for name, layout in layouts.items()}

    # ── Subsystems ─────────────────────────────────────────────────────────
    uinput = UinputDevice()
    uinput.setup()
    touch = TouchInput(TOUCH_DEVICE)
    touch.open()

    # ── Load settings ──────────────────────────────────────────────────────
    settings = load_settings()
    accent_index = settings['accent_index']
    accent = ACCENT_PRESETS[accent_index]
    brightness_val = settings['brightness']  # 0.0–1.0
    apply_brightness(brightness_val)         # Apply saved brightness to DSI-1

    # ── State ──────────────────────────────────────────────────────────────
    visible = False
    running = True
    current_layer = 'main'
    prev_layer = 'main'  # Layer to return to from options

    pressed_label = None
    pressed_key = None
    press_time = 0.0
    shift_active = False
    shift_sticky = False

    toggle_flag = False
    needs_redraw = True
    last_repeat_time = 0.0
    last_reassert_time = time.time()

    def on_r3_press():
        nonlocal toggle_flag
        toggle_flag = True

    def on_signal(sig, frame):
        nonlocal running
        running = False

    signal.signal(signal.SIGTERM, on_signal)
    signal.signal(signal.SIGINT, on_signal)

    joypad = JoypadMonitor(JOYPAD_DEVICE, BTN_THUMBR, on_r3_press)
    joypad.start()
    print("[engine] Running — press R3 to toggle keyboard")

    # ── Helper: brightness as 0.0–1.0 ────────────────────────────────────
    def _brightness_pct():
        return brightness_val

    # ── Main loop ──────────────────────────────────────────────────────────
    try:
        while running:
            now = time.time()

            while sdl.poll_event() is not None:
                pass

            # ── R3 toggle ──────────────────────────────────────────────────
            if toggle_flag:
                toggle_flag = False
                visible = not visible
                if visible:
                    touch.grab()
                    needs_redraw = True
                    print("[engine] Keyboard shown")
                else:
                    touch.ungrab()
                    current_layer = 'main'
                    prev_layer = 'main'
                    shift_active = False
                    shift_sticky = False
                    pressed_label = None
                    pressed_key = None
                    draw_blank(sdl, ren)
                    print("[engine] Keyboard hidden")

            # ── Periodic reassert ──────────────────────────────────────────
            if visible and now - last_reassert_time > REASSERT_INTERVAL:
                _place_window()
                last_reassert_time = now

            if not visible:
                sdl.delay(50)
                continue

            # ── Touch events ───────────────────────────────────────────────
            touch.read()
            for event_type, tx, ty in touch.get_events():

                if event_type == 'down':
                    hit = _hit_test(rects[current_layer], tx, ty)
                    if hit:
                        # Skip non-interactive labels
                        if hit['l'] in ('opt_title', 'br_label', 'br_bar'):
                            continue
                        pressed_label = hit['l']
                        pressed_key = hit
                        press_time = now
                        last_repeat_time = 0.0
                        needs_redraw = True

                elif event_type == 'up':
                    if pressed_label and pressed_key:
                        hit = _hit_test(rects[current_layer], tx, ty)
                        if hit and hit['l'] == pressed_label:
                            action = hit.get('a')

                            # ── Options actions ────────────────────────────
                            if action and action.startswith('accent_'):
                                idx = int(action.split('_')[1])
                                if 0 <= idx < len(ACCENT_PRESETS):
                                    accent_index = idx
                                    accent = ACCENT_PRESETS[idx]
                                    save_settings(accent_index, brightness_val)
                                    needs_redraw = True

                            elif action == 'bright_up':
                                brightness_val = brightness_up(brightness_val)
                                save_settings(accent_index, brightness_val)
                                needs_redraw = True

                            elif action == 'bright_down':
                                brightness_val = brightness_down(brightness_val)
                                save_settings(accent_index, brightness_val)
                                needs_redraw = True

                            # ── Options layer entry ────────────────────────
                            elif action == 'options':
                                prev_layer = current_layer
                                current_layer = 'options'
                                shift_sticky = False
                                shift_active = False

                            # ── Layer switching ────────────────────────────
                            elif action == 'shift':
                                current_layer = 'shift'
                                shift_sticky = True
                                shift_active = True

                            elif action == 'unshift':
                                current_layer = 'main'
                                shift_sticky = False
                                shift_active = False

                            elif action in ('symbols', 'main', 'nav'):
                                current_layer = action
                                shift_sticky = False
                                shift_active = False

                            # ── Normal key emission ────────────────────────
                            elif hit['c'] is not None:
                                if hit['l'] not in REPEATABLE_KEYS or last_repeat_time == 0:
                                    uinput.press(hit['c'], shift=hit.get('s', False))

                                # Shift auto-return
                                if (current_layer == 'shift' and shift_sticky
                                        and len(hit['d']) == 1 and hit['d'].isalpha()):
                                    current_layer = 'main'
                                    shift_sticky = False
                                    shift_active = False

                    pressed_label = None
                    pressed_key = None
                    needs_redraw = True

            # ── Key repeat ─────────────────────────────────────────────────
            if (pressed_label and pressed_key
                    and pressed_key['l'] in REPEATABLE_KEYS
                    and pressed_key['c'] is not None):
                elapsed = now - press_time
                if elapsed > REPEAT_DELAY:
                    if last_repeat_time == 0.0 or now - last_repeat_time > REPEAT_RATE:
                        uinput.press(pressed_key['c'], shift=pressed_key.get('s', False))
                        last_repeat_time = now

            # ── Redraw ─────────────────────────────────────────────────────
            if needs_redraw:
                draw_keyboard(
                    sdl, ren, rects[current_layer],
                    pressed_label=pressed_label,
                    shift_active=shift_active,
                    accent=accent,
                    brightness_pct=_brightness_pct(),
                )
                needs_redraw = False

            sdl.delay(16)

    except KeyboardInterrupt:
        print("\n[engine] Interrupted")
    finally:
        joypad.running = False
        touch.close()
        uinput.close()
        sdl.destroy_renderer(ren)
        sdl.destroy_window(win)
        sdl.quit()
        print("[engine] Shutdown complete")

    return 0
