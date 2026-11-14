# WeChat MCP Server

<div align="center">

![Python version](https://img.shields.io/badge/python-3.8%2B-blue)

**A WeChat message sending server compliant with the Model Context Protocol (MCP) standard, designed for AI assistants**

[简体中文](README.md) | **English**

</div>

---

## What is MCP?

**Model Context Protocol (MCP)** is an open standard protocol for connecting AI assistants to various data sources and tools. It is like the USB-C port for AI applications, providing a standardized way to connect AI models to external systems.

**Compatibility:** Supports Windows 10/11, WeChat 4.0 and above (NT framework) as well as legacy versions, and works with Claude, ChatGPT, and other AI assistants that support MCP.

## Features

- MCP standard compliant, built on JSON-RPC 2.0
- Sends WeChat text messages (Chinese, English, digits, emoji) with optional scheduled sending
- Detects the WeChat version automatically and adapts to the NT framework (4.0 and above) or legacy versions
- Works in the background through Windows UI Automation and window messages: does not move the mouse or take keyboard focus, so you can keep using other windows while it sends
- Verifies each send by reading the message back from the chat, retries each step once, and returns a clear error when sending fails
- Falls back to keyboard and clipboard input on WeChat builds without an accessibility tree (that mode needs the foreground and cannot verify delivery)
- Asynchronous processing that does not block the AI assistant, with full error handling and logging

## Project Structure

```
WeChat-MCP-Server/
├── src/               # MCP server and WeChat controller
├── tests/             # Test scripts
├── examples/          # Client usage example
├── docs/              # Quick start guide (Chinese and English)
├── mcp_config.json    # MCP configuration file
└── requirements.txt   # Dependency list
```

## Installation and Setup

### 1. Install Dependencies

```bash
git clone https://github.com/hhuangpanda/WeChat-MCP-Server.git
cd WeChat-MCP-Server
pip install -r requirements.txt
```

### 2. Make Sure WeChat Is Running and Logged In

Before use, make sure the WeChat client is running and logged in. The window can be behind other windows or minimized, but not closed to the system tray.

### 3. Configure Your AI Assistant

Add this MCP server to your AI assistant's configuration. Using **Claude Desktop** as an example:

```json
{
  "mcpServers": {
    "wechat": {
      "command": "python",
      "args": ["C:/path/to/WeChat-MCP-Server/src/mcp_server.py"],
      "env": {}
    }
  }
}
```

Replace `C:/path/to/WeChat-MCP-Server` with your actual project path.

## Available Tools

### send_wechat_message

Send a text message to a specified WeChat contact or group.

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `contact_name` | `string` | ✅ | Contact or group name |
| `message` | `string` | ✅ | Text message to send |

```json
{
  "name": "send_wechat_message",
  "arguments": {
    "contact_name": "文件传输助手",
    "message": "Hello from AI assistant!"
  }
}
```

On success it returns `Message sent and verified in chat '<chat name>'`, followed by `(retried: ...)` if any step needed a retry. On failure the result has `isError: true` and text such as `Failed to send message (stage=open_chat, reason=contact_not_found_or_chat_not_opened, retries=[...], ...)`, where `stage` is the step that failed (`find_window`, `open_chat`, `set_text`, `click_send`, `verify`).

### schedule_wechat_message

Schedule a message to be sent after a specified delay.

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `contact_name` | `string` | ✅ | Contact or group name |
| `message` | `string` | ✅ | Text message to send |
| `delay_seconds` | `number` | ✅ | Delay before sending, in seconds |

```json
{
  "name": "schedule_wechat_message",
  "arguments": {
    "contact_name": "文件传输助手",
    "message": "This is a scheduled message!",
    "delay_seconds": 30
  }
}
```

### show_scheduled_wechat_messages

Shows pending scheduled messages (`pending`) and the send results of the last 20 fired messages (`recent`). Takes no parameters. `result` is the same text `send_wechat_message` returns.

The list is held in memory, covers only messages scheduled through this server process, and is cleared when the process exits.

```json
{
  "pending": [
    {
      "contact_name": "文件传输助手",
      "message": "This is a scheduled message!",
      "scheduled_for": "2026-11-01T15:00:00-05:00",
      "seconds_remaining": 30
    }
  ],
  "recent": [
    {
      "contact_name": "文件传输助手",
      "message": "Earlier message",
      "scheduled_for": "2026-11-01T14:30:00-05:00",
      "result": "Message sent and verified in chat '文件传输助手'"
    }
  ]
}
```

## Usage

Once configured, you can make requests to your AI assistant in natural language:

- "Send Zhang San a WeChat message saying 'The meeting is postponed to 3 PM'"
- "Remind me about the meeting in 10 minutes, and send it to the work group"
- "Send today's work summary to File Transfer Assistant"

Direct testing:

```bash
python tests/test_server.py
cd examples && python mcp_client_example.py
```

End-to-end test (sends real messages to File Transfer while another process simulates clicking and typing; do not use the mouse or keyboard while it runs):

```bash
python tests/e2e_interference.py
```

## MCP Protocol Implementation

The server implements the following standard methods: `initialize` (initialize the connection), `tools/list` (list tools), and `tools/call` (call a tool).

## Technical Architecture

- **mcp_server.py**: Implements JSON-RPC 2.0, handles MCP method calls, and manages tool registration and execution
- **wechat_controller.py**: Opens the chat, enters the text and clicks Send through UI Automation (comtypes) and posted window messages, then confirms the message appears in the chat; falls back to pyautogui keyboard input when WeChat exposes no accessibility tree; supports scheduled sending

## Notes

- Requires Windows, the WeChat client, and Python 3.8+
- Messages containing emoji or line breaks are pasted in the background: the clipboard is used for a moment and then restored with all its formats, and the message is kept out of Windows clipboard history. If the clipboard holds something that cannot be restored exactly (such as copied files), it is left alone and the text is typed instead
- Only if those methods fail is the text set through UI Automation, which activates WeChat for a moment; focus is handed straight back, and the text is checked again before sending
- Clicking into WeChat yourself while a message is being sent can interrupt it; the tool then reports a failure instead of sending the wrong text
- Any unsent draft in the recipient's chat is cleared before the message is typed; drafts in other chats are not touched
- If WeChat is minimized, it is shown (without taking focus) for the duration of the send and minimized again afterwards
- Test with "File Transfer Assistant" first
- Intended only for automating personal WeChat operations. Comply with the WeChat terms of use, and do not use it to send large volumes of messages

## Troubleshooting

- **WeChat window not found**: Make sure WeChat is running and logged in and the window is visible; restart WeChat if needed
- **Message sending failed**: The error's `stage` shows which step failed. `open_chat` usually means the contact name matched no search result; check the name as WeChat displays it
- **MCP connection failed**: Check the Python environment, dependencies, and configuration file path, and read the server logs

## Development and Extension

Adding a new tool:

1. Add the tool definition in `_register_tools()` in `mcp_server.py`
2. Implement the corresponding execution method
3. Add the specific functionality in `wechat_controller.py`
4. Update the configuration file and documentation

The current version supports Windows only. Supporting other platforms requires replacing the win32gui-related code, adapting window management, and adjusting the keyboard shortcut mappings.

Roadmap:

- [ ] Support macOS and Linux
- [ ] Add more WeChat operations (such as sending images and files)

## Important Disclaimer

This project involves WeChat automation and carries risk. Assess it yourself before use, and bear all consequences.

- This project is for technical research and learning only. It has no affiliation with Tencent or WeChat and has not been authorized or endorsed by them
- Using WeChat automation tools may violate the WeChat terms of service and can lead to your account being restricted, banned, or closed
- It may cause message sending errors, data loss, or leakage, and a WeChat update may break the project at any time
- Do not use it to send ads or spam in bulk, harass others, or for any purpose that violates laws and regulations
- Assess the legal risks yourself before any commercial use
- Developers, contributors, and distributors bear no responsibility for any consequences of using this project. Continued use means you accept these terms

## License

This project is released under the **MIT License**, which allows commercial use, modification, distribution, and private use, provided the copyright and license notices are kept. The MIT License legally permits commercial use, but commercial use of WeChat automation tools carries high risk, which the user bears.

## Contributing

Report bugs or suggest features through [Issues](https://github.com/hhuangpanda/WeChat-MCP-Server/issues), with detailed error messages and steps to reproduce.

Code contributions: fork the project, create a feature branch, commit your changes, and open a Pull Request.
