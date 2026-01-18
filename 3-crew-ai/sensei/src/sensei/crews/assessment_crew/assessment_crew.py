"""Assessment Crew - Generates quizzes and evaluates learner performance.

This crew is responsible for assessing learner understanding after completing
a module. Like the Teaching Crew, it uses a "dynamic task selection" pattern
with two independent execution paths:
- generate_quiz(): Uses Quiz Designer to create assessment questions
- evaluate_answers(): Uses Performance Analyst to analyze results

Each method creates a focused mini-crew with just the relevant agent
and task, sharing the same configuration and memory settings.

Note: This crew does NOT use @CrewBase because it needs dynamic task
selection (only one agent/task per call). @CrewBase expects all agents
and tasks to be used together, which doesn't fit this pattern.
"""

import json
from pathlib import Path
from typing import Any

import yaml
from crewai import Agent, Crew, Process, Task

from sensei.models.schemas import (
    AnswerResult,
    Module,
    Quiz,
    QuizQuestion,
    QuizResult,
    UserPreferences,
)
from sensei.models.enums import QuestionType
from sensei.storage.memory_manager import (
    format_experience_level,
    format_learning_style,
    get_openai_embedder_config,
)


class AssessmentCrew:
    """Assessment Crew - Creates quizzes and evaluates performance.
    
    This crew contains two agents that work in separate phases:
    - Quiz Designer: Creates targeted quiz questions
    - Performance Analyst: Evaluates answers and provides feedback
    
    The crew uses a "dynamic task selection" pattern where each
    public method creates a mini-crew with only the relevant
    agent and task for that operation.
    
    Design Decision:
    ----------------
    Like TeachingCrew, AssessmentCrew manually loads YAML configs because:
    
    1. @CrewBase expects all @agent/@task decorated methods to be used
       together in a single crew execution
    2. AssessmentCrew needs to run agents INDEPENDENTLY (generate OR evaluate,
       not both)
    3. The two phases are separated by user action (user takes the quiz)
    
    Example:
        ```python
        crew = AssessmentCrew()
        
        # Phase 1: Generate quiz
        quiz = crew.generate_quiz(
            module=module,
            weak_concepts=["concept-123"],
            user_prefs=UserPreferences(experience_level="intermediate")
        )
        
        # ... User takes quiz, submits answers ...
        
        # Phase 2: Evaluate results
        result = crew.evaluate_answers(
            quiz=quiz,
            answers={"q-1": "A", "q-2": "C"},
            user_prefs=user_prefs
        )
        ```
    """
    
    def __init__(self) -> None:
        """Initialize the Assessment Crew by loading configurations."""
        self._config_dir = Path(__file__).parent / "config"
        self._agents_config = self._load_yaml("agents.yaml")
        self._tasks_config = self._load_yaml("tasks.yaml")
    
    def _load_yaml(self, filename: str) -> dict[str, Any]:
        """Load a YAML configuration file."""
        config_path = self._config_dir / filename
        with open(config_path) as f:
            return yaml.safe_load(f)
    
    # ==================== AGENTS ====================
    
    def _create_quiz_designer(self) -> Agent:
        """Create the Quiz Designer agent.
        
        This agent is responsible for creating diverse, targeted
        quiz questions that accurately assess understanding.
        """
        return Agent(
            config=self._agents_config["quiz_designer"],
            verbose=True,
        )
    
    def _create_performance_analyst(self) -> Agent:
        """Create the Performance Analyst agent.
        
        This agent is responsible for analyzing quiz results
        and providing encouraging, actionable feedback.
        """
        return Agent(
            config=self._agents_config["performance_analyst"],
            verbose=True,
        )
    
    # ==================== TASKS ====================
    
    def _create_generate_quiz_task(self, agent: Agent) -> Task:
        """Create the generate quiz task.
        
        Args:
            agent: The agent to assign this task to.
        """
        return Task(
            config=self._tasks_config["generate_quiz_task"],
            agent=agent,
        )
    
    def _create_evaluate_quiz_task(self, agent: Agent) -> Task:
        """Create the evaluate quiz task.
        
        Args:
            agent: The agent to assign this task to.
        """
        return Task(
            config=self._tasks_config["evaluate_quiz_task"],
            agent=agent,
        )
    
    # ==================== CREW CREATION ====================
    
    def _create_assessment_crew(self, agent: Agent, task: Task) -> Crew:
        """Create a focused mini-crew for a specific operation.
        
        This method creates a crew with just one agent and one task,
        allowing for independent execution of quiz generation or evaluation.
        
        Args:
            agent: The agent to include in the crew.
            task: The task for the agent to perform.
            
        Returns:
            A configured Crew ready for execution.
        """
        return Crew(
            agents=[agent],
            tasks=[task],
            process=Process.sequential,  # Single task, sequential is fine
            verbose=True,
            memory=True,
            embedder=get_openai_embedder_config(),
        )
    
    # ==================== HELPER METHODS ====================
    
    def _format_concepts_list(self, concepts: list[dict[str, Any]]) -> str:
        """Format a list of concepts for the prompt.
        
        Args:
            concepts: List of concept dictionaries.
            
        Returns:
            Formatted string listing all concepts.
        """
        if not concepts:
            return "No concepts available."
        
        lines = []
        for i, concept in enumerate(concepts, 1):
            title = concept.get("title", "Untitled")
            content = concept.get("content", "")
            concept_id = concept.get("id", f"concept-{i}")
            
            # Truncate content if too long
            if len(content) > 200:
                content = content[:200] + "..."
            
            lines.append(f"{i}. **{title}** (ID: {concept_id})")
            if content:
                lines.append(f"   {content}")
        
        return "\n".join(lines)
    
    def _format_focus_concepts(
        self,
        concepts: list[dict[str, Any]],
        focus_ids: list[str],
    ) -> str:
        """Format focus concepts for the prompt.
        
        Args:
            concepts: List of concept dictionaries.
            focus_ids: List of concept IDs to focus on.
            
        Returns:
            Formatted string describing focus areas.
        """
        if not focus_ids:
            return "No specific focus areas. Test all concepts evenly."
        
        focus_concepts = [
            c for c in concepts
            if c.get("id", "") in focus_ids
        ]
        
        if not focus_concepts:
            return "No specific focus areas. Test all concepts evenly."
        
        lines = ["These concepts need extra attention (low mastery or previous struggles):"]
        for concept in focus_concepts:
            lines.append(f"- **{concept.get('title', 'Untitled')}** (ID: {concept.get('id', '')})")
        
        return "\n".join(lines)
    
    def _format_detailed_results(
        self,
        quiz: Quiz,
        answers: dict[str, str],
    ) -> str:
        """Format detailed quiz results for the evaluation prompt.
        
        Args:
            quiz: The quiz that was taken.
            answers: Dictionary mapping question_id to user's answer.
            
        Returns:
            Formatted string with detailed results per question.
        """
        lines = []
        for i, question in enumerate(quiz.questions, 1):
            user_answer = answers.get(question.id, "Not answered")
            is_correct = user_answer == question.correct_answer
            status = "✅ Correct" if is_correct else "❌ Incorrect"
            
            lines.append(f"**Question {i}:** {question.question}")
            lines.append(f"- Your answer: {user_answer}")
            lines.append(f"- Correct answer: {question.correct_answer}")
            lines.append(f"- Status: {status}")
            lines.append(f"- Concept: {question.concept_id}")
            lines.append("")
        
        return "\n".join(lines)
    
    def _parse_quiz_response(self, response: str, module: Module) -> Quiz:
        """Parse the LLM's quiz response into a Quiz object.
        
        Args:
            response: The raw response from the Quiz Designer.
            module: The module being assessed.
            
        Returns:
            A Quiz object with the parsed questions.
            
        Raises:
            ValueError: If the response cannot be parsed.
        """
        # Try to extract JSON from the response
        try:
            # Look for JSON in the response (might be wrapped in markdown)
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            
            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON found in response")
            
            json_str = response[json_start:json_end]
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse quiz JSON: {e}") from e
        
        # Extract questions
        questions_data = data.get("questions", [])
        if not questions_data:
            raise ValueError("No questions found in response")
        
        questions = []
        for q_data in questions_data:
            # Map question type
            q_type_str = q_data.get("question_type", "multiple_choice")
            q_type = QuestionType.MULTIPLE_CHOICE
            if q_type_str == "true_false":
                q_type = QuestionType.TRUE_FALSE
            elif q_type_str == "code":
                q_type = QuestionType.CODE
            elif q_type_str == "open_ended":
                q_type = QuestionType.OPEN_ENDED
            
            question = QuizQuestion(
                question=q_data.get("question", ""),
                question_type=q_type,
                options=q_data.get("options", []),
                correct_answer=q_data.get("correct_answer", ""),
                explanation=q_data.get("explanation", ""),
                concept_id=q_data.get("concept_id", ""),
                difficulty=q_data.get("difficulty", 2),
            )
            questions.append(question)
        
        return Quiz(
            module_id=module.id,
            module_title=module.title,
            questions=questions,
        )
    
    def _parse_evaluation_response(
        self,
        response: str,
        quiz: Quiz,
        answers: dict[str, str],
        course_id: str = "",
    ) -> QuizResult:
        """Parse the LLM's evaluation response into a QuizResult object.
        
        Args:
            response: The raw response from the Performance Analyst.
            quiz: The quiz that was evaluated.
            answers: Dictionary mapping question_id to user's answer.
            course_id: The course ID for the result.
            
        Returns:
            A QuizResult object with the parsed evaluation.
            
        Raises:
            ValueError: If the response cannot be parsed.
        """
        # Calculate actual score from answers
        correct_count = 0
        for question in quiz.questions:
            user_answer = answers.get(question.id, "")
            if user_answer == question.correct_answer:
                correct_count += 1
        
        total_questions = len(quiz.questions)
        actual_score = correct_count / total_questions if total_questions > 0 else 0.0
        passed = actual_score >= 0.8
        
        # Try to extract JSON from the response for feedback
        feedback = "Quiz completed."
        weak_concepts: list[str] = []
        
        try:
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            
            if json_start != -1 and json_end > 0:
                json_str = response[json_start:json_end]
                data = json.loads(json_str)
                
                feedback = data.get("feedback", feedback)
                weak_concepts = data.get("weak_concepts", [])
                
                # Add next_steps to feedback if available
                next_steps = data.get("next_steps", "")
                if next_steps:
                    feedback = f"{feedback}\n\n**Next Steps:** {next_steps}"
        except (json.JSONDecodeError, ValueError):
            # If we can't parse JSON, use the raw response as feedback
            feedback = response
        
        # If no weak concepts from LLM, calculate from wrong answers
        if not weak_concepts:
            for question in quiz.questions:
                user_answer = answers.get(question.id, "")
                if user_answer != question.correct_answer and question.concept_id:
                    if question.concept_id not in weak_concepts:
                        weak_concepts.append(question.concept_id)
        
        return QuizResult(
            quiz_id=quiz.id,
            course_id=course_id,
            module_id=quiz.module_id,
            module_title=quiz.module_title,
            score=actual_score,
            correct_count=correct_count,
            total_questions=total_questions,
            weak_concepts=weak_concepts,
            feedback=feedback,
            passed=passed,
        )
    
    # ==================== PUBLIC METHODS ====================
    
    def generate_quiz(
        self,
        module: Module,
        weak_concepts: list[str] | None = None,
        user_prefs: UserPreferences | None = None,
        previous_attempts: int = 0,
    ) -> Quiz:
        """Generate a quiz for a module.
        
        This method creates a mini-crew with the Quiz Designer
        to generate assessment questions for the module.
        
        Args:
            module: The module to create a quiz for.
            weak_concepts: List of concept IDs that need extra focus.
            user_prefs: User's learning preferences.
            previous_attempts: Number of previous quiz attempts for this module.
        
        Returns:
            A Quiz object with generated questions.
        
        Raises:
            ValueError: If module is None or has no concepts.
            RuntimeError: If quiz generation fails.
        """
        if module is None:
            raise ValueError("Module cannot be None")
        if not module.concepts:
            raise ValueError("Module must have concepts to quiz")
        
        # Set defaults
        if weak_concepts is None:
            weak_concepts = []
        if user_prefs is None:
            user_prefs = UserPreferences()
        
        # Create the agent and task
        designer = self._create_quiz_designer()
        task = self._create_generate_quiz_task(designer)
        
        # Create the crew
        crew = self._create_assessment_crew(designer, task)
        
        # Prepare concepts as dictionaries for formatting
        concepts_data = [c.model_dump() for c in module.concepts]
        
        # Prepare inputs
        inputs = {
            "module_title": module.title,
            "module_id": module.id,
            "concepts_list": self._format_concepts_list(concepts_data),
            "experience_level": format_experience_level(user_prefs.experience_level),
            "previous_attempts": str(previous_attempts),
            "focus_concepts": self._format_focus_concepts(concepts_data, weak_concepts),
            "weak_areas": (
                ", ".join(weak_concepts) if weak_concepts
                else "No previously identified weak areas."
            ),
        }
        
        # Execute the crew
        result = crew.kickoff(inputs=inputs)
        
        # Parse the response into a Quiz object
        return self._parse_quiz_response(result.raw, module)
    
    def evaluate_answers(
        self,
        quiz: Quiz,
        answers: dict[str, str],
        user_prefs: UserPreferences | None = None,
        course_id: str = "",
        previous_scores: list[float] | None = None,
    ) -> QuizResult:
        """Evaluate quiz answers and provide feedback.
        
        This method creates a mini-crew with the Performance Analyst
        to evaluate the learner's quiz performance.
        
        Args:
            quiz: The quiz that was taken.
            answers: Dictionary mapping question_id to user's answer.
            user_prefs: User's learning preferences.
            course_id: The course ID for tracking.
            previous_scores: List of previous quiz scores for context.
        
        Returns:
            A QuizResult with score, feedback, and recommendations.
        
        Raises:
            ValueError: If quiz is None or has no questions.
            RuntimeError: If evaluation fails.
        """
        if quiz is None:
            raise ValueError("Quiz cannot be None")
        if not quiz.questions:
            raise ValueError("Quiz must have questions to evaluate")
        
        # Set defaults
        if user_prefs is None:
            user_prefs = UserPreferences()
        if previous_scores is None:
            previous_scores = []
        
        # Calculate basic stats
        correct_count = sum(
            1 for q in quiz.questions
            if answers.get(q.id, "") == q.correct_answer
        )
        incorrect_count = len(quiz.questions) - correct_count
        score_percentage = int((correct_count / len(quiz.questions)) * 100)
        
        # Create the agent and task
        analyst = self._create_performance_analyst()
        task = self._create_evaluate_quiz_task(analyst)
        
        # Create the crew
        crew = self._create_assessment_crew(analyst, task)
        
        # Format previous performance
        if previous_scores:
            prev_perf = f"Previous scores for this module: {', '.join(f'{int(s*100)}%' for s in previous_scores)}"
            if len(previous_scores) > 1:
                trend = "improving" if previous_scores[-1] > previous_scores[0] else "needs attention"
                prev_perf += f"\nTrend: {trend}"
        else:
            prev_perf = "This is the first attempt for this module."
        
        # Prepare inputs
        inputs = {
            "module_title": quiz.module_title,
            "total_questions": str(len(quiz.questions)),
            "correct_count": str(correct_count),
            "incorrect_count": str(incorrect_count),
            "score_percentage": str(score_percentage),
            "detailed_results": self._format_detailed_results(quiz, answers),
            "experience_level": format_experience_level(user_prefs.experience_level),
            "learning_style": format_learning_style(user_prefs.learning_style),
            "previous_performance": prev_perf,
        }
        
        # Execute the crew
        result = crew.kickoff(inputs=inputs)
        
        # Parse the response into a QuizResult object
        return self._parse_evaluation_response(result.raw, quiz, answers, course_id)
