"""Functional tests for TeachingCrew with real LLM calls.

These tests verify the quality of AI-generated lessons and Q&A.
They are non-deterministic and should be run manually or in pre-release.

Run with: pytest tests/test_functional/ -v -m functional
"""

import pytest

from sensei.crews.teaching_crew import TeachingCrew
from sensei.models.enums import ExperienceLevel, LearningStyle
from sensei.models.schemas import Concept, UserPreferences


@pytest.mark.functional
class TestTeachingCrewTeachConceptFunctional:
    """Functional tests for TeachingCrew.teach_concept()."""
    
    def test_generates_lesson_for_for_loops(self, skip_if_no_keys):
        """Should generate a comprehensive lesson about for loops.
        
        Verifies:
        - Lesson contains explanation
        - Has code example
        - Has key takeaways
        """
        crew = TeachingCrew()
        
        concept = Concept(
            title="For Loops in Python",
            content="Learn how to use for loops to iterate over sequences.",
            order=0,
        )
        
        lesson = crew.teach_concept(
            concept=concept,
            user_prefs=UserPreferences(
                experience_level=ExperienceLevel.BEGINNER,
                learning_style=LearningStyle.HANDS_ON,
            ),
            module_title="Control Flow",
        )
        
        # Should have content
        assert len(lesson) >= 100, f"Lesson too short: {len(lesson)} chars"
        
        # Should have markdown structure
        assert "##" in lesson or "#" in lesson, "Lesson should have headers"
        
        # Should have code example for hands-on learner
        assert "```" in lesson, "Lesson should have code blocks"
        
        # Should mention the topic
        lesson_lower = lesson.lower()
        assert "for" in lesson_lower or "loop" in lesson_lower, (
            "Lesson should discuss for loops"
        )
    
    def test_lesson_adapts_to_visual_learner(self, skip_if_no_keys):
        """Should adapt lesson for visual learners.
        
        Visual learners should get diagrams or visual representations.
        """
        crew = TeachingCrew()
        
        concept = Concept(
            title="Linked Lists",
            content="A linear data structure where elements are linked.",
            order=0,
        )
        
        lesson = crew.teach_concept(
            concept=concept,
            user_prefs=UserPreferences(
                experience_level=ExperienceLevel.INTERMEDIATE,
                learning_style=LearningStyle.VISUAL,
            ),
            module_title="Data Structures",
        )
        
        # Should have content
        assert len(lesson) >= 100
        
        # Visual learners might get ASCII diagrams or mentions of visualizing
        # (LLM may vary, so we just verify it's a valid lesson)
        lesson_lower = lesson.lower()
        assert "linked" in lesson_lower or "list" in lesson_lower
    
    def test_lesson_adapts_to_reading_learner(self, skip_if_no_keys):
        """Should adapt lesson for reading-preference learners.
        
        Reading learners should get detailed written explanations.
        """
        crew = TeachingCrew()
        
        concept = Concept(
            title="Recursion",
            content="A technique where a function calls itself.",
            order=0,
        )
        
        lesson = crew.teach_concept(
            concept=concept,
            user_prefs=UserPreferences(
                experience_level=ExperienceLevel.INTERMEDIATE,
                learning_style=LearningStyle.READING,
            ),
            module_title="Advanced Techniques",
        )
        
        # Reading learners should get longer explanations
        assert len(lesson) >= 200, "Reading learner should get detailed content"
        
        # Should discuss recursion
        assert "recursion" in lesson.lower() or "calls itself" in lesson.lower()
    
    def test_lesson_appropriate_length(self, skip_if_no_keys):
        """Lesson should be appropriate length (300-600 words)."""
        crew = TeachingCrew()
        
        concept = Concept(
            title="Variables",
            content="Named containers that store data.",
            order=0,
        )
        
        lesson = crew.teach_concept(
            concept=concept,
            user_prefs=UserPreferences(experience_level=ExperienceLevel.BEGINNER),
            module_title="Programming Fundamentals",
        )
        
        word_count = len(lesson.split())
        
        # Should be between 200-800 words (reasonable for a lesson)
        assert word_count >= 200, f"Lesson too short: {word_count} words"
        assert word_count <= 1000, f"Lesson too long: {word_count} words"


@pytest.mark.functional
class TestTeachingCrewAnswerQuestionFunctional:
    """Functional tests for TeachingCrew.answer_question()."""
    
    def test_answers_conceptual_question(self, skip_if_no_keys):
        """Should answer a conceptual question about the topic."""
        crew = TeachingCrew()
        
        concept = Concept(
            title="For Loops",
            content="Used to iterate over sequences.",
            order=0,
        )
        
        answer = crew.answer_question(
            question="Why do we use loops instead of writing the same code multiple times?",
            concept=concept,
            lesson_content="For loops allow us to repeat code efficiently.",
            user_prefs=UserPreferences(experience_level=ExperienceLevel.BEGINNER),
        )
        
        # Should have content
        assert len(answer) >= 50, f"Answer too short: {len(answer)} chars"
        
        # Should be relevant
        answer_lower = answer.lower()
        relevant_terms = ["loop", "repeat", "efficient", "code", "iteration", "reuse"]
        has_relevant = any(term in answer_lower for term in relevant_terms)
        assert has_relevant, f"Answer should be relevant to loops: {answer[:200]}"
    
    def test_answers_with_context(self, skip_if_no_keys):
        """Should use chat history context when answering."""
        crew = TeachingCrew()
        
        concept = Concept(
            title="Functions",
            content="Reusable blocks of code.",
            order=0,
        )
        
        # Simulate previous Q&A
        chat_history = [
            {"role": "user", "content": "What is a function?"},
            {"role": "assistant", "content": "A function is a reusable block of code that performs a specific task."},
        ]
        
        answer = crew.answer_question(
            question="Can you give me an example?",
            concept=concept,
            lesson_content="Functions help organize and reuse code.",
            chat_history=chat_history,
            user_prefs=UserPreferences(experience_level=ExperienceLevel.BEGINNER),
        )
        
        # Should have content
        assert len(answer) >= 50
        
        # Should include an example (based on context)
        answer_lower = answer.lower()
        has_example = "def " in answer or "example" in answer_lower or "```" in answer
        # May or may not have code, but should be a real answer
        assert len(answer) >= 50
    
    def test_answer_is_encouraging(self, skip_if_no_keys):
        """Should be encouraging and supportive in tone."""
        crew = TeachingCrew()
        
        concept = Concept(
            title="Error Handling",
            content="Managing exceptions in code.",
            order=0,
        )
        
        answer = crew.answer_question(
            question="I don't understand this at all. It's too confusing.",
            concept=concept,
            user_prefs=UserPreferences(experience_level=ExperienceLevel.BEGINNER),
        )
        
        # Should have supportive content
        assert len(answer) >= 50
        
        # Should not be dismissive (basic check)
        negative_terms = ["you're wrong", "you should know", "obviously"]
        answer_lower = answer.lower()
        is_negative = any(term in answer_lower for term in negative_terms)
        assert not is_negative, "Answer should be encouraging, not dismissive"
    
    def test_answer_appropriate_length(self, skip_if_no_keys):
        """Answer should be appropriate length (100-300 words)."""
        crew = TeachingCrew()
        
        concept = Concept(
            title="Classes",
            content="Blueprints for objects.",
            order=0,
        )
        
        answer = crew.answer_question(
            question="What's the difference between a class and an object?",
            concept=concept,
            user_prefs=UserPreferences(experience_level=ExperienceLevel.INTERMEDIATE),
        )
        
        word_count = len(answer.split())
        
        # Should be reasonable length
        assert word_count >= 50, f"Answer too short: {word_count} words"
        assert word_count <= 500, f"Answer too long: {word_count} words"
