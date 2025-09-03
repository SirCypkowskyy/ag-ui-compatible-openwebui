#!/usr/bin/env python3
"""
Test script to demonstrate state management in the pydantic-ai agent
"""

import asyncio
import json
from main import agent, GameState
from pydantic_ai.ag_ui import StateDeps


async def test_state_management():
    """Test the state management functionality"""
    
    print("🎮 Testing Pydantic-AI Agent with State Management")
    print("=" * 60)
    
    # Initialize state
    initial_state = GameState(player_name="Alice")
    deps = StateDeps(initial_state)
    
    print(f"📊 Initial state: {initial_state.model_dump()}")
    print()
    
    # Test 1: Set player name and get state
    print("🔧 Test 1: Setting player name and getting state")
    result1 = await agent.run(
        "Hi! My name is Bob. Can you show me my current game state?",
        deps=deps
    )
    print(f"Response: {result1.output}")
    print(f"State after: {deps.state.model_dump()}")
    print()
    
    # Test 2: Solve a math problem and update score
    print("🔧 Test 2: Solving math problem and updating score")
    result2 = await agent.run(
        "What's 15 + 27? When I get it right, give me 10 points!",
        deps=deps
    )
    print(f"Response: {result2.output}")
    print(f"State after: {deps.state.model_dump()}")
    print()
    
    # Test 3: Solve another problem to build streak
    print("🔧 Test 3: Solving another problem to build streak")
    result3 = await agent.run(
        "What's 8 * 7? Give me 15 points for this one!",
        deps=deps
    )
    print(f"Response: {result3.output}")
    print(f"State after: {deps.state.model_dump()}")
    print()
    
    # Test 4: Get final state
    print("🔧 Test 4: Getting final game state")
    result4 = await agent.run(
        "Show me my final game statistics!",
        deps=deps
    )
    print(f"Response: {result4.output}")
    print(f"Final state: {deps.state.model_dump()}")
    print()
    
    # Test 5: Reset game
    print("🔧 Test 5: Resetting the game")
    result5 = await agent.run(
        "Reset my game but keep my best streak record",
        deps=deps
    )
    print(f"Response: {result5.output}")
    print(f"State after reset: {deps.state.model_dump()}")
    
    print("\n✅ State management test completed!")
    print(f"🏆 Final best streak: {deps.state.best_streak}")
    print(f"👤 Player: {deps.state.player_name}")


if __name__ == "__main__":
    asyncio.run(test_state_management())
