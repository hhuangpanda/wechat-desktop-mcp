"""
微信 MCP 服务器包
用于微信消息自动化的模型上下文协议服务器。
"""

from .mcp_server import MCPServer, __version__
from .wechat_controller import WeChatController

__all__ = ["MCPServer", "WeChatController", "__version__"]
