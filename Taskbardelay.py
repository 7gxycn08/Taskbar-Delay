import ctypes
import threading
import time
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
    global taskbar_hidden, user32
    user32.ShowWindow(user32.FindWindowW("Shell_TrayWnd", None), 1)
    taskbar_hidden = False

def hide_taskbar():
    global taskbar_hidden, user32
    if not taskbar_hidden:
        user32.ShowWindow(user32.FindWindowW("Shell_TrayWnd", None), 0)
        taskbar_hidden = True

def mouse_on_taskbar():
    global user32, point, queue
    while True:
        user32.GetCursorPos(ctypes.byref(point))
        x, y = point.x, point.y

        user32.GetSystemMetrics(0)
        screen_height = user32.GetSystemMetrics(1)

        if y == screen_height - 1:
            queue = True
        elif screen_height - 40 < y < screen_height:
            queue = True
        else:
            queue = False
        time.sleep(0.1)

def start_keyboard_listener():
    with pynput.keyboard.Listener(on_press=on_win_press) as listener:
        listener.join()

def start():
    global win_pressed, taskbar_visible, mouse_in_bottom_region
    while True:
        mouse_on_q = queue
        if win_pressed:
            win_pressed = False
            show_taskbar()
            time.sleep(int(delay))
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
            time.sleep(int(delay))
            hide_taskbar()
            mouse_in_bottom_region = False
            taskbar_visible = False
            continue
        else:
            hide_taskbar()
        time.sleep(0.1)


class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long),
                ("y", ctypes.c_long)]


point = POINT()
user32 = ctypes.WinDLL('user32.dll')
threading.Thread(target=start_keyboard_listener, daemon=True).start()
mouse_in_bottom_region = False
taskbar_visible = False
queue = None
threading.Thread(target=lambda: mouse_on_taskbar(), daemon=True).start()

if __name__ == "__main__":
    start()
