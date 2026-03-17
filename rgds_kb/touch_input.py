"""
touch_input.py — Raw multitouch event reader for the Goodix touchscreen.

Reads /dev/input/event2 directly, parses input_event structs, and produces
simple ('down', x, y) / ('up', x, y) events.
"""

import fcntl
import os
import struct
import threading

from .constants import (
    INPUT_EVENT_FORMAT, INPUT_EVENT_SIZE,
    EV_SYN, EV_KEY, EV_ABS,
    ABS_MT_POSITION_X, ABS_MT_POSITION_Y, ABS_MT_TRACKING_ID,
    BTN_TOUCH, EVIOCGRAB,
)

# Track grabbed file descriptors for cleanup on crash
_grabbed_fds = []


def cleanup_grabs():
    """Release all grabbed input devices. Called via atexit."""
    for fd in _grabbed_fds:
        try:
            fcntl.ioctl(fd, EVIOCGRAB, 0)
        except OSError:
            pass


class TouchInput:
    """Reads multitouch events from the capacitive touchscreen.

    The touchscreen is opened in non-blocking mode. Call read() in your main
    loop to ingest raw events, then get_events() to retrieve parsed touch
    down/up events.

    When the keyboard is visible, call grab() to prevent touches from leaking
    to other apps. Call ungrab() when hiding the keyboard.
    """

    def __init__(self, device_path):
        self._path = device_path
        self._fd = None
        self._grabbed = False

        # Current touch position (updated by ABS_MT events)
        self._touch_x = -1
        self._touch_y = -1

        # Parsed event queue (thread-safe)
        self._events = []
        self._lock = threading.Lock()

    @property
    def is_open(self):
        return self._fd is not None

    def open(self):
        """Open the touch device in non-blocking read mode."""
        self._fd = os.open(self._path, os.O_RDONLY | os.O_NONBLOCK)
        print(f"[touch] Opened {self._path}")

    def grab(self):
        """Exclusively grab the touch device (prevents other apps from seeing touches)."""
        if self._fd is not None and not self._grabbed:
            try:
                fcntl.ioctl(self._fd, EVIOCGRAB, 1)
                self._grabbed = True
                _grabbed_fds.append(self._fd)
                print("[touch] Grabbed exclusively")
            except OSError as err:
                print(f"[touch] Grab failed: {err}")

    def ungrab(self):
        """Release exclusive grab on the touch device."""
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
        """Read available raw events from the device and parse into touch events.

        Call this every frame. Non-blocking — returns immediately if no data.
        """
        if self._fd is None:
            return

        try:
            data = os.read(self._fd, INPUT_EVENT_SIZE * 32)
        except OSError:
            return  # EAGAIN — no data available

        offset = 0
        new_down = False
        new_up = False

        while offset + INPUT_EVENT_SIZE <= len(data):
            _, _, event_type, code, value = struct.unpack_from(
                INPUT_EVENT_FORMAT, data, offset
            )
            offset += INPUT_EVENT_SIZE

            if event_type == EV_ABS:
                if code == ABS_MT_POSITION_X:
                    self._touch_x = value
                elif code == ABS_MT_POSITION_Y:
                    self._touch_y = value
                elif code == ABS_MT_TRACKING_ID:
                    if value >= 0:
                        new_down = True
                    else:
                        new_up = True

            elif event_type == EV_KEY and code == BTN_TOUCH:
                if value == 1:
                    new_down = True
                elif value == 0:
                    new_up = True

            elif event_type == EV_SYN:
                with self._lock:
                    if new_down and self._touch_x >= 0:
                        self._events.append(('down', self._touch_x, self._touch_y))
                        new_down = False
                    if new_up:
                        self._events.append(('up', self._touch_x, self._touch_y))
                        new_up = False

    def get_events(self):
        """Return and clear all pending touch events.

        Returns:
            List of tuples: ('down', x, y) or ('up', x, y)
        """
        with self._lock:
            events = self._events[:]
            self._events.clear()
        return events

    def close(self):
        """Ungrab and close the touch device."""
        self.ungrab()
        if self._fd is not None:
            os.close(self._fd)
            self._fd = None
            print("[touch] Closed")
