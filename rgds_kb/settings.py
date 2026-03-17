"""
settings.py — Persistent settings: accent color index and screen brightness.

Saves to /storage/.rgds_keyboard_settings as simple key=value lines.
Brightness is controlled via /sys/class/backlight/*/brightness.
"""

import glob
import os

from .constants import (
    SETTINGS_FILE, BRIGHTNESS_PATH,
    BRIGHTNESS_STEP, BRIGHTNESS_MIN, BRIGHTNESS_MAX,
    ACCENT_PRESETS, DEFAULT_ACCENT_INDEX,
)


def _find_backlight():
    """Find the first backlight sysfs path, or None."""
    paths = glob.glob(os.path.join(BRIGHTNESS_PATH, "*", "brightness"))
    return paths[0] if paths else None


def _find_max_brightness():
    """Read the max_brightness value from sysfs."""
    paths = glob.glob(os.path.join(BRIGHTNESS_PATH, "*", "max_brightness"))
    if paths:
        try:
            with open(paths[0], 'r') as f:
                return int(f.read().strip())
        except (IOError, ValueError):
            pass
    return BRIGHTNESS_MAX


def load_settings():
    """Load settings from disk. Returns dict with 'accent_index' and 'brightness'.

    Missing or corrupt file → returns defaults.
    """
    settings = {
        'accent_index': DEFAULT_ACCENT_INDEX,
    }

    try:
        with open(SETTINGS_FILE, 'r') as f:
            for line in f:
                line = line.strip()
                if '=' in line:
                    key, val = line.split('=', 1)
                    key = key.strip()
                    val = val.strip()
                    if key == 'accent_index':
                        idx = int(val)
                        if 0 <= idx < len(ACCENT_PRESETS):
                            settings['accent_index'] = idx
    except (IOError, ValueError):
        pass

    return settings


def save_settings(accent_index):
    """Write settings to disk."""
    try:
        with open(SETTINGS_FILE, 'w') as f:
            f.write(f"accent_index={accent_index}\n")
    except IOError as err:
        print(f"[settings] Save failed: {err}")


def get_brightness():
    """Read current screen brightness (0–max_brightness). Returns -1 on failure."""
    path = _find_backlight()
    if not path:
        return -1
    try:
        with open(path, 'r') as f:
            return int(f.read().strip())
    except (IOError, ValueError):
        return -1


def set_brightness(value):
    """Write screen brightness value. Clamps to [BRIGHTNESS_MIN, max_brightness]."""
    path = _find_backlight()
    if not path:
        return False
    max_br = _find_max_brightness()
    value = max(BRIGHTNESS_MIN, min(max_br, value))
    try:
        with open(path, 'w') as f:
            f.write(str(value))
        return True
    except IOError:
        return False


def brightness_up():
    """Increase brightness by one step. Returns new value or -1."""
    cur = get_brightness()
    if cur < 0:
        return -1
    new = cur + BRIGHTNESS_STEP
    set_brightness(new)
    return get_brightness()


def brightness_down():
    """Decrease brightness by one step. Returns new value or -1."""
    cur = get_brightness()
    if cur < 0:
        return -1
    new = cur - BRIGHTNESS_STEP
    set_brightness(new)
    return get_brightness()
