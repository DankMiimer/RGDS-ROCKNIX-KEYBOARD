"""
Configuration — themes, settings, JSON persistence.
Stores to /storage/.config/rgds-keyboard/config.json (zero external deps).
"""

import json, os

CONFIG_DIR = "/storage/.config/rgds-keyboard"
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")

# ---------------------------------------------------------------------------
# Theme palettes — each has semantic colour roles (RGB tuples)
# ---------------------------------------------------------------------------

def _hex(h):
    """Convert '#RRGGBB' to (R,G,B,255)."""
    h = h.lstrip('#')
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255)

THEMES = {
    "midnight": {
        "label": "Midnight OLED",
        "bg":       _hex("#000000"), "key":       _hex("#1A1A1A"),
        "key_hi":   _hex("#252525"), "key_press": _hex("#333333"),
        "key_sp":   _hex("#111111"), "key_act":   _hex("#0A3D7A"),
        "text":     _hex("#FFFFFF"), "text_sp":   _hex("#0A84FF"),
        "text_num": _hex("#AAAAAA"), "accent":    _hex("#0A84FF"),
        "border":   _hex("#2C2C2C"), "divider":   _hex("#1A1A1A"),
    },
    "dracula": {
        "label": "Dracula",
        "bg":       _hex("#282A36"), "key":       _hex("#44475A"),
        "key_hi":   _hex("#4E5172"), "key_press": _hex("#6272A4"),
        "key_sp":   _hex("#363949"), "key_act":   _hex("#6A3FA0"),
        "text":     _hex("#F8F8F2"), "text_sp":   _hex("#BD93F9"),
        "text_num": _hex("#BBBFC9"), "accent":    _hex("#BD93F9"),
        "border":   _hex("#6272A4"), "divider":   _hex("#363949"),
    },
    "nord": {
        "label": "Nord",
        "bg":       _hex("#2E3440"), "key":       _hex("#3B4252"),
        "key_hi":   _hex("#434E61"), "key_press": _hex("#434C5E"),
        "key_sp":   _hex("#333B49"), "key_act":   _hex("#3B6383"),
        "text":     _hex("#ECEFF4"), "text_sp":   _hex("#88C0D0"),
        "text_num": _hex("#B0B8C4"), "accent":    _hex("#88C0D0"),
        "border":   _hex("#4C566A"), "divider":   _hex("#3B4252"),
    },
    "catppuccin": {
        "label": "Catppuccin Mocha",
        "bg":       _hex("#1E1E2E"), "key":       _hex("#313244"),
        "key_hi":   _hex("#3B3D52"), "key_press": _hex("#45475A"),
        "key_sp":   _hex("#282839"), "key_act":   _hex("#5C3D8F"),
        "text":     _hex("#CDD6F4"), "text_sp":   _hex("#CBA6F7"),
        "text_num": _hex("#9DA4C0"), "accent":    _hex("#CBA6F7"),
        "border":   _hex("#585B70"), "divider":   _hex("#2A2A3C"),
    },
    "gruvbox": {
        "label": "Gruvbox Dark",
        "bg":       _hex("#282828"), "key":       _hex("#3C3836"),
        "key_hi":   _hex("#484442"), "key_press": _hex("#504945"),
        "key_sp":   _hex("#32302F"), "key_act":   _hex("#8F5A00"),
        "text":     _hex("#EBDBB2"), "text_sp":   _hex("#FE8019"),
        "text_num": _hex("#B8A98A"), "accent":    _hex("#FE8019"),
        "border":   _hex("#665C54"), "divider":   _hex("#3C3836"),
    },
    "solarized": {
        "label": "Solarized Dark",
        "bg":       _hex("#002B36"), "key":       _hex("#073642"),
        "key_hi":   _hex("#0D4050"), "key_press": _hex("#586E75"),
        "key_sp":   _hex("#04303C"), "key_act":   _hex("#155880"),
        "text":     _hex("#839496"), "text_sp":   _hex("#268BD2"),
        "text_num": _hex("#6A7A7C"), "accent":    _hex("#268BD2"),
        "border":   _hex("#586E75"), "divider":   _hex("#073642"),
    },
    "tokyonight": {
        "label": "Tokyo Night",
        "bg":       _hex("#1A1B26"), "key":       _hex("#24283B"),
        "key_hi":   _hex("#2D3250"), "key_press": _hex("#414868"),
        "key_sp":   _hex("#1F2133"), "key_act":   _hex("#3D4F91"),
        "text":     _hex("#A9B1D6"), "text_sp":   _hex("#7AA2F7"),
        "text_num": _hex("#858DAD"), "accent":    _hex("#7AA2F7"),
        "border":   _hex("#3B4261"), "divider":   _hex("#24283B"),
    },
    "onedark": {
        "label": "One Dark",
        "bg":       _hex("#282C34"), "key":       _hex("#32363E"),
        "key_hi":   _hex("#3C414C"), "key_press": _hex("#636D83"),
        "key_sp":   _hex("#2C3039"), "key_act":   _hex("#2D5A8F"),
        "text":     _hex("#ABB2BF"), "text_sp":   _hex("#61AFEF"),
        "text_num": _hex("#8A909B"), "accent":    _hex("#61AFEF"),
        "border":   _hex("#5C6370"), "divider":   _hex("#32363E"),
    },
}

THEME_ORDER = [
    "tokyonight", "catppuccin", "dracula", "nord",
    "gruvbox", "onedark", "solarized", "midnight",
]

# ---------------------------------------------------------------------------
# Default settings
# ---------------------------------------------------------------------------

DEFAULTS = {
    "theme":            "tokyonight",
    "brightness":       1.0,         # DSI-1 brightness 0.0–1.0
    "haptic_enabled":   True,
    "sound_enabled":    False,
    "repeat_delay":     0.4,         # seconds before key repeat starts
    "repeat_rate":      0.05,        # seconds between repeats
    "touch_device":     "",          # empty = auto-detect
    "joypad_device":    "",          # empty = auto-detect
}

# ---------------------------------------------------------------------------
# Settings I/O
# ---------------------------------------------------------------------------

class Settings:
    """Persistent settings backed by a JSON file."""

    __slots__ = ('_data', '_path')

    def __init__(self, path=CONFIG_PATH):
        self._path = path
        self._data = dict(DEFAULTS)
        self._load()

    def _load(self):
        try:
            with open(self._path, 'r') as f:
                saved = json.load(f)
            for k, v in saved.items():
                if k in DEFAULTS:
                    self._data[k] = type(DEFAULTS[k])(v)
        except (OSError, json.JSONDecodeError, ValueError):
            pass  # first run or corrupt — use defaults

    def save(self):
        try:
            os.makedirs(os.path.dirname(self._path), exist_ok=True)
            with open(self._path, 'w') as f:
                json.dump(self._data, f, indent=2)
        except OSError as e:
            print(f"[config] Save failed: {e}")

    def __getattr__(self, name):
        if name.startswith('_'):
            return object.__getattribute__(self, name)
        try:
            return self._data[name]
        except KeyError:
            raise AttributeError(name)

    def __setattr__(self, name, value):
        if name.startswith('_'):
            object.__setattr__(self, name, value)
        else:
            self._data[name] = value

    @property
    def theme_colors(self):
        """Return the active theme's colour dict."""
        return THEMES.get(self._data['theme'], THEMES['tokyonight'])
