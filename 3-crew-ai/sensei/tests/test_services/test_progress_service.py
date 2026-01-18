"""Unit tests for ProgressService."""

import pytest
from datetime import datetime

from sensei.models.schemas import LearningStats, Progress, QuizResult
from sensei.services.progress_service import ProgressService
from sensei.storage.database import Database


class TestProgressServiceGetCourseProgress:
    """Tests for ProgressService.get_course_progress()."""
    
    def test_get_course_progress_returns_empty_for_new_course(
        self, mock_database
    ):
        """Should return Progress with 0% for unknown course."""
        service = ProgressService(database=mock_database)
        progress = service.get_course_progress("unknown-course")
        
        assert isinstance(progress, Progress)
        assert progress.course_id == "unknown-course"
        assert progress.completion_percentage == 0.0
        assert progress.concepts_completed == 0
    
    def test_get_course_progress_returns_existing_progress(
        self, mock_database
    ):
        """Should return existing progress for known course."""
        # Save some progress first
        mock_database.save_progress({
            "course_id": "test-course",
            "completion_percentage": 0.5,
            "concepts_completed": 5,
            "total_concepts": 10,
            "modules_completed": 2,
            "total_modules": 4,
            "time_spent_minutes": 120,
        })
        
        service = ProgressService(database=mock_database)
        progress = service.get_course_progress("test-course")
        
        assert progress.course_id == "test-course"
        assert progress.completion_percentage == 0.5
        assert progress.concepts_completed == 5
        assert progress.total_concepts == 10
        assert progress.time_spent_minutes == 120


class TestProgressServiceUpdateProgress:
    """Tests for ProgressService.update_progress()."""
    
    def test_update_progress_creates_new_record(
        self, mock_database
    ):
        """Should create progress record for new course."""
        service = ProgressService(database=mock_database)
        
        progress = service.update_progress(
            course_id="new-course",
            concepts_completed=3,
            total_concepts=10,
            modules_completed=1,
            total_modules=4,
        )
        
        assert progress.course_id == "new-course"
        assert progress.concepts_completed == 3
        assert progress.total_concepts == 10
        assert progress.completion_percentage == 0.3
    
    def test_update_progress_calculates_completion(
        self, mock_database
    ):
        """Should calculate completion percentage correctly."""
        service = ProgressService(database=mock_database)
        
        progress = service.update_progress(
            course_id="test-course",
            concepts_completed=7,
            total_concepts=10,
        )
        
        assert progress.completion_percentage == 0.7
    
    def test_update_progress_handles_zero_concepts(
        self, mock_database
    ):
        """Should handle zero total concepts gracefully."""
        service = ProgressService(database=mock_database)
        
        progress = service.update_progress(
            course_id="empty-course",
            concepts_completed=0,
            total_concepts=0,
        )
        
        assert progress.completion_percentage == 0.0
    
    def test_update_progress_accumulates_time(
        self, mock_database
    ):
        """Should accumulate time spent across updates."""
        service = ProgressService(database=mock_database)
        
        # First update with 30 minutes
        service.update_progress(
            course_id="test-course",
            concepts_completed=1,
            total_concepts=10,
            time_spent_minutes=30,
        )
        
        # Second update with 15 more minutes
        progress = service.update_progress(
            course_id="test-course",
            concepts_completed=2,
            total_concepts=10,
            time_spent_minutes=15,
        )
        
        assert progress.time_spent_minutes == 45
    
    def test_update_progress_returns_progress_object(
        self, mock_database
    ):
        """Should return a Progress object."""
        service = ProgressService(database=mock_database)
        
        result = service.update_progress(
            course_id="test-course",
            concepts_completed=5,
            total_concepts=10,
        )
        
        assert isinstance(result, Progress)


class TestProgressServiceIncrementTime:
    """Tests for ProgressService.increment_time()."""
    
    def test_increment_time_creates_progress_if_missing(
        self, mock_database
    ):
        """Should create progress record if it doesn't exist."""
        service = ProgressService(database=mock_database)
        
        progress = service.increment_time("new-course", 30)
        
        assert progress.course_id == "new-course"
        assert progress.time_spent_minutes == 30
    
    def test_increment_time_adds_to_existing(
        self, mock_database
    ):
        """Should add time to existing progress."""
        mock_database.save_progress({
            "course_id": "test-course",
            "time_spent_minutes": 60,
        })
        
        service = ProgressService(database=mock_database)
        progress = service.increment_time("test-course", 30)
        
        assert progress.time_spent_minutes == 90


class TestProgressServiceGetAllProgress:
    """Tests for ProgressService.get_all_progress()."""
    
    def test_get_all_progress_returns_empty_list(
        self, mock_database
    ):
        """Should return empty list when no progress exists."""
        service = ProgressService(database=mock_database)
        progress_list = service.get_all_progress()
        
        assert progress_list == []
    
    def test_get_all_progress_returns_all_courses(
        self, mock_database
    ):
        """Should return progress for all courses."""
        mock_database.save_progress({
            "course_id": "course-1",
            "completion_percentage": 0.5,
        })
        mock_database.save_progress({
            "course_id": "course-2",
            "completion_percentage": 0.8,
        })
        
        service = ProgressService(database=mock_database)
        progress_list = service.get_all_progress()
        
        assert len(progress_list) == 2
        assert all(isinstance(p, Progress) for p in progress_list)
        course_ids = {p.course_id for p in progress_list}
        assert course_ids == {"course-1", "course-2"}


class TestProgressServiceGetLearningStats:
    """Tests for ProgressService.get_learning_stats()."""
    
    def test_get_learning_stats_returns_zeros_when_empty(
        self, mock_database
    ):
        """Should return zeros when no learning data exists."""
        service = ProgressService(database=mock_database)
        stats = service.get_learning_stats()
        
        assert isinstance(stats, LearningStats)
        assert stats.total_courses == 0
        assert stats.concepts_mastered == 0
        assert stats.hours_learned == 0.0
        assert stats.current_streak == 0
    
    def test_get_learning_stats_aggregates_data(
        self, mock_database
    ):
        """Should aggregate stats from all courses."""
        # Create progress for multiple courses
        mock_database.save_progress({
            "course_id": "course-1",
            "concepts_completed": 10,
            "total_concepts": 20,
            "time_spent_minutes": 120,
        })
        mock_database.save_progress({
            "course_id": "course-2",
            "concepts_completed": 5,
            "total_concepts": 10,
            "time_spent_minutes": 60,
        })
        
        service = ProgressService(database=mock_database)
        stats = service.get_learning_stats()
        
        assert stats.total_courses == 2
        assert stats.concepts_mastered == 15
        assert stats.total_concepts == 30
        assert stats.hours_learned == 3.0  # 180 minutes = 3 hours


class TestProgressServiceQuizHistory:
    """Tests for quiz history methods."""
    
    def test_get_quiz_history_returns_empty_for_new_course(
        self, mock_database
    ):
        """Should return empty list for course with no quizzes."""
        service = ProgressService(database=mock_database)
        history = service.get_quiz_history("new-course")
        
        assert history == []
    
    def test_get_quiz_history_returns_quiz_results(
        self, mock_database
    ):
        """Should return QuizResult objects."""
        # Save a quiz result
        mock_database.save_quiz_result({
            "course_id": "test-course",
            "module_id": "module-1",
            "module_title": "Test Module",
            "quiz_id": "quiz-1",
            "score": 0.85,
            "correct_count": 17,
            "total_questions": 20,
            "weak_concepts": ["concept-1", "concept-2"],
            "feedback": "Good job!",
            "passed": True,
        })
        
        service = ProgressService(database=mock_database)
        history = service.get_quiz_history("test-course")
        
        assert len(history) == 1
        assert isinstance(history[0], QuizResult)
        assert history[0].score == 0.85
        assert history[0].passed is True
        assert history[0].weak_concepts == ["concept-1", "concept-2"]
    
    def test_save_quiz_result_returns_id(
        self, mock_database
    ):
        """Should return the ID of the saved record."""
        service = ProgressService(database=mock_database)
        
        result = QuizResult(
            quiz_id="quiz-1",
            course_id="test-course",
            module_id="module-1",
            score=0.9,
            correct_count=9,
            total_questions=10,
            passed=True,
        )
        
        record_id = service.save_quiz_result(result)
        
        assert isinstance(record_id, int)
        assert record_id > 0
    
    def test_get_all_quiz_history_limits_results(
        self, mock_database
    ):
        """Should respect the limit parameter."""
        service = ProgressService(database=mock_database)
        
        # Save multiple quiz results
        for i in range(5):
            mock_database.save_quiz_result({
                "course_id": f"course-{i}",
                "module_id": "module-1",
                "quiz_id": f"quiz-{i}",
                "score": 0.8,
                "correct_count": 8,
                "total_questions": 10,
            })
        
        history = service.get_all_quiz_history(limit=3)
        
        assert len(history) == 3


class TestProgressServiceDeleteCourseProgress:
    """Tests for ProgressService.delete_course_progress()."""
    
    def test_delete_course_progress_returns_false_when_none(
        self, mock_database
    ):
        """Should return False when no progress exists."""
        service = ProgressService(database=mock_database)
        result = service.delete_course_progress("nonexistent")
        
        assert result is False
    
    def test_delete_course_progress_returns_true_when_deleted(
        self, mock_database
    ):
        """Should return True when progress is deleted."""
        mock_database.save_progress({
            "course_id": "test-course",
            "completion_percentage": 0.5,
        })
        
        service = ProgressService(database=mock_database)
        result = service.delete_course_progress("test-course")
        
        assert result is True
    
    def test_delete_course_progress_removes_data(
        self, mock_database
    ):
        """Should remove all data for the course."""
        mock_database.save_progress({
            "course_id": "test-course",
            "completion_percentage": 0.5,
        })
        
        service = ProgressService(database=mock_database)
        service.delete_course_progress("test-course")
        
        # Verify data is gone
        progress = service.get_course_progress("test-course")
        assert progress.completion_percentage == 0.0


class TestProgressServiceStreakTracking:
    """Tests for streak tracking methods."""
    
    def test_record_activity_does_not_raise(
        self, mock_database
    ):
        """Should record activity without errors."""
        service = ProgressService(database=mock_database)
        
        # Should not raise
        service.record_activity(
            minutes_learned=30,
            concepts_completed=2,
            quizzes_taken=1,
        )
    
    def test_get_streak_returns_dict(
        self, mock_database
    ):
        """Should return streak information as dict."""
        service = ProgressService(database=mock_database)
        streak = service.get_streak()
        
        assert isinstance(streak, dict)
        assert "current_streak" in streak
        assert "longest_streak" in streak


class TestProgressServiceEdgeCases:
    """Tests for edge cases."""
    
    def test_quiz_result_with_datetime_object(
        self, mock_database
    ):
        """Should handle quiz result with datetime object."""
        from datetime import datetime
        
        mock_database.save_quiz_result({
            "course_id": "test",
            "module_id": "m1",
            "quiz_id": "q1",
            "score": 0.9,
            "correct_count": 9,
            "total_questions": 10,
            "completed_at": datetime.now().isoformat(),
        })
        
        service = ProgressService(database=mock_database)
        history = service.get_quiz_history("test")
        
        assert len(history) == 1
        assert isinstance(history[0].completed_at, datetime)
    
    def test_update_progress_with_no_time(
        self, mock_database
    ):
        """Should handle update without time increment."""
        service = ProgressService(database=mock_database)
        
        progress = service.update_progress(
            course_id="test",
            concepts_completed=5,
            total_concepts=10,
        )
        
        assert progress.time_spent_minutes == 0
