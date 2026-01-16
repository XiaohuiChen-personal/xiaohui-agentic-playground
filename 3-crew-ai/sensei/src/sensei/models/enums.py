"""Enumerations for Sensei data models.

This module defines all enum types used throughout the application
for type-safe categorical values.
"""

from enum import Enum


class LearningStyle(str, Enum):
    """User's preferred learning style.
    
    Used to personalize lesson generation and content delivery.
    """
    VISUAL = "visual"
    READING = "reading"
    HANDS_ON = "hands_on"
    
    def __str__(self) -> str:
        return self.value
    
    @property
    def display_name(self) -> str:
        """Human-readable display name."""
        names = {
            "visual": "Visual (diagrams, images)",
            "reading": "Reading (text explanations)",
            "hands_on": "Hands-on (code examples)",
        }
        return names.get(self.value, self.value)


class ExperienceLevel(str, Enum):
    """User's experience level with the subject matter.
    
    Used to adjust content complexity and depth.
    """
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    
    def __str__(self) -> str:
        return self.value
    
    @property
    def display_name(self) -> str:
        """Human-readable display name."""
        return self.value.capitalize()


class ConceptStatus(str, Enum):
    """Learning status of a concept for a user.
    
    Tracks progress through individual concepts.
    """
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    NEEDS_REVIEW = "needs_review"
    
    def __str__(self) -> str:
        return self.value
    
    @property
    def display_name(self) -> str:
        """Human-readable display name."""
        names = {
            "not_started": "Not Started",
            "in_progress": "In Progress",
            "completed": "Completed",
            "needs_review": "Needs Review",
        }
        return names.get(self.value, self.value)
    
    @property
    def emoji(self) -> str:
        """Emoji representation of status."""
        emojis = {
            "not_started": "○",
            "in_progress": "▶",
            "completed": "✅",
            "needs_review": "🔄",
        }
        return emojis.get(self.value, "○")


class QuestionType(str, Enum):
    """Type of quiz question.
    
    Determines how the question is displayed and answered.
    """
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    CODE = "code"
    OPEN_ENDED = "open_ended"
    
    def __str__(self) -> str:
        return self.value
    
    @property
    def display_name(self) -> str:
        """Human-readable display name."""
        names = {
            "multiple_choice": "Multiple Choice",
            "true_false": "True/False",
            "code": "Code Completion",
            "open_ended": "Open Ended",
        }
        return names.get(self.value, self.value)


class MessageRole(str, Enum):
    """Role of a chat message sender.
    
    Used in the Q&A chat interface.
    """
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    
    def __str__(self) -> str:
        return self.value
