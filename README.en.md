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
- Smart input box positioning that adapts to different window sizes and layouts
- Clipboard input that avoids input method interference, with automatic backup and restore of the user's clipboard
- Multiple send shortcuts: Enter, Ctrl+Enter, Alt+S
- Asynchronous processing that does not block the AI assistant, with full error handling and logging

## Project Structure

```
WeChat-MCP-Server/
├── src/
│   ├── __init__.py
│   ├── mcp_server.py          # Main MCP server implementation
│   └── wechat_controller.py   # WeChat automation controller
├── tests/
│   ├── test_server.py         # Server functionality test
│   └── test_send_chinese.py   # Chinese message sending test
├── examples/
│   └── mcp_client_example.py  # Client usage example
├── docs/
│   ├── QUICK_START.md         # Quick start guide (Chinese)
│   └── QUICK_START.en.md      # Quick start guide (English)
├── mcp_config.json            # MCP configuration file
├── requirements.txt           # Dependency list
├── LICENSE                    # License file
├── AGENTS.md                  # Guidance for AI assistants
├── README.md                  # Project documentation (Chinese)
└── README.en.md               # Project documentation (English)
```

## Installation and Setup

### 1. Install Dependencies

```bash
git clone https://github.com/hhuangpanda/WeChat-MCP-Server.git
cd WeChat-MCP-Server
pip install -r requirements.txt
```

### 2. Make Sure WeChat Is Running and Logged In

Before use, make sure the WeChat client is running, logged in, and its window is visible (not minimized).

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

## MCP Protocol Implementation

The server implements the following standard methods: `initialize` (initialize the connection), `tools/list` (list tools), and `tools/call` (call a tool).

## Technical Architecture

- **mcp_server.py**: Implements JSON-RPC 2.0, handles MCP method calls, and manages tool registration and execution
- **wechat_controller.py**: Uses pyautogui and win32gui to control the WeChat window, detects the WeChat version (NT framework or legacy) automatically, inputs text through the clipboard, and supports asynchronous sending and scheduling

## Notes

- Requires Windows, the WeChat client, and Python 3.8+
- Requires screen control permission (pyautogui)
- Do not operate the WeChat window manually while the tool is running, and make sure the window is visible and not obscured
- Test with "File Transfer Assistant" first
- Intended only for automating personal WeChat operations. Comply with the WeChat terms of use, and do not use it to send large volumes of messages

## Troubleshooting

- **WeChat window not found**: Make sure WeChat is running and logged in and the window is visible; restart WeChat if needed
- **Message sending failed**: Check that the contact name is correct and the contact is in the recent chats list, and that the WeChat window is active
- **Input box positioning failed**: Keep the WeChat window fully visible and not obscured
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
