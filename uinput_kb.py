"""
Virtual keyboard via Linux uinput.
Injects EV_KEY events that appear as a physical keyboard to the compositor.
"""

import os, struct, fcntl, time

from layouts import ALL_KEYCODES, KEY_LEFTSHIFT

# ---------------------------------------------------------------------------
# Linux evdev / uinput constants
# ---------------------------------------------------------------------------

EV_SYN = 0x00
EV_KEY = 0x01
EV_FMT = 'llHHi'
EV_SIZE = struct.calcsize(EV_FMT)

UI_SET_EVBIT  = 0x40045564
UI_SET_KEYBIT = 0x40045565
UI_DEV_CREATE = 0x5501
UI_DEV_DESTROY = 0x5502

# ---------------------------------------------------------------------------
# Virtual keyboard
# ---------------------------------------------------------------------------

class VirtualKeyboard:
    """Injects keystrokes via /dev/uinput."""

    __slots__ = ('_fd',)

    def __init__(self):
        self._fd = None

    def setup(self):
        """Create the uinput device."""
        self._fd = os.open("/dev/uinput", os.O_WRONLY | os.O_NONBLOCK)
        fcntl.ioctl(self._fd, UI_SET_EVBIT, EV_KEY)
        for code in ALL_KEYCODES:
            fcntl.ioctl(self._fd, UI_SET_KEYBIT, code)

        # uinput_user_dev: name[80] + id(4×u16) + ff_effects_max(i32) + absmax[64×i32] ...
        name = b"RGDS Virtual Keyboard\0" + b"\0" * 58  # 80 bytes
        dev_id = struct.pack('HHHHi', 3, 0x1234, 0x5678, 1, 0)
        abs_data = b"\0" * (64 * 4 * 4)  # 4 arrays × 64 entries × 4 bytes
        os.write(self._fd, name + dev_id + abs_data)
        fcntl.ioctl(self._fd, UI_DEV_CREATE)
        time.sleep(0.3)
        print("[uinput] Virtual keyboard created")

    def _emit(self, ev_type, code, value):
        """Write a single input event."""
        t = int(time.time())
        us = int((time.time() % 1) * 1e6)
        os.write(self._fd, struct.pack(EV_FMT, t, us, ev_type, code, value))

    def press(self, code, shift=False):
        """Send a key press+release, optionally with shift."""
        if shift:
            self._emit(EV_KEY, KEY_LEFTSHIFT, 1)
            self._emit(EV_SYN, 0, 0)
        self._emit(EV_KEY, code, 1)
        self._emit(EV_SYN, 0, 0)
        self._emit(EV_KEY, code, 0)
        self._emit(EV_SYN, 0, 0)
        if shift:
            self._emit(EV_KEY, KEY_LEFTSHIFT, 0)
            self._emit(EV_SYN, 0, 0)

    def close(self):
        """Destroy the uinput device."""
        if self._fd is not None:
            try:
                fcntl.ioctl(self._fd, UI_DEV_DESTROY)
            except OSError:
                pass
            try:
                os.close(self._fd)
            except OSError:
                pass
            self._fd = None
