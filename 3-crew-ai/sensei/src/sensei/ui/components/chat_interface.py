"""Chat interface component for Sensei.

This module provides a chat UI for Q&A with the AI tutor including:
- Message history display
- Input field with send button
- User/assistant message styling
- Typing indicators
- LaTeX math formula rendering
"""

from typing import Callable

import streamlit as st

from sensei.models.enums import MessageRole
from sensei.models.schemas import ChatMessage
from sensei.utils.formatters import format_latex_for_streamlit


def render_chat(
    messages: list[ChatMessage] | list[dict],
    on_send: Callable[[str], None] | None = None,
    placeholder: str = "Ask Sensei a question...",
    disabled: bool = False,
    show_context_hint: bool = True,
) -> str | None:
    """Render a chat interface with message history and input.
    
    Args:
        messages: List of ChatMessage objects or dicts with 'role' and 'content'.
        on_send: Callback when a message is sent. Receives the message text.
        placeholder: Placeholder text for the input field.
        disabled: Whether the chat input is disabled.
        show_context_hint: Whether to show contextual hints above the chat.
    
    Returns:
        The submitted message text if one was sent, None otherwise.
    
    Example:
        ```python
        messages = [
            ChatMessage(role=MessageRole.USER, content="What is a thread block?"),
            ChatMessage(role=MessageRole.ASSISTANT, content="A thread block is..."),
        ]
        render_chat(messages, on_send=lambda msg: handle_question(msg))
        ```
    """
    # Chat header
    st.markdown("### 💬 Ask Sensei")
    
    if show_context_hint:
        st.caption("Questions about this concept? I'm here to help!")
    
    # Message history container
    chat_container = st.container()
    
    with chat_container:
        if not messages:
            _render_empty_chat()
        else:
            for message in messages:
                _render_message(message)
    
    st.markdown("---")
    
    # Input form
    submitted_message = _render_chat_input(
        on_send=on_send,
        placeholder=placeholder,
        disabled=disabled,
    )
    
    return submitted_message


def render_chat_compact(
    messages: list[ChatMessage] | list[dict],
    on_send: Callable[[str], None] | None = None,
    max_messages: int = 5,
) -> str | None:
    """Render a compact chat view with limited message history.
    
    Useful for embedding in smaller UI areas.
    
    Args:
        messages: List of chat messages.
        on_send: Callback when message is sent.
        max_messages: Maximum number of recent messages to display.
    
    Returns:
        Submitted message if any, None otherwise.
    """
    # Show only recent messages
    recent_messages = messages[-max_messages:] if len(messages) > max_messages else messages
    
    if len(messages) > max_messages:
        st.caption(f"Showing last {max_messages} messages...")
    
    # Messages
    for message in recent_messages:
        _render_message_compact(message)
    
    # Input
    return _render_chat_input(
        on_send=on_send,
        placeholder="Type a question...",
    )


def _render_message(message: ChatMessage | dict) -> None:
    """Render a single chat message with styling.
    
    Handles LaTeX math formulas by converting common delimiters
    (\\(...\\) and \\[...\\]) to Streamlit-compatible format ($...$ and $$...$$).
    
    Args:
        message: ChatMessage object or dict with role and content.
    """
    # Handle both ChatMessage objects and dicts
    # Use duck typing (hasattr) instead of isinstance to handle Streamlit hot reload
    # where objects created before reload fail isinstance checks
    if hasattr(message, "role") and hasattr(message, "content"):
        role = message.role
        content = message.content
    else:
        role_str = message.get("role", "assistant")
        if isinstance(role_str, MessageRole):
            role = role_str
        else:
            role = MessageRole(role_str) if role_str in ["user", "assistant", "system"] else MessageRole.ASSISTANT
        content = message.get("content", "")
    
    # Convert LaTeX delimiters for proper rendering
    formatted_content = format_latex_for_streamlit(content)
    
    # Use Streamlit's native chat message component
    if role == MessageRole.USER:
        with st.chat_message("user", avatar="👤"):
            st.markdown(formatted_content)
    elif role == MessageRole.ASSISTANT:
        with st.chat_message("assistant", avatar="🥋"):
            st.markdown(formatted_content)
    else:
        # System message - display as info
        st.info(formatted_content)


def _render_message_compact(message: ChatMessage | dict) -> None:
    """Render a message in compact format.
    
    Note: Compact format uses unsafe_allow_html for styling, which means
    LaTeX formulas won't render properly in this view. For full LaTeX
    support, use the standard _render_message function.
    
    Args:
        message: ChatMessage object or dict.
    """
    # Use duck typing instead of isinstance to handle Streamlit hot reload
    if hasattr(message, "role") and hasattr(message, "content"):
        role = message.role
        content = message.content
    else:
        role_str = message.get("role", "assistant")
        role = MessageRole(role_str) if isinstance(role_str, str) and role_str in ["user", "assistant", "system"] else MessageRole.ASSISTANT
        content = message.get("content", "")
    
    icon = "👤" if role == MessageRole.USER else "🥋"
    role_label = "You" if role == MessageRole.USER else "Sensei"
    
    # Truncate long messages (LaTeX not supported in compact HTML view)
    display_content = content[:200] + "..." if len(content) > 200 else content
    
    st.markdown(
        f"""
        <div style="
            padding: 0.5rem;
            margin: 0.25rem 0;
            border-radius: 8px;
            background: {'#e3f2fd' if role == MessageRole.USER else '#f5f5f5'};
        ">
            <strong>{icon} {role_label}:</strong> {display_content}
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_chat_input(
    on_send: Callable[[str], None] | None = None,
    placeholder: str = "Type your message...",
    disabled: bool = False,
) -> str | None:
    """Render the chat input field with send button.
    
    Args:
        on_send: Callback when message is sent.
        placeholder: Input placeholder text.
        disabled: Whether input is disabled.
    
    Returns:
        The submitted message if any.
    """
    # Use Streamlit's chat input for better UX
    if prompt := st.chat_input(placeholder, disabled=disabled, key="chat_input"):
        if on_send:
            on_send(prompt)
        return prompt
    
    return None


def _render_empty_chat() -> None:
    """Render empty chat state with helpful suggestions."""
    st.markdown(
        """
        <div style="
            text-align: center;
            padding: 2rem;
            background: #f8f9fa;
            border-radius: 10px;
            margin: 1rem 0;
        ">
            <span style="font-size: 2rem;">🥋</span>
            <p style="color: #6c757d; margin-top: 0.5rem;">
                No questions yet. Feel free to ask anything!
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # Suggested questions
    st.caption("Try asking:")
    suggestions = [
        "Can you explain this in simpler terms?",
        "What's a real-world example of this?",
        "Why is this important?",
        "How does this relate to what I learned before?",
    ]
    
    cols = st.columns(2)
    for idx, suggestion in enumerate(suggestions):
        with cols[idx % 2]:
            st.markdown(f"• *{suggestion}*")


def render_typing_indicator() -> None:
    """Render a typing indicator for when AI is generating a response."""
    st.markdown(
        """
        <div style="
            display: flex;
            align-items: center;
            padding: 0.5rem 1rem;
            background: #f0f0f0;
            border-radius: 1rem;
            width: fit-content;
            margin: 0.5rem 0;
        ">
            <span style="margin-right: 0.5rem;">🥋</span>
            <span style="color: #6c757d;">Sensei is typing</span>
            <span class="typing-dots">...</span>
        </div>
        <style>
        .typing-dots {
            animation: blink 1.4s infinite both;
        }
        @keyframes blink {
            0% { opacity: .2; }
            20% { opacity: 1; }
            100% { opacity: .2; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_chat_error(error_message: str) -> None:
    """Render an error message in the chat.
    
    Args:
        error_message: The error message to display.
    """
    st.error(f"🥋 Sorry, I encountered an issue: {error_message}")
    st.caption("Please try again or rephrase your question.")


def render_chat_with_form(
    messages: list[ChatMessage] | list[dict],
    on_send: Callable[[str], None] | None = None,
    form_key: str = "chat_form",
) -> str | None:
    """Render chat with a form-based input (alternative to chat_input).
    
    This version uses a form which allows for more control over submission.
    
    Args:
        messages: List of chat messages.
        on_send: Callback when message is sent.
        form_key: Unique key for the form.
    
    Returns:
        Submitted message if any.
    """
    # Message history
    for message in messages:
        _render_message(message)
    
    if not messages:
        _render_empty_chat()
    
    st.markdown("---")
    
    # Form-based input
    with st.form(key=form_key, clear_on_submit=True):
        col1, col2 = st.columns([5, 1])
        
        with col1:
            user_input = st.text_input(
                "Your question",
                placeholder="Ask Sensei a question...",
                label_visibility="collapsed",
            )
        
        with col2:
            submitted = st.form_submit_button("Send", use_container_width=True)
        
        if submitted and user_input.strip():
            if on_send:
                on_send(user_input.strip())
            return user_input.strip()
    
    return None
