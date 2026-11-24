#!/usr/bin/env python3
"""WeChat detection and schedule replies with fake processes and no window. Sends no messages."""

import asyncio
import os
import re
import sys
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import wechat_controller
from mcp_server import MCPServer
from wechat_controller import WeChatController


def fake_processes(*names):
    procs = [SimpleNamespace(pid=i, info={"name": n, "exe": n}) for i, n in enumerate(names)]
    return lambda *args, **kwargs: iter(procs)


def fake_version(major):
    return lambda exe, _: {"FileVersionMS": major << 16, "FileVersionLS": 0}


async def send_with(*process_names, major=4):
    with patch.object(wechat_controller.psutil, "process_iter", fake_processes(*process_names)), \
         patch.object(wechat_controller.win32api, "GetFileVersionInfo", fake_version(major)), \
         patch.object(WeChatController, "_find_wechat_window", lambda self: None):
        return await WeChatController().send_text_message("File", "x")


def check(result, stage, reason):
    assert (result["stage"], result["reason"]) == (stage, reason), result


async def schedule_with(*process_names, window=None):
    with patch.object(wechat_controller.psutil, "process_iter", fake_processes(*process_names)), \
         patch.object(wechat_controller.win32api, "GetFileVersionInfo", fake_version(4)), \
         patch.object(WeChatController, "_find_wechat_window", lambda self: window):
        server = MCPServer()
        await server.handle_request({"jsonrpc": "2.0", "method": "initialize", "params": {}, "id": 0})
        response = await server.handle_request({
            "jsonrpc": "2.0", "id": 1, "method": "tools/call",
            "params": {"name": "schedule_wechat_message",
                       "arguments": {"contact_name": "File", "message": "x", "delay_seconds": 3600.0}},
        })
    WeChatController._pending.clear()
    return response["result"]["content"][0]["text"]


async def check_schedule_replies():
    pattern = r"Message scheduled for \d{4}-\d\d-\d\d \d\d:\d\d:\d\d \(in 3600 seconds\)\."
    tail = r": WeChat must be open, not in the tray, by then or the send will fail\."
    assert re.fullmatch(pattern, await schedule_with("Weixin.exe", window=1))
    assert re.fullmatch(pattern + r" Warning \(wechat_not_running\)" + tail, await schedule_with())
    assert re.fullmatch(pattern + r" Warning \(wechat_window_not_found\)" + tail, await schedule_with("Weixin.exe"))


async def main():
    check(await send_with(), "find_window", "wechat_not_running")
    # Helper processes alone don't count as WeChat running
    check(await send_with("WeChatAppEx.exe"), "find_window", "wechat_not_running")
    # Running but closed to the tray: no visible window
    check(await send_with("Weixin.exe", "WeChatAppEx.exe"), "find_window", "wechat_window_not_found")
    check(await send_with("WeChat.exe", major=3), "version_check", "non_nt_version_skipped")
    await check_schedule_replies()


if __name__ == "__main__":
    asyncio.run(main())
    print("OK")
