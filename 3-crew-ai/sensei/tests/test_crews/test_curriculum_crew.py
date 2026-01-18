"""Unit tests for CurriculumCrew with mocked LLM (Flow-based design).

These tests verify the CurriculumCrew's business logic without making
actual LLM API calls. The Flow components are mocked to return
predictable outputs.
"""

from unittest.mock import MagicMock, patch

import pytest

from sensei.models.enums import ExperienceLevel, LearningStyle
from sensei.models.schemas import (
    ConceptOutline,
    ConceptOutput,
    Course,
    CurriculumOutline,
    Module,
    ModuleOutline,
    ModuleOutput,
    UserPreferences,
)


# Path to patch - must be where the name is looked up, not where it's defined
CURRICULUM_FLOW_PATH = 'sensei.crews.curriculum_crew.curriculum_crew.CurriculumFlow'


# ==================== FIXTURES ====================


@pytest.fixture
def valid_curriculum_outline():
    """Return a valid CurriculumOutline from Step 1."""
    return CurriculumOutline(
        title="Python Basics",
        description="A comprehensive course for learning Python programming",
        experience_level="beginner",
        learning_style="reading",
        modules=[
            ModuleOutline(
                title="Introduction to Python",
                description="Learn the basics of Python syntax",
                order=0,
                estimated_minutes=60,
                concepts=[
                    ConceptOutline(title="Variables", order=0),
                    ConceptOutline(title="Data Types", order=1),
                ],
            ),
            ModuleOutline(
                title="Control Flow",
                description="Learn about conditionals and loops",
                order=1,
                estimated_minutes=60,
                concepts=[
                    ConceptOutline(title="If Statements", order=0),
                    ConceptOutline(title="For Loops", order=1),
                ],
            ),
        ],
    )


@pytest.fixture
def valid_module_output_0():
    """Return a valid ModuleOutput for module 0."""
    return ModuleOutput(
        title="Introduction to Python",
        description="Learn the basics of Python syntax and programming fundamentals.",
        order=0,
        estimated_minutes=60,
        concepts=[
            ConceptOutput(
                title="Variables",
                content="Variables are containers that store data values in memory. "
                        "In Python, you don't need to declare variable types explicitly.",
                order=0,
            ),
            ConceptOutput(
                title="Data Types",
                content="Python has several built-in data types including integers, "
                        "floats, strings, and booleans.",
                order=1,
            ),
        ],
    )


@pytest.fixture
def valid_module_output_1():
    """Return a valid ModuleOutput for module 1."""
    return ModuleOutput(
        title="Control Flow",
        description="Learn about conditionals and loops to control program execution.",
        order=1,
        estimated_minutes=60,
        concepts=[
            ConceptOutput(
                title="If Statements",
                content="If statements allow you to conditionally execute code blocks "
                        "based on boolean expressions.",
                order=0,
            ),
            ConceptOutput(
                title="For Loops",
                content="For loops iterate over sequences like lists, tuples, or strings.",
                order=1,
            ),
        ],
    )


@pytest.fixture
def valid_course():
    """Return a valid Course object."""
    return Course(
        title="Python Basics",
        description="A comprehensive course for learning Python programming",
        modules=[
            Module(
                title="Introduction to Python",
                description="Learn the basics",
                order=0,
                estimated_minutes=60,
                concepts=[],
            ),
        ],
    )


# ==================== TEST: CURRICULUM CREW CREATE CURRICULUM ====================


class TestCurriculumCrewCreateCurriculum:
    """Tests for CurriculumCrew.create_curriculum()."""
    
    def test_create_curriculum_returns_course(self, valid_course):
        """Should return a Course object on success."""
        from sensei.crews.curriculum_crew import CurriculumCrew
        
        with patch(CURRICULUM_FLOW_PATH) as MockFlow:
            mock_flow_instance = MagicMock()
            mock_flow_instance.kickoff.return_value = valid_course
            MockFlow.return_value = mock_flow_instance
            
            crew = CurriculumCrew()
            course = crew.create_curriculum("Python Basics")
            
            assert isinstance(course, Course)
            assert course.title == "Python Basics"
    
    def test_create_curriculum_passes_user_prefs(self, valid_course):
        """Should pass user preferences to the flow."""
        from sensei.crews.curriculum_crew import CurriculumCrew
        
        with patch(CURRICULUM_FLOW_PATH) as MockFlow:
            mock_flow_instance = MagicMock()
            mock_flow_instance.kickoff.return_value = valid_course
            MockFlow.return_value = mock_flow_instance
            
            crew = CurriculumCrew()
            user_prefs = UserPreferences(
                experience_level=ExperienceLevel.ADVANCED,
                learning_style=LearningStyle.HANDS_ON,
                goals="Become a Python expert",
            )
            
            crew.create_curriculum("Python Basics", user_prefs)
            
            # Check that the flow was configured with correct values
            assert mock_flow_instance.topic == "Python Basics"
            assert mock_flow_instance.experience_level == "advanced"
            assert mock_flow_instance.learning_style == "hands_on"
            assert mock_flow_instance.goals == "Become a Python expert"
    
    def test_create_curriculum_default_user_prefs(self, valid_course):
        """Should use default preferences if not provided."""
        from sensei.crews.curriculum_crew import CurriculumCrew
        
        with patch(CURRICULUM_FLOW_PATH) as MockFlow:
            mock_flow_instance = MagicMock()
            mock_flow_instance.kickoff.return_value = valid_course
            MockFlow.return_value = mock_flow_instance
            
            crew = CurriculumCrew()
            crew.create_curriculum("Python Basics", None)
            
            # Default experience level is beginner
            assert mock_flow_instance.experience_level == "beginner"
    
    def test_create_curriculum_raises_for_empty_topic(self):
        """Should raise ValueError for empty topic."""
        from sensei.crews.curriculum_crew import CurriculumCrew
        
        crew = CurriculumCrew()
        
        with pytest.raises(ValueError, match="Topic cannot be empty"):
            crew.create_curriculum("")
    
    def test_create_curriculum_raises_for_whitespace_topic(self):
        """Should raise ValueError for whitespace-only topic."""
        from sensei.crews.curriculum_crew import CurriculumCrew
        
        crew = CurriculumCrew()
        
        with pytest.raises(ValueError, match="Topic cannot be empty"):
            crew.create_curriculum("   ")
    
    def test_create_curriculum_strips_topic(self, valid_course):
        """Should strip whitespace from topic."""
        from sensei.crews.curriculum_crew import CurriculumCrew
        
        with patch(CURRICULUM_FLOW_PATH) as MockFlow:
            mock_flow_instance = MagicMock()
            mock_flow_instance.kickoff.return_value = valid_course
            MockFlow.return_value = mock_flow_instance
            
            crew = CurriculumCrew()
            crew.create_curriculum("  Python Basics  ")
            
            assert mock_flow_instance.topic == "Python Basics"
    
    def test_create_curriculum_raises_on_flow_error(self):
        """Should raise RuntimeError when flow fails."""
        from sensei.crews.curriculum_crew import CurriculumCrew
        
        with patch(CURRICULUM_FLOW_PATH) as MockFlow:
            mock_flow_instance = MagicMock()
            mock_flow_instance.kickoff.side_effect = Exception("API Error")
            MockFlow.return_value = mock_flow_instance
            
            crew = CurriculumCrew()
            
            with pytest.raises(RuntimeError, match="Failed to create curriculum"):
                crew.create_curriculum("Python Basics")


# ==================== TEST: CURRICULUM FLOW AGGREGATE ====================


class TestCurriculumFlowAggregate:
    """Tests for CurriculumFlow.aggregate() - Step 3.
    
    This tests the pure Python aggregation logic which doesn't need mocking.
    """
    
    def test_aggregate_returns_course(
        self,
        valid_curriculum_outline,
        valid_module_output_0,
        valid_module_output_1,
    ):
        """Should return a Course object from expanded modules."""
        from sensei.crews.curriculum_crew import CurriculumFlow
        
        # Mock YAML loading to avoid file access
        with patch.object(CurriculumFlow, '_load_yaml', return_value={}):
            flow = CurriculumFlow()
            flow.topic = "Python Basics"
            flow.outline = valid_curriculum_outline
            
            expanded_modules = [valid_module_output_0, valid_module_output_1]
            
            course = flow.aggregate(expanded_modules)
            
            assert isinstance(course, Course)
            assert course.title == "Python Basics"
            assert len(course.modules) == 2
    
    def test_aggregate_sorts_modules_by_order(self, valid_curriculum_outline):
        """Should sort modules by order."""
        from sensei.crews.curriculum_crew import CurriculumFlow
        
        with patch.object(CurriculumFlow, '_load_yaml', return_value={}):
            flow = CurriculumFlow()
            flow.outline = valid_curriculum_outline
            
            # Create modules out of order
            module_1 = ModuleOutput(title="Second", order=1, concepts=[])
            module_0 = ModuleOutput(title="First", order=0, concepts=[])
            
            # Pass in reverse order
            course = flow.aggregate([module_1, module_0])
            
            assert course.modules[0].title == "First"
            assert course.modules[1].title == "Second"
    
    def test_aggregate_generates_ids(self, valid_curriculum_outline):
        """Should generate IDs for course, modules, and concepts."""
        from sensei.crews.curriculum_crew import CurriculumFlow
        
        with patch.object(CurriculumFlow, '_load_yaml', return_value={}):
            flow = CurriculumFlow()
            flow.outline = valid_curriculum_outline
            
            module = ModuleOutput(
                title="Test Module",
                order=0,
                concepts=[
                    ConceptOutput(title="Test Concept", content="Content", order=0),
                ],
            )
            
            course = flow.aggregate([module])
            
            assert course.id.startswith("course-")
            assert course.modules[0].id.startswith("module-")
            assert course.modules[0].concepts[0].id.startswith("concept-")
    
    def test_aggregate_uses_outline_title_when_available(self, valid_curriculum_outline):
        """Should use outline title if available."""
        from sensei.crews.curriculum_crew import CurriculumFlow
        
        with patch.object(CurriculumFlow, '_load_yaml', return_value={}):
            flow = CurriculumFlow()
            flow.topic = "Different Topic"
            flow.outline = valid_curriculum_outline  # Has title "Python Basics"
            
            course = flow.aggregate([])
            
            # Should use outline title, not topic
            assert course.title == "Python Basics"
    
    def test_aggregate_uses_topic_when_no_outline(self):
        """Should use topic if outline is not available."""
        from sensei.crews.curriculum_crew import CurriculumFlow
        
        with patch.object(CurriculumFlow, '_load_yaml', return_value={}):
            flow = CurriculumFlow()
            flow.topic = "My Topic"
            flow.outline = None
            
            course = flow.aggregate([])
            
            assert course.title == "My Topic"


# ==================== TEST: CURRICULUM FLOW FALLBACK ====================


class TestCurriculumFlowFallback:
    """Tests for fallback module creation."""
    
    def test_create_fallback_module(self):
        """Should create a fallback module from outline."""
        from sensei.crews.curriculum_crew import CurriculumFlow
        
        with patch.object(CurriculumFlow, '_load_yaml', return_value={}):
            flow = CurriculumFlow()
            
            outline = ModuleOutline(
                title="Test Module",
                description="Test description",
                order=0,
                estimated_minutes=60,
                concepts=[
                    ConceptOutline(title="Concept 1", order=0),
                    ConceptOutline(title="Concept 2", order=1),
                ],
            )
            
            fallback = flow._create_fallback_module(outline)
            
            assert isinstance(fallback, ModuleOutput)
            assert fallback.title == "Test Module"
            assert len(fallback.concepts) == 2
            assert fallback.concepts[0].title == "Concept 1"
            assert "Concept 1" in fallback.concepts[0].content
    
    def test_create_fallback_module_preserves_order(self):
        """Should preserve order in fallback module."""
        from sensei.crews.curriculum_crew import CurriculumFlow
        
        with patch.object(CurriculumFlow, '_load_yaml', return_value={}):
            flow = CurriculumFlow()
            
            outline = ModuleOutline(
                title="Test",
                order=5,
                estimated_minutes=90,
                concepts=[
                    ConceptOutline(title="A", order=2),
                ],
            )
            
            fallback = flow._create_fallback_module(outline)
            
            assert fallback.order == 5
            assert fallback.estimated_minutes == 90
            assert fallback.concepts[0].order == 2


# ==================== TEST: EDGE CASES ====================


class TestCurriculumCrewEdgeCases:
    """Edge case tests for CurriculumCrew."""
    
    def test_unicode_in_output(self):
        """Should handle unicode characters in output."""
        from sensei.crews.curriculum_crew import CurriculumCrew
        
        with patch(CURRICULUM_FLOW_PATH) as MockFlow:
            mock_flow_instance = MagicMock()
            mock_flow_instance.kickoff.return_value = Course(
                title="学习Python",
                description="Python课程 🐍",
                modules=[],
            )
            MockFlow.return_value = mock_flow_instance
            
            crew = CurriculumCrew()
            course = crew.create_curriculum("Python")
            
            assert course.title == "学习Python"
            assert "🐍" in course.description
    
    def test_special_characters_in_topic(self):
        """Should handle special characters in topic."""
        from sensei.crews.curriculum_crew import CurriculumCrew
        
        with patch(CURRICULUM_FLOW_PATH) as MockFlow:
            mock_flow_instance = MagicMock()
            mock_flow_instance.kickoff.return_value = Course(title="C++", modules=[])
            MockFlow.return_value = mock_flow_instance
            
            crew = CurriculumCrew()
            crew.create_curriculum("C++ & Data Structures (Advanced)")
            
            assert mock_flow_instance.topic == "C++ & Data Structures (Advanced)"
    
    def test_all_experience_levels(self):
        """Should handle all experience levels."""
        from sensei.crews.curriculum_crew import CurriculumCrew
        
        for level in ExperienceLevel:
            with patch(CURRICULUM_FLOW_PATH) as MockFlow:
                mock_flow_instance = MagicMock()
                mock_flow_instance.kickoff.return_value = Course(title="Test", modules=[])
                MockFlow.return_value = mock_flow_instance
                
                crew = CurriculumCrew()
                user_prefs = UserPreferences(experience_level=level)
                course = crew.create_curriculum("Topic", user_prefs)
                
                assert isinstance(course, Course)
    
    def test_all_learning_styles(self):
        """Should handle all learning styles."""
        from sensei.crews.curriculum_crew import CurriculumCrew
        
        for style in LearningStyle:
            with patch(CURRICULUM_FLOW_PATH) as MockFlow:
                mock_flow_instance = MagicMock()
                mock_flow_instance.kickoff.return_value = Course(title="Test", modules=[])
                MockFlow.return_value = mock_flow_instance
                
                crew = CurriculumCrew()
                user_prefs = UserPreferences(learning_style=style)
                course = crew.create_curriculum("Topic", user_prefs)
                
                assert isinstance(course, Course)


# ==================== TEST: INTEGRATION WITH COURSE SERVICE ====================


class TestCurriculumCrewServiceIntegration:
    """Tests for integration with CourseService."""
    
    def test_course_output_is_serializable(self):
        """Course output should be serializable for storage."""
        from sensei.crews.curriculum_crew import CurriculumCrew
        
        with patch(CURRICULUM_FLOW_PATH) as MockFlow:
            mock_flow_instance = MagicMock()
            mock_flow_instance.kickoff.return_value = Course(
                title="Test Course",
                description="A test course",
                modules=[],
            )
            MockFlow.return_value = mock_flow_instance
            
            crew = CurriculumCrew()
            course = crew.create_curriculum("Test Topic")
            
            # Should be serializable to dict
            course_dict = course.model_dump()
            
            assert "id" in course_dict
            assert "title" in course_dict
            assert "created_at" in course_dict
    
    def test_course_has_required_fields_for_service(self):
        """Course should have all fields required by CourseService."""
        from sensei.crews.curriculum_crew import CurriculumCrew
        
        with patch(CURRICULUM_FLOW_PATH) as MockFlow:
            mock_flow_instance = MagicMock()
            mock_flow_instance.kickoff.return_value = Course(
                title="Test Course",
                description="A test course",
                modules=[],
            )
            MockFlow.return_value = mock_flow_instance
            
            crew = CurriculumCrew()
            course = crew.create_curriculum("Test Topic")
            
            # CourseService expects these fields
            assert hasattr(course, 'id')
            assert hasattr(course, 'title')
            assert hasattr(course, 'description')
            assert hasattr(course, 'modules')
            assert hasattr(course, 'created_at')
            assert hasattr(course, 'total_modules')
            assert hasattr(course, 'total_concepts')


# ==================== TEST: PYDANTIC MODEL VALIDATION ====================


class TestPydanticModels:
    """Tests for the new Pydantic outline models."""
    
    def test_concept_outline_creation(self):
        """Should create ConceptOutline with minimal fields."""
        outline = ConceptOutline(title="Variables", order=0)
        
        assert outline.title == "Variables"
        assert outline.order == 0
    
    def test_module_outline_creation(self):
        """Should create ModuleOutline with concepts."""
        outline = ModuleOutline(
            title="Introduction",
            description="Getting started",
            order=0,
            estimated_minutes=60,
            concepts=[
                ConceptOutline(title="C1", order=0),
                ConceptOutline(title="C2", order=1),
            ],
        )
        
        assert outline.title == "Introduction"
        assert len(outline.concepts) == 2
    
    def test_curriculum_outline_creation(self):
        """Should create CurriculumOutline with modules."""
        outline = CurriculumOutline(
            title="Python Basics",
            description="Learn Python",
            experience_level="beginner",
            learning_style="reading",
            modules=[
                ModuleOutline(
                    title="Module 1",
                    order=0,
                    concepts=[ConceptOutline(title="C1", order=0)],
                ),
            ],
        )
        
        assert outline.title == "Python Basics"
        assert len(outline.modules) == 1
        assert outline.experience_level == "beginner"
    
    def test_concept_output_creation(self):
        """Should create ConceptOutput with content."""
        output = ConceptOutput(
            title="Variables",
            content="Variables store data in memory.",
            order=0,
        )
        
        assert output.title == "Variables"
        assert "data" in output.content
    
    def test_module_output_creation(self):
        """Should create ModuleOutput with concepts."""
        output = ModuleOutput(
            title="Introduction",
            description="Getting started with Python",
            order=0,
            estimated_minutes=60,
            concepts=[
                ConceptOutput(title="C1", content="Content 1", order=0),
            ],
        )
        
        assert output.title == "Introduction"
        assert len(output.concepts) == 1
        assert output.concepts[0].content == "Content 1"
