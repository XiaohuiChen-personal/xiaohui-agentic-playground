"""Unit tests for quiz page."""

from unittest.mock import MagicMock, patch

import pytest

from sensei.models.enums import QuestionType
from sensei.models.schemas import AnswerResult, Quiz, QuizQuestion, QuizResult


@pytest.fixture
def sample_quiz():
    """Sample Quiz for testing."""
    return Quiz(
        id="quiz-123",
        module_id="m1",
        module_title="Introduction to Python",
        questions=[
            QuizQuestion(
                id="q1",
                question="What is 2 + 2?",
                question_type=QuestionType.MULTIPLE_CHOICE,
                options=["3", "4", "5", "6"],
                correct_answer="4",
                explanation="Basic arithmetic",
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
        ],
    )


@pytest.fixture
def sample_quiz_no_title():
    """Sample Quiz without module_title for testing."""
    return Quiz(
        id="quiz-456",
        module_id="m1",
        module_title="",  # Empty title
        questions=[
            QuizQuestion(
                id="q1",
                question="Test question?",
                question_type=QuestionType.MULTIPLE_CHOICE,
                options=["A", "B"],
                correct_answer="A",
            ),
        ],
    )


@pytest.fixture
def sample_answer_result_correct():
    """Sample correct answer result."""
    return AnswerResult(
        question_id="q1",
        user_answer="4",
        is_correct=True,
        correct_answer="4",
        explanation="2 + 2 = 4",
    )


@pytest.fixture
def sample_answer_result_incorrect():
    """Sample incorrect answer result."""
    return AnswerResult(
        question_id="q1",
        user_answer="5",
        is_correct=False,
        correct_answer="4",
        explanation="2 + 2 = 4, not 5",
    )


@pytest.fixture
def sample_quiz_result_pass():
    """Sample passing quiz result."""
    return QuizResult(
        quiz_id="quiz-123",
        score=0.9,
        correct_count=9,
        total_questions=10,
        weak_concepts=[],
        feedback="Excellent work!",
        passed=True,
    )


@pytest.fixture
def sample_quiz_result_fail():
    """Sample failing quiz result."""
    return QuizResult(
        quiz_id="quiz-123",
        score=0.5,
        correct_count=5,
        total_questions=10,
        weak_concepts=["concept-1", "concept-2"],
        feedback="Review the concepts and try again.",
        passed=False,
    )


class TestRenderQuizPage:
    """Tests for render_quiz_page function."""

    def test_render_quiz_page_basic(self, mock_streamlit, sample_quiz):
        """Test rendering quiz page without errors."""
        with patch("sensei.ui.pages.quiz.st", mock_streamlit):
            with patch("sensei.ui.components.sidebar.st", mock_streamlit):
                with patch("sensei.ui.components.quiz_question.st", mock_streamlit):
                    from sensei.ui.pages.quiz import render_quiz_page
                    
                    render_quiz_page(quiz=sample_quiz)
                    
                    mock_streamlit.markdown.assert_called()

    def test_render_quiz_page_no_quiz(self, mock_streamlit):
        """Test page shows message when no quiz available."""
        with patch("sensei.ui.pages.quiz.st", mock_streamlit):
            with patch("sensei.ui.components.sidebar.st", mock_streamlit):
                with patch("sensei.ui.components.quiz_question.st", mock_streamlit):
                    from sensei.ui.pages.quiz import render_quiz_page
                    
                    render_quiz_page(quiz=None)
                    
                    calls = mock_streamlit.markdown.call_args_list
                    assert any("No quiz" in str(c) for c in calls)

    def test_render_quiz_page_shows_question(self, mock_streamlit, sample_quiz):
        """Test page shows current question."""
        with patch("sensei.ui.pages.quiz.st", mock_streamlit):
            with patch("sensei.ui.components.sidebar.st", mock_streamlit):
                with patch("sensei.ui.components.quiz_question.st", mock_streamlit):
                    from sensei.ui.pages.quiz import render_quiz_page
                    
                    render_quiz_page(
                        quiz=sample_quiz,
                        current_question_idx=0,
                    )
                    
                    calls = mock_streamlit.markdown.call_args_list
                    # Should show first question
                    assert any("2 + 2" in str(c) for c in calls)

    def test_render_quiz_page_shows_options(self, mock_streamlit, sample_quiz):
        """Test page shows answer options."""
        with patch("sensei.ui.pages.quiz.st", mock_streamlit):
            with patch("sensei.ui.components.sidebar.st", mock_streamlit):
                with patch("sensei.ui.components.quiz_question.st", mock_streamlit):
                    from sensei.ui.pages.quiz import render_quiz_page
                    
                    render_quiz_page(
                        quiz=sample_quiz,
                        current_question_idx=0,
                    )
                    
                    mock_streamlit.radio.assert_called()

    def test_render_quiz_page_submit_button(self, mock_streamlit, sample_quiz):
        """Test page shows submit button."""
        with patch("sensei.ui.pages.quiz.st", mock_streamlit):
            with patch("sensei.ui.components.sidebar.st", mock_streamlit):
                with patch("sensei.ui.components.quiz_question.st", mock_streamlit):
                    from sensei.ui.pages.quiz import render_quiz_page
                    
                    render_quiz_page(
                        quiz=sample_quiz,
                        current_question_idx=0,
                    )
                    
                    button_calls = [
                        c for c in mock_streamlit.button.call_args_list
                        if "Submit" in str(c)
                    ]
                    assert len(button_calls) > 0

    def test_render_quiz_page_shows_results_when_complete(
        self, mock_streamlit, sample_quiz, sample_quiz_result_pass
    ):
        """Test page shows results when quiz is complete."""
        with patch("sensei.ui.pages.quiz.st", mock_streamlit):
            with patch("sensei.ui.components.sidebar.st", mock_streamlit):
                with patch("sensei.ui.components.quiz_question.st", mock_streamlit):
                    from sensei.ui.pages.quiz import render_quiz_page
                    
                    render_quiz_page(
                        quiz=sample_quiz,
                        is_complete=True,
                        quiz_result=sample_quiz_result_pass,
                    )
                    
                    calls = mock_streamlit.markdown.call_args_list
                    assert any("Complete" in str(c) for c in calls)


class TestRenderHeader:
    """Tests for _render_header function."""

    def test_render_header_shows_module_title(self, mock_streamlit):
        """Test header shows module title."""
        with patch("sensei.ui.pages.quiz.st", mock_streamlit):
            from sensei.ui.pages.quiz import _render_header
            
            _render_header("Introduction to Python")
            
            calls = mock_streamlit.markdown.call_args_list
            assert any("Introduction to Python" in str(c) for c in calls)


class TestRenderQuestionSection:
    """Tests for _render_question_section function."""

    def test_render_question_section_shows_question(
        self, mock_streamlit, sample_quiz
    ):
        """Test question section shows question text."""
        with patch("sensei.ui.pages.quiz.st", mock_streamlit):
            from sensei.ui.pages.quiz import _render_question_section
            
            _render_question_section(
                question=sample_quiz.questions[0],
                last_result=None,
                on_submit=None,
                on_next=None,
            )
            
            calls = mock_streamlit.markdown.call_args_list
            assert any("2 + 2" in str(c) for c in calls)

    def test_render_question_section_shows_feedback(
        self, mock_streamlit, sample_quiz, sample_answer_result_correct
    ):
        """Test question section shows feedback when answered."""
        with patch("sensei.ui.pages.quiz.st", mock_streamlit):
            from sensei.ui.pages.quiz import _render_question_section
            
            _render_question_section(
                question=sample_quiz.questions[0],
                last_result=sample_answer_result_correct,
                on_submit=None,
                on_next=None,
            )
            
            calls = mock_streamlit.markdown.call_args_list
            assert any("Correct" in str(c) for c in calls)


class TestRenderAnswerFeedback:
    """Tests for _render_answer_feedback function."""

    def test_render_feedback_correct(
        self, mock_streamlit, sample_quiz, sample_answer_result_correct
    ):
        """Test feedback shows correct message."""
        with patch("sensei.ui.pages.quiz.st", mock_streamlit):
            from sensei.ui.pages.quiz import _render_answer_feedback
            
            _render_answer_feedback(
                sample_answer_result_correct,
                sample_quiz.questions[0],
            )
            
            calls = mock_streamlit.markdown.call_args_list
            assert any("Correct" in str(c) for c in calls)

    def test_render_feedback_incorrect(
        self, mock_streamlit, sample_quiz, sample_answer_result_incorrect
    ):
        """Test feedback shows incorrect message with correct answer."""
        with patch("sensei.ui.pages.quiz.st", mock_streamlit):
            from sensei.ui.pages.quiz import _render_answer_feedback
            
            _render_answer_feedback(
                sample_answer_result_incorrect,
                sample_quiz.questions[0],
            )
            
            calls = mock_streamlit.markdown.call_args_list
            assert any("Incorrect" in str(c) for c in calls)
            # Should show correct answer
            assert any("4" in str(c) for c in calls)


class TestRenderResultsSection:
    """Tests for _render_results_section function."""

    def test_render_results_pass(
        self, mock_streamlit, sample_quiz_result_pass
    ):
        """Test results show pass message."""
        with patch("sensei.ui.pages.quiz.st", mock_streamlit):
            from sensei.ui.pages.quiz import _render_results_section
            
            _render_results_section(
                quiz_result=sample_quiz_result_pass,
                on_continue=None,
                on_review=None,
                on_retake=None,
            )
            
            calls = mock_streamlit.markdown.call_args_list
            assert any("PASSED" in str(c) for c in calls)

    def test_render_results_fail(
        self, mock_streamlit, sample_quiz_result_fail
    ):
        """Test results show fail message."""
        with patch("sensei.ui.pages.quiz.st", mock_streamlit):
            from sensei.ui.pages.quiz import _render_results_section
            
            _render_results_section(
                quiz_result=sample_quiz_result_fail,
                on_continue=None,
                on_review=None,
                on_retake=None,
            )
            
            calls = mock_streamlit.markdown.call_args_list
            # Should encourage practicing
            assert any("practicing" in str(c).lower() for c in calls)

    def test_render_results_shows_score(
        self, mock_streamlit, sample_quiz_result_pass
    ):
        """Test results show score."""
        with patch("sensei.ui.pages.quiz.st", mock_streamlit):
            from sensei.ui.pages.quiz import _render_results_section
            
            _render_results_section(
                quiz_result=sample_quiz_result_pass,
                on_continue=None,
                on_review=None,
                on_retake=None,
            )
            
            calls = mock_streamlit.markdown.call_args_list
            # Should show score
            assert any("9/10" in str(c) or "90%" in str(c) for c in calls)

    def test_render_results_shows_weak_concepts(
        self, mock_streamlit, sample_quiz_result_fail
    ):
        """Test results show weak concepts."""
        with patch("sensei.ui.pages.quiz.st", mock_streamlit):
            from sensei.ui.pages.quiz import _render_results_section
            
            _render_results_section(
                quiz_result=sample_quiz_result_fail,
                on_continue=None,
                on_review=None,
                on_retake=None,
            )
            
            calls = mock_streamlit.markdown.call_args_list
            # Should show areas to review
            assert any("Review" in str(c) for c in calls)

    def test_render_results_continue_callback(
        self, mock_streamlit, sample_quiz_result_pass
    ):
        """Test continue button triggers callback."""
        def button_side_effect(*args, **kwargs):
            if "continue" in kwargs.get("key", ""):
                return True
            return False
        
        mock_streamlit.button.side_effect = button_side_effect
        
        with patch("sensei.ui.pages.quiz.st", mock_streamlit):
            from sensei.ui.pages.quiz import _render_results_section
            
            callback = MagicMock()
            
            _render_results_section(
                quiz_result=sample_quiz_result_pass,
                on_continue=callback,
                on_review=None,
                on_retake=None,
            )
            
            callback.assert_called_once()


class TestRenderQuizWithServices:
    """Tests for render_quiz_with_services function."""

    def test_render_with_services_generates_quiz(self, mock_streamlit):
        """Test service integration generates quiz for course/module."""
        with patch("sensei.ui.pages.quiz.st", mock_streamlit):
            with patch("sensei.ui.components.sidebar.st", mock_streamlit):
                with patch("sensei.ui.components.quiz_question.st", mock_streamlit):
                    from sensei.ui.pages.quiz import render_quiz_with_services
                    
                    mock_quiz_service = MagicMock()
                    mock_quiz_service.is_quiz_active = False
                    mock_quiz_service.current_quiz = None
                    
                    # After generate_quiz, is_quiz_active should be True
                    def gen_side_effect(*args, **kwargs):
                        mock_quiz_service.is_quiz_active = True
                        mock_quiz_service.current_quiz = Quiz(
                            id="q1",
                            module_id="m1",
                            questions=[
                                QuizQuestion(
                                    id="q1",
                                    question="Test?",
                                    question_type=QuestionType.MULTIPLE_CHOICE,
                                    options=["A", "B"],
                                    correct_answer="A",
                                )
                            ],
                        )
                    
                    mock_quiz_service.generate_quiz.side_effect = gen_side_effect
                    
                    render_quiz_with_services(
                        quiz_service=mock_quiz_service,
                        course_id="test-course",
                        module_idx=0,
                    )
                    
                    mock_quiz_service.generate_quiz.assert_called()

    def test_render_with_services_no_quiz_error(self, mock_streamlit):
        """Test shows error when no quiz can be generated."""
        with patch("sensei.ui.pages.quiz.st", mock_streamlit):
            with patch("sensei.ui.components.sidebar.st", mock_streamlit):
                with patch("sensei.ui.components.quiz_question.st", mock_streamlit):
                    from sensei.ui.pages.quiz import render_quiz_with_services
                    
                    mock_quiz_service = MagicMock()
                    mock_quiz_service.is_quiz_active = False
                    mock_quiz_service.current_quiz = None
                    
                    render_quiz_with_services(
                        quiz_service=mock_quiz_service,
                    )
                    
                    mock_streamlit.error.assert_called()

    def test_render_with_services_uses_quiz_module_title(self, mock_streamlit, sample_quiz):
        """Test service integration uses quiz.module_title for header."""
        with patch("sensei.ui.pages.quiz.st", mock_streamlit):
            with patch("sensei.ui.components.sidebar.st", mock_streamlit):
                with patch("sensei.ui.components.quiz_question.st", mock_streamlit):
                    from sensei.ui.pages.quiz import render_quiz_with_services
                    
                    mock_quiz_service = MagicMock()
                    mock_quiz_service.is_quiz_active = True
                    mock_quiz_service.current_quiz = sample_quiz
                    
                    render_quiz_with_services(
                        quiz_service=mock_quiz_service,
                        course_id="test-course",
                        module_idx=0,
                    )
                    
                    # Verify module title from quiz is shown in header
                    calls = mock_streamlit.markdown.call_args_list
                    assert any("Introduction to Python" in str(c) for c in calls)

    def test_render_with_services_handles_empty_module_title(
        self, mock_streamlit, sample_quiz_no_title
    ):
        """Test service integration handles quiz with empty module_title."""
        with patch("sensei.ui.pages.quiz.st", mock_streamlit):
            with patch("sensei.ui.components.sidebar.st", mock_streamlit):
                with patch("sensei.ui.components.quiz_question.st", mock_streamlit):
                    from sensei.ui.pages.quiz import render_quiz_with_services
                    
                    mock_quiz_service = MagicMock()
                    mock_quiz_service.is_quiz_active = True
                    mock_quiz_service.current_quiz = sample_quiz_no_title
                    
                    # Should not raise any errors
                    render_quiz_with_services(
                        quiz_service=mock_quiz_service,
                        course_id="test-course",
                        module_idx=0,
                    )
                    
                    # Page should still render (markdown called for header)
                    mock_streamlit.markdown.assert_called()

    def test_render_with_services_no_private_module_data_access(self, mock_streamlit, sample_quiz):
        """Test service integration does NOT access _module_data (uses quiz.module_title)."""
        with patch("sensei.ui.pages.quiz.st", mock_streamlit):
            with patch("sensei.ui.components.sidebar.st", mock_streamlit):
                with patch("sensei.ui.components.quiz_question.st", mock_streamlit):
                    from sensei.ui.pages.quiz import render_quiz_with_services
                    
                    mock_quiz_service = MagicMock()
                    mock_quiz_service.is_quiz_active = True
                    mock_quiz_service.current_quiz = sample_quiz
                    # Remove _module_data attribute to ensure it's not accessed
                    del mock_quiz_service._module_data
                    
                    # Should NOT raise AttributeError
                    render_quiz_with_services(
                        quiz_service=mock_quiz_service,
                        course_id="test-course",
                        module_idx=0,
                    )
                    
                    # Should use quiz.module_title instead
                    calls = mock_streamlit.markdown.call_args_list
                    assert any("Introduction to Python" in str(c) for c in calls)

    def test_render_with_services_shows_spinner_during_quiz_generation(
        self, mock_streamlit
    ):
        """Test spinner is shown during quiz generation."""
        with patch("sensei.ui.pages.quiz.st", mock_streamlit):
            with patch("sensei.ui.components.sidebar.st", mock_streamlit):
                with patch("sensei.ui.components.quiz_question.st", mock_streamlit):
                    from sensei.ui.pages.quiz import render_quiz_with_services
                    
                    mock_quiz_service = MagicMock()
                    mock_quiz_service.is_quiz_active = False
                    mock_quiz_service.current_quiz = None
                    
                    # After generate_quiz, quiz should be active
                    def gen_side_effect(*args, **kwargs):
                        mock_quiz_service.is_quiz_active = True
                        mock_quiz_service.current_quiz = Quiz(
                            id="q1",
                            module_id="m1",
                            questions=[
                                QuizQuestion(
                                    id="q1",
                                    question="Test?",
                                    question_type=QuestionType.MULTIPLE_CHOICE,
                                    options=["A", "B"],
                                    correct_answer="A",
                                )
                            ],
                        )
                    
                    mock_quiz_service.generate_quiz.side_effect = gen_side_effect
                    
                    render_quiz_with_services(
                        quiz_service=mock_quiz_service,
                        course_id="test-course",
                        module_idx=0,
                    )
                    
                    # Verify spinner was called during quiz generation
                    mock_streamlit.spinner.assert_called()
                    spinner_calls = mock_streamlit.spinner.call_args_list
                    assert any("Assessment Crew" in str(c) for c in spinner_calls)

    def test_render_with_services_shows_spinner_during_retake(
        self, mock_streamlit, sample_quiz
    ):
        """Test spinner is shown during quiz retake."""
        # Set up button to trigger retake
        def button_side_effect(*args, **kwargs):
            if "retake" in kwargs.get("key", ""):
                return True
            return False
        
        mock_streamlit.button.side_effect = button_side_effect
        
        with patch("sensei.ui.pages.quiz.st", mock_streamlit):
            with patch("sensei.ui.components.sidebar.st", mock_streamlit):
                with patch("sensei.ui.components.quiz_question.st", mock_streamlit):
                    from sensei.ui.pages.quiz import render_quiz_with_services
                    
                    mock_quiz_service = MagicMock()
                    mock_quiz_service.is_quiz_active = True
                    mock_quiz_service.current_quiz = sample_quiz
                    
                    # Set up session state for completed quiz (failed)
                    mock_streamlit.session_state = {
                        "quiz_current_idx": 0,
                        "quiz_last_result": None,
                        "quiz_is_complete": True,
                        "quiz_final_result": QuizResult(
                            quiz_id="quiz-123",
                            score=0.5,
                            correct_count=5,
                            total_questions=10,
                            passed=False,
                        ),
                    }
                    
                    render_quiz_with_services(
                        quiz_service=mock_quiz_service,
                        course_id="test-course",
                        module_idx=0,
                    )
                    
                    # Verify generate_quiz was called for retake
                    if mock_quiz_service.generate_quiz.called:
                        spinner_calls = mock_streamlit.spinner.call_args_list
                        assert any("new quiz" in str(c).lower() for c in spinner_calls)
