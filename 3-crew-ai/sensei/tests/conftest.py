"""Shared pytest fixtures and configuration for Sensei tests."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.fixture
def temp_data_dir(tmp_path: Path) -> Path:
    """Create a temporary data directory for tests.
    
    Returns:
        Path to temporary data directory with courses subdirectory.
    """
    courses_dir = tmp_path / "courses"
    courses_dir.mkdir()
    return tmp_path


@pytest.fixture
def mock_user_preferences() -> dict:
    """Return mock user preferences for testing."""
    return {
        "name": "Test User",
        "learning_style": "reading",
        "session_length_minutes": 30,
        "experience_level": "intermediate",
        "goals": "Learn for testing purposes",
        "is_onboarded": True,
    }


@pytest.fixture
def mock_course_data() -> dict:
    """Return mock course data for testing."""
    return {
        "id": "test-course-123",
        "title": "Test Course",
        "description": "A course for testing",
        "created_at": "2026-01-10T10:00:00",
        "modules": [
            {
                "id": "module-1",
                "title": "Module 1",
                "description": "First module",
                "order": 0,
                "estimated_minutes": 30,
                "concepts": [
                    {
                        "id": "concept-1",
                        "title": "Concept 1",
                        "content": "Content for concept 1",
                        "order": 0,
                        "status": "not_started",
                        "mastery": 0.0,
                    },
                    {
                        "id": "concept-2",
                        "title": "Concept 2",
                        "content": "Content for concept 2",
                        "order": 1,
                        "status": "not_started",
                        "mastery": 0.0,
                    },
                ],
            },
            {
                "id": "module-2",
                "title": "Module 2",
                "description": "Second module",
                "order": 1,
                "estimated_minutes": 45,
                "concepts": [
                    {
                        "id": "concept-3",
                        "title": "Concept 3",
                        "content": "Content for concept 3",
                        "order": 0,
                        "status": "not_started",
                        "mastery": 0.0,
                    },
                ],
            },
        ],
    }


@pytest.fixture
def mock_quiz_data() -> dict:
    """Return mock quiz data for testing."""
    return {
        "id": "quiz-123",
        "module_id": "module-1",
        "created_at": "2026-01-10T10:00:00",
        "questions": [
            {
                "id": "q1",
                "question": "What is 2 + 2?",
                "question_type": "multiple_choice",
                "options": ["3", "4", "5", "6"],
                "correct_answer": "4",
                "explanation": "2 + 2 equals 4",
                "concept_id": "concept-1",
                "difficulty": 1,
            },
            {
                "id": "q2",
                "question": "Is the sky blue?",
                "question_type": "true_false",
                "options": ["True", "False"],
                "correct_answer": "True",
                "explanation": "The sky appears blue due to light scattering",
                "concept_id": "concept-1",
                "difficulty": 1,
            },
        ],
    }


@pytest.fixture
def mock_progress_data() -> dict:
    """Return mock progress data for testing."""
    return {
        "course_id": "test-course-123",
        "completion_percentage": 0.5,
        "modules_completed": 1,
        "total_modules": 2,
        "concepts_completed": 2,
        "total_concepts": 3,
        "time_spent_minutes": 45,
        "current_module_idx": 1,
        "current_concept_idx": 0,
    }


@pytest.fixture
def mock_quiz_result() -> dict:
    """Return mock quiz result data for testing."""
    return {
        "course_id": "test-course-123",
        "module_id": "module-1",
        "module_title": "Module 1",
        "quiz_id": "quiz-123",
        "score": 0.8,
        "correct_count": 4,
        "total_questions": 5,
        "weak_concepts": ["concept-2"],
        "feedback": "Good progress!",
        "passed": True,
    }


@pytest.fixture
def mock_chat_messages() -> list:
    """Return mock chat messages for testing."""
    return [
        {"role": "user", "content": "What is machine learning?"},
        {"role": "assistant", "content": "Machine learning is a subset of AI..."},
        {"role": "user", "content": "Can you give an example?"},
        {"role": "assistant", "content": "Sure! A common example is spam detection..."},
    ]


# ============================================================================
# Storage Test Fixtures
# ============================================================================

@pytest.fixture
def temp_db(tmp_path: Path):
    """Create a temporary database for testing.
    
    Returns:
        Database instance with temporary SQLite file.
    """
    from sensei.storage.database import Database
    
    db_path = tmp_path / "test.db"
    db = Database(db_path=db_path)
    return db


@pytest.fixture
def mock_database(tmp_path: Path):
    """Create a mock database for service testing.
    
    Alias for temp_db with a more service-oriented name.
    
    Returns:
        Database instance with temporary SQLite file.
    """
    from sensei.storage.database import Database
    
    db_path = tmp_path / "test_services.db"
    db = Database(db_path=db_path)
    return db


@pytest.fixture
def mock_file_storage_paths(tmp_path: Path, monkeypatch):
    """Mock file storage paths to use temporary directory.
    
    This fixture patches the module-level path constants in file_storage
    to use temporary directories for isolated testing.
    """
    import sensei.storage.file_storage as fs
    
    data_dir = tmp_path / "data"
    courses_dir = data_dir / "courses"
    courses_dir.mkdir(parents=True)
    
    # Patch the module constants
    monkeypatch.setattr(fs, "DATA_DIR", data_dir)
    monkeypatch.setattr(fs, "COURSES_DIR", courses_dir)
    monkeypatch.setattr(fs, "USER_PREFERENCES_PATH", data_dir / "user_preferences.json")
    monkeypatch.setattr(fs, "CHAT_HISTORY_PATH", data_dir / "chat_history.json")
    
    return {
        "data_dir": data_dir,
        "courses_dir": courses_dir,
        "user_preferences_path": data_dir / "user_preferences.json",
        "chat_history_path": data_dir / "chat_history.json",
    }


@pytest.fixture
def mock_memory_paths(tmp_path: Path, monkeypatch):
    """Mock memory manager paths to use temporary directory."""
    import sensei.storage.memory_manager as mm
    from sensei.utils.constants import DATA_DIR
    
    data_dir = tmp_path / "data"
    memory_dir = data_dir / "memory"
    db_path = data_dir / "sensei.db"
    
    data_dir.mkdir(parents=True)
    
    # Patch the module constants
    monkeypatch.setattr(mm, "MEMORY_DIR", memory_dir)
    monkeypatch.setattr(mm, "DATA_DIR", data_dir)
    monkeypatch.setattr(mm, "DATABASE_PATH", db_path)
    
    return {
        "data_dir": data_dir,
        "memory_dir": memory_dir,
        "db_path": db_path,
    }
