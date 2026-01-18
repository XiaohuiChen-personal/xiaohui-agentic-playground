"""Data models and schemas for Sensei.

This package provides Pydantic models and enumerations for all
data structures used throughout the application.

Usage:
    from sensei.models import Course, Module, Concept
    from sensei.models import LearningStyle, ExperienceLevel
    from sensei.models import Quiz, QuizQuestion, QuizResult
"""

# Enumerations
from sensei.models.enums import (
    ConceptStatus,
    ExperienceLevel,
    LearningStyle,
    MessageRole,
    QuestionType,
)

# Core Schemas
from sensei.models.schemas import (
    Concept,
    Module,
    Course,
)

# Quiz Schemas
from sensei.models.schemas import (
    QuizQuestion,
    Quiz,
    AnswerResult,
    QuizResult,
)

# User & Session Schemas
from sensei.models.schemas import (
    UserPreferences,
    ChatMessage,
    LearningSession,
    Progress,
)

# Additional Schemas
from sensei.models.schemas import (
    ConceptLesson,
    LearningStats,
)

# LLM Output Schemas (for CrewAI output_pydantic)
from sensei.models.schemas import (
    ConceptOutput,
    ModuleOutput,
    CourseOutput,
    QuizQuestionOutput,
    QuizOutput,
    QuizEvaluationOutput,
)

# Helper function
from sensei.models.schemas import generate_id

__all__ = [
    # Enums
    "ConceptStatus",
    "ExperienceLevel",
    "LearningStyle",
    "MessageRole",
    "QuestionType",
    # Core
    "Concept",
    "Module",
    "Course",
    # Quiz
    "QuizQuestion",
    "Quiz",
    "AnswerResult",
    "QuizResult",
    # User & Session
    "UserPreferences",
    "ChatMessage",
    "LearningSession",
    "Progress",
    # Additional
    "ConceptLesson",
    "LearningStats",
    # LLM Output Schemas
    "ConceptOutput",
    "ModuleOutput",
    "CourseOutput",
    "QuizQuestionOutput",
    "QuizOutput",
    "QuizEvaluationOutput",
    # Helpers
    "generate_id",
]
