"""Business logic services for Sensei.

This module provides the service layer that bridges the UI with
the storage and CrewAI layers. Services handle business logic,
data validation, and orchestration.

Services:
    UserService: User preferences and onboarding management
    ProgressService: Learning progress and statistics tracking
    CourseService: Course creation and management
    LearningService: Learning session management
    QuizService: Quiz generation and assessment

Example:
    ```python
    from sensei.services import (
        UserService,
        ProgressService,
        CourseService,
        LearningService,
        QuizService,
    )
    
    # Initialize services
    user_service = UserService()
    course_service = CourseService()
    
    # Use services
    if not user_service.is_onboarded():
        # Show onboarding...
        pass
    
    courses = course_service.list_courses()
    ```
"""

from sensei.services.user_service import UserService
from sensei.services.progress_service import ProgressService
from sensei.services.course_service import CourseService
from sensei.services.learning_service import LearningService
from sensei.services.quiz_service import QuizService

__all__ = [
    "UserService",
    "ProgressService",
    "CourseService",
    "LearningService",
    "QuizService",
]
