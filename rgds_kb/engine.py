"""
engine.py — Main application loop: event dispatch, state machine, key repeat.

Coordinates all subsystems (SDL, touch, joypad, uinput, renderer) and runs
the frame loop at ~60fps. Handles:
  - R3 toggle (show/hide keyboard)
  - Touch hit-testing against key rects
  - Key press/release → uinput injection
  - Shift auto-return after one uppercase letter
  - Held-key repeat for backspace, space, arrows
  - Periodic DSI-1 power re-assertion
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
)
from .sdl import SDL
from .uinput_device import UinputDevice
from .touch_input import TouchInput, cleanup_grabs
from .joypad import JoypadMonitor
from .layouts import build_layouts
from .renderer import compute_key_rects, draw_keyboard, draw_blank


# =============================================================================
# Sway helpers
# =============================================================================

def _sway_cmd(cmd):
    """Run a swaymsg command, ignoring errors."""
    try:
        subprocess.run(['swaymsg', cmd], capture_output=True, timeout=2)
    except Exception:
        pass


def _place_window():
    """Move our window to DSI-1 and make it fullscreen."""
    _sway_cmd('output DSI-1 power on')
    _sway_cmd(f'[title="{WINDOW_TITLE}"] move to output DSI-1')
    _sway_cmd(f'[title="{WINDOW_TITLE}"] fullscreen enable')


# =============================================================================
# Hit testing
# =============================================================================

def _hit_test(rows, x, y):
    """Find which key (if any) contains the point (x, y).

    Returns the key dict, or None.
    """
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

    # Register crash-safety cleanup
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
        WINDOW_TITLE,
        0x1FFF0000, 0x1FFF0000,  # SDL_WINDOWPOS_UNDEFINED
        SCREEN_WIDTH, SCREEN_HEIGHT,
        0x04,  # SDL_WINDOW_SHOWN
    )
    ren = sdl.create_renderer(win, -1, 0x06)  # ACCELERATED | PRESENTVSYNC

    # Initial blank frame, then place on DSI-1
    sdl.set_draw_color(ren, 30, 30, 50, 255)
    sdl.clear(ren)
    sdl.present(ren)
    time.sleep(0.5)
    _place_window()
    time.sleep(0.3)
    draw_blank(sdl, ren)

    # ── Build layouts and compute geometry ─────────────────────────────────
    layouts = build_layouts()
    rects = {name: compute_key_rects(layout) for name, layout in layouts.items()}

    # ── Subsystems ─────────────────────────────────────────────────────────
    uinput = UinputDevice()
    uinput.setup()

    touch = TouchInput(TOUCH_DEVICE)
    touch.open()

    # ── State ──────────────────────────────────────────────────────────────
    visible = False
    running = True
    current_layer = 'main'

    pressed_label = None      # Label of the key currently under the finger
    pressed_key = None        # Key dict of the key currently under the finger
    press_time = 0.0          # When the finger went down
    shift_active = False      # Visual shift indicator
    shift_sticky = False      # Shift was activated (auto-return after one letter)

    toggle_flag = False       # Set by joypad thread when R3 is pressed
    needs_redraw = True
    last_repeat_time = 0.0
    last_reassert_time = time.time()

    # ── R3 toggle callback (called from joypad thread) ─────────────────────
    def on_r3_press():
        nonlocal toggle_flag
        toggle_flag = True

    # ── Signal handlers ────────────────────────────────────────────────────
    def on_signal(sig, frame):
        nonlocal running
        running = False

    signal.signal(signal.SIGTERM, on_signal)
    signal.signal(signal.SIGINT, on_signal)

    # ── Start joypad monitor ───────────────────────────────────────────────
    joypad = JoypadMonitor(JOYPAD_DEVICE, BTN_THUMBR, on_r3_press)
    joypad.start()
    print("[engine] Running — press R3 to toggle keyboard")

    # ── Main loop ──────────────────────────────────────────────────────────
    try:
        while running:
            now = time.time()

            # Drain SDL event queue (we don't use SDL events, but must pump)
            while sdl.poll_event() is not None:
                pass

            # ── Handle R3 toggle ───────────────────────────────────────────
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
                    shift_active = False
                    shift_sticky = False
                    pressed_label = None
                    pressed_key = None
                    draw_blank(sdl, ren)
                    print("[engine] Keyboard hidden")

            # ── Periodic DSI-1 re-assertion ────────────────────────────────
            if visible and now - last_reassert_time > REASSERT_INTERVAL:
                _place_window()
                last_reassert_time = now

            # ── Sleep when hidden ──────────────────────────────────────────
            if not visible:
                sdl.delay(50)
                continue

            # ── Read touch events ──────────────────────────────────────────
            touch.read()
            for event_type, tx, ty in touch.get_events():

                if event_type == 'down':
                    # Find which key the finger landed on
                    hit = _hit_test(rects[current_layer], tx, ty)
                    if hit:
                        pressed_label = hit['l']
                        pressed_key = hit
                        press_time = now
                        last_repeat_time = 0.0
                        needs_redraw = True

                elif event_type == 'up':
                    if pressed_label and pressed_key:
                        # Check if finger is still over the same key
                        hit = _hit_test(rects[current_layer], tx, ty)
                        if hit and hit['l'] == pressed_label:
                            _handle_key_action(
                                hit, uinput, rects, current_layer,
                                shift_sticky, shift_active, last_repeat_time,
                            )
                            action = hit.get('a')

                            # Layer switching
                            if action == 'shift':
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
                            elif (
                                current_layer == 'shift'
                                and shift_sticky
                                and len(hit['d']) == 1
                                and hit['d'].isalpha()
                            ):
                                # Auto-return from shift after one letter
                                current_layer = 'main'
                                shift_sticky = False
                                shift_active = False

                    pressed_label = None
                    pressed_key = None
                    needs_redraw = True

            # ── Key repeat (held keys) ─────────────────────────────────────
            if (
                pressed_label
                and pressed_key
                and pressed_key['l'] in REPEATABLE_KEYS
                and pressed_key['c'] is not None
            ):
                elapsed = now - press_time
                if elapsed > REPEAT_DELAY:
                    if last_repeat_time == 0.0 or now - last_repeat_time > REPEAT_RATE:
                        uinput.press(pressed_key['c'], shift=pressed_key.get('s', False))
                        last_repeat_time = now

            # ── Redraw if needed ───────────────────────────────────────────
            if needs_redraw:
                draw_keyboard(
                    sdl, ren,
                    rects[current_layer],
                    pressed_label=pressed_label,
                    shift_active=shift_active,
                )
                needs_redraw = False

            sdl.delay(16)  # ~60fps cap

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


def _handle_key_action(key, uinput, rects, current_layer,
                       shift_sticky, shift_active, last_repeat_time):
    """Emit the keycode for a tapped key (if it has one and isn't repeat-only).

    Action-only keys (shift, layer switches) are handled by the caller.
    Keys that are repeatable and have already emitted via repeat are skipped.
    """
    if key.get('a'):
        return  # Action-only key — no keycode to emit

    if key['c'] is None:
        return

    # If this key is repeatable and was already fired by the repeat system,
    # don't fire again on release
    if key['l'] in REPEATABLE_KEYS and last_repeat_time > 0:
        return

    uinput.press(key['c'], shift=key.get('s', False))
