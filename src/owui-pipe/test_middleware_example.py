#!/usr/bin/env python3
"""
Test example demonstrating AG-UI middleware pipe functionality.
This script shows how the pipe transforms OpenWebUI requests to AG-UI format.
"""

import json
import uuid
from pipe import Pipe

def test_request_transformation():
    """Test OpenWebUI to AG-UI request transformation"""
    
    # Initialize the pipe
    pipe = Pipe()
    
    # Create standard OpenWebUI request
    openwebui_request = {
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful assistant."
            },
            {
                "role": "user", 
                "content": "Hello! Can you explain what AG-UI is?"
            }
        ],
        "model": "aguimiddleware.openaigpt4omini",
        "temperature": 0.8,
        "max_tokens": 1000,
        "stream": True,
        "top_p": 0.9
    }
    
    print("🔍 Testing OpenWebUI to AG-UI Transformation")
    print("=" * 60)
    print("📥 OpenWebUI Request:")
    print(json.dumps(openwebui_request, indent=2))
    
    # Transform to AG-UI format
    ag_ui_request = pipe.transform_openwebui_to_ag_ui(openwebui_request)
    
    print("\n📤 Transformed AG-UI Request:")
    print(json.dumps(ag_ui_request, indent=2))
    
    print("\n✅ Transformation Details:")
    print(f"   Thread ID: {ag_ui_request['threadId']}")
    print(f"   Run ID: {ag_ui_request['runId']}")
    print(f"   Model: {ag_ui_request['forwardedProps']['model']}")
    print(f"   State: {ag_ui_request.get('state', 'missing')} (empty object)")
    print(f"   State field present: {'state' in ag_ui_request}")
    print(f"   Messages: {len(ag_ui_request['messages'])}")
    print(f"   Context Items: {len(ag_ui_request['context'])}")
    if ag_ui_request['context']:
        print(f"   Context format: description + value (AG-UI compliant)")
        print(f"   First context: {ag_ui_request['context'][0]['description']}")
        print(f"   Value type: {type(ag_ui_request['context'][0]['value'])}")
        print(f"   Value is JSON string: {isinstance(ag_ui_request['context'][0]['value'], str)}")
    print(f"   OpenWebUI Metadata: {ag_ui_request['forwardedProps']['openwebui_request']}")
    
    return ag_ui_request

def test_middleware_flow():
    """Test the complete middleware flow (requires running AG-UI endpoint)"""
    
    pipe = Pipe()
    
    # Create test request
    test_request = {
        "messages": [
            {
                "role": "user",
                "content": "Hello from OpenWebUI middleware test!"
            }
        ],
        "model": "aguimiddleware.openaigpt4omini",
        "stream": True,
        "temperature": 0.7
    }
    
    print("\n🧪 Testing Complete Middleware Flow")
    print("=" * 60)
    print(f"🎯 Target Endpoint: {pipe.valves.AG_UI_ENDPOINT_URL}")
    print("📋 Request:")
    print(json.dumps(test_request, indent=2))
    
    print("\n🚀 Sending request through middleware...")
    print("-" * 40)
    
    try:
        # This will attempt to connect to the actual AG-UI endpoint
        response_generator = pipe.pipe(test_request)
        
        print("📨 Response stream:")
        for chunk in response_generator:
            if isinstance(chunk, str):
                print(chunk, end="", flush=True)
                
        print("\n✅ Middleware flow completed successfully!")
        
    except Exception as e:
        print(f"❌ Error (expected if no AG-UI endpoint running): {e}")
        print("\n💡 To test the complete flow:")
        print(f"   1. Start an AG-UI compatible endpoint at {pipe.valves.AG_UI_ENDPOINT_URL}")
        print("   2. Run this test again")

def test_configuration():
    """Test pipe configuration"""
    
    pipe = Pipe()
    
    print("\n⚙️  Testing Pipe Configuration")
    print("=" * 60)
    print(f"🔗 AG-UI Endpoint URL: {pipe.valves.AG_UI_ENDPOINT_URL}")
    print(f"🏷️  Thread ID Prefix: {pipe.valves.THREAD_ID_PREFIX}")
    print(f"🤖 Default Model: {pipe.valves.DEFAULT_MODEL}")
    print(f"🔧 Tool Calls: Always visible to user")
    print(f"🆔 Pipe ID: {pipe.id}")
    print(f"📛 Pipe Name: {pipe.name}")
    print(f"🔧 Pipe Type: {pipe.type}")
    
    print("\n📋 Available Models:")
    models = pipe.get_ag_ui_models()
    for model in models:
        print(f"   - {model['id']} ({model['name']})")

def demonstrate_ag_ui_format():
    """Demonstrate the AG-UI RunAgentInput format"""
    
    print("\n📚 AG-UI RunAgentInput Format Reference")
    print("=" * 60)
    
    example_format = {
        "threadId": "string - unique conversation thread identifier",
        "runId": "string - unique run identifier", 
        "state": "object - agent state and configuration",
        "messages": "array - conversation messages with IDs",
        "tools": "array - available tools for the agent",
        "context": "array - contextual information",
        "forwardedProps": "object - additional properties"
    }
    
    print("Required fields from request.json:")
    print(json.dumps(example_format, indent=2))
    
    print("\n🔄 This pipe automatically transforms OpenWebUI requests to include:")
    print("   ✅ threadId - Generated with configurable prefix")
    print("   ✅ runId - Unique UUID for each request")
    print("   ✅ state - Model config, temperature, tokens, etc.")
    print("   ✅ messages - Transformed with unique IDs")
    print("   ✅ tools - Empty array (extensible)")
    print("   ✅ context - OpenWebUI metadata")
    print("   ✅ forwardedProps - Original request parameters")

if __name__ == "__main__":
    print("🧪 AG-UI Middleware Pipe Test Suite")
    print("=" * 60)
    
    # Test request transformation
    ag_ui_request = test_request_transformation()
    
    # Test configuration
    test_configuration()
    
    # Demonstrate AG-UI format
    demonstrate_ag_ui_format()
    
    # Test complete middleware flow (will fail if no endpoint)
    test_middleware_flow()
    
    print("\n" + "=" * 60)
    print("✅ Test Suite Complete!")
    print("\n📝 Notes:")
    print("- Set AG_UI_ENDPOINT_URL environment variable to test with real endpoint")
    print("- The pipe automatically handles all protocol transformation")
    print("- Check OpenWebUI logs for detailed middleware operation info")
    print("- Ensure your AG-UI endpoint implements the required event types")
