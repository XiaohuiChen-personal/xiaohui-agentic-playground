"""Unit tests for quiz_question component."""

from unittest.mock import MagicMock, patch

import pytest

from sensei.models.enums import QuestionType
from sensei.models.schemas import QuizQuestion, AnswerResult, QuizResult


class TestRenderQuestion:
    """Tests for render_question function."""

    def test_render_question_multiple_choice(
        self, mock_streamlit, sample_quiz_question_mc
    ):
        """Test rendering multiple choice question."""
        # selectbox returns the labeled option string
        mock_streamlit.selectbox.return_value = "A) 3"
        
        with patch("sensei.ui.components.quiz_question.st", mock_streamlit):
            from sensei.ui.components.quiz_question import render_question
            
            result = render_question(
                question=sample_quiz_question_mc,
                question_idx=0,
                total_questions=5,
            )
            
            mock_streamlit.markdown.assert_called()
            mock_streamlit.selectbox.assert_called()
            assert result is None  # No button click

    def test_render_question_true_false(
        self, mock_streamlit, sample_quiz_question_tf
    ):
        """Test rendering true/false question."""
        # True/False now uses selectbox via _render_multiple_choice
        mock_streamlit.selectbox.return_value = "A) True"
        
        with patch("sensei.ui.components.quiz_question.st", mock_streamlit):
            from sensei.ui.components.quiz_question import render_question
            
            result = render_question(
                question=sample_quiz_question_tf,
                question_idx=1,
                total_questions=5,
            )
            
            mock_streamlit.selectbox.assert_called()
            assert result is None

    def test_render_question_from_dict(
        self, mock_streamlit, sample_quiz_question_dict
    ):
        """Test rendering question from dictionary."""
        # selectbox returns the labeled option string
        mock_streamlit.selectbox.return_value = "A) abc"
        
        with patch("sensei.ui.components.quiz_question.st", mock_streamlit):
            from sensei.ui.components.quiz_question import render_question
            
            result = render_question(
                question=sample_quiz_question_dict,
                question_idx=2,
                total_questions=5,
            )
            
            mock_streamlit.selectbox.assert_called()
            assert result is None

    def test_render_question_with_submit_callback(
        self, mock_streamlit, sample_quiz_question_mc
    ):
        """Test question with submit callback."""
        # selectbox returns the labeled option "B) 4" (second option)
        mock_streamlit.selectbox.return_value = "B) 4"
        mock_streamlit.button.return_value = True  # Submit clicked
        
        with patch("sensei.ui.components.quiz_question.st", mock_streamlit):
            from sensei.ui.components.quiz_question import render_question
            
            callback = MagicMock()
            result = render_question(
                question=sample_quiz_question_mc,
                question_idx=0,
                total_questions=5,
                on_answer=callback,
            )
            
            callback.assert_called_with("q1", "4")
            assert result == "4"

    def test_render_question_no_selection_submit_disabled(
        self, mock_streamlit, sample_quiz_question_mc
    ):
        """Test that submit is disabled when no selection."""
        mock_streamlit.selectbox.return_value = None
        
        with patch("sensei.ui.components.quiz_question.st", mock_streamlit):
            from sensei.ui.components.quiz_question import render_question
            
            render_question(
                question=sample_quiz_question_mc,
                question_idx=0,
                total_questions=5,
            )
            
            # Button should be called with disabled=True
            mock_streamlit.button.assert_called()

    def test_render_question_with_feedback(
        self, mock_streamlit, sample_quiz_question_mc, sample_answer_result_correct
    ):
        """Test rendering question with feedback."""
        mock_streamlit.selectbox.return_value = "B) 4"
        
        with patch("sensei.ui.components.quiz_question.st", mock_streamlit):
            from sensei.ui.components.quiz_question import render_question
            
            render_question(
                question=sample_quiz_question_mc,
                question_idx=0,
                total_questions=5,
                show_feedback=True,
                answer_result=sample_answer_result_correct,
            )
            
            mock_streamlit.success.assert_called()

    def test_render_question_with_incorrect_feedback(
        self, mock_streamlit, sample_quiz_question_mc, sample_answer_result_incorrect
    ):
        """Test rendering question with incorrect feedback."""
        mock_streamlit.selectbox.return_value = "C) 5"
        
        with patch("sensei.ui.components.quiz_question.st", mock_streamlit):
            from sensei.ui.components.quiz_question import render_question
            
            render_question(
                question=sample_quiz_question_mc,
                question_idx=0,
                total_questions=5,
                show_feedback=True,
                answer_result=sample_answer_result_incorrect,
            )
            
            mock_streamlit.error.assert_called()

    def test_render_question_with_selected_answer(
        self, mock_streamlit, sample_quiz_question_mc
    ):
        """Test rendering with previously selected answer."""
        mock_streamlit.selectbox.return_value = "B) 4"
        
        with patch("sensei.ui.components.quiz_question.st", mock_streamlit):
            from sensei.ui.components.quiz_question import render_question
            
            render_question(
                question=sample_quiz_question_mc,
                question_idx=0,
                total_questions=5,
                selected_answer="4",
            )
            
            mock_streamlit.selectbox.assert_called()

    def test_render_question_dict_missing_question_type(self, mock_streamlit):
        """Test question dict without question_type defaults to multiple choice."""
        question = {
            "id": "q_test",
            "question": "Test question?",
            "options": ["A", "B", "C"],
            "correct_answer": "B",
        }
        mock_streamlit.selectbox.return_value = "A) A"
        
        with patch("sensei.ui.components.quiz_question.st", mock_streamlit):
            from sensei.ui.components.quiz_question import render_question
            
            render_question(
                question=question,
                question_idx=0,
                total_questions=1,
            )
            
            mock_streamlit.selectbox.assert_called()

    def test_render_question_dict_with_enum_type(self, mock_streamlit):
        """Test question dict with QuestionType enum."""
        question = {
            "id": "q_test",
            "question": "Test?",
            "options": ["A", "B"],
            "correct_answer": "A",
            "question_type": QuestionType.MULTIPLE_CHOICE,
        }
        mock_streamlit.selectbox.return_value = "A) A"
        
        with patch("sensei.ui.components.quiz_question.st", mock_streamlit):
            from sensei.ui.components.quiz_question import render_question
            
            render_question(
                question=question,
                question_idx=0,
                total_questions=1,
            )
            
            mock_streamlit.selectbox.assert_called()


class TestRenderQuizProgress:
    """Tests for render_quiz_progress function."""

    def test_render_progress_basic(self, mock_streamlit):
        """Test basic quiz progress rendering."""
        with patch("sensei.ui.components.quiz_question.st", mock_streamlit):
            from sensei.ui.components.quiz_question import render_quiz_progress
            
            render_quiz_progress(
                current_question=2,
                total_questions=10,
            )
            
            mock_streamlit.progress.assert_called()
            mock_streamlit.markdown.assert_called()

    def test_render_progress_with_correct_count(self, mock_streamlit):
        """Test progress with correct count shown."""
        with patch("sensei.ui.components.quiz_question.st", mock_streamlit):
            from sensei.ui.components.quiz_question import render_quiz_progress
            
            render_quiz_progress(
                current_question=5,
                total_questions=10,
                correct_count=4,
            )
            
            mock_streamlit.markdown.assert_called()

    def test_render_progress_first_question(self, mock_streamlit):
        """Test progress on first question."""
        with patch("sensei.ui.components.quiz_question.st", mock_streamlit):
            from sensei.ui.components.quiz_question import render_quiz_progress
            
            render_quiz_progress(
                current_question=0,
                total_questions=10,
            )
            
            mock_streamlit.progress.assert_called()

    def test_render_progress_last_question(self, mock_streamlit):
        """Test progress on last question."""
        with patch("sensei.ui.components.quiz_question.st", mock_streamlit):
            from sensei.ui.components.quiz_question import render_quiz_progress
            
            render_quiz_progress(
                current_question=9,
                total_questions=10,
            )
            
            mock_streamlit.progress.assert_called()

    def test_render_progress_zero_total(self, mock_streamlit):
        """Test progress with zero total questions."""
        with patch("sensei.ui.components.quiz_question.st", mock_streamlit):
            from sensei.ui.components.quiz_question import render_quiz_progress
            
            render_quiz_progress(
                current_question=0,
                total_questions=0,
            )
            
            mock_streamlit.progress.assert_called()

    def test_render_progress_displays_correct_question_number(self, mock_streamlit):
        """Test that progress displays correct 1-based question number.
        
        This test catches the bug where double +1 increment was happening:
        - Component receives 0-based index
        - Component should display 1-based number (index + 1)
        """
        with patch("sensei.ui.components.quiz_question.st", mock_streamlit):
            from sensei.ui.components.quiz_question import render_quiz_progress
            
            # When current_question=0 (0-based index), should display "Question 1 of 10"
            render_quiz_progress(
                current_question=0,
                total_questions=10,
            )
            
            # Verify markdown was called with "Question 1 of 10"
            markdown_calls = [str(c) for c in mock_streamlit.markdown.call_args_list]
            assert any("Question 1 of 10" in call for call in markdown_calls), \
                f"Expected 'Question 1 of 10' but got: {markdown_calls}"

    def test_render_progress_displays_correct_last_question(self, mock_streamlit):
        """Test that last question displays correct number.
        
        When current_question=9 (0-based, last of 10), should display "Question 10 of 10".
        NOT "Question 11 of 10" which would indicate double increment.
        """
        with patch("sensei.ui.components.quiz_question.st", mock_streamlit):
            from sensei.ui.components.quiz_question import render_quiz_progress
            
            render_quiz_progress(
                current_question=9,  # 0-based index for question 10
                total_questions=10,
            )
            
            markdown_calls = [str(c) for c in mock_streamlit.markdown.call_args_list]
            assert any("Question 10 of 10" in call for call in markdown_calls), \
                f"Expected 'Question 10 of 10' but got: {markdown_calls}"
            # Ensure we DON'T have Question 11 (double increment bug)
            assert not any("Question 11" in call for call in markdown_calls), \
                "Bug: Double increment detected - showing Question 11 instead of 10"

    def test_render_progress_middle_question(self, mock_streamlit):
        """Test that middle question displays correctly."""
        with patch("sensei.ui.components.quiz_question.st", mock_streamlit):
            from sensei.ui.components.quiz_question import render_quiz_progress
            
            render_quiz_progress(
                current_question=4,  # 0-based index for question 5
                total_questions=8,
            )
            
            markdown_calls = [str(c) for c in mock_streamlit.markdown.call_args_list]
            assert any("Question 5 of 8" in call for call in markdown_calls), \
                f"Expected 'Question 5 of 8' but got: {markdown_calls}"


class TestRenderQuizResults:
    """Tests for render_quiz_results function."""

    def test_render_results_pass(self, mock_streamlit, sample_quiz_result_pass):
        """Test rendering passing quiz results."""
        with patch("sensei.ui.components.quiz_question.st", mock_streamlit):
            from sensei.ui.components.quiz_question import render_quiz_results
            
            render_quiz_results(result=sample_quiz_result_pass)
            
            mock_streamlit.markdown.assert_called()
            mock_streamlit.success.assert_called()

    def test_render_results_fail(self, mock_streamlit, sample_quiz_result_fail):
        """Test rendering failing quiz results."""
        with patch("sensei.ui.components.quiz_question.st", mock_streamlit):
            from sensei.ui.components.quiz_question import render_quiz_results
            
            render_quiz_results(result=sample_quiz_result_fail)
            
            mock_streamlit.markdown.assert_called()
            mock_streamlit.warning.assert_called()

    def test_render_results_from_dict(
        self, mock_streamlit, sample_quiz_result_dict
    ):
        """Test rendering results from dictionary."""
        with patch("sensei.ui.components.quiz_question.st", mock_streamlit):
            from sensei.ui.components.quiz_question import render_quiz_results
            
            render_quiz_results(result=sample_quiz_result_dict)
            
            mock_streamlit.markdown.assert_called()

    def test_render_results_custom_threshold(
        self, mock_streamlit, sample_quiz_result_fail
    ):
        """Test results with custom pass threshold."""
        with patch("sensei.ui.components.quiz_question.st", mock_streamlit):
            from sensei.ui.components.quiz_question import render_quiz_results
            
            # With 50% threshold, 60% should pass
            render_quiz_results(
                result=sample_quiz_result_fail,
                pass_threshold=0.5,
            )
            
            mock_streamlit.success.assert_called()

    def test_render_results_continue_callback(
        self, mock_streamlit, sample_quiz_result_pass
    ):
        """Test continue button callback."""
        # Buttons are: Review, (Retake - only if fail), Continue
        # For passing result: Review=False, Continue=True
        mock_streamlit.button.side_effect = [False, True]
        
        with patch("sensei.ui.components.quiz_question.st", mock_streamlit):
            from sensei.ui.components.quiz_question import render_quiz_results
            
            callback = MagicMock()
            render_quiz_results(
                result=sample_quiz_result_pass,
                on_continue=callback,
            )
            
            callback.assert_called_once()

    def test_render_results_review_callback(
        self, mock_streamlit, sample_quiz_result_pass
    ):
        """Test review button callback."""
        mock_streamlit.button.side_effect = [True, False, False]  # Review clicked
        
        with patch("sensei.ui.components.quiz_question.st", mock_streamlit):
            from sensei.ui.components.quiz_question import render_quiz_results
            
            callback = MagicMock()
            render_quiz_results(
                result=sample_quiz_result_pass,
                on_review=callback,
            )
            
            callback.assert_called_once()

    def test_render_results_retake_callback(
        self, mock_streamlit, sample_quiz_result_fail
    ):
        """Test retake button callback (only shown on fail)."""
        mock_streamlit.button.side_effect = [False, True, False]  # Retake clicked
        
        with patch("sensei.ui.components.quiz_question.st", mock_streamlit):
            from sensei.ui.components.quiz_question import render_quiz_results
            
            callback = MagicMock()
            render_quiz_results(
                result=sample_quiz_result_fail,
                on_retake=callback,
            )
            
            callback.assert_called_once()

    def test_render_results_with_weak_concepts(
        self, mock_streamlit, sample_quiz_result_fail
    ):
        """Test results display weak concepts."""
        with patch("sensei.ui.components.quiz_question.st", mock_streamlit):
            from sensei.ui.components.quiz_question import render_quiz_results
            
            render_quiz_results(result=sample_quiz_result_fail)
            
            mock_streamlit.markdown.assert_called()

    def test_render_results_no_weak_concepts(self, mock_streamlit):
        """Test results without weak concepts."""
        result = QuizResult(
            quiz_id="q1",
            score=0.9,
            correct_count=9,
            total_questions=10,
            weak_concepts=[],
            feedback="Great!",
        )
        
        with patch("sensei.ui.components.quiz_question.st", mock_streamlit):
            from sensei.ui.components.quiz_question import render_quiz_results
            
            render_quiz_results(result=result)
            
            mock_streamlit.success.assert_called()

    def test_render_results_no_feedback(self, mock_streamlit):
        """Test results without feedback."""
        result = QuizResult(
            quiz_id="q1",
            score=0.85,
            correct_count=17,
            total_questions=20,
            weak_concepts=[],
            feedback="",
        )
        
        with patch("sensei.ui.components.quiz_question.st", mock_streamlit):
            from sensei.ui.components.quiz_question import render_quiz_results
            
            render_quiz_results(result=result)
            
            mock_streamlit.markdown.assert_called()


class TestRenderQuestionReview:
    """Tests for render_question_review function."""

    def test_render_review_correct(self, mock_streamlit, sample_quiz_question_mc):
        """Test rendering correct answer in review mode."""
        with patch("sensei.ui.components.quiz_question.st", mock_streamlit):
            from sensei.ui.components.quiz_question import render_question_review
            
            render_question_review(
                question=sample_quiz_question_mc,
                user_answer="4",
                is_correct=True,
            )
            
            mock_streamlit.markdown.assert_called()

    def test_render_review_incorrect(self, mock_streamlit, sample_quiz_question_mc):
        """Test rendering incorrect answer in review mode."""
        with patch("sensei.ui.components.quiz_question.st", mock_streamlit):
            from sensei.ui.components.quiz_question import render_question_review
            
            render_question_review(
                question=sample_quiz_question_mc,
                user_answer="5",
                is_correct=False,
            )
            
            mock_streamlit.markdown.assert_called()

    def test_render_review_from_dict(
        self, mock_streamlit, sample_quiz_question_dict
    ):
        """Test review rendering from dict."""
        with patch("sensei.ui.components.quiz_question.st", mock_streamlit):
            from sensei.ui.components.quiz_question import render_question_review
            
            render_question_review(
                question=sample_quiz_question_dict,
                user_answer="def",
                is_correct=True,
            )
            
            mock_streamlit.markdown.assert_called()

    def test_render_review_with_explanation(
        self, mock_streamlit, sample_quiz_question_mc
    ):
        """Test review shows explanation."""
        with patch("sensei.ui.components.quiz_question.st", mock_streamlit):
            from sensei.ui.components.quiz_question import render_question_review
            
            render_question_review(
                question=sample_quiz_question_mc,
                user_answer="4",
                is_correct=True,
            )
            
            mock_streamlit.info.assert_called()

    def test_render_review_no_explanation(self, mock_streamlit):
        """Test review without explanation."""
        question = QuizQuestion(
            id="q1",
            question="Test?",
            options=["A", "B"],
            correct_answer="A",
            explanation="",
        )
        
        with patch("sensei.ui.components.quiz_question.st", mock_streamlit):
            from sensei.ui.components.quiz_question import render_question_review
            
            render_question_review(
                question=question,
                user_answer="A",
                is_correct=True,
            )
            
            mock_streamlit.markdown.assert_called()


class TestRenderProgress:
    """Tests for _render_progress private function."""

    def test_render_progress_first(self, mock_streamlit):
        """Test progress on first question."""
        with patch("sensei.ui.components.quiz_question.st", mock_streamlit):
            from sensei.ui.components.quiz_question import _render_progress
            
            _render_progress(0, 5)
            
            mock_streamlit.markdown.assert_called()

    def test_render_progress_middle(self, mock_streamlit):
        """Test progress in middle."""
        with patch("sensei.ui.components.quiz_question.st", mock_streamlit):
            from sensei.ui.components.quiz_question import _render_progress
            
            _render_progress(2, 5)
            
            mock_streamlit.markdown.assert_called()

    def test_render_progress_last(self, mock_streamlit):
        """Test progress on last question."""
        with patch("sensei.ui.components.quiz_question.st", mock_streamlit):
            from sensei.ui.components.quiz_question import _render_progress
            
            _render_progress(4, 5)
            
            mock_streamlit.markdown.assert_called()


class TestRenderMultipleChoice:
    """Tests for _render_multiple_choice private function."""

    def test_render_mc_basic(self, mock_streamlit):
        """Test basic multiple choice rendering."""
        # selectbox returns the labeled option string
        mock_streamlit.selectbox.return_value = "A) A"
        
        with patch("sensei.ui.components.quiz_question.st", mock_streamlit):
            from sensei.ui.components.quiz_question import _render_multiple_choice
            
            result = _render_multiple_choice(
                question_id="q1",
                options=["A", "B", "C"],
            )
            
            mock_streamlit.selectbox.assert_called()
            assert result == "A"

    def test_render_mc_with_selected(self, mock_streamlit):
        """Test multiple choice with pre-selected answer."""
        mock_streamlit.selectbox.return_value = "B) B"
        
        with patch("sensei.ui.components.quiz_question.st", mock_streamlit):
            from sensei.ui.components.quiz_question import _render_multiple_choice
            
            result = _render_multiple_choice(
                question_id="q1",
                options=["A", "B", "C"],
                selected="B",
            )
            
            assert result == "B"

    def test_render_mc_with_feedback(self, mock_streamlit, sample_answer_result_correct):
        """Test multiple choice with feedback displayed."""
        mock_streamlit.selectbox.return_value = "B) 4"
        
        with patch("sensei.ui.components.quiz_question.st", mock_streamlit):
            from sensei.ui.components.quiz_question import _render_multiple_choice
            
            _render_multiple_choice(
                question_id="q1",
                options=["3", "4", "5"],
                show_feedback=True,
                answer_result=sample_answer_result_correct,
            )
            
            mock_streamlit.success.assert_called()

    def test_render_mc_with_incorrect_feedback(
        self, mock_streamlit, sample_answer_result_incorrect
    ):
        """Test multiple choice with incorrect feedback."""
        mock_streamlit.selectbox.return_value = "C) 5"  # Selected "5"
        
        with patch("sensei.ui.components.quiz_question.st", mock_streamlit):
            from sensei.ui.components.quiz_question import _render_multiple_choice
            
            _render_multiple_choice(
                question_id="q1",
                options=["3", "4", "5"],
                selected="5",
                show_feedback=True,
                answer_result=sample_answer_result_incorrect,
            )
            
            mock_streamlit.error.assert_called()

    def test_render_mc_invalid_selected(self, mock_streamlit):
        """Test multiple choice with invalid selected option."""
        mock_streamlit.selectbox.return_value = "A) A"
        
        with patch("sensei.ui.components.quiz_question.st", mock_streamlit):
            from sensei.ui.components.quiz_question import _render_multiple_choice
            
            result = _render_multiple_choice(
                question_id="q1",
                options=["A", "B"],
                selected="Z",  # Not in options
            )
            
            # Should not raise error
            assert result == "A"

    def test_render_mc_no_selection(self, mock_streamlit):
        """Test multiple choice with no selection (None)."""
        mock_streamlit.selectbox.return_value = None
        
        with patch("sensei.ui.components.quiz_question.st", mock_streamlit):
            from sensei.ui.components.quiz_question import _render_multiple_choice
            
            result = _render_multiple_choice(
                question_id="q1",
                options=["A", "B"],
            )
            
            assert result is None

    def test_render_mc_no_default_selection(self, mock_streamlit):
        """Test that selectbox is called with index=None when no selection provided."""
        mock_streamlit.selectbox.return_value = None
        
        with patch("sensei.ui.components.quiz_question.st", mock_streamlit):
            from sensei.ui.components.quiz_question import _render_multiple_choice
            
            _render_multiple_choice(
                question_id="q1",
                options=["A", "B", "C"],
                selected=None,  # Explicitly no selection
            )
            
            # Verify selectbox was called with index=None (no default selection)
            mock_streamlit.selectbox.assert_called_once()
            call_kwargs = mock_streamlit.selectbox.call_args[1]
            assert call_kwargs.get("index") is None


class TestRenderTrueFalse:
    """Tests for _render_true_false private function."""

    def test_render_tf_basic(self, mock_streamlit):
        """Test basic true/false rendering."""
        # True/False now uses selectbox via _render_multiple_choice
        mock_streamlit.selectbox.return_value = "A) True"
        
        with patch("sensei.ui.components.quiz_question.st", mock_streamlit):
            from sensei.ui.components.quiz_question import _render_true_false
            
            result = _render_true_false(question_id="q1")
            
            mock_streamlit.selectbox.assert_called()
            assert result == "True"

    def test_render_tf_false_selected(self, mock_streamlit):
        """Test true/false with False selected."""
        mock_streamlit.selectbox.return_value = "B) False"
        
        with patch("sensei.ui.components.quiz_question.st", mock_streamlit):
            from sensei.ui.components.quiz_question import _render_true_false
            
            result = _render_true_false(question_id="q1")
            
            assert result == "False"


class TestRenderFeedback:
    """Tests for _render_feedback private function."""

    def test_render_feedback_correct(
        self, mock_streamlit, sample_answer_result_correct
    ):
        """Test rendering correct answer feedback."""
        with patch("sensei.ui.components.quiz_question.st", mock_streamlit):
            from sensei.ui.components.quiz_question import _render_feedback
            
            _render_feedback(sample_answer_result_correct)
            
            mock_streamlit.success.assert_called()

    def test_render_feedback_incorrect(
        self, mock_streamlit, sample_answer_result_incorrect
    ):
        """Test rendering incorrect answer feedback."""
        with patch("sensei.ui.components.quiz_question.st", mock_streamlit):
            from sensei.ui.components.quiz_question import _render_feedback
            
            _render_feedback(sample_answer_result_incorrect)
            
            mock_streamlit.error.assert_called()

    def test_render_feedback_with_explanation(
        self, mock_streamlit, sample_answer_result_correct
    ):
        """Test feedback with explanation parameter."""
        with patch("sensei.ui.components.quiz_question.st", mock_streamlit):
            from sensei.ui.components.quiz_question import _render_feedback
            
            _render_feedback(
                sample_answer_result_correct,
                explanation="Custom explanation",
            )
            
            mock_streamlit.info.assert_called()

    def test_render_feedback_uses_result_explanation(
        self, mock_streamlit, sample_answer_result_correct
    ):
        """Test feedback uses result's explanation when no explicit one."""
        with patch("sensei.ui.components.quiz_question.st", mock_streamlit):
            from sensei.ui.components.quiz_question import _render_feedback
            
            _render_feedback(sample_answer_result_correct, explanation="")
            
            mock_streamlit.info.assert_called()


class TestRenderQuizHeader:
    """Tests for render_quiz_header function."""

    def test_render_quiz_header(self, mock_streamlit):
        """Test quiz header rendering."""
        with patch("sensei.ui.components.quiz_question.st", mock_streamlit):
            from sensei.ui.components.quiz_question import render_quiz_header
            
            render_quiz_header(
                module_title="Variables",
                question_count=10,
            )
            
            mock_streamlit.markdown.assert_called()


class TestRenderQuizIntro:
    """Tests for render_quiz_intro function."""

    def test_render_quiz_intro_basic(self, mock_streamlit):
        """Test quiz intro rendering."""
        with patch("sensei.ui.components.quiz_question.st", mock_streamlit):
            from sensei.ui.components.quiz_question import render_quiz_intro
            
            render_quiz_intro(
                module_title="Variables",
                question_count=10,
            )
            
            mock_streamlit.markdown.assert_called()
            mock_streamlit.metric.assert_called()

    def test_render_quiz_intro_custom_time(self, mock_streamlit):
        """Test quiz intro with custom estimated time."""
        with patch("sensei.ui.components.quiz_question.st", mock_streamlit):
            from sensei.ui.components.quiz_question import render_quiz_intro
            
            render_quiz_intro(
                module_title="Variables",
                question_count=20,
                estimated_time=10,
            )
            
            mock_streamlit.metric.assert_called()

    def test_render_quiz_intro_start_callback(self, mock_streamlit):
        """Test quiz intro start button callback."""
        mock_streamlit.button.return_value = True
        
        with patch("sensei.ui.components.quiz_question.st", mock_streamlit):
            from sensei.ui.components.quiz_question import render_quiz_intro
            
            callback = MagicMock()
            render_quiz_intro(
                module_title="Variables",
                question_count=10,
                on_start=callback,
            )
            
            callback.assert_called_once()

    def test_render_quiz_intro_no_callback(self, mock_streamlit):
        """Test quiz intro without start callback."""
        mock_streamlit.button.return_value = True
        
        with patch("sensei.ui.components.quiz_question.st", mock_streamlit):
            from sensei.ui.components.quiz_question import render_quiz_intro
            
            # Should not raise error
            render_quiz_intro(
                module_title="Variables",
                question_count=10,
                on_start=None,
            )
