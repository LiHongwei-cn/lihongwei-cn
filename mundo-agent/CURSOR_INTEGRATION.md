# MUNDO Agent — Cursor MCP Integration Guide

## Quick Setup

### 1. Install MUNDO Agent

```bash
git clone https://github.com/LiHongwei-cn/lihongwei-cn.git
cd lihongwei-cn/mundo-agent
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Cursor

Add to your Cursor MCP settings (`.cursor/mcp.json` or global settings):

```json
{
  "mcpServers": {
    "mundo-agent": {
      "command": "python3",
      "args": ["/path/to/lihongwei-cn/mundo-agent/mcp_server.py"],
      "env": {
        "DEEPSEEK_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

### 3. Use MUNDO in Cursor

Once configured, you can use MUNDO's tools in Cursor:

- **Chat with MUNDO**: Ask questions, get code suggestions
- **Execute Tasks**: Let MUNDO plan and execute complex tasks
- **Memory System**: MUNDO remembers your preferences across sessions

## Available Tools

### `mundo_chat`
Chat with MUNDO Agent. Send a message and get a response with tool execution.

**Parameters:**
- `message` (required): The message to send to MUNDO
- `provider` (optional): LLM provider (default: deepseek)

**Example:**
```json
{
  "message": "Write a Python function to calculate fibonacci numbers"
}
```

### `mundo_execute`
Execute a task with MUNDO. MUNDO will plan, execute, and report results.

**Parameters:**
- `task` (required): The task to execute
- `timeout` (optional): Timeout in seconds (default: 90)

**Example:**
```json
{
  "task": "Create a REST API with FastAPI that has user authentication",
  "timeout": 120
}
```

### `mundo_remember`
Store a fact in MUNDO's memory.

**Parameters:**
- `key` (required): The key to store the fact under
- `value` (required): The fact to remember

**Example:**
```json
{
  "key": "coding_style",
  "value": "Prefer functional programming over OOP"
}
```

### `mundo_recall`
Retrieve a fact from MUNDO's memory.

**Parameters:**
- `key` (required): The key to retrieve

**Example:**
```json
{
  "key": "coding_style"
}
```

### `mundo_status`
Get MUNDO's current status and memory statistics.

**Parameters:** None

## Usage Examples

### Code Generation
```
User: Write a Python function to sort a list of dictionaries by a specific key
MUNDO: [Generates optimized code with error handling]
```

### Task Execution
```
User: Create a CLI tool that converts CSV to JSON
MUNDO: [Plans the task, creates the tool, tests it, reports results]
```

### Memory System
```
User: Remember that I prefer TypeScript over JavaScript
MUNDO: [Stores preference in memory]

User: What's my language preference?
MUNDO: [Recalls from memory: TypeScript over JavaScript]
```

## Troubleshooting

### MUNDO not responding
1. Check if the MCP server is running
2. Verify API keys are set correctly
3. Check Cursor's MCP logs for errors

### Slow responses
MUNDO's response time depends on:
- Task complexity
- LLM provider latency
- Number of tool calls required

Typical response times:
- Simple questions: 2-5 seconds
- Code generation: 3-10 seconds
- Complex tasks: 30-90 seconds

### Memory not persisting
MUNDO stores memory in `~/.hermes/mundo-agent/memory.db`. Ensure:
- The directory is writable
- The virtual environment is activated

## Advanced Configuration

### Custom Provider
```json
{
  "mcpServers": {
    "mundo-agent": {
      "command": "python3",
      "args": ["/path/to/mcp_server.py"],
      "env": {
        "OPENAI_API_KEY": "your_openai_key",
        "ANTHROPIC_API_KEY": "your_anthropic_key"
      }
    }
  }
}
```

### Multiple Instances
You can run multiple MUNDO instances with different configurations:
```json
{
  "mcpServers": {
    "mundo-code": {
      "command": "python3",
      "args": ["/path/to/mcp_server.py"],
      "env": {"DEEPSEEK_API_KEY": "key1"}
    },
    "mundo-research": {
      "command": "python3",
      "args": ["/path/to/mcp_server.py"],
      "env": {"OPENAI_API_KEY": "key2"}
    }
  }
}
```

## Links

- **GitHub**: https://github.com/LiHongwei-cn/lihongwei-cn
- **Documentation**: https://github.com/LiHongwei-cn/lihongwei-cn/blob/main/mundo-agent/README.md
- **Issues**: https://github.com/LiHongwei-cn/lihongwei-cn/issues
