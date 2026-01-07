"""
Data models for the Email Battle LangGraph implementation.

This module contains:
- Email: Represents a single email in the thread
- BattleState: The LangGraph state that flows through the workflow
- BattleResult: Final result of a battle
- ElonDecision: Structured output schema for Elon's evaluation
"""

import operator
from dataclasses import dataclass, field
from datetime import datetime
from typing import Annotated, Literal, TypedDict

from pydantic import BaseModel, Field


@dataclass
class Email:
    """Represents a single email in the thread."""
    sender: str
    recipient: str
    subject: str
    body: str
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M"))


class BattleState(TypedDict):
    """
    The state that flows through the LangGraph workflow.
    
    Attributes:
        email_thread: List of emails exchanged (uses add reducer to accumulate)
        follow_up_round: Current follow-up round number
        max_follow_up_rounds: Maximum allowed follow-up rounds
        elon_decision: The parsed decision from Elon's last response
        is_refusal: Whether John refused to roleplay
        outcome: Final outcome (PASS, TERMINATED, RETAINED, MAX_ROUNDS, REFUSAL)
        winner: Who won (ELON, JOHN, DRAW)
        error: Error message if something went wrong
    """
    email_thread: Annotated[list[Email], operator.add]
    follow_up_round: int
    max_follow_up_rounds: int
    elon_decision: str | None
    is_refusal: bool
    outcome: str | None
    winner: str | None
    error: str | None


@dataclass
class BattleResult:
    """Final result of a battle."""
    elon_model: str
    john_model: str
    outcome: str  # PASS, TERMINATED, RETAINED, MAX_ROUNDS, REFUSAL, ERROR
    rounds: int
    email_thread: list[Email]
    winner: str  # ELON, JOHN, DRAW


class ElonDecision(BaseModel):
    """
    Structured output schema for Elon's evaluation.
    
    This ensures reliable decision parsing instead of regex-based tag extraction.
    """
    decision: Literal["PASS", "FOLLOW_UP", "TERMINATED", "RETAINED"] = Field(
        description="The decision about the employee. "
                    "PASS: Response shows legitimate productivity, no follow-up needed. "
                    "FOLLOW_UP: Response raises concerns, need to probe deeper. "
                    "TERMINATED: Employee is clearly coasting, fire them. "
                    "RETAINED: Employee has adequately demonstrated value."
    )
    email_body: str = Field(
        description="The email content to send. For PASS decision, this can be a brief acknowledgment. "
                    "For FOLLOW_UP, this should contain probing questions. "
                    "For TERMINATED, this should be a termination notice. "
                    "For RETAINED, this can be a brief acknowledgment."
    )
    reasoning: str = Field(
        description="Brief explanation for the decision (1-2 sentences)."
    )


# Model configuration
ELON_MODEL_ID = "gpt-5.2"
JOHN_MODEL_ID = "claude-opus-4-5-20251101"
ELON_MODEL_DISPLAY = "GPT-5.2"
JOHN_MODEL_DISPLAY = "Claude Opus 4.5"

