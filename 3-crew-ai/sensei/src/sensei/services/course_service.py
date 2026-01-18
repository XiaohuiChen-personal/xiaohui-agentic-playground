"""Course service for managing courses and curriculum.

This service provides methods for creating, listing, and managing courses.
Course generation uses the CurriculumCrew for AI-powered curriculum creation,
with a stub fallback for testing without LLM calls.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sensei.models.schemas import Concept, Course, Module, Progress, UserPreferences
from sensei.storage.database import Database
from sensei.storage.file_storage import (
    delete_course,
    list_courses_with_metadata,
    load_course,
    load_user_preferences,
    save_course,
)

if TYPE_CHECKING:
    from sensei.crews.curriculum_crew import CurriculumCrew


class CourseService:
    """Service for managing courses and curriculum.
    
    This service handles:
    - Creating new courses (AI-powered via CurriculumCrew)
    - Listing and retrieving courses
    - Deleting courses and associated data
    
    The service supports two modes:
    - AI mode (default): Uses CurriculumCrew for intelligent course generation
    - Stub mode: Uses static templates for testing without LLM calls
    
    Example:
        ```python
        # With AI (production)
        service = CourseService()
        course = service.create_course("Python Basics")
        
        # Without AI (testing)
        service = CourseService(use_ai=False)
        course = service.create_course("Python Basics")
        ```
    """
    
    def __init__(
        self,
        database: Database | None = None,
        curriculum_crew: "CurriculumCrew | None" = None,
        use_ai: bool = True,
    ):
        """Initialize the course service.
        
        Args:
            database: Optional Database instance for progress management.
            curriculum_crew: Optional CurriculumCrew instance for AI generation.
                If not provided and use_ai=True, will be created on demand.
            use_ai: Whether to use AI for course generation. Set to False
                for testing without LLM calls.
        """
        self._db = database or Database()
        self._curriculum_crew = curriculum_crew
        self._use_ai = use_ai
    
    def create_course(
        self,
        topic: str,
        user_prefs: UserPreferences | None = None,
    ) -> Course:
        """Create a new course for the given topic.
        
        When use_ai=True, this uses the CurriculumCrew to generate
        a personalized curriculum based on the topic and user preferences.
        When use_ai=False, it uses a stub generator for testing.
        
        Args:
            topic: The topic to create a course for.
            user_prefs: Optional user preferences for personalization.
                If not provided, will attempt to load from storage.
        
        Returns:
            The created Course object.
        
        Raises:
            ValueError: If topic is empty or whitespace only.
            RuntimeError: If AI course generation fails (when use_ai=True).
        """
        # Validate topic
        if not topic or not topic.strip():
            raise ValueError("Topic cannot be empty")
        
        # Normalize topic (strip whitespace)
        topic = topic.strip()
        
        # Load user preferences if not provided
        if user_prefs is None:
            prefs_dict = load_user_preferences()
            user_prefs = UserPreferences(**prefs_dict) if prefs_dict else UserPreferences()
        
        # Generate course structure
        if self._use_ai:
            course = self._generate_course_with_ai(topic, user_prefs)
        else:
            course = self._generate_course_stub(topic)
        
        # Save course to file storage
        course_dict = course.model_dump()
        save_course(course_dict)
        
        # Initialize progress record
        self._db.save_progress({
            "course_id": course.id,
            "completion_percentage": 0.0,
            "modules_completed": 0,
            "total_modules": course.total_modules,
            "concepts_completed": 0,
            "total_concepts": course.total_concepts,
            "time_spent_minutes": 0,
            "current_module_idx": 0,
            "current_concept_idx": 0,
        })
        
        return course
    
    def _generate_course_with_ai(
        self,
        topic: str,
        user_prefs: UserPreferences,
    ) -> Course:
        """Generate a course using the CurriculumCrew.
        
        This method lazily initializes the CurriculumCrew if not provided
        during construction.
        
        Args:
            topic: The topic to create a course for.
            user_prefs: User preferences for personalization.
        
        Returns:
            The generated Course object.
        
        Raises:
            RuntimeError: If course generation fails.
        """
        # Lazy initialization of CurriculumCrew
        if self._curriculum_crew is None:
            from sensei.crews.curriculum_crew import CurriculumCrew
            self._curriculum_crew = CurriculumCrew()
        
        try:
            return self._curriculum_crew.create_curriculum(
                topic=topic,
                user_prefs=user_prefs,
            )
        except Exception as e:
            raise RuntimeError(
                f"Failed to generate course for '{topic}': {e}"
            ) from e
    
    def list_courses(self) -> list[dict[str, Any]]:
        """List all courses with basic metadata.
        
        Returns lightweight course info suitable for dashboard display.
        
        Returns:
            List of course metadata dictionaries containing:
            - id, title, description, created_at
            - total_modules, total_concepts
        """
        return list_courses_with_metadata()
    
    def list_courses_with_progress(self) -> list[dict[str, Any]]:
        """List all courses with their progress.
        
        Combines course metadata with progress data for dashboard display.
        
        Returns:
            List of dictionaries with course info and progress.
        """
        courses = list_courses_with_metadata()
        
        for course in courses:
            progress_dict = self._db.get_progress(course["id"])
            if progress_dict:
                course["progress"] = Progress.from_db_row(progress_dict)
            else:
                course["progress"] = Progress(course_id=course["id"])
        
        return courses
    
    def get_course(self, course_id: str) -> Course | None:
        """Get full course details by ID.
        
        Args:
            course_id: The unique identifier for the course.
        
        Returns:
            Course object if found, None otherwise.
        """
        course_dict = load_course(course_id)
        
        if course_dict is None:
            return None
        
        return self._dict_to_course(course_dict)
    
    def delete_course(self, course_id: str) -> bool:
        """Delete a course and all associated data.
        
        Removes:
        - Course JSON file
        - Progress data from database
        - Quiz history from database
        - Concept mastery data from database
        
        Args:
            course_id: The unique identifier for the course.
        
        Returns:
            True if course was deleted, False if it didn't exist.
        """
        # Delete from file storage
        file_deleted = delete_course(course_id)
        
        # Delete from database (progress, quizzes, etc.)
        self._db.delete_course_data(course_id)
        
        return file_deleted
    
    def course_exists(self, course_id: str) -> bool:
        """Check if a course exists.
        
        Args:
            course_id: The unique identifier for the course.
        
        Returns:
            True if course exists, False otherwise.
        """
        return load_course(course_id) is not None
    
    def get_course_progress(self, course_id: str) -> Progress:
        """Get progress for a specific course.
        
        Convenience method that delegates to ProgressService.
        
        Args:
            course_id: The unique identifier for the course.
        
        Returns:
            Progress object for the course.
        """
        progress_dict = self._db.get_progress(course_id)
        
        if progress_dict is None:
            return Progress(course_id=course_id)
        
        return Progress.from_db_row(progress_dict)
    
    def _generate_course_stub(self, topic: str) -> Course:
        """Generate a stub course structure for testing.
        
        Creates a realistic-looking course with 3-5 modules,
        each containing 3-5 concepts. Used when use_ai=False
        or as a fallback in development/testing.
        
        Args:
            topic: The topic for the course.
        
        Returns:
            A Course object with stub content.
        """
        # Create modules based on topic
        modules = self._generate_stub_modules(topic)
        
        course = Course(
            title=f"{topic}",
            description=f"A comprehensive course on {topic}. "
                       f"This course covers fundamental concepts and practical applications.",
            modules=modules,
            created_at=datetime.now(),
        )
        
        return course
    
    def _generate_stub_modules(self, topic: str) -> list[Module]:
        """Generate stub modules for a topic."""
        # Define module templates based on common learning patterns
        module_templates = [
            {
                "title": f"Introduction to {topic}",
                "description": f"Get started with the fundamentals of {topic}.",
                "concepts": [
                    f"What is {topic}?",
                    f"Why learn {topic}?",
                    f"Setting up your environment",
                    f"Your first {topic} example",
                ],
            },
            {
                "title": f"Core Concepts of {topic}",
                "description": f"Master the essential building blocks of {topic}.",
                "concepts": [
                    "Fundamental principles",
                    "Key terminology",
                    "Basic operations",
                    "Common patterns",
                    "Best practices",
                ],
            },
            {
                "title": f"Intermediate {topic}",
                "description": f"Take your {topic} skills to the next level.",
                "concepts": [
                    "Advanced techniques",
                    "Error handling",
                    "Performance optimization",
                    "Debugging strategies",
                ],
            },
            {
                "title": f"Practical {topic}",
                "description": f"Apply {topic} to real-world problems.",
                "concepts": [
                    "Project planning",
                    "Building a complete solution",
                    "Testing and validation",
                    "Deployment basics",
                ],
            },
        ]
        
        modules = []
        for idx, template in enumerate(module_templates):
            concepts = [
                Concept(
                    title=concept_title,
                    content=f"Learn about {concept_title.lower()} in the context of {topic}.",
                    order=concept_idx,
                )
                for concept_idx, concept_title in enumerate(template["concepts"])
            ]
            
            module = Module(
                title=template["title"],
                description=template["description"],
                concepts=concepts,
                order=idx,
                estimated_minutes=len(concepts) * 10,  # ~10 min per concept
            )
            modules.append(module)
        
        return modules
    
    def _dict_to_course(self, data: dict[str, Any]) -> Course:
        """Convert a dictionary to a Course object.
        
        Handles nested module and concept conversion.
        """
        # Convert modules
        modules = []
        for module_data in data.get("modules", []):
            concepts = [
                Concept(**concept_data)
                for concept_data in module_data.get("concepts", [])
            ]
            module = Module(
                id=module_data.get("id", ""),
                title=module_data.get("title", ""),
                description=module_data.get("description", ""),
                concepts=concepts,
                order=module_data.get("order", 0),
                estimated_minutes=module_data.get("estimated_minutes", 30),
            )
            modules.append(module)
        
        # Handle created_at
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        elif created_at is None:
            created_at = datetime.now()
        
        return Course(
            id=data.get("id", ""),
            title=data.get("title", ""),
            description=data.get("description", ""),
            modules=modules,
            created_at=created_at,
        )
