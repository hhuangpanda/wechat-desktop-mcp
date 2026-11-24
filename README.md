# WeChat Desktop MCP Server

<div align="center">

[![PyPI](https://img.shields.io/pypi/v/wechat-desktop-mcp)](https://pypi.org/project/wechat-desktop-mcp/)
![Python version](https://img.shields.io/badge/python-3.9%2B-blue)
![Platform](https://img.shields.io/badge/platform-Windows-0078D6)
[![Tests](https://github.com/hhuangpanda/wechat-desktop-mcp/actions/workflows/tests.yml/badge.svg)](https://github.com/hhuangpanda/wechat-desktop-mcp/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

**通过 Windows 桌面版微信在后台发送消息的 MCP 服务器**

**简体中文** | [English](README.en.md)

</div>

---

让 AI 助手通过电脑上的微信桌面客户端，立即或定时替你发送微信消息，且不占用你的鼠标和键盘。仅支持 Windows 10/11 和微信 4.0 及以上版本。适用于任何能运行 stdio 服务器的 MCP 客户端，例如 Claude Desktop、Claude Code、Cursor、opencode、DeepSeek Harness 或 ChatGPT 应用中的 Codex。

例如：*"给文件传输助手发一条'马上到'"*，或 *"30 分钟后提醒家庭群吃饭"*。

<!-- mcp-name: io.github.hhuangpanda/wechat-desktop-mcp -->

## 安装和配置

需要已启动并登录的微信桌面客户端。窗口可以最小化或被遮挡，但不能关闭到系统托盘。

安装 [uv](https://docs.astral.sh/uv/getting-started/installation/)，然后将服务器添加到客户端的 MCP 配置中（Claude Desktop：`%APPDATA%\Claude\claude_desktop_config.json`）：

```json
{
  "mcpServers": {
    "wechat": {
      "command": "uvx",
      "args": ["wechat-desktop-mcp"]
    }
  }
}
```

Claude Code：

```bash
claude mcp add wechat -- uvx wechat-desktop-mcp
```

opencode：

```bash
opencode mcp add wechat --global -- uvx wechat-desktop-mcp
```

DeepSeek Harness（dsh）：在智能体预设中添加以下条目：

```yaml
- id: mcp-wechat
  name: '@deepseek-ai/dsh-mcp-client'
  config:
    serverName: wechat
    transport: stdio
    command: uvx
    args: ['wechat-desktop-mcp']
```

不使用 uv 时，安装 Python 3.9+，运行 `pip install wechat-desktop-mcp`，并使用 `"command": "wechat-desktop-mcp"`（不需要 `args`）。

### 从源码运行

```bash
git clone https://github.com/hhuangpanda/wechat-desktop-mcp.git
cd wechat-desktop-mcp
pip install -e .
```

然后同样使用 `"command": "wechat-desktop-mcp"`。

## 工具

### send_wechat_message

| 参数名 | 类型 | 描述 |
|--------|------|------|
| `contact_name` | `string` | 联系人或群组名称 |
| `message` | `string` | 要发送的文本 |

如果聊天列表中能看到该聊天，就直接从列表打开，否则通过微信搜索打开。搜索时优先选择名称完全一致的结果，没有则选第一个结果，因此 `文件传输` 这样的部分名称可以打开文件传输助手，但含糊的名称可能发到错误的聊天。

成功时返回 `Message sent and verified in chat '<聊天名称>'`，如有步骤经过重试，后面附加 `(retried: ...)`。失败时结果带有 `isError: true`，文本类似 `Failed to send message (stage=open_chat, reason=contact_not_found_or_chat_not_opened, ...)`，其中 `stage` 为 `find_window`、`version_check`、`open_chat`、`set_text`、`click_send`、`verify` 之一。

### schedule_wechat_message

参数与 `send_wechat_message` 相同，另加 `delay_seconds`（`number`）。

返回 `Message scheduled for <本地时间> (in <n> seconds).`。如果此时微信没有运行或在托盘中，会附加 `Warning (wechat_not_running)` 或 `Warning (wechat_window_not_found)`；消息仍会保留，但发送时微信必须已打开。

### show_scheduled_wechat_messages

无参数。返回待发送的消息和最近 20 条已触发消息的结果。只包含本服务器进程安排的消息，进程退出后清空。

```json
{
  "pending": [{"contact_name": "文件传输", "message": "...", "scheduled_for": "2026-11-01T15:00:00-05:00", "seconds_remaining": 30}],
  "recent": [{"contact_name": "文件传输", "message": "...", "scheduled_for": "2026-11-01T14:30:00-05:00", "result": "Message sent and verified in chat '文件传输助手'"}]
}
```

## 后台行为

- 点击和输入以窗口消息的形式发给微信，发送期间不会动用鼠标、键盘或其他窗口。
- 从列表选择聊天或关闭搜索时，微信自身会请求切换到前台。Windows 通常会拒绝，改为闪烁微信的任务栏按钮；如果允许，焦点会立即交还给你的窗口。
- 包含表情符号或换行的消息通过粘贴输入，之后恢复剪贴板，且消息不进入剪贴板历史记录。如果剪贴板中的内容无法完整恢复（例如复制的文件），则改为逐字输入。
- 先清空收件人聊天中未发送的草稿。如果微信已最小化，发送期间会显示窗口（不抢占焦点），完成后重新最小化。
- 发送期间如果你自己点击微信窗口，可能会打断发送；此时工具会报告失败，而不会发送错误的文本。
- 对于没有无障碍树的微信版本，回退到键盘输入，该模式需要前台窗口，且无法确认是否送达。

## 测试

`tests/test_server.py`、`tests/test_show_scheduled.py`、`tests/test_stdio.py` 和 `tests/test_detection.py` 不发送任何消息。以下命令会向文件传输助手发送真实消息：

```bash
python tests/test_send_chinese.py
python examples/mcp_client_example.py
python tests/e2e_interference.py
```

端到端测试会在微信上方打开一个自己的窗口，在发送消息的同时向该窗口发送真实的鼠标点击和按键，以检查微信从未切换到前台、按键没有丢失。测试会移动你的鼠标指针，运行期间请勿使用鼠标和键盘。

## 故障排除

- **`stage=find_window`**：`reason=wechat_not_running` 表示微信没有运行；`wechat_window_not_found` 表示微信在运行但没有窗口，通常是因为关闭到了托盘。
- **`stage=version_check`**：微信版本低于 4.0，请更新。
- **发送失败**：`stage` 指出失败的步骤。`open_chat` 通常表示名称没有匹配到聊天，请按微信中显示的名称检查。
- **客户端无法连接**：确认客户端的 PATH 中能找到 `uvx`（或 `wechat-desktop-mcp`）；服务器日志输出到 stderr。

## 免责声明

本项目与腾讯公司、微信官方无任何关联。自动化操作微信可能违反其服务条款，导致账号被限制或封禁，微信更新也可能随时使本项目失效。请勿用于批量发送、垃圾消息或骚扰他人。使用风险自负。

## 致谢

基于 [1052666/WeChat-MCP-Server](https://github.com/1052666/WeChat-MCP-Server)，在此基础上改为后台发送并确认送达。

## 许可证

[MIT](LICENSE)。欢迎通过 [Issues](https://github.com/hhuangpanda/wechat-desktop-mcp/issues) 报告问题或提交 Pull Request。
