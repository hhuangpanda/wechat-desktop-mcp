# WeChat MCP Server

<div align="center">

![Python version](https://img.shields.io/badge/python-3.9%2B-blue)

**An MCP server that sends WeChat messages from the Windows desktop client**

[简体中文](README.md) | **English**

</div>

---

Windows 10/11 and WeChat 4.0 or later only. Works with any MCP client that can run a stdio server, such as Claude Desktop, Claude Code, or Codex in the ChatGPT app.

## Setup

Requires Python 3.9+ and the WeChat desktop client, running and logged in. The window can be minimized or covered, but not closed to the system tray.

```bash
git clone https://github.com/hhuangpanda/WeChat-MCP-Server.git
cd WeChat-MCP-Server
pip install -r requirements.txt
```

Add the server to your client's MCP configuration (for Claude Desktop: `%APPDATA%\Claude\claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "wechat": {
      "command": "python",
      "args": ["C:/path/to/WeChat-MCP-Server/src/mcp_server.py"]
    }
  }
}
```

## Tools

### send_wechat_message

| Name | Type | Description |
|------|------|-------------|
| `contact_name` | `string` | Contact or group name |
| `message` | `string` | Text to send |

The chat is opened from the chat list if it is visible there, otherwise through WeChat's search. A search picks the result whose name matches exactly, or the first result if none does, so a partial name such as `File` reaches File Transfer, but a vague name can reach the wrong chat.

Returns `Message sent and verified in chat '<chat name>'`, plus `(retried: ...)` if a step needed a retry. On failure the result has `isError: true` and text such as `Failed to send message (stage=open_chat, reason=contact_not_found_or_chat_not_opened, ...)`, where `stage` is one of `find_window`, `open_chat`, `set_text`, `click_send`, `verify`.

### schedule_wechat_message

Same parameters as `send_wechat_message`, plus `delay_seconds` (`number`).

### show_scheduled_wechat_messages

No parameters. Returns pending messages and the results of the last 20 that fired. Only messages scheduled by this server process are listed, and they are lost when it exits.

```json
{
  "pending": [{"contact_name": "File", "message": "...", "scheduled_for": "2026-11-01T15:00:00-05:00", "seconds_remaining": 30}],
  "recent": [{"contact_name": "File", "message": "...", "scheduled_for": "2026-11-01T14:30:00-05:00", "result": "Message sent and verified in chat 'File Transfer'"}]
}
```

## Background behavior

- Clicks and typing go to WeChat as window messages, so the mouse, keyboard and other windows are left alone while a message is sent.
- WeChat itself asks to come to the front when a chat is picked from the list or the search closes. Windows usually refuses and flashes WeChat's taskbar button instead; when it allows it, focus is handed back to your window right away.
- Messages with emoji or line breaks are pasted, and the clipboard is restored afterwards and kept out of clipboard history. If the clipboard holds something that cannot be restored exactly (such as copied files), the text is typed instead.
- An unsent draft in the recipient's chat is cleared first. If WeChat is minimized, it is shown without focus during the send and minimized again.
- Clicking into WeChat yourself during a send can interrupt it; the tool then reports a failure rather than sending the wrong text.
- WeChat builds that expose no accessibility tree fall back to keyboard input, which needs the foreground and cannot verify delivery.

## Testing

`tests/test_server.py` and `tests/test_show_scheduled.py` send nothing. These send real messages to File Transfer:

```bash
python tests/test_send_chinese.py
cd examples && python mcp_client_example.py && cd ..
python tests/e2e_interference.py
```

The e2e test opens its own window over WeChat and sends real mouse clicks and keystrokes to it while messages are sent, to check that WeChat never takes the foreground and no keystrokes are lost. It moves your cursor, so don't use the mouse or keyboard while it runs.

## Troubleshooting

- **WeChat window not found**: make sure WeChat is running, logged in and not closed to the tray.
- **Send failed**: `stage` shows the step. `open_chat` usually means the name matched no chat; check it as WeChat displays it.
- **Client can't connect**: check the Python path and dependencies; the server logs to stderr.

## Disclaimer

This project has no affiliation with Tencent or WeChat. Automating WeChat may break its terms of service and get your account restricted or banned, and a WeChat update can break this project at any time. Don't use it for bulk messages, spam or harassment. You use it at your own risk.

## License

[MIT](LICENSE). Bug reports and pull requests are welcome through [Issues](https://github.com/hhuangpanda/WeChat-MCP-Server/issues).
