"""Pytest fixtures for UI component testing.

These fixtures provide mocked Streamlit objects for testing UI components
without requiring a running Streamlit session.
"""

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from sensei.models.enums import MessageRole, ConceptStatus, QuestionType
from sensei.models.schemas import (
    ChatMessage,
    Progress,
    QuizQuestion,
    AnswerResult,
    QuizResult,
)


# ============================================================================
# Streamlit Mock Fixtures
# ============================================================================

@pytest.fixture
def mock_streamlit():
    """Create a comprehensive mock for Streamlit.
    
    Returns a MagicMock that can be used to patch 'streamlit' imports.
    Includes common Streamlit functions pre-configured.
    """
    mock_st = MagicMock()
    
    # Configure session_state as a dict-like object
    mock_st.session_state = {}
    
    # Configure column context managers - dynamically return the right number
    def create_columns(spec):
        """Create the right number of mock columns based on spec."""
        if isinstance(spec, int):
            num_cols = spec
        elif isinstance(spec, (list, tuple)):
            num_cols = len(spec)
        else:
            num_cols = 2  # default
        
        cols = []
        for _ in range(num_cols):
            mock_col = MagicMock()
            mock_col.__enter__ = MagicMock(return_value=mock_col)
            mock_col.__exit__ = MagicMock(return_value=False)
            cols.append(mock_col)
        return cols
    
    mock_st.columns.side_effect = create_columns
    
    # Configure container context manager
    mock_container = MagicMock()
    mock_container.__enter__ = MagicMock(return_value=mock_container)
    mock_container.__exit__ = MagicMock(return_value=False)
    mock_st.container.return_value = mock_container
    
    # Configure sidebar context manager
    mock_sidebar = MagicMock()
    mock_sidebar.__enter__ = MagicMock(return_value=mock_sidebar)
    mock_sidebar.__exit__ = MagicMock(return_value=False)
    mock_st.sidebar = mock_sidebar
    
    # Configure expander context manager
    mock_expander = MagicMock()
    mock_expander.__enter__ = MagicMock(return_value=mock_expander)
    mock_expander.__exit__ = MagicMock(return_value=False)
    mock_st.expander.return_value = mock_expander
    
    # Configure form context manager
    mock_form = MagicMock()
    mock_form.__enter__ = MagicMock(return_value=mock_form)
    mock_form.__exit__ = MagicMock(return_value=False)
    mock_st.form.return_value = mock_form
    
    # Configure chat_message context manager
    mock_chat_msg = MagicMock()
    mock_chat_msg.__enter__ = MagicMock(return_value=mock_chat_msg)
    mock_chat_msg.__exit__ = MagicMock(return_value=False)
    mock_st.chat_message.return_value = mock_chat_msg
    
    # Configure button to return False by default
    mock_st.button.return_value = False
    
    # Configure radio to return the first option index by default
    mock_st.radio.return_value = 0
    
    # Configure text_input to return empty string by default
    mock_st.text_input.return_value = ""
    
    # Configure chat_input to return None by default
    mock_st.chat_input.return_value = None
    
    # Configure form_submit_button to return False by default
    mock_st.form_submit_button.return_value = False
    
    # Configure empty to return a MagicMock
    mock_st.empty.return_value = MagicMock()
    
    # Configure divider
    mock_st.divider.return_value = None
    
    return mock_st


@pytest.fixture
def mock_streamlit_with_button_click(mock_streamlit):
    """Mock Streamlit with button click returning True."""
    mock_streamlit.button.return_value = True
    return mock_streamlit


@pytest.fixture
def mock_streamlit_with_chat_input(mock_streamlit):
    """Mock Streamlit with chat input returning a message."""
    mock_streamlit.chat_input.return_value = "Test message from user"
    return mock_streamlit


# ============================================================================
# Course Data Fixtures
# ============================================================================

@pytest.fixture
def sample_course_outline():
    """Sample course data for testing sidebar and course cards."""
    return {
        "id": "test-course-123",
        "title": "Python Basics",
        "description": "Learn Python programming from scratch",
        "total_modules": 3,
        "total_concepts": 9,
        "modules": [
            {
                "id": "module-1",
                "title": "Introduction",
                "description": "Getting started with Python",
                "order": 0,
                "estimated_minutes": 30,
                "concepts": [
                    {"id": "c1", "title": "What is Python?", "status": "completed"},
                    {"id": "c2", "title": "Installing Python", "status": "completed"},
                    {"id": "c3", "title": "Hello World", "status": "in_progress"},
                ],
            },
            {
                "id": "module-2",
                "title": "Variables and Types",
                "description": "Understanding data types",
                "order": 1,
                "estimated_minutes": 45,
                "concepts": [
                    {"id": "c4", "title": "Variables", "status": "not_started"},
                    {"id": "c5", "title": "Numbers", "status": "not_started"},
                    {"id": "c6", "title": "Strings", "status": "not_started"},
                ],
            },
            {
                "id": "module-3",
                "title": "Control Flow",
                "description": "Conditional statements and loops",
                "order": 2,
                "estimated_minutes": 60,
                "concepts": [
                    {"id": "c7", "title": "If Statements", "status": "not_started"},
                    {"id": "c8", "title": "For Loops", "status": "not_started"},
                    {"id": "c9", "title": "While Loops", "status": "not_started"},
                ],
            },
        ],
    }


@pytest.fixture
def sample_course_minimal():
    """Minimal course data for edge case testing."""
    return {
        "id": "minimal-course",
        "title": "Minimal Course",
    }


@pytest.fixture
def sample_course_empty_modules():
    """Course with empty modules list."""
    return {
        "id": "empty-modules-course",
        "title": "Empty Modules Course",
        "modules": [],
    }


# ============================================================================
# Progress Fixtures
# ============================================================================

@pytest.fixture
def sample_progress_zero():
    """Progress object with 0% completion."""
    return Progress(
        course_id="test-course-123",
        completion_percentage=0.0,
        modules_completed=0,
        total_modules=3,
        concepts_completed=0,
        total_concepts=9,
        time_spent_minutes=0,
        current_module_idx=0,
        current_concept_idx=0,
    )


@pytest.fixture
def sample_progress_partial():
    """Progress object with partial completion."""
    return Progress(
        course_id="test-course-123",
        completion_percentage=0.5,
        modules_completed=1,
        total_modules=3,
        concepts_completed=4,
        total_concepts=9,
        time_spent_minutes=45,
        current_module_idx=1,
        current_concept_idx=1,
    )


@pytest.fixture
def sample_progress_complete():
    """Progress object with 100% completion."""
    return Progress(
        course_id="test-course-123",
        completion_percentage=1.0,
        modules_completed=3,
        total_modules=3,
        concepts_completed=9,
        total_concepts=9,
        time_spent_minutes=120,
        current_module_idx=2,
        current_concept_idx=2,
    )


# ============================================================================
# Chat Fixtures
# ============================================================================

@pytest.fixture
def sample_chat_messages_empty():
    """Empty chat message list."""
    return []


@pytest.fixture
def sample_chat_messages():
    """Sample chat messages as ChatMessage objects."""
    return [
        ChatMessage(role=MessageRole.USER, content="What is a variable?"),
        ChatMessage(role=MessageRole.ASSISTANT, content="A variable is a named storage location..."),
        ChatMessage(role=MessageRole.USER, content="Can you give an example?"),
        ChatMessage(role=MessageRole.ASSISTANT, content="Sure! Here's an example: x = 5"),
    ]


@pytest.fixture
def sample_chat_messages_dict():
    """Sample chat messages as dictionaries."""
    return [
        {"role": "user", "content": "What is a variable?"},
        {"role": "assistant", "content": "A variable is a named storage location..."},
        {"role": "user", "content": "Can you give an example?"},
        {"role": "assistant", "content": "Sure! Here's an example: x = 5"},
    ]


@pytest.fixture
def sample_chat_message_system():
    """Chat message with system role."""
    return ChatMessage(role=MessageRole.SYSTEM, content="System initialization message")


# ============================================================================
# Quiz Fixtures
# ============================================================================

@pytest.fixture
def sample_quiz_question_mc():
    """Sample multiple choice question."""
    return QuizQuestion(
        id="q1",
        question="What is 2 + 2?",
        question_type=QuestionType.MULTIPLE_CHOICE,
        options=["3", "4", "5", "6"],
        correct_answer="4",
        explanation="2 + 2 equals 4 by basic arithmetic.",
        concept_id="concept-1",
        difficulty=1,
    )


@pytest.fixture
def sample_quiz_question_tf():
    """Sample true/false question."""
    return QuizQuestion(
        id="q2",
        question="Python is a compiled language.",
        question_type=QuestionType.TRUE_FALSE,
        options=["True", "False"],
        correct_answer="False",
        explanation="Python is an interpreted language.",
        concept_id="concept-1",
        difficulty=1,
    )


@pytest.fixture
def sample_quiz_question_dict():
    """Sample quiz question as dictionary."""
    return {
        "id": "q3",
        "question": "What keyword is used to define a function?",
        "question_type": "multiple_choice",
        "options": ["func", "def", "function", "define"],
        "correct_answer": "def",
        "explanation": "In Python, 'def' is used to define functions.",
        "concept_id": "concept-2",
        "difficulty": 1,
    }


@pytest.fixture
def sample_answer_result_correct():
    """Sample correct answer result."""
    return AnswerResult(
        question_id="q1",
        user_answer="4",
        is_correct=True,
        correct_answer="4",
        explanation="2 + 2 equals 4.",
    )


@pytest.fixture
def sample_answer_result_incorrect():
    """Sample incorrect answer result."""
    return AnswerResult(
        question_id="q1",
        user_answer="5",
        is_correct=False,
        correct_answer="4",
        explanation="2 + 2 equals 4, not 5.",
    )


@pytest.fixture
def sample_quiz_result_pass():
    """Sample passing quiz result."""
    return QuizResult(
        quiz_id="quiz-123",
        score=0.85,
        correct_count=17,
        total_questions=20,
        weak_concepts=["concept-3"],
        feedback="Great job! You showed strong understanding.",
    )


@pytest.fixture
def sample_quiz_result_fail():
    """Sample failing quiz result."""
    return QuizResult(
        quiz_id="quiz-456",
        score=0.6,
        correct_count=12,
        total_questions=20,
        weak_concepts=["concept-1", "concept-2", "concept-3"],
        feedback="Keep practicing! Review the highlighted concepts.",
    )


@pytest.fixture
def sample_quiz_result_dict():
    """Sample quiz result as dictionary."""
    return {
        "quiz_id": "quiz-789",
        "score": 0.75,
        "correct_count": 15,
        "total_questions": 20,
        "weak_concepts": ["concept-2"],
        "feedback": "Good progress!",
    }


# ============================================================================
# Concept Fixtures
# ============================================================================

@pytest.fixture
def sample_concept_content():
    """Sample concept lesson content in markdown."""
    return """
## Variables in Python

A **variable** is a named storage location in memory that holds a value.

### Key Points
- Variables are created when you assign a value
- Python is dynamically typed
- Variable names are case-sensitive

### Example

```python
# Creating variables
name = "Alice"
age = 25
is_student = True
```

### Common Operations

You can reassign variables at any time:

```python
x = 10
x = x + 5  # x is now 15
```
"""


@pytest.fixture
def sample_concept_dict():
    """Sample concept as dictionary."""
    return {
        "id": "concept-1",
        "title": "Variables",
        "description": "Learn about variables in Python",
        "content": "Variables are named storage locations...",
        "status": "in_progress",
    }
