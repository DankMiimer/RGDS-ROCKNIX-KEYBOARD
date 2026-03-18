"""
settings.py — Persistent settings: accent color and DSI-1 screen brightness.

Brightness is controlled via `swaymsg output DSI-1 brightness <0.0-1.0>`,
which targets the bottom screen specifically. The old sysfs approach
(/sys/class/backlight/*) was hitting the top screen.

Settings saved to /storage/.rgds_keyboard_settings as key=value lines.
"""

import json
import os
import subprocess

from .constants import (
    SETTINGS_FILE,
    BRIGHTNESS_STEP, BRIGHTNESS_MIN, BRIGHTNESS_MAX,
    ACCENT_PRESETS, DEFAULT_ACCENT_INDEX,
)


# =============================================================================
# Settings persistence
# =============================================================================

def load_settings():
    """Load settings from disk.

    Returns dict with 'accent_index' (int) and 'brightness' (float 0.0–1.0).
    """
    settings = {
        'accent_index': DEFAULT_ACCENT_INDEX,
        'brightness': 0.6,
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
                    elif key == 'brightness':
                        br = float(val)
                        if BRIGHTNESS_MIN <= br <= BRIGHTNESS_MAX:
                            settings['brightness'] = br
    except (IOError, ValueError):
        pass

    return settings


def save_settings(accent_index, brightness):
    """Write settings to disk."""
    try:
        with open(SETTINGS_FILE, 'w') as f:
            f.write(f"accent_index={accent_index}\n")
            f.write(f"brightness={brightness:.2f}\n")
    except IOError as err:
        print(f"[settings] Save failed: {err}")


# =============================================================================
# DSI-1 brightness via swaymsg
# =============================================================================

def _sway_cmd(cmd):
    """Run a swaymsg command, return stdout or None on failure."""
    try:
        result = subprocess.run(
            ['swaymsg', cmd], capture_output=True, timeout=2, text=True,
        )
        return result.stdout.strip() if result.returncode == 0 else None
    except Exception:
        return None


def apply_brightness(value):
    """Set DSI-1 bottom screen brightness via swaymsg.

    Args:
        value: float 0.0–1.0 (clamped to BRIGHTNESS_MIN..BRIGHTNESS_MAX)

    Returns:
        The clamped value that was applied.
    """
    value = max(BRIGHTNESS_MIN, min(BRIGHTNESS_MAX, value))
    _sway_cmd(f'output DSI-1 brightness {value:.2f}')
    return value


def get_brightness_from_sway():
    """Try to read DSI-1 brightness from sway. Returns float or None."""
    output = _sway_cmd('-t get_outputs -r')
    if not output:
        return None
    try:
        outputs = json.loads(output)
        for o in outputs:
            if o.get('name') == 'DSI-1':
                # Sway stores this as a float like 0.6 or 1.0
                # The field is called 'brightness' if available
                br = o.get('brightness')
                if br is not None:
                    return float(br)
    except (json.JSONDecodeError, TypeError, ValueError):
        pass
    return None


def brightness_up(current):
    """Increase brightness by one step. Returns new value."""
    new = min(BRIGHTNESS_MAX, current + BRIGHTNESS_STEP)
    return apply_brightness(new)


def brightness_down(current):
    """Decrease brightness by one step. Returns new value."""
    new = max(BRIGHTNESS_MIN, current - BRIGHTNESS_STEP)
    return apply_brightness(new)
