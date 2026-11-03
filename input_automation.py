import time
import win32api
import win32con
import win32gui
from typing import Optional, List, Tuple

# Карта популярных клавиш для win32api
KEY_MAP = {
    "enter": win32con.VK_RETURN,
    "return": win32con.VK_RETURN,
    "space": win32con.VK_SPACE,
    "tab": win32con.VK_TAB,
    "esc": win32con.VK_ESCAPE,
    "escape": win32con.VK_ESCAPE,
    "backspace": win32con.VK_BACK,
    "up": win32con.VK_UP,
    "down": win32con.VK_DOWN,
    "left": win32con.VK_LEFT,
    "right": win32con.VK_RIGHT,
    "ctrl": win32con.VK_CONTROL,
    "alt": win32con.VK_MENU,
    "shift": win32con.VK_SHIFT,
    "win": win32con.VK_LWIN,
    "f1": win32con.VK_F1,
    "f2": win32con.VK_F2,
    "f3": win32con.VK_F3,
    "f4": win32con.VK_F4,
    "f5": win32con.VK_F5,
    "f11": win32con.VK_F11,
    "f12": win32con.VK_F12,
}

def find_window_by_title(keyword: str) -> Optional[int]:
    """Ищет дескриптор окна по части названия (например 'Happ')"""
    keyword_lower = keyword.lower().strip()
    found_hwnd = None

    def enum_windows_callback(hwnd, extra):
        nonlocal found_hwnd
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title and keyword_lower in title.lower():
                found_hwnd = hwnd
                return False
        return True

    try:
        win32gui.EnumWindows(enum_windows_callback, None)
    except Exception:
        pass

    return found_hwnd

def focus_window(keyword: str) -> bool:
    """Выводит окно на передний план по имени"""
    hwnd = find_window_by_title(keyword)
    if not hwnd:
        return False
    try:
        # Восстанавливаем, если свернуто
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        time.sleep(0.1)
        win32gui.SetForegroundWindow(hwnd)
        time.sleep(0.1)
        return True
    except Exception as e:
        print(f"Ошибка фокуса окна: {e}")
        return False

def press_key(key_str: str, duration: float = 0.05):
    """
    Нажимает клавишу или комбинацию (например: 'enter', 'space', 'ctrl+c', 'alt+f4')
    """
    keys = [k.strip().lower() for k in key_str.split("+") if k.strip()]
    if not keys:
        return

    vk_codes = []
    for k in keys:
        if k in KEY_MAP:
            vk_codes.append(KEY_MAP[k])
        elif len(k) == 1:
            # Для букв и цифр VkKeyScan
            vk = win32api.VkKeyScan(k) & 0xFF
            vk_codes.append(vk)

    # Нажимаем все клавиши комбинации
    for vk in vk_codes:
        win32api.keybd_event(vk, 0, 0, 0)

    time.sleep(duration)

    # Отпускаем в обратном порядке
    for vk in reversed(vk_codes):
        win32api.keybd_event(vk, 0, win32con.KEYEVENTF_KEYUP, 0)

def mouse_click(x: Optional[int] = None, y: Optional[int] = None, button: str = "left", double: bool = False):
    """Кликает мышкой по координатам X, Y или на текущем месте курсора"""
    if x is not None and y is not None:
        win32api.SetCursorPos((int(x), int(y)))
        time.sleep(0.05)

    btn = button.lower().strip()
    down_event = win32con.MOUSEEVENTF_RIGHTDOWN if btn == "right" else win32con.MOUSEEVENTF_LEFTDOWN
    up_event = win32con.MOUSEEVENTF_RIGHTUP if btn == "right" else win32con.MOUSEEVENTF_LEFTUP

    clicks = 2 if double else 1
    for _ in range(clicks):
        win32api.mouse_event(down_event, 0, 0, 0, 0)
        time.sleep(0.04)
        win32api.mouse_event(up_event, 0, 0, 0, 0)
        if double:
            time.sleep(0.08)

def get_current_mouse_pos() -> Tuple[int, int]:
    """Возвращает текущие координаты курсора (x, y)"""
    return win32gui.GetCursorPos()

def type_text(text: str, delay: float = 0.02):
    """Печатает текст посимвольно"""
    for ch in text:
        vk = win32api.VkKeyScan(ch)
        if vk != -1:
            shift = (vk >> 8) & 1
            code = vk & 0xFF
            if shift:
                win32api.keybd_event(win32con.VK_SHIFT, 0, 0, 0)
            win32api.keybd_event(code, 0, 0, 0)
            win32api.keybd_event(code, 0, win32con.KEYEVENTF_KEYUP, 0)
            if shift:
                win32api.keybd_event(win32con.VK_SHIFT, 0, win32con.KEYEVENTF_KEYUP, 0)
        time.sleep(delay)
