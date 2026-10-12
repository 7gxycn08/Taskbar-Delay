import ctypes
import threading
import time
import pynput
import configparser
import win32gui
from ctypes import wintypes
from tkinter import messagebox
from typing import Optional
from threading import Timer

# --- Constants ---
EVENT_SYSTEM_FOREGROUND = 0x0003
# noinspection SpellCheckingInspection
WINEVENT_OUTOFCONTEXT = 0x0000
# noinspection SpellCheckingInspection
GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x00080000
LWA_ALPHA = 0x2
# noinspection SpellCheckingInspection
DWMWA_WINDOW_CORNER_PREFERENCE = 33

# --- Configuration ---
config = configparser.ConfigParser()
config.read('Config.ini')
fade = config.getboolean('MainConfig', 'fade_in_out')
rounded = config.getboolean('MainConfig', 'rounded_corners')
location = config['MainConfig']['location']
hide_delay = float(config['MainConfig']['delay'])  # Seconds to wait before hiding
hide_timer: Optional[Timer] = None # Holds the timer object

state_lock = threading.RLock()
taskbar_visible = True
last_hide_time = 0
is_fading = False
suppress_events = False

class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long),
                ("y", ctypes.c_long)]

# --- WinEvent Setup ---
WinEventProcType = ctypes.WINFUNCTYPE(
    ctypes.c_long, wintypes.HWND, ctypes.c_long, wintypes.HWND,
    ctypes.c_long, ctypes.c_long, ctypes.c_uint, ctypes.c_void_p
)

def win_event_callback():
    global last_hide_time
    # If we are currently fading or showing/hiding, ignore Windows events
    if suppress_events:
        return 0

    with state_lock:
        if is_taskbar_physically_visible():
            current_time = time.time()
            if current_time - last_hide_time > 0.5:
                last_hide_time = current_time
                if not queue:
                    threading.Thread(target=hide_taskbar, daemon=True).start()
    return 0


win_event_callback_ptr = WinEventProcType(win_event_callback)

def start_event_hook():
    user32.SetWinEventHook(
        EVENT_SYSTEM_FOREGROUND, EVENT_SYSTEM_FOREGROUND,
        WINEVENT_OUTOFCONTEXT, win_event_callback_ptr, 0, 0, 0
    )
    msg = wintypes.MSG()
    while user32.GetMessageW(ctypes.byref(msg), 0, 0, 0) != 0:
        user32.TranslateMessage(ctypes.byref(msg))
        user32.DispatchMessageW(ctypes.byref(msg))


# --- Taskbar Control ---
def is_taskbar_physically_visible():
    hwnd = user32.FindWindowW("Shell_TrayWnd", None)
    return user32.IsWindowVisible(hwnd) if hwnd else False


def show_taskbar():
    global hide_timer # Add this
    with state_lock:
        # CANCEL the hide timer immediately if we are showing the taskbar
        if hide_timer is not None:
            hide_timer.cancel()
            hide_timer = None

        if not is_taskbar_physically_visible():
            # noinspection SpellCheckingInspection
            hwnds = []
            win32gui.EnumWindows(enum_handler, hwnds)
            for hwnd, cls in hwnds:
                if rounded:
                    round_taskbar(hwnd, 2)
                else:
                    round_taskbar(hwnd, 0)
                if fade:
                    fade_in(hwnd)
                else:
                    user32.ShowWindow(user32.FindWindowW(cls, None), 5)
                    user32.SetForegroundWindow(hwnd)
            return True
    return False



def hide_taskbar():
    global hide_timer, last_hide_time

    # IMPORTANT: If a timer is already counting down, do nothing.
    # This prevents the start() loop from resetting the timer every 0.1s.
    if hide_timer is not None:
        return

    def delayed_hide():
        global last_hide_time, hide_timer
        try:
            with state_lock:
                if is_taskbar_physically_visible():
                    last_hide_time = time.time()
                    # noinspection SpellCheckingInspection
                    hwnds = []
                    win32gui.EnumWindows(enum_handler, hwnds)
                    for hwnd, cls in hwnds:
                        if fade:
                            fade_out(hwnd)
                        else:
                            user32.ShowWindow(user32.FindWindowW(cls, None), 0)
        except Exception as error:
            messagebox.showerror(f"Taskbar-Delay Hide Error:", f"{error}")
        finally:
            # Reset timer variable so it can be started again later
            hide_timer = None

    # Start the timer
    hide_timer = threading.Timer(hide_delay, delayed_hide)
    hide_timer.start()

# --- Helpers ---
# noinspection SpellCheckingInspection
def enum_handler(hwnd, hwnds):
    class_name = win32gui.GetClassName(hwnd)
    if class_name in ("Shell_TrayWnd", "Shell_SecondaryTrayWnd"):
        hwnds.append((hwnd, class_name))
    return True


def round_taskbar(hwnd, dwm_wcp_round):
    preference = ctypes.c_int(dwm_wcp_round)
    dwm_api.DwmSetWindowAttribute(hwnd, DWMWA_WINDOW_CORNER_PREFERENCE, ctypes.byref(preference),
                                 ctypes.sizeof(preference))


def fade_out(hwnd):
    global is_fading, suppress_events
    if is_fading: return

    try:
        is_fading = True
        suppress_events = True  # <--- Block the hook

        ex_style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        user32.SetWindowLongW(hwnd, GWL_EXSTYLE, ex_style | WS_EX_LAYERED)

        for i in range(60, -1, -1):
            user32.SetLayeredWindowAttributes(hwnd, 0, int(255 * i / 60), LWA_ALPHA)
            time.sleep(0.5 / 60)

        # Finally, actually hide the window so it doesn't capture clicks
        user32.ShowWindow(hwnd, 0)

    except Exception as error:
        messagebox.showerror(f"Taskbar-delay Fade Out Error:",f"{error}")
    finally:
        is_fading = False
        suppress_events = False  # <--- Re-enable the hook


def fade_in(hwnd):
    global is_fading, suppress_events
    if is_fading: return

    try:
        is_fading = True
        suppress_events = True  # <--- Block the hook

        # Ensure window is visible before fading in
        user32.ShowWindow(hwnd, 5)

        ex_style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        user32.SetWindowLongW(hwnd, GWL_EXSTYLE, ex_style | WS_EX_LAYERED)

        for i in range(0, 61):
            user32.SetLayeredWindowAttributes(hwnd, 0, int(255 * i / 60), LWA_ALPHA)
            time.sleep(0.1 / 60)
    except Exception as error:
        messagebox.showerror(f"Taskbar-delay Fade In Error:",f"{error}")
    finally:
        is_fading = False
        suppress_events = False  # <--- Re-enable the hook


def on_win_press(key):
    if key == pynput.keyboard.Key.cmd:
        show_taskbar()


def mouse_on_taskbar():
    global queue
    sw, sh = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
    while True:
        user32.GetCursorPos(ctypes.byref(point))
        x, y = point.x, point.y
        with state_lock:
            if (location == "top" and y <= 105) or \
                    (location == "bottom" and y >= sh - 105) or \
                    (location == "left" and x <= 105) or \
                    (location == "right" and x >= sw - 105):
                queue = True
            else:
                queue = False
        time.sleep(0.1)


def start_keyboard_listener():
    with pynput.keyboard.Listener(on_press=on_win_press) as listener:
        listener.join()


def start():
    global queue
    while True:
        with state_lock:
            m_active = queue
            v_active = is_taskbar_physically_visible()

        if m_active and not v_active:
            show_taskbar()
        elif not m_active and v_active:
            # This now only triggers the timer ONCE
            hide_taskbar()

        time.sleep(0.1)


# --- Initialization ---
try:
    point = POINT()
    user32 = ctypes.WinDLL('user32.dll')
    user32.SetProcessDPIAware()
    # noinspection SpellCheckingInspection
    dwm_api = ctypes.WinDLL("dwmapi.dll")
    queue = False

    threading.Thread(target=start_event_hook, daemon=True).start()
    threading.Thread(target=start_keyboard_listener, daemon=True).start()
    threading.Thread(target=mouse_on_taskbar, daemon=True).start()

    hide_taskbar()
    start()
except Exception as e:
    messagebox.showerror("Taskbar-Delay Error", f"{e}")

if __name__ == "__main__":
    hide_taskbar()
    start()
