#!/usr/bin/env python3
"""Runs the server over stdio and checks the MCP handshake. Sends no messages.

Usage: python tests/test_stdio.py [server command...]  (default: python src/mcp_server.py)
"""

import json
import os
import subprocess
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
command = sys.argv[1:] or [sys.executable, os.path.join(ROOT, "src", "mcp_server.py")]

requests = [
    {"jsonrpc": "2.0", "method": "initialize", "params": {}, "id": 1},
    {"jsonrpc": "2.0", "method": "notifications/initialized"},
    {"jsonrpc": "2.0", "method": "ping", "id": 2},
    {"jsonrpc": "2.0", "method": "tools/list", "id": 3},
]
stdin = "".join(json.dumps(r) + "\n" for r in requests)
proc = subprocess.run(command, input=stdin.encode("utf-8"), capture_output=True, timeout=60)
responses = [json.loads(line) for line in proc.stdout.decode("utf-8").splitlines() if line.strip()]

assert [r.get("id") for r in responses] == [1, 2, 3], responses
assert responses[0]["result"]["serverInfo"]["name"] == "wechat-desktop-mcp"
assert responses[1]["result"] == {}
tools = {t["name"] for t in responses[2]["result"]["tools"]}
assert tools == {"send_wechat_message", "schedule_wechat_message", "show_scheduled_wechat_messages"}, tools
print("OK", responses[0]["result"]["serverInfo"]["version"])
