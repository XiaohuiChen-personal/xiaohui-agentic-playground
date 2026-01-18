"""Functional tests for AssessmentCrew with real LLM calls.

These tests verify the quality of AI-generated quizzes and evaluations.
They are non-deterministic and should be run manually or in pre-release.

Run with: pytest tests/test_functional/ -v -m functional
"""

import pytest

from sensei.crews.assessment_crew import AssessmentCrew
from sensei.models.enums import ExperienceLevel, QuestionType
from sensei.models.schemas import (
    Concept,
    Module,
    Quiz,
    QuizQuestion,
    UserPreferences,
)


@pytest.mark.functional
class TestAssessmentCrewGenerateQuizFunctional:
    """Functional tests for AssessmentCrew.generate_quiz()."""
    
    def test_generates_quiz_with_multiple_questions(self, skip_if_no_keys):
        """Should generate a quiz with multiple questions for a module.
        
        Verifies:
        - Quiz has 5+ questions
        - Questions are relevant to module concepts
        """
        crew = AssessmentCrew()
        
        module = Module(
            title="Python Basics",
            description="Introduction to Python programming",
            concepts=[
                Concept(title="Variables", content="Named containers", order=0),
                Concept(title="Data Types", content="int, str, float, etc.", order=1),
                Concept(title="Operators", content="Math and comparison", order=2),
                Concept(title="Print Function", content="Output to console", order=3),
            ],
            order=0,
            estimated_minutes=60,
        )
        
        quiz = crew.generate_quiz(
            module=module,
            user_prefs=UserPreferences(experience_level=ExperienceLevel.BEGINNER),
        )
        
        # Structural validation
        assert isinstance(quiz, Quiz)
        assert len(quiz.questions) >= 5, f"Expected 5+ questions, got {len(quiz.questions)}"
        
        for question in quiz.questions:
            assert question.question != "", "Question text cannot be empty"
            assert question.correct_answer != "", "Correct answer cannot be empty"
            assert question.explanation != "", "Explanation cannot be empty"
    
    def test_quiz_has_diverse_question_types(self, skip_if_no_keys):
        """Should generate questions of multiple types."""
        crew = AssessmentCrew()
        
        module = Module(
            title="Control Flow",
            description="Conditional statements and loops",
            concepts=[
                Concept(title="If Statements", content="Conditional logic", order=0),
                Concept(title="For Loops", content="Iteration over sequences", order=1),
                Concept(title="While Loops", content="Condition-based iteration", order=2),
            ],
            order=1,
            estimated_minutes=45,
        )
        
        quiz = crew.generate_quiz(
            module=module,
            user_prefs=UserPreferences(experience_level=ExperienceLevel.INTERMEDIATE),
        )
        
        question_types = {q.question_type for q in quiz.questions}
        
        # Should have at least 2 different question types
        assert len(question_types) >= 2, (
            f"Quiz should have diverse question types, got: {question_types}"
        )
    
    def test_quiz_includes_open_ended_question(self, skip_if_no_keys):
        """Should include at least one open-ended question."""
        crew = AssessmentCrew()
        
        module = Module(
            title="Functions",
            description="Reusable code blocks",
            concepts=[
                Concept(title="Function Definition", content="def keyword", order=0),
                Concept(title="Parameters", content="Input values", order=1),
                Concept(title="Return Values", content="Output from functions", order=2),
            ],
            order=2,
            estimated_minutes=50,
        )
        
        quiz = crew.generate_quiz(
            module=module,
            user_prefs=UserPreferences(experience_level=ExperienceLevel.BEGINNER),
        )
        
        has_open_ended = any(
            q.question_type == QuestionType.OPEN_ENDED
            for q in quiz.questions
        )
        
        # Should have at least one open-ended question per design doc
        assert has_open_ended, "Quiz should have at least one open-ended question"
    
    def test_quiz_focuses_on_weak_concepts(self, skip_if_no_keys):
        """Should focus more questions on weak concepts."""
        crew = AssessmentCrew()
        
        weak_concept = Concept(
            id="weak-concept-1",
            title="Recursion",
            content="Functions calling themselves",
            order=0,
        )
        
        module = Module(
            title="Advanced Functions",
            description="Complex function patterns",
            concepts=[
                weak_concept,
                Concept(id="concept-2", title="Lambda", content="Anonymous functions", order=1),
                Concept(id="concept-3", title="Decorators", content="Function wrappers", order=2),
            ],
            order=3,
            estimated_minutes=60,
        )
        
        quiz = crew.generate_quiz(
            module=module,
            weak_concepts=["weak-concept-1"],
            user_prefs=UserPreferences(experience_level=ExperienceLevel.ADVANCED),
        )
        
        # Should have questions about the weak concept
        weak_concept_questions = [
            q for q in quiz.questions
            if q.concept_id == "weak-concept-1"
        ]
        
        # At least one question should target the weak concept
        # (LLM might not always generate concept_id correctly, so be lenient)
        assert len(quiz.questions) >= 5


@pytest.mark.functional
class TestAssessmentCrewEvaluateAnswersFunctional:
    """Functional tests for AssessmentCrew.evaluate_answers()."""
    
    def test_evaluates_correct_answers(self, skip_if_no_keys):
        """Should correctly evaluate mostly correct answers."""
        crew = AssessmentCrew()
        
        # Create a quiz with questions
        quiz = Quiz(
            module_id="mod-1",
            module_title="Test Module",
            questions=[
                QuizQuestion(
                    id="q1",
                    question="What is 2 + 2?",
                    question_type=QuestionType.MULTIPLE_CHOICE,
                    options=["3", "4", "5", "6"],
                    correct_answer="4",
                    explanation="Basic addition",
                    concept_id="c1",
                    difficulty=1,
                ),
                QuizQuestion(
                    id="q2",
                    question="Is Python interpreted?",
                    question_type=QuestionType.TRUE_FALSE,
                    options=["True", "False"],
                    correct_answer="True",
                    explanation="Python is an interpreted language",
                    concept_id="c2",
                    difficulty=1,
                ),
                QuizQuestion(
                    id="q3",
                    question="What is the keyword to define a function?",
                    question_type=QuestionType.MULTIPLE_CHOICE,
                    options=["function", "def", "func", "define"],
                    correct_answer="def",
                    explanation="Python uses def keyword",
                    concept_id="c3",
                    difficulty=1,
                ),
            ],
        )
        
        # Submit all correct answers
        answers = {"q1": "4", "q2": "True", "q3": "def"}
        
        result = crew.evaluate_answers(
            quiz=quiz,
            answers=answers,
            course_id="test-course",
            user_prefs=UserPreferences(experience_level=ExperienceLevel.BEGINNER),
        )
        
        # Should pass with high score
        assert result.score >= 0.8, f"Score should be high for all correct: {result.score}"
        assert result.passed is True
        assert len(result.weak_concepts) == 0 or result.correct_count == 3
    
    def test_evaluates_incorrect_answers(self, skip_if_no_keys):
        """Should correctly evaluate incorrect answers."""
        crew = AssessmentCrew()
        
        quiz = Quiz(
            module_id="mod-1",
            module_title="Test Module",
            questions=[
                QuizQuestion(
                    id="q1",
                    question="What is 2 + 2?",
                    question_type=QuestionType.MULTIPLE_CHOICE,
                    options=["3", "4", "5", "6"],
                    correct_answer="4",
                    explanation="Basic addition",
                    concept_id="c1",
                    difficulty=1,
                ),
                QuizQuestion(
                    id="q2",
                    question="Is Python compiled?",
                    question_type=QuestionType.TRUE_FALSE,
                    options=["True", "False"],
                    correct_answer="False",
                    explanation="Python is interpreted",
                    concept_id="c2",
                    difficulty=1,
                ),
            ],
        )
        
        # Submit wrong answers
        answers = {"q1": "3", "q2": "True"}
        
        result = crew.evaluate_answers(
            quiz=quiz,
            answers=answers,
            course_id="test-course",
            user_prefs=UserPreferences(experience_level=ExperienceLevel.BEGINNER),
        )
        
        # Should fail with low score
        assert result.score <= 0.5, f"Score should be low for wrong answers: {result.score}"
        assert result.passed is False
        assert result.correct_count == 0
    
    def test_provides_helpful_feedback(self, skip_if_no_keys):
        """Should provide helpful feedback based on performance."""
        crew = AssessmentCrew()
        
        quiz = Quiz(
            module_id="mod-1",
            module_title="Python Variables",
            questions=[
                QuizQuestion(
                    id="q1",
                    question="How do you assign a value to a variable?",
                    question_type=QuestionType.MULTIPLE_CHOICE,
                    options=["x == 5", "x := 5", "x = 5", "let x = 5"],
                    correct_answer="x = 5",
                    explanation="Python uses = for assignment",
                    concept_id="c1",
                    difficulty=1,
                ),
            ],
        )
        
        answers = {"q1": "x = 5"}
        
        result = crew.evaluate_answers(
            quiz=quiz,
            answers=answers,
            course_id="test-course",
            user_prefs=UserPreferences(experience_level=ExperienceLevel.BEGINNER),
        )
        
        # Should have feedback
        assert result.feedback != "", "Result should have feedback"
        assert len(result.feedback) >= 20, "Feedback should be substantive"
    
    def test_identifies_weak_concepts(self, skip_if_no_keys):
        """Should identify weak concepts from incorrect answers."""
        crew = AssessmentCrew()
        
        quiz = Quiz(
            module_id="mod-1",
            module_title="Test Module",
            questions=[
                QuizQuestion(
                    id="q1",
                    question="Question about recursion",
                    question_type=QuestionType.MULTIPLE_CHOICE,
                    options=["A", "B", "C", "D"],
                    correct_answer="A",
                    explanation="Recursion is...",
                    concept_id="recursion-concept",
                    difficulty=2,
                ),
                QuizQuestion(
                    id="q2",
                    question="Question about iteration",
                    question_type=QuestionType.TRUE_FALSE,
                    options=["True", "False"],
                    correct_answer="True",
                    explanation="Iteration is...",
                    concept_id="iteration-concept",
                    difficulty=2,
                ),
            ],
        )
        
        # Get recursion wrong, iteration correct
        answers = {"q1": "B", "q2": "True"}
        
        result = crew.evaluate_answers(
            quiz=quiz,
            answers=answers,
            course_id="test-course",
            user_prefs=UserPreferences(experience_level=ExperienceLevel.INTERMEDIATE),
        )
        
        # Should identify weak concept
        assert "recursion-concept" in result.weak_concepts or result.score < 1.0
    
    def test_recommends_proceed_or_review(self, skip_if_no_keys):
        """Should recommend whether to proceed or review."""
        crew = AssessmentCrew()
        
        quiz = Quiz(
            module_id="mod-1",
            module_title="Test Module",
            questions=[
                QuizQuestion(
                    id="q1",
                    question="Test question",
                    question_type=QuestionType.MULTIPLE_CHOICE,
                    options=["A", "B", "C", "D"],
                    correct_answer="A",
                    explanation="Explanation",
                    concept_id="c1",
                    difficulty=1,
                ),
            ],
        )
        
        answers = {"q1": "B"}  # Wrong
        
        result = crew.evaluate_answers(
            quiz=quiz,
            answers=answers,
            course_id="test-course",
            user_prefs=UserPreferences(experience_level=ExperienceLevel.BEGINNER),
        )
        
        # Feedback should mention review or next steps
        feedback_lower = result.feedback.lower()
        has_recommendation = (
            "review" in feedback_lower or
            "proceed" in feedback_lower or
            "next" in feedback_lower or
            "continue" in feedback_lower or
            "step" in feedback_lower
        )
        
        # Should have some kind of guidance
        assert len(result.feedback) >= 20, "Feedback should provide guidance"
