#!/usr/bin/env python3
"""show_scheduled_wechat_messages 测试。发送函数已替换，不会发送真实消息。"""

import asyncio
import json
import os
import sys
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from mcp_server import MCPServer
from wechat_controller import WeChatController


async def call(server, name, arguments=None):
    response = await server.handle_request({
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {"name": name, "arguments": arguments or {}},
        "id": 1,
    })
    return response["result"]["content"][0]["text"]


async def show(server):
    return json.loads(await call(server, "show_scheduled_wechat_messages"))


async def fake_send(self, contact_name, message):
    if contact_name == "fail":
        return {"ok": False, "stage": "find_window", "reason": "wechat_window_not_found",
                "wechat_version": None, "is_nt_framework": False}
    if contact_name == "raise":
        raise RuntimeError("boom")
    return {"ok": True, "verified": True, "chat_name": contact_name}


async def test_show_scheduled():
    server = MCPServer()
    await server.handle_request({"jsonrpc": "2.0", "method": "initialize", "params": {}, "id": 0})

    assert await show(server) == {"pending": [], "recent": []}

    for contact_name, delay in [("later", 3600), ("ok", 0.02), ("fail", 0.04), ("raise", 0.06)]:
        await call(server, "schedule_wechat_message",
                   {"contact_name": contact_name, "message": "消息", "delay_seconds": delay})

    pending = (await show(server))["pending"]
    assert [entry["contact_name"] for entry in pending] == ["ok", "fail", "raise", "later"]
    assert pending[0]["message"] == "消息"
    assert pending[-1]["seconds_remaining"] > 3500

    await asyncio.sleep(0.2)

    shown = await show(server)
    assert [entry["contact_name"] for entry in shown["pending"]] == ["later"]
    results = {entry["contact_name"]: entry["result"] for entry in shown["recent"]}
    assert results["ok"] == "Message sent and verified in chat 'ok'"
    assert results["fail"] == ("Failed to send message (stage=find_window, "
                               "reason=wechat_window_not_found, retries=None, wechat_version=None, nt=False)")
    assert results["raise"].startswith("Failed to send message (stage=exception, reason=boom")

    text = await call(server, "schedule_wechat_message",
                      {"contact_name": "bad", "message": "消息", "delay_seconds": "soon"})
    assert text == "Failed to schedule message"
    assert len((await show(server))["pending"]) == 1


async def test_recent_is_capped():
    WeChatController._pending.clear()
    WeChatController._recent.clear()
    controller = WeChatController()
    for i in range(25):
        await controller.schedule_message(str(i), "消息", 0)
    await asyncio.sleep(0.05)

    recent = WeChatController.list_scheduled()["recent"]
    assert len(recent) == 20
    assert recent[0]["contact_name"] == "24"


if __name__ == "__main__":
    with patch.object(WeChatController, "send_text_message", fake_send):
        asyncio.run(test_show_scheduled())
        asyncio.run(test_recent_is_capped())
    print("OK")
