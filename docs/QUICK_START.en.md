# Quick Start Guide

[简体中文](QUICK_START.md) | **English**

## Deploy the WeChat MCP Server in 5 Minutes

### Step 1: Prepare the Environment

1. **Make sure Python is installed**
   ```bash
   python --version  # Requires Python 3.8+
   ```

2. **Install dependencies**
   ```bash
   cd WeChat-MCP-Server
   pip install -r requirements.txt
   ```

3. **Start WeChat and log in**
   - Open the WeChat client
   - Make sure you are logged in
   - Keep the WeChat window visible

### Step 2: Test the MCP Server

Run the test script to verify it works:

```bash
cd examples
python mcp_client_example.py
```

If you see output similar to the following, the server is working:
```
MCP Server started
Initialize response: {'jsonrpc': '2.0', 'result': {...}, 'id': 1}
Tools list: {'jsonrpc': '2.0', 'result': {'tools': [...]}, 'id': 2}
```

### Step 3: Configure Your AI Assistant

#### For Claude Desktop:

1. Open the Claude Desktop configuration file:
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`

2. Add the MCP server configuration:
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

3. Restart Claude Desktop

#### For other AI assistants:

Refer to their MCP configuration documentation and use the same server path and arguments.

### Step 4: Start Using It

Try the following commands in your AI assistant:

1. **Send a simple message**
   ```
   "Send a message to File Transfer Assistant: Hello from AI!"
   ```

2. **Send a scheduled message**
   ```
   "In 10 seconds, send File Transfer Assistant the message: This is a scheduled message"
   ```

3. **Send to a specific contact**
   ```
   "Send Zhang San a WeChat message: Tomorrow's meeting is moved to 3 PM"
   ```

### Quick Fixes for Common Problems

#### Problem 1: WeChat window not found
**Solution:**
- Make sure WeChat is running
- Check that the WeChat window is visible
- Try clicking the WeChat window to give it focus

#### Problem 2: Contact not found
**Solution:**
- Make sure the contact name is exactly correct
- Search for the contact manually once first
- Test with "File Transfer Assistant"

#### Problem 3: MCP connection failed
**Solution:**
- Check that the Python path is correct
- Verify that all dependencies are installed
- Check the AI assistant's error logs

### Advanced Configuration

#### Custom shortcuts
If WeChat uses different shortcuts, you can change the shortcut settings in `wechat_controller.py`.

#### Adjusting the log level
Change the log level in `mcp_server.py`:
```python
logging.basicConfig(level=logging.DEBUG)  # More detailed logs
```

#### Adding more contacts
It is recommended to pin frequently used contacts in WeChat, so that searching is faster and more accurate.

### Next Steps

- Read the full [README.en.md](../README.en.md) to learn about more features

### Getting Help

If you run into problems:
1. Check the log output
2. Review the FAQ
3. Submit an Issue to the project repository
