# WeChat MCP Server

<div align="center">

![Python version](https://img.shields.io/badge/python-3.8%2B-blue)

**一个符合 Model Context Protocol (MCP) 标准的微信消息发送服务器，专为AI助手设计**

**简体中文** | [English](README.en.md)

</div>

---

## 什么是 MCP？

**Model Context Protocol (MCP)** 是一个开放标准协议，用于连接AI助手与各种数据源和工具。它就像AI应用的USB-C接口，提供了标准化的方式来连接AI模型与外部系统。

**兼容性：** 支持 Windows 10/11，支持微信4.0以上的NT框架版本和传统版本，兼容 Claude、ChatGPT 等支持MCP的AI助手。

## 功能特点

- 符合 MCP 标准，基于 JSON-RPC 2.0
- 发送微信文本消息（支持中文、英文、数字、表情符号）和定时发送
- 自动检测微信版本，适配4.0以上的NT框架版本和传统版本
- 智能输入框定位，适配不同窗口大小和布局
- 剪贴板输入，避免输入法干扰，并自动备份和恢复用户剪贴板
- 支持 Enter、Ctrl+Enter、Alt+S 等多种发送快捷键
- 异步处理，不阻塞AI助手；完整的错误处理和日志

## 项目结构

```
WeChat-MCP-Server/
├── src/               # MCP服务器和微信控制器
├── tests/             # 测试脚本
├── examples/          # 客户端使用示例
├── docs/              # 快速开始指南（中英文）
├── mcp_config.json    # MCP配置文件
└── requirements.txt   # 依赖包列表
```

## 安装和配置

### 1. 安装依赖

```bash
git clone https://github.com/hhuangpanda/WeChat-MCP-Server.git
cd WeChat-MCP-Server
pip install -r requirements.txt
```

### 2. 确保微信已启动并登录

使用前请确保微信客户端正在运行、已登录，且窗口可见（不要最小化）。

### 3. 配置AI助手

将此MCP服务器添加到您的AI助手配置中。以 **Claude Desktop** 为例：

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

请将 `C:/path/to/WeChat-MCP-Server` 替换为您实际的项目路径。

## 可用工具

### send_wechat_message

发送文本消息到指定的微信联系人或群组。

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| `contact_name` | `string` | ✅ | 联系人或群组名称 |
| `message` | `string` | ✅ | 要发送的文本消息 |

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

安排在指定延迟后发送消息。

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| `contact_name` | `string` | ✅ | 联系人或群组名称 |
| `message` | `string` | ✅ | 要发送的文本消息 |
| `delay_seconds` | `number` | ✅ | 延迟发送的秒数 |

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

显示待发送的定时消息（`pending`）和最近 20 条已触发消息的发送结果（`recent`）。无参数。`result` 与 `send_wechat_message` 的返回文本相同。

列表保存在内存中，仅包含本服务器进程安排的消息，进程退出后清空。

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
      "result": "Message sent successfully"
    }
  ]
}
```

## 使用方法

配置完成后，可以直接在AI助手中使用自然语言请求：

- "帮我给张三发个微信消息说'会议推迟到下午3点'"
- "10分钟后提醒我开会，发到工作群"
- "给文件传输助手发送今天的工作总结"

直接测试：

```bash
python tests/test_server.py
cd examples && python mcp_client_example.py
```

## MCP协议实现

服务器实现了以下标准方法：`initialize`（初始化连接）、`tools/list`（列出工具）、`tools/call`（调用工具）。

## 技术架构

- **mcp_server.py**：实现 JSON-RPC 2.0，处理MCP方法调用，管理工具注册和执行
- **wechat_controller.py**：使用 pyautogui 和 win32gui 控制微信窗口，自动检测微信版本（NT框架或传统版本），通过剪贴板输入文本，支持异步发送和调度

## 注意事项

- 需要 Windows 系统、微信客户端和 Python 3.8+
- 需要屏幕控制权限（pyautogui）
- 使用期间请勿手动操作微信窗口，并确保窗口可见且未被遮挡
- 建议先向"文件传输助手"测试
- 仅用于自动化个人微信操作，请遵守微信使用条款，不建议用于大量消息发送

## 故障排除

- **找不到微信窗口**：确认微信已启动并登录、窗口可见，必要时重启微信
- **消息发送失败**：确认联系人名称正确且在最近聊天列表中，微信窗口处于活动状态
- **输入框定位失败**：保持微信窗口完整可见，不要被遮挡
- **MCP连接失败**：检查Python环境、依赖包和配置文件路径，查看服务器日志

## 开发和扩展

添加新工具：

1. 在 `mcp_server.py` 的 `_register_tools()` 中添加工具定义
2. 实现对应的执行方法
3. 在 `wechat_controller.py` 中添加具体功能
4. 更新配置文件和文档

当前仅支持Windows。支持其他平台需要替换 win32gui 相关代码、适配窗口管理并调整快捷键映射。

后续计划：

- [ ] 支持macOS和Linux系统
- [ ] 增加更多微信操作功能（如发送图片、文件等）

## 重要免责声明

本项目涉及微信自动化操作，存在风险。使用前请自行评估，并承担全部后果。

- 本项目仅用于技术研究和学习，与腾讯公司、微信官方无任何关联，未经官方授权或认可
- 使用微信自动化工具可能违反微信服务条款，导致账号被限制、封禁或注销
- 可能造成消息发送错误、数据丢失或泄露等问题，微信更新也可能使本项目失效
- 严禁用于批量发送广告、骚扰他人或违反法律法规的用途
- 商业使用前请自行评估法律风险
- 开发者、贡献者和分发者不对使用本项目产生的任何后果承担责任。继续使用即表示您接受以上条款

## 许可证

本项目采用 **MIT License**，允许商业使用、修改、分发和私人使用，但需保留版权声明和许可证声明。MIT许可证在法律上允许商业使用，但商业使用微信自动化工具风险较高，风险由使用者自行承担。

## 贡献

欢迎提交 [Issues](https://github.com/hhuangpanda/WeChat-MCP-Server/issues) 报告bug或提出功能建议，请附上详细的错误信息和复现步骤。

代码贡献：Fork 本项目，创建功能分支，提交更改，然后创建 Pull Request。
