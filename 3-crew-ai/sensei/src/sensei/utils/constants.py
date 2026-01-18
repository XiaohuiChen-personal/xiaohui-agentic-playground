"""Application-wide constants for Sensei.

This module also handles environment variable loading for API keys.
Call `load_environment()` at application startup before using any crews.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent  # sensei/
WORKSPACE_ROOT = PROJECT_ROOT.parent.parent  # xiaohui-agentic-playground/
DATA_DIR = PROJECT_ROOT / "data"


def load_environment() -> bool:
    """Load environment variables from .env file.
    
    Looks for .env file in the workspace root directory
    (xiaohui-agentic-playground/), which is shared across all projects.
    
    This function should be called at application startup, before
    any CrewAI crews are instantiated.
    
    Returns:
        True if .env file was found and loaded, False otherwise.
    
    Required environment variables for Sensei:
        - GOOGLE_API_KEY: For Gemini models (Curriculum Architect)
        - ANTHROPIC_API_KEY: For Claude models (Content Researcher)
        - OPENAI_API_KEY: For OpenAI models (future crews)
    
    Example:
        ```python
        from sensei.utils.constants import load_environment
        
        # Call at app startup
        load_environment()
        
        # Now crews can be instantiated
        from sensei.crews import CurriculumCrew
        crew = CurriculumCrew()
        ```
    """
    env_path = WORKSPACE_ROOT / ".env"
    
    if env_path.exists():
        load_dotenv(env_path)
        return True
    
    # Also try project-specific .env as fallback
    project_env_path = PROJECT_ROOT / ".env"
    if project_env_path.exists():
        load_dotenv(project_env_path)
        return True
    
    return False


def get_api_key(provider: str) -> str | None:
    """Get API key for a specific provider.
    
    Args:
        provider: One of 'openai', 'anthropic', 'google'.
    
    Returns:
        The API key if set, None otherwise.
    """
    key_names = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "google": "GOOGLE_API_KEY",
    }
    
    key_name = key_names.get(provider.lower())
    if key_name:
        return os.environ.get(key_name)
    return None


def check_required_api_keys() -> dict[str, bool]:
    """Check which API keys are configured.
    
    Returns:
        Dictionary mapping provider names to whether their API key is set.
    
    Example:
        ```python
        from sensei.utils.constants import check_required_api_keys
        
        keys = check_required_api_keys()
        if not keys['google']:
            print("Warning: GOOGLE_API_KEY not set - Gemini models won't work")
        ```
    """
    return {
        "openai": bool(os.environ.get("OPENAI_API_KEY")),
        "anthropic": bool(os.environ.get("ANTHROPIC_API_KEY")),
        "google": bool(os.environ.get("GOOGLE_API_KEY")),
    }
COURSES_DIR = DATA_DIR / "courses"
DATABASE_PATH = DATA_DIR / "sensei.db"
USER_PREFERENCES_PATH = DATA_DIR / "user_preferences.json"
CHAT_HISTORY_PATH = DATA_DIR / "chat_history.json"

# Defaults
DEFAULT_SESSION_LENGTH = 30  # minutes
DEFAULT_QUIZ_QUESTIONS = 5  # questions per quiz

# Thresholds
QUIZ_PASS_THRESHOLD = 0.8  # 80% to pass

# Limits
MAX_THREADS_PER_BLOCK = 1024  # Example from CUDA course
MAX_CHAT_HISTORY = 50  # messages to keep in memory
