# AG-UI Middleware Pipe for OpenWebUI

This OpenWebUI pipe acts as a **middleware** that transforms standard OpenWebUI requests into AG-UI protocol format, forwards them to AG-UI compatible endpoints, and transforms the responses back to OpenWebUI format.

## Architecture

```
OpenWebUI Client → OpenWebUI Pipe → AG-UI Endpoint → OpenWebUI Pipe → OpenWebUI Client
```

**Flow:**
1. User sends request from OpenWebUI
2. Pipe transforms OpenWebUI request to AG-UI `RunAgentInput` format
3. Pipe forwards request to AG-UI compatible endpoint  
4. Pipe receives AG-UI event stream response
5. Pipe transforms AG-UI events back to OpenWebUI text format
6. User sees response in OpenWebUI

## Features

- **Protocol Translation**: Converts OpenWebUI requests to AG-UI `RunAgentInput` format with all required fields
- **Event Stream Processing**: Handles AG-UI event streams and converts them to OpenWebUI text chunks
- **Configurable Endpoint**: Easy configuration of target AG-UI endpoint URL
- **Error Handling**: Comprehensive error handling and logging
- **Model Pass-through**: Forwards model selection to AG-UI endpoint

### Valve Configuration

The pipe exposes these configuration options in OpenWebUI:

- **AG_UI_ENDPOINT_URL**: URL of your AG-UI compatible endpoint (default: `http://host.docker.internal:8000`)
- **THREAD_ID_PREFIX**: Prefix for generated thread IDs (default: `openwebui`)
- **DEFAULT_MODEL**: Default model ID to request (default: `agui-agent`)

## Request Transformation

### OpenWebUI Request → AG-UI RunAgentInput

The pipe transforms standard OpenWebUI requests:

**Note**: The middleware sends an empty `state` object (`{}`), which is handled by the AG-UI endpoint using a custom StateHandler. Model and parameter information is passed through `forwardedProps` and `context` instead.

```json
{
  "messages": [
    {"role": "user", "content": "Hello!"}
  ],
  "model": "aguimiddleware.agui-agent",
  "temperature": 0.8,
  "stream": true
}
```

Into AG-UI `RunAgentInput` format:

```json
{
  "threadId": "openwebui_12345678-1234-1234-1234-123456789012",
  "runId": "run_87654321-4321-4321-4321-210987654321",
  "state": {},
  "messages": [
    {
      "id": "msg_11111111-1111-1111-1111-111111111111",
      "role": "user", 
      "content": "Hello!"
    }
  ],
  "tools": [],
  "context": [
    {
      "description": "OpenWebUI request metadata",
      "value": "{\"original_model\":\"aguimiddleware.agui-agent\",\"requested_model\":\"agui-agent\",\"user_preferences\":{},\"source\":\"openwebui_pipe\",\"temperature\":0.8,\"max_tokens\":4096,\"stream\":true}"
    }
  ],
  "forwardedProps": {
    "openwebui_request": true,
    "model": "agui-agent",
    "original_params": {
      "temperature": 0.8,
      "stream": true,
      "max_tokens": 4096
    }
  }
}
```

### AG-UI Response → OpenWebUI Format

The pipe processes AG-UI events and converts them:

- `TEXT_MESSAGE_CONTENT` events → Text chunks for OpenWebUI
- `RUN_STARTED`/`RUN_FINISHED` → Logged (not shown to user)
- `RUN_ERROR` → Error messages
- `TOOL_CALL_*` events → Displayed to user (tool calls and results visible)

### Tool Call Formatting

The pipe displays tool calls to users similar to standard OpenWebUI models:

1. **Tool call start** - Shows when a tool is being called: `**🔧 Calling tool: `math`**`
2. **Tool arguments** - Streams tool arguments as they're built
3. **Tool result** - Shows formatted tool results in code blocks
4. **Model response** - The AI model's natural response incorporating the tool results

**Example output:**
```
**🔧 Calling tool: `math`**
2137*19

**📋 Tool result:**
```
40603
```

2137 multiplied by 19 equals 40,603! 🎉
```

This provides full transparency of tool usage while maintaining readability.

## Installation

1. **Install dependencies:**
   ```bash
   pip install requests>=2.31.0 pydantic>=2.0.0
   ```

2. **Place the pipe** in your OpenWebUI pipes directory

3. **Configure your AG-UI endpoint** through environment variables or OpenWebUI valves

4. **Start your AG-UI compatible endpoint** (must implement AG-UI protocol)

## Usage

1. **Select the pipe model** in OpenWebUI (e.g., `aguimiddleware.agui-agent`)
2. **Chat normally** - the pipe handles all protocol translation automatically
3. **Monitor logs** to see the request/response transformation process

## AG-UI Endpoint Requirements

Your AG-UI endpoint must:

- Accept `POST` requests with `RunAgentInput` JSON body
- Return AG-UI event streams for streaming requests (`Accept: text/event-stream`)
- Return JSON responses for non-streaming requests (`Accept: application/json`)
- Implement standard AG-UI events: `RUN_STARTED`, `TEXT_MESSAGE_START`, `TEXT_MESSAGE_CONTENT`, `TEXT_MESSAGE_END`, `RUN_FINISHED`, `RUN_ERROR`
- Expect context items with `description` (string) and `value` (string) fields
- Handle JSON-serialized metadata in context `value` fields
- Handle empty `state` objects with appropriate StateHandler (see example endpoint)

## Example AG-UI Endpoint

See the `pydantic_ai_agent/main.py` in this repository for an example AG-UI compatible endpoint implementation.

## Debugging

The pipe includes extensive logging. Check your OpenWebUI logs for:

- `🔄 Forwarding to AG-UI endpoint: <url>`
- `✅ Connected to AG-UI endpoint, processing events...`
- `📝 Message started/ended`
- `❌ Error messages` for troubleshooting

## Error Handling

Common errors and solutions:

- **Connection refused**: Check if AG-UI endpoint is running
- **404/500 errors**: Verify AG-UI endpoint implements the protocol correctly
- **Timeout**: Increase timeout or check endpoint performance
- **JSON parsing errors**: Verify AG-UI endpoint returns valid event format