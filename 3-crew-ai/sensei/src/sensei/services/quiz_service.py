"""Quiz service for managing assessments.

This service handles quiz generation, answer submission, and result
calculation. Quiz generation uses the AssessmentCrew for AI-powered
quizzes, with stub fallbacks for testing.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sensei.models.enums import QuestionType
from sensei.models.schemas import (
    AnswerResult,
    Concept,
    Module,
    Quiz,
    QuizQuestion,
    QuizResult,
    UserPreferences,
)
from sensei.storage.database import Database
from sensei.storage.file_storage import load_course, load_user_preferences
from sensei.utils.constants import QUIZ_PASS_THRESHOLD

if TYPE_CHECKING:
    from sensei.crews.assessment_crew import AssessmentCrew


class QuizService:
    """Service for managing quiz assessments.
    
    This service handles:
    - Generating quizzes for modules (AI-powered via AssessmentCrew)
    - Processing answer submissions
    - Calculating and returning results (AI-powered evaluation)
    - Tracking weak concepts
    
    The service supports two modes:
    - AI mode (default): Uses AssessmentCrew for intelligent quizzes
    - Stub mode: Uses static templates for testing without LLM calls
    
    Example:
        ```python
        # With AI (production)
        service = QuizService()
        quiz = service.generate_quiz("course-123", 0)
        
        # Without AI (testing)
        service = QuizService(use_ai=False)
        quiz = service.generate_quiz("course-123", 0)
        ```
    """
    
    def __init__(
        self,
        database: Database | None = None,
        assessment_crew: "AssessmentCrew | None" = None,
        use_ai: bool = True,
    ):
        """Initialize the quiz service.
        
        Args:
            database: Optional Database instance.
            assessment_crew: Optional AssessmentCrew instance for AI generation.
                If not provided and use_ai=True, will be created on demand.
            use_ai: Whether to use AI for quiz generation/evaluation.
                Set to False for testing without LLM calls.
        """
        self._db = database or Database()
        self._assessment_crew = assessment_crew
        self._use_ai = use_ai
        self._current_quiz: Quiz | None = None
        self._course_id: str | None = None
        self._module_idx: int | None = None
        self._answers: dict[str, str] = {}
        self._results: list[AnswerResult] = []
    
    @property
    def is_quiz_active(self) -> bool:
        """Check if a quiz is currently in progress."""
        return self._current_quiz is not None
    
    @property
    def current_quiz(self) -> Quiz | None:
        """Get the current quiz if one is active."""
        return self._current_quiz
    
    def generate_quiz(
        self,
        course_id: str,
        module_idx: int,
        num_questions: int = 5,
        user_prefs: UserPreferences | None = None,
    ) -> Quiz:
        """Generate a quiz for a module.
        
        When use_ai=True, this uses the AssessmentCrew to generate
        targeted quiz questions. When use_ai=False, it uses
        stub content for testing.
        
        Args:
            course_id: The unique identifier for the course.
            module_idx: Zero-based index of the module.
            num_questions: Number of questions to generate (default 5).
            user_prefs: Optional user preferences for personalization.
                If not provided, will attempt to load from storage.
        
        Returns:
            Quiz object with generated questions.
        
        Raises:
            ValueError: If course or module doesn't exist.
            RuntimeError: If AI quiz generation fails (when use_ai=True).
        """
        # Load course and module
        course = load_course(course_id)
        if course is None:
            raise ValueError(f"Course not found: {course_id}")
        
        modules = course.get("modules", [])
        if module_idx < 0 or module_idx >= len(modules):
            raise ValueError(f"Module index out of range: {module_idx}")
        
        module_dict = modules[module_idx]
        
        # Generate quiz
        if self._use_ai:
            if user_prefs is None:
                prefs_dict = load_user_preferences()
                user_prefs = (
                    UserPreferences(**prefs_dict) if prefs_dict else UserPreferences()
                )
            quiz = self._generate_quiz_with_ai(
                module_dict, course_id, user_prefs, num_questions
            )
        else:
            quiz = self._generate_quiz_stub(module_dict, num_questions)
        
        # Store state
        self._current_quiz = quiz
        self._course_id = course_id
        self._module_idx = module_idx
        self._answers = {}
        self._results = []
        
        return quiz
    
    def _generate_quiz_with_ai(
        self,
        module_dict: dict[str, Any],
        course_id: str,
        user_prefs: UserPreferences,
        num_questions: int,
    ) -> Quiz:
        """Generate a quiz using the AssessmentCrew.
        
        Args:
            module_dict: Module dictionary from course data.
            course_id: The course identifier.
            user_prefs: User preferences for personalization.
            num_questions: Number of questions to generate.
        
        Returns:
            Generated Quiz object.
        
        Raises:
            RuntimeError: If quiz generation fails.
        """
        # Lazy initialization of AssessmentCrew
        if self._assessment_crew is None:
            from sensei.crews.assessment_crew import AssessmentCrew
            self._assessment_crew = AssessmentCrew()
        
        # Convert module dict to Module object
        concepts = [
            Concept(
                id=c.get("id", ""),
                title=c.get("title", ""),
                content=c.get("content", ""),
                order=c.get("order", idx),
            )
            for idx, c in enumerate(module_dict.get("concepts", []))
        ]
        
        module = Module(
            id=module_dict.get("id", ""),
            title=module_dict.get("title", ""),
            description=module_dict.get("description", ""),
            concepts=concepts,
            order=module_dict.get("order", 0),
            estimated_minutes=module_dict.get("estimated_minutes", 60),
        )
        
        # Get weak concepts from previous quiz history
        weak_concepts = self._get_weak_concepts_from_history(course_id, module.id)
        
        # Get previous attempts count for this module
        history = self._db.get_quiz_history(course_id)
        previous_attempts = sum(
            1 for h in history if h.get("module_id") == module.id
        )
        
        try:
            return self._assessment_crew.generate_quiz(
                module=module,
                weak_concepts=weak_concepts,
                user_prefs=user_prefs,
                previous_attempts=previous_attempts,
            )
        except Exception as e:
            raise RuntimeError(
                f"Failed to generate quiz for module '{module.title}': {e}"
            ) from e
    
    def _get_weak_concepts_from_history(
        self,
        course_id: str,
        module_id: str,
    ) -> list[str]:
        """Get weak concepts from previous quiz history.
        
        Args:
            course_id: The course identifier.
            module_id: The module identifier.
        
        Returns:
            List of concept IDs that need extra attention.
        """
        # Get quiz history for this course and filter by module
        all_history = self._db.get_quiz_history(course_id)
        module_history = [h for h in all_history if h.get("module_id") == module_id]
        
        weak = set()
        for result in module_history[:3]:  # Look at last 3 quizzes
            if result.get("weak_concepts"):
                for concept_id in result["weak_concepts"]:
                    weak.add(concept_id)
        
        return list(weak)
    
    def submit_answer(self, question_id: str, answer: str) -> AnswerResult:
        """Submit an answer for a quiz question.
        
        Args:
            question_id: The ID of the question being answered.
            answer: The user's answer.
        
        Returns:
            AnswerResult with correctness and feedback.
        
        Raises:
            RuntimeError: If no quiz is active.
            ValueError: If question ID is not in current quiz, answer is empty,
                or question was already answered.
        """
        if not self._current_quiz:
            raise RuntimeError("No active quiz")
        
        # Validate answer is not empty
        if not answer or not answer.strip():
            raise ValueError("Answer cannot be empty")
        
        # Find the question
        question = None
        for q in self._current_quiz.questions:
            if q.id == question_id:
                question = q
                break
        
        if question is None:
            raise ValueError(f"Question not found: {question_id}")
        
        # Check for duplicate submission
        if question_id in self._answers:
            raise ValueError(f"Question already answered: {question_id}")
        
        # Store answer
        self._answers[question_id] = answer
        
        # Check if correct (returns None for open-ended questions)
        is_correct_result = self._check_answer(question, answer)
        
        # Determine if this is a pending evaluation (open-ended)
        is_pending = is_correct_result is None
        
        # Create result
        # For pending (open-ended), is_correct defaults to False until AI evaluates
        result = AnswerResult(
            question_id=question_id,
            user_answer=answer,
            is_correct=is_correct_result if is_correct_result is not None else False,
            correct_answer=question.correct_answer,
            explanation=question.explanation if not is_pending else "This answer will be evaluated by AI.",
            is_pending=is_pending,
        )
        
        self._results.append(result)
        
        return result
    
    def get_results(
        self,
        user_prefs: UserPreferences | None = None,
    ) -> QuizResult:
        """Get final quiz results.
        
        When use_ai=True and there are open-ended questions, uses the
        AssessmentCrew Performance Analyst for intelligent evaluation.
        Otherwise, calculates score directly from submitted answers.
        
        Args:
            user_prefs: Optional user preferences for feedback personalization.
                If not provided, will attempt to load from storage.
        
        Returns:
            QuizResult with score, feedback, and recommendations.
        
        Raises:
            RuntimeError: If no quiz is active.
        """
        if not self._current_quiz or not self._course_id:
            raise RuntimeError("No active quiz")
        
        # Check if we should use AI evaluation
        # (for open-ended questions or more personalized feedback)
        has_open_ended = any(
            q.question_type == QuestionType.OPEN_ENDED
            for q in self._current_quiz.questions
        )
        
        if self._use_ai and has_open_ended:
            if user_prefs is None:
                prefs_dict = load_user_preferences()
                user_prefs = (
                    UserPreferences(**prefs_dict) if prefs_dict else UserPreferences()
                )
            result = self._evaluate_with_ai(user_prefs)
        else:
            result = self._evaluate_directly()
        
        # Save to database
        self._db.save_quiz_result({
            "course_id": self._course_id,
            "module_id": self._current_quiz.module_id,
            "module_title": self._current_quiz.module_title,
            "quiz_id": self._current_quiz.id,
            "score": result.score,
            "correct_count": result.correct_count,
            "total_questions": result.total_questions,
            "weak_concepts": result.weak_concepts,
            "feedback": result.feedback,
            "passed": result.passed,
        })
        
        # Update concept mastery
        self._update_concept_mastery(result.weak_concepts, result.score)
        
        return result
    
    def _evaluate_directly(self) -> QuizResult:
        """Evaluate quiz using direct answer comparison.
        
        Used for quizzes without open-ended questions or when
        AI evaluation is disabled.
        
        Note: This method should NOT be used when there are pending (open-ended)
        answers that need AI evaluation. Use _evaluate_with_ai() instead.
        
        Returns:
            QuizResult with calculated score and stub feedback.
        """
        if not self._current_quiz or not self._course_id:
            raise RuntimeError("No active quiz")
        
        # Calculate score (exclude pending answers from correct count)
        total = len(self._current_quiz.questions)
        correct_count = sum(
            1 for r in self._results 
            if r.is_correct and not r.is_pending
        )
        score = correct_count / total if total > 0 else 0.0
        
        # Identify weak concepts (from wrong answers)
        weak_concepts = self._identify_weak_concepts()
        
        # Determine pass/fail
        passed = score >= QUIZ_PASS_THRESHOLD
        
        # Generate feedback
        feedback = self._generate_feedback_stub(score, weak_concepts)
        
        return QuizResult(
            quiz_id=self._current_quiz.id,
            course_id=self._course_id,
            module_id=self._current_quiz.module_id,
            module_title=self._current_quiz.module_title,
            score=score,
            correct_count=correct_count,
            total_questions=total,
            weak_concepts=weak_concepts,
            feedback=feedback,
            passed=passed,
            completed_at=datetime.now(),
        )
    
    def _evaluate_with_ai(self, user_prefs: UserPreferences) -> QuizResult:
        """Evaluate quiz using the AssessmentCrew Performance Analyst.
        
        Provides more intelligent evaluation, especially for open-ended
        questions, and more personalized feedback.
        
        Args:
            user_prefs: User preferences for feedback personalization.
        
        Returns:
            QuizResult with AI-generated feedback.
        
        Raises:
            RuntimeError: If AI evaluation fails.
        """
        if not self._current_quiz or not self._course_id:
            raise RuntimeError("No active quiz")
        
        # Lazy initialization of AssessmentCrew
        if self._assessment_crew is None:
            from sensei.crews.assessment_crew import AssessmentCrew
            self._assessment_crew = AssessmentCrew()
        
        # Get previous scores for context
        all_history = self._db.get_quiz_history(self._course_id)
        module_history = [
            h for h in all_history
            if h.get("module_id") == self._current_quiz.module_id
        ]
        previous_scores = [h.get("score", 0.0) for h in module_history[:5]]
        
        try:
            return self._assessment_crew.evaluate_answers(
                quiz=self._current_quiz,
                answers=self._answers,
                user_prefs=user_prefs,
                course_id=self._course_id,
                previous_scores=previous_scores,
            )
        except Exception as e:
            raise RuntimeError(
                f"Failed to evaluate quiz: {e}"
            ) from e
    
    def is_passed(self) -> bool:
        """Check if current quiz was passed.
        
        Returns:
            True if quiz score meets threshold.
        
        Raises:
            RuntimeError: If no quiz is active.
        """
        if not self._current_quiz:
            raise RuntimeError("No active quiz")
        
        total = len(self._current_quiz.questions)
        if total == 0:
            return True
        
        correct_count = sum(1 for r in self._results if r.is_correct)
        score = correct_count / total
        
        return score >= QUIZ_PASS_THRESHOLD
    
    def get_weak_concepts(self) -> list[str]:
        """Get list of concept IDs that need review.
        
        Based on questions answered incorrectly.
        
        Returns:
            List of concept IDs.
        
        Raises:
            RuntimeError: If no quiz is active.
        """
        if not self._current_quiz:
            raise RuntimeError("No active quiz")
        
        return self._identify_weak_concepts()
    
    def get_current_progress(self) -> dict[str, Any]:
        """Get current quiz progress.
        
        Returns:
            Dictionary with progress information.
        """
        if not self._current_quiz:
            raise RuntimeError("No active quiz")
        
        total = len(self._current_quiz.questions)
        answered = len(self._answers)
        
        return {
            "total_questions": total,
            "answered": answered,
            "remaining": total - answered,
            "completion_percentage": answered / total if total > 0 else 0.0,
        }
    
    def reset_quiz(self) -> None:
        """Reset the current quiz state.
        
        Clears answers and results but keeps the quiz questions.
        """
        self._answers = {}
        self._results = []
    
    def end_quiz(self) -> None:
        """End the current quiz without saving results.
        
        Use get_results() first if you want to save results.
        """
        self._current_quiz = None
        self._course_id = None
        self._module_idx = None
        self._answers = {}
        self._results = []
    
    def _generate_quiz_stub(
        self,
        module: dict[str, Any],
        num_questions: int,
    ) -> Quiz:
        """Generate a stub quiz for testing.
        
        Creates quiz questions based on module concepts.
        
        Note: Will be replaced by AssessmentCrew in Milestone 6.
        """
        concepts = module.get("concepts", [])
        questions = []
        
        for i, concept in enumerate(concepts[:num_questions]):
            concept_title = concept.get("title", f"Concept {i+1}")
            concept_id = concept.get("id", f"concept-{i}")
            
            # Generate a multiple choice question
            question = QuizQuestion(
                question=f"Which of the following best describes '{concept_title}'?",
                question_type=QuestionType.MULTIPLE_CHOICE,
                options=[
                    f"A correct description of {concept_title}",
                    f"An incorrect description that's plausible",
                    f"Another incorrect but related concept",
                    f"A completely unrelated concept",
                ],
                correct_answer="A correct description of " + concept_title,
                explanation=f"This is the correct answer because {concept_title} refers to this specific concept.",
                concept_id=concept_id,
                difficulty=2,
            )
            questions.append(question)
        
        # Add a true/false question if we have room
        if len(questions) < num_questions and concepts:
            concept = concepts[0]
            concept_title = concept.get("title", "this concept")
            
            tf_question = QuizQuestion(
                question=f"True or False: {concept_title} is an important concept in this module.",
                question_type=QuestionType.TRUE_FALSE,
                options=["True", "False"],
                correct_answer="True",
                explanation="This is true because all concepts in the curriculum are important.",
                concept_id=concept.get("id", ""),
                difficulty=1,
            )
            questions.append(tf_question)
        
        return Quiz(
            module_id=module.get("id", ""),
            module_title=module.get("title", "Module"),
            questions=questions,
            created_at=datetime.now(),
        )
    
    def _check_answer(self, question: QuizQuestion, answer: str) -> bool | None:
        """Check if an answer is correct.
        
        For multiple choice and true/false, uses exact matching.
        For code questions, uses normalized comparison.
        For open-ended questions, returns None (deferred to AI evaluation).
        
        Args:
            question: The quiz question.
            answer: The user's answer.
            
        Returns:
            True if correct, False if incorrect, None if pending AI evaluation.
        """
        # For open-ended questions, defer evaluation to Performance Analyst AI
        # These need semantic evaluation, not exact string matching
        if question.question_type == QuestionType.OPEN_ENDED:
            return None  # Pending AI evaluation
        
        # Normalize both answers for comparison
        normalized_answer = answer.strip().lower()
        normalized_correct = question.correct_answer.strip().lower()
        
        # For multiple choice, check if answer matches correct answer
        if question.question_type == QuestionType.MULTIPLE_CHOICE:
            return normalized_answer == normalized_correct
        
        # For true/false, normalize to true/false strings
        if question.question_type == QuestionType.TRUE_FALSE:
            return normalized_answer == normalized_correct
        
        # For code questions, normalize whitespace and compare
        if question.question_type == QuestionType.CODE:
            # Normalize whitespace for code comparison
            normalized_answer = " ".join(normalized_answer.split())
            normalized_correct = " ".join(normalized_correct.split())
            return normalized_answer == normalized_correct
        
        # Fallback: exact match for unknown types
        return normalized_answer == normalized_correct
    
    def _identify_weak_concepts(self) -> list[str]:
        """Identify concepts where user answered incorrectly."""
        if not self._current_quiz:
            return []
        
        weak = set()
        
        for result in self._results:
            if not result.is_correct:
                # Find the question to get its concept_id
                for q in self._current_quiz.questions:
                    if q.id == result.question_id and q.concept_id:
                        weak.add(q.concept_id)
                        break
        
        return list(weak)
    
    def _update_concept_mastery(
        self,
        weak_concepts: list[str],
        overall_score: float,
    ) -> None:
        """Update concept mastery based on quiz results.
        
        Handles cases where multiple questions may test the same concept.
        If ANY question about a concept was answered correctly, the concept
        gets high mastery. Only if ALL questions were wrong/unanswered does
        the concept get low mastery.
        """
        if not self._current_quiz or not self._course_id:
            return
        
        # Build a set of correctly answered question IDs
        # This ensures unanswered questions are NOT counted as correct
        correctly_answered = {
            r.question_id for r in self._results if r.is_correct
        }
        
        # Group questions by concept and track if ANY was correct
        # This handles duplicate concepts (multiple questions about same concept)
        concept_was_correct: dict[str, bool] = {}
        
        for question in self._current_quiz.questions:
            concept_id = question.concept_id
            if not concept_id:
                continue
            
            was_correct = question.id in correctly_answered
            
            # If this is the first question for this concept, record the result
            # If we've seen this concept before, keep True if either was correct
            if concept_id not in concept_was_correct:
                concept_was_correct[concept_id] = was_correct
            elif was_correct:
                # Already have an entry, but this one is correct - update to True
                concept_was_correct[concept_id] = True
        
        # Now save mastery once per concept (no overwrites)
        for concept_id, was_correct in concept_was_correct.items():
            mastery = 0.8 if was_correct else 0.3
            
            self._db.save_concept_mastery(
                self._course_id,
                concept_id,
                mastery_level=mastery,
            )
    
    def _generate_feedback_stub(
        self,
        score: float,
        weak_concepts: list[str],
    ) -> str:
        """Generate stub feedback for quiz results.
        
        Note: Will be replaced by AssessmentCrew in Milestone 6.
        """
        percentage = int(score * 100)
        
        if score >= 0.9:
            praise = "Excellent work! 🌟"
            recommendation = "You've mastered this module."
        elif score >= QUIZ_PASS_THRESHOLD:
            praise = "Good job! 👍"
            recommendation = "You can proceed to the next module."
        elif score >= 0.6:
            praise = "Nice effort! 💪"
            recommendation = "Review the concepts you missed before moving on."
        else:
            praise = "Keep practicing! 📚"
            recommendation = "Consider reviewing this module before retaking the quiz."
        
        feedback = f"{praise}\n\nYou scored {percentage}%.\n\n{recommendation}"
        
        if weak_concepts:
            feedback += f"\n\nFocus areas: {len(weak_concepts)} concept(s) need review."
        
        return feedback
