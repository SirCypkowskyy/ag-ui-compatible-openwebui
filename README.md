# AG-UI Compatible OpenWebUI

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Pydantic AI](https://img.shields.io/badge/Pydantic_AI-0.8.1+-green.svg)](https://github.com/pydantic/pydantic-ai)

A comprehensive middleware solution that bridges **OpenWebUI** with **AG-UI compatible agents**, enabling seamless integration of advanced AI agents with state management, tool calls, and event streaming capabilities.

> ⚠️ **Early Development**: This project is in very early stages of development. The architecture, APIs, and implementation details are subject to significant changes as we work towards a more stable and robust solution. Use in production environments is not recommended at this time.

## Features

- **🔄 Protocol Translation**: Converts OpenWebUI requests to AG-UI `RunAgentInput` format and back
- **📊 State Management**: Full support for persistent agent state using Pydantic models
- **🛠️ Tool Call Visibility**: Transparent tool execution with proper formatting for users
- **⚡ Event Streaming**: Real-time AG-UI event stream processing with SSE support
- **🔧 Configurable**: Easy configuration via environment variables or OpenWebUI valves
- **🎯 Type-Safe**: Full type safety with Pydantic validation throughout

## Architecture

```
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐    ┌─────────────────┐
│             │    │              │    │                 │    │                 │
│ OpenWebUI   ├────► Pipe         ├────► AG-UI Agent     ├────► Response        │
│ Client      │    │ Middleware   │    │ (Pydantic AI)   │    │ Processing      │
│             │    │              │    │                 │    │                 │
└─────────────┘    └──────────────┘    └─────────────────┘    └─────────────────┘
                           │                      │
                           ▼                      ▼
                   ┌──────────────┐    ┌─────────────────┐
                   │ Request      │    │ State           │
                   │ Transform    │    │ Management      │
                   └──────────────┘    └─────────────────┘
```

**Data Flow:**
1. User sends request from OpenWebUI
2. Pipe transforms OpenWebUI request to AG-UI `RunAgentInput` format
3. Request forwarded to AG-UI compatible endpoint with state management
4. Agent processes request using tools and updates state
5. AG-UI event stream converted back to OpenWebUI format
6. User sees formatted response with visible tool calls

## Components

### OpenWebUI Pipe (`src/owui-pipe/`)
- **Middleware pipe** that handles protocol translation
- **Event stream processing** for real-time responses  
- **Tool call formatting** for user visibility
- **Error handling** with detailed validation feedback

### AG-UI Agent (`src/pydantic_ai_agent/`)
- **Pydantic AI agent** with state management
- **Math game example** with score tracking and streaks
- **Multiple tools** for state manipulation and calculations
- **FastAPI endpoint** implementing AG-UI protocol

## Quick Start

### Prerequisites

- Python 3.11+
- OpenWebUI instance with admin access
- [`uv`](https://docs.astral.sh/uv/) package manager (recommended) or `pip`
- [ngrok](https://ngrok.com/) (recommended for testing with external access)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/sircypkowskyy/ag-ui-compatible-openwebui.git
   cd ag-ui-compatible-openwebui
   ```

2. **Set up the AG-UI agent:**
   ```bash
   cd src/pydantic_ai_agent
   uv sync
   ```

3. **Set up the OpenWebUI pipe:**
   ```bash
   cd ../owui-pipe
   uv sync
   ```

4. **Configure environment variables:**
   ```bash
   export OPENAI_API_KEY="your-openai-api-key"
   ```

### Running the System

1. **Start the AG-UI agent:**
   ```bash
   cd src/pydantic_ai_agent
   uv run uvicorn main:app --host 0.0.0.0 --port 8000
   ```

2. **Install the pipe in OpenWebUI:**
   - Navigate to your OpenWebUI instance
   - Go to **Admin Panel** → **Functions** (`/admin/functions`)
   - Click **"+ Add Function"** 
   - Copy the entire contents of `src/owui-pipe/pipe.py` and paste it
   - Save the function
   - Configure the **Valves** with appropriate settings:
     - `AG_UI_ENDPOINT_URL`: Your AG-UI agent endpoint (e.g., `http://localhost:8000` or ngrok URL)
     - `THREAD_ID_PREFIX`: `"openwebui"` (default)
     - `DEFAULT_MODEL`: `"agui-agent"` (default)

3. **(Optional) Set up ngrok for external access:**
   ```bash
   # In a separate terminal, expose your local agent
   ngrok http 8000
   
   # Use the ngrok URL in your OpenWebUI pipe valves
   # Example: https://abc123.ngrok.io
   ```

4. **Test the integration:**
   ```bash
   cd src/pydantic_ai_agent
   uv run python test_state_example.py
   ```

## Usage Example

### Tool Call Visibility

**User**: "What's 25 + 17?"

**Agent**:

**🔧 Calling tool: `math`**
{"expression":"25 + 17"}

**📋 Tool result:**
```
42
```
## Configuration

### Environment Variables

put your OpenAI API key in the `.env` file in the root of the pydantic-ai agent project folder
```bash
export OPENAI_API_KEY="your-api-key"
```

### OpenWebUI Valve Configuration
- **AG_UI_ENDPOINT_URL**: Your AG-UI agent endpoint
- **THREAD_ID_PREFIX**: Prefix for conversation threads
- **DEFAULT_MODEL**: Fallback model identifier

## Testing

### Run Agent State Tests
```bash
cd src/pydantic_ai_agent
uv run python test_state_example.py
```

### Run Pipe Middleware Tests  
```bash
cd src/owui-pipe
python test_middleware_example.py
```

### Manual Testing Prompts
- `"Hi! I'm [Name]. Set my name and show my game state."`
- `"What's 25 + 17? Give me 10 points for the correct answer!"`
- `"Show me my current game statistics"`
- `"Reset my game but keep my best streak"`

### Testing with ngrok (Recommended)

For testing the full OpenWebUI → Pipe → Agent flow:

1. **Start the AG-UI agent:**
   ```bash
   cd src/pydantic_ai_agent
   uv run uvicorn main:app --host 0.0.0.0 --port 8000
   ```

2. **In another terminal, start ngrok:**
   ```bash
   ngrok http 8000
   ```

3. **Configure OpenWebUI pipe valves:**
   - Set `AG_UI_ENDPOINT_URL` to your ngrok URL (e.g., `https://abc123.ngrok.io`)
   - Save the configuration

4. **Test in OpenWebUI:**
   - Select the `aguimiddleware.openaigpt4omini` model
   - Send test messages and observe tool calls and state management

## State Management

The agent maintains game state using Pydantic models:

```python
class GameState(BaseModel):
    score: int = 0
    problems_solved: int = 0  
    current_streak: int = 0
    best_streak: int = 0
    player_name: str = "Player"
```

**Available Tools:**
- `get_game_state()` - Display current state
- `update_score(points, correct)` - Update score and streak
- `set_player_name(name)` - Set player name
- `reset_game()` - Reset game keeping best streak
- `math(expression)` - Solve math problems

## Development

### Using pip instead of uv

If you prefer `pip` over `uv`, you can install dependencies using:

```bash
# For AG-UI agent
cd src/pydantic_ai_agent
pip install -e .

# For OpenWebUI pipe  
cd ../owui-pipe
pip install -e .
```

### Project Structure
```
ag-ui-compatible-openwebui/
├── src/
│   ├── owui-pipe/           # OpenWebUI middleware
│   │   ├── pipe.py          # Main pipe implementation
│   │   ├── test_middleware_example.py
│   │   └── README.md
│   └── pydantic_ai_agent/   # AG-UI compatible agent
│       ├── main.py          # FastAPI AG-UI endpoint
│       ├── test_state_example.py
│       └── pyproject.toml
└── README.md
```

### Adding New Tools
```python
@agent.tool
def your_tool(ctx: RunContext[StateDeps[GameState]], param: str) -> str:
    """Your tool description"""
    # Access state: ctx.deps.state
    # Modify state: ctx.deps.state.field = value
    return "Tool result"
```

### Extending State Model
```python
class YourState(BaseModel):
    # Add your fields
    custom_field: str = "default"
    
# Update agent configuration
agent = Agent(
    'openai:gpt-4o-mini',
    deps_type=StateDeps[YourState]
)
```

## Areas for Improvement

- 🔧 Enhanced error handling and recovery
- 📊 More sophisticated state management patterns
- 🛠️ Additional tool types and integrations
- 🎨 Better UI/UX for tool call visualization and user interaction
- 📈 Performance optimizations
- 🧪 Comprehensive test coverage

## Acknowledgments

- [Pydantic AI](https://github.com/pydantic/pydantic-ai) - The AI agent framework I like to use when developing AI agents
- [OpenWebUI](https://github.com/open-webui/open-webui) - The web interface 
- [AG-UI Protocol](https://docs.ag-ui.com/) - The agent-UI communication standard

## Support

- 📖 [Documentation](docs/)
- 🐛 [Issue Tracker](https://github.com/sircypkowskyy/ag-ui-compatible-openwebui/issues)
- 💬 [Discussions](https://github.com/sircypkowskyy/ag-ui-compatible-openwebui/discussions)
