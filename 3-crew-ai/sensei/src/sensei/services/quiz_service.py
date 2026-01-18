"""Quiz service for managing assessments.

This service handles quiz generation, answer submission, and result
calculation. Quiz generation is stubbed and will be replaced with
CrewAI integration in Milestone 6.
"""

from datetime import datetime
from typing import Any

from sensei.models.enums import QuestionType
from sensei.models.schemas import AnswerResult, Quiz, QuizQuestion, QuizResult
from sensei.storage.database import Database
from sensei.storage.file_storage import load_course
from sensei.utils.constants import QUIZ_PASS_THRESHOLD


class QuizService:
    """Service for managing quiz assessments.
    
    This service handles:
    - Generating quizzes for modules (stub for now)
    - Processing answer submissions
    - Calculating and returning results
    - Tracking weak concepts
    
    Example:
        ```python
        service = QuizService()
        
        # Generate a quiz for a module
        quiz = service.generate_quiz("course-123", 0)
        
        # Submit answers
        for question in quiz.questions:
            result = service.submit_answer(question.id, "user_answer")
            print(f"Correct: {result.is_correct}")
        
        # Get final results
        results = service.get_results()
        print(f"Score: {results.score_percentage}%")
        ```
    """
    
    def __init__(self, database: Database | None = None):
        """Initialize the quiz service.
        
        Args:
            database: Optional Database instance.
        """
        self._db = database or Database()
        self._current_quiz: Quiz | None = None
        self._course_id: str | None = None
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
    ) -> Quiz:
        """Generate a quiz for a module.
        
        Note: This currently uses a stub generator. In Milestone 6,
        this will be replaced with AssessmentCrew integration.
        
        Args:
            course_id: The unique identifier for the course.
            module_idx: Zero-based index of the module.
            num_questions: Number of questions to generate (default 5).
        
        Returns:
            Quiz object with generated questions.
        
        Raises:
            ValueError: If course or module doesn't exist.
        """
        # Load course and module
        course = load_course(course_id)
        if course is None:
            raise ValueError(f"Course not found: {course_id}")
        
        modules = course.get("modules", [])
        if module_idx < 0 or module_idx >= len(modules):
            raise ValueError(f"Module index out of range: {module_idx}")
        
        module = modules[module_idx]
        
        # Generate stub quiz
        quiz = self._generate_quiz_stub(module, num_questions)
        
        # Store state
        self._current_quiz = quiz
        self._course_id = course_id
        self._answers = {}
        self._results = []
        
        return quiz
    
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
        
        # Check if correct
        is_correct = self._check_answer(question, answer)
        
        # Create result
        result = AnswerResult(
            question_id=question_id,
            user_answer=answer,
            is_correct=is_correct,
            correct_answer=question.correct_answer,
            explanation=question.explanation,
        )
        
        self._results.append(result)
        
        return result
    
    def get_results(self) -> QuizResult:
        """Get final quiz results.
        
        Calculates score, identifies weak concepts, and saves to database.
        
        Returns:
            QuizResult with score, feedback, and recommendations.
        
        Raises:
            RuntimeError: If no quiz is active.
        """
        if not self._current_quiz or not self._course_id:
            raise RuntimeError("No active quiz")
        
        # Calculate score
        total = len(self._current_quiz.questions)
        correct_count = sum(1 for r in self._results if r.is_correct)
        score = correct_count / total if total > 0 else 0.0
        
        # Identify weak concepts (from wrong answers)
        weak_concepts = self._identify_weak_concepts()
        
        # Determine pass/fail
        passed = score >= QUIZ_PASS_THRESHOLD
        
        # Generate feedback
        feedback = self._generate_feedback_stub(score, weak_concepts)
        
        # Create result
        result = QuizResult(
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
        
        # Save to database
        self._db.save_quiz_result({
            "course_id": self._course_id,
            "module_id": self._current_quiz.module_id,
            "module_title": self._current_quiz.module_title,
            "quiz_id": self._current_quiz.id,
            "score": score,
            "correct_count": correct_count,
            "total_questions": total,
            "weak_concepts": weak_concepts,
            "feedback": feedback,
            "passed": passed,
        })
        
        # Update concept mastery for weak concepts
        self._update_concept_mastery(weak_concepts, score)
        
        return result
    
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
    
    def _check_answer(self, question: QuizQuestion, answer: str) -> bool:
        """Check if an answer is correct."""
        # Normalize both answers for comparison
        normalized_answer = answer.strip().lower()
        normalized_correct = question.correct_answer.strip().lower()
        
        # For multiple choice, check if answer matches correct answer
        if question.question_type == QuestionType.MULTIPLE_CHOICE:
            return normalized_answer == normalized_correct
        
        # For true/false, normalize to true/false strings
        if question.question_type == QuestionType.TRUE_FALSE:
            return normalized_answer == normalized_correct
        
        # For other types, do exact match for now
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
