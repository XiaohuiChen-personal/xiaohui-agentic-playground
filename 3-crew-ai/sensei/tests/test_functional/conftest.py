"""Configuration and fixtures for functional tests.

Functional tests call actual LLM APIs and are:
- Non-deterministic (LLM outputs vary)
- Slow (API latency)
- Costly (incur token costs)

These tests should be run manually or in pre-release, not in CI.

LangSmith Integration:
    If LANGSMITH_API_KEY is set, traces will be sent to LangSmith
    for observability. Set LANGSMITH_PROJECT to organize traces.
"""

import os

import pytest

from sensei.utils.constants import load_environment


# Load environment variables AND initialize LangSmith tracing
# This must happen BEFORE any CrewAI imports
load_environment(init_tracing=True)


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers",
        "functional: mark test as functional test (requires real API keys)",
    )


@pytest.fixture(scope="session")
def has_api_keys():
    """Check if required API keys are available.
    
    All three keys are REQUIRED for functional tests:
    - GOOGLE_API_KEY: For Gemini models (curriculum_architect)
    - ANTHROPIC_API_KEY: For Claude models (content_researcher, knowledge_teacher, quiz_designer)
    - OPENAI_API_KEY: For GPT models (qa_mentor, performance_analyst) and embeddings
    
    Returns:
        True if all required keys are present.
    """
    required_keys = [
        "GOOGLE_API_KEY",      # Gemini - curriculum_architect
        "ANTHROPIC_API_KEY",   # Claude - content_researcher, knowledge_teacher, quiz_designer
        "OPENAI_API_KEY",      # GPT - qa_mentor, performance_analyst, and embeddings
    ]
    
    return all(os.getenv(key) for key in required_keys)


@pytest.fixture(scope="session")
def skip_if_no_keys(has_api_keys):
    """Skip test if API keys are not available."""
    if not has_api_keys:
        missing_keys = []
        if not os.getenv("GOOGLE_API_KEY"):
            missing_keys.append("GOOGLE_API_KEY (for Gemini models)")
        if not os.getenv("ANTHROPIC_API_KEY"):
            missing_keys.append("ANTHROPIC_API_KEY (for Claude models)")
        if not os.getenv("OPENAI_API_KEY"):
            missing_keys.append("OPENAI_API_KEY (for GPT models and embeddings)")
        
        missing_str = "\n  - ".join(missing_keys)
        pytest.skip(f"Missing required API keys for functional tests:\n  - {missing_str}")


def check_api_keys_at_startup():
    """Check and report API key status at test session start.
    
    This is called during conftest loading to provide early feedback
    about missing API keys.
    """
    required = {
        "GOOGLE_API_KEY": "Gemini (curriculum_architect)",
        "ANTHROPIC_API_KEY": "Claude (content_researcher, knowledge_teacher, quiz_designer)",
        "OPENAI_API_KEY": "GPT (qa_mentor, performance_analyst) + embeddings",
    }
    
    missing = []
    for key, usage in required.items():
        if not os.getenv(key):
            missing.append(f"{key}: {usage}")
    
    if missing:
        import warnings
        warnings.warn(
            f"\n⚠️ Missing API keys for functional tests:\n" +
            "\n".join(f"  - {m}" for m in missing) +
            "\n\nFunctional tests will be skipped unless all keys are set.",
            UserWarning
        )


# Check API keys when conftest is loaded
check_api_keys_at_startup()


@pytest.fixture(scope="module")
def functional_database(tmp_path_factory):
    """Create a database for functional tests.
    
    Uses a temporary directory to isolate functional test data.
    """
    from sensei.storage.database import Database
    
    tmp_dir = tmp_path_factory.mktemp("functional_data")
    db_path = tmp_dir / "functional_test.db"
    
    return Database(str(db_path))


@pytest.fixture(scope="module")
def functional_file_paths(tmp_path_factory, monkeypatch_module):
    """Set up file paths for functional tests."""
    from sensei.storage import file_storage
    
    tmp_dir = tmp_path_factory.mktemp("functional_files")
    courses_dir = tmp_dir / "courses"
    courses_dir.mkdir(parents=True)
    
    monkeypatch_module.setattr(file_storage, "DATA_DIR", str(tmp_dir))
    monkeypatch_module.setattr(file_storage, "COURSES_DIR", str(courses_dir))
    monkeypatch_module.setattr(
        file_storage, "USER_PREFERENCES_PATH", str(tmp_dir / "user_preferences.json")
    )
    
    return {
        "data_dir": tmp_dir,
        "courses_dir": courses_dir,
    }


@pytest.fixture(scope="module")
def monkeypatch_module():
    """Module-scoped monkeypatch fixture."""
    from _pytest.monkeypatch import MonkeyPatch
    mp = MonkeyPatch()
    yield mp
    mp.undo()
