"""Configuration and fixtures for functional tests.

Functional tests call actual LLM APIs and are:
- Non-deterministic (LLM outputs vary)
- Slow (API latency)
- Costly (incur token costs)

These tests should be run manually or in pre-release, not in CI.
"""

import os

import pytest

from sensei.utils.constants import load_environment


# Load environment variables
load_environment()


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers",
        "functional: mark test as functional test (requires real API keys)",
    )


@pytest.fixture(scope="session")
def has_api_keys():
    """Check if required API keys are available.
    
    Returns:
        True if all required keys are present.
    """
    required_keys = ["OPENAI_API_KEY"]
    optional_keys = ["ANTHROPIC_API_KEY", "GOOGLE_API_KEY"]
    
    has_required = all(os.getenv(key) for key in required_keys)
    has_optional = any(os.getenv(key) for key in optional_keys)
    
    return has_required and has_optional


@pytest.fixture(scope="session")
def skip_if_no_keys(has_api_keys):
    """Skip test if API keys are not available."""
    if not has_api_keys:
        pytest.skip("API keys not available for functional tests")


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
