"""Unit tests for CourseService."""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch

from sensei.models.enums import ExperienceLevel, LearningStyle
from sensei.models.schemas import Concept, Course, Module, Progress, UserPreferences
from sensei.services.course_service import CourseService


class TestCourseServiceCreateCourse:
    """Tests for CourseService.create_course() with stub mode."""
    
    def test_create_course_returns_course_object(
        self, mock_file_storage_paths, mock_database
    ):
        """Should return a Course object."""
        service = CourseService(database=mock_database, use_ai=False)
        course = service.create_course("Python Basics")
        
        assert isinstance(course, Course)
    
    def test_create_course_sets_title(
        self, mock_file_storage_paths, mock_database
    ):
        """Should set the course title to the topic."""
        service = CourseService(database=mock_database, use_ai=False)
        course = service.create_course("Machine Learning")
        
        assert course.title == "Machine Learning"
    
    def test_create_course_generates_description(
        self, mock_file_storage_paths, mock_database
    ):
        """Should generate a description for the course."""
        service = CourseService(database=mock_database, use_ai=False)
        course = service.create_course("Data Science")
        
        assert "Data Science" in course.description
        assert len(course.description) > 20
    
    def test_create_course_generates_modules(
        self, mock_file_storage_paths, mock_database
    ):
        """Should generate multiple modules."""
        service = CourseService(database=mock_database, use_ai=False)
        course = service.create_course("React")
        
        assert len(course.modules) >= 3
        assert all(isinstance(m, Module) for m in course.modules)
    
    def test_create_course_generates_concepts(
        self, mock_file_storage_paths, mock_database
    ):
        """Should generate concepts within modules."""
        service = CourseService(database=mock_database, use_ai=False)
        course = service.create_course("Docker")
        
        for module in course.modules:
            assert len(module.concepts) >= 3
            assert all(isinstance(c, Concept) for c in module.concepts)
    
    def test_create_course_saves_to_storage(
        self, mock_file_storage_paths, mock_database
    ):
        """Should save course to file storage."""
        service = CourseService(database=mock_database, use_ai=False)
        course = service.create_course("Kubernetes")
        
        # Verify course can be loaded back
        loaded = service.get_course(course.id)
        assert loaded is not None
        assert loaded.title == "Kubernetes"
    
    def test_create_course_initializes_progress(
        self, mock_file_storage_paths, mock_database
    ):
        """Should initialize progress record with 0%."""
        service = CourseService(database=mock_database, use_ai=False)
        course = service.create_course("TypeScript")
        
        progress = service.get_course_progress(course.id)
        assert progress.course_id == course.id
        assert progress.completion_percentage == 0.0
        assert progress.total_concepts == course.total_concepts
        assert progress.total_modules == course.total_modules
    
    def test_create_course_sets_created_at(
        self, mock_file_storage_paths, mock_database
    ):
        """Should set created_at timestamp."""
        before = datetime.now()
        service = CourseService(database=mock_database, use_ai=False)
        course = service.create_course("Go")
        after = datetime.now()
        
        assert before <= course.created_at <= after
    
    def test_create_course_generates_unique_ids(
        self, mock_file_storage_paths, mock_database
    ):
        """Should generate unique IDs for courses."""
        service = CourseService(database=mock_database, use_ai=False)
        course1 = service.create_course("Python")
        course2 = service.create_course("Python")
        
        assert course1.id != course2.id
    
    def test_create_course_raises_for_empty_topic(
        self, mock_file_storage_paths, mock_database
    ):
        """Should raise ValueError for empty topic."""
        service = CourseService(database=mock_database, use_ai=False)
        
        with pytest.raises(ValueError, match="Topic cannot be empty"):
            service.create_course("")
    
    def test_create_course_raises_for_whitespace_only_topic(
        self, mock_file_storage_paths, mock_database
    ):
        """Should raise ValueError for whitespace-only topic."""
        service = CourseService(database=mock_database, use_ai=False)
        
        with pytest.raises(ValueError, match="Topic cannot be empty"):
            service.create_course("   ")
    
    def test_create_course_strips_whitespace_from_topic(
        self, mock_file_storage_paths, mock_database
    ):
        """Should strip leading/trailing whitespace from topic."""
        service = CourseService(database=mock_database, use_ai=False)
        course = service.create_course("  Python Basics  ")
        
        assert course.title == "Python Basics"
    
    def test_create_course_with_user_prefs(
        self, mock_file_storage_paths, mock_database
    ):
        """Should accept user preferences."""
        service = CourseService(database=mock_database, use_ai=False)
        prefs = UserPreferences(
            name="Test User",
            learning_style=LearningStyle.VISUAL,
            experience_level=ExperienceLevel.BEGINNER,
        )
        
        course = service.create_course("Python Basics", user_prefs=prefs)
        
        assert isinstance(course, Course)


class TestCourseServiceCreateCourseWithAI:
    """Tests for CourseService.create_course() with AI mode."""
    
    def test_create_course_uses_curriculum_crew(
        self, mock_file_storage_paths, mock_database
    ):
        """Should use CurriculumCrew when use_ai=True."""
        # Create a mock CurriculumCrew
        mock_crew = MagicMock()
        mock_course = Course(
            title="AI Generated Python Course",
            description="An AI-generated course about Python",
            modules=[
                Module(
                    title="Getting Started",
                    description="Introduction",
                    concepts=[
                        Concept(title="What is Python?", content="Intro", order=0),
                    ],
                    order=0,
                    estimated_minutes=30,
                ),
            ],
        )
        mock_crew.create_curriculum.return_value = mock_course
        
        service = CourseService(
            database=mock_database,
            curriculum_crew=mock_crew,
            use_ai=True,
        )
        
        course = service.create_course("Python Basics")
        
        # Verify crew was called
        mock_crew.create_curriculum.assert_called_once()
        call_args = mock_crew.create_curriculum.call_args
        assert call_args.kwargs["topic"] == "Python Basics"
        assert isinstance(call_args.kwargs["user_prefs"], UserPreferences)
        
        # Verify course was returned
        assert course.title == "AI Generated Python Course"
    
    def test_create_course_passes_user_prefs_to_crew(
        self, mock_file_storage_paths, mock_database
    ):
        """Should pass user preferences to CurriculumCrew."""
        mock_crew = MagicMock()
        mock_crew.create_curriculum.return_value = Course(
            title="Custom Course",
            description="Test",
            modules=[],
        )
        
        prefs = UserPreferences(
            name="Alice",
            learning_style=LearningStyle.HANDS_ON,
            experience_level=ExperienceLevel.ADVANCED,
        )
        
        service = CourseService(
            database=mock_database,
            curriculum_crew=mock_crew,
            use_ai=True,
        )
        
        service.create_course("Test Topic", user_prefs=prefs)
        
        call_args = mock_crew.create_curriculum.call_args
        assert call_args.kwargs["user_prefs"] == prefs
    
    def test_create_course_handles_crew_failure(
        self, mock_file_storage_paths, mock_database
    ):
        """Should raise RuntimeError when crew fails."""
        mock_crew = MagicMock()
        mock_crew.create_curriculum.side_effect = Exception("LLM API Error")
        
        service = CourseService(
            database=mock_database,
            curriculum_crew=mock_crew,
            use_ai=True,
        )
        
        with pytest.raises(RuntimeError, match="Failed to generate course"):
            service.create_course("Test Topic")
    
    def test_create_course_lazy_initializes_crew(
        self, mock_file_storage_paths, mock_database
    ):
        """Should lazily initialize CurriculumCrew if not provided."""
        mock_course = Course(
            title="Lazy Course",
            description="Test",
            modules=[],
        )
        
        # Patch the import at the location where it's used
        with patch(
            "sensei.crews.curriculum_crew.CurriculumCrew"
        ) as MockCrewClass:
            mock_crew_instance = MagicMock()
            mock_crew_instance.create_curriculum.return_value = mock_course
            MockCrewClass.return_value = mock_crew_instance
            
            # Create service without crew
            service = CourseService(
                database=mock_database,
                use_ai=True,
            )
            
            course = service.create_course("Test Topic")
            
            # Verify CurriculumCrew was instantiated
            MockCrewClass.assert_called_once()
            assert course.title == "Lazy Course"
    
    def test_create_course_saves_ai_course_to_storage(
        self, mock_file_storage_paths, mock_database
    ):
        """Should save AI-generated course to storage."""
        mock_crew = MagicMock()
        mock_course = Course(
            title="AI Course",
            description="Generated by AI",
            modules=[
                Module(
                    title="Module 1",
                    description="First module",
                    concepts=[
                        Concept(title="Concept 1", content="Content", order=0),
                    ],
                    order=0,
                    estimated_minutes=30,
                ),
            ],
        )
        mock_crew.create_curriculum.return_value = mock_course
        
        service = CourseService(
            database=mock_database,
            curriculum_crew=mock_crew,
            use_ai=True,
        )
        
        created = service.create_course("Test")
        
        # Verify course was saved and can be loaded
        loaded = service.get_course(created.id)
        assert loaded is not None
        assert loaded.title == "AI Course"
    
    def test_create_course_initializes_progress_for_ai_course(
        self, mock_file_storage_paths, mock_database
    ):
        """Should initialize progress for AI-generated course."""
        mock_crew = MagicMock()
        mock_course = Course(
            title="AI Course",
            description="Test",
            modules=[
                Module(
                    title="Module 1",
                    description="M1",
                    concepts=[
                        Concept(title="C1", content="Content", order=0),
                        Concept(title="C2", content="Content", order=1),
                    ],
                    order=0,
                    estimated_minutes=30,
                ),
            ],
        )
        mock_crew.create_curriculum.return_value = mock_course
        
        service = CourseService(
            database=mock_database,
            curriculum_crew=mock_crew,
            use_ai=True,
        )
        
        course = service.create_course("Test")
        
        progress = service.get_course_progress(course.id)
        assert progress.completion_percentage == 0.0
        assert progress.total_modules == 1
        assert progress.total_concepts == 2


class TestCourseServiceListCourses:
    """Tests for CourseService.list_courses()."""
    
    def test_list_courses_returns_empty_when_none(
        self, mock_file_storage_paths, mock_database
    ):
        """Should return empty list when no courses exist."""
        service = CourseService(database=mock_database, use_ai=False)
        courses = service.list_courses()
        
        assert courses == []
    
    def test_list_courses_returns_all_courses(
        self, mock_file_storage_paths, mock_database
    ):
        """Should return all courses."""
        service = CourseService(database=mock_database, use_ai=False)
        
        # Create multiple courses
        service.create_course("Python")
        service.create_course("Java")
        service.create_course("Rust")
        
        courses = service.list_courses()
        
        assert len(courses) == 3
    
    def test_list_courses_returns_metadata(
        self, mock_file_storage_paths, mock_database
    ):
        """Should return course metadata."""
        service = CourseService(database=mock_database, use_ai=False)
        service.create_course("Flask")
        
        courses = service.list_courses()
        
        assert len(courses) == 1
        course = courses[0]
        assert "id" in course
        assert "title" in course
        assert "description" in course
        assert "total_modules" in course
        assert "total_concepts" in course


class TestCourseServiceListCoursesWithProgress:
    """Tests for CourseService.list_courses_with_progress()."""
    
    def test_list_courses_with_progress_includes_progress(
        self, mock_file_storage_paths, mock_database
    ):
        """Should include progress for each course."""
        service = CourseService(database=mock_database, use_ai=False)
        service.create_course("Django")
        
        courses = service.list_courses_with_progress()
        
        assert len(courses) == 1
        assert "progress" in courses[0]
        assert isinstance(courses[0]["progress"], Progress)
    
    def test_list_courses_with_progress_shows_actual_progress(
        self, mock_file_storage_paths, mock_database
    ):
        """Should show actual progress values."""
        service = CourseService(database=mock_database, use_ai=False)
        course = service.create_course("FastAPI")
        
        # Update progress
        mock_database.save_progress({
            "course_id": course.id,
            "completion_percentage": 0.5,
            "concepts_completed": 5,
            "total_concepts": 10,
        })
        
        courses = service.list_courses_with_progress()
        
        assert courses[0]["progress"].completion_percentage == 0.5


class TestCourseServiceGetCourse:
    """Tests for CourseService.get_course()."""
    
    def test_get_course_returns_none_for_unknown(
        self, mock_file_storage_paths, mock_database
    ):
        """Should return None for unknown course ID."""
        service = CourseService(database=mock_database, use_ai=False)
        result = service.get_course("nonexistent-id")
        
        assert result is None
    
    def test_get_course_returns_full_course(
        self, mock_file_storage_paths, mock_database
    ):
        """Should return complete Course object."""
        service = CourseService(database=mock_database, use_ai=False)
        created = service.create_course("Node.js")
        
        loaded = service.get_course(created.id)
        
        assert loaded is not None
        assert isinstance(loaded, Course)
        assert loaded.title == "Node.js"
        assert len(loaded.modules) > 0
    
    def test_get_course_preserves_structure(
        self, mock_file_storage_paths, mock_database
    ):
        """Should preserve full course structure."""
        service = CourseService(database=mock_database, use_ai=False)
        created = service.create_course("Vue.js")
        
        loaded = service.get_course(created.id)
        
        assert loaded.total_modules == created.total_modules
        assert loaded.total_concepts == created.total_concepts
        
        for orig_module, loaded_module in zip(created.modules, loaded.modules):
            assert orig_module.title == loaded_module.title
            assert len(orig_module.concepts) == len(loaded_module.concepts)


class TestCourseServiceDeleteCourse:
    """Tests for CourseService.delete_course()."""
    
    def test_delete_course_returns_false_for_unknown(
        self, mock_file_storage_paths, mock_database
    ):
        """Should return False for unknown course."""
        service = CourseService(database=mock_database, use_ai=False)
        result = service.delete_course("nonexistent")
        
        assert result is False
    
    def test_delete_course_returns_true_when_deleted(
        self, mock_file_storage_paths, mock_database
    ):
        """Should return True when course is deleted."""
        service = CourseService(database=mock_database, use_ai=False)
        course = service.create_course("Scala")
        
        result = service.delete_course(course.id)
        
        assert result is True
    
    def test_delete_course_removes_from_storage(
        self, mock_file_storage_paths, mock_database
    ):
        """Should remove course from file storage."""
        service = CourseService(database=mock_database, use_ai=False)
        course = service.create_course("Kotlin")
        
        service.delete_course(course.id)
        
        assert service.get_course(course.id) is None
    
    def test_delete_course_removes_progress(
        self, mock_file_storage_paths, mock_database
    ):
        """Should remove progress data."""
        service = CourseService(database=mock_database, use_ai=False)
        course = service.create_course("Swift")
        
        # Verify progress exists
        progress = mock_database.get_progress(course.id)
        assert progress is not None
        
        # Delete and verify progress removed
        service.delete_course(course.id)
        
        progress = mock_database.get_progress(course.id)
        assert progress is None


class TestCourseServiceCourseExists:
    """Tests for CourseService.course_exists()."""
    
    def test_course_exists_returns_false_for_unknown(
        self, mock_file_storage_paths, mock_database
    ):
        """Should return False for unknown course."""
        service = CourseService(database=mock_database, use_ai=False)
        assert service.course_exists("unknown") is False
    
    def test_course_exists_returns_true_for_existing(
        self, mock_file_storage_paths, mock_database
    ):
        """Should return True for existing course."""
        service = CourseService(database=mock_database, use_ai=False)
        course = service.create_course("C++")
        
        assert service.course_exists(course.id) is True
    
    def test_course_exists_returns_false_after_delete(
        self, mock_file_storage_paths, mock_database
    ):
        """Should return False after course is deleted."""
        service = CourseService(database=mock_database, use_ai=False)
        course = service.create_course("C#")
        
        service.delete_course(course.id)
        
        assert service.course_exists(course.id) is False


class TestCourseServiceStubGeneration:
    """Tests for stub course generation quality."""
    
    def test_stub_generates_proper_module_order(
        self, mock_file_storage_paths, mock_database
    ):
        """Should set correct order on modules."""
        service = CourseService(database=mock_database, use_ai=False)
        course = service.create_course("Test")
        
        for idx, module in enumerate(course.modules):
            assert module.order == idx
    
    def test_stub_generates_proper_concept_order(
        self, mock_file_storage_paths, mock_database
    ):
        """Should set correct order on concepts within modules."""
        service = CourseService(database=mock_database, use_ai=False)
        course = service.create_course("Test")
        
        for module in course.modules:
            for idx, concept in enumerate(module.concepts):
                assert concept.order == idx
    
    def test_stub_sets_estimated_minutes(
        self, mock_file_storage_paths, mock_database
    ):
        """Should set estimated minutes based on concept count."""
        service = CourseService(database=mock_database, use_ai=False)
        course = service.create_course("Test")
        
        for module in course.modules:
            assert module.estimated_minutes > 0
            # Approximately 10 min per concept
            assert module.estimated_minutes == len(module.concepts) * 10
    
    def test_stub_concepts_have_content(
        self, mock_file_storage_paths, mock_database
    ):
        """Should set content for all concepts."""
        service = CourseService(database=mock_database, use_ai=False)
        course = service.create_course("Test")
        
        for module in course.modules:
            for concept in module.concepts:
                assert concept.content != ""
                assert len(concept.content) > 10


class TestCourseServiceEdgeCases:
    """Tests for edge cases and error handling."""
    
    def test_get_course_progress_for_nonexistent(
        self, mock_file_storage_paths, mock_database
    ):
        """Should return empty progress for nonexistent course."""
        service = CourseService(database=mock_database, use_ai=False)
        progress = service.get_course_progress("nonexistent")
        
        assert progress.course_id == "nonexistent"
        assert progress.completion_percentage == 0.0
    
    def test_dict_to_course_handles_missing_fields(
        self, mock_file_storage_paths, mock_database
    ):
        """Should handle course dict with missing fields."""
        service = CourseService(database=mock_database, use_ai=False)
        
        # Minimal course dict
        data = {
            "id": "test",
            "title": "Test",
            "modules": [],
        }
        
        course = service._dict_to_course(data)
        
        assert course.id == "test"
        assert course.title == "Test"
        assert len(course.modules) == 0
    
    def test_dict_to_course_handles_string_datetime(
        self, mock_file_storage_paths, mock_database
    ):
        """Should handle course dict with string datetime."""
        service = CourseService(database=mock_database, use_ai=False)
        
        data = {
            "id": "test",
            "title": "Test",
            "modules": [],
            "created_at": "2026-01-15T10:30:00",
        }
        
        course = service._dict_to_course(data)
        
        assert course.created_at.year == 2026
        assert course.created_at.month == 1
