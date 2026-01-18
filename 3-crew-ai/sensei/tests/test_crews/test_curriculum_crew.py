"""Unit tests for CurriculumCrew with mocked LLM.

These tests verify the CurriculumCrew's business logic without making
actual LLM API calls. All CrewAI components are mocked to return
predictable outputs.
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from sensei.crews.curriculum_crew import CurriculumCrew
from sensei.models.enums import ExperienceLevel, LearningStyle
from sensei.models.schemas import Course, Module, Concept, UserPreferences


# ==================== FIXTURES ====================


@pytest.fixture
def valid_crew_output():
    """Return a valid JSON output from the crew."""
    return json.dumps({
        "title": "Python Basics",
        "description": "A comprehensive course for learning Python programming",
        "modules": [
            {
                "title": "Introduction to Python",
                "description": "Learn the basics of Python syntax",
                "order": 0,
                "estimated_minutes": 45,
                "concepts": [
                    {
                        "title": "Variables",
                        "content": "Variables store data values in memory.",
                        "order": 0,
                    },
                    {
                        "title": "Data Types",
                        "content": "Python has several built-in data types.",
                        "order": 1,
                    },
                ],
            },
            {
                "title": "Control Flow",
                "description": "Learn about conditionals and loops",
                "order": 1,
                "estimated_minutes": 60,
                "concepts": [
                    {
                        "title": "If Statements",
                        "content": "Conditionally execute code blocks.",
                        "order": 0,
                    },
                ],
            },
        ],
    })


@pytest.fixture
def crew_output_with_extra_text(valid_crew_output):
    """Return crew output with text before and after JSON."""
    return f"Here is the curriculum:\n\n{valid_crew_output}\n\nHope this helps!"


# ==================== TEST: CREATE CURRICULUM ====================


class TestCurriculumCrewCreateCurriculum:
    """Tests for CurriculumCrew.create_curriculum()."""
    
    def test_create_curriculum_returns_course(self, valid_crew_output):
        """Should return a Course object on success."""
        crew = CurriculumCrew()
        
        with patch.object(crew, 'crew') as mock_crew_method:
            mock_result = MagicMock()
            mock_result.raw = valid_crew_output
            mock_crew_instance = MagicMock()
            mock_crew_instance.kickoff.return_value = mock_result
            mock_crew_method.return_value = mock_crew_instance
            
            course = crew.create_curriculum("Python Basics")
            
            assert isinstance(course, Course)
            assert course.title == "Python Basics"
    
    def test_create_curriculum_parses_modules(self, valid_crew_output):
        """Should correctly parse modules from output."""
        crew = CurriculumCrew()
        
        with patch.object(crew, 'crew') as mock_crew_method:
            mock_result = MagicMock()
            mock_result.raw = valid_crew_output
            mock_crew_instance = MagicMock()
            mock_crew_instance.kickoff.return_value = mock_result
            mock_crew_method.return_value = mock_crew_instance
            
            course = crew.create_curriculum("Python Basics")
            
            assert len(course.modules) == 2
            assert course.modules[0].title == "Introduction to Python"
            assert course.modules[1].title == "Control Flow"
    
    def test_create_curriculum_parses_concepts(self, valid_crew_output):
        """Should correctly parse concepts from output."""
        crew = CurriculumCrew()
        
        with patch.object(crew, 'crew') as mock_crew_method:
            mock_result = MagicMock()
            mock_result.raw = valid_crew_output
            mock_crew_instance = MagicMock()
            mock_crew_instance.kickoff.return_value = mock_result
            mock_crew_method.return_value = mock_crew_instance
            
            course = crew.create_curriculum("Python Basics")
            
            assert len(course.modules[0].concepts) == 2
            assert course.modules[0].concepts[0].title == "Variables"
            assert course.modules[0].concepts[1].title == "Data Types"
    
    def test_create_curriculum_passes_user_prefs(self, valid_crew_output):
        """Should pass user preferences to the crew."""
        crew = CurriculumCrew()
        
        with patch.object(crew, 'crew') as mock_crew_method:
            mock_result = MagicMock()
            mock_result.raw = valid_crew_output
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
    
    def test_create_curriculum_default_user_prefs(self, valid_crew_output):
        """Should use default preferences if not provided."""
        crew = CurriculumCrew()
        
        with patch.object(crew, 'crew') as mock_crew_method:
            mock_result = MagicMock()
            mock_result.raw = valid_crew_output
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
    
    def test_create_curriculum_strips_topic(self, valid_crew_output):
        """Should strip whitespace from topic."""
        crew = CurriculumCrew()
        
        with patch.object(crew, 'crew') as mock_crew_method:
            mock_result = MagicMock()
            mock_result.raw = valid_crew_output
            mock_crew_instance = MagicMock()
            mock_crew_instance.kickoff.return_value = mock_result
            mock_crew_method.return_value = mock_crew_instance
            
            crew.create_curriculum("  Python Basics  ")
            
            call_args = mock_crew_instance.kickoff.call_args
            inputs = call_args.kwargs.get("inputs", {})
            
            assert inputs["topic"] == "Python Basics"


# ==================== TEST: PARSE CREW OUTPUT ====================


class TestCurriculumCrewParseOutput:
    """Tests for _parse_crew_output() and related methods."""
    
    def test_parse_crew_output_valid_json(self, valid_crew_output):
        """Should parse valid JSON output."""
        crew = CurriculumCrew()
        course = crew._parse_crew_output(valid_crew_output, "Fallback Topic")
        
        assert isinstance(course, Course)
        assert course.title == "Python Basics"
    
    def test_parse_crew_output_extracts_json_from_text(
        self, crew_output_with_extra_text
    ):
        """Should extract JSON from text with surrounding content."""
        crew = CurriculumCrew()
        course = crew._parse_crew_output(crew_output_with_extra_text, "Fallback")
        
        assert isinstance(course, Course)
        assert course.title == "Python Basics"
    
    def test_parse_crew_output_uses_fallback_title(self):
        """Should use fallback topic when title is missing."""
        crew = CurriculumCrew()
        output = json.dumps({
            "description": "A course",
            "modules": [],
        })
        
        course = crew._parse_crew_output(output, "My Fallback Topic")
        
        assert course.title == "My Fallback Topic"
    
    def test_parse_crew_output_invalid_json(self):
        """Should raise RuntimeError for invalid JSON."""
        crew = CurriculumCrew()
        
        with pytest.raises(RuntimeError, match="Failed to parse crew output"):
            crew._parse_crew_output("This is not JSON {invalid}", "Topic")
    
    def test_parse_crew_output_no_json_object(self):
        """Should raise ValueError when no JSON object is found.
        
        Note: _extract_json raises ValueError which is NOT caught by 
        _parse_crew_output's exception handler (only catches JSONDecodeError,
        KeyError, TypeError).
        """
        crew = CurriculumCrew()
        
        # ValueError from _extract_json propagates directly
        with pytest.raises(ValueError, match="No JSON object found"):
            crew._parse_crew_output("Just plain text without braces", "Topic")


# ==================== TEST: EXTRACT JSON ====================


class TestCurriculumCrewExtractJson:
    """Tests for _extract_json() method."""
    
    def test_extract_json_simple(self):
        """Should extract simple JSON object."""
        crew = CurriculumCrew()
        text = '{"key": "value"}'
        
        result = crew._extract_json(text)
        
        assert result == '{"key": "value"}'
    
    def test_extract_json_with_prefix(self):
        """Should extract JSON with text before it."""
        crew = CurriculumCrew()
        text = 'Here is the result: {"key": "value"}'
        
        result = crew._extract_json(text)
        
        assert result == '{"key": "value"}'
    
    def test_extract_json_with_suffix(self):
        """Should extract JSON with text after it."""
        crew = CurriculumCrew()
        text = '{"key": "value"} That is the result.'
        
        result = crew._extract_json(text)
        
        assert result == '{"key": "value"}'
    
    def test_extract_json_with_prefix_and_suffix(self):
        """Should extract JSON with text before and after."""
        crew = CurriculumCrew()
        text = 'Result: {"key": "value"} Done!'
        
        result = crew._extract_json(text)
        
        assert result == '{"key": "value"}'
    
    def test_extract_json_nested(self):
        """Should extract nested JSON object."""
        crew = CurriculumCrew()
        text = 'Output: {"outer": {"inner": 123}} finished'
        
        result = crew._extract_json(text)
        
        assert result == '{"outer": {"inner": 123}}'
        assert json.loads(result)["outer"]["inner"] == 123
    
    def test_extract_json_no_opening_brace(self):
        """Should raise ValueError when no opening brace."""
        crew = CurriculumCrew()
        
        with pytest.raises(ValueError, match="No JSON object found"):
            crew._extract_json("No JSON here}")
    
    def test_extract_json_no_closing_brace(self):
        """Should raise ValueError when no closing brace."""
        crew = CurriculumCrew()
        
        with pytest.raises(ValueError, match="No JSON object found"):
            crew._extract_json("{No closing brace")
    
    def test_extract_json_empty_string(self):
        """Should raise ValueError for empty string."""
        crew = CurriculumCrew()
        
        with pytest.raises(ValueError, match="No JSON object found"):
            crew._extract_json("")
    
    def test_extract_json_brace_after_close(self):
        """Should raise ValueError when open brace comes after close."""
        crew = CurriculumCrew()
        
        with pytest.raises(ValueError, match="No JSON object found"):
            crew._extract_json("} then {")


# ==================== TEST: DICT TO COURSE ====================


class TestCurriculumCrewDictToCourse:
    """Tests for _dict_to_course() method."""
    
    def test_dict_to_course_full_data(self):
        """Should convert complete data to Course."""
        crew = CurriculumCrew()
        data = {
            "title": "My Course",
            "description": "A great course",
            "modules": [
                {
                    "title": "Module 1",
                    "description": "First module",
                    "order": 0,
                    "estimated_minutes": 30,
                    "concepts": [
                        {"title": "Concept 1", "content": "Content 1", "order": 0},
                    ],
                },
            ],
        }
        
        course = crew._dict_to_course(data, "Fallback")
        
        assert course.title == "My Course"
        assert course.description == "A great course"
        assert len(course.modules) == 1
        assert course.modules[0].title == "Module 1"
    
    def test_dict_to_course_empty_modules(self):
        """Should handle empty modules list."""
        crew = CurriculumCrew()
        data = {
            "title": "Empty Course",
            "description": "No modules",
            "modules": [],
        }
        
        course = crew._dict_to_course(data, "Fallback")
        
        assert len(course.modules) == 0
    
    def test_dict_to_course_missing_title(self):
        """Should use fallback topic when title is missing."""
        crew = CurriculumCrew()
        data = {
            "description": "Course without title",
            "modules": [],
        }
        
        course = crew._dict_to_course(data, "Fallback Topic")
        
        assert course.title == "Fallback Topic"
    
    def test_dict_to_course_missing_module_title(self):
        """Should generate module title when missing."""
        crew = CurriculumCrew()
        data = {
            "title": "Course",
            "modules": [
                {
                    "description": "No title",
                    "concepts": [],
                },
            ],
        }
        
        course = crew._dict_to_course(data, "Fallback")
        
        assert course.modules[0].title == "Module 1"
    
    def test_dict_to_course_missing_concept_title(self):
        """Should use default title when concept title is missing."""
        crew = CurriculumCrew()
        data = {
            "title": "Course",
            "modules": [
                {
                    "title": "Module",
                    "concepts": [
                        {"content": "Some content"},
                    ],
                },
            ],
        }
        
        course = crew._dict_to_course(data, "Fallback")
        
        assert course.modules[0].concepts[0].title == "Untitled Concept"
    
    def test_dict_to_course_default_estimated_minutes(self):
        """Should use default 60 minutes when not specified."""
        crew = CurriculumCrew()
        data = {
            "title": "Course",
            "modules": [
                {
                    "title": "Module",
                    "concepts": [],
                },
            ],
        }
        
        course = crew._dict_to_course(data, "Fallback")
        
        assert course.modules[0].estimated_minutes == 60
    
    def test_dict_to_course_preserves_order(self):
        """Should preserve module and concept order."""
        crew = CurriculumCrew()
        data = {
            "title": "Course",
            "modules": [
                {
                    "title": "Module A",
                    "order": 5,
                    "concepts": [
                        {"title": "Concept X", "order": 10},
                    ],
                },
            ],
        }
        
        course = crew._dict_to_course(data, "Fallback")
        
        assert course.modules[0].order == 5
        assert course.modules[0].concepts[0].order == 10
    
    def test_dict_to_course_generates_default_description(self):
        """Should generate default description when missing."""
        crew = CurriculumCrew()
        data = {
            "title": "My Course",
            "modules": [],
        }
        
        course = crew._dict_to_course(data, "Fallback Topic")
        
        assert "Fallback Topic" in course.description


# ==================== TEST: EDGE CASES ====================


class TestCurriculumCrewEdgeCases:
    """Edge case tests for CurriculumCrew."""
    
    def test_unicode_in_output(self):
        """Should handle unicode characters in output."""
        crew = CurriculumCrew()
        
        with patch.object(crew, 'crew') as mock_crew_method:
            mock_result = MagicMock()
            mock_result.raw = json.dumps({
                "title": "学习Python",
                "description": "Python课程 🐍",
                "modules": [
                    {
                        "title": "基础知识",
                        "concepts": [
                            {"title": "变量", "content": "变量是存储数据的容器。"},
                        ],
                    },
                ],
            })
            mock_crew_instance = MagicMock()
            mock_crew_instance.kickoff.return_value = mock_result
            mock_crew_method.return_value = mock_crew_instance
            
            course = crew.create_curriculum("Python")
            
            assert course.title == "学习Python"
            assert "🐍" in course.description
    
    def test_special_characters_in_topic(self, valid_crew_output):
        """Should handle special characters in topic."""
        crew = CurriculumCrew()
        
        with patch.object(crew, 'crew') as mock_crew_method:
            mock_result = MagicMock()
            mock_result.raw = valid_crew_output
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
            # Keep description under 1000 chars (Pydantic limit)
            modules = []
            for i in range(20):
                concepts = [
                    {"title": f"Concept {j}", "content": f"Content for concept {j}.", "order": j}
                    for j in range(10)
                ]
                modules.append({
                    "title": f"Module {i}",
                    "description": f"Description for module {i}",
                    "order": i,
                    "estimated_minutes": 60,
                    "concepts": concepts,
                })
            
            mock_result = MagicMock()
            mock_result.raw = json.dumps({
                "title": "Large Course",
                "description": "A very large course",
                "modules": modules,
            })
            mock_crew_instance = MagicMock()
            mock_crew_instance.kickoff.return_value = mock_result
            mock_crew_method.return_value = mock_crew_instance
            
            course = crew.create_curriculum("Large Topic")
            
            assert len(course.modules) == 20
            assert all(len(m.concepts) == 10 for m in course.modules)
    
    def test_dict_to_course_missing_title_uses_fallback(self):
        """Should use fallback for missing course title."""
        crew = CurriculumCrew()
        # When title key is missing (not present), the fallback is used
        data = {
            # Note: "title" key is completely missing, not empty string
            "description": "",
            "modules": [],
        }
        
        course = crew._dict_to_course(data, "Fallback")
        
        # Missing title should use fallback topic
        assert course.title == "Fallback"
    
    def test_dict_to_course_empty_string_title_raises_validation_error(self):
        """Should raise ValidationError when title is empty string.
        
        When title key exists but is empty string, Pydantic validation fails
        because Course.title has min_length=1 constraint.
        """
        from pydantic import ValidationError
        
        crew = CurriculumCrew()
        data = {
            "title": "",  # Empty string (not missing)
            "description": "",
            "modules": [],
        }
        
        with pytest.raises(ValidationError):
            crew._dict_to_course(data, "Fallback")
    
    def test_dict_to_course_module_missing_title_gets_default(self):
        """Should generate default module title when missing."""
        crew = CurriculumCrew()
        # When module title is missing (not present in dict), it gets a default
        data = {
            "title": "Test Course",
            "description": "Description",
            "modules": [
                {
                    # Note: "title" key is missing, not empty string
                    "description": "A module",
                    "concepts": [
                        {"title": "Concept 1", "content": "Content"},
                    ],
                },
            ],
        }
        
        course = crew._dict_to_course(data, "Fallback")
        
        # Missing module title gets default "Module 1"
        assert course.modules[0].title == "Module 1"
    
    def test_malformed_json_in_modules(self):
        """Should raise AttributeError for malformed module data.
        
        When modules is a string instead of a list, iterating over it yields
        characters, and calling .get() on a string raises AttributeError.
        Note: _parse_crew_output only catches JSONDecodeError, KeyError, TypeError,
        not AttributeError, so it propagates directly.
        """
        crew = CurriculumCrew()
        
        with patch.object(crew, 'crew') as mock_crew_method:
            mock_result = MagicMock()
            # JSON is valid but structure is unexpected (modules is string not list)
            # This will cause AttributeError when calling .get() on string characters
            mock_result.raw = '{"modules": "not a list"}'
            mock_crew_instance = MagicMock()
            mock_crew_instance.kickoff.return_value = mock_result
            mock_crew_method.return_value = mock_crew_instance
            
            # AttributeError is NOT caught, so it propagates
            with pytest.raises(AttributeError, match="'str' object has no attribute 'get'"):
                crew.create_curriculum("Topic")
    
    def test_all_experience_levels(self, valid_crew_output):
        """Should handle all experience levels."""
        crew = CurriculumCrew()
        
        for level in ExperienceLevel:
            with patch.object(crew, 'crew') as mock_crew_method:
                mock_result = MagicMock()
                mock_result.raw = valid_crew_output
                mock_crew_instance = MagicMock()
                mock_crew_instance.kickoff.return_value = mock_result
                mock_crew_method.return_value = mock_crew_instance
                
                user_prefs = UserPreferences(experience_level=level)
                course = crew.create_curriculum("Topic", user_prefs)
                
                assert isinstance(course, Course)
    
    def test_all_learning_styles(self, valid_crew_output):
        """Should handle all learning styles."""
        crew = CurriculumCrew()
        
        for style in LearningStyle:
            with patch.object(crew, 'crew') as mock_crew_method:
                mock_result = MagicMock()
                mock_result.raw = valid_crew_output
                mock_crew_instance = MagicMock()
                mock_crew_instance.kickoff.return_value = mock_result
                mock_crew_method.return_value = mock_crew_instance
                
                user_prefs = UserPreferences(learning_style=style)
                course = crew.create_curriculum("Topic", user_prefs)
                
                assert isinstance(course, Course)
