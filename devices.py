"""
Device auto-detection for touchscreens and gamepads.
Parses /proc/bus/input/devices — no python-evdev dependency required.
Falls back to hardcoded paths if detection fails.
"""

import os, re, struct, fcntl

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Capability bit indices (from linux/input-event-codes.h)
EV_SYN = 0x00
EV_KEY = 0x01
EV_ABS = 0x03
EV_FF  = 0x15

# ABS codes
ABS_MT_POSITION_X = 0x35
ABS_MT_POSITION_Y = 0x36

# KEY codes
BTN_SOUTH  = 0x130  # 304 — standard gamepad A
BTN_THUMBR = 0x13E  # 318 — right stick click

# ioctl for reading abs info
_IOC_READ = 2
_EVIOCGABS_BASE = (_IOC_READ << 30) | (ord('E') << 8) | 0x40

def _eviocgabs(axis):
    """ioctl number for EVIOCGABS(axis)."""
    # struct input_absinfo is 6 × int32 = 24 bytes
    return _EVIOCGABS_BASE | (24 << 16) | axis

# Fallbacks if auto-detect fails
FALLBACK_TOUCH  = "/dev/input/event2"
FALLBACK_JOYPAD = "/dev/input/event6"

# ---------------------------------------------------------------------------
# /proc/bus/input/devices parser
# ---------------------------------------------------------------------------

def _parse_proc_devices():
    """
    Parse /proc/bus/input/devices into a list of device dicts.
    Each dict has keys: name, phys, handlers, ev_bits, abs_bits, key_bits, ff_bits.
    """
    devices = []
    try:
        with open("/proc/bus/input/devices", "r") as f:
            text = f.read()
    except OSError:
        return devices

    for block in text.strip().split("\n\n"):
        dev = {"name": "", "phys": "", "handlers": [], "ev_bits": 0,
               "abs_bits": 0, "key_bits": set(), "ff_bits": 0, "event_path": ""}
        for line in block.split("\n"):
            line = line.strip()
            if line.startswith("N: Name="):
                dev["name"] = line.split('"')[1] if '"' in line else ""
            elif line.startswith("P: Phys="):
                dev["phys"] = line.split("=", 1)[1].strip()
            elif line.startswith("H: Handlers="):
                parts = line.split("=", 1)[1].strip().split()
                dev["handlers"] = parts
                for p in parts:
                    if p.startswith("event"):
                        dev["event_path"] = f"/dev/input/{p}"
            elif line.startswith("B: EV="):
                dev["ev_bits"] = int(line.split("=", 1)[1].strip(), 16)
            elif line.startswith("B: ABS="):
                # ABS bitmap can be multiple hex words (MSB first)
                words = line.split("=", 1)[1].strip().split()
                val = 0
                for w in words:
                    val = (val << (len(w) * 4)) | int(w, 16)
                dev["abs_bits"] = val
            elif line.startswith("B: KEY="):
                words = line.split("=", 1)[1].strip().split()
                # Reconstruct full bitmap
                val = 0
                for w in words:
                    val = (val << (len(w) * 4)) | int(w, 16)
                # Extract set bits
                bits = set()
                n = val
                idx = 0
                while n:
                    if n & 1:
                        bits.add(idx)
                    n >>= 1
                    idx += 1
                dev["key_bits"] = bits
            elif line.startswith("B: FF="):
                dev["ff_bits"] = int(line.split("=", 1)[1].strip(), 16)
        if dev["event_path"]:
            devices.append(dev)
    return devices


def _bit_set(bitmap, bit):
    """Check if a bit is set in an integer bitmap."""
    return bool(bitmap & (1 << bit))


def _get_abs_max(event_path, axis):
    """Read the max value for an ABS axis via ioctl."""
    try:
        fd = os.open(event_path, os.O_RDONLY)
        try:
            buf = bytearray(24)
            fcntl.ioctl(fd, _eviocgabs(axis), buf)
            # struct input_absinfo: value, min, max, fuzz, flat, resolution
            _, _, maximum, _, _, _ = struct.unpack("iiiiii", buf)
            return maximum
        finally:
            os.close(fd)
    except (OSError, struct.error):
        return -1


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def find_touchscreen(prefer_bottom=True):
    """
    Find the bottom-screen touchscreen event path.

    On the RG DS there are two Goodix touchscreens.  The bottom screen is
    identified by having ABS_MT_POSITION_X with max ~640 (matching DSI-1
    resolution), or by its phys/name string.

    Returns event path string or FALLBACK_TOUCH.
    """
    devices = _parse_proc_devices()
    candidates = []

    for dev in devices:
        # Must have EV_ABS capability
        if not (dev["ev_bits"] & (1 << EV_ABS)):
            continue
        # Must have multitouch X axis
        if not _bit_set(dev["abs_bits"], ABS_MT_POSITION_X):
            continue
        # This is a touchscreen
        candidates.append(dev)

    if not candidates:
        print(f"[devices] No touchscreen found, falling back to {FALLBACK_TOUCH}")
        return FALLBACK_TOUCH

    if len(candidates) == 1:
        path = candidates[0]["event_path"]
        print(f"[devices] Touchscreen: {path} ({candidates[0]['name']})")
        return path

    # Multiple touchscreens (RG DS dual-screen) — pick the bottom one.
    # Strategy: the bottom screen (DSI-1) on RG DS is typically the second
    # Goodix device, or the one with higher event number.  We also check
    # abs max to differentiate if resolutions differ.
    if prefer_bottom:
        # Sort by event number descending — bottom screen tends to be higher
        candidates.sort(key=lambda d: d["event_path"], reverse=True)
        # If names contain useful info, prefer the one with "bottom" or higher index
        for c in candidates:
            name_lower = c["name"].lower()
            if "bottom" in name_lower or "dsi-1" in name_lower or "dsi1" in name_lower:
                print(f"[devices] Bottom touchscreen (by name): {c['event_path']} ({c['name']})")
                return c["event_path"]

        # Fallback: use the higher event number (typically bottom on RG DS)
        path = candidates[0]["event_path"]
        print(f"[devices] Bottom touchscreen (by index): {path} ({candidates[0]['name']})")
        return path

    path = candidates[0]["event_path"]
    print(f"[devices] Touchscreen: {path} ({candidates[0]['name']})")
    return path


def find_joypad():
    """
    Find the gamepad/joypad event path with BTN_THUMBR support.
    Returns event path string or FALLBACK_JOYPAD.
    """
    devices = _parse_proc_devices()

    for dev in devices:
        # Must have EV_KEY capability
        if not (dev["ev_bits"] & (1 << EV_KEY)):
            continue
        # Must have BTN_THUMBR (R3 stick click)
        if BTN_THUMBR in dev["key_bits"]:
            print(f"[devices] Joypad (BTN_THUMBR): {dev['event_path']} ({dev['name']})")
            return dev["event_path"]

    # Fallback: look for any gamepad (BTN_SOUTH)
    for dev in devices:
        if not (dev["ev_bits"] & (1 << EV_KEY)):
            continue
        if BTN_SOUTH in dev["key_bits"]:
            print(f"[devices] Joypad (BTN_SOUTH fallback): {dev['event_path']} ({dev['name']})")
            return dev["event_path"]

    print(f"[devices] No joypad found, falling back to {FALLBACK_JOYPAD}")
    return FALLBACK_JOYPAD


def find_haptic():
    """
    Find a device with force-feedback support (vibration motor).
    Returns event path string or None.
    """
    devices = _parse_proc_devices()

    for dev in devices:
        if dev["ff_bits"]:
            print(f"[devices] Haptic (FF): {dev['event_path']} ({dev['name']})")
            return dev["event_path"]

    # Fallback: check sysfs for vibrator LED
    vibrator_path = "/sys/class/leds/vibrator/brightness"
    if os.path.exists(vibrator_path):
        print(f"[devices] Haptic (sysfs): {vibrator_path}")
        return vibrator_path

    print("[devices] No haptic device found")
    return None
