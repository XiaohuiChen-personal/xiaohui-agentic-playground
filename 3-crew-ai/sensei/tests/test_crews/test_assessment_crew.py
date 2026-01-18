"""Unit tests for AssessmentCrew with mocked LLM.

These tests verify the AssessmentCrew's business logic without making
actual LLM API calls. All CrewAI components are mocked to return
predictable outputs via the output_pydantic feature.
"""

from unittest.mock import MagicMock, patch

import pytest

from sensei.crews.assessment_crew import AssessmentCrew
from sensei.models.enums import ExperienceLevel, LearningStyle, QuestionType
from sensei.models.schemas import (
    Concept,
    Module,
    Quiz,
    QuizEvaluationOutput,
    QuizOutput,
    QuizQuestion,
    QuizQuestionOutput,
    QuizResult,
    UserPreferences,
)


# ==================== FIXTURES ====================


@pytest.fixture
def sample_module():
    """Return a sample module with concepts."""
    return Module(
        title="Introduction to Python",
        description="Learn Python basics",
        order=0,
        estimated_minutes=60,
        concepts=[
            Concept(
                title="Variables",
                content="Variables store data values.",
                order=0,
            ),
            Concept(
                title="Data Types",
                content="Python has several data types.",
                order=1,
            ),
        ],
    )


@pytest.fixture
def sample_quiz(sample_module):
    """Return a sample quiz."""
    return Quiz(
        module_id=sample_module.id,
        module_title=sample_module.title,
        questions=[
            QuizQuestion(
                question="What is a variable?",
                question_type=QuestionType.MULTIPLE_CHOICE,
                options=["A) Storage location", "B) Function", "C) Loop", "D) Class"],
                correct_answer="A) Storage location",
                explanation="Variables store data values.",
                concept_id=sample_module.concepts[0].id,
                difficulty=2,
            ),
            QuizQuestion(
                question="Python is dynamically typed.",
                question_type=QuestionType.TRUE_FALSE,
                options=["True", "False"],
                correct_answer="True",
                explanation="Python determines types at runtime.",
                concept_id=sample_module.concepts[1].id,
                difficulty=1,
            ),
        ],
    )


@pytest.fixture
def valid_quiz_output():
    """Return a valid QuizOutput from the crew."""
    return QuizOutput(
        questions=[
            QuizQuestionOutput(
                question="What is a variable?",
                question_type="multiple_choice",
                options=["A) Storage", "B) Function", "C) Loop", "D) Class"],
                correct_answer="A) Storage",
                explanation="Variables store data.",
                concept_id="concept-123",
                difficulty=2,
            ),
            QuizQuestionOutput(
                question="Python is compiled.",
                question_type="true_false",
                options=["True", "False"],
                correct_answer="False",
                explanation="Python is interpreted.",
                concept_id="concept-456",
                difficulty=1,
            ),
        ],
    )


@pytest.fixture
def valid_evaluation_output():
    """Return a valid QuizEvaluationOutput from the crew."""
    return QuizEvaluationOutput(
        score=0.85,
        passed=True,
        correct_count=6,
        total_questions=7,
        weak_concepts=["concept-123"],
        feedback="Great job! You showed strong understanding of variables.",
        detailed_analysis={
            "strengths": ["Good grasp of variables"],
            "areas_for_improvement": ["Review data types"],
        },
        recommendation="proceed",
        next_steps="Continue to the next module on control flow.",
    )


# ==================== TEST: GENERATE QUIZ ====================


class TestAssessmentCrewGenerateQuiz:
    """Tests for AssessmentCrew.generate_quiz()."""
    
    def test_generate_quiz_returns_quiz(self, sample_module, valid_quiz_output):
        """Should return a Quiz object on success."""
        crew = AssessmentCrew()
        
        with patch.object(crew, '_create_assessment_crew') as mock_create:
            mock_result = MagicMock()
            mock_result.pydantic = valid_quiz_output
            mock_crew_instance = MagicMock()
            mock_crew_instance.kickoff.return_value = mock_result
            mock_create.return_value = mock_crew_instance
            
            quiz = crew.generate_quiz(sample_module)
            
            assert isinstance(quiz, Quiz)
            assert len(quiz.questions) == 2
    
    def test_generate_quiz_parses_questions(self, sample_module, valid_quiz_output):
        """Should correctly parse questions from output."""
        crew = AssessmentCrew()
        
        with patch.object(crew, '_create_assessment_crew') as mock_create:
            mock_result = MagicMock()
            mock_result.pydantic = valid_quiz_output
            mock_crew_instance = MagicMock()
            mock_crew_instance.kickoff.return_value = mock_result
            mock_create.return_value = mock_crew_instance
            
            quiz = crew.generate_quiz(sample_module)
            
            assert quiz.questions[0].question == "What is a variable?"
            assert quiz.questions[0].question_type == QuestionType.MULTIPLE_CHOICE
            assert quiz.questions[1].question_type == QuestionType.TRUE_FALSE
    
    def test_generate_quiz_passes_user_prefs(self, sample_module, valid_quiz_output):
        """Should pass user preferences to the crew."""
        crew = AssessmentCrew()
        
        with patch.object(crew, '_create_assessment_crew') as mock_create:
            mock_result = MagicMock()
            mock_result.pydantic = valid_quiz_output
            mock_crew_instance = MagicMock()
            mock_crew_instance.kickoff.return_value = mock_result
            mock_create.return_value = mock_crew_instance
            
            user_prefs = UserPreferences(experience_level=ExperienceLevel.ADVANCED)
            crew.generate_quiz(sample_module, user_prefs=user_prefs)
            
            call_args = mock_crew_instance.kickoff.call_args
            inputs = call_args.kwargs.get("inputs", {})
            
            assert "advanced" in inputs["experience_level"].lower()
    
    def test_generate_quiz_passes_weak_concepts(self, sample_module, valid_quiz_output):
        """Should pass weak concepts to the crew."""
        crew = AssessmentCrew()
        
        with patch.object(crew, '_create_assessment_crew') as mock_create:
            mock_result = MagicMock()
            mock_result.pydantic = valid_quiz_output
            mock_crew_instance = MagicMock()
            mock_crew_instance.kickoff.return_value = mock_result
            mock_create.return_value = mock_crew_instance
            
            weak_concepts = ["concept-123", "concept-456"]
            crew.generate_quiz(sample_module, weak_concepts=weak_concepts)
            
            call_args = mock_crew_instance.kickoff.call_args
            inputs = call_args.kwargs.get("inputs", {})
            
            assert "concept-123" in inputs["weak_areas"]
            assert "concept-456" in inputs["weak_areas"]
    
    def test_generate_quiz_raises_for_none_module(self):
        """Should raise ValueError for None module."""
        crew = AssessmentCrew()
        
        with pytest.raises(ValueError, match="Module cannot be None"):
            crew.generate_quiz(None)
    
    def test_generate_quiz_raises_for_empty_concepts(self):
        """Should raise ValueError for module with no concepts."""
        crew = AssessmentCrew()
        module = Module(title="Empty", description="No concepts", concepts=[])
        
        with pytest.raises(ValueError, match="Module must have concepts"):
            crew.generate_quiz(module)
    
    def test_generate_quiz_raises_on_no_pydantic_output(self, sample_module):
        """Should raise RuntimeError when pydantic output is None."""
        crew = AssessmentCrew()
        
        with patch.object(crew, '_create_assessment_crew') as mock_create:
            mock_result = MagicMock()
            mock_result.pydantic = None
            mock_result.raw = "Some raw text"
            mock_crew_instance = MagicMock()
            mock_crew_instance.kickoff.return_value = mock_result
            mock_create.return_value = mock_crew_instance
            
            with pytest.raises(RuntimeError, match="Failed to get structured output"):
                crew.generate_quiz(sample_module)


# ==================== TEST: EVALUATE ANSWERS ====================


class TestAssessmentCrewEvaluateAnswers:
    """Tests for AssessmentCrew.evaluate_answers()."""
    
    def test_evaluate_answers_returns_quiz_result(self, sample_quiz, valid_evaluation_output):
        """Should return a QuizResult object on success."""
        crew = AssessmentCrew()
        answers = {
            sample_quiz.questions[0].id: "A) Storage location",
            sample_quiz.questions[1].id: "True",
        }
        
        with patch.object(crew, '_create_assessment_crew') as mock_create:
            mock_result = MagicMock()
            mock_result.pydantic = valid_evaluation_output
            mock_crew_instance = MagicMock()
            mock_crew_instance.kickoff.return_value = mock_result
            mock_create.return_value = mock_crew_instance
            
            result = crew.evaluate_answers(sample_quiz, answers)
            
            assert isinstance(result, QuizResult)
            assert result.score == 0.85
            assert result.passed is True
    
    def test_evaluate_answers_includes_feedback(self, sample_quiz, valid_evaluation_output):
        """Should include feedback in result."""
        crew = AssessmentCrew()
        answers = {sample_quiz.questions[0].id: "A) Storage location"}
        
        with patch.object(crew, '_create_assessment_crew') as mock_create:
            mock_result = MagicMock()
            mock_result.pydantic = valid_evaluation_output
            mock_crew_instance = MagicMock()
            mock_crew_instance.kickoff.return_value = mock_result
            mock_create.return_value = mock_crew_instance
            
            result = crew.evaluate_answers(sample_quiz, answers)
            
            assert "Great job" in result.feedback
            assert "Next Steps" in result.feedback  # next_steps appended
    
    def test_evaluate_answers_includes_weak_concepts(self, sample_quiz, valid_evaluation_output):
        """Should include weak concepts from LLM."""
        crew = AssessmentCrew()
        answers = {}
        
        with patch.object(crew, '_create_assessment_crew') as mock_create:
            mock_result = MagicMock()
            mock_result.pydantic = valid_evaluation_output
            mock_crew_instance = MagicMock()
            mock_crew_instance.kickoff.return_value = mock_result
            mock_create.return_value = mock_crew_instance
            
            result = crew.evaluate_answers(sample_quiz, answers)
            
            assert "concept-123" in result.weak_concepts
    
    def test_evaluate_answers_calculates_weak_concepts_from_wrong_answers(
        self, sample_quiz
    ):
        """Should calculate weak concepts if LLM doesn't provide them."""
        crew = AssessmentCrew()
        answers = {
            sample_quiz.questions[0].id: "Wrong answer",  # Incorrect
        }
        
        # Evaluation output without weak_concepts
        output = QuizEvaluationOutput(
            score=0.5,
            passed=False,
            correct_count=1,
            total_questions=2,
            weak_concepts=[],  # Empty
            feedback="Need improvement.",
        )
        
        with patch.object(crew, '_create_assessment_crew') as mock_create:
            mock_result = MagicMock()
            mock_result.pydantic = output
            mock_crew_instance = MagicMock()
            mock_crew_instance.kickoff.return_value = mock_result
            mock_create.return_value = mock_crew_instance
            
            result = crew.evaluate_answers(sample_quiz, answers)
            
            # Should have calculated weak concepts from wrong answers
            assert sample_quiz.questions[0].concept_id in result.weak_concepts
    
    def test_evaluate_answers_passes_user_prefs(self, sample_quiz, valid_evaluation_output):
        """Should pass user preferences to the crew."""
        crew = AssessmentCrew()
        answers = {}
        
        with patch.object(crew, '_create_assessment_crew') as mock_create:
            mock_result = MagicMock()
            mock_result.pydantic = valid_evaluation_output
            mock_crew_instance = MagicMock()
            mock_crew_instance.kickoff.return_value = mock_result
            mock_create.return_value = mock_crew_instance
            
            user_prefs = UserPreferences(
                experience_level=ExperienceLevel.INTERMEDIATE,
                learning_style=LearningStyle.VISUAL,
            )
            crew.evaluate_answers(sample_quiz, answers, user_prefs=user_prefs)
            
            call_args = mock_crew_instance.kickoff.call_args
            inputs = call_args.kwargs.get("inputs", {})
            
            assert "intermediate" in inputs["experience_level"].lower()
            assert "visual" in inputs["learning_style"].lower()
    
    def test_evaluate_answers_passes_previous_scores(
        self, sample_quiz, valid_evaluation_output
    ):
        """Should pass previous scores to the crew."""
        crew = AssessmentCrew()
        answers = {}
        
        with patch.object(crew, '_create_assessment_crew') as mock_create:
            mock_result = MagicMock()
            mock_result.pydantic = valid_evaluation_output
            mock_crew_instance = MagicMock()
            mock_crew_instance.kickoff.return_value = mock_result
            mock_create.return_value = mock_crew_instance
            
            previous_scores = [0.6, 0.7, 0.8]
            crew.evaluate_answers(
                sample_quiz, answers, previous_scores=previous_scores
            )
            
            call_args = mock_crew_instance.kickoff.call_args
            inputs = call_args.kwargs.get("inputs", {})
            
            assert "60%" in inputs["previous_performance"]
            assert "improving" in inputs["previous_performance"]
    
    def test_evaluate_answers_raises_for_none_quiz(self):
        """Should raise ValueError for None quiz."""
        crew = AssessmentCrew()
        
        with pytest.raises(ValueError, match="Quiz cannot be None"):
            crew.evaluate_answers(None, {})
    
    def test_evaluate_answers_raises_for_empty_questions(self):
        """Should raise ValueError for quiz with no questions."""
        crew = AssessmentCrew()
        quiz = Quiz(module_id="m1", module_title="Test", questions=[])
        
        with pytest.raises(ValueError, match="Quiz must have questions"):
            crew.evaluate_answers(quiz, {})
    
    def test_evaluate_answers_raises_on_no_pydantic_output(self, sample_quiz):
        """Should raise RuntimeError when pydantic output is None."""
        crew = AssessmentCrew()
        
        with patch.object(crew, '_create_assessment_crew') as mock_create:
            mock_result = MagicMock()
            mock_result.pydantic = None
            mock_result.raw = "Some raw text"
            mock_crew_instance = MagicMock()
            mock_crew_instance.kickoff.return_value = mock_result
            mock_create.return_value = mock_crew_instance
            
            with pytest.raises(RuntimeError, match="Failed to get structured output"):
                crew.evaluate_answers(sample_quiz, {})


# ==================== TEST: OUTPUT TO QUIZ ====================


class TestAssessmentCrewOutputToQuiz:
    """Tests for _output_to_quiz() method."""
    
    def test_output_to_quiz_converts_question_types(self, sample_module):
        """Should correctly convert question type strings to enums."""
        crew = AssessmentCrew()
        output = QuizOutput(
            questions=[
                QuizQuestionOutput(
                    question="Q1",
                    question_type="multiple_choice",
                    correct_answer="A",
                ),
                QuizQuestionOutput(
                    question="Q2",
                    question_type="true_false",
                    correct_answer="True",
                ),
                QuizQuestionOutput(
                    question="Q3",
                    question_type="code",
                    correct_answer="print('hello')",
                ),
                QuizQuestionOutput(
                    question="Q4",
                    question_type="open_ended",
                    correct_answer="Explain variables...",
                ),
            ],
        )
        
        quiz = crew._output_to_quiz(output, sample_module)
        
        assert quiz.questions[0].question_type == QuestionType.MULTIPLE_CHOICE
        assert quiz.questions[1].question_type == QuestionType.TRUE_FALSE
        assert quiz.questions[2].question_type == QuestionType.CODE
        assert quiz.questions[3].question_type == QuestionType.OPEN_ENDED
    
    def test_output_to_quiz_generates_ids(self, sample_module):
        """Should generate IDs for quiz and questions."""
        crew = AssessmentCrew()
        output = QuizOutput(
            questions=[
                QuizQuestionOutput(question="Q1", correct_answer="A"),
            ],
        )
        
        quiz = crew._output_to_quiz(output, sample_module)
        
        assert quiz.id.startswith("quiz-")
        assert quiz.questions[0].id.startswith("q-")
    
    def test_output_to_quiz_sets_module_info(self, sample_module):
        """Should set module ID and title from module."""
        crew = AssessmentCrew()
        output = QuizOutput(
            questions=[
                QuizQuestionOutput(question="Q1", correct_answer="A"),
            ],
        )
        
        quiz = crew._output_to_quiz(output, sample_module)
        
        assert quiz.module_id == sample_module.id
        assert quiz.module_title == sample_module.title


# ==================== TEST: HELPER METHODS ====================


class TestAssessmentCrewHelperMethods:
    """Tests for helper formatting methods."""
    
    def test_format_concepts_list_empty(self):
        """Should handle empty concepts list."""
        crew = AssessmentCrew()
        
        result = crew._format_concepts_list([])
        
        assert result == "No concepts available."
    
    def test_format_concepts_list_with_concepts(self):
        """Should format concepts as numbered list."""
        crew = AssessmentCrew()
        concepts = [
            {"title": "Variables", "content": "Store data", "id": "c1"},
            {"title": "Functions", "content": "Reusable code", "id": "c2"},
        ]
        
        result = crew._format_concepts_list(concepts)
        
        assert "1. **Variables**" in result
        assert "2. **Functions**" in result
        assert "(ID: c1)" in result
    
    def test_format_concepts_list_truncates_long_content(self):
        """Should truncate content over 200 characters."""
        crew = AssessmentCrew()
        long_content = "x" * 300
        concepts = [{"title": "Test", "content": long_content, "id": "c1"}]
        
        result = crew._format_concepts_list(concepts)
        
        assert "..." in result
        assert len(result) < len(long_content) + 100
    
    def test_format_focus_concepts_empty(self):
        """Should handle empty focus concepts."""
        crew = AssessmentCrew()
        
        result = crew._format_focus_concepts([], [])
        
        assert "No specific focus areas" in result
    
    def test_format_focus_concepts_with_ids(self):
        """Should format focus concepts."""
        crew = AssessmentCrew()
        concepts = [
            {"title": "Variables", "id": "c1"},
            {"title": "Functions", "id": "c2"},
        ]
        
        result = crew._format_focus_concepts(concepts, ["c1"])
        
        assert "**Variables**" in result
        assert "extra attention" in result
    
    def test_format_detailed_results(self, sample_quiz):
        """Should format detailed results."""
        crew = AssessmentCrew()
        answers = {
            sample_quiz.questions[0].id: "A) Storage location",
            sample_quiz.questions[1].id: "Wrong",
        }
        
        result = crew._format_detailed_results(sample_quiz, answers)
        
        assert "Question 1" in result
        assert "Question 2" in result
        assert "✅ Correct" in result
        assert "❌ Incorrect" in result


# ==================== TEST: EDGE CASES ====================


class TestAssessmentCrewEdgeCases:
    """Edge case tests for AssessmentCrew."""
    
    def test_unicode_in_questions(self, sample_module):
        """Should handle unicode in questions."""
        crew = AssessmentCrew()
        
        with patch.object(crew, '_create_assessment_crew') as mock_create:
            mock_result = MagicMock()
            mock_result.pydantic = QuizOutput(
                questions=[
                    QuizQuestionOutput(
                        question="Что такое переменная? 🤔",
                        correct_answer="Хранилище данных",
                    ),
                ],
            )
            mock_crew_instance = MagicMock()
            mock_crew_instance.kickoff.return_value = mock_result
            mock_create.return_value = mock_crew_instance
            
            quiz = crew.generate_quiz(sample_module)
            
            assert "🤔" in quiz.questions[0].question
    
    def test_empty_answers_dict(self, sample_quiz, valid_evaluation_output):
        """Should handle empty answers dictionary."""
        crew = AssessmentCrew()
        
        with patch.object(crew, '_create_assessment_crew') as mock_create:
            mock_result = MagicMock()
            mock_result.pydantic = valid_evaluation_output
            mock_crew_instance = MagicMock()
            mock_crew_instance.kickoff.return_value = mock_result
            mock_create.return_value = mock_crew_instance
            
            result = crew.evaluate_answers(sample_quiz, {})
            
            assert isinstance(result, QuizResult)
    
    def test_unknown_question_type_defaults_to_mc(self, sample_module):
        """Should default unknown question types to multiple choice."""
        crew = AssessmentCrew()
        output = QuizOutput(
            questions=[
                QuizQuestionOutput(
                    question="Test?",
                    question_type="unknown_type",
                    correct_answer="A",
                ),
            ],
        )
        
        quiz = crew._output_to_quiz(output, sample_module)
        
        assert quiz.questions[0].question_type == QuestionType.MULTIPLE_CHOICE
    
    def test_large_quiz(self, sample_module):
        """Should handle large quizzes."""
        crew = AssessmentCrew()
        
        with patch.object(crew, '_create_assessment_crew') as mock_create:
            questions = [
                QuizQuestionOutput(
                    question=f"Question {i}?",
                    correct_answer=f"Answer {i}",
                )
                for i in range(20)
            ]
            mock_result = MagicMock()
            mock_result.pydantic = QuizOutput(questions=questions)
            mock_crew_instance = MagicMock()
            mock_crew_instance.kickoff.return_value = mock_result
            mock_create.return_value = mock_crew_instance
            
            quiz = crew.generate_quiz(sample_module)
            
            assert len(quiz.questions) == 20
    
    def test_all_experience_levels(self, sample_module, valid_quiz_output):
        """Should handle all experience levels."""
        crew = AssessmentCrew()
        
        for level in ExperienceLevel:
            with patch.object(crew, '_create_assessment_crew') as mock_create:
                mock_result = MagicMock()
                mock_result.pydantic = valid_quiz_output
                mock_crew_instance = MagicMock()
                mock_crew_instance.kickoff.return_value = mock_result
                mock_create.return_value = mock_crew_instance
                
                user_prefs = UserPreferences(experience_level=level)
                quiz = crew.generate_quiz(sample_module, user_prefs=user_prefs)
                
                assert isinstance(quiz, Quiz)
