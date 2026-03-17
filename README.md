# RGDS Virtual Keyboard

A touchscreen virtual keyboard for the **Anbernic RG DS** running **ROCKNIX**.

Renders a phone-style keyboard on the bottom screen (DSI-1) and injects keystrokes to whatever app is running on the top screen. Toggle it on/off anytime with **R3** (right stick click).

![Layout: Phone-style QWERTY with shift, backspace, symbols, and navigation layers](https://img.shields.io/badge/layout-QWERTY-blue) ![Pure Python, no dependencies](https://img.shields.io/badge/deps-none-green) ![License: MIT](https://img.shields.io/badge/license-MIT-yellow)

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

## Manual Install

```bash
# Copy to device via SCP
scp -r rgds_kb/ root@<DEVICE_IP>:/storage/
scp rgds_keyboard.py root@<DEVICE_IP>:/storage/
scp rgds-keyboard.sh root@<DEVICE_IP>:/storage/
scp Keyboard.sh root@<DEVICE_IP>:/storage/roms/ports/

# SSH in and set permissions
ssh root@<DEVICE_IP>
chmod +x /storage/rgds_keyboard.py /storage/rgds-keyboard.sh /storage/roms/ports/Keyboard.sh
```

## Usage

### From EmulationStation

1. Navigate to **Ports**
2. Select **Keyboard** to start the daemon — the bottom screen powers on
3. Press **R3** anytime to show/hide the keyboard
4. Select **Keyboard** again in Ports to stop (bottom screen powers off)

### From SSH

```bash
bash /storage/rgds-keyboard.sh start
bash /storage/rgds-keyboard.sh stop
bash /storage/rgds-keyboard.sh restart
```

## Layout

Phone-style QWERTY with four layers:

### Main (ABC)
```
 Q  W  E  R  T  Y  U  I  O  P
   A  S  D  F  G  H  J  K  L
 SHIFT Z  X  C  V  B  N  M  ⌫
  #+  ,      SPACE       .  RET
  1  2  3  4  5  6  7  8  9  0
 TAB ESC NAV  -  ?  !  @
```

### Shift
Same letters (uppercase), auto-returns after one letter.
Number row becomes `! @ # $ % ^ & * ( )`.

### Symbols (#+)
Three rows of brackets, punctuation, and operators.

### Nav
Arrow keys, Home, End, Delete, Insert — for text editing.

## Features

- **R3 Toggle** — show/hide keyboard without leaving your app
- **Key Repeat** — hold backspace, space, or arrows for rapid repeat
- **Shift Auto-Return** — types one capital letter then goes back to lowercase
- **App Survive** — keyboard stays running when switching apps; periodically re-powers DSI-1 to counter ES's power-off rule
- **Touch Isolation** — bottom touchscreen is captured when keyboard is visible, released when hidden
- **Crash Safety** — `atexit` handler releases all grabbed input devices

## Project Structure

```
rgds-keyboard/
├── CLAUDE.md              # LLM context (architecture, patterns, conventions)
├── README.md              # This file
├── LICENSE                # MIT
├── install.sh             # One-command device installer
├── rgds-keyboard.sh       # CLI launcher (start/stop/restart)
├── Keyboard.sh            # EmulationStation Ports entry
├── rgds_keyboard.py       # Entry point (imports and runs rgds_kb.engine)
└── rgds_kb/               # Core package
    ├── __init__.py        # Package metadata
    ├── constants.py       # Device paths, keycodes, colors, timing
    ├── font.py            # 5×7 bitmap font data and text helpers
    ├── sdl.py             # SDL2 ctypes wrapper
    ├── uinput_device.py   # Virtual keyboard (uinput EV_KEY emitter)
    ├── touch_input.py     # Touchscreen reader (raw evdev multitouch)
    ├── joypad.py          # R3 button monitor thread
    ├── layouts.py         # Keyboard layout definitions (4 layers)
    ├── renderer.py        # Key drawing and screen painting
    └── engine.py          # Main loop, state machine, key repeat
```

## Compatibility

Tested and working with:

| App | Type | Status |
|-----|------|--------|
| NetSurf | Wayland browser | ✅ |
| foot | Wayland terminal | ✅ |
| ScummVM | SDL game engine | ✅ |
| Counter-Strike 1.6 | PortMaster port | ✅ |

Should work with any app that receives keyboard input via Sway/Wayland or evdev.

## How It Works

```
Touch (Goodix /dev/input/event2)
  → Python reads multitouch events
  → Maps touch coordinates to key grid
  → Writes EV_KEY events to /dev/uinput
  → Kernel delivers to Sway compositor
  → Sway delivers to focused app on top screen
```

- **Rendering**: SDL2 via Python ctypes (Wayland backend), 5×7 bitmap font, zero external dependencies
- **Window routing**: Title contains `[Bottom]` which triggers ROCKNIX's built-in sway rule to auto-route to DSI-1
- **Screen power**: Periodically calls `swaymsg output DSI-1 power on` to counter EmulationStation's power-off rule

## Uninstall

```bash
rm -rf /storage/rgds_kb/
rm /storage/rgds_keyboard.py
rm /storage/rgds-keyboard.sh
rm /storage/roms/ports/Keyboard.sh
```

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Keyboard doesn't appear | Check `/tmp/rgds_keyboard.log` |
| Bottom screen stays off | `swaymsg 'output DSI-1 power on'` via SSH |
| Controls frozen after crash | Reboot the device |
| No input in apps | Verify with `evtest /dev/input/event7` while tapping keys |
| Shortcut missing after reboot | Make sure `Keyboard.sh` is in `/storage/roms/ports/` |

## Contributing

See `CLAUDE.md` for architecture details and modification patterns.

Areas for improvement:

- **Better font rendering** — TTF/FreeType instead of bitmap font
- **Swipe typing** — gesture-based input
- **Themes** — user-selectable color schemes
- **Word prediction** — autocomplete bar
- **Multi-language layouts** — AZERTY, QWERTZ, Cyrillic, etc.
- **Haptic feedback** — vibration motor on keypress
- **Auto-detect input devices** — scan `/dev/input/` instead of hardcoded paths

PRs welcome!

## License

MIT — free to use, modify, and distribute.

## Acknowledgments

Built for the [ROCKNIX](https://github.com/ROCKNIX/distribution) community and the Anbernic RG DS.
