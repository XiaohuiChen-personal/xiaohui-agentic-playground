"""Unit tests for AssessmentCrew with mocked LLM.

These tests verify the AssessmentCrew's business logic without making
actual LLM API calls. All CrewAI components are mocked to return
predictable outputs.
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from sensei.crews.assessment_crew import AssessmentCrew
from sensei.models.enums import ExperienceLevel, LearningStyle, QuestionType
from sensei.models.schemas import (
    Concept,
    Module,
    Quiz,
    QuizQuestion,
    QuizResult,
    UserPreferences,
)


# ==================== FIXTURES ====================


@pytest.fixture
def sample_module():
    """Create a sample module with concepts."""
    return Module(
        title="Python Basics",
        description="Introduction to Python programming",
        order=0,
        estimated_minutes=60,
        concepts=[
            Concept(title="Variables", content="Variables store data.", order=0),
            Concept(title="Data Types", content="Different types of data.", order=1),
            Concept(title="Operators", content="Math and comparison operators.", order=2),
        ],
    )


@pytest.fixture
def sample_quiz(sample_module):
    """Create a sample quiz."""
    return Quiz(
        module_id=sample_module.id,
        module_title=sample_module.title,
        questions=[
            QuizQuestion(
                question="What is a variable?",
                question_type=QuestionType.MULTIPLE_CHOICE,
                options=["A) Storage", "B) Function", "C) Loop", "D) Class"],
                correct_answer="A) Storage",
                explanation="Variables store data values.",
                concept_id="concept-1",
                difficulty=2,
            ),
            QuizQuestion(
                question="Python is dynamically typed.",
                question_type=QuestionType.TRUE_FALSE,
                options=["True", "False"],
                correct_answer="True",
                explanation="Python determines types at runtime.",
                concept_id="concept-2",
                difficulty=1,
            ),
        ],
    )


@pytest.fixture
def sample_user_prefs():
    """Create sample user preferences."""
    return UserPreferences(
        experience_level=ExperienceLevel.INTERMEDIATE,
        learning_style=LearningStyle.VISUAL,
    )


@pytest.fixture
def quiz_generation_output():
    """Return mock quiz generation output."""
    return json.dumps({
        "questions": [
            {
                "question": "What is a variable in Python?",
                "question_type": "multiple_choice",
                "options": [
                    "A) A container for storing data",
                    "B) A type of loop",
                    "C) A function definition",
                    "D) An import statement",
                ],
                "correct_answer": "A) A container for storing data",
                "explanation": "Variables are named locations in memory.",
                "concept_id": "concept-1",
                "difficulty": 2,
            },
            {
                "question": "True or False: Python uses dynamic typing.",
                "question_type": "true_false",
                "options": ["True", "False"],
                "correct_answer": "True",
                "explanation": "Python determines variable types at runtime.",
                "concept_id": "concept-2",
                "difficulty": 1,
            },
        ]
    })


@pytest.fixture
def evaluation_output():
    """Return mock evaluation output."""
    return json.dumps({
        "score": 0.85,
        "passed": True,
        "feedback": "Great job! You demonstrated strong understanding of the concepts.",
        "weak_concepts": ["concept-2"],
        "detailed_analysis": {
            "strengths": ["Good grasp of variables"],
            "areas_for_improvement": ["Review data types"],
        },
        "recommendation": "proceed",
        "next_steps": "You're ready to move on to Control Flow!",
    })


@pytest.fixture
def mock_agents_config():
    """Return mock agents configuration."""
    return {
        "quiz_designer": {
            "role": "Quiz Designer",
            "goal": "Create effective quiz questions",
            "backstory": "Expert assessment designer",
            "llm": "anthropic/claude-opus-4-5-20251101",
        },
        "performance_analyst": {
            "role": "Performance Analyst",
            "goal": "Analyze quiz results",
            "backstory": "Learning analyst",
            "llm": "openai/gpt-5.2",
        },
    }


@pytest.fixture
def mock_tasks_config():
    """Return mock tasks configuration."""
    return {
        "generate_quiz_task": {
            "description": "Generate quiz for {module_title}",
            "expected_output": "JSON with questions",
        },
        "evaluate_quiz_task": {
            "description": "Evaluate quiz results",
            "expected_output": "JSON with feedback",
        },
    }


# ==================== TEST: INITIALIZATION ====================


class TestAssessmentCrewInit:
    """Tests for AssessmentCrew initialization."""
    
    def test_init_loads_configs(self, mock_agents_config, mock_tasks_config):
        """Should load configurations on init."""
        with patch.object(
            AssessmentCrew, '_load_yaml',
            side_effect=[mock_agents_config, mock_tasks_config]
        ):
            crew = AssessmentCrew()
            
            assert crew._agents_config == mock_agents_config
            assert crew._tasks_config == mock_tasks_config


# ==================== TEST: GENERATE QUIZ ====================


class TestAssessmentCrewGenerateQuiz:
    """Tests for AssessmentCrew.generate_quiz()."""
    
    def test_generate_quiz_returns_quiz(
        self, mock_agents_config, mock_tasks_config, sample_module, quiz_generation_output
    ):
        """Should return a Quiz object."""
        with patch.object(
            AssessmentCrew, '_load_yaml',
            side_effect=[mock_agents_config, mock_tasks_config]
        ):
            crew = AssessmentCrew()
        
        with patch.object(crew, '_create_assessment_crew') as mock_create_crew:
            mock_result = MagicMock()
            mock_result.raw = quiz_generation_output
            mock_crew_instance = MagicMock()
            mock_crew_instance.kickoff.return_value = mock_result
            mock_create_crew.return_value = mock_crew_instance
            
            quiz = crew.generate_quiz(sample_module)
            
            assert isinstance(quiz, Quiz)
            assert len(quiz.questions) == 2
    
    def test_generate_quiz_parses_questions(
        self, mock_agents_config, mock_tasks_config, sample_module, quiz_generation_output
    ):
        """Should correctly parse quiz questions."""
        with patch.object(
            AssessmentCrew, '_load_yaml',
            side_effect=[mock_agents_config, mock_tasks_config]
        ):
            crew = AssessmentCrew()
        
        with patch.object(crew, '_create_assessment_crew') as mock_create_crew:
            mock_result = MagicMock()
            mock_result.raw = quiz_generation_output
            mock_crew_instance = MagicMock()
            mock_crew_instance.kickoff.return_value = mock_result
            mock_create_crew.return_value = mock_crew_instance
            
            quiz = crew.generate_quiz(sample_module)
            
            assert quiz.questions[0].question_type == QuestionType.MULTIPLE_CHOICE
            assert quiz.questions[1].question_type == QuestionType.TRUE_FALSE
    
    def test_generate_quiz_sets_module_info(
        self, mock_agents_config, mock_tasks_config, sample_module, quiz_generation_output
    ):
        """Should set module ID and title."""
        with patch.object(
            AssessmentCrew, '_load_yaml',
            side_effect=[mock_agents_config, mock_tasks_config]
        ):
            crew = AssessmentCrew()
        
        with patch.object(crew, '_create_assessment_crew') as mock_create_crew:
            mock_result = MagicMock()
            mock_result.raw = quiz_generation_output
            mock_crew_instance = MagicMock()
            mock_crew_instance.kickoff.return_value = mock_result
            mock_create_crew.return_value = mock_crew_instance
            
            quiz = crew.generate_quiz(sample_module)
            
            assert quiz.module_id == sample_module.id
            assert quiz.module_title == sample_module.title
    
    def test_generate_quiz_raises_for_none_module(
        self, mock_agents_config, mock_tasks_config
    ):
        """Should raise ValueError for None module."""
        with patch.object(
            AssessmentCrew, '_load_yaml',
            side_effect=[mock_agents_config, mock_tasks_config]
        ):
            crew = AssessmentCrew()
        
        with pytest.raises(ValueError, match="Module cannot be None"):
            crew.generate_quiz(None)
    
    def test_generate_quiz_raises_for_no_concepts(
        self, mock_agents_config, mock_tasks_config
    ):
        """Should raise ValueError for module without concepts."""
        with patch.object(
            AssessmentCrew, '_load_yaml',
            side_effect=[mock_agents_config, mock_tasks_config]
        ):
            crew = AssessmentCrew()
        
        empty_module = Module(title="Empty", description="No concepts", concepts=[])
        
        with pytest.raises(ValueError, match="Module must have concepts"):
            crew.generate_quiz(empty_module)
    
    def test_generate_quiz_with_weak_concepts(
        self, mock_agents_config, mock_tasks_config, sample_module, quiz_generation_output
    ):
        """Should pass weak concepts to crew."""
        with patch.object(
            AssessmentCrew, '_load_yaml',
            side_effect=[mock_agents_config, mock_tasks_config]
        ):
            crew = AssessmentCrew()
        
        with patch.object(crew, '_create_assessment_crew') as mock_create_crew:
            mock_result = MagicMock()
            mock_result.raw = quiz_generation_output
            mock_crew_instance = MagicMock()
            mock_crew_instance.kickoff.return_value = mock_result
            mock_create_crew.return_value = mock_crew_instance
            
            crew.generate_quiz(sample_module, weak_concepts=["concept-1", "concept-2"])
            
            call_args = mock_crew_instance.kickoff.call_args
            inputs = call_args.kwargs.get("inputs", {})
            
            assert "concept-1" in inputs["weak_areas"]
            assert "concept-2" in inputs["weak_areas"]
    
    def test_generate_quiz_with_previous_attempts(
        self, mock_agents_config, mock_tasks_config, sample_module, quiz_generation_output
    ):
        """Should pass previous attempts count."""
        with patch.object(
            AssessmentCrew, '_load_yaml',
            side_effect=[mock_agents_config, mock_tasks_config]
        ):
            crew = AssessmentCrew()
        
        with patch.object(crew, '_create_assessment_crew') as mock_create_crew:
            mock_result = MagicMock()
            mock_result.raw = quiz_generation_output
            mock_crew_instance = MagicMock()
            mock_crew_instance.kickoff.return_value = mock_result
            mock_create_crew.return_value = mock_crew_instance
            
            crew.generate_quiz(sample_module, previous_attempts=3)
            
            call_args = mock_crew_instance.kickoff.call_args
            inputs = call_args.kwargs.get("inputs", {})
            
            assert inputs["previous_attempts"] == "3"


# ==================== TEST: EVALUATE ANSWERS ====================


class TestAssessmentCrewEvaluateAnswers:
    """Tests for AssessmentCrew.evaluate_answers()."""
    
    def test_evaluate_answers_returns_quiz_result(
        self, mock_agents_config, mock_tasks_config, sample_quiz, evaluation_output
    ):
        """Should return a QuizResult object."""
        with patch.object(
            AssessmentCrew, '_load_yaml',
            side_effect=[mock_agents_config, mock_tasks_config]
        ):
            crew = AssessmentCrew()
        
        with patch.object(crew, '_create_assessment_crew') as mock_create_crew:
            mock_result = MagicMock()
            mock_result.raw = evaluation_output
            mock_crew_instance = MagicMock()
            mock_crew_instance.kickoff.return_value = mock_result
            mock_create_crew.return_value = mock_crew_instance
            
            answers = {
                sample_quiz.questions[0].id: "A) Storage",
                sample_quiz.questions[1].id: "True",
            }
            
            result = crew.evaluate_answers(sample_quiz, answers)
            
            assert isinstance(result, QuizResult)
    
    def test_evaluate_answers_calculates_score(
        self, mock_agents_config, mock_tasks_config, sample_quiz, evaluation_output
    ):
        """Should calculate score from actual answers."""
        with patch.object(
            AssessmentCrew, '_load_yaml',
            side_effect=[mock_agents_config, mock_tasks_config]
        ):
            crew = AssessmentCrew()
        
        with patch.object(crew, '_create_assessment_crew') as mock_create_crew:
            mock_result = MagicMock()
            mock_result.raw = evaluation_output
            mock_crew_instance = MagicMock()
            mock_crew_instance.kickoff.return_value = mock_result
            mock_create_crew.return_value = mock_crew_instance
            
            # Answer both correctly
            answers = {
                sample_quiz.questions[0].id: "A) Storage",
                sample_quiz.questions[1].id: "True",
            }
            
            result = crew.evaluate_answers(sample_quiz, answers)
            
            assert result.score == 1.0
            assert result.passed is True
    
    def test_evaluate_answers_partial_score(
        self, mock_agents_config, mock_tasks_config, sample_quiz, evaluation_output
    ):
        """Should calculate partial score correctly."""
        with patch.object(
            AssessmentCrew, '_load_yaml',
            side_effect=[mock_agents_config, mock_tasks_config]
        ):
            crew = AssessmentCrew()
        
        with patch.object(crew, '_create_assessment_crew') as mock_create_crew:
            mock_result = MagicMock()
            mock_result.raw = evaluation_output
            mock_crew_instance = MagicMock()
            mock_crew_instance.kickoff.return_value = mock_result
            mock_create_crew.return_value = mock_crew_instance
            
            # Answer first correctly, second incorrectly
            answers = {
                sample_quiz.questions[0].id: "A) Storage",
                sample_quiz.questions[1].id: "False",  # Wrong
            }
            
            result = crew.evaluate_answers(sample_quiz, answers)
            
            assert result.score == 0.5
            assert result.passed is False
    
    def test_evaluate_answers_raises_for_none_quiz(
        self, mock_agents_config, mock_tasks_config
    ):
        """Should raise ValueError for None quiz."""
        with patch.object(
            AssessmentCrew, '_load_yaml',
            side_effect=[mock_agents_config, mock_tasks_config]
        ):
            crew = AssessmentCrew()
        
        with pytest.raises(ValueError, match="Quiz cannot be None"):
            crew.evaluate_answers(None, {"q-1": "A"})
    
    def test_evaluate_answers_raises_for_no_questions(
        self, mock_agents_config, mock_tasks_config
    ):
        """Should raise ValueError for quiz without questions."""
        with patch.object(
            AssessmentCrew, '_load_yaml',
            side_effect=[mock_agents_config, mock_tasks_config]
        ):
            crew = AssessmentCrew()
        
        empty_quiz = Quiz(module_id="m-1", module_title="Test", questions=[])
        
        with pytest.raises(ValueError, match="Quiz must have questions"):
            crew.evaluate_answers(empty_quiz, {})
    
    def test_evaluate_answers_includes_feedback(
        self, mock_agents_config, mock_tasks_config, sample_quiz, evaluation_output
    ):
        """Should include feedback in result."""
        with patch.object(
            AssessmentCrew, '_load_yaml',
            side_effect=[mock_agents_config, mock_tasks_config]
        ):
            crew = AssessmentCrew()
        
        with patch.object(crew, '_create_assessment_crew') as mock_create_crew:
            mock_result = MagicMock()
            mock_result.raw = evaluation_output
            mock_crew_instance = MagicMock()
            mock_crew_instance.kickoff.return_value = mock_result
            mock_create_crew.return_value = mock_crew_instance
            
            answers = {sample_quiz.questions[0].id: "A) Storage"}
            
            result = crew.evaluate_answers(sample_quiz, answers)
            
            assert "Great job" in result.feedback
    
    def test_evaluate_answers_with_previous_scores(
        self, mock_agents_config, mock_tasks_config, sample_quiz, evaluation_output
    ):
        """Should pass previous scores to crew."""
        with patch.object(
            AssessmentCrew, '_load_yaml',
            side_effect=[mock_agents_config, mock_tasks_config]
        ):
            crew = AssessmentCrew()
        
        with patch.object(crew, '_create_assessment_crew') as mock_create_crew:
            mock_result = MagicMock()
            mock_result.raw = evaluation_output
            mock_crew_instance = MagicMock()
            mock_crew_instance.kickoff.return_value = mock_result
            mock_create_crew.return_value = mock_crew_instance
            
            answers = {sample_quiz.questions[0].id: "A) Storage"}
            
            crew.evaluate_answers(
                sample_quiz, answers,
                previous_scores=[0.6, 0.7, 0.75]
            )
            
            call_args = mock_crew_instance.kickoff.call_args
            inputs = call_args.kwargs.get("inputs", {})
            
            assert "60%" in inputs["previous_performance"]
            assert "70%" in inputs["previous_performance"]


# ==================== TEST: PARSE QUIZ RESPONSE ====================


class TestAssessmentCrewParseQuizResponse:
    """Tests for _parse_quiz_response() method."""
    
    def test_parse_quiz_response_valid(
        self, mock_agents_config, mock_tasks_config, sample_module, quiz_generation_output
    ):
        """Should parse valid quiz response."""
        with patch.object(
            AssessmentCrew, '_load_yaml',
            side_effect=[mock_agents_config, mock_tasks_config]
        ):
            crew = AssessmentCrew()
        
        quiz = crew._parse_quiz_response(quiz_generation_output, sample_module)
        
        assert isinstance(quiz, Quiz)
        assert len(quiz.questions) == 2
    
    def test_parse_quiz_response_with_markdown(
        self, mock_agents_config, mock_tasks_config, sample_module, quiz_generation_output
    ):
        """Should extract JSON from markdown code block."""
        with patch.object(
            AssessmentCrew, '_load_yaml',
            side_effect=[mock_agents_config, mock_tasks_config]
        ):
            crew = AssessmentCrew()
        
        wrapped_output = f"```json\n{quiz_generation_output}\n```"
        
        quiz = crew._parse_quiz_response(wrapped_output, sample_module)
        
        assert len(quiz.questions) == 2
    
    def test_parse_quiz_response_no_json(
        self, mock_agents_config, mock_tasks_config, sample_module
    ):
        """Should raise ValueError when no JSON found."""
        with patch.object(
            AssessmentCrew, '_load_yaml',
            side_effect=[mock_agents_config, mock_tasks_config]
        ):
            crew = AssessmentCrew()
        
        with pytest.raises(ValueError, match="No JSON found"):
            crew._parse_quiz_response("No JSON here", sample_module)
    
    def test_parse_quiz_response_no_questions(
        self, mock_agents_config, mock_tasks_config, sample_module
    ):
        """Should raise ValueError when no questions found."""
        with patch.object(
            AssessmentCrew, '_load_yaml',
            side_effect=[mock_agents_config, mock_tasks_config]
        ):
            crew = AssessmentCrew()
        
        with pytest.raises(ValueError, match="No questions found"):
            crew._parse_quiz_response('{"questions": []}', sample_module)
    
    def test_parse_quiz_response_all_question_types(
        self, mock_agents_config, mock_tasks_config, sample_module
    ):
        """Should parse all question types correctly."""
        with patch.object(
            AssessmentCrew, '_load_yaml',
            side_effect=[mock_agents_config, mock_tasks_config]
        ):
            crew = AssessmentCrew()
        
        response = json.dumps({
            "questions": [
                {"question": "Q1", "question_type": "multiple_choice", "correct_answer": "A", "options": []},
                {"question": "Q2", "question_type": "true_false", "correct_answer": "True", "options": []},
                {"question": "Q3", "question_type": "code", "correct_answer": "print()", "options": []},
                {"question": "Q4", "question_type": "open_ended", "correct_answer": "Any", "options": []},
            ]
        })
        
        quiz = crew._parse_quiz_response(response, sample_module)
        
        assert quiz.questions[0].question_type == QuestionType.MULTIPLE_CHOICE
        assert quiz.questions[1].question_type == QuestionType.TRUE_FALSE
        assert quiz.questions[2].question_type == QuestionType.CODE
        assert quiz.questions[3].question_type == QuestionType.OPEN_ENDED


# ==================== TEST: PARSE EVALUATION RESPONSE ====================


class TestAssessmentCrewParseEvaluationResponse:
    """Tests for _parse_evaluation_response() method."""
    
    def test_parse_evaluation_response_valid(
        self, mock_agents_config, mock_tasks_config, sample_quiz, evaluation_output
    ):
        """Should parse valid evaluation response."""
        with patch.object(
            AssessmentCrew, '_load_yaml',
            side_effect=[mock_agents_config, mock_tasks_config]
        ):
            crew = AssessmentCrew()
        
        answers = {
            sample_quiz.questions[0].id: "A) Storage",
            sample_quiz.questions[1].id: "True",
        }
        
        result = crew._parse_evaluation_response(
            evaluation_output, sample_quiz, answers, "course-123"
        )
        
        assert isinstance(result, QuizResult)
        assert result.course_id == "course-123"
    
    def test_parse_evaluation_response_includes_next_steps(
        self, mock_agents_config, mock_tasks_config, sample_quiz, evaluation_output
    ):
        """Should include next_steps in feedback."""
        with patch.object(
            AssessmentCrew, '_load_yaml',
            side_effect=[mock_agents_config, mock_tasks_config]
        ):
            crew = AssessmentCrew()
        
        answers = {sample_quiz.questions[0].id: "A) Storage"}
        
        result = crew._parse_evaluation_response(
            evaluation_output, sample_quiz, answers
        )
        
        assert "Next Steps" in result.feedback
        assert "Control Flow" in result.feedback
    
    def test_parse_evaluation_response_fallback_for_invalid_json(
        self, mock_agents_config, mock_tasks_config, sample_quiz
    ):
        """Should use raw response as feedback when JSON parsing fails."""
        with patch.object(
            AssessmentCrew, '_load_yaml',
            side_effect=[mock_agents_config, mock_tasks_config]
        ):
            crew = AssessmentCrew()
        
        answers = {sample_quiz.questions[0].id: "A) Storage"}
        
        # When JSON is invalid (malformed), the raw response is used as feedback
        # The response must have { } for JSON parsing to be attempted
        raw_response = "Here is feedback: { invalid json here }"
        result = crew._parse_evaluation_response(
            raw_response, sample_quiz, answers
        )
        
        # The method uses the raw response when JSON parsing raises an exception
        assert result.feedback == raw_response
    
    def test_parse_evaluation_response_no_json_uses_default(
        self, mock_agents_config, mock_tasks_config, sample_quiz
    ):
        """Should use default feedback when no JSON braces found."""
        with patch.object(
            AssessmentCrew, '_load_yaml',
            side_effect=[mock_agents_config, mock_tasks_config]
        ):
            crew = AssessmentCrew()
        
        answers = {sample_quiz.questions[0].id: "A) Storage"}
        
        # When there are no { } braces, JSON parsing is skipped
        raw_response = "Great work! Keep it up!"
        result = crew._parse_evaluation_response(
            raw_response, sample_quiz, answers
        )
        
        # Default feedback is used when no JSON found
        assert result.feedback == "Quiz completed."
    
    def test_parse_evaluation_response_calculates_weak_concepts(
        self, mock_agents_config, mock_tasks_config, sample_quiz
    ):
        """Should calculate weak concepts from wrong answers."""
        with patch.object(
            AssessmentCrew, '_load_yaml',
            side_effect=[mock_agents_config, mock_tasks_config]
        ):
            crew = AssessmentCrew()
        
        # Answer first wrong, second correct
        answers = {
            sample_quiz.questions[0].id: "Wrong",
            sample_quiz.questions[1].id: "True",
        }
        
        # Return JSON without weak_concepts to test fallback
        response = json.dumps({
            "feedback": "Review variables.",
            "weak_concepts": [],
        })
        
        result = crew._parse_evaluation_response(response, sample_quiz, answers)
        
        # Should calculate weak concepts from wrong answer
        assert "concept-1" in result.weak_concepts


# ==================== TEST: HELPER METHODS ====================


class TestAssessmentCrewHelperMethods:
    """Tests for helper formatting methods."""
    
    def test_format_concepts_list_empty(self, mock_agents_config, mock_tasks_config):
        """Should handle empty concepts list."""
        with patch.object(
            AssessmentCrew, '_load_yaml',
            side_effect=[mock_agents_config, mock_tasks_config]
        ):
            crew = AssessmentCrew()
        
        result = crew._format_concepts_list([])
        
        assert result == "No concepts available."
    
    def test_format_concepts_list_with_concepts(self, mock_agents_config, mock_tasks_config):
        """Should format concepts as numbered list."""
        with patch.object(
            AssessmentCrew, '_load_yaml',
            side_effect=[mock_agents_config, mock_tasks_config]
        ):
            crew = AssessmentCrew()
        
        concepts = [
            {"title": "Variables", "content": "Store data", "id": "c-1"},
            {"title": "Functions", "content": "Reusable code", "id": "c-2"},
        ]
        
        result = crew._format_concepts_list(concepts)
        
        assert "1. **Variables**" in result
        assert "2. **Functions**" in result
        assert "(ID: c-1)" in result
    
    def test_format_concepts_list_truncates_long_content(
        self, mock_agents_config, mock_tasks_config
    ):
        """Should truncate long content."""
        with patch.object(
            AssessmentCrew, '_load_yaml',
            side_effect=[mock_agents_config, mock_tasks_config]
        ):
            crew = AssessmentCrew()
        
        concepts = [
            {"title": "Test", "content": "A" * 500, "id": "c-1"},
        ]
        
        result = crew._format_concepts_list(concepts)
        
        assert "..." in result
        assert len(result) < 500
    
    def test_format_focus_concepts_empty(self, mock_agents_config, mock_tasks_config):
        """Should handle empty focus concepts."""
        with patch.object(
            AssessmentCrew, '_load_yaml',
            side_effect=[mock_agents_config, mock_tasks_config]
        ):
            crew = AssessmentCrew()
        
        result = crew._format_focus_concepts([], [])
        
        assert "No specific focus areas" in result
    
    def test_format_focus_concepts_with_ids(self, mock_agents_config, mock_tasks_config):
        """Should format focus concepts correctly."""
        with patch.object(
            AssessmentCrew, '_load_yaml',
            side_effect=[mock_agents_config, mock_tasks_config]
        ):
            crew = AssessmentCrew()
        
        concepts = [
            {"title": "Variables", "id": "c-1"},
            {"title": "Functions", "id": "c-2"},
        ]
        
        result = crew._format_focus_concepts(concepts, ["c-1"])
        
        assert "Variables" in result
        assert "Functions" not in result
    
    def test_format_detailed_results(
        self, mock_agents_config, mock_tasks_config, sample_quiz
    ):
        """Should format detailed results correctly."""
        with patch.object(
            AssessmentCrew, '_load_yaml',
            side_effect=[mock_agents_config, mock_tasks_config]
        ):
            crew = AssessmentCrew()
        
        answers = {
            sample_quiz.questions[0].id: "A) Storage",
            sample_quiz.questions[1].id: "False",
        }
        
        result = crew._format_detailed_results(sample_quiz, answers)
        
        assert "Question 1" in result
        assert "Question 2" in result
        assert "✅ Correct" in result
        assert "❌ Incorrect" in result
    
    def test_format_detailed_results_unanswered(
        self, mock_agents_config, mock_tasks_config, sample_quiz
    ):
        """Should handle unanswered questions."""
        with patch.object(
            AssessmentCrew, '_load_yaml',
            side_effect=[mock_agents_config, mock_tasks_config]
        ):
            crew = AssessmentCrew()
        
        # Only answer first question
        answers = {sample_quiz.questions[0].id: "A) Storage"}
        
        result = crew._format_detailed_results(sample_quiz, answers)
        
        assert "Not answered" in result


# ==================== TEST: EDGE CASES ====================


class TestAssessmentCrewEdgeCases:
    """Edge case tests for AssessmentCrew."""
    
    def test_unicode_in_questions(
        self, mock_agents_config, mock_tasks_config, sample_module
    ):
        """Should handle unicode in quiz questions."""
        with patch.object(
            AssessmentCrew, '_load_yaml',
            side_effect=[mock_agents_config, mock_tasks_config]
        ):
            crew = AssessmentCrew()
        
        with patch.object(crew, '_create_assessment_crew') as mock_create_crew:
            response = json.dumps({
                "questions": [
                    {
                        "question": "什么是变量？🐍",
                        "question_type": "multiple_choice",
                        "options": ["A) 存储数据", "B) 函数"],
                        "correct_answer": "A) 存储数据",
                        "explanation": "变量用于存储数据。",
                        "concept_id": "c-1",
                        "difficulty": 2,
                    }
                ]
            })
            
            mock_result = MagicMock()
            mock_result.raw = response
            mock_crew_instance = MagicMock()
            mock_crew_instance.kickoff.return_value = mock_result
            mock_create_crew.return_value = mock_crew_instance
            
            quiz = crew.generate_quiz(sample_module)
            
            assert "🐍" in quiz.questions[0].question
    
    def test_all_experience_levels(
        self, mock_agents_config, mock_tasks_config, sample_module, quiz_generation_output
    ):
        """Should handle all experience levels."""
        for level in ExperienceLevel:
            with patch.object(
                AssessmentCrew, '_load_yaml',
                side_effect=[mock_agents_config, mock_tasks_config]
            ):
                crew = AssessmentCrew()
            
            with patch.object(crew, '_create_assessment_crew') as mock_create_crew:
                mock_result = MagicMock()
                mock_result.raw = quiz_generation_output
                mock_crew_instance = MagicMock()
                mock_crew_instance.kickoff.return_value = mock_result
                mock_create_crew.return_value = mock_crew_instance
                
                user_prefs = UserPreferences(experience_level=level)
                quiz = crew.generate_quiz(sample_module, user_prefs=user_prefs)
                
                assert isinstance(quiz, Quiz)
    
    def test_empty_answers_dict(
        self, mock_agents_config, mock_tasks_config, sample_quiz, evaluation_output
    ):
        """Should handle empty answers (all unanswered)."""
        with patch.object(
            AssessmentCrew, '_load_yaml',
            side_effect=[mock_agents_config, mock_tasks_config]
        ):
            crew = AssessmentCrew()
        
        with patch.object(crew, '_create_assessment_crew') as mock_create_crew:
            mock_result = MagicMock()
            mock_result.raw = evaluation_output
            mock_crew_instance = MagicMock()
            mock_crew_instance.kickoff.return_value = mock_result
            mock_create_crew.return_value = mock_crew_instance
            
            result = crew.evaluate_answers(sample_quiz, {})
            
            assert result.score == 0.0
            assert result.passed is False
    
    def test_parse_quiz_response_unknown_question_type(
        self, mock_agents_config, mock_tasks_config, sample_module
    ):
        """Should default to multiple choice for unknown type."""
        with patch.object(
            AssessmentCrew, '_load_yaml',
            side_effect=[mock_agents_config, mock_tasks_config]
        ):
            crew = AssessmentCrew()
        
        response = json.dumps({
            "questions": [
                {
                    "question": "Test?",
                    "question_type": "unknown_type",
                    "correct_answer": "A",
                    "options": ["A", "B"],
                }
            ]
        })
        
        quiz = crew._parse_quiz_response(response, sample_module)
        
        assert quiz.questions[0].question_type == QuestionType.MULTIPLE_CHOICE
    
    def test_large_quiz(
        self, mock_agents_config, mock_tasks_config, sample_module
    ):
        """Should handle large quiz with many questions."""
        with patch.object(
            AssessmentCrew, '_load_yaml',
            side_effect=[mock_agents_config, mock_tasks_config]
        ):
            crew = AssessmentCrew()
        
        with patch.object(crew, '_create_assessment_crew') as mock_create_crew:
            # Generate 20 questions
            questions = [
                {
                    "question": f"Question {i}?",
                    "question_type": "multiple_choice",
                    "options": ["A", "B", "C", "D"],
                    "correct_answer": "A",
                    "explanation": f"Explanation {i}",
                    "concept_id": f"c-{i}",
                    "difficulty": 2,
                }
                for i in range(20)
            ]
            
            mock_result = MagicMock()
            mock_result.raw = json.dumps({"questions": questions})
            mock_crew_instance = MagicMock()
            mock_crew_instance.kickoff.return_value = mock_result
            mock_create_crew.return_value = mock_crew_instance
            
            quiz = crew.generate_quiz(sample_module)
            
            assert len(quiz.questions) == 20
    
    def test_improving_trend_detection(
        self, mock_agents_config, mock_tasks_config, sample_quiz, evaluation_output
    ):
        """Should detect improving trend in previous scores."""
        with patch.object(
            AssessmentCrew, '_load_yaml',
            side_effect=[mock_agents_config, mock_tasks_config]
        ):
            crew = AssessmentCrew()
        
        with patch.object(crew, '_create_assessment_crew') as mock_create_crew:
            mock_result = MagicMock()
            mock_result.raw = evaluation_output
            mock_crew_instance = MagicMock()
            mock_crew_instance.kickoff.return_value = mock_result
            mock_create_crew.return_value = mock_crew_instance
            
            answers = {sample_quiz.questions[0].id: "A) Storage"}
            
            crew.evaluate_answers(
                sample_quiz, answers,
                previous_scores=[0.5, 0.6, 0.75]  # Improving
            )
            
            call_args = mock_crew_instance.kickoff.call_args
            inputs = call_args.kwargs.get("inputs", {})
            
            assert "improving" in inputs["previous_performance"]
    
    def test_declining_trend_detection(
        self, mock_agents_config, mock_tasks_config, sample_quiz, evaluation_output
    ):
        """Should detect declining trend in previous scores."""
        with patch.object(
            AssessmentCrew, '_load_yaml',
            side_effect=[mock_agents_config, mock_tasks_config]
        ):
            crew = AssessmentCrew()
        
        with patch.object(crew, '_create_assessment_crew') as mock_create_crew:
            mock_result = MagicMock()
            mock_result.raw = evaluation_output
            mock_crew_instance = MagicMock()
            mock_crew_instance.kickoff.return_value = mock_result
            mock_create_crew.return_value = mock_crew_instance
            
            answers = {sample_quiz.questions[0].id: "A) Storage"}
            
            crew.evaluate_answers(
                sample_quiz, answers,
                previous_scores=[0.8, 0.7, 0.6]  # Declining
            )
            
            call_args = mock_crew_instance.kickoff.call_args
            inputs = call_args.kwargs.get("inputs", {})
            
            assert "needs attention" in inputs["previous_performance"]
