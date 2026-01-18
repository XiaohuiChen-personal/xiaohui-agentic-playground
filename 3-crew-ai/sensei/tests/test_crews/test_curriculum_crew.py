"""Unit tests for CurriculumCrew with mocked LLM.

These tests verify the CurriculumCrew's business logic without making
actual LLM API calls. All CrewAI components are mocked to return
predictable outputs via the output_pydantic feature.
"""

from unittest.mock import MagicMock, patch

import pytest

from sensei.crews.curriculum_crew import CurriculumCrew
from sensei.models.enums import ExperienceLevel, LearningStyle
from sensei.models.schemas import (
    ConceptOutput,
    Course,
    CourseOutput,
    ModuleOutput,
    UserPreferences,
)


# ==================== FIXTURES ====================


@pytest.fixture
def valid_course_output():
    """Return a valid CourseOutput from the crew."""
    return CourseOutput(
        title="Python Basics",
        description="A comprehensive course for learning Python programming",
        modules=[
            ModuleOutput(
                title="Introduction to Python",
                description="Learn the basics of Python syntax",
                order=0,
                estimated_minutes=45,
                concepts=[
                    ConceptOutput(
                        title="Variables",
                        content="Variables store data values in memory.",
                        order=0,
                    ),
                    ConceptOutput(
                        title="Data Types",
                        content="Python has several built-in data types.",
                        order=1,
                    ),
                ],
            ),
            ModuleOutput(
                title="Control Flow",
                description="Learn about conditionals and loops",
                order=1,
                estimated_minutes=60,
                concepts=[
                    ConceptOutput(
                        title="If Statements",
                        content="Conditionally execute code blocks.",
                        order=0,
                    ),
                ],
            ),
        ],
    )


# ==================== TEST: CREATE CURRICULUM ====================


class TestCurriculumCrewCreateCurriculum:
    """Tests for CurriculumCrew.create_curriculum()."""
    
    def test_create_curriculum_returns_course(self, valid_course_output):
        """Should return a Course object on success."""
        crew = CurriculumCrew()
        
        with patch.object(crew, 'crew') as mock_crew_method:
            mock_result = MagicMock()
            mock_result.pydantic = valid_course_output
            mock_crew_instance = MagicMock()
            mock_crew_instance.kickoff.return_value = mock_result
            mock_crew_method.return_value = mock_crew_instance
            
            course = crew.create_curriculum("Python Basics")
            
            assert isinstance(course, Course)
            assert course.title == "Python Basics"
    
    def test_create_curriculum_parses_modules(self, valid_course_output):
        """Should correctly parse modules from output."""
        crew = CurriculumCrew()
        
        with patch.object(crew, 'crew') as mock_crew_method:
            mock_result = MagicMock()
            mock_result.pydantic = valid_course_output
            mock_crew_instance = MagicMock()
            mock_crew_instance.kickoff.return_value = mock_result
            mock_crew_method.return_value = mock_crew_instance
            
            course = crew.create_curriculum("Python Basics")
            
            assert len(course.modules) == 2
            assert course.modules[0].title == "Introduction to Python"
            assert course.modules[1].title == "Control Flow"
    
    def test_create_curriculum_parses_concepts(self, valid_course_output):
        """Should correctly parse concepts from output."""
        crew = CurriculumCrew()
        
        with patch.object(crew, 'crew') as mock_crew_method:
            mock_result = MagicMock()
            mock_result.pydantic = valid_course_output
            mock_crew_instance = MagicMock()
            mock_crew_instance.kickoff.return_value = mock_result
            mock_crew_method.return_value = mock_crew_instance
            
            course = crew.create_curriculum("Python Basics")
            
            assert len(course.modules[0].concepts) == 2
            assert course.modules[0].concepts[0].title == "Variables"
            assert course.modules[0].concepts[1].title == "Data Types"
    
    def test_create_curriculum_passes_user_prefs(self, valid_course_output):
        """Should pass user preferences to the crew."""
        crew = CurriculumCrew()
        
        with patch.object(crew, 'crew') as mock_crew_method:
            mock_result = MagicMock()
            mock_result.pydantic = valid_course_output
            mock_crew_instance = MagicMock()
            mock_crew_instance.kickoff.return_value = mock_result
            mock_crew_method.return_value = mock_crew_instance
            
            user_prefs = UserPreferences(
                experience_level=ExperienceLevel.ADVANCED,
                learning_style=LearningStyle.HANDS_ON,
                goals="Become a Python expert",
            )
            crew.create_curriculum("Python Basics", user_prefs)
            
            call_args = mock_crew_instance.kickoff.call_args
            inputs = call_args.kwargs.get("inputs", {})
            
            assert inputs["experience_level"] == "advanced"
            assert inputs["learning_style"] == "hands_on"
            assert inputs["goals"] == "Become a Python expert"
    
    def test_create_curriculum_default_user_prefs(self, valid_course_output):
        """Should use default preferences if not provided."""
        crew = CurriculumCrew()
        
        with patch.object(crew, 'crew') as mock_crew_method:
            mock_result = MagicMock()
            mock_result.pydantic = valid_course_output
            mock_crew_instance = MagicMock()
            mock_crew_instance.kickoff.return_value = mock_result
            mock_crew_method.return_value = mock_crew_instance
            
            crew.create_curriculum("Python Basics", None)
            
            call_args = mock_crew_instance.kickoff.call_args
            inputs = call_args.kwargs.get("inputs", {})
            
            # Default experience level is beginner
            assert inputs["experience_level"] == "beginner"
    
    def test_create_curriculum_raises_for_empty_topic(self):
        """Should raise ValueError for empty topic."""
        crew = CurriculumCrew()
        
        with pytest.raises(ValueError, match="Topic cannot be empty"):
            crew.create_curriculum("")
    
    def test_create_curriculum_raises_for_whitespace_topic(self):
        """Should raise ValueError for whitespace-only topic."""
        crew = CurriculumCrew()
        
        with pytest.raises(ValueError, match="Topic cannot be empty"):
            crew.create_curriculum("   ")
    
    def test_create_curriculum_strips_topic(self, valid_course_output):
        """Should strip whitespace from topic."""
        crew = CurriculumCrew()
        
        with patch.object(crew, 'crew') as mock_crew_method:
            mock_result = MagicMock()
            mock_result.pydantic = valid_course_output
            mock_crew_instance = MagicMock()
            mock_crew_instance.kickoff.return_value = mock_result
            mock_crew_method.return_value = mock_crew_instance
            
            crew.create_curriculum("  Python Basics  ")
            
            call_args = mock_crew_instance.kickoff.call_args
            inputs = call_args.kwargs.get("inputs", {})
            
            assert inputs["topic"] == "Python Basics"
    
    def test_create_curriculum_raises_on_no_pydantic_output(self):
        """Should raise RuntimeError when pydantic output is None."""
        crew = CurriculumCrew()
        
        with patch.object(crew, 'crew') as mock_crew_method:
            mock_result = MagicMock()
            mock_result.pydantic = None
            mock_result.raw = "Some raw text output"
            mock_crew_instance = MagicMock()
            mock_crew_instance.kickoff.return_value = mock_result
            mock_crew_method.return_value = mock_crew_instance
            
            with pytest.raises(RuntimeError, match="Failed to get structured output"):
                crew.create_curriculum("Python Basics")


# ==================== TEST: OUTPUT TO COURSE ====================


class TestCurriculumCrewOutputToCourse:
    """Tests for _output_to_course() method."""
    
    def test_output_to_course_full_data(self):
        """Should convert complete CourseOutput to Course."""
        crew = CurriculumCrew()
        output = CourseOutput(
            title="My Course",
            description="A great course",
            modules=[
                ModuleOutput(
                    title="Module 1",
                    description="First module",
                    order=0,
                    estimated_minutes=30,
                    concepts=[
                        ConceptOutput(title="Concept 1", content="Content 1", order=0),
                    ],
                ),
            ],
        )
        
        course = crew._output_to_course(output)
        
        assert course.title == "My Course"
        assert course.description == "A great course"
        assert len(course.modules) == 1
        assert course.modules[0].title == "Module 1"
        # Auto-generated fields should exist
        assert course.id is not None
        assert course.created_at is not None
    
    def test_output_to_course_empty_modules(self):
        """Should handle empty modules list."""
        crew = CurriculumCrew()
        output = CourseOutput(
            title="Empty Course",
            description="No modules",
            modules=[],
        )
        
        course = crew._output_to_course(output)
        
        assert len(course.modules) == 0
    
    def test_output_to_course_preserves_order(self):
        """Should preserve module and concept order."""
        crew = CurriculumCrew()
        output = CourseOutput(
            title="Course",
            description="",
            modules=[
                ModuleOutput(
                    title="Module A",
                    order=5,
                    estimated_minutes=60,
                    concepts=[
                        ConceptOutput(title="Concept X", order=10),
                    ],
                ),
            ],
        )
        
        course = crew._output_to_course(output)
        
        assert course.modules[0].order == 5
        assert course.modules[0].concepts[0].order == 10
    
    def test_output_to_course_generates_ids(self):
        """Should generate IDs for course, modules, and concepts."""
        crew = CurriculumCrew()
        output = CourseOutput(
            title="Test Course",
            modules=[
                ModuleOutput(
                    title="Module 1",
                    concepts=[
                        ConceptOutput(title="Concept 1"),
                    ],
                ),
            ],
        )
        
        course = crew._output_to_course(output)
        
        assert course.id.startswith("course-")
        assert course.modules[0].id.startswith("module-")
        assert course.modules[0].concepts[0].id.startswith("concept-")


# ==================== TEST: EDGE CASES ====================


class TestCurriculumCrewEdgeCases:
    """Edge case tests for CurriculumCrew."""
    
    def test_unicode_in_output(self):
        """Should handle unicode characters in output."""
        crew = CurriculumCrew()
        
        with patch.object(crew, 'crew') as mock_crew_method:
            mock_result = MagicMock()
            mock_result.pydantic = CourseOutput(
                title="学习Python",
                description="Python课程 🐍",
                modules=[
                    ModuleOutput(
                        title="基础知识",
                        concepts=[
                            ConceptOutput(title="变量", content="变量是存储数据的容器。"),
                        ],
                    ),
                ],
            )
            mock_crew_instance = MagicMock()
            mock_crew_instance.kickoff.return_value = mock_result
            mock_crew_method.return_value = mock_crew_instance
            
            course = crew.create_curriculum("Python")
            
            assert course.title == "学习Python"
            assert "🐍" in course.description
    
    def test_special_characters_in_topic(self):
        """Should handle special characters in topic."""
        crew = CurriculumCrew()
        
        with patch.object(crew, 'crew') as mock_crew_method:
            mock_result = MagicMock()
            mock_result.pydantic = CourseOutput(title="C++", modules=[])
            mock_crew_instance = MagicMock()
            mock_crew_instance.kickoff.return_value = mock_result
            mock_crew_method.return_value = mock_crew_instance
            
            crew.create_curriculum("C++ & Data Structures (Advanced)")
            
            call_args = mock_crew_instance.kickoff.call_args
            inputs = call_args.kwargs.get("inputs", {})
            
            assert inputs["topic"] == "C++ & Data Structures (Advanced)"
    
    def test_large_output(self):
        """Should handle large course output."""
        crew = CurriculumCrew()
        
        with patch.object(crew, 'crew') as mock_crew_method:
            # Create a large course with many modules and concepts
            modules = []
            for i in range(20):
                concepts = [
                    ConceptOutput(title=f"Concept {j}", content=f"Content for concept {j}.", order=j)
                    for j in range(10)
                ]
                modules.append(ModuleOutput(
                    title=f"Module {i}",
                    description=f"Description for module {i}",
                    order=i,
                    estimated_minutes=60,
                    concepts=concepts,
                ))
            
            mock_result = MagicMock()
            mock_result.pydantic = CourseOutput(
                title="Large Course",
                description="A very large course",
                modules=modules,
            )
            mock_crew_instance = MagicMock()
            mock_crew_instance.kickoff.return_value = mock_result
            mock_crew_method.return_value = mock_crew_instance
            
            course = crew.create_curriculum("Large Topic")
            
            assert len(course.modules) == 20
            assert all(len(m.concepts) == 10 for m in course.modules)
    
    def test_all_experience_levels(self):
        """Should handle all experience levels."""
        crew = CurriculumCrew()
        
        for level in ExperienceLevel:
            with patch.object(crew, 'crew') as mock_crew_method:
                mock_result = MagicMock()
                mock_result.pydantic = CourseOutput(title="Test", modules=[])
                mock_crew_instance = MagicMock()
                mock_crew_instance.kickoff.return_value = mock_result
                mock_crew_method.return_value = mock_crew_instance
                
                user_prefs = UserPreferences(experience_level=level)
                course = crew.create_curriculum("Topic", user_prefs)
                
                assert isinstance(course, Course)
    
    def test_all_learning_styles(self):
        """Should handle all learning styles."""
        crew = CurriculumCrew()
        
        for style in LearningStyle:
            with patch.object(crew, 'crew') as mock_crew_method:
                mock_result = MagicMock()
                mock_result.pydantic = CourseOutput(title="Test", modules=[])
                mock_crew_instance = MagicMock()
                mock_crew_instance.kickoff.return_value = mock_result
                mock_crew_method.return_value = mock_crew_instance
                
                user_prefs = UserPreferences(learning_style=style)
                course = crew.create_curriculum("Topic", user_prefs)
                
                assert isinstance(course, Course)
