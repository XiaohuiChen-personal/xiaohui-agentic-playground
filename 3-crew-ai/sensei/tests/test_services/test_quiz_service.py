"""Unit tests for QuizService."""

import pytest
from datetime import datetime

from sensei.models.schemas import AnswerResult, Quiz, QuizQuestion, QuizResult
from sensei.services.course_service import CourseService
from sensei.services.quiz_service import QuizService
from sensei.utils.constants import QUIZ_PASS_THRESHOLD


@pytest.fixture
def course_with_quiz_service(mock_file_storage_paths, mock_database):
    """Create a course and return both course and quiz service."""
    course_service = CourseService(database=mock_database)
    course = course_service.create_course("Test Topic")
    quiz_service = QuizService(database=mock_database)
    return course, quiz_service, mock_database


class TestQuizServiceGenerateQuiz:
    """Tests for QuizService.generate_quiz()."""
    
    def test_generate_quiz_returns_quiz_object(
        self, course_with_quiz_service
    ):
        """Should return a Quiz object."""
        course, service, _ = course_with_quiz_service
        quiz = service.generate_quiz(course.id, 0)
        
        assert isinstance(quiz, Quiz)
    
    def test_generate_quiz_has_questions(
        self, course_with_quiz_service
    ):
        """Should have quiz questions."""
        course, service, _ = course_with_quiz_service
        quiz = service.generate_quiz(course.id, 0)
        
        assert len(quiz.questions) > 0
        assert all(isinstance(q, QuizQuestion) for q in quiz.questions)
    
    def test_generate_quiz_respects_num_questions(
        self, course_with_quiz_service
    ):
        """Should generate specified number of questions."""
        course, service, _ = course_with_quiz_service
        quiz = service.generate_quiz(course.id, 0, num_questions=3)
        
        # May have fewer if module has fewer concepts
        assert len(quiz.questions) <= 3 + 1  # +1 for possible T/F question
    
    def test_generate_quiz_sets_module_info(
        self, course_with_quiz_service
    ):
        """Should set module ID and title."""
        course, service, _ = course_with_quiz_service
        quiz = service.generate_quiz(course.id, 0)
        
        assert quiz.module_id != ""
        assert quiz.module_title != ""
    
    def test_generate_quiz_raises_for_unknown_course(
        self, mock_file_storage_paths, mock_database
    ):
        """Should raise ValueError for unknown course."""
        service = QuizService(database=mock_database)
        
        with pytest.raises(ValueError, match="Course not found"):
            service.generate_quiz("nonexistent", 0)
    
    def test_generate_quiz_raises_for_invalid_module_idx(
        self, course_with_quiz_service
    ):
        """Should raise ValueError for invalid module index."""
        course, service, _ = course_with_quiz_service
        
        with pytest.raises(ValueError, match="Module index out of range"):
            service.generate_quiz(course.id, 100)
    
    def test_generate_quiz_sets_active_state(
        self, course_with_quiz_service
    ):
        """Should set is_quiz_active to True."""
        course, service, _ = course_with_quiz_service
        
        assert service.is_quiz_active is False
        
        service.generate_quiz(course.id, 0)
        
        assert service.is_quiz_active is True


class TestQuizServiceSubmitAnswer:
    """Tests for QuizService.submit_answer()."""
    
    def test_submit_answer_returns_answer_result(
        self, course_with_quiz_service
    ):
        """Should return an AnswerResult object."""
        course, service, _ = course_with_quiz_service
        quiz = service.generate_quiz(course.id, 0)
        
        question = quiz.questions[0]
        result = service.submit_answer(question.id, "some answer")
        
        assert isinstance(result, AnswerResult)
    
    def test_submit_answer_correct_answer(
        self, course_with_quiz_service
    ):
        """Should mark correct answer as correct."""
        course, service, _ = course_with_quiz_service
        quiz = service.generate_quiz(course.id, 0)
        
        question = quiz.questions[0]
        result = service.submit_answer(question.id, question.correct_answer)
        
        assert result.is_correct is True
    
    def test_submit_answer_incorrect_answer(
        self, course_with_quiz_service
    ):
        """Should mark incorrect answer as incorrect."""
        course, service, _ = course_with_quiz_service
        quiz = service.generate_quiz(course.id, 0)
        
        question = quiz.questions[0]
        result = service.submit_answer(question.id, "wrong answer")
        
        assert result.is_correct is False
    
    def test_submit_answer_includes_correct_answer(
        self, course_with_quiz_service
    ):
        """Should include correct answer in result."""
        course, service, _ = course_with_quiz_service
        quiz = service.generate_quiz(course.id, 0)
        
        question = quiz.questions[0]
        result = service.submit_answer(question.id, "any answer")
        
        assert result.correct_answer == question.correct_answer
    
    def test_submit_answer_includes_explanation(
        self, course_with_quiz_service
    ):
        """Should include explanation in result."""
        course, service, _ = course_with_quiz_service
        quiz = service.generate_quiz(course.id, 0)
        
        question = quiz.questions[0]
        result = service.submit_answer(question.id, "any answer")
        
        assert result.explanation == question.explanation
    
    def test_submit_answer_raises_without_quiz(
        self, mock_file_storage_paths, mock_database
    ):
        """Should raise RuntimeError without active quiz."""
        service = QuizService(database=mock_database)
        
        with pytest.raises(RuntimeError, match="No active quiz"):
            service.submit_answer("q-1", "answer")
    
    def test_submit_answer_raises_for_unknown_question(
        self, course_with_quiz_service
    ):
        """Should raise ValueError for unknown question ID."""
        course, service, _ = course_with_quiz_service
        service.generate_quiz(course.id, 0)
        
        with pytest.raises(ValueError, match="Question not found"):
            service.submit_answer("nonexistent-question", "answer")
    
    def test_submit_answer_raises_for_empty_answer(
        self, course_with_quiz_service
    ):
        """Should raise ValueError for empty answer."""
        course, service, _ = course_with_quiz_service
        quiz = service.generate_quiz(course.id, 0)
        
        with pytest.raises(ValueError, match="Answer cannot be empty"):
            service.submit_answer(quiz.questions[0].id, "")
    
    def test_submit_answer_raises_for_whitespace_only_answer(
        self, course_with_quiz_service
    ):
        """Should raise ValueError for whitespace-only answer."""
        course, service, _ = course_with_quiz_service
        quiz = service.generate_quiz(course.id, 0)
        
        with pytest.raises(ValueError, match="Answer cannot be empty"):
            service.submit_answer(quiz.questions[0].id, "   ")
    
    def test_submit_answer_raises_for_duplicate_submission(
        self, course_with_quiz_service
    ):
        """Should raise ValueError when answering same question twice."""
        course, service, _ = course_with_quiz_service
        quiz = service.generate_quiz(course.id, 0)
        
        question = quiz.questions[0]
        # First submission should succeed
        service.submit_answer(question.id, "first answer")
        
        # Second submission should raise
        with pytest.raises(ValueError, match="Question already answered"):
            service.submit_answer(question.id, "second answer")


class TestQuizServiceGetResults:
    """Tests for QuizService.get_results()."""
    
    def test_get_results_returns_quiz_result(
        self, course_with_quiz_service
    ):
        """Should return a QuizResult object."""
        course, service, _ = course_with_quiz_service
        quiz = service.generate_quiz(course.id, 0)
        
        # Answer all questions
        for q in quiz.questions:
            service.submit_answer(q.id, q.correct_answer)
        
        result = service.get_results()
        
        assert isinstance(result, QuizResult)
    
    def test_get_results_calculates_score(
        self, course_with_quiz_service
    ):
        """Should calculate score correctly."""
        course, service, _ = course_with_quiz_service
        quiz = service.generate_quiz(course.id, 0)
        
        # Answer all correctly
        for q in quiz.questions:
            service.submit_answer(q.id, q.correct_answer)
        
        result = service.get_results()
        
        assert result.score == 1.0
        assert result.correct_count == len(quiz.questions)
    
    def test_get_results_calculates_partial_score(
        self, course_with_quiz_service
    ):
        """Should calculate partial score correctly."""
        course, service, _ = course_with_quiz_service
        quiz = service.generate_quiz(course.id, 0)
        
        if len(quiz.questions) < 2:
            pytest.skip("Need at least 2 questions for this test")
        
        # Answer first one correctly, rest incorrectly
        for i, q in enumerate(quiz.questions):
            answer = q.correct_answer if i == 0 else "wrong"
            service.submit_answer(q.id, answer)
        
        result = service.get_results()
        
        expected_score = 1 / len(quiz.questions)
        assert result.score == pytest.approx(expected_score, rel=0.01)
    
    def test_get_results_sets_passed_flag(
        self, course_with_quiz_service
    ):
        """Should set passed flag based on threshold."""
        course, service, _ = course_with_quiz_service
        quiz = service.generate_quiz(course.id, 0)
        
        # Answer all correctly (should pass)
        for q in quiz.questions:
            service.submit_answer(q.id, q.correct_answer)
        
        result = service.get_results()
        
        assert result.passed is True
    
    def test_get_results_identifies_weak_concepts(
        self, course_with_quiz_service
    ):
        """Should identify weak concepts from wrong answers."""
        course, service, _ = course_with_quiz_service
        quiz = service.generate_quiz(course.id, 0)
        
        # Answer all incorrectly
        for q in quiz.questions:
            service.submit_answer(q.id, "wrong answer")
        
        result = service.get_results()
        
        # Should have weak concepts from incorrect answers
        assert len(result.weak_concepts) > 0 or all(
            not q.concept_id for q in quiz.questions
        )
    
    def test_get_results_generates_feedback(
        self, course_with_quiz_service
    ):
        """Should generate feedback string."""
        course, service, _ = course_with_quiz_service
        quiz = service.generate_quiz(course.id, 0)
        
        for q in quiz.questions:
            service.submit_answer(q.id, q.correct_answer)
        
        result = service.get_results()
        
        assert result.feedback != ""
        assert len(result.feedback) > 20
    
    def test_get_results_saves_to_database(
        self, course_with_quiz_service
    ):
        """Should save result to database."""
        course, service, db = course_with_quiz_service
        quiz = service.generate_quiz(course.id, 0)
        
        for q in quiz.questions:
            service.submit_answer(q.id, q.correct_answer)
        
        service.get_results()
        
        # Check database has the result
        history = db.get_quiz_history(course.id)
        assert len(history) == 1


class TestQuizServiceIsPassed:
    """Tests for QuizService.is_passed()."""
    
    def test_is_passed_returns_true_when_passed(
        self, course_with_quiz_service
    ):
        """Should return True when score meets threshold."""
        course, service, _ = course_with_quiz_service
        quiz = service.generate_quiz(course.id, 0)
        
        # Answer all correctly
        for q in quiz.questions:
            service.submit_answer(q.id, q.correct_answer)
        
        assert service.is_passed() is True
    
    def test_is_passed_returns_false_when_failed(
        self, course_with_quiz_service
    ):
        """Should return False when score below threshold."""
        course, service, _ = course_with_quiz_service
        quiz = service.generate_quiz(course.id, 0)
        
        # Answer all incorrectly
        for q in quiz.questions:
            service.submit_answer(q.id, "wrong")
        
        assert service.is_passed() is False
    
    def test_is_passed_raises_without_quiz(
        self, mock_file_storage_paths, mock_database
    ):
        """Should raise RuntimeError without active quiz."""
        service = QuizService(database=mock_database)
        
        with pytest.raises(RuntimeError, match="No active quiz"):
            service.is_passed()


class TestQuizServiceGetWeakConcepts:
    """Tests for QuizService.get_weak_concepts()."""
    
    def test_get_weak_concepts_returns_list(
        self, course_with_quiz_service
    ):
        """Should return a list of concept IDs."""
        course, service, _ = course_with_quiz_service
        quiz = service.generate_quiz(course.id, 0)
        
        # Answer all incorrectly
        for q in quiz.questions:
            service.submit_answer(q.id, "wrong")
        
        weak = service.get_weak_concepts()
        
        assert isinstance(weak, list)
    
    def test_get_weak_concepts_empty_when_all_correct(
        self, course_with_quiz_service
    ):
        """Should return empty list when all answers correct."""
        course, service, _ = course_with_quiz_service
        quiz = service.generate_quiz(course.id, 0)
        
        for q in quiz.questions:
            service.submit_answer(q.id, q.correct_answer)
        
        weak = service.get_weak_concepts()
        
        assert weak == []


class TestQuizServiceGetCurrentProgress:
    """Tests for QuizService.get_current_progress()."""
    
    def test_get_current_progress_returns_dict(
        self, course_with_quiz_service
    ):
        """Should return progress dictionary."""
        course, service, _ = course_with_quiz_service
        service.generate_quiz(course.id, 0)
        
        progress = service.get_current_progress()
        
        assert isinstance(progress, dict)
        assert "total_questions" in progress
        assert "answered" in progress
        assert "remaining" in progress
        assert "completion_percentage" in progress
    
    def test_get_current_progress_tracks_answers(
        self, course_with_quiz_service
    ):
        """Should track number of answers submitted."""
        course, service, _ = course_with_quiz_service
        quiz = service.generate_quiz(course.id, 0)
        
        assert service.get_current_progress()["answered"] == 0
        
        service.submit_answer(quiz.questions[0].id, "answer")
        
        assert service.get_current_progress()["answered"] == 1


class TestQuizServiceResetQuiz:
    """Tests for QuizService.reset_quiz()."""
    
    def test_reset_quiz_clears_answers(
        self, course_with_quiz_service
    ):
        """Should clear submitted answers."""
        course, service, _ = course_with_quiz_service
        quiz = service.generate_quiz(course.id, 0)
        
        service.submit_answer(quiz.questions[0].id, "answer")
        assert service.get_current_progress()["answered"] == 1
        
        service.reset_quiz()
        
        assert service.get_current_progress()["answered"] == 0
    
    def test_reset_quiz_keeps_questions(
        self, course_with_quiz_service
    ):
        """Should keep the quiz questions."""
        course, service, _ = course_with_quiz_service
        quiz = service.generate_quiz(course.id, 0)
        original_count = len(quiz.questions)
        
        service.submit_answer(quiz.questions[0].id, "answer")
        service.reset_quiz()
        
        assert service.is_quiz_active is True
        assert len(service.current_quiz.questions) == original_count


class TestQuizServiceEndQuiz:
    """Tests for QuizService.end_quiz()."""
    
    def test_end_quiz_clears_state(
        self, course_with_quiz_service
    ):
        """Should clear all quiz state."""
        course, service, _ = course_with_quiz_service
        service.generate_quiz(course.id, 0)
        
        assert service.is_quiz_active is True
        
        service.end_quiz()
        
        assert service.is_quiz_active is False
        assert service.current_quiz is None


class TestQuizServiceQuestionTypes:
    """Tests for different question type handling."""
    
    def test_multiple_choice_answer_matching(
        self, course_with_quiz_service
    ):
        """Should correctly match multiple choice answers."""
        course, service, _ = course_with_quiz_service
        quiz = service.generate_quiz(course.id, 0)
        
        # Find a multiple choice question
        mc_question = None
        for q in quiz.questions:
            if q.question_type.value == "multiple_choice":
                mc_question = q
                break
        
        if mc_question is None:
            pytest.skip("No multiple choice question generated")
        
        # Correct answer should be marked correct
        result = service.submit_answer(mc_question.id, mc_question.correct_answer)
        assert result.is_correct is True
    
    def test_true_false_answer_matching(
        self, course_with_quiz_service
    ):
        """Should correctly match true/false answers."""
        course, service, _ = course_with_quiz_service
        quiz = service.generate_quiz(course.id, 0)
        
        # Find a true/false question
        tf_question = None
        for q in quiz.questions:
            if q.question_type.value == "true_false":
                tf_question = q
                break
        
        if tf_question is None:
            pytest.skip("No true/false question generated")
        
        # Correct answer should be marked correct
        result = service.submit_answer(tf_question.id, tf_question.correct_answer)
        assert result.is_correct is True


class TestQuizServiceFeedback:
    """Tests for feedback generation."""
    
    def test_feedback_excellent_score(
        self, course_with_quiz_service
    ):
        """Should generate excellent feedback for high scores."""
        course, service, _ = course_with_quiz_service
        quiz = service.generate_quiz(course.id, 0)
        
        # Answer all correctly
        for q in quiz.questions:
            service.submit_answer(q.id, q.correct_answer)
        
        result = service.get_results()
        
        assert "Excellent" in result.feedback or "100%" in result.feedback
    
    def test_feedback_failing_score(
        self, course_with_quiz_service
    ):
        """Should generate encouraging feedback for low scores."""
        course, service, _ = course_with_quiz_service
        quiz = service.generate_quiz(course.id, 0)
        
        # Answer all incorrectly
        for q in quiz.questions:
            service.submit_answer(q.id, "wrong")
        
        result = service.get_results()
        
        assert "%" in result.feedback  # Should show percentage
    
    def test_get_current_progress_raises_without_quiz(
        self, mock_file_storage_paths, mock_database
    ):
        """Should raise RuntimeError without active quiz."""
        service = QuizService(database=mock_database)
        
        with pytest.raises(RuntimeError, match="No active quiz"):
            service.get_current_progress()
    
    def test_get_weak_concepts_raises_without_quiz(
        self, mock_file_storage_paths, mock_database
    ):
        """Should raise RuntimeError without active quiz."""
        service = QuizService(database=mock_database)
        
        with pytest.raises(RuntimeError, match="No active quiz"):
            service.get_weak_concepts()
    
    def test_get_results_raises_without_quiz(
        self, mock_file_storage_paths, mock_database
    ):
        """Should raise RuntimeError without active quiz."""
        service = QuizService(database=mock_database)
        
        with pytest.raises(RuntimeError, match="No active quiz"):
            service.get_results()


class TestQuizServiceAnswerNormalization:
    """Tests for answer normalization."""
    
    def test_case_insensitive_matching(
        self, course_with_quiz_service
    ):
        """Should match answers case-insensitively."""
        course, service, _ = course_with_quiz_service
        quiz = service.generate_quiz(course.id, 0)
        
        question = quiz.questions[0]
        # Submit with different case
        result = service.submit_answer(
            question.id,
            question.correct_answer.upper()
        )
        
        assert result.is_correct is True
    
    def test_whitespace_trimming(
        self, course_with_quiz_service
    ):
        """Should trim whitespace from answers."""
        course, service, _ = course_with_quiz_service
        quiz = service.generate_quiz(course.id, 0)
        
        question = quiz.questions[0]
        # Submit with extra whitespace
        result = service.submit_answer(
            question.id,
            "  " + question.correct_answer + "  "
        )
        
        assert result.is_correct is True


class TestQuizServiceConceptMastery:
    """Tests for concept mastery tracking."""
    
    def test_unanswered_questions_not_counted_as_correct(
        self, course_with_quiz_service
    ):
        """Unanswered questions should NOT get mastery boost.
        
        This is a regression test for a bug where unanswered questions
        were incorrectly treated as correct because the logic checked
        if question_id was NOT in the wrong_answers list, rather than
        checking if it WAS in the correct_answers list.
        """
        course, service, db = course_with_quiz_service
        quiz = service.generate_quiz(course.id, 0)
        
        if len(quiz.questions) < 2:
            pytest.skip("Need at least 2 questions for this test")
        
        # Only answer the FIRST question correctly, leave others unanswered
        first_question = quiz.questions[0]
        service.submit_answer(first_question.id, first_question.correct_answer)
        
        # Get results (this triggers _update_concept_mastery)
        service.get_results()
        
        # Check mastery levels in database
        # First question (answered correctly) should have high mastery
        if first_question.concept_id:
            first_mastery = db.get_concept_mastery(course.id, first_question.concept_id)
            assert first_mastery is not None
            assert first_mastery["mastery_level"] == 0.8
        
        # Second question (unanswered) should have LOW mastery, not high
        second_question = quiz.questions[1]
        if second_question.concept_id:
            second_mastery = db.get_concept_mastery(course.id, second_question.concept_id)
            assert second_mastery is not None
            # BUG FIX: Unanswered should be 0.3, NOT 0.8
            assert second_mastery["mastery_level"] == 0.3
    
    def test_correctly_answered_gets_high_mastery(
        self, course_with_quiz_service
    ):
        """Correctly answered questions should get 0.8 mastery."""
        course, service, db = course_with_quiz_service
        quiz = service.generate_quiz(course.id, 0)
        
        # Answer first question correctly
        question = quiz.questions[0]
        service.submit_answer(question.id, question.correct_answer)
        service.get_results()
        
        if question.concept_id:
            mastery = db.get_concept_mastery(course.id, question.concept_id)
            assert mastery is not None
            assert mastery["mastery_level"] == 0.8
    
    def test_incorrectly_answered_gets_low_mastery(
        self, course_with_quiz_service
    ):
        """Incorrectly answered questions should get 0.3 mastery."""
        course, service, db = course_with_quiz_service
        quiz = service.generate_quiz(course.id, 0)
        
        # Answer first question incorrectly
        question = quiz.questions[0]
        service.submit_answer(question.id, "definitely wrong answer")
        service.get_results()
        
        if question.concept_id:
            mastery = db.get_concept_mastery(course.id, question.concept_id)
            assert mastery is not None
            assert mastery["mastery_level"] == 0.3
