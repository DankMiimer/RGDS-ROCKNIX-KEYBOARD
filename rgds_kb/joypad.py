"""
joypad.py — Background thread that monitors the joypad for the R3 button.

Watches /dev/input/event6 for BTN_THUMBR press events and calls a callback.
Runs as a daemon thread so it doesn't prevent shutdown.
"""

import os
import select
import struct
import threading
import time

from .constants import (
    INPUT_EVENT_FORMAT, INPUT_EVENT_SIZE,
    EV_KEY,
)


class JoypadMonitor(threading.Thread):
    """Daemon thread that watches a joypad device for a specific button press.

    Args:
        device_path: Path to the joypad input device (e.g. /dev/input/event6)
        button_code: evdev button code to watch for (e.g. BTN_THUMBR = 318)
        on_press: Callable invoked (from this thread) when the button is pressed
    """

    def __init__(self, device_path, button_code, on_press):
        super().__init__(daemon=True)
        self._path = device_path
        self._button = button_code
        self._on_press = on_press
        self.running = True

    def run(self):
        try:
            fd = os.open(self._path, os.O_RDONLY | os.O_NONBLOCK)
        except OSError:
            print(f"[joypad] Cannot open {self._path}")
            return

        print(f"[joypad] Monitoring button {self._button} on {self._path}")

        while self.running:
            try:
                readable, _, _ = select.select([fd], [], [], 0.5)
                if not readable:
                    continue

                data = os.read(fd, INPUT_EVENT_SIZE * 16)
                offset = 0
                while offset + INPUT_EVENT_SIZE <= len(data):
                    _, _, event_type, code, value = struct.unpack_from(
                        INPUT_EVENT_FORMAT, data, offset
                    )
                    offset += INPUT_EVENT_SIZE

                    if event_type == EV_KEY and code == self._button and value == 1:
                        self._on_press()

            except OSError:
                time.sleep(0.1)

        os.close(fd)
        print("[joypad] Monitor stopped")
