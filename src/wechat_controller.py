#!/usr/bin/env python3
"""
微信控制器
处理微信自动化发送消息功能。
仅支持 NT 架构（WeChat 4.0+）；低于 4.0 的版本直接跳过。
"""

import asyncio
import ctypes
import itertools
import logging
import time
import uuid
from collections import deque
from datetime import datetime, timedelta
from typing import Any, Callable, Deque, Dict, List, Optional

# Per-monitor DPI awareness so UIA rectangles and posted click coordinates are both physical pixels; must precede pyautogui
try:
    ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
except Exception:
    pass

import psutil
import pyautogui
import win32api
import win32con
import win32gui
import win32clipboard

VK_PACKET = 0xE7

try:
    import comtypes.client
    comtypes.client.GetModule("UIAutomationCore.dll")
    from comtypes.gen import UIAutomationClient as UIA
except Exception:
    UIA = None

class WeChatController:
    """微信自动化操作控制器（仅 NT 版本）。"""

    # 类级别：每次工具调用都会新建控制器
    _pending: Dict[str, Dict[str, Any]] = {}
    _recent: Deque[Dict[str, Any]] = deque(maxlen=20)

    def __init__(self):
        # 设置日志级别为DEBUG
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.3

        self.wechat_version: Optional[str] = None
        self.is_nt_version: bool = False
        self._last_window_kind: Optional[str] = None
        self._detect_wechat_version()

    def _detect_wechat_version(self) -> Optional[str]:
        try:
            window_hwnd = self._find_wechat_window()
            window_is_nt = self._last_window_kind == "nt" and window_hwnd is not None

            for proc in psutil.process_iter(['name', 'exe']):
                name = proc.info.get('name') or ""
                if 'wechat' not in name.lower():
                    continue

                exe = proc.info.get('exe')
                if not exe:
                    continue

                version_info = win32api.GetFileVersionInfo(exe, "\\")
                version = f"{version_info['FileVersionMS'] >> 16}.{version_info['FileVersionMS'] & 0xFFFF}.{version_info['FileVersionLS'] >> 16}.{version_info['FileVersionLS'] & 0xFFFF}"
                self.wechat_version = version

                try:
                    major_version = int(version.split('.')[0])
                except Exception:
                    major_version = 0

                self.is_nt_version = window_is_nt or major_version >= 4
                if self.is_nt_version and major_version >= 4:
                    self.logger.info(f"Detected WeChat NT framework version: {version}")
                elif self.is_nt_version and window_is_nt:
                    self.logger.info(f"Detected WeChat NT framework window (file version: {version})")
                else:
                    self.logger.info(f"Detected WeChat legacy version (<4.0): {version} (will be skipped)")
                return version

            self.logger.warning("Could not detect WeChat process/version")
            self.wechat_version = None
            self.is_nt_version = window_is_nt
            return None
        except Exception as e:
            self.logger.error(f"Error detecting WeChat version: {e}")
            self.wechat_version = None
            self.is_nt_version = False
            return None

    def _find_wechat_window(self) -> Optional[int]:
        import re

        import win32process

        nt_windows = []
        legacy_windows = []
        # Title matching alone also hits other apps, e.g. an editor showing a path containing "WeChat"
        wechat_pids = {p.pid for p in psutil.process_iter(['name']) if (p.info.get('name') or "").lower() in ("weixin.exe", "wechat.exe")}

        def enum_windows_callback(hwnd, _):
            if not win32gui.IsWindowVisible(hwnd):
                return True
            if win32process.GetWindowThreadProcessId(hwnd)[1] not in wechat_pids:
                return True
            class_name = win32gui.GetClassName(hwnd)
            window_text = win32gui.GetWindowText(hwnd)

            # 优先匹配主窗口类名
            if class_name == "WeChatMainWndForPC":
                nt_windows.insert(0, hwnd) # 插入到最前面
                return True
            
            nt_class_patterns = [
                r"ChatWnd",
                r"Qt\d+QWindowIcon",
            ]
            for pattern in nt_class_patterns:
                if re.match(pattern, class_name):
                    # 只有标题包含 WeChat 或 微信 才认为是有效窗口，防止误匹配其他 Qt 应用
                    if "WeChat" in window_text or "微信" in window_text:
                        nt_windows.append(hwnd)
                        return True

            if "微信" in window_text or "WeChat" in window_text:
                legacy_windows.append(hwnd)
            return True

        win32gui.EnumWindows(enum_windows_callback, None)
        if nt_windows:
            self._last_window_kind = "nt"
            return nt_windows[0]
        if legacy_windows:
            self._last_window_kind = "legacy"
            return legacy_windows[0]
        self._last_window_kind = None
        return None

    def _ensure_modifiers_released(self):
        """确保所有修饰键都已释放"""
        import ctypes
        keys = [0x10, 0x11, 0x12] # Shift, Ctrl, Alt
        for key in keys:
            if ctypes.windll.user32.GetKeyState(key) & 0x8000:
                ctypes.windll.user32.keybd_event(key, 0, 0x0002, 0) # Key up

    def _activate_window(self, hwnd: int) -> bool:
        try:
            self._ensure_modifiers_released()
            
            # 1. 强制恢复窗口（解决最小化问题）
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            
            # 2. 尝试标准置顶
            try:
                win32gui.SetForegroundWindow(hwnd)
            except Exception:
                pass  # 可能会因为 Windows 限制而失败

            # 3. 检查是否已经置顶
            if win32gui.GetForegroundWindow() == hwnd:
                return True

            # Foreground lock: a synthetic Alt press makes this process the last input source
            try:
                win32api.keybd_event(win32con.VK_MENU, 0, 0, 0)
                try:
                    win32gui.SetForegroundWindow(hwnd)
                finally:
                    win32api.keybd_event(win32con.VK_MENU, 0, win32con.KEYEVENTF_KEYUP, 0)
            except Exception as e:
                self.logger.error(f"Alt-key foreground attempt failed: {e}")
            if win32gui.GetForegroundWindow() == hwnd:
                return True

            # 4. 如果标准置顶失败，使用 AttachThreadInput 大法
            # 这是官方推荐的绕过 Foreground Lock 的方法，比模拟按键更安全
            try:
                import win32process
                import ctypes
                from ctypes import windll
                
                foreground_hwnd = win32gui.GetForegroundWindow()
                if foreground_hwnd != 0:
                    foreground_thread_id = win32process.GetWindowThreadProcessId(foreground_hwnd)[0]
                    current_thread_id = windll.kernel32.GetCurrentThreadId()
                    
                    if foreground_thread_id != current_thread_id:
                        # 附加输入上下文
                        windll.user32.AttachThreadInput(current_thread_id, foreground_thread_id, True)
                        # 再次尝试置顶
                        try:
                            win32gui.SetForegroundWindow(hwnd)
                            win32gui.SetFocus(hwnd)
                        except Exception:
                            pass
                        # 解除附加
                        windll.user32.AttachThreadInput(current_thread_id, foreground_thread_id, False)
            except Exception as e:
                self.logger.error(f"AttachThreadInput failed: {e}")

            # 5. 等待并验证置顶结果
            for _ in range(10): # 最多等待 1 秒
                if win32gui.GetForegroundWindow() == hwnd:
                    return True
                time.sleep(0.1)
                try:
                    win32gui.SetForegroundWindow(hwnd)
                except Exception:
                    pass
            
            # 6. 最终检查：如果没有获得焦点，绝对不要继续
            if win32gui.GetForegroundWindow() != hwnd:
                self.logger.error("Failed to bring WeChat window to foreground. Operation aborted to prevent mis-clicks.")
                return False
                
            return True
        except Exception as e:
            self.logger.error(f"Failed to activate window: {e}")
            return False

    def _find_and_click_input_box(self) -> bool:
        try:
            hwnd = self._find_wechat_window()
            if not hwnd:
                self.logger.error("WeChat window not found")
                return False

            rect = win32gui.GetWindowRect(hwnd)
            window_left, window_top, window_right, window_bottom = rect
            window_width = window_right - window_left

            input_positions = [
                (window_left + window_width // 2, window_bottom - 80),
                (window_left + window_width // 2, window_bottom - 120),
                (window_left + window_width // 3, window_bottom - 100),
                (window_left + window_width * 2 // 3, window_bottom - 100),
                (pyautogui.size()[0] // 2, int(pyautogui.size()[1] * 0.85)),
            ]

            for click_x, click_y in input_positions:
                try:
                    pyautogui.click(int(click_x), int(click_y))
                    time.sleep(0.4)
                    pyautogui.typewrite('a')
                    time.sleep(0.1)
                    pyautogui.press('backspace')
                    time.sleep(0.1)
                    return True
                except Exception:
                    continue

            self.logger.error("All input box positions failed")
            return False
        except Exception as e:
            self.logger.error(f"Failed to locate input box: {e}")
            return False

    def _paste_text_via_clipboard(self, text: str) -> Optional[str]:
        original_data: Optional[str] = None
        win32clipboard.OpenClipboard()
        try:
            try:
                data = win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
                if isinstance(data, str):
                    original_data = data
            except Exception:
                original_data = None
        finally:
            win32clipboard.CloseClipboard()

        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.12)
        pyautogui.press('delete')
        time.sleep(0.25)

        win32clipboard.OpenClipboard()
        try:
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardText(text, win32clipboard.CF_UNICODETEXT)
        finally:
            win32clipboard.CloseClipboard()

        time.sleep(0.25)
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(0.6)
        return original_data

    def _restore_clipboard(self, original_data: Optional[str]) -> None:
        if not original_data:
            return
        try:
            win32clipboard.OpenClipboard()
            try:
                win32clipboard.EmptyClipboard()
                win32clipboard.SetClipboardText(original_data, win32clipboard.CF_UNICODETEXT)
            finally:
                win32clipboard.CloseClipboard()
        except Exception:
            return

    def _input_text_via_clipboard(self, text: str) -> bool:
        try:
            original_data = self._paste_text_via_clipboard(text)
            self._restore_clipboard(original_data)
            return True
        except Exception as e:
            self.logger.error(f"Failed to input text via clipboard: {e}")
            return False

    def _search_contact_nt(self, contact_name: str) -> bool:
        # Double check focus before typing
        hwnd = self._find_wechat_window()
        if not hwnd or win32gui.GetForegroundWindow() != hwnd:
             self.logger.error("WeChat not focused, aborting search")
             return False

        original_data: Optional[str] = None
        try:
            pyautogui.hotkey('ctrl', 'f')
            time.sleep(1.0)
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.2)
            pyautogui.press('delete')
            time.sleep(0.2)

            original_data = self._paste_text_via_clipboard(contact_name)

            pyautogui.press('enter')
            time.sleep(1.0)

            return True
        except Exception as e:
            self.logger.error(f"Failed to search contact in NT: {e}")
            return False
        finally:
            self._restore_clipboard(original_data)

    def _send_text_nt(self, message: str) -> bool:
        try:
            if not self._find_and_click_input_box():
                # 尝试再次寻找
                time.sleep(0.5)
                if not self._find_and_click_input_box():
                    return False

            original_data = self._paste_text_via_clipboard(message)

            try:
                pyautogui.press('enter')
                time.sleep(0.6)
                # 尝试恢复剪贴板，但失败不影响发送结果
                try:
                    self._restore_clipboard(original_data)
                except Exception:
                    pass
                return True
            except Exception:
                try:
                    pyautogui.hotkey('ctrl', 'enter')
                    time.sleep(0.6)
                    # 尝试恢复剪贴板，但失败不影响发送结果
                    try:
                        self._restore_clipboard(original_data)
                    except Exception:
                        pass
                    return True
                except Exception:
                    try:
                        pyautogui.hotkey('alt', 's')
                        time.sleep(0.6)
                        # 尝试恢复剪贴板，但失败不影响发送结果
                        try:
                            self._restore_clipboard(original_data)
                        except Exception:
                            pass
                        return True
                    except Exception:
                        return False
        except Exception as e:
            self.logger.error(f"Failed to send text in NT: {e}")
            return False
    
    # --- UI Automation path: no foreground, real cursor, keyboard or clipboard use ---

    @staticmethod
    def _normalize(text: Optional[str]) -> str:
        return " ".join((text or "").split())

    @staticmethod
    def _wait_for(check: Callable[[], Any], timeout: float, interval: float = 0.15) -> Any:
        deadline = time.monotonic() + timeout
        while True:
            value = check()
            if value or time.monotonic() >= deadline:
                return value
            time.sleep(interval)

    def _uia_client(self):
        if UIA is None:
            return None
        if getattr(self, "_uia", None) is None:
            self._uia = comtypes.client.CreateObject(UIA.CUIAutomation, interface=UIA.IUIAutomation)
        return self._uia

    def _uia_find(self, root, prop_id: int, value: str):
        try:
            return root.FindFirst(UIA.TreeScope_Descendants, self._uia.CreatePropertyCondition(prop_id, value))
        except Exception:
            return None

    def _uia_children(self, element) -> list:
        try:
            found = element.FindAll(UIA.TreeScope_Children, self._uia.CreateTrueCondition())
            return [found.GetElement(i) for i in range(found.Length)]
        except Exception:
            return []

    def _uia_value(self, element) -> Optional[str]:
        try:
            return element.GetCurrentPattern(UIA.UIA_ValuePatternId).QueryInterface(UIA.IUIAutomationValuePattern).CurrentValue
        except Exception:
            return None

    def _uia_set_value(self, element, text: str) -> bool:
        try:
            element.GetCurrentPattern(UIA.UIA_ValuePatternId).QueryInterface(UIA.IUIAutomationValuePattern).SetValue(text)
            return True
        except Exception as e:
            self.logger.error(f"UIA SetValue failed: {e}")
            return False

    def _post_click(self, hwnd: int, element) -> bool:
        """Click via posted window messages; WeChat need not be foreground or uncovered."""
        try:
            rect = element.CurrentBoundingRectangle
            if rect.right <= rect.left or rect.bottom <= rect.top:
                return False
            cx, cy = win32gui.ScreenToClient(hwnd, ((rect.left + rect.right) // 2, (rect.top + rect.bottom) // 2))
            lparam = win32api.MAKELONG(cx & 0xFFFF, cy & 0xFFFF)
            # A click on a window Qt thinks is inactive makes WeChat activate itself; a sent WM_SETFOCUS avoids that
            win32gui.SendMessage(hwnd, win32con.WM_SETFOCUS, 0, 0)
            win32gui.PostMessage(hwnd, win32con.WM_MOUSEMOVE, 0, lparam)
            # Freshly shown rows (search results) ignore a click until they have seen hover
            time.sleep(0.1)
            win32gui.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lparam)
            win32gui.PostMessage(hwnd, win32con.WM_LBUTTONUP, 0, lparam)
            return True
        except Exception as e:
            self.logger.error(f"Posted click failed: {e}")
            return False

    def _uia_chat_ui_available(self, hwnd: int) -> bool:
        if self._uia_client() is None:
            return False
        root = self._uia.ElementFromHandle(hwnd)
        return self._uia_find(root, UIA.UIA_AutomationIdPropertyId, "session_list") is not None

    def _uia_current_chat(self, root) -> Optional[str]:
        field = self._uia_find(root, UIA.UIA_AutomationIdPropertyId, "chat_input_field")
        return field.CurrentName if field else None

    def _uia_bubbles(self, root) -> List[str]:
        messages = self._uia_find(root, UIA.UIA_AutomationIdPropertyId, "chat_message_list")
        if not messages:
            return []
        # ChatItemView rows are timestamps
        return [self._normalize(e.CurrentName) for e in self._uia_children(messages) if e.CurrentClassName != "mmui::ChatItemView"]

    @staticmethod
    def _post_key(hwnd: int, vk: int, count: int = 1) -> None:
        for _ in range(count):
            win32gui.PostMessage(hwnd, win32con.WM_KEYDOWN, vk, 1)
            win32gui.PostMessage(hwnd, win32con.WM_KEYUP, vk, 0xC0000001)

    def _post_text(self, hwnd: int, field, text: str) -> bool:
        """Type by posted WM_CHAR. Emoji need a VK_PACKET key-down per UTF-16 unit, and WeChat
        inserts them ahead of pending plain text, so each run is confirmed before the next."""
        typed = self._uia_value(field) or ""
        for wide, run in itertools.groupby(text, key=lambda ch: ord(ch) > 0xFFFF):
            run = "".join(run)
            data = run.encode("utf-16-le")
            if wide:
                # VK_PACKET input is only accepted while WeChat believes it has focus
                win32gui.SendMessage(hwnd, win32con.WM_SETFOCUS, 0, 0)
            for i in range(0, len(data), 2):
                unit = int.from_bytes(data[i:i + 2], "little")
                if wide:
                    win32gui.PostMessage(hwnd, win32con.WM_KEYDOWN, VK_PACKET, 1)
                win32gui.PostMessage(hwnd, win32con.WM_CHAR, unit, 1)
                if wide:
                    win32gui.PostMessage(hwnd, win32con.WM_KEYUP, VK_PACKET, 0xC0000001)
            typed += run
            if not self._wait_for(lambda: self._uia_value(field) == typed, 0.6 if wide else 1.5, 0.05):
                return False
        return True

    def _restore_foreground(self, hwnd: int, previous: int) -> None:
        """Hand focus back to the user's window after WeChat had to be activated."""
        if not previous or previous == hwnd or not win32gui.IsWindow(previous) or win32gui.GetForegroundWindow() != hwnd:
            return
        import win32process
        wechat_thread = win32process.GetWindowThreadProcessId(hwnd)[0]
        current_thread = win32api.GetCurrentThreadId()
        ctypes.windll.user32.AttachThreadInput(current_thread, wechat_thread, True)
        try:
            win32gui.SetForegroundWindow(previous)
        except Exception:
            pass
        finally:
            ctypes.windll.user32.AttachThreadInput(current_thread, wechat_thread, False)

    def _open_chat_from_list(self, hwnd: int, root, contact_name: str) -> Optional[str]:
        """Background click on a visible chat list row; WeChat is not activated."""
        if self._uia_current_chat(root) == contact_name:
            return contact_name
        item = self._uia_find(root, UIA.UIA_AutomationIdPropertyId, f"session_item_{contact_name}")
        listing = self._uia_find(root, UIA.UIA_AutomationIdPropertyId, "session_list")
        if not item or not listing:
            return None
        row, area = item.CurrentBoundingRectangle, listing.CurrentBoundingRectangle
        if row.top < area.top or row.bottom > area.bottom:
            return None
        if self._post_click(hwnd, item) and self._wait_for(lambda: self._uia_current_chat(root) == contact_name, 2.0):
            return contact_name
        return None

    def _with_wechat_keys(self, hwnd: int, vks: List[int], action: Callable[[], Any]) -> Any:
        """Run action with vks held in WeChat's thread key state only; the real keyboard is untouched.
        Qt reads modifiers from this state, so posted keys then act as Ctrl+V or Shift+Enter."""
        import win32process
        wechat_thread = win32process.GetWindowThreadProcessId(hwnd)[0]
        current_thread = win32api.GetCurrentThreadId()
        user32 = ctypes.windll.user32
        if not user32.AttachThreadInput(current_thread, wechat_thread, True):
            return None
        state = (ctypes.c_ubyte * 256)()
        user32.GetKeyboardState(state)
        saved = bytes(state)
        try:
            for vk in vks:
                state[vk] |= 0x80
            user32.SetKeyboardState(state)
            return action()
        finally:
            user32.SetKeyboardState((ctypes.c_ubyte * 256)(*saved))
            user32.AttachThreadInput(current_thread, wechat_thread, False)

    def _field_equals(self, field, text: str) -> Callable[[], bool]:
        return lambda: (self._uia_value(field) or "").replace("\r", "\n") == text

    @staticmethod
    def _clipboard_snapshot() -> Optional[List[tuple]]:
        """Every clipboard format as restorable data, or None if something (e.g. copied files) cannot be restored exactly."""
        # Windows recreates these from the formats that are kept
        synthesized = {win32con.CF_TEXT, win32con.CF_OEMTEXT, win32con.CF_LOCALE, win32con.CF_BITMAP, win32con.CF_DIBV5}
        win32clipboard.OpenClipboard()
        try:
            saved, fmt = [], 0
            while True:
                fmt = win32clipboard.EnumClipboardFormats(fmt)
                if not fmt:
                    return saved
                if fmt in synthesized:
                    continue
                data = win32clipboard.GetClipboardData(fmt)
                if not isinstance(data, (bytes, str)):
                    return None
                saved.append((fmt, data))
        except Exception:
            return None
        finally:
            win32clipboard.CloseClipboard()

    @staticmethod
    def _clipboard_put(entries: List[tuple]) -> None:
        win32clipboard.OpenClipboard()
        try:
            win32clipboard.EmptyClipboard()
            for fmt, data in entries:
                win32clipboard.SetClipboardData(fmt, data)
        finally:
            win32clipboard.CloseClipboard()

    def _paste_text(self, hwnd: int, field, text: str) -> bool:
        """Paste via clipboard and a background Ctrl+V; the user's clipboard is restored afterwards."""
        snapshot = self._clipboard_snapshot()
        if snapshot is None:
            return False
        # Keeps the message out of Windows clipboard history and cloud sync
        exclude = win32clipboard.RegisterClipboardFormat("ExcludeClipboardContentFromMonitorProcessing")
        try:
            self._clipboard_put([(win32con.CF_UNICODETEXT, text), (exclude, b"\0")])

            def paste():
                self._post_key(hwnd, ord("V"))
                return self._wait_for(self._field_equals(field, text), 1.5, 0.05)

            return bool(self._with_wechat_keys(hwnd, [win32con.VK_CONTROL, win32con.VK_LCONTROL], paste))
        except Exception as e:
            self.logger.error(f"Clipboard paste failed: {e}")
            return False
        finally:
            try:
                self._clipboard_put(snapshot)
            except Exception as e:
                self.logger.error(f"Failed to restore clipboard: {e}")

    def _type_lines(self, hwnd: int, field, text: str) -> bool:
        """Posted typing with a background Shift+Enter for each line break."""
        lines = text.split("\n")
        for i, line in enumerate(lines):
            if line and not self._post_text(hwnd, field, line):
                return False
            if i < len(lines) - 1:
                expected = "\n".join(lines[:i + 1]) + "\n"

                def newline():
                    self._post_key(hwnd, win32con.VK_RETURN)
                    return self._wait_for(self._field_equals(field, expected), 1.0, 0.05)

                if not self._with_wechat_keys(hwnd, [win32con.VK_SHIFT, win32con.VK_LSHIFT], newline):
                    return False
        return True

    def _enter_text(self, hwnd: int, field, text: str, previous_foreground: int) -> None:
        """Type into a field that already has focus inside WeChat, trying the background methods first."""
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        if not any(ord(ch) > 0xFFFF or ch in "\n\t" for ch in text):
            if self._post_text(hwnd, field, text):
                return
        else:
            # Emoji and line breaks: posted characters cannot carry them reliably
            if self._paste_text(hwnd, field, text):
                return
            self._clear_field(hwnd, field)
            if "\t" not in text and self._type_lines(hwnd, field, text):
                return
        # Last resort: SetValue is reliable but activates WeChat, so hand focus straight back
        self._clear_field(hwnd, field)
        self._uia_set_value(field, text)
        self._restore_foreground(hwnd, previous_foreground)

    def _open_chat_via_search(self, hwnd: int, root, contact_name: str, previous_foreground: int) -> Optional[str]:
        search = self._uia_find(root, UIA.UIA_ClassNamePropertyId, "mmui::XValidatorTextEdit")
        if not search:
            return None

        def snapshot() -> list:
            listing = self._uia_find(root, UIA.UIA_AutomationIdPropertyId, "search_list")
            return [(e, e.CurrentAutomationId or "", e.CurrentName) for e in self._uia_children(listing)] if listing else []

        # WeChat only shows search results while it believes it has focus, which _post_click provides
        if not self._post_click(hwnd, search):
            return None
        time.sleep(0.2)
        self._clear_field(hwnd, search)
        time.sleep(0.2)
        baseline = [s[1:] for s in snapshot()]
        self._enter_text(hwnd, search, contact_name, previous_foreground)

        # Results refresh with a lag; wait until they differ from the cleared state and stop changing
        previous, current = None, []
        deadline = time.monotonic() + 3.0
        while time.monotonic() < deadline:
            time.sleep(0.1)
            current = snapshot()
            keys = [s[1:] for s in current]
            if keys and keys != baseline and keys == previous:
                break
            previous = keys
        candidates = [e for e, auto_id, _ in current if auto_id.startswith("search_item_")]
        # Results for any other query (e.g. stray input in the box) must not pick the chat
        if not candidates or self._uia_value(search) != contact_name:
            self._clear_field(hwnd, search)
            return None
        target = next((e for e in candidates if e.CurrentName == contact_name), candidates[0])
        chat_name = target.CurrentName
        if self._uia_current_chat(root) == chat_name:
            # Selecting the chat that is already open closes it instead
            # No Escape: outside the search box it can hide WeChat to the tray. Typing clicks the input box, which closes the search
            self._clear_field(hwnd, search)
            return chat_name
        # Closing the results popup makes WeChat activate itself; the caller hands focus back
        if self._post_click(hwnd, target) and self._wait_for(lambda: self._uia_current_chat(root) == chat_name, 2.0):
            return chat_name
        self._clear_field(hwnd, search)
        return None

    def _clear_field(self, hwnd: int, field) -> bool:
        value = self._uia_value(field) or ""
        if value:
            # Deletes and backspaces in equal number empty the box wherever the caret is
            units = len(value.encode("utf-16-le")) // 2 + 2
            self._post_key(hwnd, win32con.VK_DELETE, units)
            self._post_key(hwnd, win32con.VK_BACK, units)
            if not self._wait_for(lambda: not self._uia_value(field), 1.0):
                self._uia_set_value(field, "")
        return not self._uia_value(field)

    def _type_message(self, hwnd: int, field, message: str, previous_foreground: int) -> bool:
        if not self._post_click(hwnd, field):
            return False
        time.sleep(0.2)
        if not self._clear_field(hwnd, field):
            return False
        self._enter_text(hwnd, field, message, previous_foreground)
        target = self._normalize(message)
        return bool(self._wait_for(lambda: self._normalize(self._uia_value(field)) == target, 1.5))

    def _send_via_uia(self, hwnd: int, contact_name: str, message: str, result: Dict[str, Any]) -> Dict[str, Any]:
        result["method"] = "uia"
        retries: List[str] = []
        result["retry_used"] = retries
        root = self._uia.ElementFromHandle(hwnd)
        previous_foreground = win32gui.GetForegroundWindow()
        was_minimized = bool(win32gui.IsIconic(hwnd))
        if was_minimized:
            win32gui.ShowWindow(hwnd, win32con.SW_SHOWNOACTIVATE)
            time.sleep(0.5)

        def fail(stage: str, reason: str) -> Dict[str, Any]:
            result["stage"], result["reason"] = stage, reason
            self.logger.error(f"UIA send failed at {stage}: {reason} (retries: {retries})")
            return result

        try:
            chat_name = None
            for attempt in range(2):
                chat_name = self._open_chat_from_list(hwnd, root, contact_name) or self._open_chat_via_search(hwnd, root, contact_name, previous_foreground)
                self._restore_foreground(hwnd, previous_foreground)
                if chat_name:
                    break
                retries.append("open_chat")
            if not chat_name:
                return fail("open_chat", "contact_not_found_or_chat_not_opened")
            result["chat_name"] = chat_name

            field = self._wait_for(lambda: self._uia_find(root, UIA.UIA_AutomationIdPropertyId, "chat_input_field"), 2.0)
            send_button = self._uia_find(root, UIA.UIA_ClassNamePropertyId, "mmui::XOutlineButton")
            if not field or not send_button:
                return fail("set_text", "input_field_not_found")
            target = self._normalize(message)
            before = self._uia_bubbles(root)

            # Typing and clicking Send retry together; Send is only clicked while the box holds exactly the message
            failure: Optional[tuple] = None
            for attempt in range(2):
                if failure:
                    retries.append(failure[0])
                if not self._type_message(hwnd, field, message, previous_foreground):
                    failure = ("set_text", "input_text_mismatch")
                    continue
                if self._normalize(self._uia_value(field)) != target:
                    failure = ("set_text", "input_changed_before_send")
                    continue
                self._post_click(hwnd, send_button)
                if self._wait_for(lambda: not self._normalize(self._uia_value(field)), 3.0):
                    failure = None
                    break
                failure = ("click_send", "send_button_had_no_effect")
            if failure:
                self._clear_field(hwnd, field)
                return fail(*failure)

            def delivered() -> bool:
                after = self._uia_bubbles(root)
                return bool(after) and after[-1] == target and after != before

            if not self._wait_for(delivered, 4.0):
                # Input was cleared, so it may have sent; not retried to avoid a duplicate
                return fail("verify", "message_not_found_in_chat_after_send")

            result.update(ok=True, verified=True, stage="send_text", reason=None)
            return result
        finally:
            self._restore_foreground(hwnd, previous_foreground)
            if win32gui.GetForegroundWindow() != hwnd:
                # Undo the simulated focus from the search step
                win32gui.SendMessage(hwnd, win32con.WM_KILLFOCUS, 0, 0)
            if was_minimized:
                win32gui.ShowWindow(hwnd, win32con.SW_SHOWMINNOACTIVE)

    async def send_text_message(self, contact_name: str, message: str) -> Dict[str, Any]:
        """向指定联系人发送文本消息。"""
        result: Dict[str, Any] = {
            "ok": False,
            "contact_name": contact_name,
            "wechat_version": None,
            "is_nt_framework": False,
            "stage": None,
            "reason": None,
            "retry_used": None,
            "verified": False,
            "method": None,
        }
        try:
            version = self._detect_wechat_version()
            result["wechat_version"] = version
            result["is_nt_framework"] = self.is_nt_version

            if not self.is_nt_version:
                result["stage"] = "version_check"
                result["reason"] = "non_nt_version_skipped"
                return result

            hwnd = self._find_wechat_window()
            if not hwnd:
                result["stage"] = "find_window"
                result["reason"] = "wechat_window_not_found"
                return result

            if self._uia_chat_ui_available(hwnd):
                return self._send_via_uia(hwnd, contact_name, message, result)

            # Fallback for builds without an accessibility tree: keyboard input, needs foreground, unverified
            self.logger.warning("WeChat UI Automation tree unavailable, falling back to keyboard input")
            result["method"] = "keyboard"
            if not self._activate_window(hwnd):
                result["stage"] = "activate_window"
                result["reason"] = "failed_to_activate_window"
                return result
            if not self._search_contact_nt(contact_name):
                result["stage"] = "search_contact"
                result["reason"] = "search_failed"
                return result

            if self._send_text_nt(message):
                result["ok"] = True
                result["stage"] = "send_text"
                result["reason"] = None
                return result

            result["stage"] = "send_text"
            result["reason"] = "send_failed"
            return result

        except Exception as e:
            self.logger.error(f"Error sending message: {e}")
            result["stage"] = result["stage"] or "exception"
            result["reason"] = str(e)
            return result
    
    async def schedule_message(self, contact_name: str, message: str, delay_seconds: float) -> bool:
        """安排在延迟后发送消息。"""
        try:
            self.logger.info(f"Scheduling message to {contact_name} in {delay_seconds} seconds")

            entry_id = uuid.uuid4().hex
            scheduled_for = datetime.now().astimezone() + timedelta(seconds=delay_seconds)
            self._pending[entry_id] = {
                "contact_name": contact_name,
                "message": message,
                "scheduled_for": scheduled_for,
            }

            async def delayed_send():
                await asyncio.sleep(delay_seconds)
                entry = self._pending.pop(entry_id)
                # 调用异步函数
                try:
                    send_result = await self.send_text_message(contact_name, message)
                except Exception as e:
                    self.logger.error(f"Error in delayed send: {e}")
                    send_result = {"ok": False, "stage": "exception", "reason": str(e)}
                self._recent.appendleft({**entry, "send_result": send_result})

            # 创建异步任务
            asyncio.create_task(delayed_send())
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error scheduling message: {e}")
            return False

    @classmethod
    def list_scheduled(cls) -> Dict[str, List[Dict[str, Any]]]:
        """返回本进程中待发送的定时消息和最近已触发的消息。"""
        return {
            "pending": sorted(cls._pending.values(), key=lambda entry: entry["scheduled_for"]),
            "recent": list(cls._recent),
        }

    def default_test_contact(self) -> str:
        """按客户端语言返回测试联系人：中文版 文件传输助手，英文版 File。
        4.x 中文版窗口标题仍为 WeChat，因此同时检查搜索框名称。"""
        hwnd = self._find_wechat_window()
        chinese = "微信" in (win32gui.GetWindowText(hwnd) if hwnd else "")
        if hwnd and not chinese and self._uia_client():
            search = self._uia_find(self._uia.ElementFromHandle(hwnd), UIA.UIA_ClassNamePropertyId, "mmui::XValidatorTextEdit")
            chinese = search is not None and search.CurrentName == "搜索"
        return "文件传输助手" if chinese else "File"

    def get_status(self) -> Dict[str, Any]:
        """获取微信控制器的当前状态。"""
        try:
            version = self._detect_wechat_version()
            hwnd = self._find_wechat_window()
            return {
                "wechat_available": hwnd is not None,
                "window_handle": hwnd,
                "wechat_version": version,
                "is_nt_framework": self.is_nt_version,
                "supported": self.is_nt_version,
                "framework_type": "NT framework (4.0+)" if self.is_nt_version else "Legacy (<4.0, skipped)"
            }
        except Exception as e:
            self.logger.error(f"Error checking status: {e}")
            return {
                "wechat_available": False,
                "error": str(e)
            }
