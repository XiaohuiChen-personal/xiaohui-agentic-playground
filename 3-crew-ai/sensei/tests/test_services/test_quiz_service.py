"""Unit tests for QuizService."""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch

from sensei.models.enums import ExperienceLevel, LearningStyle, QuestionType
from sensei.models.schemas import (
    AnswerResult,
    Concept,
    Module,
    Quiz,
    QuizQuestion,
    QuizResult,
    UserPreferences,
)
from sensei.services.course_service import CourseService
from sensei.services.quiz_service import QuizService
from sensei.utils.constants import QUIZ_PASS_THRESHOLD


@pytest.fixture
def course_with_quiz_service(mock_file_storage_paths, mock_database):
    """Create a course and return both course and quiz service (stub mode)."""
    course_service = CourseService(database=mock_database, use_ai=False)
    course = course_service.create_course("Test Topic")
    quiz_service = QuizService(database=mock_database, use_ai=False)
    return course, quiz_service, mock_database


@pytest.fixture
def course_with_mock_crew(mock_file_storage_paths, mock_database):
    """Create a course and return quiz service with mock crew."""
    course_service = CourseService(database=mock_database, use_ai=False)
    course = course_service.create_course("Test Topic")
    
    # Create mock quiz for generate_quiz
    mock_quiz = Quiz(
        module_id="module-1",
        module_title="Test Module",
        questions=[
            QuizQuestion(
                question="AI Generated Question?",
                question_type=QuestionType.MULTIPLE_CHOICE,
                options=["A", "B", "C", "D"],
                correct_answer="A",
                explanation="AI explanation",
                concept_id="concept-1",
                difficulty=2,
            ),
        ],
    )
    
    # Create mock result for evaluate_answers
    mock_result = QuizResult(
        quiz_id="quiz-1",
        course_id=course.id,
        module_id="module-1",
        module_title="Test Module",
        score=0.8,
        correct_count=4,
        total_questions=5,
        weak_concepts=[],
        feedback="AI Generated Feedback",
        passed=True,
    )
    
    mock_crew = MagicMock()
    mock_crew.generate_quiz.return_value = mock_quiz
    mock_crew.evaluate_answers.return_value = mock_result
    
    quiz_service = QuizService(
        database=mock_database,
        assessment_crew=mock_crew,
        use_ai=True,
    )
    return course, quiz_service, mock_crew, mock_database


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


class TestQuizServiceCodeQuestions:
    """Tests for CODE question type handling."""
    
    def test_code_question_exact_match(
        self, mock_file_storage_paths, mock_database
    ):
        """Should match code answers exactly."""
        from sensei.models.enums import QuestionType
        
        service = QuizService(database=mock_database)
        
        # Create a quiz with a code question manually
        code_question = QuizQuestion(
            question="What is the output of print(1 + 1)?",
            question_type=QuestionType.CODE,
            options=[],
            correct_answer="2",
            explanation="1 + 1 equals 2",
            concept_id="test-concept",
            difficulty=2,
        )
        
        quiz = Quiz(
            module_id="test-module",
            module_title="Test Module",
            questions=[code_question],
        )
        
        # Set quiz state manually
        service._current_quiz = quiz
        service._course_id = "test-course"
        
        # Test exact match
        result = service.submit_answer(code_question.id, "2")
        assert result.is_correct is True
    
    def test_code_question_whitespace_normalization(
        self, mock_file_storage_paths, mock_database
    ):
        """Should normalize whitespace in code answers."""
        from sensei.models.enums import QuestionType
        
        service = QuizService(database=mock_database)
        
        # Create a quiz with a code question that has whitespace
        code_question = QuizQuestion(
            question="Write a for loop",
            question_type=QuestionType.CODE,
            options=[],
            correct_answer="for i in range(10): print(i)",
            explanation="Basic for loop",
            concept_id="test-concept",
            difficulty=3,
        )
        
        quiz = Quiz(
            module_id="test-module",
            module_title="Test Module",
            questions=[code_question],
        )
        
        service._current_quiz = quiz
        service._course_id = "test-course"
        
        # Submit with different whitespace (extra spaces)
        result = service.submit_answer(
            code_question.id, 
            "for   i   in   range(10):    print(i)"
        )
        assert result.is_correct is True
    
    def test_code_question_multiline_whitespace_normalization(
        self, mock_file_storage_paths, mock_database
    ):
        """Should normalize multiline code to single line for comparison."""
        from sensei.models.enums import QuestionType
        
        service = QuizService(database=mock_database)
        
        code_question = QuizQuestion(
            question="Define a function",
            question_type=QuestionType.CODE,
            options=[],
            correct_answer="def hello(): return 'hi'",
            explanation="Simple function",
            concept_id="test-concept",
            difficulty=2,
        )
        
        quiz = Quiz(
            module_id="test-module",
            module_title="Test Module",
            questions=[code_question],
        )
        
        service._current_quiz = quiz
        service._course_id = "test-course"
        
        # Submit with newlines/tabs (will be normalized to spaces)
        result = service.submit_answer(
            code_question.id,
            "def hello():\n\treturn 'hi'"
        )
        assert result.is_correct is True
    
    def test_code_question_wrong_answer(
        self, mock_file_storage_paths, mock_database
    ):
        """Should detect wrong code answers."""
        from sensei.models.enums import QuestionType
        
        service = QuizService(database=mock_database)
        
        code_question = QuizQuestion(
            question="What is 2 + 2?",
            question_type=QuestionType.CODE,
            options=[],
            correct_answer="4",
            explanation="Basic math",
            concept_id="test-concept",
            difficulty=1,
        )
        
        quiz = Quiz(
            module_id="test-module",
            module_title="Test Module",
            questions=[code_question],
        )
        
        service._current_quiz = quiz
        service._course_id = "test-course"
        
        result = service.submit_answer(code_question.id, "5")
        assert result.is_correct is False


class TestQuizServiceOpenEndedQuestions:
    """Tests for OPEN_ENDED question type handling.
    
    Open-ended questions are marked as 'pending' and deferred to AI
    evaluation (Performance Analyst) rather than immediate string matching.
    """
    
    def test_open_ended_returns_pending(
        self, mock_file_storage_paths, mock_database
    ):
        """Open-ended questions should return is_pending=True for AI evaluation.
        
        The actual evaluation of open-ended answers is deferred to the
        Performance Analyst (Assessment Crew). The answer is marked as
        pending, not immediately correct/incorrect.
        """
        from sensei.models.enums import QuestionType
        
        service = QuizService(database=mock_database)
        
        open_question = QuizQuestion(
            question="Explain the concept of recursion in your own words.",
            question_type=QuestionType.OPEN_ENDED,
            options=[],
            correct_answer="Recursion is when a function calls itself to solve smaller subproblems.",
            explanation="Recursion involves a function calling itself.",
            concept_id="test-concept",
            difficulty=3,
        )
        
        quiz = Quiz(
            module_id="test-module",
            module_title="Test Module",
            questions=[open_question],
        )
        
        service._current_quiz = quiz
        service._course_id = "test-course"
        
        # Answer should be marked as pending for AI evaluation
        result = service.submit_answer(
            open_question.id,
            "Recursion is calling yourself over and over until you reach a base case."
        )
        assert result.is_pending is True
        assert result.is_correct is False  # Not yet evaluated
        assert "evaluated by AI" in result.explanation
    
    def test_open_ended_different_wording_is_pending(
        self, mock_file_storage_paths, mock_database
    ):
        """Differently worded open-ended answers should be pending."""
        from sensei.models.enums import QuestionType
        
        service = QuizService(database=mock_database)
        
        open_question = QuizQuestion(
            question="What is polymorphism?",
            question_type=QuestionType.OPEN_ENDED,
            options=[],
            correct_answer="Polymorphism is the ability of objects to take many forms.",
            explanation="Polymorphism allows different types to be treated uniformly.",
            concept_id="test-concept",
            difficulty=4,
        )
        
        quiz = Quiz(
            module_id="test-module",
            module_title="Test Module",
            questions=[open_question],
        )
        
        service._current_quiz = quiz
        service._course_id = "test-course"
        
        # Completely different wording should be marked as pending
        result = service.submit_answer(
            open_question.id,
            "It means one interface can work with many different implementations!"
        )
        assert result.is_pending is True
        assert result.is_correct is False  # Pending AI evaluation
    
    def test_open_ended_short_answer_is_pending(
        self, mock_file_storage_paths, mock_database
    ):
        """Short open-ended answers should be marked pending for AI evaluation."""
        from sensei.models.enums import QuestionType
        
        service = QuizService(database=mock_database)
        
        open_question = QuizQuestion(
            question="Describe how garbage collection works.",
            question_type=QuestionType.OPEN_ENDED,
            options=[],
            correct_answer="Garbage collection automatically frees memory by removing unused objects.",
            explanation="GC manages memory automatically.",
            concept_id="test-concept",
            difficulty=3,
        )
        
        quiz = Quiz(
            module_id="test-module",
            module_title="Test Module",
            questions=[open_question],
        )
        
        service._current_quiz = quiz
        service._course_id = "test-course"
        
        # Even a very short answer is pending (AI will evaluate quality)
        result = service.submit_answer(
            open_question.id,
            "It cleans up memory."
        )
        assert result.is_pending is True
        assert result.is_correct is False  # Not yet evaluated by AI
    
    def test_open_ended_check_answer_returns_none(
        self, mock_file_storage_paths, mock_database
    ):
        """_check_answer should return None for open-ended questions."""
        from sensei.models.enums import QuestionType
        
        service = QuizService(database=mock_database)
        
        open_question = QuizQuestion(
            question="Explain OOP principles.",
            question_type=QuestionType.OPEN_ENDED,
            options=[],
            correct_answer="OOP has encapsulation, inheritance, polymorphism, and abstraction.",
            explanation="Four pillars of OOP.",
            concept_id="oop-concept",
            difficulty=3,
        )
        
        # _check_answer should return None (pending) for open-ended
        result = service._check_answer(open_question, "Something about classes and objects")
        assert result is None

    def test_evaluate_directly_excludes_pending_from_score(
        self, mock_file_storage_paths, mock_database
    ):
        """_evaluate_directly should exclude pending (open-ended) answers from correct count."""
        from sensei.models.enums import QuestionType
        
        service = QuizService(database=mock_database)
        
        # Create a quiz with 2 MC questions and 1 open-ended
        mc_question_1 = QuizQuestion(
            question="What is 2+2?",
            question_type=QuestionType.MULTIPLE_CHOICE,
            options=["3", "4", "5"],
            correct_answer="4",
            concept_id="test-concept-1",
        )
        
        mc_question_2 = QuizQuestion(
            question="What is 3+3?",
            question_type=QuestionType.MULTIPLE_CHOICE,
            options=["5", "6", "7"],
            correct_answer="6",
            concept_id="test-concept-2",
        )
        
        open_question = QuizQuestion(
            question="Explain addition.",
            question_type=QuestionType.OPEN_ENDED,
            options=[],
            correct_answer="Addition combines numbers.",
            concept_id="test-concept-3",
        )
        
        quiz = Quiz(
            module_id="test-module",
            module_title="Test Module",
            questions=[mc_question_1, mc_question_2, open_question],
        )
        
        service._current_quiz = quiz
        service._course_id = "test-course"
        
        # Answer both MC correctly, open-ended with anything
        service.submit_answer(mc_question_1.id, "4")  # Correct
        service.submit_answer(mc_question_2.id, "6")  # Correct
        service.submit_answer(open_question.id, "It adds stuff")  # Pending
        
        # Use _evaluate_directly
        result = service._evaluate_directly()
        
        # 2 out of 3 total, but should only count non-pending
        # 2 MC correct, 1 open-ended pending (is_correct=False, is_pending=True)
        assert result.correct_count == 2
        assert result.total_questions == 3
        # Score should be 2/3 (66.67%)
        assert result.score == pytest.approx(2/3, rel=0.01)

    def test_evaluate_directly_all_open_ended_gives_zero_score(
        self, mock_file_storage_paths, mock_database
    ):
        """When all questions are open-ended, direct evaluation gives 0% (all pending)."""
        from sensei.models.enums import QuestionType
        
        service = QuizService(database=mock_database)
        
        open_question_1 = QuizQuestion(
            question="Explain concept A.",
            question_type=QuestionType.OPEN_ENDED,
            options=[],
            correct_answer="Concept A is...",
            concept_id="test-concept-1",
        )
        
        open_question_2 = QuizQuestion(
            question="Explain concept B.",
            question_type=QuestionType.OPEN_ENDED,
            options=[],
            correct_answer="Concept B is...",
            concept_id="test-concept-2",
        )
        
        quiz = Quiz(
            module_id="test-module",
            module_title="Test Module",
            questions=[open_question_1, open_question_2],
        )
        
        service._current_quiz = quiz
        service._course_id = "test-course"
        
        # Answer both open-ended questions
        service.submit_answer(open_question_1.id, "My answer A")
        service.submit_answer(open_question_2.id, "My answer B")
        
        # Direct evaluation should give 0% since all are pending
        result = service._evaluate_directly()
        
        # Both are pending, so correct_count is 0
        assert result.correct_count == 0
        assert result.total_questions == 2
        assert result.score == 0.0


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


class TestQuizServiceGenerateQuizWithAI:
    """Tests for QuizService.generate_quiz() with AI mode."""
    
    def test_generate_quiz_uses_assessment_crew(
        self, course_with_mock_crew
    ):
        """Should use AssessmentCrew when use_ai=True."""
        course, service, mock_crew, _ = course_with_mock_crew
        quiz = service.generate_quiz(course.id, 0)
        
        # Verify crew was called
        mock_crew.generate_quiz.assert_called_once()
        assert quiz.module_title == "Test Module"
        assert len(quiz.questions) == 1
    
    def test_generate_quiz_passes_user_prefs_to_crew(
        self, course_with_mock_crew
    ):
        """Should pass user preferences to AssessmentCrew."""
        course, service, mock_crew, _ = course_with_mock_crew
        
        prefs = UserPreferences(
            name="Test User",
            learning_style=LearningStyle.VISUAL,
            experience_level=ExperienceLevel.ADVANCED,
        )
        
        service.generate_quiz(course.id, 0, user_prefs=prefs)
        
        call_args = mock_crew.generate_quiz.call_args
        assert call_args.kwargs["user_prefs"] == prefs
    
    def test_generate_quiz_passes_module_to_crew(
        self, course_with_mock_crew
    ):
        """Should pass Module object to AssessmentCrew."""
        course, service, mock_crew, _ = course_with_mock_crew
        
        service.generate_quiz(course.id, 0)
        
        call_args = mock_crew.generate_quiz.call_args
        module = call_args.kwargs["module"]
        assert isinstance(module, Module)
        assert len(module.concepts) > 0
    
    def test_generate_quiz_handles_crew_failure(
        self, course_with_mock_crew
    ):
        """Should raise RuntimeError when crew fails."""
        course, service, mock_crew, _ = course_with_mock_crew
        mock_crew.generate_quiz.side_effect = Exception("LLM API Error")
        
        with pytest.raises(RuntimeError, match="Failed to generate quiz"):
            service.generate_quiz(course.id, 0)
    
    def test_generate_quiz_lazy_initializes_crew(
        self, mock_file_storage_paths, mock_database
    ):
        """Should lazily initialize AssessmentCrew if not provided."""
        course_service = CourseService(database=mock_database, use_ai=False)
        course = course_service.create_course("Test Topic")
        
        mock_quiz = Quiz(
            module_id="module-1",
            module_title="Test Module",
            questions=[
                QuizQuestion(
                    question="Lazy AI Question?",
                    question_type=QuestionType.MULTIPLE_CHOICE,
                    options=["A", "B"],
                    correct_answer="A",
                    explanation="Explanation",
                    concept_id="concept-1",
                    difficulty=2,
                ),
            ],
        )
        
        with patch(
            "sensei.crews.assessment_crew.AssessmentCrew"
        ) as MockCrewClass:
            mock_crew_instance = MagicMock()
            mock_crew_instance.generate_quiz.return_value = mock_quiz
            MockCrewClass.return_value = mock_crew_instance
            
            service = QuizService(database=mock_database, use_ai=True)
            quiz = service.generate_quiz(course.id, 0)
            
            MockCrewClass.assert_called_once()
            assert quiz.module_title == "Test Module"


class TestQuizServiceGetResultsWithAI:
    """Tests for QuizService.get_results() with AI evaluation."""
    
    def test_get_results_uses_ai_for_open_ended(
        self, course_with_mock_crew
    ):
        """Should use AI evaluation when quiz has open-ended questions."""
        course, service, mock_crew, _ = course_with_mock_crew
        
        # Create a quiz with an open-ended question
        open_ended_quiz = Quiz(
            module_id="module-1",
            module_title="Test Module",
            questions=[
                QuizQuestion(
                    question="Explain recursion",
                    question_type=QuestionType.OPEN_ENDED,
                    options=[],
                    correct_answer="Recursion is...",
                    explanation="Explanation",
                    concept_id="concept-1",
                    difficulty=3,
                ),
            ],
        )
        mock_crew.generate_quiz.return_value = open_ended_quiz
        
        # Generate and take quiz
        service.generate_quiz(course.id, 0)
        service.submit_answer(
            open_ended_quiz.questions[0].id,
            "My explanation of recursion"
        )
        
        # Get results - should use AI
        result = service.get_results()
        
        mock_crew.evaluate_answers.assert_called_once()
        assert result.feedback == "AI Generated Feedback"
    
    def test_get_results_direct_for_non_open_ended(
        self, course_with_mock_crew
    ):
        """Should use direct evaluation for quizzes without open-ended."""
        course, service, mock_crew, _ = course_with_mock_crew
        
        # Generate quiz (which has only MC questions in our mock)
        quiz = service.generate_quiz(course.id, 0)
        
        # Answer the question
        service.submit_answer(quiz.questions[0].id, "A")
        
        # Get results - should NOT use AI (no open-ended)
        result = service.get_results()
        
        # evaluate_answers should NOT be called
        mock_crew.evaluate_answers.assert_not_called()
        assert "%" in result.feedback  # Should have stub feedback
    
    def test_get_results_handles_ai_failure(
        self, course_with_mock_crew
    ):
        """Should raise RuntimeError when AI evaluation fails."""
        course, service, mock_crew, _ = course_with_mock_crew
        
        # Create quiz with open-ended question
        open_ended_quiz = Quiz(
            module_id="module-1",
            module_title="Test Module",
            questions=[
                QuizQuestion(
                    question="Explain something",
                    question_type=QuestionType.OPEN_ENDED,
                    options=[],
                    correct_answer="Answer",
                    explanation="Explanation",
                    concept_id="concept-1",
                    difficulty=2,
                ),
            ],
        )
        mock_crew.generate_quiz.return_value = open_ended_quiz
        mock_crew.evaluate_answers.side_effect = Exception("LLM API Error")
        
        service.generate_quiz(course.id, 0)
        service.submit_answer(open_ended_quiz.questions[0].id, "My answer")
        
        with pytest.raises(RuntimeError, match="Failed to evaluate quiz"):
            service.get_results()
    
    def test_get_results_saves_ai_result_to_database(
        self, course_with_mock_crew
    ):
        """Should save AI-evaluated result to database."""
        course, service, mock_crew, db = course_with_mock_crew
        
        # Create quiz with open-ended question
        open_ended_quiz = Quiz(
            module_id="module-1",
            module_title="Test Module",
            questions=[
                QuizQuestion(
                    question="Explain",
                    question_type=QuestionType.OPEN_ENDED,
                    options=[],
                    correct_answer="Answer",
                    explanation="Explanation",
                    concept_id="concept-1",
                    difficulty=2,
                ),
            ],
        )
        mock_crew.generate_quiz.return_value = open_ended_quiz
        
        service.generate_quiz(course.id, 0)
        service.submit_answer(open_ended_quiz.questions[0].id, "My answer")
        service.get_results()
        
        # Check database
        history = db.get_quiz_history(course.id)
        assert len(history) >= 1
        latest = history[0]
        assert latest["feedback"] == "AI Generated Feedback"
