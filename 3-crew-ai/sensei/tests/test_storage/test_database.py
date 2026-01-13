"""Unit tests for sensei.storage.database module.

Tests cover 100% of database operations including:
- Table initialization
- Progress CRUD operations
- Quiz results CRUD operations
- Concept mastery tracking
- Learning session management
- Streak tracking
- Daily activity tracking
- Learning statistics
"""

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

from sensei.storage.database import Database


class TestDatabaseInitialization:
    """Tests for Database class initialization."""
    
    def test_init_creates_database_file(self, tmp_path: Path):
        """Database file should be created on initialization."""
        db_path = tmp_path / "test.db"
        assert not db_path.exists()
        
        db = Database(db_path=db_path)
        
        assert db_path.exists()
        assert db.db_path == db_path
    
    def test_init_creates_parent_directories(self, tmp_path: Path):
        """Parent directories should be created if they don't exist."""
        db_path = tmp_path / "nested" / "dir" / "test.db"
        
        db = Database(db_path=db_path)
        
        assert db_path.parent.exists()
        assert db_path.exists()
    
    def test_init_creates_all_tables(self, temp_db: Database):
        """All required tables should be created on initialization."""
        with temp_db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
            tables = {row["name"] for row in cursor.fetchall()}
        
        expected_tables = {
            "user_progress",
            "quiz_results",
            "concept_mastery",
            "learning_sessions",
            "daily_activity",
            "learning_streak",
        }
        assert expected_tables.issubset(tables)
    
    def test_init_initializes_streak_record(self, temp_db: Database):
        """Streak record should be initialized with default values."""
        streak = temp_db.get_streak()
        
        assert streak["current_streak"] == 0
        assert streak["longest_streak"] == 0
        assert streak["last_activity_date"] is None


class TestDatabaseConnection:
    """Tests for database connection management."""
    
    def test_get_connection_returns_connection(self, temp_db: Database):
        """get_connection should return a valid SQLite connection."""
        with temp_db.get_connection() as conn:
            assert isinstance(conn, sqlite3.Connection)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            assert cursor.fetchone()[0] == 1
    
    def test_get_connection_commits_on_success(self, temp_db: Database):
        """Changes should be committed when context exits normally."""
        with temp_db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO user_progress (course_id) VALUES (?)",
                ("test-commit",)
            )
        
        # Verify data persisted
        with temp_db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT course_id FROM user_progress WHERE course_id = ?",
                ("test-commit",)
            )
            assert cursor.fetchone() is not None
    
    def test_get_connection_rollbacks_on_error(self, temp_db: Database):
        """Changes should be rolled back when an exception occurs."""
        try:
            with temp_db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO user_progress (course_id) VALUES (?)",
                    ("test-rollback",)
                )
                raise ValueError("Test error")
        except ValueError:
            pass
        
        # Verify data was rolled back
        with temp_db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT course_id FROM user_progress WHERE course_id = ?",
                ("test-rollback",)
            )
            assert cursor.fetchone() is None
    
    def test_get_connection_uses_row_factory(self, temp_db: Database):
        """Connection should use Row factory for dict-like access."""
        temp_db.save_progress({"course_id": "test-row"})
        
        with temp_db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM user_progress WHERE course_id = ?",
                ("test-row",)
            )
            row = cursor.fetchone()
            
            # Should be accessible by column name
            assert row["course_id"] == "test-row"


class TestProgressOperations:
    """Tests for user progress CRUD operations."""
    
    def test_save_progress_creates_new_record(
        self, temp_db: Database, mock_progress_data: dict
    ):
        """save_progress should create a new progress record."""
        temp_db.save_progress(mock_progress_data)
        
        result = temp_db.get_progress(mock_progress_data["course_id"])
        
        assert result is not None
        assert result["course_id"] == mock_progress_data["course_id"]
        assert result["completion_percentage"] == mock_progress_data["completion_percentage"]
        assert result["modules_completed"] == mock_progress_data["modules_completed"]
        assert result["total_modules"] == mock_progress_data["total_modules"]
        assert result["concepts_completed"] == mock_progress_data["concepts_completed"]
        assert result["total_concepts"] == mock_progress_data["total_concepts"]
        assert result["time_spent_minutes"] == mock_progress_data["time_spent_minutes"]
    
    def test_save_progress_updates_existing_record(self, temp_db: Database):
        """save_progress should update an existing record."""
        # Create initial record
        temp_db.save_progress({
            "course_id": "test-update",
            "completion_percentage": 0.25,
            "concepts_completed": 1,
        })
        
        # Update record
        temp_db.save_progress({
            "course_id": "test-update",
            "completion_percentage": 0.75,
            "concepts_completed": 3,
        })
        
        result = temp_db.get_progress("test-update")
        
        assert result["completion_percentage"] == 0.75
        assert result["concepts_completed"] == 3
    
    def test_save_progress_sets_last_accessed(self, temp_db: Database):
        """save_progress should set last_accessed to current timestamp."""
        before = datetime.now()
        temp_db.save_progress({"course_id": "test-timestamp"})
        after = datetime.now()
        
        result = temp_db.get_progress("test-timestamp")
        last_accessed = datetime.fromisoformat(result["last_accessed"])
        
        assert before <= last_accessed <= after
    
    def test_save_progress_with_default_values(self, temp_db: Database):
        """save_progress should use defaults for missing fields."""
        temp_db.save_progress({"course_id": "test-defaults"})
        
        result = temp_db.get_progress("test-defaults")
        
        assert result["completion_percentage"] == 0.0
        assert result["modules_completed"] == 0
        assert result["total_modules"] == 0
        assert result["concepts_completed"] == 0
        assert result["total_concepts"] == 0
        assert result["time_spent_minutes"] == 0
        assert result["current_module_idx"] == 0
        assert result["current_concept_idx"] == 0
    
    def test_get_progress_returns_none_for_nonexistent(self, temp_db: Database):
        """get_progress should return None for non-existent course."""
        result = temp_db.get_progress("nonexistent-course")
        assert result is None
    
    def test_get_all_progress_returns_all_records(self, temp_db: Database):
        """get_all_progress should return all progress records."""
        temp_db.save_progress({"course_id": "course-1"})
        temp_db.save_progress({"course_id": "course-2"})
        temp_db.save_progress({"course_id": "course-3"})
        
        results = temp_db.get_all_progress()
        
        assert len(results) == 3
        course_ids = {r["course_id"] for r in results}
        assert course_ids == {"course-1", "course-2", "course-3"}
    
    def test_get_all_progress_sorted_by_last_accessed(self, temp_db: Database):
        """get_all_progress should return records sorted by last_accessed DESC."""
        # Create records with slight time difference
        temp_db.save_progress({"course_id": "oldest"})
        temp_db.save_progress({"course_id": "middle"})
        temp_db.save_progress({"course_id": "newest"})
        
        results = temp_db.get_all_progress()
        
        # Newest should be first
        assert results[0]["course_id"] == "newest"
        assert results[-1]["course_id"] == "oldest"
    
    def test_get_all_progress_empty_database(self, temp_db: Database):
        """get_all_progress should return empty list when no progress exists."""
        results = temp_db.get_all_progress()
        assert results == []
    
    def test_delete_progress_removes_record(self, temp_db: Database):
        """delete_progress should remove the progress record."""
        temp_db.save_progress({"course_id": "to-delete"})
        assert temp_db.get_progress("to-delete") is not None
        
        result = temp_db.delete_progress("to-delete")
        
        assert result is True
        assert temp_db.get_progress("to-delete") is None
    
    def test_delete_progress_returns_false_for_nonexistent(self, temp_db: Database):
        """delete_progress should return False for non-existent course."""
        result = temp_db.delete_progress("nonexistent")
        assert result is False


class TestQuizResultsOperations:
    """Tests for quiz results CRUD operations."""
    
    def test_save_quiz_result_creates_record(
        self, temp_db: Database, mock_quiz_result: dict
    ):
        """save_quiz_result should create a new quiz result record."""
        result_id = temp_db.save_quiz_result(mock_quiz_result)
        
        assert result_id > 0
        
        history = temp_db.get_quiz_history(mock_quiz_result["course_id"])
        assert len(history) == 1
        assert history[0]["score"] == mock_quiz_result["score"]
        assert history[0]["module_title"] == mock_quiz_result["module_title"]
    
    def test_save_quiz_result_converts_weak_concepts_list_to_string(
        self, temp_db: Database
    ):
        """save_quiz_result should convert weak_concepts list to comma-separated string."""
        result = {
            "course_id": "test",
            "module_id": "mod-1",
            "quiz_id": "quiz-1",
            "score": 0.6,
            "correct_count": 3,
            "total_questions": 5,
            "weak_concepts": ["concept-a", "concept-b", "concept-c"],
        }
        
        temp_db.save_quiz_result(result)
        
        history = temp_db.get_quiz_history("test")
        assert history[0]["weak_concepts"] == ["concept-a", "concept-b", "concept-c"]
    
    def test_save_quiz_result_handles_string_weak_concepts(self, temp_db: Database):
        """save_quiz_result should handle weak_concepts as string."""
        result = {
            "course_id": "test",
            "module_id": "mod-1",
            "quiz_id": "quiz-1",
            "score": 0.6,
            "correct_count": 3,
            "total_questions": 5,
            "weak_concepts": "concept-a,concept-b",
        }
        
        temp_db.save_quiz_result(result)
        
        history = temp_db.get_quiz_history("test")
        assert history[0]["weak_concepts"] == ["concept-a", "concept-b"]
    
    def test_save_quiz_result_handles_empty_weak_concepts(self, temp_db: Database):
        """save_quiz_result should handle empty weak_concepts."""
        result = {
            "course_id": "test",
            "module_id": "mod-1",
            "quiz_id": "quiz-1",
            "score": 1.0,
            "correct_count": 5,
            "total_questions": 5,
        }
        
        temp_db.save_quiz_result(result)
        
        history = temp_db.get_quiz_history("test")
        assert history[0]["weak_concepts"] == []
    
    def test_save_quiz_result_converts_passed_to_int(self, temp_db: Database):
        """save_quiz_result should convert passed boolean to int."""
        temp_db.save_quiz_result({
            "course_id": "test",
            "module_id": "mod-1",
            "quiz_id": "quiz-1",
            "score": 0.9,
            "correct_count": 9,
            "total_questions": 10,
            "passed": True,
        })
        
        history = temp_db.get_quiz_history("test")
        assert history[0]["passed"] is True
    
    def test_save_quiz_result_updates_daily_activity(self, temp_db: Database):
        """save_quiz_result should update daily activity with quiz count."""
        temp_db.save_quiz_result({
            "course_id": "test",
            "module_id": "mod-1",
            "quiz_id": "quiz-1",
            "score": 0.8,
            "correct_count": 4,
            "total_questions": 5,
        })
        
        activity = temp_db.get_daily_activity()
        assert activity is not None
        assert activity["quizzes_taken"] == 1
    
    def test_get_quiz_history_returns_sorted_results(self, temp_db: Database):
        """get_quiz_history should return results sorted by completed_at DESC."""
        for i in range(3):
            temp_db.save_quiz_result({
                "course_id": "test",
                "module_id": f"mod-{i}",
                "quiz_id": f"quiz-{i}",
                "score": 0.7 + i * 0.1,
                "correct_count": 7 + i,
                "total_questions": 10,
            })
        
        history = temp_db.get_quiz_history("test")
        
        assert len(history) == 3
        # Newest should be first
        assert history[0]["quiz_id"] == "quiz-2"
        assert history[-1]["quiz_id"] == "quiz-0"
    
    def test_get_quiz_history_empty_for_no_results(self, temp_db: Database):
        """get_quiz_history should return empty list when no results exist."""
        history = temp_db.get_quiz_history("nonexistent")
        assert history == []
    
    def test_get_all_quiz_history_returns_all_quizzes(self, temp_db: Database):
        """get_all_quiz_history should return quizzes from all courses."""
        # Add quizzes for multiple courses
        for course_num in range(3):
            for quiz_num in range(2):
                temp_db.save_quiz_result({
                    "course_id": f"course-{course_num}",
                    "module_id": f"mod-{quiz_num}",
                    "quiz_id": f"quiz-{course_num}-{quiz_num}",
                    "score": 0.8,
                    "correct_count": 4,
                    "total_questions": 5,
                })
        
        history = temp_db.get_all_quiz_history()
        
        assert len(history) == 6
        # Should include quizzes from all courses
        course_ids = {q["course_id"] for q in history}
        assert course_ids == {"course-0", "course-1", "course-2"}
    
    def test_get_all_quiz_history_sorted_by_date(self, temp_db: Database):
        """get_all_quiz_history should return newest first."""
        for i in range(3):
            temp_db.save_quiz_result({
                "course_id": f"course-{i}",
                "module_id": "mod-1",
                "quiz_id": f"quiz-{i}",
                "score": 0.8,
                "correct_count": 4,
                "total_questions": 5,
            })
        
        history = temp_db.get_all_quiz_history()
        
        # Newest should be first (course-2 was added last)
        assert history[0]["course_id"] == "course-2"
        assert history[-1]["course_id"] == "course-0"
    
    def test_get_all_quiz_history_respects_limit(self, temp_db: Database):
        """get_all_quiz_history should respect the limit parameter."""
        for i in range(10):
            temp_db.save_quiz_result({
                "course_id": "test",
                "module_id": f"mod-{i}",
                "quiz_id": f"quiz-{i}",
                "score": 0.8,
                "correct_count": 4,
                "total_questions": 5,
            })
        
        history = temp_db.get_all_quiz_history(limit=5)
        
        assert len(history) == 5
    
    def test_get_all_quiz_history_empty(self, temp_db: Database):
        """get_all_quiz_history should return empty list when no quizzes exist."""
        history = temp_db.get_all_quiz_history()
        assert history == []


class TestConceptMasteryOperations:
    """Tests for concept mastery tracking."""
    
    def test_save_concept_mastery_creates_record(self, temp_db: Database):
        """save_concept_mastery should create a new mastery record."""
        temp_db.save_concept_mastery(
            course_id="test-course",
            concept_id="concept-1",
            mastery_level=0.8,
            questions_asked=3,
        )
        
        result = temp_db.get_concept_mastery("test-course", "concept-1")
        
        assert result is not None
        assert result["mastery_level"] == 0.8
        assert result["questions_asked"] == 3
        assert result["times_reviewed"] == 1
    
    def test_save_concept_mastery_updates_existing(self, temp_db: Database):
        """save_concept_mastery should update existing record and increment counters."""
        # First save
        temp_db.save_concept_mastery(
            course_id="test-course",
            concept_id="concept-1",
            mastery_level=0.5,
            questions_asked=2,
        )
        
        # Second save
        temp_db.save_concept_mastery(
            course_id="test-course",
            concept_id="concept-1",
            mastery_level=0.9,
            questions_asked=1,
        )
        
        result = temp_db.get_concept_mastery("test-course", "concept-1")
        
        assert result["mastery_level"] == 0.9
        assert result["questions_asked"] == 3  # 2 + 1
        assert result["times_reviewed"] == 2  # Incremented
    
    def test_save_concept_mastery_sets_last_reviewed(self, temp_db: Database):
        """save_concept_mastery should set last_reviewed timestamp."""
        before = datetime.now()
        temp_db.save_concept_mastery("test", "concept-1", 0.7)
        after = datetime.now()
        
        result = temp_db.get_concept_mastery("test", "concept-1")
        last_reviewed = datetime.fromisoformat(result["last_reviewed"])
        
        assert before <= last_reviewed <= after
    
    def test_get_concept_mastery_returns_none_for_nonexistent(
        self, temp_db: Database
    ):
        """get_concept_mastery should return None for non-existent record."""
        result = temp_db.get_concept_mastery("nonexistent", "concept-1")
        assert result is None
    
    def test_get_all_concept_mastery_returns_all_concepts(self, temp_db: Database):
        """get_all_concept_mastery should return all mastery records for a course."""
        course_id = "test-course"
        for i in range(5):
            temp_db.save_concept_mastery(
                course_id=course_id,
                concept_id=f"concept-{i}",
                mastery_level=0.5 + i * 0.1,
            )
        
        mastery = temp_db.get_all_concept_mastery(course_id)
        
        assert len(mastery) == 5
        concept_ids = {m["concept_id"] for m in mastery}
        assert concept_ids == {"concept-0", "concept-1", "concept-2", "concept-3", "concept-4"}
    
    def test_get_all_concept_mastery_sorted_by_last_reviewed(self, temp_db: Database):
        """get_all_concept_mastery should return newest reviewed first."""
        course_id = "test-course"
        for i in range(3):
            temp_db.save_concept_mastery(
                course_id=course_id,
                concept_id=f"concept-{i}",
                mastery_level=0.5,
            )
        
        mastery = temp_db.get_all_concept_mastery(course_id)
        
        # Newest should be first
        assert mastery[0]["concept_id"] == "concept-2"
        assert mastery[-1]["concept_id"] == "concept-0"
    
    def test_get_all_concept_mastery_empty(self, temp_db: Database):
        """get_all_concept_mastery should return empty list for no records."""
        mastery = temp_db.get_all_concept_mastery("nonexistent")
        assert mastery == []
    
    def test_get_all_concept_mastery_only_returns_for_course(self, temp_db: Database):
        """get_all_concept_mastery should only return records for specified course."""
        temp_db.save_concept_mastery("course-1", "concept-a", 0.5)
        temp_db.save_concept_mastery("course-1", "concept-b", 0.6)
        temp_db.save_concept_mastery("course-2", "concept-c", 0.7)
        
        mastery = temp_db.get_all_concept_mastery("course-1")
        
        assert len(mastery) == 2
        assert all(m["course_id"] == "course-1" for m in mastery)


class TestLearningSessionOperations:
    """Tests for learning session management."""
    
    def test_start_learning_session_creates_session(self, temp_db: Database):
        """start_learning_session should create a new session record."""
        session_id = temp_db.start_learning_session("test-course")
        
        assert session_id > 0
        
        with temp_db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM learning_sessions WHERE id = ?",
                (session_id,)
            )
            row = cursor.fetchone()
            
            assert row is not None
            assert row["course_id"] == "test-course"
            assert row["started_at"] is not None
            assert row["ended_at"] is None
    
    def test_end_learning_session_updates_session(self, temp_db: Database):
        """end_learning_session should update the session with end data."""
        session_id = temp_db.start_learning_session("test-course")
        
        temp_db.end_learning_session(
            session_id=session_id,
            concepts_covered=5,
            questions_asked=3,
        )
        
        with temp_db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM learning_sessions WHERE id = ?",
                (session_id,)
            )
            row = cursor.fetchone()
            
            assert row["ended_at"] is not None
            assert row["concepts_covered"] == 5
            assert row["questions_asked"] == 3
            assert row["duration_minutes"] >= 0
    
    def test_end_learning_session_calculates_duration(self, temp_db: Database):
        """end_learning_session should calculate correct duration."""
        session_id = temp_db.start_learning_session("test-course")
        
        # Manually set an earlier start time for predictable duration
        with temp_db.get_connection() as conn:
            cursor = conn.cursor()
            earlier = (datetime.now() - timedelta(minutes=15)).isoformat()
            cursor.execute(
                "UPDATE learning_sessions SET started_at = ? WHERE id = ?",
                (earlier, session_id)
            )
        
        temp_db.end_learning_session(session_id)
        
        with temp_db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT duration_minutes FROM learning_sessions WHERE id = ?",
                (session_id,)
            )
            row = cursor.fetchone()
            
            # Should be approximately 15 minutes (allow for test execution time)
            assert 14 <= row["duration_minutes"] <= 16
    
    def test_end_learning_session_nonexistent_does_nothing(self, temp_db: Database):
        """end_learning_session should handle non-existent session gracefully."""
        # Should not raise an error
        temp_db.end_learning_session(session_id=99999)
    
    def test_end_learning_session_updates_daily_activity(self, temp_db: Database):
        """end_learning_session should update daily activity."""
        session_id = temp_db.start_learning_session("test-course")
        
        temp_db.end_learning_session(
            session_id=session_id,
            concepts_covered=3,
        )
        
        activity = temp_db.get_daily_activity()
        assert activity is not None
        assert activity["concepts_completed"] == 3
    
    def test_get_learning_sessions_returns_sessions(self, temp_db: Database):
        """get_learning_sessions should return session history for a course."""
        course_id = "test-course"
        
        # Create multiple sessions
        for i in range(3):
            session_id = temp_db.start_learning_session(course_id)
            temp_db.end_learning_session(session_id, concepts_covered=i + 1)
        
        sessions = temp_db.get_learning_sessions(course_id)
        
        assert len(sessions) == 3
        assert all(s["course_id"] == course_id for s in sessions)
    
    def test_get_learning_sessions_sorted_by_started_at(self, temp_db: Database):
        """get_learning_sessions should return newest first."""
        course_id = "test-course"
        
        # Create sessions with different concepts_covered to identify them
        for i in range(3):
            session_id = temp_db.start_learning_session(course_id)
            temp_db.end_learning_session(session_id, concepts_covered=i + 1)
        
        sessions = temp_db.get_learning_sessions(course_id)
        
        # Newest (concepts_covered=3) should be first
        assert sessions[0]["concepts_covered"] == 3
        assert sessions[-1]["concepts_covered"] == 1
    
    def test_get_learning_sessions_respects_limit(self, temp_db: Database):
        """get_learning_sessions should respect the limit parameter."""
        course_id = "test-course"
        
        for _ in range(10):
            session_id = temp_db.start_learning_session(course_id)
            temp_db.end_learning_session(session_id)
        
        sessions = temp_db.get_learning_sessions(course_id, limit=5)
        
        assert len(sessions) == 5
    
    def test_get_learning_sessions_empty(self, temp_db: Database):
        """get_learning_sessions should return empty list when no sessions exist."""
        sessions = temp_db.get_learning_sessions("nonexistent")
        assert sessions == []
    
    def test_get_learning_sessions_only_returns_for_course(self, temp_db: Database):
        """get_learning_sessions should only return sessions for specified course."""
        temp_db.start_learning_session("course-1")
        temp_db.start_learning_session("course-1")
        temp_db.start_learning_session("course-2")
        
        sessions = temp_db.get_learning_sessions("course-1")
        
        assert len(sessions) == 2
        assert all(s["course_id"] == "course-1" for s in sessions)


class TestStreakTracking:
    """Tests for learning streak functionality."""
    
    def test_record_activity_starts_streak(self, temp_db: Database):
        """record_activity should start a streak on first activity."""
        temp_db.record_activity(minutes_learned=30)
        
        streak = temp_db.get_streak()
        
        assert streak["current_streak"] == 1
        assert streak["longest_streak"] == 1
        assert streak["last_activity_date"] == datetime.now().date().isoformat()
    
    def test_record_activity_same_day_no_increment(self, temp_db: Database):
        """record_activity should not increment streak for same day."""
        temp_db.record_activity(minutes_learned=30)
        temp_db.record_activity(minutes_learned=20)
        
        streak = temp_db.get_streak()
        
        assert streak["current_streak"] == 1
    
    def test_record_activity_consecutive_day_increments(self, temp_db: Database):
        """record_activity on consecutive day should increment streak."""
        # First activity
        temp_db.record_activity(minutes_learned=30)
        
        # Manually set last activity to yesterday
        yesterday = (datetime.now().date() - timedelta(days=1)).isoformat()
        with temp_db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE learning_streak SET last_activity_date = ? WHERE id = 1",
                (yesterday,)
            )
        
        # Second activity today
        temp_db.record_activity(minutes_learned=20)
        
        streak = temp_db.get_streak()
        
        assert streak["current_streak"] == 2
    
    def test_record_activity_streak_break_resets(self, temp_db: Database):
        """record_activity after streak break should reset to 1."""
        # First activity
        temp_db.record_activity(minutes_learned=30)
        
        # Manually set last activity to 2 days ago (streak broken)
        two_days_ago = (datetime.now().date() - timedelta(days=2)).isoformat()
        with temp_db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE learning_streak SET current_streak = 5, last_activity_date = ? WHERE id = 1",
                (two_days_ago,)
            )
        
        # Activity today
        temp_db.record_activity(minutes_learned=20)
        
        streak = temp_db.get_streak()
        
        assert streak["current_streak"] == 1
    
    def test_record_activity_updates_longest_streak(self, temp_db: Database):
        """record_activity should update longest_streak when exceeded."""
        # Set up existing streak
        with temp_db.get_connection() as conn:
            cursor = conn.cursor()
            yesterday = (datetime.now().date() - timedelta(days=1)).isoformat()
            cursor.execute(
                """UPDATE learning_streak SET 
                   current_streak = 10, longest_streak = 10, 
                   last_activity_date = ? WHERE id = 1""",
                (yesterday,)
            )
        
        # Activity today - should make streak 11
        temp_db.record_activity(minutes_learned=20)
        
        streak = temp_db.get_streak()
        
        assert streak["current_streak"] == 11
        assert streak["longest_streak"] == 11
    
    def test_get_streak_default_values(self, temp_db: Database):
        """get_streak should return default values when no activity."""
        streak = temp_db.get_streak()
        
        assert streak["current_streak"] == 0
        assert streak["longest_streak"] == 0
        assert streak["last_activity_date"] is None


class TestDailyActivity:
    """Tests for daily activity tracking."""
    
    def test_get_daily_activity_returns_today(self, temp_db: Database):
        """get_daily_activity without date should return today's activity."""
        temp_db.record_activity(minutes_learned=45, concepts_completed=3)
        
        activity = temp_db.get_daily_activity()
        
        assert activity is not None
        assert activity["date"] == datetime.now().date().isoformat()
        assert activity["minutes_learned"] == 45
        assert activity["concepts_completed"] == 3
    
    def test_get_daily_activity_specific_date(self, temp_db: Database):
        """get_daily_activity should return activity for specific date."""
        # Record activity
        temp_db.record_activity(minutes_learned=30)
        
        # Query for today
        today = datetime.now().date().isoformat()
        activity = temp_db.get_daily_activity(today)
        
        assert activity is not None
        assert activity["date"] == today
    
    def test_get_daily_activity_returns_none_for_no_activity(
        self, temp_db: Database
    ):
        """get_daily_activity should return None when no activity exists."""
        activity = temp_db.get_daily_activity("2020-01-01")
        assert activity is None
    
    def test_get_daily_activity_accumulates(self, temp_db: Database):
        """Multiple activities on same day should accumulate."""
        temp_db.record_activity(minutes_learned=20, quizzes_taken=1)
        temp_db.record_activity(minutes_learned=30, concepts_completed=2)
        temp_db.record_activity(quizzes_taken=1)
        
        activity = temp_db.get_daily_activity()
        
        assert activity["minutes_learned"] == 50
        assert activity["concepts_completed"] == 2
        assert activity["quizzes_taken"] == 2
    
    def test_get_activity_history_returns_recent_days(self, temp_db: Database):
        """get_activity_history should return activity for recent days."""
        # Record activity for multiple days manually
        today = datetime.now().date()
        
        with temp_db.get_connection() as conn:
            cursor = conn.cursor()
            for i in range(5):
                date = (today - timedelta(days=i)).isoformat()
                cursor.execute(
                    """INSERT INTO daily_activity 
                       (date, minutes_learned, concepts_completed, quizzes_taken)
                       VALUES (?, ?, ?, ?)""",
                    (date, 30, 2, 1)
                )
        
        history = temp_db.get_activity_history(days=3)
        
        assert len(history) == 3
        # Should be sorted newest first
        assert history[0]["date"] == today.isoformat()
    
    def test_get_activity_history_respects_limit(self, temp_db: Database):
        """get_activity_history should respect the days limit."""
        # Record activity
        temp_db.record_activity(minutes_learned=30)
        
        history = temp_db.get_activity_history(days=10)
        
        # Should return whatever exists, up to limit
        assert len(history) <= 10


class TestLearningStats:
    """Tests for overall learning statistics."""
    
    def test_get_learning_stats_empty_database(self, temp_db: Database):
        """get_learning_stats should return zeros for empty database."""
        stats = temp_db.get_learning_stats()
        
        assert stats["total_courses"] == 0
        assert stats["concepts_mastered"] == 0
        assert stats["total_concepts"] == 0
        assert stats["hours_learned"] == 0.0
        assert stats["current_streak"] == 0
        assert stats["longest_streak"] == 0
    
    def test_get_learning_stats_with_data(self, temp_db: Database):
        """get_learning_stats should aggregate data from all courses."""
        # Add progress for multiple courses
        temp_db.save_progress({
            "course_id": "course-1",
            "concepts_completed": 10,
            "total_concepts": 20,
            "time_spent_minutes": 120,
        })
        temp_db.save_progress({
            "course_id": "course-2",
            "concepts_completed": 5,
            "total_concepts": 10,
            "time_spent_minutes": 60,
        })
        
        # Start a streak
        temp_db.record_activity(minutes_learned=30)
        
        stats = temp_db.get_learning_stats()
        
        assert stats["total_courses"] == 2
        assert stats["concepts_mastered"] == 15
        assert stats["total_concepts"] == 30
        assert stats["hours_learned"] == 3.0  # 180 minutes = 3 hours
        assert stats["current_streak"] == 1


class TestDeleteCourseData:
    """Tests for cascading course data deletion."""
    
    def test_delete_course_data_removes_all_related_data(self, temp_db: Database):
        """delete_course_data should remove all data for a course."""
        course_id = "test-course"
        
        # Create progress
        temp_db.save_progress({
            "course_id": course_id,
            "completion_percentage": 0.5,
        })
        
        # Create quiz results
        temp_db.save_quiz_result({
            "course_id": course_id,
            "module_id": "mod-1",
            "quiz_id": "quiz-1",
            "score": 0.8,
            "correct_count": 4,
            "total_questions": 5,
        })
        
        # Create concept mastery
        temp_db.save_concept_mastery(course_id, "concept-1", 0.7)
        
        # Create learning session
        temp_db.start_learning_session(course_id)
        
        # Delete all course data
        deleted = temp_db.delete_course_data(course_id)
        
        # Verify all data was deleted
        assert deleted["progress"] == 1
        assert deleted["quiz_results"] == 1
        assert deleted["concept_mastery"] == 1
        assert deleted["learning_sessions"] == 1
        
        # Verify data is actually gone
        assert temp_db.get_progress(course_id) is None
        assert temp_db.get_quiz_history(course_id) == []
        assert temp_db.get_all_concept_mastery(course_id) == []
        assert temp_db.get_learning_sessions(course_id) == []
    
    def test_delete_course_data_only_affects_specified_course(self, temp_db: Database):
        """delete_course_data should not affect other courses."""
        # Set up data for two courses
        for course_id in ["course-1", "course-2"]:
            temp_db.save_progress({"course_id": course_id})
            temp_db.save_quiz_result({
                "course_id": course_id,
                "module_id": "mod-1",
                "quiz_id": "quiz-1",
                "score": 0.8,
                "correct_count": 4,
                "total_questions": 5,
            })
            temp_db.save_concept_mastery(course_id, "concept-1", 0.7)
            temp_db.start_learning_session(course_id)
        
        # Delete only course-1
        temp_db.delete_course_data("course-1")
        
        # Verify course-1 data is gone
        assert temp_db.get_progress("course-1") is None
        
        # Verify course-2 data still exists
        assert temp_db.get_progress("course-2") is not None
        assert len(temp_db.get_quiz_history("course-2")) == 1
        assert len(temp_db.get_all_concept_mastery("course-2")) == 1
        assert len(temp_db.get_learning_sessions("course-2")) == 1
    
    def test_delete_course_data_returns_zero_for_nonexistent(self, temp_db: Database):
        """delete_course_data should return zeros for non-existent course."""
        deleted = temp_db.delete_course_data("nonexistent")
        
        assert deleted["progress"] == 0
        assert deleted["quiz_results"] == 0
        assert deleted["concept_mastery"] == 0
        assert deleted["learning_sessions"] == 0
    
    def test_delete_course_data_with_multiple_records(self, temp_db: Database):
        """delete_course_data should delete multiple records per table."""
        course_id = "test-course"
        
        # Create multiple quiz results
        for i in range(3):
            temp_db.save_quiz_result({
                "course_id": course_id,
                "module_id": f"mod-{i}",
                "quiz_id": f"quiz-{i}",
                "score": 0.8,
                "correct_count": 4,
                "total_questions": 5,
            })
        
        # Create multiple concept mastery records
        for i in range(5):
            temp_db.save_concept_mastery(course_id, f"concept-{i}", 0.7)
        
        # Create multiple sessions
        for _ in range(2):
            temp_db.start_learning_session(course_id)
        
        deleted = temp_db.delete_course_data(course_id)
        
        assert deleted["quiz_results"] == 3
        assert deleted["concept_mastery"] == 5
        assert deleted["learning_sessions"] == 2
