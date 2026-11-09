"""Capture screenshots of each GUI tab for the README/user guide.
Uses PrintWindow so overlapping windows (LM Studio, browsers) never contaminate shots."""
import ctypes
import sys
from pathlib import Path

from PIL import Image, ImageGrab

if __name__ != "__main__":
    raise SystemExit("This is a script - run it directly: python capture_screens.py")

import gui

OUT = Path(__file__).parent / "screenshots"
OUT.mkdir(exist_ok=True)

PW_RENDERFULLCONTENT = 3


def grab_window(hwnd):
    """Capture a window's own content via PrintWindow (works even when obscured)."""
    import ctypes.wintypes as wt

    user32, gdi32 = ctypes.windll.user32, ctypes.windll.gdi32
    rect = wt.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    w, h = rect.right - rect.left, rect.bottom - rect.top

    hwnd_dc = user32.GetWindowDC(hwnd)
    mfc_dc = gdi32.CreateCompatibleDC(hwnd_dc)
    bmp = gdi32.CreateCompatibleBitmap(hwnd_dc, w, h)
    gdi32.SelectObject(mfc_dc, bmp)
    # PrintWindow with PW_RENDERFULLCONTENT captures via DWM even if covered
    result = user32.PrintWindow(hwnd, mfc_dc, PW_RENDERFULLCONTENT)
    if not result:
        # fallback: regular PrintWindow
        result = user32.PrintWindow(hwnd, mfc_dc, 2)
    if not result:
        gdi32.DeleteObject(bmp)
        gdi32.DeleteDC(mfc_dc)
        user32.ReleaseDC(hwnd, hwnd_dc)
        return None

    class BITMAPINFOHEADER(ctypes.Structure):
        _fields_ = [
            ("biSize", ctypes.c_uint32), ("biWidth", ctypes.c_int32),
            ("biHeight", ctypes.c_int32), ("biPlanes", ctypes.c_uint16),
            ("biBitCount", ctypes.c_uint16), ("biCompression", ctypes.c_uint32),
            ("biSizeImage", ctypes.c_uint32), ("biXPelsPerMeter", ctypes.c_int32),
            ("biYPelsPerMeter", ctypes.c_int32), ("biClrUsed", ctypes.c_uint32),
            ("biClrImportant", ctypes.c_uint32),
        ]

    bmi = BITMAPINFOHEADER()
    bmi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bmi.biWidth = w
    bmi.biHeight = -h  # top-down
    bmi.biPlanes = 1
    bmi.biBitCount = 32
    bmi.biCompression = 0
    buf = ctypes.create_string_buffer(w * h * 4)
    gdi32.GetDIBits(mfc_dc, bmp, 0, h, buf, ctypes.byref(bmi), 0)

    img = Image.frombuffer("RGBA", (w, h), buf, "raw", "BGRA", 0, 1).convert("RGB")
    gdi32.DeleteObject(bmp)
    gdi32.DeleteDC(mfc_dc)
    user32.ReleaseDC(hwnd, hwnd_dc)
    return img


root = gui.tk.Tk()
app = gui.App(root)
root.geometry("1040x760")
root.attributes("-topmost", True)  # keep other windows (LM Studio etc.) from covering us
root.update()
root.lift()
root.focus_force()
try:
    ctypes.windll.user32.SetForegroundWindow(root.winfo_id())
except Exception:
    pass

SHOTS = [
    (1, "01_home.png"),
    (2, "02_hardware.png"),
    (3, "03_recommend.png"),
    (4, "04_setup.png"),
    (5, "05_models.png"),
    (7, "06_online.png"),
]


def capture(idx, name, done):
    app.nb.select(idx)
    root.update()
    root.update_idletasks()

    def snap():
        hwnd = ctypes.windll.user32.GetParent(root.winfo_id()) or root.winfo_id()
        try:
            ctypes.windll.user32.SetForegroundWindow(hwnd)
        except Exception:
            pass
        root.lift()
        root.update()
        img = None
        for attempt in range(3):  # PrintWindow can fail while the frame is composing
            img = grab_window(hwnd)
            if img is not None:
                break
            root.update()
            __import__("time").sleep(0.3)
        if img is None:
            # last resort: ensure we are on top before a screen grab
            root.attributes("-topmost", True)
            root.lift()
            root.focus_force()
            root.update()
            __import__("time").sleep(0.5)
            img = ImageGrab.grab(bbox=(root.winfo_rootx(), root.winfo_rooty(),
                                       root.winfo_rootx() + root.winfo_width(),
                                       root.winfo_rooty() + root.winfo_height()))
            print(f"  ! {name}: PrintWindow failed, used screen grab")
        img.save(OUT / name)
        print(f"saved {name} ({img.width}x{img.height})")
        done()

    root.after(1200, snap)  # give DWM time to compose the topmost frame


def step(i):
    if i >= len(SHOTS):
        print("ALL DONE")
        root.destroy()
        return
    idx, name = SHOTS[i]
    capture(idx, name, lambda: step(i + 1))


root.after(800, lambda: step(0))
root.mainloop()
sys.exit(0)
