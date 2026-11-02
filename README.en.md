# WeChat MCP Server

<div align="center">

![Python version](https://img.shields.io/badge/python-3.8%2B-blue)

**A WeChat message sending server compliant with the Model Context Protocol (MCP) standard, designed for AI assistants**

[简体中文](README.md) | **English**

[Quick Start](#-installation-and-setup) • [Features](#-features) • [Usage](#-usage) • [API Docs](#️-available-tools) • [Contributing](#-contributing)

</div>

---

## 📋 Table of Contents

- [What is MCP?](#-what-is-mcp)
- [Features](#-features)
- [Project Structure](#-project-structure)
- [Installation and Setup](#-installation-and-setup)
- [Available Tools](#️-available-tools)
- [Usage](#-usage)
- [Automated Tasks and Message Reporting](#-automated-tasks-and-message-reporting)
- [MCP Protocol Implementation](#-mcp-protocol-implementation)
- [Technical Architecture](#️-technical-architecture)
- [Notes](#️-notes)
- [Troubleshooting](#-troubleshooting)
- [Development and Extension](#-development-and-extension)
- [Disclaimer](#️-important-disclaimer)
- [License](#-license)
- [Contributing](#-contributing)

---

## 🤖 What is MCP?

> **Model Context Protocol (MCP)** is an open standard protocol for connecting AI assistants to various data sources and tools. It is like the USB-C port for AI applications, providing a standardized way to connect AI models to external systems.

## 💻 Compatibility

- ✅ **WeChat version** - Fully supports WeChat 4.0 and above (NT framework) as well as legacy WeChat versions
- ✅ **Operating system** - Supports Windows 10/11
- ✅ **AI assistants** - Compatible with Claude, ChatGPT, and other AI assistants that support the MCP protocol

## ✨ Features

- ✅ **MCP standard compliant** - Fully conforms to the MCP specification
- ✅ **JSON-RPC 2.0** - Built on the standard JSON-RPC 2.0 protocol
- ✅ **WeChat message sending** - Supports sending WeChat text messages
- ✅ **Scheduled sending** - Supports sending messages on a delay
- ✅ **Comprehensive version support** - Fully supports WeChat 4.0 and above (NT framework) as well as legacy WeChat versions
- ✅ **Smart version detection** - Automatically detects the WeChat version and adapts its operation accordingly
- ✅ **Smart input box positioning** - Adapts to the input box position across different window sizes and layouts
- ✅ **Clipboard input technique** - Uses clipboard input to completely avoid input method (IME) state issues
- ✅ **Multiple send methods** - Supports Enter, Ctrl+Enter, Alt+S, and other send shortcuts
- ✅ **Asynchronous processing** - Runs asynchronously without blocking the AI assistant
- ✅ **Complete logging** - Full error handling and log recording
- ✅ **Partial text support** - Currently supports sending English, digits, emoji, and so on; Chinese messages are not yet supported (may cause garbled text)

## 📁 Project Structure

```
WeChat-MCP-Server/
├── 📂 src/
│   ├── 📄 __init__.py
│   ├── 📄 mcp_server.py          # Main MCP server implementation
│   └── 📄 wechat_controller.py   # WeChat automation controller
├── 📂 examples/
│   └── 📄 mcp_client_example.py  # Client usage example
├── 📂 docs/
│   └── 📄 QUICK_START.md         # Quick start guide
├── 📄 mcp_config.json           # MCP configuration file
├── 📄 requirements.txt          # Dependency list
├── 📄 LICENSE                   # License file
├── 📄 AGENTS.md                 # Guidance for AI assistants
├── 📄 README.md                 # Project documentation (Chinese)
└── 📄 README.en.md              # Project documentation (English)
```

## 🚀 Installation and Setup

### 1️⃣ Install Dependencies

```bash
# Clone the project
git clone https://github.com/hhuangpanda/WeChat-MCP-Server.git
cd WeChat-MCP-Server

# Install dependencies
pip install -r requirements.txt
```

### 2️⃣ Make Sure WeChat Is Running and Logged In

> ⚠️ **Important**
> 
> Before use, make sure that:
> - ✅ The WeChat client is installed and running
> - ✅ You are successfully logged in to your WeChat account
> - ✅ The WeChat window is visible (do not minimize it)




### 3️⃣ Configure Your AI Assistant

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

> **Note**: Replace `C:/path/to/WeChat-MCP-Server` with your actual project path

## 🛠️ Available Tools

### 📤 send_wechat_message

Send a text message to a specified WeChat contact or group.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `contact_name` | `string` | ✅ | Contact or group name |
| `message` | `string` | ✅ | Text message to send |

**Example:**
```json
{
  "name": "send_wechat_message",
  "arguments": {
    "contact_name": "文件传输助手",
    "message": "Hello from AI assistant!"
  }
}
```

### ⏰ schedule_wechat_message

Schedule a message to be sent after a specified delay.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `contact_name` | `string` | ✅ | Contact or group name |
| `message` | `string` | ✅ | Text message to send |
| `delay_seconds` | `number` | ✅ | Delay before sending, in seconds |

**Example:**
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

## 💡 Usage

### 🤖 Using It in an AI Assistant

Once configured, you can make requests directly to your AI assistant in natural language:

> 💬 **Example conversations**
> 
> - "Send Zhang San a WeChat message saying 'The meeting is postponed to 3 PM'"
> - "Remind me about the meeting in 10 minutes, and send it to the work group"
> - "Send today's work summary to File Transfer Assistant"

### 🧪 Direct Testing

Run the example client to test:

## 🔄 Automated Tasks and Message Reporting

### 🚀 Automated Workflows with Cloud Code

Imagine using automation tools such as Cloud Code to complete all kinds of tasks and automatically send report messages through WeChat:

#### 📊 Example Automation Scenarios

1. **Code deployment notifications**
   - When a CI/CD pipeline finishes, automatically send the deployment status to the development team group
   - Includes build results, test coverage, and deployment environment information

2. **Monitoring alert integration**
   - Push server monitoring alerts directly to the operations group
   - System load and abnormal states are notified to the responsible people in real time

3. **Data processing completion notifications**
   - Automatically notify data analysts when a large data processing task completes
   - Includes processing time, data volume, and a summary of results

4. **Scheduled report delivery**
   - Automatically generate daily/weekly business reports and send them to management
   - Key metrics such as sales data and user growth are summarized automatically

#### 💻 Implementation Example

```python
# Example: send a WeChat notification after GitHub Actions completes
import requests

def send_deployment_notification(status, details):
    # Call the WeChat MCP Server API
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "send_wechat_message",
            "arguments": {
                "contact_name": "技术团队群",
                "message": f"🚀 部署状态: {status}\n📋 详情: {details}"
            }
        }
    }
    
    response = requests.post("http://localhost:8080/mcp", json=payload)
    return response.json()

# Call from the CI/CD pipeline
if __name__ == "__main__":
    send_deployment_notification("成功", "版本v2.1.0已部署到生产环境")
```

```bash
cd examples
python mcp_client_example.py
```

## 🔧 MCP Protocol Implementation

This server implements the following standard MCP methods:

| Method | Description |
|--------|-------------|
| `initialize` | Initialize the server connection |
| `tools/list` | List available tools |
| `tools/call` | Call a specified tool |

### 📡 JSON-RPC Message Format

<details>
<summary>Click to view detailed message format examples</summary>

**Request example:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "send_wechat_message",
    "arguments": {
      "contact_name": "文件传输助手",
      "message": "Hello World!"
    }
  },
  "id": 1
}
```

**Response example:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "content": [
      {
        "type": "text",
        "text": "Successfully sent message to 文件传输助手: Hello World!"
      }
    ]
  },
  "id": 1
}
```

</details>

## 🏗️ Technical Architecture

### 🖥️ MCP Server (mcp_server.py)
- Implements the JSON-RPC 2.0 protocol
- Handles standard MCP method calls
- Manages tool registration and execution
- Provides complete error handling

### 📱 WeChat Controller (wechat_controller.py)
- Uses pyautogui for UI automation
- Uses win32gui to find and control the WeChat window
- **🆕 NT framework support**: Fully supports WeChat 4.0 and above
- **🔍 Smart version detection**: Automatically detects the WeChat version and adapts its operation
- **🎯 Multi-window-type recognition**: Supports the QT framework and legacy window types
- Supports asynchronous message sending and scheduling
- Provides status checking

#### 🔧 NT Framework Technical Features
- **Version detection**: Detects the WeChat version automatically from process information
- **Window recognition**: Supports pattern matching on QT framework window class names
- **Operation adaptation**: Search and send logic optimized for the NT framework
- **Compatibility**: Backward compatible with legacy WeChat versions (<4.0)

#### 🎯 Smart Input Technique
- **Smart positioning**: Adaptive detection of the input box position across window sizes
- **Clipboard input**: Uses the Windows clipboard API for text input, completely avoiding IME interference
- **Focus verification**: Verifies input box focus by typing a test character
- **Clipboard protection**: Automatically backs up and restores the user's original clipboard content
- **Multiple send fallbacks**: Supports Enter, Ctrl+Enter, Alt+S, and other send shortcuts as alternatives

## ⚠️ Notes

### 🖥️ System Requirements
- **Operating system**: Windows
- **WeChat version**: WeChat client (all versions supported, including 4.0 and above NT framework versions)
- **Python version**: Python 3.8+

### 🔐 Permission Requirements
- Requires screen control permission (pyautogui)

### 📝 Usage Limitations
> ⚠️ **Important**
> 
> - Do not operate the WeChat window manually while the tool is running
> - Make sure the WeChat window is visible and not obscured
> - It is recommended to test with "File Transfer Assistant" first

### 🛡️ Security Considerations
- This tool is intended only for automating personal WeChat operations
- Please comply with the WeChat terms of use
- It is not recommended for sending large volumes of messages

## 🔍 Troubleshooting

<details>
<summary>📋 Common problems and solutions</summary>

### ❌ WeChat Window Not Found
- ✅ Make sure WeChat is running and logged in
- ✅ Check that the WeChat window is visible
- ✅ Try restarting WeChat

### ❌ Message Sending Failed
- ✅ Check that the contact name is correct
- ✅ Make sure the contact is in the recent chats list
- ✅ Verify that the WeChat window is active

### ❌ Input Method Issues
- ✅ **Resolved**: This project uses clipboard input, which completely avoids input method state issues
- ✅ Supports Chinese, English, and emoji input under any input method state
- ✅ Automatically protects the user's clipboard content and restores it after use

### ❌ Input Box Positioning Failed
- ✅ **Optimized**: The smart input box positioning system adapts to different window sizes
- ✅ Supports multiple WeChat interface layouts and resolutions
- ✅ Automatically tries several possible input box positions

### ❌ MCP Connection Issues
- ✅ Check the Python environment and dependencies
- ✅ Verify the MCP configuration file path
- ✅ Check the server log output

</details>

### 📊 Log Debugging

The server outputs detailed log information, including:
- ✅ Request processing status
- ✅ WeChat operation results
- ✅ Error messages and stack traces

## 🚧 Development and Extension

### ➕ Adding New Tools

1. Add the tool definition in the `_register_tools()` method in `mcp_server.py`
2. Implement the corresponding execution method
3. Add the specific functionality in `wechat_controller.py`
4. Update the configuration file and documentation

### 🌐 Supporting Other Platforms

The current version supports Windows only. To support other platforms, you need to:
- Replace the win32gui-related code
- Adapt window management for different systems
- Adjust the keyboard shortcut mappings

### 🗺️ Roadmap

- [x] ~~Smart input box positioning~~ ✅ **Done**
- [x] ~~Clipboard input technique~~ ✅ **Done**
- [x] ~~Multiple send method support~~ ✅ **Done**
- [x] ~~Input method compatibility issues~~ ✅ **Done**
- [ ] Support macOS and Linux
- [ ] Add more WeChat operations (such as sending images and files)


## ⚠️ Important Disclaimer

> **🚨 Serious Warning**
> 
> This project involves WeChat automation and carries significant risks. Please assess the risks fully before use and bear all consequences yourself.

<details>
<summary>📋 Click to view the full disclaimer</summary>

### 🏷️ Nature of the Project
1. **Pure technical research**: This project is created only for technical research and learning purposes, to demonstrate an implementation of the MCP protocol
2. **Unofficial tool**: This project has no affiliation with Tencent or WeChat, and has not been authorized or endorsed by WeChat
3. **Experimental**: This project is experimental code, with no guarantee of stability, security, or reliability

### ⚠️ Usage Risk Warnings
1. **Account risk**: Using any WeChat automation tool may cause your account to be restricted, banned, or permanently closed
2. **Data risk**: May lead to loss of chat history, leakage of contact information, or other data security problems
3. **System risk**: May cause instability or security vulnerabilities in your computer system
4. **Legal risk**: In some regions or circumstances, using such tools may violate relevant laws and regulations
5. **Privacy risk**: May involve the processing and transmission of personal private information

### 📱 WeChat-Related Disclaimers
1. **Violation of terms of service**: Using this project may violate the WeChat user service agreement and terms of use
2. **Loss of functionality**: A WeChat update may render this project completely non-functional at any time
3. **Official sanctions**: Tencent has the right to take any action against accounts that use automation tools
4. **No official support**: WeChat will not provide technical support for any problems arising from the use of this project

### 🔴 Full Disclaimer of Liability

**Developers, contributors, and distributors bear no responsibility under any circumstances, including but not limited to:**

#### Disclaimer of Direct Liability
- WeChat account being banned, restricted, or closed
- Loss, leakage, or misuse of personal data
- Damage to the computer system or data corruption
- Message sending errors or failures
- Leakage of private information
- Financial or business losses

#### Disclaimer of Indirect Liability
- Any third-party losses caused by using this project
- Consequential losses caused by defects in the project
- Legal consequences arising from violations of laws and regulations
- Penalties arising from violations of platform rules
- Any form of emotional distress or reputational damage

#### Disclaimer of Legal Liability
- Liability for violating local laws and regulations
- Liability for violating the WeChat terms of service
- Liability for infringing the rights of others
- Liability for violating data protection regulations
- Any civil, criminal, or administrative liability

### 📋 Conditions of Use
**By using this project, you:**
1. Have fully understood and accepted all of the above risks and disclaimers
2. Agree to bear all risks and consequences of using this project yourself
3. Promise not to hold the developers responsible for any problems arising from the use of this project
4. Understand that the developers may stop maintaining the project at any time without any liability
5. Agree that the developers bear no responsibility in the event of any dispute

### ⛔ Prohibited Use
**Use of this project is strictly prohibited in the following cases:**
- Sending advertisements or spam in bulk
- Harassing others or malicious use
- Purposes that violate local laws and regulations
- Actions that infringe the rights of others
- Actions that violate the WeChat terms of service

### 💼 Commercial Use Warning
**Although the MIT license permits commercial use, we strongly recommend:**
- Fully assess the legal risks before commercial use
- Ensure compliance with the relevant laws and regulations in your region
- Comply with the WeChat platform's commercial use policies
- Consult a legal professional
- All risks arising from commercial use are borne by the user

**If you do not agree with any of the above terms, stop downloading, installing, or using this project immediately. Continued use is deemed full agreement with and acceptance of all disclaimers.**

</details>

---

## 📄 License

This project is released under the **MIT License**.

<details>
<summary>📋 License details</summary>

The MIT License allows:
- ✅ **Commercial use** (⚠️ assess the risks)
- ✅ Modifying the code
- ✅ Distributing the code
- ✅ Private use

But requires:
- 📋 Retaining the copyright notice
- 📋 Retaining the license notice

**Important reminder**: 
- ✅ The MIT License legally permits commercial use
- ⚠️ However, commercial use of WeChat automation tools carries high risk
- 🔍 Consult a legal professional before commercial use
- 📋 All risks of commercial use are borne by the user

</details>

## 🤝 Contributing

We welcome contributions of all kinds!

### 🐛 Reporting Issues
- Use [Issues](https://github.com/hhuangpanda/WeChat-MCP-Server/issues) to report bugs
- Provide detailed error messages and steps to reproduce

### 💡 Feature Suggestions
- Suggest new features in [Issues](https://github.com/hhuangpanda/WeChat-MCP-Server/issues)
- Describe the feature requirements and use cases in detail

### 🔧 Code Contributions
1. Fork this project
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Create a Pull Request

---

<div align="center">

**Thank you for using WeChat MCP Server!**

If this project helps you, please consider giving us a ⭐

[Back to top](#wechat-mcp-server)

</div>
