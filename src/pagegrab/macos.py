"""Thin macOS helpers: display geometry, mouse position, screenshots, key presses.

Only uses ctypes + the built-in `screencapture` and `osascript` tools, so no pyobjc is needed.
"""
import ctypes
import ctypes.util
import subprocess
import sys
from collections import namedtuple

Display = namedtuple("Display", "index id x y w h is_main")

# macOS virtual key codes for the keys people usually use to turn pages.
KEY_CODES = {
    "right": 124,
    "left": 123,
    "down": 125,
    "up": 126,
    "space": 49,
    "pagedown": 121,
    "pageup": 116,
    "return": 36,
}


class _Point(ctypes.Structure):
    _fields_ = [("x", ctypes.c_double), ("y", ctypes.c_double)]


class _Size(ctypes.Structure):
    _fields_ = [("w", ctypes.c_double), ("h", ctypes.c_double)]


class _Rect(ctypes.Structure):
    _fields_ = [("origin", _Point), ("size", _Size)]


def _cg():
    if sys.platform != "darwin":
        raise SystemExit("pagegrab currently supports macOS only.")
    cg = ctypes.CDLL(ctypes.util.find_library("CoreGraphics"))
    cg.CGDisplayBounds.restype = _Rect
    cg.CGDisplayBounds.argtypes = [ctypes.c_uint32]
    cg.CGDisplayIsMain.restype = ctypes.c_bool
    cg.CGDisplayIsMain.argtypes = [ctypes.c_uint32]
    cg.CGEventCreate.restype = ctypes.c_void_p
    cg.CGEventCreate.argtypes = [ctypes.c_void_p]
    cg.CGEventGetLocation.restype = _Point
    cg.CGEventGetLocation.argtypes = [ctypes.c_void_p]
    return cg


def displays():
    """Active displays, main first, then left-to-right. `index` is 1-based and matches `screencapture -D`."""
    cg = _cg()
    ids = (ctypes.c_uint32 * 16)()
    count = ctypes.c_uint32()
    cg.CGGetActiveDisplayList(16, ids, ctypes.byref(count))
    found = []
    for did in list(ids)[: count.value]:
        b = cg.CGDisplayBounds(did)
        found.append((did, int(b.origin.x), int(b.origin.y), int(b.size.w), int(b.size.h), bool(cg.CGDisplayIsMain(did))))
    found.sort(key=lambda d: (not d[5], d[1]))
    return [Display(i + 1, *d) for i, d in enumerate(found)]


def get_display(index):
    for d in displays():
        if d.index == index:
            return d
    raise SystemExit(f"No display #{index}. Run `pagegrab displays` to list them.")


def mouse_pos():
    """Cursor position in global screen points."""
    cg = _cg()
    p = cg.CGEventGetLocation(cg.CGEventCreate(None))
    return int(p.x), int(p.y)


def display_at(x, y):
    for d in displays():
        if d.x <= x < d.x + d.w and d.y <= y < d.y + d.h:
            return d
    return displays()[0]


def screenshot(region, path):
    """Save a screenshot of a region given in GLOBAL screen points (x, y, w, h)."""
    x, y, w, h = region
    subprocess.run(["screencapture", "-x", "-R", f"{x},{y},{w},{h}", str(path)], check=True)


def press_key(key="right", app=None):
    """Press a key, optionally bringing `app` to the front first."""
    if key not in KEY_CODES:
        raise SystemExit(f"Unsupported --key {key!r}. Choose from: {', '.join(KEY_CODES)}")
    script = f'tell application "System Events" to key code {KEY_CODES[key]}'
    if app:
        script = f'tell application "{app}" to activate\ndelay 0.2\n' + script
    subprocess.run(["osascript", "-e", script], check=True)
