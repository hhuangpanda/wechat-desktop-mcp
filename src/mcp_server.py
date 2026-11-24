#!/usr/bin/env python3
"""
微信 MCP 服务器
用于发送微信消息的模型上下文协议服务器。
"""

import asyncio
import json
import sys
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
import logging
import io

if __package__:
    from .wechat_controller import WeChatController
else:
    from wechat_controller import WeChatController

try:
    from importlib.metadata import PackageNotFoundError, version as _package_version
    __version__ = _package_version("wechat-desktop-mcp")
except PackageNotFoundError:
    __version__ = "0.0.0"

# 设置标准输出编码为UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')

# MCP 协议类型
class JSONRPCRequest:
    def __init__(self, method: str, params: Optional[Dict[str, Any]] = None, id: Optional[Union[str, int]] = None):
        self.jsonrpc = "2.0"
        self.method = method
        self.params = params or {}
        self.id = id

class JSONRPCResponse:
    def __init__(self, result: Optional[Any] = None, error: Optional[Dict[str, Any]] = None, id: Optional[Union[str, int]] = None):
        self.jsonrpc = "2.0"
        self.result = result
        self.error = error
        self.id = id
    
    def to_dict(self) -> Dict[str, Any]:
        response = {"jsonrpc": self.jsonrpc}
        if self.result is not None:
            response["result"] = self.result
        if self.error is not None:
            response["error"] = self.error
        if self.id is not None:
            response["id"] = self.id
        return response

class MCPServer:
    """微信消息传递的 MCP 服务器实现。"""
    
    def __init__(self):
        self.name = "wechat-desktop-mcp"
        self.version = __version__
        self.initialized = False
        self.capabilities = {
            "tools": {}
        }
        self.tools = []
        self._setup_logging()
        self._register_tools()
    
    def _setup_logging(self):
        """设置日志配置。"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(self.name)
    
    def _register_tools(self):
        """注册可用的 MCP 工具。"""
        self.tools = [
            {
                "name": "send_wechat_message",
                "description": "向微信联系人或群组发送文本消息",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "contact_name": {
                            "type": "string",
                            "description": "要发送消息的微信联系人或群组名称"
                        },
                        "message": {
                            "type": "string",
                            "description": "要发送的文本消息内容"
                        }
                    },
                    "required": ["contact_name", "message"]
                }
            },
            {
                "name": "schedule_wechat_message",
                "description": "安排在延迟后发送微信消息",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "contact_name": {
                            "type": "string",
                            "description": "要发送消息的微信联系人或群组名称"
                        },
                        "message": {
                            "type": "string",
                            "description": "要发送的文本消息内容"
                        },
                        "delay_seconds": {
                            "type": "number",
                            "description": "发送消息前的延迟秒数"
                        }
                    },
                    "required": ["contact_name", "message", "delay_seconds"]
                }
            },
            {
                "name": "show_scheduled_wechat_messages",
                "description": "显示待发送的定时微信消息和最近 20 条已触发消息的发送结果。仅包含本服务器进程安排的消息，进程退出后清空，因此空列表不代表其他进程没有定时消息",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            }
        ]
    
    async def handle_request(self, request_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """处理传入的 JSON-RPC 请求。"""
        try:
            method = request_data.get("method")
            params = request_data.get("params", {})
            request_id = request_data.get("id")
            
            self.logger.info(f"处理请求: {method}")

            if "id" not in request_data:
                return None
            if method == "ping":
                return JSONRPCResponse(result={}, id=request_id).to_dict()
            if method == "initialize":
                return await self._handle_initialize(params, request_id)
            elif method == "tools/list":
                return await self._handle_tools_list(request_id)
            elif method == "tools/call":
                return await self._handle_tools_call(params, request_id)
            else:
                error = {
                    "code": -32601,
                    "message": f"方法未找到: {method}"
                }
                return JSONRPCResponse(error=error, id=request_id).to_dict()
                
        except Exception as e:
            self.logger.error(f"Error handling request: {e}")
            error = {
                "code": -32603,
                "message": f"Internal error: {str(e)}"
            }
            return JSONRPCResponse(error=error, id=request_data.get("id")).to_dict()
    
    async def _handle_initialize(self, params: Dict[str, Any], request_id: Optional[Union[str, int]]) -> Dict[str, Any]:
        """处理 MCP 初始化请求。"""
        self.initialized = True
        
        result = {
            "protocolVersion": "2024-11-05",
            "capabilities": self.capabilities,
            "serverInfo": {
                "name": self.name,
                "version": self.version
            }
        }
        
        self.logger.info("Server initialized successfully")
        return JSONRPCResponse(result=result, id=request_id).to_dict()
    
    async def _handle_tools_list(self, request_id: Optional[Union[str, int]]) -> Dict[str, Any]:
        """处理 tools/list 请求。"""
        if not self.initialized:
            error = {
                "code": -32002,
                "message": "Server not initialized"
            }
            return JSONRPCResponse(error=error, id=request_id).to_dict()
        
        result = {"tools": self.tools}
        return JSONRPCResponse(result=result, id=request_id).to_dict()
    
    async def _handle_tools_call(self, params: Dict[str, Any], request_id: Optional[Union[str, int]]) -> Dict[str, Any]:
        """处理 tools/call 请求。"""
        if not self.initialized:
            error = {
                "code": -32002,
                "message": "Server not initialized"
            }
            return JSONRPCResponse(error=error, id=request_id).to_dict()
        
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if tool_name == "send_wechat_message":
            return await self._execute_send_message(arguments, request_id)
        elif tool_name == "schedule_wechat_message":
            return await self._execute_schedule_message(arguments, request_id)
        elif tool_name == "show_scheduled_wechat_messages":
            return await self._execute_show_scheduled(request_id)
        else:
            error = {
                "code": -32601,
                "message": f"Unknown tool: {tool_name}"
            }
            return JSONRPCResponse(error=error, id=request_id).to_dict()
    
    @staticmethod
    def _format_send_result(send_result: Union[bool, Dict[str, Any]]) -> str:
        """将发送结果转换为工具返回的文本。"""
        success = send_result if isinstance(send_result, bool) else bool(send_result.get("ok"))
        if success:
            if isinstance(send_result, dict) and send_result.get("verified"):
                retries = send_result.get("retry_used")
                suffix = f" (retried: {', '.join(retries)})" if retries else ""
                return f"Message sent and verified in chat '{send_result.get('chat_name')}'{suffix}"
            return "Message sent via keyboard fallback; delivery could not be verified"
        if isinstance(send_result, dict):
            stage = send_result.get("stage")
            reason = send_result.get("reason")
            version = send_result.get("wechat_version")
            is_nt = send_result.get("is_nt_framework")
            retries = send_result.get("retry_used")
            return f"Failed to send message (stage={stage}, reason={reason}, retries={retries}, wechat_version={version}, nt={is_nt})"
        return "Failed to send message"

    async def _execute_send_message(self, arguments: Dict[str, Any], request_id: Optional[Union[str, int]]) -> Dict[str, Any]:
        """执行 send_wechat_message 工具。"""
        try:
            contact_name = arguments.get("contact_name")
            message = arguments.get("message")
            
            if not contact_name or not message:
                error = {
                    "code": -32602,
                    "message": "Missing required parameters: contact_name and message"
                }
                return JSONRPCResponse(error=error, id=request_id).to_dict()
            
            controller = WeChatController()
            send_result = await controller.send_text_message(contact_name, message)

            result = {
                "content": [
                    {
                        "type": "text",
                        "text": self._format_send_result(send_result)
                    }
                ],
                "isError": not send_result.get("ok")
            }

            return JSONRPCResponse(result=result, id=request_id).to_dict()

        except Exception as e:
            self.logger.error(f"Error executing send_message: {e}")
            error = {
                "code": -32603,
                "message": f"Tool execution error: {str(e)}"
            }
            return JSONRPCResponse(error=error, id=request_id).to_dict()
    
    async def _execute_schedule_message(self, arguments: Dict[str, Any], request_id: Optional[Union[str, int]]) -> Dict[str, Any]:
        """执行 schedule_wechat_message 工具。"""
        try:
            contact_name = arguments.get("contact_name")
            message = arguments.get("message")
            delay_seconds = arguments.get("delay_seconds")
            
            if not contact_name or not message or delay_seconds is None:
                error = {
                    "code": -32602,
                    "message": "Missing required parameters: contact_name, message and delay_seconds"
                }
                return JSONRPCResponse(error=error, id=request_id).to_dict()
            
            controller = WeChatController()
            success = await controller.schedule_message(contact_name, message, delay_seconds)
            
            if success:
                send_at = datetime.now().astimezone() + timedelta(seconds=delay_seconds)
                text = f"Message scheduled for {send_at:%Y-%m-%d %H:%M:%S} (in {delay_seconds:g} seconds)."
                issue = controller.availability_issue()
                if issue:
                    text += f" Warning ({issue}): WeChat must be open, not in the tray, by then or the send will fail."
                result = {
                    "content": [
                        {
                            "type": "text",
                            "text": text
                        }
                    ]
                }
            else:
                result = {
                    "content": [
                        {
                            "type": "text",
                            "text": "Failed to schedule message"
                        }
                    ]
                }
            
            return JSONRPCResponse(result=result, id=request_id).to_dict()
            
        except Exception as e:
            self.logger.error(f"Error executing schedule_message: {e}")
            error = {
                "code": -32603,
                "message": f"Tool execution error: {str(e)}"
            }
            return JSONRPCResponse(error=error, id=request_id).to_dict()

    async def _execute_show_scheduled(self, request_id: Optional[Union[str, int]]) -> Dict[str, Any]:
        """执行 show_scheduled_wechat_messages 工具。"""
        try:
            scheduled = WeChatController.list_scheduled()
            now = datetime.now().astimezone()
            payload = {
                "pending": [
                    {
                        "contact_name": entry["contact_name"],
                        "message": entry["message"],
                        "scheduled_for": entry["scheduled_for"].isoformat(timespec="seconds"),
                        "seconds_remaining": max(0, round((entry["scheduled_for"] - now).total_seconds()))
                    }
                    for entry in scheduled["pending"]
                ],
                "recent": [
                    {
                        "contact_name": entry["contact_name"],
                        "message": entry["message"],
                        "scheduled_for": entry["scheduled_for"].isoformat(timespec="seconds"),
                        "result": self._format_send_result(entry["send_result"])
                    }
                    for entry in scheduled["recent"]
                ]
            }

            result = {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(payload, ensure_ascii=False)
                    }
                ]
            }

            return JSONRPCResponse(result=result, id=request_id).to_dict()

        except Exception as e:
            self.logger.error(f"Error executing show_scheduled: {e}")
            error = {
                "code": -32603,
                "message": f"Tool execution error: {str(e)}"
            }
            return JSONRPCResponse(error=error, id=request_id).to_dict()

async def main():
    """MCP 服务器的主入口点。"""
    server = MCPServer()
    
    # 从标准输入读取并写入标准输出进行 MCP 通信
    while True:
        try:
            line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
            if not line:
                break
                
            request_data = json.loads(line.strip())
            response = await server.handle_request(request_data)
            if response is None:
                continue

            print(json.dumps(response, ensure_ascii=False, separators=(',', ':')))
            sys.stdout.flush()
            
        except json.JSONDecodeError as e:
            error_response = JSONRPCResponse(
                error={"code": -32700, "message": f"解析错误: {str(e)}"}
            ).to_dict()
            print(json.dumps(error_response, ensure_ascii=False, separators=(',', ':')))
            sys.stdout.flush()
        except Exception as e:
            server.logger.error(f"意外错误: {e}")
            break

def run():
    asyncio.run(main())


if __name__ == "__main__":
    run()
