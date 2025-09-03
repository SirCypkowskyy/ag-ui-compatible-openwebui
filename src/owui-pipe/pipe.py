"""
title: AG-UI Middleware Pipe
authors: Cyprian Gburek
author_url: https://github.com/sircypkowskyy
funding_url: https://github.com/open-webui
version: 0.0.1
required_open_webui_version: 0.3.17
license: MIT
"""

import os
import requests
import json
import time
import uuid
from typing import List, Union, Generator, Iterator, Any, Optional
from pydantic import BaseModel, Field
from open_webui.utils.misc import pop_system_message


class Pipe:
    class Valves(BaseModel):
        AG_UI_ENDPOINT_URL: str = Field(
            default="http://host.docker.internal:8000", 
            description="AG-UI compatible agent endpoint URL"
        )
        THREAD_ID_PREFIX: str = Field(
            default="openwebui", 
            description="Prefix for generated thread IDs"
        )
        DEFAULT_MODEL: str = Field(
            default="agui-agent", 
            description="Default model ID to request from AG-UI endpoint"
        )


    def __init__(self):
        self.type = "manifold"
        self.id = "aguimiddleware"
        self.name = "ag-ui/"
        self.valves = self.Valves(
            **{
                "AG_UI_ENDPOINT_URL": os.getenv("AG_UI_ENDPOINT_URL", "http://host.docker.internal:8000"),
                "THREAD_ID_PREFIX": os.getenv("THREAD_ID_PREFIX", "openwebui"),
                "DEFAULT_MODEL": os.getenv("DEFAULT_MODEL", "agui-agent")
            }
        )

    def get_model_mapping(self):
        """Map OpenWebUI-safe model IDs to actual model names"""
        return {
            "agui-agent": "agui-agent"
        }

    def get_ag_ui_models(self):
        """Return available models - these will be passed through to the AG-UI endpoint"""
        return [
            {"id": "agui-agent", "name": "agui-agent"},
        ]

    def pipes(self) -> List[dict]:
        return self.get_ag_ui_models()

    def transform_openwebui_to_ag_ui(self, body: dict) -> dict:
        """Transform OpenWebUI request to AG-UI RunAgentInput format"""
        system_message, messages = pop_system_message(body.get("messages", []))
        
        # Generate unique identifiers
        thread_id = f"{self.valves.THREAD_ID_PREFIX}_{uuid.uuid4()}"
        run_id = f"run_{uuid.uuid4()}"
        
        # Transform messages to AG-UI format
        ag_ui_messages = []
        
        # Add system message if present
        if system_message:
            ag_ui_messages.append({
                "id": f"msg_{uuid.uuid4()}",
                "role": "system",
                "content": str(system_message)
            })
        
        # Transform regular messages
        for msg in messages:
            ag_ui_msg = {
                "id": f"msg_{uuid.uuid4()}",
                "role": msg.get("role", "user"),
                "content": msg.get("content", "")
            }
            ag_ui_messages.append(ag_ui_msg)
        
        # Extract model from the request (remove pipe prefix if present)
        requested_model = body.get("model", self.valves.DEFAULT_MODEL)
        if requested_model and "." in requested_model:
            # Remove pipe prefix (e.g., "aguimiddleware.agui-agent" -> "agui-agent")
            model_id = requested_model.split(".", 1)[1]
            # Map to actual model name
            model_mapping = self.get_model_mapping()
            requested_model = model_mapping.get(model_id, self.valves.DEFAULT_MODEL)
        else:
            # If no prefix, try to map directly
            model_mapping = self.get_model_mapping()
            requested_model = model_mapping.get(requested_model, requested_model)
        
        # Build AG-UI RunAgentInput
        ag_ui_request = {
            "threadId": thread_id,  # Note: AG-UI uses camelCase
            "runId": run_id,
            "state": {},  # Required field - empty object
            "messages": ag_ui_messages,
            "tools": [],  # Could be extended to transform OpenWebUI tools
            "context": [
                {
                    "description": "OpenWebUI request metadata",
                    "value": json.dumps({
                        "original_model": body.get("model"),
                        "requested_model": requested_model,
                        "user_preferences": body.get("user", {}),
                        "source": "openwebui_pipe",
                        "temperature": body.get("temperature"),
                        "max_tokens": body.get("max_tokens"),
                        "stream": body.get("stream", True)
                    })
                }
            ],
            "forwardedProps": {
                "openwebui_request": True,
                "model": requested_model,  # Pass model in forwardedProps instead
                "original_params": {
                    "temperature": body.get("temperature"),
                    "top_p": body.get("top_p"),
                    "top_k": body.get("top_k"),
                    "stop": body.get("stop"),
                    "stream": body.get("stream"),
                    "max_tokens": body.get("max_tokens")
                }
            }
        }
        
        return ag_ui_request

    def pipe(self, body: dict) -> Union[str, Generator, Iterator]:
        """Main pipe method - transforms OpenWebUI request to AG-UI and back"""
        try:
            # Transform OpenWebUI request to AG-UI format
            ag_ui_request = self.transform_openwebui_to_ag_ui(body)
            
            print(f"🔄 Forwarding to AG-UI endpoint: {self.valves.AG_UI_ENDPOINT_URL}")
            print(f"📋 Request: threadId={ag_ui_request['threadId']}, runId={ag_ui_request['runId']}")
            print(f"🤖 Model: {ag_ui_request['forwardedProps']['model']}")
            print(f"💬 Messages: {len(ag_ui_request['messages'])}")
            print(f"📝 Context: {len(ag_ui_request['context'])} items")
            print(f"🔧 State: {{}} (empty object - required field)")
            print(f"🔧 Tool calls will be shown to user")
            if ag_ui_request['context']:
                print(f"📋 Context value type: {type(ag_ui_request['context'][0]['value'])}")
            
            # Forward to AG-UI endpoint and transform response back
            if body.get("stream", True):
                return self.stream_ag_ui_request(ag_ui_request)
            else:
                return self.non_stream_ag_ui_request(ag_ui_request)
                
        except Exception as e:
            print(f"❌ Error in pipe method: {e}")
            return f"Error: {e}"

    def stream_ag_ui_request(self, ag_ui_request: dict) -> Generator:
        """Forward AG-UI request to endpoint and transform streaming response back to OpenWebUI format"""
        try:
            headers = {
                "Content-Type": "application/json",
                "Accept": "text/event-stream"
            }
            
            # Forward request to AG-UI endpoint
            with requests.post(
                self.valves.AG_UI_ENDPOINT_URL,
                json=ag_ui_request,
                headers=headers,
                stream=True,
                timeout=(3.05, 60)
            ) as response:
                if response.status_code != 200:
                    error_text = response.text
                    print(f"❌ AG-UI endpoint error {response.status_code}: {error_text}")
                    
                    # Try to parse validation errors for better user feedback
                    if response.status_code == 422:
                        try:
                            error_data = json.loads(error_text)
                            if isinstance(error_data, list):
                                validation_errors = []
                                for error in error_data:
                                    field = ".".join(str(loc) for loc in error.get("loc", []))
                                    msg = error.get("msg", "Unknown error")
                                    validation_errors.append(f"{field}: {msg}")
                                yield f"Validation Error: {'; '.join(validation_errors)}"
                                return
                        except json.JSONDecodeError:
                            pass
                    
                    yield f"Error: AG-UI endpoint returned {response.status_code}: {error_text}"
                    return
                
                print("✅ Connected to AG-UI endpoint, processing events...")
                
                # Process AG-UI event stream and convert to OpenWebUI format
                for line in response.iter_lines():
                    if line:
                        line = line.decode("utf-8")
                        if line.startswith("data: "):
                            try:
                                event_data = json.loads(line[6:])
                                event_type = event_data.get("type", "")
                                
                                # Transform AG-UI events to OpenWebUI text chunks
                                if event_type == "TEXT_MESSAGE_CONTENT":
                                    # Extract delta text and yield as OpenWebUI expects
                                    delta = event_data.get("delta", "")
                                    if delta:
                                        yield delta
                                
                                elif event_type == "TEXT_MESSAGE_START":
                                    print(f"📝 Message started: {event_data.get('messageId', 'unknown')}")
                                
                                elif event_type == "TEXT_MESSAGE_END":
                                    print(f"✅ Message ended: {event_data.get('messageId', 'unknown')}")
                                
                                elif event_type == "RUN_STARTED":
                                    print(f"🚀 Run started: {event_data.get('runId', 'unknown')}")
                                
                                elif event_type == "RUN_FINISHED":
                                    print(f"🏁 Run finished: {event_data.get('runId', 'unknown')}")
                                    break
                                
                                elif event_type == "RUN_ERROR":
                                    error_msg = event_data.get("message", "Unknown error")
                                    print(f"❌ AG-UI error: {error_msg}")
                                    yield f"Error from AG-UI endpoint: {error_msg}"
                                    break
                                
                                elif event_type == "TOOL_CALL_START":
                                    tool_name = event_data.get("toolCallName", "unknown")
                                    tool_id = event_data.get("toolCallId", "unknown")
                                    print(f"🔧 Tool call started: {tool_name}")
                                    # Show tool call start to user (similar to OpenWebUI format)
                                    yield f"\n**🔧 Calling tool: `{tool_name}`**\n"
                                
                                elif event_type == "TOOL_CALL_ARGS":
                                    # Show tool arguments being built (streaming)
                                    args_delta = event_data.get("delta", "")
                                    if args_delta:
                                        yield args_delta
                                
                                elif event_type == "TOOL_CALL_END":
                                    print(f"🔧 Tool call completed")
                                    # Add line break after tool arguments
                                    yield "\n"
                                
                                elif event_type == "TOOL_CALL_RESULT":
                                    tool_result = event_data.get("content", "")
                                    print(f"🔍 Tool result: {tool_result}")
                                    if tool_result:
                                        # Show tool result to user (similar to OpenWebUI format)
                                        yield f"**📋 Tool result:**\n```\n{tool_result}\n```\n\n"
                                
                                # Add small delay to avoid overwhelming
                                time.sleep(0.01)
                                
                            except json.JSONDecodeError as e:
                                print(f"⚠️  Failed to parse AG-UI event: {line} - {e}")
                                continue
                            except KeyError as e:
                                print(f"⚠️  Unexpected AG-UI event structure: {e}")
                                continue
        
        except requests.exceptions.ConnectionError:
            error_msg = f"Failed to connect to AG-UI endpoint at {self.valves.AG_UI_ENDPOINT_URL}"
            print(f"❌ {error_msg}")
            yield f"Error: {error_msg}. Please check if the AG-UI endpoint is running."
        except requests.exceptions.RequestException as e:
            print(f"❌ Request to AG-UI endpoint failed: {e}")
            yield f"Error: Failed to connect to AG-UI endpoint: {e}"
        except Exception as e:
            print(f"❌ Error in AG-UI streaming: {e}")
            yield f"Error: {e}"

    def non_stream_ag_ui_request(self, ag_ui_request: dict) -> str:
        """Forward AG-UI request to endpoint and return non-streaming response"""
        try:
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            # Set non-streaming in the request
            ag_ui_request["state"]["stream"] = False
            
            response = requests.post(
                self.valves.AG_UI_ENDPOINT_URL,
                json=ag_ui_request,
                headers=headers,
                timeout=(3.05, 60)
            )
            
            if response.status_code != 200:
                error_text = response.text
                print(f"❌ AG-UI endpoint error {response.status_code}: {error_text}")
                
                # Try to parse validation errors for better user feedback
                if response.status_code == 422:
                    try:
                        error_data = json.loads(error_text)
                        if isinstance(error_data, list):
                            validation_errors = []
                            for error in error_data:
                                field = ".".join(str(loc) for loc in error.get("loc", []))
                                msg = error.get("msg", "Unknown error")
                                validation_errors.append(f"{field}: {msg}")
                            return f"Validation Error: {'; '.join(validation_errors)}"
                    except json.JSONDecodeError:
                        pass
                
                return f"Error: AG-UI endpoint returned {response.status_code}: {error_text}"
            
            # Parse response and extract text content
            result = response.json()
            
            # Extract text from AG-UI response format
            # This depends on how your AG-UI endpoint returns non-streaming responses
            if isinstance(result, dict):
                if "content" in result:
                    return result["content"]
                elif "message" in result:
                    return result["message"]
                elif "text" in result:
                    return result["text"]
                elif "result" in result:
                    return str(result["result"])
                else:
                    # Return the whole response as JSON if we can't find expected fields
                    return json.dumps(result, indent=2)
            else:
                return str(result)
                
        except requests.exceptions.ConnectionError:
            error_msg = f"Failed to connect to AG-UI endpoint at {self.valves.AG_UI_ENDPOINT_URL}"
            print(f"❌ {error_msg}")
            return f"Error: {error_msg}. Please check if the AG-UI endpoint is running."
        except requests.exceptions.RequestException as e:
            print(f"❌ Request to AG-UI endpoint failed: {e}")
            return f"Error: Failed to connect to AG-UI endpoint: {e}"
        except Exception as e:
            print(f"❌ Error in non-streaming AG-UI request: {e}")
            return f"Error: {e}"