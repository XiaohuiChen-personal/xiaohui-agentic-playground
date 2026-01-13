"""Session state utilities for Streamlit."""

from typing import Any

import streamlit as st


def initialize_session_state() -> None:
    """Initialize default session state values.
    
    Call this at the start of the app to ensure all required
    state keys exist with sensible defaults.
    """
    defaults = {
        # Services (will be initialized lazily)
        "services": {},
        
        # User state
        "user": {
            "preferences": None,
            "is_onboarded": False,
        },
        
        # Course state
        "courses": {
            "list": [],
            "current_course_id": None,
        },
        
        # Learning session state
        "learning": {
            "session": None,
            "current_concept": None,
            "chat_history": [],
            "module_complete": False,
        },
        
        # Quiz state
        "quiz": {
            "current_quiz": None,
            "current_question_idx": 0,
            "answers": {},
            "results": None,
        },
        
        # UI state
        "ui": {
            "current_page": "dashboard",
            "sidebar_expanded": True,
            "show_course_outline": False,
        },
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def get_state(key: str, default: Any = None) -> Any:
    """Get a value from session state.
    
    Args:
        key: The key to retrieve. Supports dot notation for nested keys
             (e.g., "user.preferences").
        default: Value to return if key doesn't exist.
    
    Returns:
        The value at the key, or default if not found.
    """
    keys = key.split(".")
    value = st.session_state
    
    for k in keys:
        if isinstance(value, dict):
            value = value.get(k)
        elif hasattr(value, k):
            value = getattr(value, k, None)
        else:
            return default
        
        if value is None:
            return default
    
    return value


def set_state(key: str, value: Any) -> None:
    """Set a value in session state.
    
    Args:
        key: The key to set. Supports dot notation for nested keys
             (e.g., "user.preferences").
        value: The value to store.
    """
    keys = key.split(".")
    
    if len(keys) == 1:
        st.session_state[key] = value
        return
    
    # Navigate to parent and set the final key
    parent = st.session_state
    for k in keys[:-1]:
        if isinstance(parent, dict):
            if k not in parent:
                parent[k] = {}
            parent = parent[k]
        else:
            if not hasattr(parent, k):
                setattr(parent, k, {})
            parent = getattr(parent, k)
    
    final_key = keys[-1]
    if isinstance(parent, dict):
        parent[final_key] = value
    else:
        setattr(parent, final_key, value)


def clear_state(key: str) -> None:
    """Remove a key from session state.
    
    Args:
        key: The key to remove. Supports dot notation for nested keys.
    """
    keys = key.split(".")
    
    if len(keys) == 1:
        if key in st.session_state:
            del st.session_state[key]
        return
    
    # Navigate to parent and delete the final key
    parent = st.session_state
    for k in keys[:-1]:
        if isinstance(parent, dict):
            parent = parent.get(k)
        else:
            parent = getattr(parent, k, None)
        
        if parent is None:
            return
    
    final_key = keys[-1]
    if isinstance(parent, dict) and final_key in parent:
        del parent[final_key]
    elif hasattr(parent, final_key):
        delattr(parent, final_key)
