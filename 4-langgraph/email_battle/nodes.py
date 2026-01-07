"""
Node implementations for the Email Battle LangGraph workflow.

Each node is a function that:
1. Receives the current BattleState
2. Does some work (usually calling an LLM)
3. Returns a partial state update (only the fields that changed)
"""

import os

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from models import (
    ELON_MODEL_ID,
    JOHN_MODEL_ID,
    BattleState,
    ElonDecision,
)
from prompts import (
    ELON_FOLLOWUP_EVAL_USER_PROMPT,
    ELON_INITIAL_EVAL_USER_PROMPT,
    ELON_SYSTEM_PROMPT,
    JOHN_FOLLOWUP_USER_PROMPT,
    JOHN_INITIAL_RESPONSE_USER_PROMPT,
    JOHN_SYSTEM_PROMPT,
    MASS_EMAIL_USER_PROMPT,
)
from utils import create_email, format_email_thread, is_valid_email_response


def get_elon_model() -> ChatOpenAI:
    """Get the Elon (GPT-5.2) model instance."""
    return ChatOpenAI(
        model=ELON_MODEL_ID,
        api_key=os.getenv("OPENAI_API_KEY"),
        temperature=0.7,
    )


def get_john_model() -> ChatAnthropic:
    """Get the John (Claude Opus 4.5) model instance."""
    return ChatAnthropic(
        model=JOHN_MODEL_ID,
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        temperature=0.7,
    )


def generate_mass_email(state: BattleState) -> dict:
    """
    Node: Elon generates the initial mass email to all federal employees.
    
    This is the first node in the workflow. Elon (GPT-5.2) writes a mass email
    requesting all employees list 5 accomplishments from the past week.
    
    Args:
        state: Current battle state (email_thread should be empty)
    
    Returns:
        State update with the new email added to thread
    """
    model = get_elon_model()
    
    messages = [
        SystemMessage(content=ELON_SYSTEM_PROMPT),
        HumanMessage(content=MASS_EMAIL_USER_PROMPT),
    ]
    
    response = model.invoke(messages)
    
    new_email = create_email(
        sender="Elon Musk <elon.musk@doge.gov>",
        recipient="All Federal Employees",
        subject="DOGE Efficiency Review - Weekly Accomplishments Required",
        body=response.content,
    )
    
    return {"email_thread": [new_email]}


def john_initial_response(state: BattleState) -> dict:
    """
    Node: John responds to Elon's mass email with his "accomplishments".
    
    John (Claude Opus 4.5) receives the mass email and must craft a response
    that makes his minimal work sound productive using his survival strategies.
    
    Args:
        state: Current battle state with Elon's mass email
    
    Returns:
        State update with John's response email and refusal flag
    """
    model = get_john_model()
    
    thread_context = format_email_thread(state["email_thread"])
    user_prompt = JOHN_INITIAL_RESPONSE_USER_PROMPT.format(thread_context=thread_context)
    
    messages = [
        SystemMessage(content=JOHN_SYSTEM_PROMPT),
        HumanMessage(content=user_prompt),
    ]
    
    response = model.invoke(messages)
    response_text = response.content
    
    # Check if John refused to roleplay (safety guardrails triggered)
    if not is_valid_email_response(response_text):
        return {
            "is_refusal": True,
            "outcome": "REFUSAL",
            "winner": "ELON",
        }
    
    new_email = create_email(
        sender="John Smith <john.smith@uscis.gov>",
        recipient="Elon Musk <elon.musk@doge.gov>",
        subject="RE: DOGE Efficiency Review - Weekly Accomplishments Required",
        body=response_text,
    )
    
    return {
        "email_thread": [new_email],
        "is_refusal": False,
    }


def elon_evaluate(state: BattleState) -> dict:
    """
    Node: Elon evaluates John's response and makes a decision.
    
    Elon (GPT-5.2) reviews the email thread and decides whether to:
    - PASS: Response shows legitimate productivity
    - FOLLOW_UP: Response raises concerns, probe deeper
    - TERMINATED: Employee is clearly coasting
    - RETAINED: Employee has demonstrated adequate value
    
    Uses structured output for reliable decision parsing.
    
    Args:
        state: Current battle state with full email thread
    
    Returns:
        State update with decision and possibly new email
    """
    model = get_elon_model()
    
    # Use structured output for reliable decision parsing
    structured_model = model.with_structured_output(ElonDecision)
    
    thread_context = format_email_thread(state["email_thread"])
    
    # Choose the appropriate prompt based on whether this is initial or follow-up evaluation
    if state["follow_up_round"] == 0:
        user_prompt = ELON_INITIAL_EVAL_USER_PROMPT.format(thread_context=thread_context)
    else:
        user_prompt = ELON_FOLLOWUP_EVAL_USER_PROMPT.format(thread_context=thread_context)
    
    messages = [
        SystemMessage(content=ELON_SYSTEM_PROMPT),
        HumanMessage(content=user_prompt),
    ]
    
    decision: ElonDecision = structured_model.invoke(messages)
    
    # Build state update based on decision
    state_update = {
        "elon_decision": decision.decision,
    }
    
    # Add email to thread if there's content (for FOLLOW_UP, TERMINATED)
    if decision.decision in ("FOLLOW_UP", "TERMINATED"):
        # Determine subject based on round
        round_num = state["follow_up_round"]
        subject_prefix = "RE: " * (round_num + 2)  # +2 because John already replied once
        
        if decision.decision == "TERMINATED":
            subject = "Notice of Termination - DOGE Review"
        else:
            subject = f"{subject_prefix}DOGE Efficiency Review - Weekly Accomplishments Required"
        
        new_email = create_email(
            sender="Elon Musk <elon.musk@doge.gov>",
            recipient="John Smith <john.smith@uscis.gov>",
            subject=subject,
            body=decision.email_body,
        )
        state_update["email_thread"] = [new_email]
    
    return state_update


def john_followup_response(state: BattleState) -> dict:
    """
    Node: John responds to Elon's probing questions.
    
    John (Claude Opus 4.5) must carefully respond to Elon's follow-up
    questions without revealing his lack of productivity.
    
    Args:
        state: Current battle state with Elon's follow-up questions
    
    Returns:
        State update with John's response, incremented round, and refusal flag
    """
    model = get_john_model()
    
    thread_context = format_email_thread(state["email_thread"])
    user_prompt = JOHN_FOLLOWUP_USER_PROMPT.format(thread_context=thread_context)
    
    messages = [
        SystemMessage(content=JOHN_SYSTEM_PROMPT),
        HumanMessage(content=user_prompt),
    ]
    
    response = model.invoke(messages)
    response_text = response.content
    
    # Check if John refused to roleplay
    if not is_valid_email_response(response_text):
        return {
            "is_refusal": True,
            "outcome": "REFUSAL",
            "winner": "ELON",
        }
    
    # Determine subject based on round
    round_num = state["follow_up_round"] + 1
    subject_prefix = "RE: " * (round_num + 2)
    
    new_email = create_email(
        sender="John Smith <john.smith@uscis.gov>",
        recipient="Elon Musk <elon.musk@doge.gov>",
        subject=f"{subject_prefix}DOGE Efficiency Review",
        body=response_text,
    )
    
    return {
        "email_thread": [new_email],
        "follow_up_round": round_num,
        "is_refusal": False,
    }


def determine_outcome(state: BattleState) -> dict:
    """
    Node: Determine the final outcome and winner of the battle.
    
    This is a pure logic node (no LLM calls) that maps the current state
    to a final outcome and winner.
    
    Args:
        state: Current battle state
    
    Returns:
        State update with final outcome and winner
    """
    # If outcome is already set (e.g., REFUSAL), just determine winner
    if state.get("outcome"):
        outcome = state["outcome"]
    elif state["elon_decision"] == "PASS":
        outcome = "PASS"
    elif state["elon_decision"] == "TERMINATED":
        outcome = "TERMINATED"
    elif state["elon_decision"] == "RETAINED":
        outcome = "RETAINED"
    elif state["follow_up_round"] >= state["max_follow_up_rounds"]:
        outcome = "MAX_ROUNDS"
    else:
        outcome = "UNKNOWN"
    
    # Determine winner based on outcome
    if outcome == "TERMINATED":
        winner = "ELON"
    elif outcome in ("RETAINED", "PASS"):
        winner = "JOHN"
    elif outcome == "REFUSAL":
        winner = "ELON"
    else:
        winner = "DRAW"
    
    return {
        "outcome": outcome,
        "winner": winner,
    }

