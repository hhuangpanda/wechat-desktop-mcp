#!/usr/bin/env python3
"""
End-to-end test: sends real messages to File Transfer through the MCP server (stdio JSON-RPC)
while a separate process simulates a user clicking and typing in another window.

The interferer owns its own window (placed over WeChat), so no user application receives input.
Usage: python tests/e2e_interference.py [case ...]
"""

import ctypes
import json
import os
import random
import subprocess
import sys
import tempfile
import threading
import time

ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(ROOT, "src"))


def run_interferer(mode: str, rect: str, stop_file: str, stats_file: str) -> None:
    import tkinter as tk
    import win32gui

    user32 = ctypes.windll.user32
    wechat = int(rect.split(",")[4])
    left, top, right, bottom = map(int, rect.split(",")[:4])
    root = tk.Tk()
    root.title("e2e interferer")
    root.geometry(f"{right - left}x{bottom - top}+{left}+{top}")
    # Topmost so clicks land here even if WeChat was the active window when the test began
    root.attributes("-topmost", True)
    text = tk.Text(root)
    text.pack(fill="both", expand=True)
    root.update()
    own = int(root.wm_frame(), 16)
    # fg_wechat: times WeChat became the foreground window; fg_other: any window other than ours or WeChat
    stats = {"clicks": 0, "keys_sent": 0, "fg_wechat": 0, "fg_wechat_ms": 0, "fg_other": 0}
    done = threading.Event()

    # Every foreground change is reported by a WinEvent hook, so even very short activations are counted
    foreground = {"hwnd": win32gui.GetForegroundWindow(), "since": time.monotonic()}

    def on_foreground(hook, event, hwnd, id_object, id_child, thread, event_time):
        # AttachThreadInput can raise events that are not real focus changes; trust the actual foreground window
        hwnd = win32gui.GetForegroundWindow()
        if hwnd == foreground["hwnd"]:
            return
        now = time.monotonic()
        if foreground["hwnd"] == wechat:
            stats["fg_wechat_ms"] += round((now - foreground["since"]) * 1000)
        if hwnd == wechat:
            stats["fg_wechat"] += 1
        elif hwnd != own:
            stats["fg_other"] += 1
        foreground.update(hwnd=hwnd, since=now)

    callback = ctypes.WINFUNCTYPE(None, ctypes.c_void_p, ctypes.c_uint, ctypes.c_void_p, ctypes.c_long,
                                  ctypes.c_long, ctypes.c_uint, ctypes.c_uint)(on_foreground)
    user32.SetWinEventHook.restype = ctypes.c_void_p
    hook = user32.SetWinEventHook(3, 3, None, callback, 0, 0, 0)  # EVENT_SYSTEM_FOREGROUND, out of context
    cx, cy = (left + right) // 2, (top + bottom) // 2

    def click(x, y):
        user32.SetCursorPos(x, y)
        user32.mouse_event(2, 0, 0, 0, 0)
        user32.mouse_event(4, 0, 0, 0, 0)
        stats["clicks"] += 1

    def drive():
        # Focus our own window once so typing-only mode starts in it
        click(cx, cy)
        time.sleep(0.3)
        next_click = time.monotonic() + 0.8
        while not os.path.exists(stop_file):
            now = time.monotonic()
            if "click" in mode and now >= next_click:
                click(cx + random.randint(-50, 50), cy + random.randint(-50, 50))
                next_click = now + 0.8
            if "type" in mode:
                # Letters and space only: a leaked keystroke can never press Enter in WeChat
                vk = random.choice([0x20] + list(range(0x41, 0x5B)))
                user32.keybd_event(vk, 0, 0, 0)
                user32.keybd_event(vk, 0, 2, 0)
                stats["keys_sent"] += 1
            time.sleep(0.08)
        done.set()

    def finish():
        if not done.is_set():
            root.after(100, finish)
            return
        root.update()
        user32.UnhookWinEvent(ctypes.c_void_p(hook))
        if foreground["hwnd"] == wechat:
            stats["fg_wechat_ms"] += round((time.monotonic() - foreground["since"]) * 1000)
        stats["keys_received"] = len(text.get("1.0", "end-1c"))
        with open(stats_file, "w") as f:
            json.dump(stats, f)
        root.destroy()

    threading.Thread(target=drive, daemon=True).start()
    root.after(100, finish)
    root.mainloop()


class MCPClient:
    def __init__(self):
        self.proc = subprocess.Popen(
            [sys.executable, os.path.join(ROOT, "src", "mcp_server.py")],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            env={**os.environ, "PYTHONUTF8": "1"}, text=True, encoding="utf-8",
        )
        self.next_id = 0
        self.request("initialize", {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "e2e", "version": "1"}})

    def request(self, method, params):
        self.next_id += 1
        self.proc.stdin.write(json.dumps({"jsonrpc": "2.0", "method": method, "params": params, "id": self.next_id}) + "\n")
        self.proc.stdin.flush()
        return json.loads(self.proc.stdout.readline())

    def call(self, name, arguments):
        return self.request("tools/call", {"name": name, "arguments": arguments})["result"]

    def close(self):
        self.proc.stdin.close()
        try:
            self.proc.wait(10)
        except subprocess.TimeoutExpired:
            self.proc.kill()


class Interference:
    def __init__(self, mode: str, wechat_hwnd: int, wechat_rect: tuple):
        self.mode = mode
        self.dir = tempfile.mkdtemp(prefix="wechat_e2e_")
        self.stop_file = os.path.join(self.dir, "stop")
        self.stats_file = os.path.join(self.dir, "stats.json")
        rect = ",".join(map(str, (*wechat_rect, wechat_hwnd)))
        self.proc = None
        if mode != "none":
            self.proc = subprocess.Popen([sys.executable, os.path.abspath(__file__), "--interferer", mode, rect, self.stop_file, self.stats_file])
            time.sleep(2.0)

    def stop(self) -> dict:
        if not self.proc:
            return {}
        open(self.stop_file, "w").close()
        try:
            self.proc.wait(10)
        except subprocess.TimeoutExpired:
            self.proc.kill()
        with open(self.stats_file) as f:
            return json.load(f)


def open_other_chat(avoid: str) -> str:
    """Open some chat other than the target (one without unread messages) so every send has to find the recipient."""
    import re
    from wechat_controller import WeChatController, UIA
    controller = WeChatController()
    hwnd = controller._find_wechat_window()
    controller._uia_client()
    root = controller._uia.ElementFromHandle(hwnd)
    listing = controller._uia_find(root, UIA.UIA_AutomationIdPropertyId, "session_list")
    for item in controller._uia_children(listing):
        name = item.CurrentAutomationId.removeprefix("session_item_")
        # Unread badge appears as "[10]"; allow a suffix in case other UI languages add one (e.g. "[10条]")
        if name != avoid and not re.search(r"\[\d+[^\]]*\]", item.CurrentName) and controller._open_chat_from_list(hwnd, root, name):
            return name
    raise RuntimeError("no other chat without unread messages to open")


def chat_state(message: str, other_chat: str) -> dict:
    """Independent check after a case: which chat is open, whether the message is in it, any draft left behind,
    and whether the chat the case started in received the message (its chat list preview shows the latest message)."""
    from wechat_controller import WeChatController, UIA
    controller = WeChatController()
    hwnd = controller._find_wechat_window()
    controller._uia_client()
    root = controller._uia.ElementFromHandle(hwnd)
    field = controller._uia_find(root, UIA.UIA_AutomationIdPropertyId, "chat_input_field")
    other = controller._uia_find(root, UIA.UIA_AutomationIdPropertyId, f"session_item_{other_chat}")
    first_line = controller._normalize(message.split("\n")[0])
    return {
        "open_chat": controller._uia_current_chat(root),
        "in_chat": controller._normalize(message) in controller._uia_bubbles(root)[-5:],
        "draft": controller._uia_value(field) if field else None,
        "in_other_chat": bool(other) and first_line in controller._normalize(other.CurrentName),
    }


def set_test_clipboard(files: bool) -> object:
    """Put known content on the clipboard so each case can check that sending leaves it untouched."""
    import struct
    import win32clipboard, win32con
    win32clipboard.OpenClipboard()
    try:
        win32clipboard.EmptyClipboard()
        if files:
            paths = "C:\\Windows\\win.ini\0\0".encode("utf-16-le")
            win32clipboard.SetClipboardData(win32con.CF_HDROP, struct.pack("<IiiII", 20, 0, 0, 0, 1) + paths)
        else:
            win32clipboard.SetClipboardText(f"e2e clipboard sentinel {time.time()}", win32con.CF_UNICODETEXT)
    finally:
        win32clipboard.CloseClipboard()
    return read_test_clipboard()


def read_test_clipboard() -> object:
    import win32clipboard, win32con
    win32clipboard.OpenClipboard()
    try:
        for fmt in (win32con.CF_HDROP, win32con.CF_UNICODETEXT):
            if win32clipboard.IsClipboardFormatAvailable(fmt):
                return win32clipboard.GetClipboardData(fmt)
        return None
    finally:
        win32clipboard.CloseClipboard()


# Every case starts in some other chat and sends to the search term ("File"), so the recipient has to be found
# through search while the interference runs.
# name: (interference, tool, expect success, message suffix)
CASES = {
    "baseline": ("none", "send", True, ""),
    "clicks": ("click", "send", True, ""),
    "typing": ("type", "send", True, ""),
    "clicks_typing": ("click_type", "send", True, ""),
    "emoji": ("click_type", "send", True, " \U0001F600 ok"),
    "minimized": ("click_type", "send", True, ""),
    "schedule": ("click_type", "schedule", True, ""),
    "multiline": ("click", "send", True, "\nsecond line"),
    "multiline_typing": ("click_type", "send", True, "\nsecond line"),
    "emoji_multiline": ("click_type", "send", True, " \U0001F600\nline two \U0001F44D"),
    # Copied files cannot be restored exactly, so the clipboard is left alone and Shift+Enter typing is used
    "multiline_files_clipboard": ("click_type", "send", True, "\nsecond line"),
    "bad_contact": ("click_type", "send", False, ""),
}


def mask(chat: str, contacts: dict) -> str:
    """Shorten real chat names so test output can be shared."""
    if not chat or chat == contacts["recipient"]:
        return chat
    return chat[:2] + "..."


def run_case(name: str, contacts: dict, wechat_hwnd: int) -> dict:
    import win32con, win32gui
    mode, tool, expect_ok, suffix = CASES[name]
    message = f"e2e {name} {time.strftime('%H:%M:%S')} 测试消息{suffix}"
    target = contacts["search"] if expect_ok else contacts["missing"]

    other_chat = open_other_chat(contacts["recipient"])
    clipboard_before = set_test_clipboard(files=name == "multiline_files_clipboard")
    client = MCPClient()
    wechat_rect = win32gui.GetWindowRect(wechat_hwnd)
    if name == "minimized":
        win32gui.ShowWindow(wechat_hwnd, win32con.SW_SHOWMINNOACTIVE)
        time.sleep(0.5)
    interference = Interference(mode, wechat_hwnd, wechat_rect)
    started = time.monotonic()
    if tool == "send":
        result = client.call("send_wechat_message", {"contact_name": target, "message": message})
        text, is_error = result["content"][0]["text"], result.get("isError", False)
    else:
        client.call("schedule_wechat_message", {"contact_name": target, "message": message, "delay_seconds": 2})
        text, is_error = "timeout waiting for scheduled send", True
        for _ in range(40):
            time.sleep(1)
            recent = json.loads(client.call("show_scheduled_wechat_messages", {})["content"][0]["text"])["recent"]
            entry = next((r for r in recent if r["message"] == message), None)
            if entry:
                text, is_error = entry["result"], not entry["result"].startswith("Message sent")
                break
    elapsed = time.monotonic() - started
    stats = interference.stop()
    client.close()
    if name == "minimized":
        minimized_after = bool(win32gui.IsIconic(wechat_hwnd))
        win32gui.ShowWindow(wechat_hwnd, win32con.SW_SHOWNOACTIVATE)
        time.sleep(0.5)

    state = chat_state(message, other_chat)
    reported_ok = not is_error
    checks = {
        "result_matches_expectation": reported_ok == expect_ok,
        "report_is_honest": reported_ok == (state["in_chat"] and state["open_chat"] == contacts["recipient"]),
        "not_sent_to_starting_chat": not state["in_other_chat"],
        "no_draft_left": not state["draft"],
        "clipboard_preserved": read_test_clipboard() == clipboard_before,
        "wechat_never_foreground": stats.get("fg_wechat", 0) == 0,
        "no_keystrokes_lost": stats.get("keys_received", 0) == stats.get("keys_sent", 0),
    }
    if expect_ok:
        checks["sent_to_right_chat"] = state["open_chat"] == contacts["recipient"] and state["in_chat"]
    if name == "minimized":
        checks["minimized_state_restored"] = minimized_after
    return {"case": name, "passed": all(checks.values()), "failed_checks": [k for k, v in checks.items() if not v],
            "started_in": mask(other_chat, contacts), "ended_in": mask(state["open_chat"], contacts), "reported": text,
            "seconds": round(elapsed, 1), "interference": stats}


def main():
    from wechat_controller import WeChatController
    controller = WeChatController()
    hwnd = controller._find_wechat_window()
    chinese = controller.default_test_contact() == "文件传输助手"
    contacts = {
        "recipient": "文件传输助手" if chinese else "File Transfer",
        "search": "文件传输" if chinese else "File",
        "missing": "zz-no-such-contact-e2e",
    }
    cases = sys.argv[1:] or list(CASES)
    results = []
    user_clipboard = WeChatController._clipboard_snapshot()
    try:
        for case in cases:
            outcome = run_case(case, contacts, hwnd)
            results.append(outcome)
            print(json.dumps(outcome, ensure_ascii=False), flush=True)
    finally:
        if user_clipboard is not None:
            WeChatController._clipboard_put(user_clipboard)
    print(f"\n{sum(r['passed'] for r in results)}/{len(results)} passed")
    sys.exit(0 if all(r["passed"] for r in results) else 1)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--interferer":
        run_interferer(*sys.argv[2:6])
    else:
        main()
