# CLAUDE.md — RGDS Virtual Keyboard

Session context for future Claude instances. Read this before modifying any source.

## Project Overview

Custom virtual touchscreen keyboard for the Anbernic RG DS handheld running ROCKNIX Linux. Renders a phone-style keyboard on the bottom screen (DSI-1), injects keystrokes via uinput to apps on the top screen (DSI-2).

## Architecture (v5)

Multi-module package in `/storage/rgds-keyboard/`:

| Module | Responsibility |
|--------|---------------|
| `main.py` | Entry point, epoll event loop (selectors), touch/joypad handling, signal dispatch |
| `config.py` | 8 theme palettes, JSON settings persistence at `/storage/.config/rgds-keyboard/config.json` |
| `devices.py` | Auto-detect touchscreen/joypad/haptic via `/proc/bus/input/devices` parsing |
| `font.py` | Embedded 5×7 bitmap font glyph data |
| `layouts.py` | Keyboard layout definitions (main/shift/symbols/nav), keycode constants, rect computation |
| `renderer.py` | Dirty-region rendering with SDL2 render-target texture caching |
| `sdl2.py` | SDL2 ctypes bindings including texture/render-target support |
| `uinput_kb.py` | Virtual keyboard creation and keystroke injection via `/dev/uinput` |

## Critical Design Rules

These were learned through debugging on real hardware. Violating them **will** cause breakage.

1. **Window title must contain `[Bottom]`** — ROCKNIX's Sway config has a built-in rule that routes windows with `[Bottom]` in the title to DSI-1.

2. **DSI-1 must be periodically reasserted** — EmulationStation has a rule that powers off DSI-1 on focus. Counter with `swaymsg 'output DSI-1 power on'` every 1.5 seconds.

3. **Rendering must stay on main thread** — SDL2 rendering from background threads causes silent failures on this platform.

4. **Never use SDL2 hide/show for toggling** — Hiding/showing the SDL2 window causes it to leave Sway's window tree and lose DSI-1 assignment. Use render-black instead.

5. **uinput abs arrays are 64 entries × 4 bytes** — Not 256. The struct layout is: name[80] + id(8+4 bytes) + absmax[64×4] + absmin[64×4] + absfuzz[64×4] + absflat[64×4].

6. **Touchscreen grab must be cleaned up on crash** — Use `atexit` handler to release EVIOCGRAB on all grabbed file descriptors.

7. **Ports shortcuts go in `/storage/roms/ports/`** — NOT `/storage/.config/modules/`. The latter gets wiped by ROCKNIX's `001-sync-modules` autostart script on every boot.

8. **Brightness control must use swaymsg** — `/sys/class/backlight/*` targets the top screen. Use `swaymsg 'output DSI-1 brightness <float>'` for the bottom screen.

## Event Loop

The main loop uses `selectors.DefaultSelector` (epoll on Linux) to multiplex:
- Touch fd (bottom touchscreen evdev)
- Joypad fd (R3 button on gamepad)
- Signal pipe fd (for SIGUSR1/2/SIGRTMIN wakeup)

Timeouts:
- **Hidden**: blocks until joypad/signal event (with 1.5s timeout for DSI-1 reassertion)
- **Visible, idle**: 33ms timeout (30fps cap)
- **Visible, key held**: 16ms timeout (60fps for smooth repeat)

## Signal Protocol (wvkbd-compatible)

- `SIGUSR1` → hide keyboard
- `SIGUSR2` → show keyboard
- `SIGRTMIN` → toggle keyboard
- `SIGTERM` / `SIGINT` → clean shutdown

## Device Auto-Detection

Parses `/proc/bus/input/devices` to find devices by capability bits:
- **Touchscreen**: EV_ABS + ABS_MT_POSITION_X capability
- **Joypad**: EV_KEY + BTN_THUMBR capability
- **Haptic**: EV_FF capability or `/sys/class/leds/vibrator/brightness`

Dual touchscreens (RG DS) are differentiated by event number (bottom = higher index).

Config allows override: set `touch_device` / `joypad_device` in config.json.

## Rendering Pipeline

1. All keys rendered to an `SDL_Texture` with `SDL_TEXTUREACCESS_TARGET`
2. Dirty tracking: each key's visual state (pressed + shift_active) is cached
3. On change: only dirty keys are re-rendered to the texture
4. Full texture blitted to screen via single `SDL_RenderCopy`
5. Layer changes trigger full redraw

## Themes

8 palettes defined in `config.py` with semantic colour roles:
`bg`, `key`, `key_hi`, `key_press`, `key_sp`, `key_act`, `text`, `text_sp`, `text_num`, `accent`, `border`, `divider`

Default: Tokyo Night. All meet WCAG 2.1 AA contrast requirements.

## Hardware

- **Device**: Anbernic RG DS (RK3568, Mali G52-2EE, dual 640×480 IPS, Goodix touch)
- **OS**: ROCKNIX nightly (March 2026+), Sway compositor
- **Touch**: Two Goodix capacitive touchscreens (event1=top, event2=bottom typically)
- **Joypad**: retrogame device (event6 typically, R3 = BTN_THUMBR code 318)
- **Stack**: Python 3, SDL2 via ctypes, uinput — zero external dependencies
