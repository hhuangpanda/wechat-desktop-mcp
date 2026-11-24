#!/usr/bin/env python3
"""
MCP 客户端示例
演示如何与微信 MCP 服务器交互。
用法：python examples/mcp_client_example.py [联系人]（默认依次尝试 文件传输助手 和 File）
"""

import asyncio
import json
import os
import subprocess
import sys
from typing import Dict, Any, Optional


class MCPClient:
    """用于测试微信 MCP 服务器的简单 MCP 客户端。"""
    
    def __init__(self, server_path: str):
        self.server_path = server_path
        self.process = None
        self.request_id = 0
    
    async def start_server(self):
        """启动 MCP 服务器进程。"""
        self.process = await asyncio.create_subprocess_exec(
            sys.executable, self.server_path,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        print("MCP Server started")
    
    async def send_request(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """向服务器发送 JSON-RPC 请求。"""
        self.request_id += 1
        request = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
            "id": self.request_id
        }
        
        request_json = json.dumps(request) + "\n"
        self.process.stdin.write(request_json.encode())
        await self.process.stdin.drain()
        
        # 读取响应
        response_line = await self.process.stdout.readline()
        response = json.loads(response_line.decode().strip())
        
        return response
    
    async def initialize(self):
        """初始化 MCP 服务器。"""
        params = {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "wechat-mcp-client",
                "version": "1.0.0"
            }
        }
        
        response = await self.send_request("initialize", params)
        print(f"Initialize response: {response}")
        return response
    
    async def list_tools(self):
        """列出可用工具。"""
        response = await self.send_request("tools/list")
        print(f"Tools list: {response}")
        return response
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]):
        """调用特定工具。"""
        params = {
            "name": tool_name,
            "arguments": arguments
        }
        
        response = await self.send_request("tools/call", params)
        print(f"Tool call response: {response}")
        return response
    
    async def close(self):
        """关闭客户端并终止服务器。"""
        if self.process:
            self.process.terminate()
            await self.process.wait()


async def main():
    """主示例函数。"""
    # MCP 服务器路径
    server_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "mcp_server.py")
    # File Transfer is 文件传输助手 in Chinese clients; "File" is only tried after that chat wasn't found,
    # since in a Chinese client a search for "File" can open another chat
    contacts = sys.argv[1:2] or ["文件传输助手", "File"]
    
    client = MCPClient(server_path)
    
    try:
        # 启动服务器
        await client.start_server()
        
        # 初始化连接
        await client.initialize()
        
        # 列出可用工具
        await client.list_tools()
        
        # 示例 1：发送简单消息
        print("\n=== Example 1: Send Message ===")
        for contact in contacts:
            response = await client.call_tool("send_wechat_message", {
                "contact_name": contact,
                "message": "Hello from MCP! This is a test message."
            })
            if "stage=open_chat" not in json.dumps(response):
                break
        
        # 示例 2：安排消息
        print("\n=== Example 2: Schedule Message ===")
        await client.call_tool("schedule_wechat_message", {
            "contact_name": contact,
            "message": "This is a scheduled message sent 5 seconds later!",
            "delay_seconds": 5
        })
        
        # 等待一段时间查看安排的消息
        print("Waiting for scheduled message...")
        await asyncio.sleep(6)
        await client.call_tool("show_scheduled_wechat_messages", {})
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())