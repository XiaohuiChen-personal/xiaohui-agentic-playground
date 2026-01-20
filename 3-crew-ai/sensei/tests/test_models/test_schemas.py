"""Unit tests for schemas module (Subtasks 3.2, 3.3, 3.4)."""

from datetime import datetime

import pytest
from pydantic import ValidationError

from sensei.models.enums import (
    ConceptStatus,
    ExperienceLevel,
    LearningStyle,
    MessageRole,
    QuestionType,
)
from sensei.models.schemas import (
    AnswerResult,
    ChatMessage,
    Concept,
    ConceptLesson,
    Course,
    LearningSession,
    LearningStats,
    Module,
    Progress,
    Quiz,
    QuizQuestion,
    QuizResult,
    UserPreferences,
    generate_id,
)


# =============================================================================
# Helper Function Tests
# =============================================================================

class TestGenerateId:
    """Tests for generate_id helper function."""
    
    def test_generates_unique_ids(self):
        """Test that IDs are unique."""
        ids = [generate_id() for _ in range(100)]
        assert len(ids) == len(set(ids))
    
    def test_with_prefix(self):
        """Test ID generation with prefix."""
        id_with_prefix = generate_id("course")
        assert id_with_prefix.startswith("course-")
        assert len(id_with_prefix) > len("course-")
    
    def test_without_prefix(self):
        """Test ID generation without prefix."""
        id_no_prefix = generate_id()
        assert "-" not in id_no_prefix or id_no_prefix.count("-") == 0


# =============================================================================
# Core Schema Tests (Subtask 3.2)
# =============================================================================

class TestConcept:
    """Tests for Concept model."""
    
    def test_create_valid_concept(self):
        """Test creating a valid concept."""
        concept = Concept(title="Variables", content="Learn about variables")
        assert concept.title == "Variables"
        assert concept.content == "Learn about variables"
        assert concept.id.startswith("concept-")
    
    def test_concept_missing_required_title(self):
        """Test that missing title raises ValidationError."""
        with pytest.raises(ValidationError):
            Concept(content="Some content")  # type: ignore
    
    def test_default_values(self):
        """Test that default values are applied correctly."""
        concept = Concept(title="Test")
        assert concept.order == 0
        assert concept.status == ConceptStatus.NOT_STARTED
        assert concept.mastery == 0.0
        assert concept.questions_asked == 0
        assert concept.content == ""
    
    def test_mastery_validation(self):
        """Test mastery value must be between 0 and 1."""
        # Valid values work
        concept = Concept(title="Test", mastery=0.5)
        assert concept.mastery == 0.5
        
        concept_max = Concept(title="Test", mastery=1.0)
        assert concept_max.mastery == 1.0
        
        concept_min = Concept(title="Test", mastery=0.0)
        assert concept_min.mastery == 0.0
        
        # Invalid values raise ValidationError
        with pytest.raises(ValidationError):
            Concept(title="Test", mastery=1.5)
        
        with pytest.raises(ValidationError):
            Concept(title="Test", mastery=-0.5)
    
    def test_concept_to_dict(self):
        """Test serialization to dictionary."""
        concept = Concept(title="Test", status=ConceptStatus.COMPLETED)
        data = concept.model_dump()
        assert data["title"] == "Test"
        assert data["status"] == "completed"  # Enum serialized as string


class TestModule:
    """Tests for Module model."""
    
    def test_create_valid_module(self):
        """Test creating a valid module with concepts."""
        concept1 = Concept(title="Variables")
        concept2 = Concept(title="Data Types")
        module = Module(
            title="Python Basics",
            concepts=[concept1, concept2]
        )
        assert module.title == "Python Basics"
        assert module.concept_count == 2
        assert module.id.startswith("module-")
    
    def test_module_missing_title(self):
        """Test that missing title raises ValidationError."""
        with pytest.raises(ValidationError):
            Module(concepts=[])  # type: ignore
    
    def test_default_values(self):
        """Test that default values are applied correctly."""
        module = Module(title="Test")
        assert module.order == 0
        assert module.estimated_minutes == 30
        assert module.concepts == []
        assert module.description == ""
    
    def test_computed_fields(self):
        """Test computed fields work correctly."""
        module = Module(
            title="Test",
            concepts=[
                Concept(title="C1", status=ConceptStatus.COMPLETED),
                Concept(title="C2", status=ConceptStatus.COMPLETED),
                Concept(title="C3", status=ConceptStatus.NOT_STARTED),
            ]
        )
        assert module.concept_count == 3
        assert module.completed_concepts == 2
        assert module.completion_percentage == pytest.approx(2/3)
    
    def test_get_concept(self):
        """Test getting concept by index."""
        concept = Concept(title="Test Concept")
        module = Module(title="Test", concepts=[concept])
        
        assert module.get_concept(0) == concept
        assert module.get_concept(1) is None
        assert module.get_concept(-1) is None


class TestCourse:
    """Tests for Course model."""
    
    def test_create_valid_course(self):
        """Test creating a valid course."""
        course = Course(
            title="Learn Python",
            description="A comprehensive Python course"
        )
        assert course.title == "Learn Python"
        assert course.id.startswith("course-")
        assert course.created_at is not None
    
    def test_course_with_modules(self):
        """Test creating course with nested modules and concepts."""
        module = Module(
            title="Module 1",
            concepts=[Concept(title="C1"), Concept(title="C2")]
        )
        course = Course(title="Test", modules=[module])
        
        assert course.total_modules == 1
        assert course.total_concepts == 2
    
    def test_default_values(self):
        """Test that default values are applied correctly."""
        course = Course(title="Test")
        assert course.modules == []
        assert course.description == ""
        assert course.total_modules == 0
        assert course.total_concepts == 0
    
    def test_completion_percentage(self):
        """Test completion percentage calculation."""
        module = Module(
            title="Module 1",
            concepts=[
                Concept(title="C1", status=ConceptStatus.COMPLETED),
                Concept(title="C2", status=ConceptStatus.NOT_STARTED),
            ]
        )
        course = Course(title="Test", modules=[module])
        assert course.completion_percentage == 0.5
    
    def test_estimated_hours(self):
        """Test estimated hours calculation."""
        module1 = Module(title="M1", estimated_minutes=60)
        module2 = Module(title="M2", estimated_minutes=90)
        course = Course(title="Test", modules=[module1, module2])
        assert course.estimated_hours == 2.5
    
    def test_get_module(self):
        """Test getting module by index."""
        module = Module(title="Test Module")
        course = Course(title="Test", modules=[module])
        
        assert course.get_module(0) == module
        assert course.get_module(1) is None
    
    def test_get_concept(self):
        """Test getting concept by module and concept index."""
        concept = Concept(title="Test Concept")
        module = Module(title="Test Module", concepts=[concept])
        course = Course(title="Test", modules=[module])
        
        assert course.get_concept(0, 0) == concept
        assert course.get_concept(0, 1) is None
        assert course.get_concept(1, 0) is None
    
    def test_course_to_dict(self):
        """Test serialization to dictionary."""
        course = Course(title="Test")
        data = course.model_dump()
        
        assert "id" in data
        assert "title" in data
        assert "created_at" in data
        assert isinstance(data["created_at"], str)  # datetime serialized
    
    def test_course_from_dict(self):
        """Test creating course from dictionary."""
        data = {
            "title": "Test Course",
            "description": "A test",
            "modules": [
                {
                    "title": "Module 1",
                    "concepts": [{"title": "Concept 1"}]
                }
            ]
        }
        course = Course(**data)
        assert course.title == "Test Course"
        assert course.total_modules == 1
        assert course.total_concepts == 1


# =============================================================================
# Quiz Schema Tests (Subtask 3.3)
# =============================================================================

class TestQuizQuestion:
    """Tests for QuizQuestion model."""
    
    def test_create_valid_question(self):
        """Test creating a valid quiz question."""
        question = QuizQuestion(
            question="What is Python?",
            options=["A", "B", "C", "D"],
            correct_answer="A",
            explanation="Python is a programming language"
        )
        assert question.question == "What is Python?"
        assert len(question.options) == 4
        assert question.id.startswith("q-")
    
    def test_default_values(self):
        """Test that default values are applied correctly."""
        question = QuizQuestion(
            question="Test?",
            correct_answer="Yes"
        )
        assert question.question_type == QuestionType.MULTIPLE_CHOICE
        assert question.options == []
        assert question.difficulty == 1
        assert question.concept_id == ""
    
    def test_question_to_dict(self):
        """Test serialization preserves enum as string."""
        question = QuizQuestion(
            question="Test?",
            correct_answer="Yes",
            question_type=QuestionType.TRUE_FALSE
        )
        data = question.model_dump()
        assert data["question_type"] == "true_false"


class TestQuiz:
    """Tests for Quiz model."""
    
    def test_create_valid_quiz(self):
        """Test creating a valid quiz."""
        quiz = Quiz(
            module_id="module-123",
            questions=[
                QuizQuestion(question="Q1?", correct_answer="A"),
                QuizQuestion(question="Q2?", correct_answer="B"),
            ]
        )
        assert quiz.module_id == "module-123"
        assert quiz.question_count == 2
        assert quiz.id.startswith("quiz-")
    
    def test_get_question(self):
        """Test getting question by index."""
        q1 = QuizQuestion(question="Q1?", correct_answer="A")
        quiz = Quiz(module_id="m1", questions=[q1])
        
        assert quiz.get_question(0) == q1
        assert quiz.get_question(1) is None


class TestQuizResult:
    """Tests for QuizResult model."""
    
    def test_create_valid_result(self):
        """Test creating a valid quiz result."""
        result = QuizResult(
            quiz_id="quiz-123",
            score=0.85,
            correct_count=17,
            total_questions=20,
            passed=True,
            feedback="Great job!"
        )
        assert result.score == 0.85
        assert result.score_percentage == 85
    
    def test_score_validation(self):
        """Test score must be between 0 and 1."""
        # Valid scores work
        result = QuizResult(
            quiz_id="q1",
            score=0.85,
            correct_count=17,
            total_questions=20
        )
        assert result.score == 0.85
        
        result_max = QuizResult(
            quiz_id="q2",
            score=1.0,
            correct_count=10,
            total_questions=10
        )
        assert result_max.score == 1.0
        
        # Invalid scores raise ValidationError
        with pytest.raises(ValidationError):
            QuizResult(
                quiz_id="q3",
                score=1.5,
                correct_count=10,
                total_questions=10
            )
        
        with pytest.raises(ValidationError):
            QuizResult(
                quiz_id="q4",
                score=-0.5,
                correct_count=0,
                total_questions=10
            )
    
    def test_weak_concepts_list(self):
        """Test weak concepts stored as list."""
        result = QuizResult(
            quiz_id="q1",
            score=0.6,
            correct_count=6,
            total_questions=10,
            weak_concepts=["concept-1", "concept-2"]
        )
        assert len(result.weak_concepts) == 2


class TestAnswerResult:
    """Tests for AnswerResult model."""
    
    def test_create_answer_result(self):
        """Test creating an answer result."""
        result = AnswerResult(
            question_id="q1",
            user_answer="A",
            is_correct=True,
            correct_answer="A",
            explanation="Correct!"
        )
        assert result.is_correct is True

    def test_is_pending_default_false(self):
        """Test that is_pending defaults to False."""
        result = AnswerResult(
            question_id="q1",
            user_answer="My answer",
            is_correct=False,
            correct_answer="Expected answer",
        )
        assert result.is_pending is False

    def test_is_pending_true_for_open_ended(self):
        """Test creating a pending result for open-ended questions."""
        result = AnswerResult(
            question_id="q1",
            user_answer="My explanation of the concept...",
            is_correct=False,  # Not yet evaluated
            correct_answer="Sample answer",
            explanation="This answer will be evaluated by AI.",
            is_pending=True,
        )
        assert result.is_pending is True
        assert result.is_correct is False  # Not evaluated yet

    def test_answer_result_with_all_fields(self):
        """Test AnswerResult with all fields specified."""
        result = AnswerResult(
            question_id="q123",
            user_answer="User's response",
            is_correct=True,
            correct_answer="Correct response",
            explanation="Great job!",
            is_pending=False,
        )
        assert result.question_id == "q123"
        assert result.user_answer == "User's response"
        assert result.is_correct is True
        assert result.correct_answer == "Correct response"
        assert result.explanation == "Great job!"
        assert result.is_pending is False


# =============================================================================
# User & Session Schema Tests (Subtask 3.4)
# =============================================================================

class TestUserPreferences:
    """Tests for UserPreferences model."""
    
    def test_create_valid_preferences(self):
        """Test creating valid user preferences."""
        prefs = UserPreferences(
            name="John",
            learning_style=LearningStyle.VISUAL,
            experience_level=ExperienceLevel.INTERMEDIATE
        )
        assert prefs.name == "John"
        assert prefs.learning_style == LearningStyle.VISUAL
    
    def test_default_values(self):
        """Test that default values are applied correctly."""
        prefs = UserPreferences()
        assert prefs.name == ""
        assert prefs.learning_style == LearningStyle.READING
        assert prefs.experience_level == ExperienceLevel.BEGINNER
        assert prefs.session_length_minutes == 30
        assert prefs.goals == ""
        assert prefs.is_onboarded is False
    
    def test_preferences_to_dict(self):
        """Test serialization to JSON-compatible dict."""
        prefs = UserPreferences(
            name="Test",
            learning_style=LearningStyle.HANDS_ON,
            experience_level=ExperienceLevel.ADVANCED
        )
        data = prefs.model_dump()
        assert data["learning_style"] == "hands_on"
        assert data["experience_level"] == "advanced"
    
    def test_preferences_from_dict(self):
        """Test creating from dictionary (JSON deserialization)."""
        data = {
            "name": "Test",
            "learning_style": "visual",
            "experience_level": "intermediate",
            "session_length_minutes": 45,
            "goals": "Learn programming",
            "is_onboarded": True
        }
        prefs = UserPreferences.from_dict(data)
        assert prefs.name == "Test"
        assert prefs.learning_style == LearningStyle.VISUAL
        assert prefs.experience_level == ExperienceLevel.INTERMEDIATE


class TestChatMessage:
    """Tests for ChatMessage model."""
    
    def test_create_user_message(self):
        """Test creating a user message."""
        msg = ChatMessage.user_message("Hello!")
        assert msg.role == MessageRole.USER
        assert msg.content == "Hello!"
        assert msg.timestamp is not None
    
    def test_create_assistant_message(self):
        """Test creating an assistant message."""
        msg = ChatMessage.assistant_message("Hi there!")
        assert msg.role == MessageRole.ASSISTANT
        assert msg.content == "Hi there!"
    
    def test_message_to_dict(self):
        """Test serialization preserves values."""
        msg = ChatMessage(role=MessageRole.USER, content="Test")
        data = msg.model_dump()
        assert data["role"] == "user"
        assert isinstance(data["timestamp"], str)


class TestLearningSession:
    """Tests for LearningSession model."""
    
    def test_create_session(self):
        """Test creating a learning session."""
        session = LearningSession(course_id="course-123")
        assert session.course_id == "course-123"
        assert session.current_module_idx == 0
        assert session.current_concept_idx == 0
        assert session.chat_history == []
    
    def test_add_message(self):
        """Test adding messages to chat history."""
        session = LearningSession(course_id="c1")
        msg = ChatMessage.user_message("What is this?")
        session.add_message(msg)
        
        assert len(session.chat_history) == 1
        assert session.questions_asked == 1
    
    def test_advance_concept_same_module(self):
        """Test advancing to next concept in same module."""
        session = LearningSession(course_id="c1")
        result = session.advance_concept(
            total_concepts_in_module=3,
            total_modules=2
        )
        
        assert result is True
        assert session.current_concept_idx == 1
        assert session.current_module_idx == 0
        assert session.concepts_covered == 1
    
    def test_advance_concept_next_module(self):
        """Test advancing to next module."""
        session = LearningSession(
            course_id="c1",
            current_concept_idx=2  # Last concept in module
        )
        result = session.advance_concept(
            total_concepts_in_module=3,
            total_modules=2
        )
        
        assert result is True
        assert session.current_module_idx == 1
        assert session.current_concept_idx == 0
    
    def test_advance_concept_end_of_course(self):
        """Test advancing at end of course returns False."""
        session = LearningSession(
            course_id="c1",
            current_module_idx=1,  # Last module
            current_concept_idx=2  # Last concept
        )
        result = session.advance_concept(
            total_concepts_in_module=3,
            total_modules=2
        )
        
        assert result is False


class TestProgress:
    """Tests for Progress model."""
    
    def test_create_progress(self):
        """Test creating progress record."""
        progress = Progress(
            course_id="course-123",
            completion_percentage=0.75,
            concepts_completed=15,
            total_concepts=20
        )
        assert progress.completion_display == "75%"
    
    def test_completion_validation(self):
        """Test completion percentage must be between 0 and 1."""
        # Valid percentages work
        progress = Progress(
            course_id="c1",
            completion_percentage=0.75,
            concepts_completed=15,
            total_concepts=20
        )
        assert progress.completion_percentage == 0.75
        
        # Invalid percentages raise ValidationError
        with pytest.raises(ValidationError):
            Progress(
                course_id="c2",
                completion_percentage=1.5,
                concepts_completed=10,
                total_concepts=10
            )
        
        with pytest.raises(ValidationError):
            Progress(
                course_id="c3",
                completion_percentage=-0.1,
                concepts_completed=0,
                total_concepts=10
            )
    
    def test_is_complete(self):
        """Test is_complete computed field."""
        progress_incomplete = Progress(
            course_id="c1",
            completion_percentage=0.9,
            concepts_completed=9,
            total_concepts=10
        )
        assert progress_incomplete.is_complete is False
        
        progress_complete = Progress(
            course_id="c2",
            completion_percentage=1.0,
            concepts_completed=10,
            total_concepts=10
        )
        assert progress_complete.is_complete is True
    
    def test_from_db_row(self):
        """Test creating from database row."""
        row = {
            "course_id": "c1",
            "completion_percentage": 0.5,
            "modules_completed": 2,
            "total_modules": 4,
            "concepts_completed": 10,
            "total_concepts": 20,
            "time_spent_minutes": 60,
            "current_module_idx": 2,
            "current_concept_idx": 0,
            "last_accessed": "2026-01-15T10:30:00",
            "created_at": "2026-01-01T00:00:00"
        }
        progress = Progress.from_db_row(row)
        
        assert progress.course_id == "c1"
        assert isinstance(progress.last_accessed, datetime)
        assert isinstance(progress.created_at, datetime)


class TestLearningStats:
    """Tests for LearningStats model."""
    
    def test_create_stats(self):
        """Test creating learning stats."""
        stats = LearningStats(
            total_courses=3,
            concepts_mastered=47,
            total_concepts=100,
            hours_learned=12.5,
            current_streak=5,
            longest_streak=10
        )
        assert stats.mastery_percentage == 0.47
    
    def test_mastery_percentage_zero_total(self):
        """Test mastery percentage when no concepts."""
        stats = LearningStats(
            total_courses=0,
            concepts_mastered=0,
            total_concepts=0
        )
        assert stats.mastery_percentage == 0.0
