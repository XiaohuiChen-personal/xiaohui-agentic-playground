"""Display formatting utilities for Sensei."""

import re
from datetime import datetime


def format_duration(minutes: int) -> str:
    """Format a duration in minutes to a human-readable string.
    
    Args:
        minutes: Duration in minutes.
    
    Returns:
        Formatted string like "1h 30m" or "45m".
    
    Examples:
        >>> format_duration(90)
        '1h 30m'
        >>> format_duration(45)
        '45m'
        >>> format_duration(120)
        '2h'
    """
    if minutes < 0:
        return "0m"
    
    hours = minutes // 60
    remaining_minutes = minutes % 60
    
    if hours == 0:
        return f"{remaining_minutes}m"
    elif remaining_minutes == 0:
        return f"{hours}h"
    else:
        return f"{hours}h {remaining_minutes}m"


def format_percentage(value: float) -> str:
    """Format a decimal value as a percentage string.
    
    Args:
        value: A value between 0 and 1.
    
    Returns:
        Formatted percentage string like "75%".
    
    Examples:
        >>> format_percentage(0.75)
        '75%'
        >>> format_percentage(0.333)
        '33%'
        >>> format_percentage(1.0)
        '100%'
    """
    # Clamp value between 0 and 1
    clamped = max(0.0, min(1.0, value))
    return f"{int(clamped * 100)}%"


def format_date(dt: datetime) -> str:
    """Format a datetime to a human-readable date string.
    
    Args:
        dt: A datetime object.
    
    Returns:
        Formatted string like "Jan 10, 2026".
    
    Examples:
        >>> format_date(datetime(2026, 1, 10))
        'Jan 10, 2026'
    """
    return dt.strftime("%b %d, %Y")


def format_datetime(dt: datetime) -> str:
    """Format a datetime to include time.
    
    Args:
        dt: A datetime object.
    
    Returns:
        Formatted string like "Jan 10, 2026 at 2:30 PM".
    """
    return dt.strftime("%b %d, %Y at %I:%M %p")


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate text to a maximum length with a suffix.
    
    Args:
        text: The text to truncate.
        max_length: Maximum length including suffix.
        suffix: String to append when truncating (default "...").
    
    Returns:
        Original text if shorter than max_length, otherwise truncated with suffix.
    
    Examples:
        >>> truncate_text("Hello World", 8)
        'Hello...'
        >>> truncate_text("Hi", 10)
        'Hi'
    """
    if len(text) <= max_length:
        return text
    
    # Account for suffix length
    truncate_at = max_length - len(suffix)
    if truncate_at <= 0:
        return suffix[:max_length]
    
    return text[:truncate_at] + suffix


def format_score(correct: int, total: int) -> str:
    """Format a quiz score.
    
    Args:
        correct: Number of correct answers.
        total: Total number of questions.
    
    Returns:
        Formatted string like "7/10 (70%)".
    """
    if total == 0:
        return "0/0 (0%)"
    
    percentage = int((correct / total) * 100)
    return f"{correct}/{total} ({percentage}%)"


def format_latex_for_streamlit(content: str) -> str:
    """Convert LaTeX delimiters to Streamlit-compatible format.
    
    ChatGPT and other LLMs often return LaTeX math formulas using:
    - \\(...\\) for inline math
    - \\[...\\] for display/block math
    
    Streamlit's st.markdown() expects:
    - $...$ for inline math
    - $$...$$ for block math
    
    This function converts the delimiters so formulas render correctly.
    
    Args:
        content: Text content potentially containing LaTeX formulas.
    
    Returns:
        Content with converted LaTeX delimiters.
    
    Examples:
        >>> format_latex_for_streamlit("The formula is \\\\(x^2\\\\)")
        'The formula is $x^2$'
        >>> format_latex_for_streamlit("Display: \\\\[E = mc^2\\\\]")
        'Display: $$E = mc^2$$'
    """
    if not content:
        return content
    
    # Convert display/block math: \[...\] -> $$...$$
    # Use non-greedy matching to handle multiple formulas
    content = re.sub(
        r'\\\[(.*?)\\\]',
        r'$$\1$$',
        content,
        flags=re.DOTALL,
    )
    
    # Convert inline math: \(...\) -> $...$
    # Use non-greedy matching to handle multiple formulas
    content = re.sub(
        r'\\\((.*?)\\\)',
        r'$\1$',
        content,
        flags=re.DOTALL,
    )
    
    return content
