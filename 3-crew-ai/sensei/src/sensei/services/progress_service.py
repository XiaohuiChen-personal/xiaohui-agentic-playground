"""Progress service for tracking learning progress and statistics.

This service provides methods for tracking user progress through courses,
quiz history, and overall learning statistics.
"""

from datetime import datetime
from typing import Any

from sensei.models.schemas import LearningStats, Progress, QuizResult
from sensei.storage.database import Database


class ProgressService:
    """Service for tracking learning progress and statistics.
    
    This service handles:
    - Course progress tracking (completion %, concepts, time)
    - Quiz history management
    - Overall learning statistics and streaks
    
    Example:
        ```python
        service = ProgressService()
        
        # Get progress for a specific course
        progress = service.get_course_progress("course-123")
        print(f"Completion: {progress.completion_display}")
        
        # Get overall stats
        stats = service.get_learning_stats()
        print(f"Total hours: {stats.hours_learned}")
        ```
    """
    
    def __init__(self, database: Database | None = None):
        """Initialize the progress service.
        
        Args:
            database: Optional Database instance. Creates one if not provided.
        """
        self._db = database or Database()
    
    def get_course_progress(self, course_id: str) -> Progress:
        """Get learning progress for a specific course.
        
        Args:
            course_id: The unique identifier for the course.
        
        Returns:
            Progress object for the course. Returns a new Progress
            with 0% completion if no progress exists.
        """
        progress_dict = self._db.get_progress(course_id)
        
        if progress_dict is None:
            # Return empty progress for new course
            return Progress(course_id=course_id)
        
        return Progress.from_db_row(progress_dict)
    
    def update_progress(
        self,
        course_id: str,
        concepts_completed: int,
        total_concepts: int,
        modules_completed: int = 0,
        total_modules: int = 0,
        current_module_idx: int = 0,
        current_concept_idx: int = 0,
        time_spent_minutes: int | None = None,
    ) -> Progress:
        """Update learning progress for a course.
        
        Args:
            course_id: The unique identifier for the course.
            concepts_completed: Number of concepts completed.
            total_concepts: Total number of concepts in course.
            modules_completed: Number of modules completed.
            total_modules: Total number of modules in course.
            current_module_idx: Current module index.
            current_concept_idx: Current concept index within module.
            time_spent_minutes: Optional time to add (incremental).
        
        Returns:
            Updated Progress object.
        """
        # Get existing progress for time accumulation
        existing = self._db.get_progress(course_id)
        existing_time = existing.get("time_spent_minutes", 0) if existing else 0
        
        # Calculate completion percentage
        if total_concepts > 0:
            completion = concepts_completed / total_concepts
        else:
            completion = 0.0
        
        # Build progress dict
        progress_dict = {
            "course_id": course_id,
            "completion_percentage": completion,
            "modules_completed": modules_completed,
            "total_modules": total_modules,
            "concepts_completed": concepts_completed,
            "total_concepts": total_concepts,
            "current_module_idx": current_module_idx,
            "current_concept_idx": current_concept_idx,
            "time_spent_minutes": existing_time + (time_spent_minutes or 0),
        }
        
        self._db.save_progress(progress_dict)
        
        return self.get_course_progress(course_id)
    
    def increment_time(self, course_id: str, minutes: int) -> Progress:
        """Add time to a course's progress.
        
        Convenience method for adding learning time without
        updating other progress fields.
        
        Args:
            course_id: The unique identifier for the course.
            minutes: Minutes to add.
        
        Returns:
            Updated Progress object.
        """
        existing = self._db.get_progress(course_id)
        
        if existing is None:
            # Initialize progress if it doesn't exist
            progress_dict = {
                "course_id": course_id,
                "time_spent_minutes": minutes,
            }
        else:
            existing["time_spent_minutes"] = existing.get("time_spent_minutes", 0) + minutes
            progress_dict = existing
        
        self._db.save_progress(progress_dict)
        return self.get_course_progress(course_id)
    
    def get_all_progress(self) -> list[Progress]:
        """Get learning progress for all courses.
        
        Returns:
            List of Progress objects, sorted by last_accessed (newest first).
        """
        progress_rows = self._db.get_all_progress()
        return [Progress.from_db_row(row) for row in progress_rows]
    
    def get_learning_stats(self) -> LearningStats:
        """Get overall learning statistics.
        
        Returns:
            LearningStats object with aggregate statistics including:
            - total_courses
            - concepts_mastered
            - hours_learned
            - current_streak
            - longest_streak
        """
        stats_dict = self._db.get_learning_stats()
        
        return LearningStats(
            total_courses=stats_dict.get("total_courses", 0),
            concepts_mastered=stats_dict.get("concepts_mastered", 0),
            total_concepts=stats_dict.get("total_concepts", 0),
            hours_learned=stats_dict.get("hours_learned", 0.0),
            current_streak=stats_dict.get("current_streak", 0),
            longest_streak=stats_dict.get("longest_streak", 0),
        )
    
    def get_quiz_history(self, course_id: str) -> list[QuizResult]:
        """Get quiz history for a specific course.
        
        Args:
            course_id: The unique identifier for the course.
        
        Returns:
            List of QuizResult objects, sorted by completed_at (newest first).
        """
        quiz_rows = self._db.get_quiz_history(course_id)
        return [self._quiz_row_to_result(row) for row in quiz_rows]
    
    def get_all_quiz_history(self, limit: int = 50) -> list[QuizResult]:
        """Get quiz history across all courses.
        
        Args:
            limit: Maximum number of results to return.
        
        Returns:
            List of QuizResult objects, sorted by completed_at (newest first).
        """
        quiz_rows = self._db.get_all_quiz_history(limit=limit)
        return [self._quiz_row_to_result(row) for row in quiz_rows]
    
    def save_quiz_result(self, result: QuizResult) -> int:
        """Save a quiz result.
        
        Args:
            result: QuizResult object to save.
        
        Returns:
            The ID of the saved record.
        """
        result_dict = {
            "course_id": result.course_id,
            "module_id": result.module_id,
            "module_title": result.module_title,
            "quiz_id": result.quiz_id,
            "score": result.score,
            "correct_count": result.correct_count,
            "total_questions": result.total_questions,
            "weak_concepts": result.weak_concepts,
            "feedback": result.feedback,
            "passed": result.passed,
        }
        return self._db.save_quiz_result(result_dict)
    
    def delete_course_progress(self, course_id: str) -> bool:
        """Delete all progress data for a course.
        
        Args:
            course_id: The unique identifier for the course.
        
        Returns:
            True if data was deleted, False if no data existed.
        """
        deleted = self._db.delete_course_data(course_id)
        return deleted.get("progress", 0) > 0
    
    def record_activity(
        self,
        minutes_learned: int = 0,
        concepts_completed: int = 0,
        quizzes_taken: int = 0,
    ) -> None:
        """Record learning activity for streak tracking.
        
        Args:
            minutes_learned: Minutes learned in this activity.
            concepts_completed: Concepts completed in this activity.
            quizzes_taken: Quizzes taken in this activity.
        """
        self._db.record_activity(
            minutes_learned=minutes_learned,
            concepts_completed=concepts_completed,
            quizzes_taken=quizzes_taken,
        )
    
    def get_streak(self) -> dict[str, Any]:
        """Get current streak information.
        
        Returns:
            Dictionary with current_streak, longest_streak, last_activity_date.
        """
        return self._db.get_streak()
    
    def _quiz_row_to_result(self, row: dict[str, Any]) -> QuizResult:
        """Convert a database row to a QuizResult object."""
        # Handle datetime conversion
        completed_at = row.get("completed_at")
        if isinstance(completed_at, str):
            completed_at = datetime.fromisoformat(completed_at)
        elif completed_at is None:
            completed_at = datetime.now()
        
        return QuizResult(
            quiz_id=row.get("quiz_id", ""),
            course_id=row.get("course_id", ""),
            module_id=row.get("module_id", ""),
            module_title=row.get("module_title", ""),
            score=row.get("score", 0.0),
            correct_count=row.get("correct_count", 0),
            total_questions=row.get("total_questions", 0),
            weak_concepts=row.get("weak_concepts", []),
            feedback=row.get("feedback", ""),
            passed=row.get("passed", False),
            completed_at=completed_at,
        )
