import ctypes
import threading
import time
import pynput
import configparser
import win32gui

win_pressed = False
taskbar_hidden = None
config = configparser.ConfigParser()
config.read('Config.ini')
delay = config['MainConfig']['delay']
fade = config.getboolean('MainConfig', 'fade_rounded')
#noinspection SpellCheckingInspection
GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x00080000
LWA_ALPHA = 0x2
# noinspection SpellCheckingInspection
DWMWA_WINDOW_CORNER_PREFERENCE = 33


def reset_fade(hwnd, cls):
    user32.ShowWindow(user32.FindWindowW(cls, None), 5)
    # get current extended style
    ex_style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)

    # enable layered window style
    user32.SetWindowLongW(
        hwnd,
        GWL_EXSTYLE,
        ex_style | WS_EX_LAYERED
    )
    user32.SetLayeredWindowAttributes(
        hwnd,
        0,
        255,
        LWA_ALPHA
    )


def fade_out(hwnd):
    # get current extended style
    ex_style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)

    # enable layered window style
    user32.SetWindowLongW(
        hwnd,
        GWL_EXSTYLE,
        ex_style | WS_EX_LAYERED
    )

    steps = 60  # “frames”
    duration = 1.5  # seconds
    sleep = duration / steps

    for i in range(steps, -1, -1):
        alpha = int(255 * i / steps)
        user32.SetLayeredWindowAttributes(
            hwnd,
            0,
            alpha,
            LWA_ALPHA
        )
        time.sleep(sleep)


def fade_in(hwnd):
    # get current extended style
    ex_style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)

    # enable layered window style
    user32.SetWindowLongW(
        hwnd,
        GWL_EXSTYLE,
        ex_style | WS_EX_LAYERED
    )

    steps = 60  # “frames”
    duration = 1.5  # seconds
    sleep = duration / steps

    for i in range(0, steps + 1):
        alpha = int(255 * i / steps)
        user32.SetLayeredWindowAttributes(
            hwnd,
            0,
            alpha,
            LWA_ALPHA
        )
        time.sleep(sleep)


def round_taskbar(hwnd, dwm_wcp_round):
    # Find the taskbar window
    preference = ctypes.c_int(dwm_wcp_round)

    dwmapi.DwmSetWindowAttribute(
        hwnd,
        DWMWA_WINDOW_CORNER_PREFERENCE,
        ctypes.byref(preference),
        ctypes.sizeof(preference)
    )


#noinspection SpellCheckingInspection
def enum_handler(hwnd, hwnds):
    class_name = win32gui.GetClassName(hwnd)
    if class_name in ("Shell_TrayWnd", "Shell_SecondaryTrayWnd"):
        hwnds.append((hwnd, class_name))
    return True


def on_win_press(key):
    global win_pressed
    if key == pynput.keyboard.Key.cmd:
        show_taskbar()
        win_pressed = True


def show_taskbar():
    global taskbar_hidden, user32
    #noinspection SpellCheckingInspection
    hwnds = []
    win32gui.EnumWindows(enum_handler, hwnds)
    for hwnd, cls in hwnds:
        if fade:
            fade_in(hwnd)
            round_taskbar(hwnd, 2)
        else:
            round_taskbar(hwnd, 0)
            user32.ShowWindow(user32.FindWindowW(cls, None), 5)
    taskbar_hidden = False


def hide_taskbar():
    global taskbar_hidden, user32
    if not taskbar_hidden:
        # noinspection SpellCheckingInspection
        hwnds = []
        win32gui.EnumWindows(enum_handler, hwnds)
        for hwnd, cls in hwnds:
            if fade:
                fade_out(hwnd)
                round_taskbar(hwnd, 2)
            else:
                round_taskbar(hwnd, 0)
                user32.ShowWindow(user32.FindWindowW(cls, None), 0)
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
# noinspection SpellCheckingInspection
dwmapi = ctypes.WinDLL("dwmapi.dll")
threading.Thread(target=start_keyboard_listener, daemon=True).start()
mouse_in_bottom_region = False
taskbar_visible = False
queue = None
threading.Thread(target=lambda: mouse_on_taskbar(), daemon=True).start()
# noinspection SpellCheckingInspection
hwnd_s = []
win32gui.EnumWindows(enum_handler, hwnd_s)
for hwn_d, cl_s in hwnd_s:
    reset_fade(hwn_d, cl_s)

if __name__ == "__main__":
    start()
