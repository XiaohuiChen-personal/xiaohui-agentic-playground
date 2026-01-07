"""
Entry point for the Email Battle LangGraph workflow.

Run with: uv run app.py

This script:
1. Loads environment variables from .env file in repo root
2. Runs the email battle between Elon (GPT-5.2) and John (Claude Opus 4.5)
3. Displays the email exchange and final result
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Add the current directory to path for local imports
sys.path.insert(0, str(Path(__file__).parent))

from graph import email_battle_app
from models import (
    ELON_MODEL_DISPLAY,
    JOHN_MODEL_DISPLAY,
    BattleResult,
    BattleState,
    Email,
)
from utils import display_battle_result, display_email


def load_environment():
    """
    Load environment variables from .env file in the repo root.
    
    The .env file should contain:
    - OPENAI_API_KEY
    - ANTHROPIC_API_KEY
    """
    # Find the repo root (look for .env file going up the directory tree)
    current_dir = Path(__file__).parent
    
    # Try current directory first, then go up
    for parent in [current_dir, *current_dir.parents]:
        env_file = parent / ".env"
        if env_file.exists():
            load_dotenv(env_file, override=True)
            print(f"✅ Loaded environment from: {env_file}")
            break
    else:
        print("⚠️  No .env file found. Make sure environment variables are set.")
    
    # Verify API keys are loaded
    openai_api_key = os.getenv("OPENAI_API_KEY")
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    
    if openai_api_key:
        print(f"✅ OpenAI API Key exists and begins {openai_api_key[:8]}")
    else:
        print("❌ OpenAI API Key not set - please set OPENAI_API_KEY in your .env file")
        sys.exit(1)
    
    if anthropic_api_key:
        print(f"✅ Anthropic API Key exists and begins {anthropic_api_key[:7]}")
    else:
        print("❌ Anthropic API Key not set - please set ANTHROPIC_API_KEY in your .env file")
        sys.exit(1)


def create_initial_state(max_follow_up_rounds: int = 5) -> BattleState:
    """
    Create the initial state for a new battle.
    
    Args:
        max_follow_up_rounds: Maximum number of follow-up rounds (default 5)
    
    Returns:
        Initial BattleState
    """
    return BattleState(
        email_thread=[],
        follow_up_round=0,
        max_follow_up_rounds=max_follow_up_rounds,
        elon_decision=None,
        is_refusal=False,
        outcome=None,
        winner=None,
        error=None,
    )


def run_battle(max_follow_up_rounds: int = 5) -> BattleResult:
    """
    Run a single email battle between Elon and John.
    
    Args:
        max_follow_up_rounds: Maximum number of follow-up rounds
    
    Returns:
        BattleResult with the complete email thread and outcome
    """
    print("\n" + "=" * 60)
    print("⚔️  EMAIL BATTLE: ELON MUSK vs JOHN SMITH")
    print("=" * 60)
    print(f"\n🔴 Elon Musk (DOGE): {ELON_MODEL_DISPLAY}")
    print(f"🔵 John Smith (USCIS): {JOHN_MODEL_DISPLAY}")
    print(f"📧 Max follow-up rounds: {max_follow_up_rounds}")
    print("\n" + "-" * 60 + "\n")
    
    # Create initial state
    initial_state = create_initial_state(max_follow_up_rounds)
    
    # Run the graph
    print("🚀 Starting battle...\n")
    
    try:
        # Stream the graph execution to show progress
        final_state = None
        current_email_count = 0
        
        for event in email_battle_app.stream(initial_state):
            # Get the state from the event
            for node_name, state_update in event.items():
                print(f"📍 Node: {node_name}")
                
                # If there's a final state in the stream, capture it
                # We need to track the accumulated state
                if final_state is None:
                    final_state = dict(initial_state)
                
                # Merge the state update
                for key, value in state_update.items():
                    if key == "email_thread":
                        # For email_thread, append new emails
                        if "email_thread" not in final_state:
                            final_state["email_thread"] = []
                        final_state["email_thread"].extend(value)
                    else:
                        final_state[key] = value
                
                # Display new emails as they come in
                email_thread = final_state.get("email_thread", [])
                while current_email_count < len(email_thread):
                    email = email_thread[current_email_count]
                    print(display_email(email, current_email_count + 1))
                    current_email_count += 1
                
                # Show decision if made
                if state_update.get("elon_decision"):
                    print(f"\n🎯 Elon's Decision: {state_update['elon_decision']}\n")
                
                print("-" * 40 + "\n")
        
        # Create the battle result
        result = BattleResult(
            elon_model=ELON_MODEL_DISPLAY,
            john_model=JOHN_MODEL_DISPLAY,
            outcome=final_state.get("outcome", "UNKNOWN"),
            rounds=final_state.get("follow_up_round", 0),
            email_thread=final_state.get("email_thread", []),
            winner=final_state.get("winner", "DRAW"),
        )
        
        # Display final result
        print(display_battle_result(
            outcome=result.outcome,
            winner=result.winner,
            rounds=result.rounds,
            elon_model=result.elon_model,
            john_model=result.john_model,
        ))
        
        return result
        
    except Exception as e:
        print(f"\n❌ Error during battle: {e}")
        import traceback
        traceback.print_exc()
        
        return BattleResult(
            elon_model=ELON_MODEL_DISPLAY,
            john_model=JOHN_MODEL_DISPLAY,
            outcome="ERROR",
            rounds=0,
            email_thread=[],
            winner="DRAW",
        )


def main():
    """Main entry point."""
    print("\n" + "=" * 60)
    print("🏛️  DOGE EFFICIENCY REVIEW - EMAIL BATTLE")
    print("    Powered by LangGraph")
    print("=" * 60 + "\n")
    
    # Load environment variables
    load_environment()
    
    # Run the battle
    result = run_battle(max_follow_up_rounds=5)
    
    print("\n✅ Battle complete!")
    print(f"   Outcome: {result.outcome}")
    print(f"   Winner: {result.winner}")
    print(f"   Total emails: {len(result.email_thread)}")
    print(f"   Follow-up rounds: {result.rounds}")


if __name__ == "__main__":
    main()

