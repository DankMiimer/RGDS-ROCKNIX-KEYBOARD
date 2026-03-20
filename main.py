#!/usr/bin/env python3
"""
RGDS Virtual Keyboard v5
========================
Phone-style touch keyboard for Anbernic RG DS / ROCKNIX.
Renders on DSI-1 (bottom screen), injects keystrokes via uinput.

v5: Epoll event loop, dirty rendering, auto-detect devices, themes,
    JSON config, signal support, haptic feedback.
"""

import os, sys, struct, fcntl, time, signal, subprocess, atexit, gc, selectors

# Ensure our package directory is on the path
_pkg_dir = os.path.dirname(os.path.abspath(__file__))
if _pkg_dir not in sys.path:
    sys.path.insert(0, _pkg_dir)

from config import Settings, THEMES, THEME_ORDER
from devices import find_touchscreen, find_joypad, find_haptic
from layouts import build_all, REPEATABLE_LABELS, KEY_LEFTSHIFT
from renderer import Renderer, W, H
from sdl2 import SDL
from uinput_kb import VirtualKeyboard

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TITLE = "RGDS Keyboard [Bottom]"
BTN_THUMBR = 318
REASSERT_INTERVAL = 1.5     # seconds between DSI-1 power reassertion

EV_FMT = 'llHHi'
EV_SIZE = struct.calcsize(EV_FMT)
EV_SYN = 0x00; EV_KEY = 0x01; EV_ABS = 0x03
ABS_MT_X = 0x35; ABS_MT_Y = 0x36; ABS_MT_ID = 0x39
BTN_TOUCH = 330
EVIOCGRAB = 0x40044590

# Signal numbers for show/hide/toggle (wvkbd convention)
SIG_HIDE   = signal.SIGUSR1
SIG_SHOW   = signal.SIGUSR2
SIG_TOGGLE = signal.SIGRTMIN

# Haptic
HAPTIC_DURATION_MS = 20
HAPTIC_SYSFS = "/sys/class/leds/vibrator/brightness"

# ---------------------------------------------------------------------------
# Crash-safe grab tracking
# ---------------------------------------------------------------------------

_grabbed_fds = []

def _emergency_cleanup():
    for fd in _grabbed_fds:
        try:
            fcntl.ioctl(fd, EVIOCGRAB, 0)
        except Exception:
            pass

atexit.register(_emergency_cleanup)

# ---------------------------------------------------------------------------
# Sway helper
# ---------------------------------------------------------------------------

def _sway(cmd):
    try:
        subprocess.run(['swaymsg', cmd], capture_output=True, timeout=2)
    except Exception:
        pass

def _place_window():
    _sway('output DSI-1 power on')
    _sway(f'[title="{TITLE}"] move to output DSI-1')
    _sway(f'[title="{TITLE}"] fullscreen enable')

def _set_brightness(value):
    """Set DSI-1 brightness via swaymsg (float 0.0–1.0)."""
    v = max(0.0, min(1.0, value))
    _sway(f'output DSI-1 brightness {v:.2f}')


# ---------------------------------------------------------------------------
# Touch reader
# ---------------------------------------------------------------------------

class TouchReader:
    """Reads multitouch events from an evdev touchscreen."""

    __slots__ = ('_fd', '_path', '_grabbed', '_tx', '_ty', '_events')

    def __init__(self, path):
        self._path = path
        self._fd = None
        self._grabbed = False
        self._tx = -1
        self._ty = -1
        self._events = []

    @property
    def fd(self):
        return self._fd

    def open(self):
        self._fd = os.open(self._path, os.O_RDONLY | os.O_NONBLOCK)
        print(f"[touch] Opened {self._path}")

    def grab(self):
        if self._fd is not None and not self._grabbed:
            try:
                fcntl.ioctl(self._fd, EVIOCGRAB, 1)
                self._grabbed = True
                _grabbed_fds.append(self._fd)
                print("[touch] Grabbed exclusively")
            except OSError as e:
                print(f"[touch] Grab failed: {e}")

    def ungrab(self):
        if self._fd is not None and self._grabbed:
            try:
                fcntl.ioctl(self._fd, EVIOCGRAB, 0)
            except OSError:
                pass
            self._grabbed = False
            if self._fd in _grabbed_fds:
                _grabbed_fds.remove(self._fd)
            print("[touch] Released")

    def read(self):
        """Read available events.  Call from main loop when fd is readable."""
        if self._fd is None:
            return
        try:
            data = os.read(self._fd, EV_SIZE * 32)
        except OSError:
            return
        off = 0
        nd = False; nu = False
        while off + EV_SIZE <= len(data):
            _, _, et, code, val = struct.unpack_from(EV_FMT, data, off)
            off += EV_SIZE
            if et == EV_ABS:
                if code == ABS_MT_X:
                    self._tx = val
                elif code == ABS_MT_Y:
                    self._ty = val
                elif code == ABS_MT_ID:
                    if val >= 0:
                        nd = True
                    else:
                        nu = True
            elif et == EV_KEY and code == BTN_TOUCH:
                nd = (val == 1)
                nu = (val == 0)
            elif et == EV_SYN:
                if nd and self._tx >= 0:
                    self._events.append(('d', self._tx, self._ty))
                    nd = False
                if nu:
                    self._events.append(('u', self._tx, self._ty))
                    nu = False

    def drain(self):
        """Return and clear pending events."""
        evts = self._events[:]
        self._events.clear()
        return evts

    def close(self):
        self.ungrab()
        if self._fd is not None:
            os.close(self._fd)
            self._fd = None


# ---------------------------------------------------------------------------
# Joypad reader (integrated into main loop via selectors)
# ---------------------------------------------------------------------------

class JoypadReader:
    """Reads joypad button events — integrated into selectors loop."""

    __slots__ = ('_fd', '_path', '_btn')

    def __init__(self, path, button=BTN_THUMBR):
        self._path = path
        self._fd = None
        self._btn = button

    @property
    def fd(self):
        return self._fd

    def open(self):
        try:
            self._fd = os.open(self._path, os.O_RDONLY | os.O_NONBLOCK)
            print(f"[joy] Opened {self._path}")
        except OSError:
            print(f"[joy] Cannot open {self._path}")

    def read(self):
        """Read events.  Returns True if toggle button was pressed."""
        if self._fd is None:
            return False
        try:
            data = os.read(self._fd, EV_SIZE * 16)
        except OSError:
            return False
        off = 0; toggled = False
        while off + EV_SIZE <= len(data):
            _, _, et, code, val = struct.unpack_from(EV_FMT, data, off)
            off += EV_SIZE
            if et == EV_KEY and code == self._btn and val == 1:
                toggled = True
        return toggled

    def close(self):
        if self._fd is not None:
            os.close(self._fd)
            self._fd = None


# ---------------------------------------------------------------------------
# Haptic feedback
# ---------------------------------------------------------------------------

class Haptic:
    """Best-effort haptic feedback via sysfs."""

    __slots__ = ('_path', '_enabled')

    def __init__(self, path, enabled=True):
        self._path = path
        self._enabled = enabled and (path is not None)

    def buzz(self):
        if not self._enabled or not self._path:
            return
        try:
            if self._path.startswith("/sys/"):
                with open(self._path, 'w') as f:
                    f.write("128")
                # Schedule off after duration — fire-and-forget
                # (in practice the motor auto-stops on most devices)
            # EV_FF path would go here if we add it later
        except OSError:
            pass


# ---------------------------------------------------------------------------
# Main application
# ---------------------------------------------------------------------------

class KeyboardApp:
    """Orchestrates the virtual keyboard lifecycle."""

    def __init__(self):
        self.settings = Settings()
        self.visible = False
        self.running = True
        self.layer = 'main'
        self.shift_active = False
        self.shift_sticky = False
        self.pressed_label = None
        self.pressed_key = None
        self.press_time = 0
        self.last_repeat = 0
        self._toggle_pending = False

        # Signal pipe for waking selectors from signal handlers
        self._sig_r, self._sig_w = os.pipe()
        os.set_blocking(self._sig_r, False)
        os.set_blocking(self._sig_w, False)

    def run(self):
        os.environ['SDL_VIDEODRIVER'] = 'wayland'
        cfg = self.settings

        # --- SDL2 init ---
        SDL.set_hint("SDL_RENDER_BATCHING", "1")
        if SDL.init() != 0:
            print(f"[sdl] Init failed: {SDL.get_error()}")
            sys.exit(1)

        _sway('output DSI-1 power on')
        time.sleep(0.2)

        win = SDL.create_window(TITLE, 0x1FFF0000, 0x1FFF0000, W, H, 0x04)
        ren = SDL.create_renderer(win, -1, 0x06)
        SDL.set_draw_color(ren, 30, 30, 50, 255)
        SDL.clear(ren)
        SDL.present(ren)
        time.sleep(0.5)
        _place_window()
        time.sleep(0.3)

        # --- Build layouts ---
        layouts, rects = build_all()

        # --- Renderer ---
        theme = cfg.theme_colors
        renderer = Renderer(ren, theme)
        renderer.render_black()

        # --- uinput ---
        vkb = VirtualKeyboard()
        vkb.setup()

        # --- Device detection ---
        touch_path = cfg.touch_device or find_touchscreen()
        joy_path = cfg.joypad_device or find_joypad()
        haptic_path = find_haptic()

        touch = TouchReader(touch_path)
        touch.open()
        joy = JoypadReader(joy_path)
        joy.open()
        haptic = Haptic(haptic_path, enabled=cfg.haptic_enabled)

        # --- Apply saved brightness ---
        _set_brightness(cfg.brightness)

        # --- Signals ---
        self._install_signals()

        # --- GC tuning ---
        gc.collect()
        gc.freeze()
        gc.set_threshold(50000, 20, 20)

        # --- Selectors-based event loop ---
        sel = selectors.DefaultSelector()
        if touch.fd is not None:
            sel.register(touch.fd, selectors.EVENT_READ, 'touch')
        if joy.fd is not None:
            sel.register(joy.fd, selectors.EVENT_READ, 'joy')
        sel.register(self._sig_r, selectors.EVENT_READ, 'signal')

        print("[app] Running — R3 to toggle, SIGUSR1/2/SIGRTMIN for hide/show/toggle")
        last_assert = time.time()
        dirty = True
        full_redraw = True

        try:
            while self.running:
                now = time.time()

                # Determine timeout
                if self.visible:
                    if self.pressed_label and self.pressed_key:
                        timeout = 0.016  # 60fps during key repeat
                    else:
                        timeout = 0.033  # 30fps idle visible
                else:
                    # When hidden: wake every 1.5s for DSI-1 reassertion
                    timeout = REASSERT_INTERVAL

                # Wait for events
                ready = sel.select(timeout=timeout)
                now = time.time()

                # Drain SDL event queue (needed for Wayland protocol)
                while SDL.poll_event():
                    pass

                # Process selectors events
                for key, _ in ready:
                    if key.data == 'touch':
                        touch.read()
                    elif key.data == 'joy':
                        if joy.read():
                            self._toggle_pending = True
                    elif key.data == 'signal':
                        self._drain_signal_pipe()

                # Handle toggle
                if self._toggle_pending:
                    self._toggle_pending = False
                    self.visible = not self.visible
                    if self.visible:
                        touch.grab()
                        dirty = True
                        full_redraw = True
                        print("[app] Shown")
                    else:
                        touch.ungrab()
                        self.layer = 'main'
                        self.shift_active = False
                        self.shift_sticky = False
                        self.pressed_label = None
                        self.pressed_key = None
                        renderer.render_black()
                        print("[app] Hidden")

                # Periodic DSI-1 reassertion
                if self.visible and now - last_assert > REASSERT_INTERVAL:
                    _place_window()
                    last_assert = now

                if not self.visible:
                    continue

                # --- Process touch events ---
                for et, tx, ty in touch.drain():
                    if et == 'd':
                        # Touch down — find which key
                        for row in rects[self.layer]:
                            for k in row:
                                x, y, w, h = k['rect']
                                if x <= tx <= x + w and y <= ty <= y + h:
                                    self.pressed_label = k['l']
                                    self.pressed_key = k
                                    self.press_time = now
                                    self.last_repeat = 0
                                    dirty = True

                    elif et == 'u':
                        # Touch up — fire action if still on same key
                        if self.pressed_label and self.pressed_key:
                            hit = None
                            for row in rects[self.layer]:
                                for k in row:
                                    x, y, w, h = k['rect']
                                    if x <= tx <= x + w and y <= ty <= y + h:
                                        hit = k

                            if hit and hit['l'] == self.pressed_label:
                                action = hit.get('a')
                                if action == 'shift':
                                    self.layer = 'shift'
                                    self.shift_sticky = True
                                    self.shift_active = True
                                    full_redraw = True
                                elif action == 'unshift':
                                    self.layer = 'main'
                                    self.shift_sticky = False
                                    self.shift_active = False
                                    full_redraw = True
                                elif action in ('symbols', 'main', 'nav'):
                                    self.layer = action
                                    self.shift_sticky = False
                                    self.shift_active = False
                                    full_redraw = True
                                elif hit['c']:
                                    # Only emit if not already emitted by repeat
                                    if hit['l'] not in REPEATABLE_LABELS or self.last_repeat == 0:
                                        vkb.press(hit['c'], shift=hit.get('s', False))
                                        haptic.buzz()
                                    # Auto-return from shift after typing a letter
                                    if (self.layer == 'shift' and self.shift_sticky
                                            and len(hit['d']) == 1 and hit['d'].isalpha()):
                                        self.layer = 'main'
                                        self.shift_sticky = False
                                        self.shift_active = False
                                        full_redraw = True

                        self.pressed_label = None
                        self.pressed_key = None
                        dirty = True

                # --- Key repeat ---
                if (self.pressed_label and self.pressed_key
                        and self.pressed_key['l'] in REPEATABLE_LABELS
                        and self.pressed_key['c']):
                    elapsed = now - self.press_time
                    if elapsed > cfg.repeat_delay:
                        if self.last_repeat == 0 or now - self.last_repeat > cfg.repeat_rate:
                            vkb.press(self.pressed_key['c'],
                                      shift=self.pressed_key.get('s', False))
                            self.last_repeat = now

                # --- Render ---
                if full_redraw:
                    renderer.render_full(rects[self.layer], self.pressed_label,
                                         self.shift_active)
                    full_redraw = False
                    dirty = False
                elif dirty:
                    renderer.render_dirty(rects[self.layer], self.pressed_label,
                                          self.shift_active)
                    dirty = False

        except KeyboardInterrupt:
            print("\n[app] Interrupted")
        finally:
            sel.close()
            os.close(self._sig_r)
            os.close(self._sig_w)
            touch.close()
            joy.close()
            vkb.close()
            renderer.destroy()
            SDL.destroy_renderer(ren)
            SDL.destroy_window(win)
            SDL.quit()
            print("[app] Shutdown complete")

    # --- Signal handling ---

    def _install_signals(self):
        signal.signal(signal.SIGTERM, self._on_stop)
        signal.signal(signal.SIGINT, self._on_stop)
        signal.signal(SIG_HIDE, self._on_signal)
        signal.signal(SIG_SHOW, self._on_signal)
        signal.signal(SIG_TOGGLE, self._on_signal)

    def _on_stop(self, signum, frame):
        self.running = False
        self._wake_selector()

    def _on_signal(self, signum, frame):
        """Signal handler — writes to pipe to wake the selector."""
        try:
            os.write(self._sig_w, signum.to_bytes(1, 'little'))
        except OSError:
            pass

    def _drain_signal_pipe(self):
        """Read pending signal bytes from the pipe."""
        try:
            data = os.read(self._sig_r, 64)
        except OSError:
            return
        for b in data:
            if b == SIG_HIDE:
                if self.visible:
                    self._toggle_pending = True
            elif b == SIG_SHOW:
                if not self.visible:
                    self._toggle_pending = True
            elif b == SIG_TOGGLE:
                self._toggle_pending = True

    def _wake_selector(self):
        try:
            os.write(self._sig_w, b'\x00')
        except OSError:
            pass


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    KeyboardApp().run()
