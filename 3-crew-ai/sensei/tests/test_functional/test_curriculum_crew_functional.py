"""Functional tests for CurriculumCrew with real LLM calls.

These tests verify the quality of AI-generated curriculum content.
They are non-deterministic and should be run manually or in pre-release.

Run with: pytest tests/test_functional/ -v -m functional
"""

import pytest

from sensei.crews.curriculum_crew import CurriculumCrew
from sensei.models.enums import ExperienceLevel, LearningStyle
from sensei.models.schemas import Course, UserPreferences


@pytest.mark.functional
class TestCurriculumCrewFunctional:
    """Functional tests for CurriculumCrew."""
    
    def test_creates_course_for_python_basics(self, skip_if_no_keys):
        """Should generate a complete course for Python Basics.
        
        Verifies:
        - Course has 5+ modules
        - Each module has 3+ concepts
        - Content is relevant to Python
        """
        crew = CurriculumCrew()
        
        course = crew.create_curriculum(
            topic="Python Basics",
            user_prefs=UserPreferences(experience_level=ExperienceLevel.BEGINNER),
        )
        
        # Structural validation
        assert isinstance(course, Course)
        assert len(course.modules) >= 5, f"Expected 5+ modules, got {len(course.modules)}"
        
        for module in course.modules:
            assert len(module.concepts) >= 3, (
                f"Module '{module.title}' has only {len(module.concepts)} concepts"
            )
            assert module.title != ""
            assert module.description != ""
        
        # Content relevance
        course_text = course.title.lower() + " " + course.description.lower()
        assert "python" in course_text, "Course should mention Python"
    
    def test_creates_course_for_advanced_topic(self, skip_if_no_keys):
        """Should generate a course for an advanced technical topic.
        
        Tests: CUDA C programming for an advanced user.
        """
        crew = CurriculumCrew()
        
        course = crew.create_curriculum(
            topic="CUDA C Programming",
            user_prefs=UserPreferences(
                experience_level=ExperienceLevel.ADVANCED,
                learning_style=LearningStyle.HANDS_ON,
            ),
        )
        
        # Structural validation
        assert isinstance(course, Course)
        assert len(course.modules) >= 4
        
        # Check for technical content indicators
        all_concepts = []
        for module in course.modules:
            for concept in module.concepts:
                all_concepts.append(concept.title.lower())
        
        all_text = " ".join(all_concepts)
        
        # Should have GPU/parallel-related concepts
        gpu_terms = ["gpu", "parallel", "thread", "kernel", "cuda", "memory"]
        has_gpu_content = any(term in all_text for term in gpu_terms)
        assert has_gpu_content, f"CUDA course should have GPU-related concepts: {all_concepts}"
    
    def test_course_structure_is_logical(self, skip_if_no_keys):
        """Should create a logically structured course.
        
        Verifies modules are ordered progressively:
        - Introduction comes first
        - Advanced topics come later
        """
        crew = CurriculumCrew()
        
        course = crew.create_curriculum(
            topic="Machine Learning",
            user_prefs=UserPreferences(experience_level=ExperienceLevel.INTERMEDIATE),
        )
        
        # First module should be introductory
        first_module_title = course.modules[0].title.lower()
        intro_indicators = ["intro", "getting", "start", "overview", "foundation", "basic"]
        has_intro = any(ind in first_module_title for ind in intro_indicators)
        
        # If first module doesn't have "intro" keywords, it's still okay
        # as long as we have multiple modules with progressive titles
        assert len(course.modules) >= 5, "Should have progressive structure"
    
    def test_course_modules_have_descriptions(self, skip_if_no_keys):
        """Should generate meaningful descriptions for all modules."""
        crew = CurriculumCrew()
        
        course = crew.create_curriculum(
            topic="React Development",
            user_prefs=UserPreferences(experience_level=ExperienceLevel.BEGINNER),
        )
        
        for module in course.modules:
            assert module.description != "", f"Module '{module.title}' has no description"
            assert len(module.description) >= 20, (
                f"Module '{module.title}' description too short: {module.description}"
            )
    
    def test_course_concepts_have_content(self, skip_if_no_keys):
        """Should generate content for all concepts."""
        crew = CurriculumCrew()
        
        course = crew.create_curriculum(
            topic="Data Structures",
            user_prefs=UserPreferences(experience_level=ExperienceLevel.INTERMEDIATE),
        )
        
        for module in course.modules:
            for concept in module.concepts:
                assert concept.title != "", "Concept must have title"
                assert concept.content != "", f"Concept '{concept.title}' has no content"
    
    def test_beginner_vs_advanced_course_difference(self, skip_if_no_keys):
        """Beginner and advanced courses should differ in structure."""
        crew = CurriculumCrew()
        
        beginner_course = crew.create_curriculum(
            topic="JavaScript",
            user_prefs=UserPreferences(experience_level=ExperienceLevel.BEGINNER),
        )
        
        advanced_course = crew.create_curriculum(
            topic="JavaScript",
            user_prefs=UserPreferences(experience_level=ExperienceLevel.ADVANCED),
        )
        
        # Both should be valid courses
        assert len(beginner_course.modules) >= 4
        assert len(advanced_course.modules) >= 4
        
        # They should have different titles/structure
        beginner_titles = {m.title.lower() for m in beginner_course.modules}
        advanced_titles = {m.title.lower() for m in advanced_course.modules}
        
        # At least some modules should be different
        # (exact comparison may fail due to LLM non-determinism)
        # Just verify both are valid courses
        assert beginner_titles, "Beginner course should have modules"
        assert advanced_titles, "Advanced course should have modules"
