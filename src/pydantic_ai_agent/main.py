"""
Simple math game agent that uses the pydantic-ai library to solve math problems and track the player's progress.
"""
import json
from http import HTTPStatus

from ag_ui.core import RunAgentInput
from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel, ValidationError

from pydantic_ai import Agent, RunContext
from pydantic_ai.ag_ui import SSE_CONTENT_TYPE, StateDeps, run_ag_ui
from dotenv import load_dotenv


# Define the game state
class GameState(BaseModel):
    """State for a simple math game"""
    score: int = 0
    """The player's score"""
    problems_solved: int = 0
    """The number of problems the player has solved"""
    current_streak: int = 0
    """The current streak of problems the player has solved"""
    best_streak: int = 0
    """The best streak of problems the player has solved"""
    player_name: str = "Player"
    """The player's name"""

load_dotenv()   
agent = Agent(
    """The agent"""
    'openai:gpt-4o-mini', 
    instructions='''You are a fun math game assistant! 
    
    You help players solve math problems and track their progress. 
    You can:
    - Give math problems using the math tool
    - Update the player's score when they solve problems correctly
    - Track their streak and best streak
    - Encourage them and make the experience fun!
    
    Always be enthusiastic and encouraging!''',
    deps_type=StateDeps[GameState]
)

@agent.tool_plain
def math(expression: str) -> float:
    """Solve a math problem"""
    return eval(expression)

@agent.tool
def get_game_state(ctx: RunContext[StateDeps[GameState]]) -> dict:
    """Get the current game state"""
    return ctx.deps.state.model_dump()

@agent.tool  
def update_score(ctx: RunContext[StateDeps[GameState]], points_earned: int, problem_correct: bool = True) -> str:
    """Update the player's score and streak when they solve a problem"""
    state = ctx.deps.state
    
    if problem_correct:
        state.score += points_earned
        state.problems_solved += 1
        state.current_streak += 1
        
        if state.current_streak > state.best_streak:
            state.best_streak = state.current_streak
            
        return f"Great job! You earned {points_earned} points. Current score: {state.score}, Streak: {state.current_streak}"
    else:
        state.current_streak = 0
        return f"Oops! Your streak was reset. Current score: {state.score}, Problems solved: {state.problems_solved}"

@agent.tool
def set_player_name(ctx: RunContext[StateDeps[GameState]], name: str) -> str:
    """Set the player's name"""
    ctx.deps.state.player_name = name
    return f"Welcome to the math game, {name}! 🎉"

@agent.tool
def reset_game(ctx: RunContext[StateDeps[GameState]]) -> str:
    """Reset the game state"""
    state = ctx.deps.state
    old_best = state.best_streak
    
    state.score = 0
    state.problems_solved = 0
    state.current_streak = 0
    # Keep the best streak and player name
    
    return f"Game reset! Your best streak of {old_best} is still saved. Let's play again, {state.player_name}!"

app = FastAPI()


@app.post('/')
async def run_agent(request: Request) -> Response:
    """Run the agent"""
    accept = request.headers.get('accept', SSE_CONTENT_TYPE)
    try:
        data = await request.json()
    except Exception as e:
        data = {}
    try:
        run_input = RunAgentInput.model_validate(data)
    except ValidationError as e:  # pragma: no cover
        return Response(
            content=json.dumps(e.json()),
            media_type='application/json',
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        )

    # Create StateDeps instance with GameState
    # Initialize state from run_input or use default GameState
    if hasattr(run_input, 'state') and run_input.state:
        try:
            game_state = GameState.model_validate(run_input.state)
        except Exception:
            # If state validation fails, use default state
            game_state = GameState()
    else:
        game_state = GameState()
    
    deps = StateDeps(game_state)
    
    event_stream = run_ag_ui(agent, run_input, deps=deps, accept=accept)

    return StreamingResponse(event_stream, media_type=accept)