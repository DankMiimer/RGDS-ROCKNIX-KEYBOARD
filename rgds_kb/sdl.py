"""
sdl.py — Minimal SDL2 wrapper via ctypes.

Loads libSDL2-2.0.so.0 and exposes only the functions we need for rendering
the keyboard UI. No pygame, no external deps.
"""

import ctypes


class SDLRect(ctypes.Structure):
    """SDL_Rect struct."""
    _fields_ = [
        ("x", ctypes.c_int),
        ("y", ctypes.c_int),
        ("w", ctypes.c_int),
        ("h", ctypes.c_int),
    ]


class SDLEvent(ctypes.Union):
    """Minimal SDL_Event union — we only need the type field."""
    _fields_ = [
        ("type", ctypes.c_uint32),
        ("pad", ctypes.c_uint8 * 56),
    ]


class SDL:
    """Thin wrapper around SDL2 C functions via ctypes.

    Usage:
        sdl = SDL()
        sdl.init()
        win = sdl.create_window("Title", ...)
        ren = sdl.create_renderer(win)
        ...
        sdl.quit()
    """

    # SDL_Init flags
    SDL_INIT_VIDEO = 0x00000020
    SDL_INIT_EVENTS = 0x00004000

    # SDL_CreateWindow position sentinel
    SDL_WINDOWPOS_UNDEFINED_DISPLAY_1 = 0x1FFF0001

    # SDL_WindowFlags
    SDL_WINDOW_SHOWN = 0x00000004

    # SDL_RendererFlags
    SDL_RENDERER_ACCELERATED = 0x00000002
    SDL_RENDERER_PRESENTVSYNC = 0x00000004

    def __init__(self):
        self._lib = ctypes.CDLL('libSDL2-2.0.so.0')

        # Set return types for functions that return pointers
        self._lib.SDL_Init.restype = ctypes.c_int
        self._lib.SDL_CreateWindow.restype = ctypes.c_void_p
        self._lib.SDL_CreateRenderer.restype = ctypes.c_void_p
        self._lib.SDL_PollEvent.restype = ctypes.c_int
        self._lib.SDL_GetError.restype = ctypes.c_char_p
        self._lib.SDL_SetHint.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
        self._lib.SDL_GetCurrentVideoDriver.restype = ctypes.c_char_p

    def init(self):
        """Initialize SDL video + events subsystems. Returns 0 on success."""
        return self._lib.SDL_Init(self.SDL_INIT_VIDEO | self.SDL_INIT_EVENTS)

    def get_error(self):
        """Return the last SDL error string."""
        return self._lib.SDL_GetError().decode()

    def create_window(self, title, x, y, width, height, flags=0):
        """Create an SDL window. Returns opaque window pointer."""
        return self._lib.SDL_CreateWindow(title.encode(), x, y, width, height, flags)

    def create_renderer(self, window, index=-1, flags=0x06):
        """Create an SDL renderer for a window. Default flags = ACCELERATED|PRESENTVSYNC."""
        return self._lib.SDL_CreateRenderer(window, index, flags)

    def set_draw_color(self, renderer, r, g, b, a=255):
        """Set the current drawing color."""
        self._lib.SDL_SetRenderDrawColor(renderer, r, g, b, a)

    def clear(self, renderer):
        """Clear the renderer with the current draw color."""
        self._lib.SDL_RenderClear(renderer)

    def fill_rect(self, renderer, x, y, w, h):
        """Draw a filled rectangle."""
        rect = SDLRect(int(x), int(y), int(w), int(h))
        self._lib.SDL_RenderFillRect(renderer, ctypes.byref(rect))

    def draw_rect(self, renderer, x, y, w, h):
        """Draw a rectangle outline."""
        rect = SDLRect(int(x), int(y), int(w), int(h))
        self._lib.SDL_RenderDrawRect(renderer, ctypes.byref(rect))

    def present(self, renderer):
        """Flip the rendered frame to screen."""
        self._lib.SDL_RenderPresent(renderer)

    def poll_event(self):
        """Poll for a pending event. Returns SDLEvent or None."""
        event = SDLEvent()
        if self._lib.SDL_PollEvent(ctypes.byref(event)):
            return event
        return None

    def destroy_renderer(self, renderer):
        """Destroy an SDL renderer."""
        self._lib.SDL_DestroyRenderer(renderer)

    def destroy_window(self, window):
        """Destroy an SDL window."""
        self._lib.SDL_DestroyWindow(window)

    def quit(self):
        """Shut down SDL."""
        self._lib.SDL_Quit()

    def delay(self, milliseconds):
        """Wait for the given number of milliseconds."""
        self._lib.SDL_Delay(milliseconds)
