import ctypes
import time
from threading import Thread
import queue

def show_taskbar():
    ctypes.windll.user32.ShowWindow(ctypes.windll.user32.FindWindowW("Shell_TrayWnd", None), 1)

def hide_taskbar():
    ctypes.windll.user32.ShowWindow(ctypes.windll.user32.FindWindowW("Shell_TrayWnd", None), 0)

def mouse_on_taskbar(q):
    class POINT(ctypes.Structure):
        _fields_ = [("x", ctypes.c_long),
                    ("y", ctypes.c_long)]
    point = POINT()
    ctypes.windll.user32.GetCursorPos(ctypes.byref(point))
    x, y = point.x, point.y

    screen_width = ctypes.windll.user32.GetSystemMetrics(0)
    screen_height = ctypes.windll.user32.GetSystemMetrics(1)

    if y == screen_height - 1:
        q.put(True)
    elif y > screen_height - 40 and y < screen_height:
        q.put(True)
    else:
        q.put(False)

mouse_in_bottom_region = False
q = queue.Queue()
while True:
    mouseontaskbar = Thread(target=lambda :mouse_on_taskbar(q), daemon=True)
    mouseontaskbar.start()
    mouseon = q.get()
    if mouseon:
        Thread(target=show_taskbar(),daemon=True).start()
        mouse_in_bottom_region = True
    elif mouse_in_bottom_region:
        time.sleep(5)
        Thread(target=lambda: hide_taskbar(),daemon=True).start()
        mouse_in_bottom_region = False
    else:
        hide_taskbar()
    time.sleep(0.1)
