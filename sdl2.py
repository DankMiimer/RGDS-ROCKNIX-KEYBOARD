"""
Minimal SDL2 bindings via ctypes.
Adds render-target textures and batching for dirty-region rendering.
"""

import ctypes

# ---------------------------------------------------------------------------
# SDL2 library
# ---------------------------------------------------------------------------

_lib = ctypes.CDLL('libSDL2-2.0.so.0')

# ---------------------------------------------------------------------------
# Structures
# ---------------------------------------------------------------------------

class Rect(ctypes.Structure):
    _fields_ = [("x", ctypes.c_int), ("y", ctypes.c_int),
                 ("w", ctypes.c_int), ("h", ctypes.c_int)]

class Event(ctypes.Union):
    _fields_ = [("type", ctypes.c_uint32), ("pad", ctypes.c_uint8 * 56)]

# ---------------------------------------------------------------------------
# Function signatures
# ---------------------------------------------------------------------------

_lib.SDL_Init.restype = ctypes.c_int
_lib.SDL_CreateWindow.restype = ctypes.c_void_p
_lib.SDL_CreateRenderer.restype = ctypes.c_void_p
_lib.SDL_PollEvent.restype = ctypes.c_int
_lib.SDL_GetError.restype = ctypes.c_char_p
_lib.SDL_SetHint.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
_lib.SDL_SetHint.restype = ctypes.c_int
_lib.SDL_GetCurrentVideoDriver.restype = ctypes.c_char_p

# Texture functions
_lib.SDL_CreateTexture.restype = ctypes.c_void_p
_lib.SDL_CreateTexture.argtypes = [
    ctypes.c_void_p, ctypes.c_uint32, ctypes.c_int, ctypes.c_int, ctypes.c_int
]
_lib.SDL_SetRenderTarget.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
_lib.SDL_SetRenderTarget.restype = ctypes.c_int
_lib.SDL_RenderCopy.argtypes = [
    ctypes.c_void_p, ctypes.c_void_p,
    ctypes.POINTER(Rect), ctypes.POINTER(Rect)
]
_lib.SDL_RenderCopy.restype = ctypes.c_int
_lib.SDL_DestroyTexture.argtypes = [ctypes.c_void_p]
_lib.SDL_SetRenderDrawBlendMode.argtypes = [ctypes.c_void_p, ctypes.c_int]
_lib.SDL_SetTextureBlendMode.argtypes = [ctypes.c_void_p, ctypes.c_int]

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SDL_INIT_VIDEO   = 0x00000020
SDL_INIT_EVENTS  = 0x00004000
SDL_INIT_FLAGS   = SDL_INIT_VIDEO | SDL_INIT_EVENTS

SDL_WINDOWPOS_UNDEFINED = 0x1FFF0000
SDL_WINDOW_SHOWN        = 0x00000004

SDL_RENDERER_ACCELERATED = 0x00000002
SDL_RENDERER_PRESENTVSYNC = 0x00000004
SDL_RENDERER_FLAGS       = SDL_RENDERER_ACCELERATED | SDL_RENDERER_PRESENTVSYNC

# Pixel formats
SDL_PIXELFORMAT_RGBA8888 = 0x16462004

# Texture access
SDL_TEXTUREACCESS_TARGET = 2

# Blend modes
SDL_BLENDMODE_NONE  = 0
SDL_BLENDMODE_BLEND = 1

# ---------------------------------------------------------------------------
# Pre-allocated rect for reuse
# ---------------------------------------------------------------------------

_rect = Rect()
_evt = Event()

# ---------------------------------------------------------------------------
# High-level wrapper
# ---------------------------------------------------------------------------

class SDL:
    """Thin wrapper around SDL2 for the keyboard renderer."""

    __slots__ = ()

    @staticmethod
    def init():
        return _lib.SDL_Init(SDL_INIT_FLAGS)

    @staticmethod
    def set_hint(name, value):
        _lib.SDL_SetHint(name.encode(), value.encode())

    @staticmethod
    def create_window(title, x, y, w, h, flags=SDL_WINDOW_SHOWN):
        return _lib.SDL_CreateWindow(title.encode(), x, y, w, h, flags)

    @staticmethod
    def create_renderer(window, index=-1, flags=SDL_RENDERER_FLAGS):
        return _lib.SDL_CreateRenderer(window, index, flags)

    @staticmethod
    def set_draw_color(ren, r, g, b, a=255):
        _lib.SDL_SetRenderDrawColor(ren, r, g, b, a)

    @staticmethod
    def clear(ren):
        _lib.SDL_RenderClear(ren)

    @staticmethod
    def fill_rect(ren, x, y, w, h):
        _rect.x = int(x); _rect.y = int(y)
        _rect.w = int(w); _rect.h = int(h)
        _lib.SDL_RenderFillRect(ren, ctypes.byref(_rect))

    @staticmethod
    def draw_rect(ren, x, y, w, h):
        _rect.x = int(x); _rect.y = int(y)
        _rect.w = int(w); _rect.h = int(h)
        _lib.SDL_RenderDrawRect(ren, ctypes.byref(_rect))

    @staticmethod
    def present(ren):
        _lib.SDL_RenderPresent(ren)

    @staticmethod
    def poll_event():
        if _lib.SDL_PollEvent(ctypes.byref(_evt)):
            return _evt
        return None

    @staticmethod
    def delay(ms):
        _lib.SDL_Delay(ms)

    @staticmethod
    def destroy_renderer(ren):
        _lib.SDL_DestroyRenderer(ren)

    @staticmethod
    def destroy_window(win):
        _lib.SDL_DestroyWindow(win)

    @staticmethod
    def quit():
        _lib.SDL_Quit()

    @staticmethod
    def get_error():
        return _lib.SDL_GetError().decode()

    # --- Texture / render-target support ---

    @staticmethod
    def create_target_texture(ren, w, h):
        """Create an RGBA texture usable as a render target."""
        tex = _lib.SDL_CreateTexture(
            ren, SDL_PIXELFORMAT_RGBA8888, SDL_TEXTUREACCESS_TARGET, w, h
        )
        if tex:
            _lib.SDL_SetTextureBlendMode(tex, SDL_BLENDMODE_BLEND)
        return tex

    @staticmethod
    def set_render_target(ren, tex):
        """Redirect rendering to a texture (None = back to screen)."""
        return _lib.SDL_SetRenderTarget(ren, tex)

    @staticmethod
    def render_copy(ren, tex, src_rect=None, dst_rect=None):
        """Blit a texture to the current render target."""
        src = ctypes.byref(src_rect) if src_rect else None
        dst = ctypes.byref(dst_rect) if dst_rect else None
        return _lib.SDL_RenderCopy(ren, tex, src, dst)

    @staticmethod
    def destroy_texture(tex):
        if tex:
            _lib.SDL_DestroyTexture(tex)

    @staticmethod
    def set_blend_mode(ren, mode):
        _lib.SDL_SetRenderDrawBlendMode(ren, mode)
