"""Shared pytest fixtures and configuration for Sensei tests."""

import os
import tempfile
from pathlib import Path

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
                "order": 1,
                "estimated_minutes": 30,
                "concepts": [
                    {
                        "id": "concept-1",
                        "title": "Concept 1",
                        "content": "Content for concept 1",
                        "order": 1,
                        "status": "not_started",
                        "mastery": 0.0,
                    },
                    {
                        "id": "concept-2",
                        "title": "Concept 2",
                        "content": "Content for concept 2",
                        "order": 2,
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
