"""
uinput_device.py — Virtual keyboard via Linux uinput.

Creates a /dev/input/eventX device that looks like a real keyboard to the
system. Emits EV_KEY events so that Sway/Wayland delivers them to the
focused application.
"""

import fcntl
import os
import struct
import time

from .constants import (
    INPUT_EVENT_FORMAT,
    EV_SYN, EV_KEY,
    UI_SET_EVBIT, UI_SET_KEYBIT, UI_DEV_CREATE, UI_DEV_DESTROY,
    KEY_LEFTSHIFT,
    ALL_KEYCODES,
)


class UinputDevice:
    """Virtual keyboard that injects keystrokes via /dev/uinput.

    Usage:
        dev = UinputDevice()
        dev.setup()
        dev.press(KEY_A, shift=False)
        ...
        dev.close()
    """

    UINPUT_PATH = "/dev/uinput"

    def __init__(self):
        self._fd = None

    @property
    def is_open(self):
        return self._fd is not None

    def setup(self):
        """Open /dev/uinput, register keycodes, and create the virtual device."""
        self._fd = os.open(self.UINPUT_PATH, os.O_WRONLY | os.O_NONBLOCK)

        # Enable EV_KEY event type
        fcntl.ioctl(self._fd, UI_SET_EVBIT, EV_KEY)

        # Register every keycode we might emit
        for keycode in ALL_KEYCODES:
            fcntl.ioctl(self._fd, UI_SET_KEYBIT, keycode)

        # Build uinput_user_dev struct:
        #   char name[80] + struct input_id {bustype, vendor, product, version} + int ff_effects_max
        #   + abs info padding
        name = b"RGDS Virtual Keyboard\0" + b"\0" * 58  # 80 bytes
        input_id = struct.pack('HHHHi', 3, 0x1234, 0x5678, 1, 0)  # BUS_VIRTUAL
        abs_padding = b"\0" * (64 * 4 * 4)  # ABS_CNT * sizeof(int) * 4 arrays
        os.write(self._fd, name + input_id + abs_padding)

        fcntl.ioctl(self._fd, UI_DEV_CREATE)
        time.sleep(0.3)  # Let kernel set up the device
        print("[uinput] Virtual keyboard created")

    def _emit(self, event_type, code, value):
        """Write a single input_event to uinput."""
        now = time.time()
        sec = int(now)
        usec = int((now % 1) * 1e6)
        os.write(self._fd, struct.pack(INPUT_EVENT_FORMAT, sec, usec, event_type, code, value))

    def press(self, keycode, shift=False):
        """Emit a complete key press+release, optionally with Shift held.

        Args:
            keycode: Linux KEY_* constant (e.g. KEY_A = 30)
            shift: If True, holds KEY_LEFTSHIFT during the press
        """
        if shift:
            self._emit(EV_KEY, KEY_LEFTSHIFT, 1)
            self._emit(EV_SYN, 0, 0)

        self._emit(EV_KEY, keycode, 1)   # Key down
        self._emit(EV_SYN, 0, 0)
        self._emit(EV_KEY, keycode, 0)   # Key up
        self._emit(EV_SYN, 0, 0)

        if shift:
            self._emit(EV_KEY, KEY_LEFTSHIFT, 0)
            self._emit(EV_SYN, 0, 0)

    def close(self):
        """Destroy the virtual device and close the file descriptor."""
        if self._fd is not None:
            try:
                fcntl.ioctl(self._fd, UI_DEV_DESTROY)
            except OSError:
                pass
            os.close(self._fd)
            self._fd = None
            print("[uinput] Device closed")
