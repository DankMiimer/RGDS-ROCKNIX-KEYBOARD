# CLAUDE.md — RGDS Virtual Keyboard

> Context file for LLM-assisted development. Read this before making changes.

## Project Overview

A touchscreen virtual keyboard for the **Anbernic RG DS** handheld running **ROCKNIX** (Linux).
Renders on the bottom screen (DSI-1), injects keystrokes via uinput to whatever app runs on the top screen.
Toggle visibility with **R3** (right stick click).

## Target Environment

| Property          | Value                                              |
|-------------------|----------------------------------------------------|
| Device            | Anbernic RG DS (dual 640×480 screens, RK3568 SoC)  |
| OS                | ROCKNIX nightly (Buildroot Linux, Sway/Wayland)     |
| Python            | 3.x (system Python, no pip — zero external deps)    |
| Display server    | Sway (Wayland compositor)                           |
| Bottom screen     | DSI-1, 640×480, Goodix capacitive touch             |
| Touch device      | `/dev/input/event2` (multitouch, ABS_MT_*)          |
| Joypad device     | `/dev/input/event6` (R3 = BTN_THUMBR = 318)         |
| Virtual KB output | `/dev/uinput` (EV_KEY injection)                    |
| SDL library       | `libSDL2-2.0.so.0` loaded via ctypes (Wayland backend) |
| Install location  | `/storage/rgds_keyboard.py` on device               |
| Log file          | `/tmp/rgds_keyboard.log`                            |

## Architecture

```
Touch (Goodix /dev/input/event2)
  → TouchInput reads raw multitouch events
  → KeyboardEngine maps touch coords to key grid
  → UinputDevice writes EV_KEY to /dev/uinput
  → Linux kernel delivers to Sway compositor
  → Sway delivers to focused app on top screen

Joypad (/dev/input/event6)
  → JoypadMonitor watches for BTN_THUMBR (R3)
  → Toggles keyboard visibility on/off

SDL2 (via ctypes, Wayland backend)
  → Renders keyboard UI on DSI-1 bottom screen
  → Window title contains "[Bottom]" → ROCKNIX sway rule routes to DSI-1
  → Periodically re-asserts `swaymsg output DSI-1 power on` (counters ES power-off)
```

## Module Structure

```
rgds-keyboard/
├── CLAUDE.md              ← You are here
├── README.md              ← User-facing docs
├── LICENSE                ← MIT
├── install.sh             ← One-command device installer
├── rgds-keyboard.sh       ← CLI launcher (start/stop/restart)
├── Keyboard.sh            ← EmulationStation Ports toggle entry
├── rgds_keyboard.py       ← Main entry point (imports and runs)
└── rgds_kb/               ← Package: all keyboard logic
    ├── __init__.py
    ├── constants.py       ← All magic numbers, keycodes, colors, layout dims
    ├── font.py            ← 5×7 bitmap font data and text rendering helpers
    ├── sdl.py             ← SDL2 ctypes wrapper class
    ├── uinput_device.py   ← Virtual keyboard (uinput EV_KEY emitter)
    ├── touch_input.py     ← Touchscreen reader (evdev multitouch)
    ├── joypad.py          ← R3 button monitor thread
    ├── layouts.py         ← Keyboard layout definitions (main/shift/symbols/nav)
    ├── renderer.py        ← Key drawing, text rendering, screen painting
    └── engine.py          ← Main loop: event dispatch, state machine, key repeat
```

## Key Design Decisions

1. **Zero external dependencies.** ROCKNIX ships a minimal Python with no pip.
   Everything uses ctypes (SDL2, uinput) and stdlib only.

2. **SDL2 via ctypes, not pygame.** Pygame isn't available. We load `libSDL2-2.0.so.0`
   directly and call C functions through ctypes wrappers.

3. **Raw evdev for touch.** We read `/dev/input/event2` directly with `os.read()`
   and parse `input_event` structs. No python-evdev package.

4. **Touch grab/ungrab.** When keyboard is visible, we `EVIOCGRAB` the touch device
   so touches don't leak to other apps. Released when hidden.

5. **Window title routing.** ROCKNIX's sway config routes windows with `[Bottom]`
   in the title to DSI-1. Our window title is `"RGDS Keyboard [Bottom]"`.

6. **Periodic re-assertion.** EmulationStation turns off DSI-1 when launching apps.
   We call `swaymsg output DSI-1 power on` every 1.5s and re-fullscreen.

7. **Bitmap font.** 5×7 pixel glyphs stored as 7 bytes each (5-bit rows).
   Rendered by plotting filled rectangles at a configurable scale.

## Layout System

Four layers: `main`, `shift`, `symbols`, `nav`.

Each layout is a dict with `name` and `rows`. Each row has:
- `y`: vertical pixel offset
- `h`: row height in pixels
- `keys`: list of key dicts

Each key dict:
- `l`: label/ID (unique within layout, used for press tracking)
- `d`: display string (what's drawn on the key)
- `c`: Linux keycode (e.g. `KEY_A = 30`) or `None` for action-only keys
- `s`: bool — whether Shift modifier is held when emitting this key
- `w`: float — relative width weight (keys are proportionally sized)
- `a`: (optional) action string: `'shift'`, `'unshift'`, `'symbols'`, `'main'`, `'nav'`

Layout switching: pressing a key with `a='shift'` switches to the `shift` layout, etc.
Shift auto-returns: after typing one uppercase letter, reverts to `main`.

## Key Repeat

Keys in `REPEATABLE` set (`bksp`, `space`, `up`, `down`, `left`, `right`, `del`, etc.)
support held-key repeat: after `REPEAT_DELAY` (0.4s), emits at `REPEAT_RATE` (0.05s).

## State Machine

```
vis=False  → R3 press → vis=True  (grab touch, draw keyboard)
vis=True   → R3 press → vis=False (ungrab touch, blank screen, reset to main layer)

layer ∈ {main, shift, symbols, nav}
shift_sticky (ss): True when shift was activated, cleared on layer change
shift_active (sa): visual indicator for shift highlight
```

## Common Modification Patterns

### Adding a new key to an existing layout
1. In `layouts.py`, find the target layout and row
2. Add a key dict: `{'l':'unique_id', 'd':'DISPLAY', 'c':KEY_CODE, 's':False, 'w':1.0}`
3. Adjust `w` weights of neighboring keys if needed to fit

### Adding a new layout layer
1. In `layouts.py`, add a new layout dict following the existing pattern
2. Add action keys in other layouts with `'a':'your_layer_name'` to switch to it
3. No engine changes needed — the engine switches layers by action string

### Changing colors
Edit `constants.py` — all color tuples are `(R, G, B, A)` with descriptive names.

### Changing key repeat timing
Edit `REPEAT_DELAY` and `REPEAT_RATE` in `constants.py`.

### Adding a new font glyph
Add the character to the `FONT` dict in `font.py`. Each glyph is 7 ints,
each int is a 5-bit row (bit 4 = leftmost pixel, bit 0 = rightmost).

## Testing

No automated tests (runs on bare-metal embedded device). To verify:
1. `scp` files to device
2. `python3 /storage/rgds_keyboard.py`
3. Press R3 → keyboard should appear on bottom screen
4. Tap keys → check input arrives in focused app (e.g. `foot` terminal)
5. Check `/tmp/rgds_keyboard.log` for errors

## Deployment

```bash
# From host machine:
scp -r rgds_kb/ rgds_keyboard.py root@<DEVICE_IP>:/storage/
ssh root@<DEVICE_IP> "python3 /storage/rgds_keyboard.py"

# Or use the installer:
scp -r . root@<DEVICE_IP>:/tmp/rgds-keyboard
ssh root@<DEVICE_IP> "bash /tmp/rgds-keyboard/install.sh"
```

## Known Limitations

- Event device paths are hardcoded (`/dev/input/event2`, `event6`)
- No auto-detection of touch/joypad devices
- Font is bitmap only (no TTF/FreeType)
- No word prediction or swipe typing
- Single language (English QWERTY)
- No haptic feedback
- No theming system (colors are constants)
