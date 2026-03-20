# RGDS Virtual Keyboard

A touchscreen virtual keyboard for the **Anbernic RG DS** running **ROCKNIX**.

Renders a phone-style keyboard on the bottom screen (DSI-1) and injects keystrokes to whatever app is running on the top screen. Toggle it on/off anytime with **R3** (right stick click).

![Layout: Phone-style QWERTY with shift, backspace, symbols, and navigation layers](https://img.shields.io/badge/layout-QWERTY-blue) ![Pure Python, no dependencies](https://img.shields.io/badge/deps-none-green) ![License: MIT](https://img.shields.io/badge/license-MIT-yellow)

## What's New in v5

- **Near-zero idle CPU** — epoll-based event loop sleeps when hidden, 30fps cap when visible
- **Dirty-region rendering** — only redraws keys that change state, via GPU render-target texture
- **8 dark themes** — Tokyo Night, Catppuccin, Dracula, Nord, Gruvbox, One Dark, Solarized, Midnight
- **Auto-detect devices** — finds touchscreen and joypad by capability, no more hardcoded paths
- **Persistent settings** — theme, brightness, and repeat rates saved as JSON
- **Signal control** — SIGUSR1/2/SIGRTMIN for hide/show/toggle (wvkbd-compatible)
- **Haptic feedback** — vibration on keypress (when hardware supports it)
- **GC-tuned daemon** — freezes garbage collector after init for consistent latency
- **SDL2 render batching** — minimises GPU draw calls

## Requirements

- **Anbernic RG DS** (dual-screen, RK3568)
- **ROCKNIX** nightly with RG DS support (tested on 20260314+)
- SSH access to the device

## Quick Install

```bash
# Transfer files to the device
scp -r . root@<DEVICE_IP>:/tmp/rgds-keyboard

# SSH in and run the installer
ssh root@<DEVICE_IP>
bash /tmp/rgds-keyboard/install.sh
```

Then in EmulationStation: go to **Ports → Keyboard** to start/stop.

## Usage

### From EmulationStation

1. Navigate to **Ports**
2. Select **Keyboard** to start the daemon
3. Press **R3** anytime to show/hide the keyboard
4. Select **Keyboard** again to stop

### From SSH

```bash
bash /storage/rgds-keyboard.sh start
bash /storage/rgds-keyboard.sh stop
bash /storage/rgds-keyboard.sh restart
bash /storage/rgds-keyboard.sh show
bash /storage/rgds-keyboard.sh hide
bash /storage/rgds-keyboard.sh toggle
```

### Signal Control

```bash
PID=$(cat /tmp/rgds_keyboard.pid)
kill -USR1 $PID   # hide
kill -USR2 $PID   # show
kill -RTMIN $PID   # toggle
```

## Themes

Eight WCAG-AA-compliant dark palettes, selectable via config file:

| Theme | Background | Accent |
|-------|-----------|--------|
| **Tokyo Night** (default) | `#1A1B26` | `#7AA2F7` |
| **Catppuccin Mocha** | `#1E1E2E` | `#CBA6F7` |
| **Dracula** | `#282A36` | `#BD93F9` |
| **Nord** | `#2E3440` | `#88C0D0` |
| **Gruvbox Dark** | `#282828` | `#FE8019` |
| **One Dark** | `#282C34` | `#61AFEF` |
| **Solarized Dark** | `#002B36` | `#268BD2` |
| **Midnight OLED** | `#000000` | `#0A84FF` |

Edit `/storage/.config/rgds-keyboard/config.json` to change themes:

```json
{
  "theme": "catppuccin"
}
```

## Layout

Phone-style QWERTY with four layers:

### Main (ABC)
```
 q  w  e  r  t  y  u  i  o  p
   a  s  d  f  g  h  j  k  l
 ⇧  z  x  c  v  b  n  m  ⌫
  #+  ,      SPACE       .  RET
  1  2  3  4  5  6  7  8  9  0
 TAB ESC NAV  -  ?  !  @
```

### Shift
Same letters (uppercase), auto-returns after one letter. Number row becomes `! @ # $ % ^ & * ( )`.

### Symbols (#+)
Three rows of brackets, punctuation, and operators.

### Nav
Arrow keys, Home, End, Delete, Insert — for text editing.

## Configuration

Settings persist in `/storage/.config/rgds-keyboard/config.json`:

| Key | Default | Description |
|-----|---------|-------------|
| `theme` | `"tokyonight"` | Colour theme name |
| `brightness` | `1.0` | DSI-1 brightness (0.0–1.0) |
| `haptic_enabled` | `true` | Vibration on keypress |
| `repeat_delay` | `0.4` | Seconds before key repeat starts |
| `repeat_rate` | `0.05` | Seconds between repeats |
| `touch_device` | `""` | Override touchscreen path (empty = auto) |
| `joypad_device` | `""` | Override joypad path (empty = auto) |

## Architecture

```
Touch (auto-detected Goodix touchscreen)
  → Python reads multitouch events via epoll/selectors
  → Maps touch coordinates to key grid
  → Dirty-region renderer updates only changed keys
  → Writes EV_KEY events to /dev/uinput
  → Kernel delivers to Sway compositor
  → Sway delivers to focused app on top screen
```

### Performance

| State | CPU Usage | Mechanism |
|-------|-----------|-----------|
| Hidden | ~0% | `selectors.select()` blocks indefinitely |
| Visible, idle | <1% | 30fps timeout, no render if clean |
| Active typing | ~3–5% | Dirty-region redraws only pressed key |

### Files

| File | Installs to | Purpose |
|------|------------|---------|
| `main.py` | `/storage/rgds-keyboard/` | Application entry point, event loop |
| `config.py` | `/storage/rgds-keyboard/` | Themes, settings, JSON persistence |
| `devices.py` | `/storage/rgds-keyboard/` | Auto-detect input devices |
| `font.py` | `/storage/rgds-keyboard/` | 5×7 bitmap font data |
| `layouts.py` | `/storage/rgds-keyboard/` | Keyboard layout definitions |
| `renderer.py` | `/storage/rgds-keyboard/` | Dirty-region rendering engine |
| `sdl2.py` | `/storage/rgds-keyboard/` | SDL2 ctypes bindings |
| `uinput_kb.py` | `/storage/rgds-keyboard/` | Virtual keyboard via uinput |
| `rgds-keyboard.sh` | `/storage/` | CLI launcher |
| `Keyboard.sh` | `/storage/roms/ports/` | EmulationStation entry |
| `install.sh` | — | One-command installer |

## Compatibility

Tested and working with:

| App | Type | Status |
|-----|------|--------|
| NetSurf | Wayland browser | ✅ |
| foot | Wayland terminal | ✅ |
| ScummVM | SDL game engine | ✅ |
| Counter-Strike 1.6 | PortMaster port | ✅ |

Should work with any app that receives keyboard input via Sway/Wayland or evdev.

## Uninstall

```bash
rm -rf /storage/rgds-keyboard
rm /storage/rgds-keyboard.sh
rm /storage/roms/ports/Keyboard.sh
rm -rf /storage/.config/rgds-keyboard
```

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Keyboard doesn't appear | Check `/tmp/rgds_keyboard.log` |
| Bottom screen stays off | `swaymsg 'output DSI-1 power on'` via SSH |
| Controls frozen after crash | Reboot the device |
| Wrong touchscreen detected | Set `touch_device` in config.json |
| No input in apps | Verify with `evtest` while tapping keys |
| Shortcut missing after reboot | Ensure `Keyboard.sh` is in `/storage/roms/ports/` |

## Contributing

Areas for improvement:

- **Swipe gestures** — swipe-left for backspace-word, swipe-down to hide
- **Long-press alternate characters** — accented letters (é, ñ, ü)
- **Multi-language layouts** — AZERTY, QWERTZ, Nordic, Cyrillic
- **FreeType font rendering** — TTF support via SDL_ttf
- **Mouse emulation** — touch-to-cursor mode
- **On-screen theme picker** — select themes without editing config

PRs welcome!

## License

MIT — free to use, modify, and distribute.

## Acknowledgments

Built for the [ROCKNIX](https://github.com/ROCKNIX/distribution) community and the Anbernic RG DS.
