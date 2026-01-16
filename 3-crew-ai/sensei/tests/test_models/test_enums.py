"""Unit tests for enums module (Subtask 3.1)."""

import pytest

from sensei.models.enums import (
    ConceptStatus,
    ExperienceLevel,
    LearningStyle,
    MessageRole,
    QuestionType,
)


class TestLearningStyle:
    """Tests for LearningStyle enum."""
    
    def test_enum_values(self):
        """Test that all expected values exist."""
        assert LearningStyle.VISUAL.value == "visual"
        assert LearningStyle.READING.value == "reading"
        assert LearningStyle.HANDS_ON.value == "hands_on"
    
    def test_string_conversion(self):
        """Test enum serialization to string."""
        assert str(LearningStyle.VISUAL) == "visual"
        assert str(LearningStyle.READING) == "reading"
    
    def test_from_string(self):
        """Test creating enum from string value."""
        assert LearningStyle("visual") == LearningStyle.VISUAL
        assert LearningStyle("reading") == LearningStyle.READING
        assert LearningStyle("hands_on") == LearningStyle.HANDS_ON
    
    def test_invalid_value_raises(self):
        """Test that invalid enum value raises ValueError."""
        with pytest.raises(ValueError):
            LearningStyle("invalid")
    
    def test_display_name(self):
        """Test human-readable display names."""
        assert LearningStyle.VISUAL.display_name == "Visual (diagrams, images)"
        assert LearningStyle.READING.display_name == "Reading (text explanations)"
        assert LearningStyle.HANDS_ON.display_name == "Hands-on (code examples)"


class TestExperienceLevel:
    """Tests for ExperienceLevel enum."""
    
    def test_enum_values(self):
        """Test that all expected values exist."""
        assert ExperienceLevel.BEGINNER.value == "beginner"
        assert ExperienceLevel.INTERMEDIATE.value == "intermediate"
        assert ExperienceLevel.ADVANCED.value == "advanced"
    
    def test_string_conversion(self):
        """Test enum serialization to string."""
        assert str(ExperienceLevel.BEGINNER) == "beginner"
    
    def test_from_string(self):
        """Test creating enum from string value."""
        assert ExperienceLevel("beginner") == ExperienceLevel.BEGINNER
        assert ExperienceLevel("intermediate") == ExperienceLevel.INTERMEDIATE
        assert ExperienceLevel("advanced") == ExperienceLevel.ADVANCED
    
    def test_invalid_value_raises(self):
        """Test that invalid enum value raises ValueError."""
        with pytest.raises(ValueError):
            ExperienceLevel("expert")
    
    def test_display_name(self):
        """Test display name capitalization."""
        assert ExperienceLevel.BEGINNER.display_name == "Beginner"
        assert ExperienceLevel.INTERMEDIATE.display_name == "Intermediate"
        assert ExperienceLevel.ADVANCED.display_name == "Advanced"


class TestConceptStatus:
    """Tests for ConceptStatus enum."""
    
    def test_enum_values(self):
        """Test that all expected values exist."""
        assert ConceptStatus.NOT_STARTED.value == "not_started"
        assert ConceptStatus.IN_PROGRESS.value == "in_progress"
        assert ConceptStatus.COMPLETED.value == "completed"
        assert ConceptStatus.NEEDS_REVIEW.value == "needs_review"
    
    def test_string_conversion(self):
        """Test enum serialization to string."""
        assert str(ConceptStatus.COMPLETED) == "completed"
    
    def test_from_string(self):
        """Test creating enum from string value."""
        assert ConceptStatus("not_started") == ConceptStatus.NOT_STARTED
        assert ConceptStatus("completed") == ConceptStatus.COMPLETED
    
    def test_invalid_value_raises(self):
        """Test that invalid enum value raises ValueError."""
        with pytest.raises(ValueError):
            ConceptStatus("unknown")
    
    def test_display_name(self):
        """Test human-readable display names."""
        assert ConceptStatus.NOT_STARTED.display_name == "Not Started"
        assert ConceptStatus.IN_PROGRESS.display_name == "In Progress"
        assert ConceptStatus.COMPLETED.display_name == "Completed"
        assert ConceptStatus.NEEDS_REVIEW.display_name == "Needs Review"
    
    def test_emoji(self):
        """Test emoji representations."""
        assert ConceptStatus.NOT_STARTED.emoji == "○"
        assert ConceptStatus.IN_PROGRESS.emoji == "▶"
        assert ConceptStatus.COMPLETED.emoji == "✅"
        assert ConceptStatus.NEEDS_REVIEW.emoji == "🔄"


class TestQuestionType:
    """Tests for QuestionType enum."""
    
    def test_enum_values(self):
        """Test that all expected values exist."""
        assert QuestionType.MULTIPLE_CHOICE.value == "multiple_choice"
        assert QuestionType.TRUE_FALSE.value == "true_false"
        assert QuestionType.CODE.value == "code"
        assert QuestionType.OPEN_ENDED.value == "open_ended"
    
    def test_string_conversion(self):
        """Test enum serialization to string."""
        assert str(QuestionType.MULTIPLE_CHOICE) == "multiple_choice"
    
    def test_from_string(self):
        """Test creating enum from string value."""
        assert QuestionType("multiple_choice") == QuestionType.MULTIPLE_CHOICE
        assert QuestionType("code") == QuestionType.CODE
    
    def test_invalid_value_raises(self):
        """Test that invalid enum value raises ValueError."""
        with pytest.raises(ValueError):
            QuestionType("essay")
    
    def test_display_name(self):
        """Test human-readable display names."""
        assert QuestionType.MULTIPLE_CHOICE.display_name == "Multiple Choice"
        assert QuestionType.TRUE_FALSE.display_name == "True/False"
        assert QuestionType.CODE.display_name == "Code Completion"
        assert QuestionType.OPEN_ENDED.display_name == "Open Ended"


class TestMessageRole:
    """Tests for MessageRole enum."""
    
    def test_enum_values(self):
        """Test that all expected values exist."""
        assert MessageRole.USER.value == "user"
        assert MessageRole.ASSISTANT.value == "assistant"
        assert MessageRole.SYSTEM.value == "system"
    
    def test_string_conversion(self):
        """Test enum serialization to string."""
        assert str(MessageRole.USER) == "user"
        assert str(MessageRole.ASSISTANT) == "assistant"
