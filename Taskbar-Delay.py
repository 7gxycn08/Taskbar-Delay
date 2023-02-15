import ctypes
import time
from threading import Thread
import queue
import pynput

win_pressed = False
def on_win_press(key):
    global win_pressed
    if key == pynput.keyboard.Key.cmd:
        show_taskbar()
        win_pressed = True

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

def start_keyboard_listener():
    with pynput.keyboard.Listener(on_press=on_win_press) as listener:
        listener.join()

Thread(target=start_keyboard_listener, daemon=True).start()
mouse_in_bottom_region = False
taskbar_visible = False
q = queue.Queue()
while True:
    mouse_on_taskbar(q)
    mouseon = q.get()
    if win_pressed:
        win_pressed = False
        show_taskbar()
        time.sleep(0.5)
        continue
    elif mouseon and taskbar_visible == True:
        time.sleep(0.5)
        continue
    elif mouseon and not taskbar_visible:
        show_taskbar()
        mouse_in_bottom_region = True
        taskbar_visible = True
        continue
    elif mouse_in_bottom_region:
        time.sleep(0.5)
        hide_taskbar()
        mouse_in_bottom_region = False
        taskbar_visible = False
        continue
    else:
        hide_taskbar()
    time.sleep(0.1)
