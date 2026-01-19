"""Configuration and fixtures for functional tests.

Functional tests call actual LLM APIs and are:
- Non-deterministic (LLM outputs vary)
- Slow (API latency)
- Costly (incur token costs)

These tests should be run manually or in pre-release, not in CI.

LangSmith Integration:
    If LANGSMITH_API_KEY is set, traces will be sent to LangSmith
    for observability. Set LANGSMITH_PROJECT to organize traces.

Memory Isolation:
    CrewAI memory is cleared before each test to ensure test isolation
    and prevent cross-test contamination.
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
    - GOOGLE_API_KEY: For Gemini models (content_researcher)
    - ANTHROPIC_API_KEY: For Claude models (curriculum_architect, knowledge_teacher, quiz_designer)
    - OPENAI_API_KEY: For GPT models (qa_mentor, performance_analyst) and embeddings
    
    Returns:
        True if all required keys are present.
    """
    required_keys = [
        "GOOGLE_API_KEY",      # Gemini - content_researcher
        "ANTHROPIC_API_KEY",   # Claude - curriculum_architect, knowledge_teacher, quiz_designer
        "OPENAI_API_KEY",      # GPT - qa_mentor, performance_analyst, and embeddings
    ]
    
    return all(os.getenv(key) for key in required_keys)


@pytest.fixture(scope="session")
def skip_if_no_keys(has_api_keys):
    """Skip test if API keys are not available."""
    if not has_api_keys:
        missing_keys = []
        if not os.getenv("GOOGLE_API_KEY"):
            missing_keys.append("GOOGLE_API_KEY (for Gemini - content_researcher)")
        if not os.getenv("ANTHROPIC_API_KEY"):
            missing_keys.append("ANTHROPIC_API_KEY (for Claude - curriculum_architect, knowledge_teacher, quiz_designer)")
        if not os.getenv("OPENAI_API_KEY"):
            missing_keys.append("OPENAI_API_KEY (for GPT - qa_mentor, performance_analyst, embeddings)")
        
        missing_str = "\n  - ".join(missing_keys)
        pytest.skip(f"Missing required API keys for functional tests:\n  - {missing_str}")


def check_api_keys_at_startup():
    """Check and report API key status at test session start.
    
    This is called during conftest loading to provide early feedback
    about missing API keys.
    """
    required = {
        "GOOGLE_API_KEY": "Gemini (content_researcher)",
        "ANTHROPIC_API_KEY": "Claude (curriculum_architect, knowledge_teacher, quiz_designer)",
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


@pytest.fixture(autouse=True)
def clean_crewai_memory():
    """Clean CrewAI memory before each functional test.
    
    This ensures test isolation by clearing any persistent memory
    that CrewAI stores between crew executions. Without this,
    memories from one test could influence another test's results.
    
    The fixture runs automatically before each test (autouse=True)
    and clears memory both before and after to ensure clean state.
    """
    from sensei.storage.memory_manager import clear_all_memory
    
    # Clean before test
    clear_all_memory()
    
    yield
    
    # Clean after test (optional, but ensures no leftover state)
    clear_all_memory()


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
