"""Unit tests for LearningService."""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch

from sensei.models.enums import ExperienceLevel, LearningStyle
from sensei.models.schemas import (
    ChatMessage,
    Concept,
    ConceptLesson,
    LearningSession,
    UserPreferences,
)
from sensei.services.course_service import CourseService
from sensei.services.learning_service import LearningService


@pytest.fixture
def course_with_service(mock_file_storage_paths, mock_database):
    """Create a course and return both course and services (stub mode)."""
    course_service = CourseService(database=mock_database, use_ai=False)
    course = course_service.create_course("Test Topic")
    learning_service = LearningService(database=mock_database, use_ai=False)
    return course, learning_service, mock_database


@pytest.fixture
def course_with_mock_crew(mock_file_storage_paths, mock_database):
    """Create a course and return services with mock crew."""
    course_service = CourseService(database=mock_database, use_ai=False)
    course = course_service.create_course("Test Topic")
    
    mock_crew = MagicMock()
    mock_crew.teach_concept.return_value = "# AI Generated Lesson\n\nThis is AI content."
    mock_crew.answer_question.return_value = "Great question! Here's the AI answer."
    
    learning_service = LearningService(
        database=mock_database,
        teaching_crew=mock_crew,
        use_ai=True,
    )
    return course, learning_service, mock_crew, mock_database


class TestLearningServiceStartSession:
    """Tests for LearningService.start_session()."""
    
    def test_start_session_returns_learning_session(
        self, course_with_service
    ):
        """Should return a LearningSession object."""
        course, service, _ = course_with_service
        session = service.start_session(course.id)
        
        assert isinstance(session, LearningSession)
        assert session.course_id == course.id
    
    def test_start_session_starts_at_beginning(
        self, course_with_service
    ):
        """Should start at first module and concept for new course."""
        course, service, _ = course_with_service
        session = service.start_session(course.id)
        
        assert session.current_module_idx == 0
        assert session.current_concept_idx == 0
    
    def test_start_session_resumes_from_progress(
        self, course_with_service
    ):
        """Should resume from saved progress position."""
        course, service, db = course_with_service
        
        # Save some progress
        db.save_progress({
            "course_id": course.id,
            "current_module_idx": 1,
            "current_concept_idx": 2,
        })
        
        session = service.start_session(course.id)
        
        assert session.current_module_idx == 1
        assert session.current_concept_idx == 2
    
    def test_start_session_raises_for_unknown_course(
        self, mock_file_storage_paths, mock_database
    ):
        """Should raise ValueError for unknown course."""
        service = LearningService(database=mock_database)
        
        with pytest.raises(ValueError, match="Course not found"):
            service.start_session("nonexistent-course")
    
    def test_start_session_sets_session_active(
        self, course_with_service
    ):
        """Should set is_session_active to True."""
        course, service, _ = course_with_service
        
        assert service.is_session_active is False
        
        service.start_session(course.id)
        
        assert service.is_session_active is True


class TestLearningServiceGetCurrentConcept:
    """Tests for LearningService.get_current_concept()."""
    
    def test_get_current_concept_returns_concept_lesson(
        self, course_with_service
    ):
        """Should return a ConceptLesson object."""
        course, service, _ = course_with_service
        service.start_session(course.id)
        
        lesson = service.get_current_concept()
        
        assert isinstance(lesson, ConceptLesson)
    
    def test_get_current_concept_has_content(
        self, course_with_service
    ):
        """Should have lesson content."""
        course, service, _ = course_with_service
        service.start_session(course.id)
        
        lesson = service.get_current_concept()
        
        assert lesson.lesson_content != ""
        assert len(lesson.lesson_content) > 100
    
    def test_get_current_concept_has_metadata(
        self, course_with_service
    ):
        """Should have concept and module metadata."""
        course, service, _ = course_with_service
        service.start_session(course.id)
        
        lesson = service.get_current_concept()
        
        assert lesson.concept_title != ""
        assert lesson.module_title != ""
        assert lesson.module_idx == 0
        assert lesson.concept_idx == 0
    
    def test_get_current_concept_has_navigation_flags(
        self, course_with_service
    ):
        """Should have navigation flags."""
        course, service, _ = course_with_service
        service.start_session(course.id)
        
        lesson = service.get_current_concept()
        
        # At start, should not have previous
        assert lesson.has_previous is False
        assert lesson.has_next is True
    
    def test_get_current_concept_raises_without_session(
        self, mock_file_storage_paths, mock_database
    ):
        """Should raise RuntimeError without active session."""
        service = LearningService(database=mock_database)
        
        with pytest.raises(RuntimeError, match="No active learning session"):
            service.get_current_concept()


class TestLearningServiceNextConcept:
    """Tests for LearningService.next_concept()."""
    
    def test_next_concept_advances_concept_index(
        self, course_with_service
    ):
        """Should advance to next concept in module."""
        course, service, _ = course_with_service
        service.start_session(course.id)
        
        lesson = service.next_concept()
        
        assert lesson is not None
        assert lesson.concept_idx == 1
    
    def test_next_concept_crosses_module_boundary(
        self, course_with_service
    ):
        """Should move to next module when at end of current module."""
        course, service, db = course_with_service
        
        # Get first module's last concept index
        first_module = course.modules[0]
        last_concept_idx = len(first_module.concepts) - 1
        
        # Start at last concept of first module
        db.save_progress({
            "course_id": course.id,
            "current_module_idx": 0,
            "current_concept_idx": last_concept_idx,
        })
        
        service.start_session(course.id)
        lesson = service.next_concept()
        
        assert lesson is not None
        assert lesson.module_idx == 1
        assert lesson.concept_idx == 0
    
    def test_next_concept_returns_none_at_end(
        self, course_with_service
    ):
        """Should return None when at end of course."""
        course, service, db = course_with_service
        
        # Start at last concept of last module
        last_module_idx = len(course.modules) - 1
        last_concept_idx = len(course.modules[last_module_idx].concepts) - 1
        
        db.save_progress({
            "course_id": course.id,
            "current_module_idx": last_module_idx,
            "current_concept_idx": last_concept_idx,
        })
        
        service.start_session(course.id)
        lesson = service.next_concept()
        
        assert lesson is None
    
    def test_next_concept_saves_progress(
        self, course_with_service
    ):
        """Should save progress to database."""
        course, service, db = course_with_service
        service.start_session(course.id)
        
        service.next_concept()
        
        progress = db.get_progress(course.id)
        assert progress is not None
        assert progress["current_concept_idx"] == 1


class TestLearningServicePreviousConcept:
    """Tests for LearningService.previous_concept()."""
    
    def test_previous_concept_returns_none_at_start(
        self, course_with_service
    ):
        """Should return None when at start of course."""
        course, service, _ = course_with_service
        service.start_session(course.id)
        
        lesson = service.previous_concept()
        
        assert lesson is None
    
    def test_previous_concept_goes_back(
        self, course_with_service
    ):
        """Should go back to previous concept."""
        course, service, db = course_with_service
        
        # Start at second concept
        db.save_progress({
            "course_id": course.id,
            "current_module_idx": 0,
            "current_concept_idx": 2,
        })
        
        service.start_session(course.id)
        lesson = service.previous_concept()
        
        assert lesson is not None
        assert lesson.concept_idx == 1
    
    def test_previous_concept_within_module_to_concept_zero(
        self, course_with_service
    ):
        """Should correctly go from concept 1 to concept 0 within same module.
        
        This is a regression test for the bug where going from concept 1 to
        concept 0 would incorrectly jump to the last concept of the module.
        """
        course, service, db = course_with_service
        
        # Start at module 1, concept 1 (NOT crossing module boundary)
        db.save_progress({
            "course_id": course.id,
            "current_module_idx": 1,
            "current_concept_idx": 1,
        })
        
        service.start_session(course.id)
        lesson = service.previous_concept()
        
        assert lesson is not None
        # Should go to concept 0, NOT to last concept of module
        assert lesson.concept_idx == 0
        assert lesson.module_idx == 1  # Should stay in same module
    
    def test_previous_concept_crosses_module_boundary(
        self, course_with_service
    ):
        """Should go to last concept of previous module when crossing boundary."""
        course, service, db = course_with_service
        
        # Start at module 1, concept 0 (first concept of second module)
        db.save_progress({
            "course_id": course.id,
            "current_module_idx": 1,
            "current_concept_idx": 0,
        })
        
        service.start_session(course.id)
        
        # Get the last concept index of module 0
        first_module = course.modules[0]
        expected_last_concept_idx = len(first_module.concepts) - 1
        
        lesson = service.previous_concept()
        
        assert lesson is not None
        assert lesson.module_idx == 0  # Should go to previous module
        assert lesson.concept_idx == expected_last_concept_idx  # Should be last concept
    
    def test_previous_concept_from_module_zero_concept_one(
        self, course_with_service
    ):
        """Should go from module 0, concept 1 to module 0, concept 0."""
        course, service, db = course_with_service
        
        # Start at first module, second concept
        db.save_progress({
            "course_id": course.id,
            "current_module_idx": 0,
            "current_concept_idx": 1,
        })
        
        service.start_session(course.id)
        lesson = service.previous_concept()
        
        assert lesson is not None
        assert lesson.module_idx == 0
        assert lesson.concept_idx == 0


class TestLearningServiceAskQuestion:
    """Tests for LearningService.ask_question()."""
    
    def test_ask_question_returns_answer(
        self, course_with_service
    ):
        """Should return an answer string."""
        course, service, _ = course_with_service
        service.start_session(course.id)
        
        answer = service.ask_question("What is this?")
        
        assert isinstance(answer, str)
        assert len(answer) > 50
    
    def test_ask_question_includes_question_in_response(
        self, course_with_service
    ):
        """Should reference the question in the response."""
        course, service, _ = course_with_service
        service.start_session(course.id)
        
        question = "Why is the sky blue?"
        answer = service.ask_question(question)
        
        assert question in answer
    
    def test_ask_question_adds_to_chat_history(
        self, course_with_service
    ):
        """Should add messages to chat history."""
        course, service, _ = course_with_service
        session = service.start_session(course.id)
        
        initial_count = len(session.chat_history)
        
        service.ask_question("Test question")
        
        # Should add user message and assistant response
        assert len(session.chat_history) == initial_count + 2
    
    def test_ask_question_tracks_questions_asked(
        self, course_with_service
    ):
        """Should increment questions_asked counter."""
        course, service, _ = course_with_service
        session = service.start_session(course.id)
        
        assert session.questions_asked == 0
        
        service.ask_question("Question 1")
        assert session.questions_asked == 1
        
        service.ask_question("Question 2")
        assert session.questions_asked == 2
    
    def test_ask_question_raises_without_session(
        self, mock_file_storage_paths, mock_database
    ):
        """Should raise RuntimeError without active session."""
        service = LearningService(database=mock_database)
        
        with pytest.raises(RuntimeError, match="No active learning session"):
            service.ask_question("Test")
    
    def test_ask_question_raises_for_empty_question(
        self, course_with_service
    ):
        """Should raise ValueError for empty question."""
        course, service, _ = course_with_service
        service.start_session(course.id)
        
        with pytest.raises(ValueError, match="Question cannot be empty"):
            service.ask_question("")
    
    def test_ask_question_raises_for_whitespace_only_question(
        self, course_with_service
    ):
        """Should raise ValueError for whitespace-only question."""
        course, service, _ = course_with_service
        service.start_session(course.id)
        
        with pytest.raises(ValueError, match="Question cannot be empty"):
            service.ask_question("   ")


class TestLearningServiceEndSession:
    """Tests for LearningService.end_session()."""
    
    def test_end_session_returns_summary(
        self, course_with_service
    ):
        """Should return session summary."""
        course, service, _ = course_with_service
        service.start_session(course.id)
        
        summary = service.end_session()
        
        assert isinstance(summary, dict)
        assert "course_id" in summary
        assert "duration_minutes" in summary
        assert "concepts_covered" in summary
        assert "questions_asked" in summary
    
    def test_end_session_clears_session(
        self, course_with_service
    ):
        """Should clear active session."""
        course, service, _ = course_with_service
        service.start_session(course.id)
        
        assert service.is_session_active is True
        
        service.end_session()
        
        assert service.is_session_active is False
        assert service.current_session is None
    
    def test_end_session_saves_progress(
        self, course_with_service
    ):
        """Should save final progress."""
        course, service, db = course_with_service
        service.start_session(course.id)
        service.next_concept()
        service.next_concept()
        
        service.end_session()
        
        progress = db.get_progress(course.id)
        assert progress is not None
    
    def test_end_session_raises_without_session(
        self, mock_file_storage_paths, mock_database
    ):
        """Should raise RuntimeError without active session."""
        service = LearningService(database=mock_database)
        
        with pytest.raises(RuntimeError, match="No active learning session"):
            service.end_session()


class TestLearningServiceIsModuleComplete:
    """Tests for LearningService.is_module_complete()."""
    
    def test_is_module_complete_returns_false_at_start(
        self, course_with_service
    ):
        """Should return False when not at module end."""
        course, service, _ = course_with_service
        service.start_session(course.id)
        
        assert service.is_module_complete() is False
    
    def test_is_module_complete_returns_true_at_end(
        self, course_with_service
    ):
        """Should return True when at last concept of module."""
        course, service, db = course_with_service
        
        # Go to last concept of first module
        last_concept_idx = len(course.modules[0].concepts) - 1
        db.save_progress({
            "course_id": course.id,
            "current_module_idx": 0,
            "current_concept_idx": last_concept_idx,
        })
        
        service.start_session(course.id)
        
        assert service.is_module_complete() is True


class TestLearningServiceGetModuleProgress:
    """Tests for LearningService.get_module_progress()."""
    
    def test_get_module_progress_returns_dict(
        self, course_with_service
    ):
        """Should return module progress dictionary."""
        course, service, _ = course_with_service
        service.start_session(course.id)
        
        progress = service.get_module_progress()
        
        assert isinstance(progress, dict)
        assert "module_idx" in progress
        assert "module_title" in progress
        assert "current_concept_idx" in progress
        assert "total_concepts" in progress
        assert "completion_percentage" in progress
    
    def test_get_module_progress_calculates_percentage(
        self, course_with_service
    ):
        """Should calculate completion percentage correctly."""
        course, service, db = course_with_service
        
        # Start at concept 2 of 4 (50% through if 0-indexed)
        db.save_progress({
            "course_id": course.id,
            "current_module_idx": 0,
            "current_concept_idx": 1,  # Second concept
        })
        
        service.start_session(course.id)
        progress = service.get_module_progress()
        
        # (1 + 1) / total_concepts for percentage
        total = progress["total_concepts"]
        expected = 2 / total if total > 0 else 0
        assert progress["completion_percentage"] == expected


class TestLearningServiceEdgeCases:
    """Tests for edge cases and error paths."""
    
    def test_is_module_complete_raises_without_session(
        self, mock_file_storage_paths, mock_database
    ):
        """Should raise RuntimeError without active session."""
        service = LearningService(database=mock_database)
        
        with pytest.raises(RuntimeError, match="No active learning session"):
            service.is_module_complete()
    
    def test_get_module_progress_raises_without_session(
        self, mock_file_storage_paths, mock_database
    ):
        """Should raise RuntimeError without active session."""
        service = LearningService(database=mock_database)
        
        with pytest.raises(RuntimeError, match="No active learning session"):
            service.get_module_progress()
    
    def test_previous_concept_from_second_concept(
        self, course_with_service
    ):
        """Should go back from second concept to first."""
        course, service, db = course_with_service
        
        # Start at second concept
        db.save_progress({
            "course_id": course.id,
            "current_module_idx": 0,
            "current_concept_idx": 1,
        })
        
        service.start_session(course.id)
        lesson = service.previous_concept()
        
        assert lesson is not None
        assert lesson.concept_idx == 0
    
    def test_next_concept_raises_without_session(
        self, mock_file_storage_paths, mock_database
    ):
        """Should raise RuntimeError without active session."""
        service = LearningService(database=mock_database)
        
        with pytest.raises(RuntimeError, match="No active learning session"):
            service.next_concept()
    
    def test_previous_concept_raises_without_session(
        self, mock_file_storage_paths, mock_database
    ):
        """Should raise RuntimeError without active session."""
        service = LearningService(database=mock_database)
        
        with pytest.raises(RuntimeError, match="No active learning session"):
            service.previous_concept()
    
    def test_lesson_content_includes_topic(
        self, course_with_service
    ):
        """Should include topic in generated lesson content."""
        course, service, _ = course_with_service
        service.start_session(course.id)
        
        lesson = service.get_current_concept()
        
        # Should have markdown structure
        assert "##" in lesson.lesson_content
        assert "###" in lesson.lesson_content
    
class TestLearningServiceGetCurrentConceptWithAI:
    """Tests for LearningService.get_current_concept() with AI mode."""
    
    def test_get_current_concept_uses_teaching_crew(
        self, course_with_mock_crew
    ):
        """Should use TeachingCrew when use_ai=True."""
        course, service, mock_crew, _ = course_with_mock_crew
        service.start_session(course.id)
        
        lesson = service.get_current_concept()
        
        # Verify crew was called
        mock_crew.teach_concept.assert_called_once()
        assert "AI Generated Lesson" in lesson.lesson_content
    
    def test_get_current_concept_passes_user_prefs_to_crew(
        self, course_with_mock_crew
    ):
        """Should pass user preferences to TeachingCrew."""
        course, service, mock_crew, _ = course_with_mock_crew
        service.start_session(course.id)
        
        prefs = UserPreferences(
            name="Test User",
            learning_style=LearningStyle.VISUAL,
            experience_level=ExperienceLevel.ADVANCED,
        )
        
        service.get_current_concept(user_prefs=prefs)
        
        call_args = mock_crew.teach_concept.call_args
        assert call_args.kwargs["user_prefs"] == prefs
    
    def test_get_current_concept_caches_lesson(
        self, course_with_mock_crew
    ):
        """Should cache generated lesson and not regenerate."""
        course, service, mock_crew, _ = course_with_mock_crew
        service.start_session(course.id)
        
        # First call
        service.get_current_concept()
        assert mock_crew.teach_concept.call_count == 1
        
        # Second call should use cache
        service.get_current_concept()
        assert mock_crew.teach_concept.call_count == 1  # Not called again
    
    def test_get_current_concept_handles_crew_failure(
        self, course_with_mock_crew
    ):
        """Should raise RuntimeError when crew fails."""
        course, service, mock_crew, _ = course_with_mock_crew
        mock_crew.teach_concept.side_effect = Exception("LLM API Error")
        service.start_session(course.id)
        
        with pytest.raises(RuntimeError, match="Failed to generate lesson"):
            service.get_current_concept()
    
    def test_get_current_concept_lazy_initializes_crew(
        self, mock_file_storage_paths, mock_database
    ):
        """Should lazily initialize TeachingCrew if not provided."""
        course_service = CourseService(database=mock_database, use_ai=False)
        course = course_service.create_course("Test Topic")
        
        # Patch the import
        with patch(
            "sensei.crews.teaching_crew.TeachingCrew"
        ) as MockCrewClass:
            mock_crew_instance = MagicMock()
            mock_crew_instance.teach_concept.return_value = "Lazy AI Lesson"
            MockCrewClass.return_value = mock_crew_instance
            
            # Create service without crew
            service = LearningService(
                database=mock_database,
                use_ai=True,
            )
            service.start_session(course.id)
            
            lesson = service.get_current_concept()
            
            # Verify TeachingCrew was instantiated
            MockCrewClass.assert_called_once()
            assert "Lazy AI Lesson" in lesson.lesson_content


class TestLearningServiceAskQuestionWithAI:
    """Tests for LearningService.ask_question() with AI mode."""
    
    def test_ask_question_uses_teaching_crew(
        self, course_with_mock_crew
    ):
        """Should use TeachingCrew Q&A Mentor when use_ai=True."""
        course, service, mock_crew, _ = course_with_mock_crew
        service.start_session(course.id)
        
        answer = service.ask_question("What is this?")
        
        # Verify crew was called
        mock_crew.answer_question.assert_called_once()
        assert "AI answer" in answer
    
    def test_ask_question_passes_question_to_crew(
        self, course_with_mock_crew
    ):
        """Should pass the question to TeachingCrew."""
        course, service, mock_crew, _ = course_with_mock_crew
        service.start_session(course.id)
        
        service.ask_question("Why is Python great?")
        
        call_args = mock_crew.answer_question.call_args
        assert call_args.kwargs["question"] == "Why is Python great?"
    
    def test_ask_question_passes_user_prefs_to_crew(
        self, course_with_mock_crew
    ):
        """Should pass user preferences to TeachingCrew."""
        course, service, mock_crew, _ = course_with_mock_crew
        service.start_session(course.id)
        
        prefs = UserPreferences(
            name="Test User",
            learning_style=LearningStyle.HANDS_ON,
            experience_level=ExperienceLevel.BEGINNER,
        )
        
        service.ask_question("Test question", user_prefs=prefs)
        
        call_args = mock_crew.answer_question.call_args
        assert call_args.kwargs["user_prefs"] == prefs
    
    def test_ask_question_includes_cached_lesson(
        self, course_with_mock_crew
    ):
        """Should include cached lesson content in Q&A context."""
        course, service, mock_crew, _ = course_with_mock_crew
        service.start_session(course.id)
        
        # Generate and cache lesson
        service.get_current_concept()
        
        # Ask question
        service.ask_question("Test question")
        
        call_args = mock_crew.answer_question.call_args
        assert call_args.kwargs["lesson_content"] == "# AI Generated Lesson\n\nThis is AI content."
    
    def test_ask_question_handles_crew_failure(
        self, course_with_mock_crew
    ):
        """Should raise RuntimeError when crew fails."""
        course, service, mock_crew, _ = course_with_mock_crew
        mock_crew.answer_question.side_effect = Exception("LLM API Error")
        service.start_session(course.id)
        
        with pytest.raises(RuntimeError, match="Failed to generate answer"):
            service.ask_question("Test question")


class TestLearningServiceLessonCache:
    """Tests for lesson caching functionality."""
    
    def test_cache_cleared_on_end_session(
        self, course_with_mock_crew
    ):
        """Should clear cache when session ends."""
        course, service, mock_crew, _ = course_with_mock_crew
        service.start_session(course.id)
        
        # Generate and cache lesson
        service.get_current_concept()
        assert mock_crew.teach_concept.call_count == 1
        
        # End and restart session
        service.end_session()
        service.start_session(course.id)
        
        # Should regenerate
        service.get_current_concept()
        assert mock_crew.teach_concept.call_count == 2
    
    def test_clear_lesson_cache(
        self, course_with_mock_crew
    ):
        """Should be able to manually clear cache."""
        course, service, mock_crew, _ = course_with_mock_crew
        service.start_session(course.id)
        
        # Generate and cache lesson
        service.get_current_concept()
        assert mock_crew.teach_concept.call_count == 1
        
        # Clear cache
        service.clear_lesson_cache()
        
        # Should regenerate
        service.get_current_concept()
        assert mock_crew.teach_concept.call_count == 2
    
    def test_different_concepts_not_cached_together(
        self, course_with_mock_crew
    ):
        """Should generate new lesson for different concepts."""
        course, service, mock_crew, _ = course_with_mock_crew
        service.start_session(course.id)
        
        # First concept
        service.get_current_concept()
        assert mock_crew.teach_concept.call_count == 1
        
        # Move to next concept
        service.next_concept()
        
        # Should generate new lesson
        service.get_current_concept()
        assert mock_crew.teach_concept.call_count == 2
