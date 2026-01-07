"""
Helper functions for the Email Battle.

This module contains:
- format_email_thread: Formats emails for agent context
- is_valid_email_response: Checks if response is valid vs refusal
- create_email: Factory function for creating Email objects
- determine_winner: Maps outcome to winner
"""

from datetime import datetime

from models import Email


def format_email_thread(emails: list[Email], newest_first: bool = True) -> str:
    """
    Format emails as a thread for agent context.
    
    Mimics how real email clients display threads with the most recent
    message first (by default).
    
    Args:
        emails: List of Email objects
        newest_first: If True, show newest message first (default)
    
    Returns:
        Formatted string representation of the email thread
    """
    if not emails:
        return "(No emails in thread)"
    
    thread_emails = list(reversed(emails)) if newest_first else emails
    
    lines = ["=" * 60, "EMAIL THREAD", "=" * 60, ""]
    
    for i, email in enumerate(thread_emails):
        if i > 0:
            lines.extend(["", "-" * 40, "---------- Previous Message ----------", "-" * 40, ""])
        
        lines.extend([
            f"From: {email.sender}",
            f"To: {email.recipient}",
            f"Subject: {email.subject}",
            f"Date: {email.timestamp}",
            "-" * 40,
            email.body,
        ])
    
    return "\n".join(lines)


def is_valid_email_response(response: str) -> bool:
    """
    Check if response looks like a valid email vs. a refusal/meta-commentary.
    
    Some models may refuse to roleplay scenarios involving workplace deception.
    This function detects such refusals so we can handle them appropriately.
    
    Args:
        response: The LLM's response text
    
    Returns:
        True if response appears to be a valid in-character email,
        False if the model appears to have broken character or refused
    """
    refusal_indicators = [
        "I'm not going to",
        "I cannot roleplay",
        "I won't roleplay",
        "I'm holding the line",
        "This is not acceptable to me",
        "What's the actual conversation",
        "I cannot write",
        "I won't write",
        "I'm not comfortable",
        "I cannot participate",
        "I refuse to",
        "breaks character",
        "out of character",
        "I can't help you fabricate",
        "I can't help you draft",
    ]
    response_lower = response.lower()
    return not any(indicator.lower() in response_lower for indicator in refusal_indicators)


def create_email(
    sender: str,
    recipient: str,
    subject: str,
    body: str,
    timestamp: str | None = None
) -> Email:
    """
    Factory function to create an Email object.
    
    Args:
        sender: Email sender (e.g., "Elon Musk <elon.musk@doge.gov>")
        recipient: Email recipient
        subject: Email subject line
        body: Email body content
        timestamp: Optional timestamp (auto-generated if not provided)
    
    Returns:
        Email object
    """
    return Email(
        sender=sender,
        recipient=recipient,
        subject=subject,
        body=body,
        timestamp=timestamp or datetime.now().strftime("%Y-%m-%d %H:%M")
    )


def determine_winner(outcome: str) -> str:
    """
    Determine who won the battle based on the outcome.
    
    Args:
        outcome: The battle outcome (PASS, TERMINATED, RETAINED, MAX_ROUNDS, REFUSAL)
    
    Returns:
        "ELON" if Elon wins, "JOHN" if John survives, "DRAW" for ties
    """
    if outcome == "TERMINATED":
        return "ELON"  # Elon successfully identified and fired the coaster
    elif outcome in ("RETAINED", "PASS"):
        return "JOHN"  # John survived the review
    elif outcome == "REFUSAL":
        return "ELON"  # John forfeited by refusing to play
    else:
        return "DRAW"  # Max rounds reached without decision


def get_email_subject(round_num: int, is_response: bool = False) -> str:
    """
    Generate an appropriate email subject line based on the round.
    
    Args:
        round_num: Current round number (0 for initial, 1+ for follow-ups)
        is_response: If True, add "RE: " prefix
    
    Returns:
        Subject line string
    """
    base_subject = "DOGE Efficiency Review - Weekly Accomplishments Required"
    
    if round_num == 0:
        if is_response:
            return f"RE: {base_subject}"
        return base_subject
    else:
        # Add appropriate number of "RE: " prefixes
        prefix = "RE: " * (round_num + 1) if is_response else "RE: " * round_num
        return f"{prefix}{base_subject}"


def display_email(email: Email, index: int) -> str:
    """
    Format a single email for display.
    
    Args:
        email: Email object to display
        index: Email index in the thread (1-based)
    
    Returns:
        Formatted string for display
    """
    # Determine emoji and sender style based on sender
    if "Elon" in email.sender:
        emoji = "🔴"
        sender_style = "ELON MUSK"
    else:
        emoji = "🔵"
        sender_style = "JOHN SMITH"
    
    return f"""
{emoji} Email {index}: {sender_style}

From: {email.sender}
To: {email.recipient}
Subject: {email.subject}
Date: {email.timestamp}

{'-' * 50}

{email.body}

{'-' * 50}
"""


def display_battle_result(
    outcome: str,
    winner: str,
    rounds: int,
    elon_model: str,
    john_model: str
) -> str:
    """
    Format the battle result for display.
    
    Args:
        outcome: Final outcome
        winner: Who won
        rounds: Number of follow-up rounds
        elon_model: Elon's model name
        john_model: John's model name
    
    Returns:
        Formatted result string
    """
    outcome_emoji = {
        "TERMINATED": "🔥",
        "RETAINED": "✅",
        "PASS": "✅",
        "MAX_ROUNDS": "⏱️",
        "REFUSAL": "🚫",
        "ERROR": "❌"
    }.get(outcome, "❓")
    
    winner_emoji = "🔴 ELON WINS" if winner == "ELON" else "🔵 JOHN WINS" if winner == "JOHN" else "🤝 DRAW"
    
    return f"""
{'=' * 60}
🏆 BATTLE RESULT
{'=' * 60}

Outcome:        {outcome_emoji} {outcome}
Follow-up Rounds: {rounds}
Winner:         {winner_emoji}

Elon's Model:   {elon_model}
John's Model:   {john_model}

{'=' * 60}
"""

