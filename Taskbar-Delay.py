import ctypes
import threading
import time
import queue
import pynput
import configparser

win_pressed = False
taskbar_hidden = None
config = configparser.ConfigParser()
config.read('Config.ini')
delay = config['MainConfig']['delay']

def on_win_press(key):
    global win_pressed
    if key == pynput.keyboard.Key.cmd:
        show_taskbar()
        win_pressed = True

def show_taskbar():
    global taskbar_hidden
    ctypes.windll.user32.ShowWindow(ctypes.windll.user32.FindWindowW("Shell_TrayWnd", None), 1)
    taskbar_hidden = False

def hide_taskbar():
    global taskbar_hidden
    if not taskbar_hidden:
        ctypes.windll.user32.ShowWindow(ctypes.windll.user32.FindWindowW("Shell_TrayWnd", None), 0)
        taskbar_hidden = True

def mouse_on_taskbar(q):
    class POINT(ctypes.Structure):
        _fields_ = [("x", ctypes.c_long),
                    ("y", ctypes.c_long)]
    point = POINT()
    ctypes.windll.user32.GetCursorPos(ctypes.byref(point))
    x, y = point.x, point.y

    ctypes.windll.user32.GetSystemMetrics(0)
    screen_height = ctypes.windll.user32.GetSystemMetrics(1)

    if y == screen_height - 1:
        q.put(True)
    elif screen_height - 40 < y < screen_height:
        q.put(True)
    else:
        q.put(False)

def start_keyboard_listener():
    with pynput.keyboard.Listener(on_press=on_win_press) as listener:
        listener.join()

def start():
    global win_pressed, taskbar_visible, mouse_in_bottom_region
    while True:
        mouse_on_taskbar(queue)
        mouse_on_q = queue.get()
        if win_pressed:
            win_pressed = False
            show_taskbar()
            time.sleep(0.5)
            continue
        elif mouse_on_q and taskbar_visible == True:
            time.sleep(int(delay))
            continue
        elif mouse_on_q and not taskbar_visible:
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

threading.Thread(target=start_keyboard_listener, daemon=True).start()
mouse_in_bottom_region = False
taskbar_visible = False
queue = queue.Queue()

if __name__ == "__main__":
    start()
