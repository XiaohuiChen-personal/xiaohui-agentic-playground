"""SQLite database operations for Sensei.

This module provides database operations for storing and retrieving
user progress, quiz results, and learning session data.
"""

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from sensei.utils.constants import DATABASE_PATH


class Database:
    """SQLite database manager for Sensei.
    
    Handles connection management and provides methods for
    CRUD operations on progress and quiz data.
    """
    
    def __init__(self, db_path: Path | None = None):
        """Initialize the database.
        
        Args:
            db_path: Path to the SQLite database file.
                     Defaults to DATABASE_PATH from constants.
        """
        self.db_path = db_path or DATABASE_PATH
        self._ensure_db_directory()
        self.initialize_tables()
    
    def _ensure_db_directory(self) -> None:
        """Ensure the database directory exists."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections.
        
        Yields:
            sqlite3.Connection: Database connection with row factory set.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def initialize_tables(self) -> None:
        """Create database tables if they don't exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # User progress table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_progress (
                    course_id TEXT PRIMARY KEY,
                    completion_percentage REAL DEFAULT 0.0,
                    modules_completed INTEGER DEFAULT 0,
                    total_modules INTEGER DEFAULT 0,
                    concepts_completed INTEGER DEFAULT 0,
                    total_concepts INTEGER DEFAULT 0,
                    time_spent_minutes INTEGER DEFAULT 0,
                    current_module_idx INTEGER DEFAULT 0,
                    current_concept_idx INTEGER DEFAULT 0,
                    last_accessed TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Quiz results table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS quiz_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    course_id TEXT NOT NULL,
                    module_id TEXT NOT NULL,
                    module_title TEXT,
                    quiz_id TEXT NOT NULL,
                    score REAL NOT NULL,
                    correct_count INTEGER NOT NULL,
                    total_questions INTEGER NOT NULL,
                    weak_concepts TEXT,
                    feedback TEXT,
                    passed INTEGER DEFAULT 0,
                    completed_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (course_id) REFERENCES user_progress(course_id)
                )
            """)
            
            # Concept mastery table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS concept_mastery (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    course_id TEXT NOT NULL,
                    concept_id TEXT NOT NULL,
                    mastery_level REAL DEFAULT 0.0,
                    questions_asked INTEGER DEFAULT 0,
                    times_reviewed INTEGER DEFAULT 0,
                    last_reviewed TEXT,
                    UNIQUE(course_id, concept_id)
                )
            """)
            
            # Learning sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS learning_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    course_id TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    ended_at TEXT,
                    duration_minutes INTEGER DEFAULT 0,
                    concepts_covered INTEGER DEFAULT 0,
                    questions_asked INTEGER DEFAULT 0
                )
            """)
            
            # Daily activity table for streak tracking
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_activity (
                    date TEXT PRIMARY KEY,
                    minutes_learned INTEGER DEFAULT 0,
                    concepts_completed INTEGER DEFAULT 0,
                    quizzes_taken INTEGER DEFAULT 0
                )
            """)
            
            # Learning streak table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS learning_streak (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    current_streak INTEGER DEFAULT 0,
                    longest_streak INTEGER DEFAULT 0,
                    last_activity_date TEXT
                )
            """)
            
            # Initialize streak record if not exists
            cursor.execute("""
                INSERT OR IGNORE INTO learning_streak (id, current_streak, longest_streak)
                VALUES (1, 0, 0)
            """)
    
    def save_progress(self, progress: dict[str, Any]) -> None:
        """Save or update learning progress for a course.
        
        Args:
            progress: Dictionary containing progress data with keys:
                - course_id (required)
                - completion_percentage
                - modules_completed
                - total_modules
                - concepts_completed
                - total_concepts
                - time_spent_minutes
                - current_module_idx
                - current_concept_idx
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO user_progress (
                    course_id, completion_percentage, modules_completed,
                    total_modules, concepts_completed, total_concepts, 
                    time_spent_minutes, current_module_idx,
                    current_concept_idx, last_accessed
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(course_id) DO UPDATE SET
                    completion_percentage = excluded.completion_percentage,
                    modules_completed = excluded.modules_completed,
                    total_modules = excluded.total_modules,
                    concepts_completed = excluded.concepts_completed,
                    total_concepts = excluded.total_concepts,
                    time_spent_minutes = excluded.time_spent_minutes,
                    current_module_idx = excluded.current_module_idx,
                    current_concept_idx = excluded.current_concept_idx,
                    last_accessed = excluded.last_accessed
            """, (
                progress["course_id"],
                progress.get("completion_percentage", 0.0),
                progress.get("modules_completed", 0),
                progress.get("total_modules", 0),
                progress.get("concepts_completed", 0),
                progress.get("total_concepts", 0),
                progress.get("time_spent_minutes", 0),
                progress.get("current_module_idx", 0),
                progress.get("current_concept_idx", 0),
                datetime.now().isoformat(),
            ))
    
    def get_progress(self, course_id: str) -> dict[str, Any] | None:
        """Get learning progress for a specific course.
        
        Args:
            course_id: The unique identifier for the course.
        
        Returns:
            Progress dictionary if found, None otherwise.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT * FROM user_progress WHERE course_id = ?",
                (course_id,)
            )
            row = cursor.fetchone()
            
            if row is None:
                return None
            
            return dict(row)
    
    def get_all_progress(self) -> list[dict[str, Any]]:
        """Get learning progress for all courses.
        
        Returns:
            List of progress dictionaries, sorted by last_accessed (newest first).
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT * FROM user_progress ORDER BY last_accessed DESC"
            )
            rows = cursor.fetchall()
            
            return [dict(row) for row in rows]
    
    def delete_progress(self, course_id: str) -> bool:
        """Delete progress for a specific course.
        
        Args:
            course_id: The unique identifier for the course.
        
        Returns:
            True if a record was deleted, False otherwise.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute(
                "DELETE FROM user_progress WHERE course_id = ?",
                (course_id,)
            )
            
            return cursor.rowcount > 0
    
    def save_quiz_result(self, result: dict[str, Any]) -> int:
        """Save a quiz result.
        
        Args:
            result: Dictionary containing quiz result data with keys:
                - course_id (required)
                - module_id (required)
                - module_title (optional, for display purposes)
                - quiz_id (required)
                - score (required, 0.0-1.0)
                - correct_count (required)
                - total_questions (required)
                - weak_concepts (optional, comma-separated string)
                - feedback (optional)
                - passed (optional, boolean)
        
        Returns:
            The ID of the inserted record.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Convert weak_concepts list to comma-separated string if needed
            weak_concepts = result.get("weak_concepts", "")
            if isinstance(weak_concepts, list):
                weak_concepts = ",".join(weak_concepts)
            
            cursor.execute("""
                INSERT INTO quiz_results (
                    course_id, module_id, module_title, quiz_id, score, correct_count,
                    total_questions, weak_concepts, feedback, passed, completed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                result["course_id"],
                result["module_id"],
                result.get("module_title", ""),
                result["quiz_id"],
                result["score"],
                result["correct_count"],
                result["total_questions"],
                weak_concepts,
                result.get("feedback", ""),
                1 if result.get("passed", False) else 0,
                datetime.now().isoformat(),
            ))
            
            # Update daily activity for streak tracking
            self._update_daily_activity(conn, quizzes_taken=1)
            
            return cursor.lastrowid
    
    def get_quiz_history(self, course_id: str) -> list[dict[str, Any]]:
        """Get quiz history for a specific course.
        
        Args:
            course_id: The unique identifier for the course.
        
        Returns:
            List of quiz result dictionaries, sorted by completed_at (newest first).
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM quiz_results 
                WHERE course_id = ? 
                ORDER BY completed_at DESC
            """, (course_id,))
            
            rows = cursor.fetchall()
            return self._process_quiz_rows(rows)
    
    def get_all_quiz_history(self, limit: int = 50) -> list[dict[str, Any]]:
        """Get quiz history across all courses.
        
        Used by Progress page to display recent quiz history table.
        
        Args:
            limit: Maximum number of results to return (default 50).
        
        Returns:
            List of quiz result dictionaries, sorted by completed_at (newest first).
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM quiz_results 
                ORDER BY completed_at DESC
                LIMIT ?
            """, (limit,))
            
            rows = cursor.fetchall()
            return self._process_quiz_rows(rows)
    
    def _process_quiz_rows(self, rows) -> list[dict[str, Any]]:
        """Process quiz result rows into dictionaries.
        
        Args:
            rows: Raw database rows.
        
        Returns:
            List of processed quiz result dictionaries.
        """
        results = []
        for row in rows:
            result = dict(row)
            # Convert weak_concepts back to list
            if result.get("weak_concepts"):
                result["weak_concepts"] = result["weak_concepts"].split(",")
            else:
                result["weak_concepts"] = []
            # Convert passed to boolean
            result["passed"] = bool(result.get("passed", 0))
            results.append(result)
        return results
    
    def is_module_quiz_passed(self, course_id: str, module_id: str) -> bool | None:
        """Check if a module quiz has been passed.
        
        Args:
            course_id: The course identifier.
            module_id: The module identifier.
        
        Returns:
            True if passed, False if taken but not passed, None if not taken.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get the most recent quiz result for this module
            cursor.execute("""
                SELECT passed FROM quiz_results 
                WHERE course_id = ? AND module_id = ?
                ORDER BY completed_at DESC
                LIMIT 1
            """, (course_id, module_id))
            
            row = cursor.fetchone()
            if row is None:
                return None  # Quiz not taken
            return bool(row["passed"])
    
    def save_concept_mastery(
        self,
        course_id: str,
        concept_id: str,
        mastery_level: float,
        questions_asked: int = 0,
    ) -> None:
        """Save or update concept mastery level.
        
        Args:
            course_id: The course identifier.
            concept_id: The concept identifier.
            mastery_level: Mastery level between 0.0 and 1.0.
            questions_asked: Number of questions asked about this concept.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO concept_mastery (
                    course_id, concept_id, mastery_level, 
                    questions_asked, times_reviewed, last_reviewed
                ) VALUES (?, ?, ?, ?, 1, ?)
                ON CONFLICT(course_id, concept_id) DO UPDATE SET
                    mastery_level = excluded.mastery_level,
                    questions_asked = concept_mastery.questions_asked + excluded.questions_asked,
                    times_reviewed = concept_mastery.times_reviewed + 1,
                    last_reviewed = excluded.last_reviewed
            """, (
                course_id,
                concept_id,
                mastery_level,
                questions_asked,
                datetime.now().isoformat(),
            ))
    
    def get_concept_mastery(
        self,
        course_id: str,
        concept_id: str,
    ) -> dict[str, Any] | None:
        """Get mastery data for a specific concept.
        
        Args:
            course_id: The course identifier.
            concept_id: The concept identifier.
        
        Returns:
            Mastery dictionary if found, None otherwise.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM concept_mastery 
                WHERE course_id = ? AND concept_id = ?
            """, (course_id, concept_id))
            
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_all_concept_mastery(self, course_id: str) -> list[dict[str, Any]]:
        """Get all concept mastery records for a course.
        
        Used to display mastery levels for all concepts in a course.
        
        Args:
            course_id: The course identifier.
        
        Returns:
            List of mastery dictionaries, sorted by last_reviewed (newest first).
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM concept_mastery 
                WHERE course_id = ?
                ORDER BY last_reviewed DESC
            """, (course_id,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def start_learning_session(self, course_id: str) -> int:
        """Start a new learning session.
        
        Args:
            course_id: The course identifier.
        
        Returns:
            The session ID.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO learning_sessions (course_id, started_at)
                VALUES (?, ?)
            """, (course_id, datetime.now().isoformat()))
            
            return cursor.lastrowid
    
    def end_learning_session(
        self,
        session_id: int,
        concepts_covered: int = 0,
        questions_asked: int = 0,
    ) -> None:
        """End a learning session.
        
        Args:
            session_id: The session ID to end.
            concepts_covered: Number of concepts covered in the session.
            questions_asked: Number of questions asked in the session.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get start time to calculate duration
            cursor.execute(
                "SELECT started_at FROM learning_sessions WHERE id = ?",
                (session_id,)
            )
            row = cursor.fetchone()
            
            if row:
                started_at = datetime.fromisoformat(row["started_at"])
                ended_at = datetime.now()
                duration = int((ended_at - started_at).total_seconds() / 60)
                
                cursor.execute("""
                    UPDATE learning_sessions SET
                        ended_at = ?,
                        duration_minutes = ?,
                        concepts_covered = ?,
                        questions_asked = ?
                    WHERE id = ?
                """, (
                    ended_at.isoformat(),
                    duration,
                    concepts_covered,
                    questions_asked,
                    session_id,
                ))
                
                # Update daily activity for streak tracking
                self._update_daily_activity(
                    conn,
                    minutes_learned=duration,
                    concepts_completed=concepts_covered,
                )
    
    def get_learning_sessions(
        self,
        course_id: str,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Get learning session history for a course.
        
        Args:
            course_id: The course identifier.
            limit: Maximum number of sessions to return (default 20).
        
        Returns:
            List of session dictionaries, sorted by started_at (newest first).
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM learning_sessions 
                WHERE course_id = ?
                ORDER BY started_at DESC
                LIMIT ?
            """, (course_id, limit))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def delete_course_data(self, course_id: str) -> dict[str, int]:
        """Delete all data related to a course.
        
        This cascades deletion to quiz_results, concept_mastery,
        and learning_sessions for the course.
        
        Args:
            course_id: The course identifier.
        
        Returns:
            Dictionary with counts of deleted records per table.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            deleted = {}
            
            # Delete quiz results
            cursor.execute(
                "DELETE FROM quiz_results WHERE course_id = ?",
                (course_id,)
            )
            deleted["quiz_results"] = cursor.rowcount
            
            # Delete concept mastery
            cursor.execute(
                "DELETE FROM concept_mastery WHERE course_id = ?",
                (course_id,)
            )
            deleted["concept_mastery"] = cursor.rowcount
            
            # Delete learning sessions
            cursor.execute(
                "DELETE FROM learning_sessions WHERE course_id = ?",
                (course_id,)
            )
            deleted["learning_sessions"] = cursor.rowcount
            
            # Delete progress
            cursor.execute(
                "DELETE FROM user_progress WHERE course_id = ?",
                (course_id,)
            )
            deleted["progress"] = cursor.rowcount
            
            return deleted
    
    # =========================================================================
    # Streak Tracking Methods
    # =========================================================================
    
    def _update_daily_activity(
        self,
        conn,
        minutes_learned: int = 0,
        concepts_completed: int = 0,
        quizzes_taken: int = 0,
    ) -> None:
        """Update daily activity and streak (internal method).
        
        Args:
            conn: Database connection.
            minutes_learned: Minutes learned in this activity.
            concepts_completed: Concepts completed in this activity.
            quizzes_taken: Quizzes taken in this activity.
        """
        cursor = conn.cursor()
        today = datetime.now().date().isoformat()
        
        # Update daily activity
        cursor.execute("""
            INSERT INTO daily_activity (date, minutes_learned, concepts_completed, quizzes_taken)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(date) DO UPDATE SET
                minutes_learned = daily_activity.minutes_learned + excluded.minutes_learned,
                concepts_completed = daily_activity.concepts_completed + excluded.concepts_completed,
                quizzes_taken = daily_activity.quizzes_taken + excluded.quizzes_taken
        """, (today, minutes_learned, concepts_completed, quizzes_taken))
        
        # Update streak
        cursor.execute("SELECT * FROM learning_streak WHERE id = 1")
        streak_row = cursor.fetchone()
        
        if streak_row:
            last_activity = streak_row["last_activity_date"]
            current_streak = streak_row["current_streak"]
            longest_streak = streak_row["longest_streak"]
            
            if last_activity is None:
                # First activity ever
                new_streak = 1
            elif last_activity == today:
                # Already logged activity today, no change
                new_streak = current_streak
            else:
                yesterday = (datetime.now().date() - timedelta(days=1)).isoformat()
                if last_activity == yesterday:
                    # Consecutive day - increment streak
                    new_streak = current_streak + 1
                else:
                    # Streak broken - reset to 1
                    new_streak = 1
            
            new_longest = max(longest_streak, new_streak)
            
            cursor.execute("""
                UPDATE learning_streak SET
                    current_streak = ?,
                    longest_streak = ?,
                    last_activity_date = ?
                WHERE id = 1
            """, (new_streak, new_longest, today))
    
    def record_activity(
        self,
        minutes_learned: int = 0,
        concepts_completed: int = 0,
        quizzes_taken: int = 0,
    ) -> None:
        """Record learning activity and update streak.
        
        Call this when the user completes any learning activity.
        
        Args:
            minutes_learned: Minutes learned in this activity.
            concepts_completed: Concepts completed in this activity.
            quizzes_taken: Quizzes taken in this activity.
        """
        with self.get_connection() as conn:
            self._update_daily_activity(
                conn, minutes_learned, concepts_completed, quizzes_taken
            )
    
    def get_streak(self) -> dict[str, Any]:
        """Get current streak information.
        
        Returns:
            Dictionary with current_streak, longest_streak, last_activity_date.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM learning_streak WHERE id = 1")
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            return {
                "current_streak": 0,
                "longest_streak": 0,
                "last_activity_date": None,
            }
    
    def get_daily_activity(self, date: str | None = None) -> dict[str, Any] | None:
        """Get activity for a specific date.
        
        Args:
            date: Date in ISO format (YYYY-MM-DD). Defaults to today.
        
        Returns:
            Activity dictionary if found, None otherwise.
        """
        if date is None:
            date = datetime.now().date().isoformat()
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM daily_activity WHERE date = ?",
                (date,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_activity_history(self, days: int = 30) -> list[dict[str, Any]]:
        """Get activity history for the last N days.
        
        Args:
            days: Number of days to retrieve (default 30).
        
        Returns:
            List of daily activity dictionaries, sorted by date (newest first).
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM daily_activity
                ORDER BY date DESC
                LIMIT ?
            """, (days,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_learning_stats(self) -> dict[str, Any]:
        """Get overall learning statistics.
        
        Returns:
            Dictionary with total courses, concepts mastered, hours learned, streak.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get progress stats
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_courses,
                    COALESCE(SUM(concepts_completed), 0) as concepts_mastered,
                    COALESCE(SUM(total_concepts), 0) as total_concepts,
                    COALESCE(SUM(time_spent_minutes), 0) as total_minutes
                FROM user_progress
            """)
            progress_row = cursor.fetchone()
            
            # Get streak
            streak = self.get_streak()
            
            return {
                "total_courses": progress_row["total_courses"],
                "concepts_mastered": progress_row["concepts_mastered"],
                "total_concepts": progress_row["total_concepts"],
                "hours_learned": round(progress_row["total_minutes"] / 60, 1),
                "current_streak": streak["current_streak"],
                "longest_streak": streak["longest_streak"],
            }
