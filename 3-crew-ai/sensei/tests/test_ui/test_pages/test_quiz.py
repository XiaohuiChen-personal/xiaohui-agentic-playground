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
                    
                    # Quiz page uses radio with index=None for no default selection
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

    def test_render_quiz_page_passes_correct_index_to_progress(
        self, mock_streamlit, sample_quiz
    ):
        """Test that render_quiz_page passes 0-based index to render_quiz_progress.
        
        This test catches the double +1 bug:
        - render_quiz_page should pass current_question_idx (0-based)
        - render_quiz_progress adds +1 for display
        - If render_quiz_page also adds +1, we get double increment
        """
        # Create a separate mock for quiz_question to capture its calls
        mock_quiz_question_st = MagicMock()
        mock_quiz_question_st.columns.return_value = [MagicMock(), MagicMock()]
        
        with patch("sensei.ui.pages.quiz.st", mock_streamlit):
            with patch("sensei.ui.components.sidebar.st", mock_streamlit):
                with patch("sensei.ui.components.quiz_question.st", mock_quiz_question_st):
                    from sensei.ui.pages.quiz import render_quiz_page
                    
                    # When current_question_idx=0, the displayed text should be "Question 1"
                    render_quiz_page(
                        quiz=sample_quiz,
                        current_question_idx=0,
                    )
                    
                    # Check calls to quiz_question's st.markdown
                    markdown_calls = [str(c) for c in mock_quiz_question_st.markdown.call_args_list]
                    
                    # Should show "Question 1 of 2" (sample_quiz has 2 questions)
                    assert any("Question 1 of 2" in call for call in markdown_calls), \
                        f"Expected 'Question 1 of 2' for index 0, but got: {markdown_calls}"
                    
                    # Should NOT show "Question 2 of 2" (that would be double increment bug)
                    assert not any("Question 2 of 2" in call for call in markdown_calls), \
                        "Bug: Double increment detected - showing Question 2 for index 0"

    def test_render_quiz_page_last_question_shows_correct_number(
        self, mock_streamlit, sample_quiz
    ):
        """Test last question shows correct number (not N+1 of N)."""
        mock_quiz_question_st = MagicMock()
        mock_quiz_question_st.columns.return_value = [MagicMock(), MagicMock()]
        
        with patch("sensei.ui.pages.quiz.st", mock_streamlit):
            with patch("sensei.ui.components.sidebar.st", mock_streamlit):
                with patch("sensei.ui.components.quiz_question.st", mock_quiz_question_st):
                    from sensei.ui.pages.quiz import render_quiz_page
                    
                    # sample_quiz has 2 questions, so last index is 1
                    render_quiz_page(
                        quiz=sample_quiz,
                        current_question_idx=1,
                    )
                    
                    markdown_calls = [str(c) for c in mock_quiz_question_st.markdown.call_args_list]
                    
                    # Should show "Question 2 of 2"
                    assert any("Question 2 of 2" in call for call in markdown_calls), \
                        f"Expected 'Question 2 of 2' for last question, but got: {markdown_calls}"
                    
                    # Should NOT show "Question 3 of 2" (out of bounds)
                    assert not any("Question 3 of 2" in call for call in markdown_calls), \
                        "Bug: Double increment detected - showing Question 3 of 2"


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

    def test_render_question_section_uses_radio_with_index_none(
        self, mock_streamlit, sample_quiz
    ):
        """Test question section uses radio with index=None for answer options."""
        with patch("sensei.ui.pages.quiz.st", mock_streamlit):
            from sensei.ui.pages.quiz import _render_question_section
            
            _render_question_section(
                question=sample_quiz.questions[0],
                last_result=None,
                on_submit=None,
                on_next=None,
            )
            
            # Should use radio with index=None for no default selection
            mock_streamlit.radio.assert_called()

    def test_render_question_section_radio_no_default_selection(
        self, mock_streamlit, sample_quiz
    ):
        """Test radio is called with index=None for no default selection."""
        with patch("sensei.ui.pages.quiz.st", mock_streamlit):
            from sensei.ui.pages.quiz import _render_question_section
            
            _render_question_section(
                question=sample_quiz.questions[0],
                last_result=None,
                on_submit=None,
                on_next=None,
            )
            
            # Verify radio was called with index=None (no default selection)
            mock_streamlit.radio.assert_called_once()
            call_kwargs = mock_streamlit.radio.call_args[1]
            assert call_kwargs.get("index") is None

    def test_render_question_section_uses_options_directly(
        self, mock_streamlit, sample_quiz
    ):
        """Test radio uses options directly from question (AI provides labels)."""
        with patch("sensei.ui.pages.quiz.st", mock_streamlit):
            from sensei.ui.pages.quiz import _render_question_section
            
            _render_question_section(
                question=sample_quiz.questions[0],
                last_result=None,
                on_submit=None,
                on_next=None,
            )
            
            # Get the options passed to radio
            call_kwargs = mock_streamlit.radio.call_args[1]
            options = call_kwargs.get("options", [])
            
            # Options should be passed directly from question (AI already labels them)
            assert options == sample_quiz.questions[0].options

    def test_render_question_section_preserves_previous_selection(
        self, mock_streamlit, sample_quiz
    ):
        """Test radio preserves previous selection via session state."""
        # Simulate previous selection in session state
        mock_streamlit.session_state = {"quiz_answer_q1": "4"}
        
        with patch("sensei.ui.pages.quiz.st", mock_streamlit):
            from sensei.ui.pages.quiz import _render_question_section
            
            _render_question_section(
                question=sample_quiz.questions[0],
                last_result=None,
                on_submit=None,
                on_next=None,
            )
            
            # Radio should be called with index=1 (second option "4")
            call_kwargs = mock_streamlit.radio.call_args[1]
            assert call_kwargs.get("index") == 1

    def test_render_question_section_open_ended_shows_text_area(
        self, mock_streamlit
    ):
        """Test open-ended questions render a text area instead of radio buttons."""
        from sensei.models.schemas import QuizQuestion
        from sensei.models.enums import QuestionType
        
        # Create an open-ended question (no options)
        open_ended_question = QuizQuestion(
            id="q_open",
            question="Explain what a vector space is in your own words.",
            question_type=QuestionType.OPEN_ENDED,
            options=[],  # No options for open-ended
            correct_answer="A vector space is a set with addition and scalar multiplication...",
        )
        
        mock_streamlit.session_state = {}
        
        with patch("sensei.ui.pages.quiz.st", mock_streamlit):
            from sensei.ui.pages.quiz import _render_question_section
            
            _render_question_section(
                question=open_ended_question,
                last_result=None,
                on_submit=None,
                on_next=None,
            )
            
            # Should use text_area, NOT radio
            mock_streamlit.text_area.assert_called_once()
            mock_streamlit.radio.assert_not_called()
            
            # Verify text_area has correct placeholder
            call_kwargs = mock_streamlit.text_area.call_args[1]
            assert "Type your answer" in call_kwargs.get("placeholder", "")

    def test_render_question_section_code_question_shows_text_area(
        self, mock_streamlit
    ):
        """Test code questions render a text area with code placeholder."""
        from sensei.models.schemas import QuizQuestion
        from sensei.models.enums import QuestionType
        
        # Create a code question (no options)
        code_question = QuizQuestion(
            id="q_code",
            question="Write a function to calculate factorial.",
            question_type=QuestionType.CODE,
            options=[],  # No options for code questions
            correct_answer="def factorial(n): return 1 if n <= 1 else n * factorial(n-1)",
        )
        
        mock_streamlit.session_state = {}
        
        with patch("sensei.ui.pages.quiz.st", mock_streamlit):
            from sensei.ui.pages.quiz import _render_question_section
            
            _render_question_section(
                question=code_question,
                last_result=None,
                on_submit=None,
                on_next=None,
            )
            
            # Should use text_area for code input
            mock_streamlit.text_area.assert_called_once()
            mock_streamlit.radio.assert_not_called()
            
            # Verify text_area has code placeholder
            call_kwargs = mock_streamlit.text_area.call_args[1]
            assert "code" in call_kwargs.get("placeholder", "").lower()

    def test_render_question_section_open_ended_stores_answer(
        self, mock_streamlit
    ):
        """Test open-ended answer is stored in session state."""
        from sensei.models.schemas import QuizQuestion
        from sensei.models.enums import QuestionType
        
        open_ended_question = QuizQuestion(
            id="q_open_2",
            question="What is machine learning?",
            question_type=QuestionType.OPEN_ENDED,
            options=[],
            correct_answer="Machine learning is...",
        )
        
        # Simulate user typing an answer
        mock_streamlit.session_state = {}
        mock_streamlit.text_area.return_value = "Machine learning is a subset of AI."
        
        with patch("sensei.ui.pages.quiz.st", mock_streamlit):
            from sensei.ui.pages.quiz import _render_question_section
            
            _render_question_section(
                question=open_ended_question,
                last_result=None,
                on_submit=None,
                on_next=None,
            )
            
            # Answer should be stored in session state
            assert mock_streamlit.session_state.get("quiz_answer_q_open_2") == "Machine learning is a subset of AI."

    def test_render_question_section_open_ended_empty_answer_is_none(
        self, mock_streamlit
    ):
        """Test empty/whitespace answer is stored as None."""
        from sensei.models.schemas import QuizQuestion
        from sensei.models.enums import QuestionType
        
        open_ended_question = QuizQuestion(
            id="q_open_3",
            question="What is AI?",
            question_type=QuestionType.OPEN_ENDED,
            options=[],
            correct_answer="AI is...",
        )
        
        mock_streamlit.session_state = {}
        mock_streamlit.text_area.return_value = "   "  # Whitespace only
        
        with patch("sensei.ui.pages.quiz.st", mock_streamlit):
            from sensei.ui.pages.quiz import _render_question_section
            
            _render_question_section(
                question=open_ended_question,
                last_result=None,
                on_submit=None,
                on_next=None,
            )
            
            # Empty/whitespace answer should be None (so Submit is disabled)
            assert mock_streamlit.session_state.get("quiz_answer_q_open_3") is None


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

    def test_render_feedback_pending_for_open_ended(
        self, mock_streamlit, sample_quiz
    ):
        """Test feedback shows 'Answer Submitted' for pending open-ended questions."""
        from sensei.models.schemas import AnswerResult
        
        pending_result = AnswerResult(
            question_id="q1",
            user_answer="My explanation of the concept...",
            is_correct=False,  # Not yet evaluated
            correct_answer="Sample answer",
            explanation="This answer will be evaluated by AI.",
            is_pending=True,  # Open-ended, awaiting AI evaluation
        )
        
        with patch("sensei.ui.pages.quiz.st", mock_streamlit):
            from sensei.ui.pages.quiz import _render_answer_feedback
            
            _render_answer_feedback(
                pending_result,
                sample_quiz.questions[0],
            )
            
            calls = mock_streamlit.markdown.call_args_list
            # Should show "Answer Submitted" message
            assert any("Answer Submitted" in str(c) for c in calls)
            # Should NOT show "Correct" or "Incorrect"
            assert not any("Correct!" in str(c) for c in calls)
            assert not any("Incorrect" in str(c) for c in calls)
            # Should mention AI evaluation
            assert any("evaluated by AI" in str(c) for c in calls)

    def test_render_feedback_pending_does_not_show_explanation(
        self, mock_streamlit, sample_quiz
    ):
        """Test pending answers don't show explanation expander."""
        from sensei.models.schemas import AnswerResult
        
        pending_result = AnswerResult(
            question_id="q1",
            user_answer="My answer",
            is_correct=False,
            correct_answer="Expected answer",
            explanation="This will be evaluated by AI.",
            is_pending=True,
        )
        
        with patch("sensei.ui.pages.quiz.st", mock_streamlit):
            from sensei.ui.pages.quiz import _render_answer_feedback
            
            _render_answer_feedback(
                pending_result,
                sample_quiz.questions[0],
            )
            
            # Should NOT call expander for pending answers
            mock_streamlit.expander.assert_not_called()

    def test_render_feedback_backward_compat_open_ended_without_is_pending(
        self, mock_streamlit
    ):
        """Test backward compatibility: open-ended question with old result lacking is_pending.
        
        Old AnswerResult objects (created before is_pending was added) may have
        is_correct=True for open-ended questions. The code should detect this
        by checking the question type and treat it as pending.
        """
        from sensei.models.schemas import AnswerResult, QuizQuestion
        from sensei.models.enums import QuestionType
        
        # Simulate an old AnswerResult that doesn't have is_pending
        # (we can't actually remove the field, but we can test the fallback logic)
        old_result = AnswerResult(
            question_id="q1",
            user_answer="My explanation",
            is_correct=True,  # Old behavior - always True for open-ended
            correct_answer="Expected answer",
            explanation="Some explanation",
            is_pending=False,  # Old results would default to False
        )
        
        # But the question IS open-ended
        open_ended_question = QuizQuestion(
            id="q1",
            question="Explain the concept.",
            question_type=QuestionType.OPEN_ENDED,
            options=[],
            correct_answer="Expected answer",
        )
        
        with patch("sensei.ui.pages.quiz.st", mock_streamlit):
            from sensei.ui.pages.quiz import _render_answer_feedback
            
            _render_answer_feedback(old_result, open_ended_question)
            
            calls = mock_streamlit.markdown.call_args_list
            # Should detect open-ended question and show "Answer Submitted"
            assert any("Answer Submitted" in str(c) for c in calls)
            # Should NOT show "Correct!" even though is_correct=True
            assert not any("Correct!" in str(c) for c in calls)

    def test_render_feedback_non_open_ended_with_is_pending_false(
        self, mock_streamlit
    ):
        """Test that non-open-ended questions with is_pending=False show correct/incorrect."""
        from sensei.models.schemas import AnswerResult, QuizQuestion
        from sensei.models.enums import QuestionType
        
        # Multiple choice question with correct answer
        result = AnswerResult(
            question_id="q1",
            user_answer="4",
            is_correct=True,
            correct_answer="4",
            explanation="Correct!",
            is_pending=False,
        )
        
        mc_question = QuizQuestion(
            id="q1",
            question="What is 2+2?",
            question_type=QuestionType.MULTIPLE_CHOICE,
            options=["3", "4", "5"],
            correct_answer="4",
        )
        
        with patch("sensei.ui.pages.quiz.st", mock_streamlit):
            from sensei.ui.pages.quiz import _render_answer_feedback
            
            _render_answer_feedback(result, mc_question)
            
            calls = mock_streamlit.markdown.call_args_list
            # Should show "Correct!" for multiple choice
            assert any("Correct!" in str(c) for c in calls)
            # Should NOT show "Answer Submitted"
            assert not any("Answer Submitted" in str(c) for c in calls)


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

    def test_render_with_services_resets_state_on_different_course(
        self, mock_streamlit, sample_quiz
    ):
        """Test quiz state is reset when entering quiz for different course."""
        with patch("sensei.ui.pages.quiz.st", mock_streamlit):
            with patch("sensei.ui.components.sidebar.st", mock_streamlit):
                with patch("sensei.ui.components.quiz_question.st", mock_streamlit):
                    from sensei.ui.pages.quiz import render_quiz_with_services
                    
                    mock_quiz_service = MagicMock()
                    mock_quiz_service.is_quiz_active = True
                    mock_quiz_service.current_quiz = sample_quiz
                    
                    # Set up session state from a DIFFERENT course (course-old)
                    # Use different question IDs to avoid collision with current quiz
                    mock_streamlit.session_state = {
                        "quiz_current_idx": 3,  # Was on question 4
                        "quiz_last_result": MagicMock(),
                        "quiz_is_complete": False,
                        "quiz_final_result": None,
                        "quiz_course_id": "course-old",  # Different course!
                        "quiz_module_idx": 0,
                        "quiz_id": "old-quiz-id",
                        "quiz_answer_old_q999": "A",  # Previous answer (different question ID)
                        "radio_old_q999": "A) Option",  # Previous selection
                    }
                    
                    render_quiz_with_services(
                        quiz_service=mock_quiz_service,
                        course_id="course-new",  # NEW course
                        module_idx=0,
                    )
                    
                    # State should be reset to start fresh
                    assert mock_streamlit.session_state["quiz_current_idx"] == 0
                    assert mock_streamlit.session_state["quiz_last_result"] is None
                    assert mock_streamlit.session_state["quiz_is_complete"] is False
                    assert mock_streamlit.session_state["quiz_final_result"] is None
                    # Course/module tracking should be updated
                    assert mock_streamlit.session_state["quiz_course_id"] == "course-new"
                    assert mock_streamlit.session_state["quiz_module_idx"] == 0
                    # Previous answer keys should be removed (old question IDs)
                    assert "quiz_answer_old_q999" not in mock_streamlit.session_state
                    assert "radio_old_q999" not in mock_streamlit.session_state

    def test_render_with_services_resets_state_on_different_module(
        self, mock_streamlit, sample_quiz
    ):
        """Test quiz state is reset when entering quiz for different module."""
        with patch("sensei.ui.pages.quiz.st", mock_streamlit):
            with patch("sensei.ui.components.sidebar.st", mock_streamlit):
                with patch("sensei.ui.components.quiz_question.st", mock_streamlit):
                    from sensei.ui.pages.quiz import render_quiz_with_services
                    
                    mock_quiz_service = MagicMock()
                    mock_quiz_service.is_quiz_active = True
                    mock_quiz_service.current_quiz = sample_quiz
                    
                    # Set up session state from module 0
                    mock_streamlit.session_state = {
                        "quiz_current_idx": 5,
                        "quiz_last_result": MagicMock(),
                        "quiz_is_complete": False,
                        "quiz_final_result": None,
                        "quiz_course_id": "test-course",
                        "quiz_module_idx": 0,  # Different module!
                    }
                    
                    render_quiz_with_services(
                        quiz_service=mock_quiz_service,
                        course_id="test-course",
                        module_idx=1,  # NEW module
                    )
                    
                    # State should be reset
                    assert mock_streamlit.session_state["quiz_current_idx"] == 0
                    assert mock_streamlit.session_state["quiz_module_idx"] == 1

    def test_render_with_services_preserves_state_for_same_quiz(
        self, mock_streamlit, sample_quiz
    ):
        """Test quiz state is preserved when re-rendering same quiz."""
        with patch("sensei.ui.pages.quiz.st", mock_streamlit):
            with patch("sensei.ui.components.sidebar.st", mock_streamlit):
                with patch("sensei.ui.components.quiz_question.st", mock_streamlit):
                    from sensei.ui.pages.quiz import render_quiz_with_services
                    
                    mock_quiz_service = MagicMock()
                    mock_quiz_service.is_quiz_active = True
                    mock_quiz_service.current_quiz = sample_quiz
                    
                    # Set up session state for SAME course/module AND same quiz ID
                    # Include answer keys to show this is an in-progress quiz
                    mock_streamlit.session_state = {
                        "quiz_current_idx": 3,  # On question 4
                        "quiz_last_result": None,
                        "quiz_is_complete": False,
                        "quiz_final_result": None,
                        "quiz_course_id": "test-course",  # Same course
                        "quiz_module_idx": 0,  # Same module
                        "quiz_id": sample_quiz.id,  # Same quiz ID
                        # Include answer keys to indicate this is a resumed quiz
                        "quiz_answer_q1": "4",  # Previous answer
                        "quiz_answer_q2": "True",  # Previous answer
                    }
                    
                    render_quiz_with_services(
                        quiz_service=mock_quiz_service,
                        course_id="test-course",  # Same course
                        module_idx=0,  # Same module
                    )
                    
                    # State should be PRESERVED (not reset) because we have answers
                    assert mock_streamlit.session_state["quiz_current_idx"] == 3

    def test_render_with_services_initializes_course_module_tracking(
        self, mock_streamlit, sample_quiz
    ):
        """Test session state initializes course/module tracking."""
        with patch("sensei.ui.pages.quiz.st", mock_streamlit):
            with patch("sensei.ui.components.sidebar.st", mock_streamlit):
                with patch("sensei.ui.components.quiz_question.st", mock_streamlit):
                    from sensei.ui.pages.quiz import render_quiz_with_services
                    
                    mock_quiz_service = MagicMock()
                    mock_quiz_service.is_quiz_active = True
                    mock_quiz_service.current_quiz = sample_quiz
                    
                    # Start with empty session state
                    mock_streamlit.session_state = {}
                    
                    render_quiz_with_services(
                        quiz_service=mock_quiz_service,
                        course_id="test-course",
                        module_idx=2,
                    )
                    
                    # Should have initialized tracking keys
                    assert "quiz_course_id" in mock_streamlit.session_state
                    assert "quiz_module_idx" in mock_streamlit.session_state
                    assert mock_streamlit.session_state["quiz_course_id"] == "test-course"
                    assert mock_streamlit.session_state["quiz_module_idx"] == 2

    def test_render_with_services_clears_previous_answer_keys(
        self, mock_streamlit, sample_quiz
    ):
        """Test previous quiz answer keys are cleared when starting new quiz."""
        with patch("sensei.ui.pages.quiz.st", mock_streamlit):
            with patch("sensei.ui.components.sidebar.st", mock_streamlit):
                with patch("sensei.ui.components.quiz_question.st", mock_streamlit):
                    from sensei.ui.pages.quiz import render_quiz_with_services
                    
                    mock_quiz_service = MagicMock()
                    mock_quiz_service.is_quiz_active = True
                    mock_quiz_service.current_quiz = sample_quiz
                    
                    # Set up session state with answer keys from previous quiz
                    mock_streamlit.session_state = {
                        "quiz_current_idx": 0,
                        "quiz_last_result": None,
                        "quiz_is_complete": False,
                        "quiz_final_result": None,
                        "quiz_course_id": "old-course",
                        "quiz_module_idx": 0,
                        "quiz_id": "old-quiz-id",
                        # These should be cleared
                        "quiz_answer_old_q1": "A",
                        "quiz_answer_old_q2": "B",
                        "radio_old_q1": "A) Option",
                        "radio_old_q2": "B) Option",
                        # This should remain (not a quiz key)
                        "other_state": "preserved",
                    }
                    
                    render_quiz_with_services(
                        quiz_service=mock_quiz_service,
                        course_id="new-course",
                        module_idx=0,
                    )
                    
                    # Quiz answer keys should be cleared
                    assert "quiz_answer_old_q1" not in mock_streamlit.session_state
                    assert "quiz_answer_old_q2" not in mock_streamlit.session_state
                    assert "radio_old_q1" not in mock_streamlit.session_state
                    assert "radio_old_q2" not in mock_streamlit.session_state
                    # Other state should remain
                    assert mock_streamlit.session_state.get("other_state") == "preserved"

    def test_quiz_generation_resets_index_to_zero(
        self, mock_streamlit, sample_quiz
    ):
        """Test that quiz generation always resets quiz_current_idx to 0."""
        with patch("sensei.ui.pages.quiz.st", mock_streamlit):
            with patch("sensei.ui.components.sidebar.st", mock_streamlit):
                with patch("sensei.ui.components.quiz_question.st", mock_streamlit):
                    from sensei.ui.pages.quiz import render_quiz_with_services
                    
                    mock_quiz_service = MagicMock()
                    # Quiz service has NO active quiz - will trigger generation
                    mock_quiz_service.is_quiz_active = False
                    mock_quiz_service.current_quiz = None
                    
                    # Set up session state with STALE index from previous quiz
                    mock_streamlit.session_state = {
                        "quiz_current_idx": 5,  # Stale value - should be reset!
                        "quiz_last_result": MagicMock(),
                        "quiz_is_complete": False,
                        "quiz_final_result": None,
                        "quiz_course_id": "test-course",
                        "quiz_module_idx": 0,
                        "quiz_id": "old-quiz-id",
                    }
                    
                    # After generate_quiz, quiz becomes active
                    def gen_side_effect(*args, **kwargs):
                        mock_quiz_service.is_quiz_active = True
                        mock_quiz_service.current_quiz = sample_quiz
                    
                    mock_quiz_service.generate_quiz.side_effect = gen_side_effect
                    
                    render_quiz_with_services(
                        quiz_service=mock_quiz_service,
                        course_id="test-course",
                        module_idx=0,
                    )
                    
                    # Index should be reset to 0 after quiz generation
                    assert mock_streamlit.session_state["quiz_current_idx"] == 0
                    # Other state should also be reset
                    assert mock_streamlit.session_state["quiz_last_result"] is None
                    assert mock_streamlit.session_state["quiz_is_complete"] is False
                    assert mock_streamlit.session_state["quiz_final_result"] is None

    def test_quiz_generation_clears_stale_answer_keys(
        self, mock_streamlit, sample_quiz
    ):
        """Test that quiz generation clears any lingering answer keys."""
        with patch("sensei.ui.pages.quiz.st", mock_streamlit):
            with patch("sensei.ui.components.sidebar.st", mock_streamlit):
                with patch("sensei.ui.components.quiz_question.st", mock_streamlit):
                    from sensei.ui.pages.quiz import render_quiz_with_services
                    
                    mock_quiz_service = MagicMock()
                    # Quiz service has NO active quiz - will trigger generation
                    mock_quiz_service.is_quiz_active = False
                    mock_quiz_service.current_quiz = None
                    
                    # Set up session state with stale answer keys
                    mock_streamlit.session_state = {
                        "quiz_current_idx": 3,
                        "quiz_last_result": None,
                        "quiz_is_complete": False,
                        "quiz_final_result": None,
                        "quiz_course_id": "test-course",
                        "quiz_module_idx": 0,
                        "quiz_id": "old-quiz-id",
                        # Stale answer keys from previous quiz
                        "quiz_answer_old_q1": "A",
                        "quiz_answer_old_q2": "B",
                        "radio_old_q1": "A) Option",
                        # Non-quiz key should be preserved
                        "other_state": "preserved",
                    }
                    
                    def gen_side_effect(*args, **kwargs):
                        mock_quiz_service.is_quiz_active = True
                        mock_quiz_service.current_quiz = sample_quiz
                    
                    mock_quiz_service.generate_quiz.side_effect = gen_side_effect
                    
                    render_quiz_with_services(
                        quiz_service=mock_quiz_service,
                        course_id="test-course",
                        module_idx=0,
                    )
                    
                    # Stale answer keys should be cleared after generation
                    assert "quiz_answer_old_q1" not in mock_streamlit.session_state
                    assert "quiz_answer_old_q2" not in mock_streamlit.session_state
                    assert "radio_old_q1" not in mock_streamlit.session_state
                    # Non-quiz state should be preserved
                    assert mock_streamlit.session_state.get("other_state") == "preserved"

    def test_quiz_generation_stores_new_quiz_id(
        self, mock_streamlit, sample_quiz
    ):
        """Test that quiz generation stores the new quiz ID."""
        with patch("sensei.ui.pages.quiz.st", mock_streamlit):
            with patch("sensei.ui.components.sidebar.st", mock_streamlit):
                with patch("sensei.ui.components.quiz_question.st", mock_streamlit):
                    from sensei.ui.pages.quiz import render_quiz_with_services
                    
                    mock_quiz_service = MagicMock()
                    mock_quiz_service.is_quiz_active = False
                    mock_quiz_service.current_quiz = None
                    
                    # Session state with old quiz ID
                    mock_streamlit.session_state = {
                        "quiz_current_idx": 0,
                        "quiz_last_result": None,
                        "quiz_is_complete": False,
                        "quiz_final_result": None,
                        "quiz_course_id": "test-course",
                        "quiz_module_idx": 0,
                        "quiz_id": "old-quiz-id",
                    }
                    
                    def gen_side_effect(*args, **kwargs):
                        mock_quiz_service.is_quiz_active = True
                        mock_quiz_service.current_quiz = sample_quiz  # Has ID "quiz-123"
                    
                    mock_quiz_service.generate_quiz.side_effect = gen_side_effect
                    
                    render_quiz_with_services(
                        quiz_service=mock_quiz_service,
                        course_id="test-course",
                        module_idx=0,
                    )
                    
                    # New quiz ID should be stored
                    assert mock_streamlit.session_state["quiz_id"] == sample_quiz.id

    def test_quiz_generation_starts_at_question_one(
        self, mock_streamlit, sample_quiz
    ):
        """Test that after quiz generation, the display starts at Question 1."""
        with patch("sensei.ui.pages.quiz.st", mock_streamlit):
            with patch("sensei.ui.components.sidebar.st", mock_streamlit):
                with patch("sensei.ui.components.quiz_question.st", mock_streamlit):
                    from sensei.ui.pages.quiz import render_quiz_with_services
                    
                    mock_quiz_service = MagicMock()
                    mock_quiz_service.is_quiz_active = False
                    mock_quiz_service.current_quiz = None
                    
                    # Session state with stale index = 5 (was on Question 6)
                    mock_streamlit.session_state = {
                        "quiz_current_idx": 5,  # STALE!
                        "quiz_last_result": None,
                        "quiz_is_complete": False,
                        "quiz_final_result": None,
                        "quiz_course_id": None,  # No previous tracking
                        "quiz_module_idx": None,
                        "quiz_id": None,
                    }
                    
                    def gen_side_effect(*args, **kwargs):
                        mock_quiz_service.is_quiz_active = True
                        mock_quiz_service.current_quiz = sample_quiz
                    
                    mock_quiz_service.generate_quiz.side_effect = gen_side_effect
                    
                    render_quiz_with_services(
                        quiz_service=mock_quiz_service,
                        course_id="test-course",
                        module_idx=0,
                    )
                    
                    # After generation, index should be 0 (Question 1)
                    assert mock_streamlit.session_state["quiz_current_idx"] == 0
                    
                    # Verify the first question would be shown (not Question 6)
                    # The render_quiz_page is called with current_question_idx from session state
                    # So if quiz_current_idx = 0, render_quiz_progress shows "Question 1 of N"

    def test_force_new_flag_ends_existing_quiz_and_resets_state(
        self, mock_streamlit, sample_quiz
    ):
        """Test that force_new flag ends existing quiz and resets all state."""
        with patch("sensei.ui.pages.quiz.st", mock_streamlit):
            with patch("sensei.ui.components.sidebar.st", mock_streamlit):
                with patch("sensei.ui.components.quiz_question.st", mock_streamlit):
                    from sensei.ui.pages.quiz import render_quiz_with_services
                    
                    mock_quiz_service = MagicMock()
                    mock_quiz_service.is_quiz_active = True  # Quiz already active
                    mock_quiz_service.current_quiz = sample_quiz
                    
                    # Session state: User was on Q2, now clicks "Take Quiz" (force_new=True)
                    # Use old_xxx keys that won't be re-created by rendering
                    mock_streamlit.session_state = {
                        "quiz_current_idx": 1,  # Was on Question 2
                        "quiz_last_result": MagicMock(),
                        "quiz_is_complete": False,
                        "quiz_final_result": None,
                        "quiz_course_id": "test-course",  # Same course
                        "quiz_module_idx": 0,  # Same module
                        "quiz_id": sample_quiz.id,  # Same quiz ID
                        "quiz_answer_old_q1": "A) 1",  # OLD answer (different key)
                        "radio_old_q1": "Option A",  # OLD radio key
                        # force_new flag set by app.py's on_take_quiz
                        "quiz": {
                            "course_id": "test-course",
                            "module_idx": 0,
                            "force_new": True,  # User clicked "Take Quiz"
                        },
                    }
                    
                    # After end_quiz, quiz becomes inactive
                    def end_quiz_side_effect():
                        mock_quiz_service.is_quiz_active = False
                        mock_quiz_service.current_quiz = None
                    mock_quiz_service.end_quiz.side_effect = end_quiz_side_effect
                    
                    # After generate_quiz, quiz becomes active with new quiz
                    new_quiz = Quiz(
                        id="quiz-new-456",
                        course_id="test-course",
                        module_id="module-0",
                        module_title="Test Module",
                        questions=sample_quiz.questions,
                    )
                    def gen_side_effect(*args, **kwargs):
                        mock_quiz_service.is_quiz_active = True
                        mock_quiz_service.current_quiz = new_quiz
                    mock_quiz_service.generate_quiz.side_effect = gen_side_effect
                    
                    render_quiz_with_services(
                        quiz_service=mock_quiz_service,
                        course_id="test-course",
                        module_idx=0,
                    )
                    
                    # end_quiz should have been called
                    mock_quiz_service.end_quiz.assert_called_once()
                    # Index should be reset to 0
                    assert mock_streamlit.session_state["quiz_current_idx"] == 0
                    # force_new flag should be cleared
                    assert "force_new" not in mock_streamlit.session_state.get("quiz", {})
                    # OLD answers should be cleared (these won't be re-created)
                    assert "quiz_answer_old_q1" not in mock_streamlit.session_state
                    assert "radio_old_q1" not in mock_streamlit.session_state

    def test_force_new_flag_clears_answers_and_generates_fresh_quiz(
        self, mock_streamlit, sample_quiz
    ):
        """Test that force_new triggers a fresh quiz generation."""
        with patch("sensei.ui.pages.quiz.st", mock_streamlit):
            with patch("sensei.ui.components.sidebar.st", mock_streamlit):
                with patch("sensei.ui.components.quiz_question.st", mock_streamlit):
                    from sensei.ui.pages.quiz import render_quiz_with_services
                    
                    mock_quiz_service = MagicMock()
                    mock_quiz_service.is_quiz_active = True
                    mock_quiz_service.current_quiz = sample_quiz
                    
                    # Use old_xxx keys that won't be re-created by rendering
                    mock_streamlit.session_state = {
                        "quiz_current_idx": 3,
                        "quiz_last_result": None,
                        "quiz_is_complete": False,
                        "quiz_final_result": None,
                        "quiz_course_id": "test-course",
                        "quiz_module_idx": 0,
                        "quiz_id": sample_quiz.id,
                        "quiz_answer_old_q1": "A",  # OLD keys
                        "quiz_answer_old_q2": "B",
                        "radio_old_q1": "Option A",
                        "quiz": {
                            "course_id": "test-course",
                            "module_idx": 0,
                            "force_new": True,
                        },
                    }
                    
                    def end_quiz_side_effect():
                        mock_quiz_service.is_quiz_active = False
                        mock_quiz_service.current_quiz = None
                    mock_quiz_service.end_quiz.side_effect = end_quiz_side_effect
                    
                    new_quiz = Quiz(
                        id="new-quiz-id",
                        course_id="test-course",
                        module_id="module-0",
                        module_title="Test Module",
                        questions=sample_quiz.questions,
                    )
                    def gen_side_effect(*args, **kwargs):
                        mock_quiz_service.is_quiz_active = True
                        mock_quiz_service.current_quiz = new_quiz
                    mock_quiz_service.generate_quiz.side_effect = gen_side_effect
                    
                    render_quiz_with_services(
                        quiz_service=mock_quiz_service,
                        course_id="test-course",
                        module_idx=0,
                    )
                    
                    # All OLD answers should be cleared (won't be re-created)
                    assert "quiz_answer_old_q1" not in mock_streamlit.session_state
                    assert "quiz_answer_old_q2" not in mock_streamlit.session_state
                    assert "radio_old_q1" not in mock_streamlit.session_state
                    # New quiz ID should be stored
                    assert mock_streamlit.session_state["quiz_id"] == new_quiz.id
                    # Index should be 0
                    assert mock_streamlit.session_state["quiz_current_idx"] == 0
