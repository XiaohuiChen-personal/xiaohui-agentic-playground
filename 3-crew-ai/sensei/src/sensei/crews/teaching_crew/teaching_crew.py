"""Teaching Crew - Generates lesson content and answers questions.

This crew is responsible for teaching concepts during learning sessions.
Unlike the Curriculum Crew which runs sequentially, the Teaching Crew
has two independent execution paths:
- teach_concept(): Uses Knowledge Teacher to generate lessons
- answer_question(): Uses Q&A Mentor to answer learner questions

Each method creates a focused mini-crew with just the relevant agent
and task, sharing the same configuration and memory settings.

Note: This crew does NOT use @CrewBase because it needs dynamic task
selection (only one agent/task per call). @CrewBase expects all agents
and tasks to be used together, which doesn't fit this pattern.
"""

from pathlib import Path
from typing import Any

import yaml
from crewai import Agent, Crew, Process, Task

from sensei.models.schemas import Concept, UserPreferences
from sensei.storage.memory_manager import (
    format_chat_history,
    format_experience_level,
    format_learning_style,
    get_openai_embedder_config,
)


class TeachingCrew:
    """Teaching Crew - Generates lessons and answers questions.
    
    This crew contains two agents that work independently:
    - Knowledge Teacher: Creates comprehensive lesson content
    - Q&A Mentor: Answers learner questions
    
    The crew uses a "dynamic task selection" pattern where each
    public method creates a mini-crew with only the relevant
    agent and task for that operation.
    
    Design Decision:
    ----------------
    Unlike CurriculumCrew which uses @CrewBase decorator, TeachingCrew
    manually loads YAML configs because:
    
    1. @CrewBase expects all @agent/@task decorated methods to be used
       together in a single crew execution
    2. TeachingCrew needs to run agents INDEPENDENTLY (teach OR answer,
       not both)
    3. Manual loading allows creating mini-crews with just one agent/task
    
    The trade-off is slightly more boilerplate, but this enables the
    dynamic task selection pattern required by the Teaching Crew.
    
    Example:
        ```python
        crew = TeachingCrew()
        
        # Generate a lesson for a concept
        lesson = crew.teach_concept(
            concept=concept,
            user_prefs=UserPreferences(learning_style="visual"),
            module_title="Introduction to Python"
        )
        
        # Answer a question about the concept
        answer = crew.answer_question(
            question="Why do we use variables?",
            concept=concept,
            lesson_content=lesson,
            chat_history=[]
        )
        ```
    """
    
    def __init__(self) -> None:
        """Initialize the Teaching Crew by loading configurations."""
        self._config_dir = Path(__file__).parent / "config"
        self._agents_config = self._load_yaml("agents.yaml")
        self._tasks_config = self._load_yaml("tasks.yaml")
    
    def _load_yaml(self, filename: str) -> dict[str, Any]:
        """Load a YAML configuration file."""
        config_path = self._config_dir / filename
        with open(config_path) as f:
            return yaml.safe_load(f)
    
    # ==================== AGENTS ====================
    
    def _create_knowledge_teacher(self) -> Agent:
        """Create the Knowledge Teacher agent.
        
        This agent is responsible for creating comprehensive,
        engaging lesson content adapted to the learner's style.
        """
        # Use config= parameter for cleaner config passing
        # (same pattern as CurriculumCrew, just without @agent decorator)
        return Agent(
            config=self._agents_config["knowledge_teacher"],
            verbose=True,
        )
    
    def _create_qa_mentor(self) -> Agent:
        """Create the Q&A Mentor agent.
        
        This agent is responsible for answering learner questions
        in a patient, encouraging manner.
        """
        return Agent(
            config=self._agents_config["qa_mentor"],
            verbose=True,
        )
    
    # ==================== TASKS ====================
    
    def _create_teach_concept_task(self, agent: Agent) -> Task:
        """Create the teach concept task.
        
        Args:
            agent: The agent to assign this task to.
        """
        return Task(
            config=self._tasks_config["teach_concept_task"],
            agent=agent,
        )
    
    def _create_answer_question_task(self, agent: Agent) -> Task:
        """Create the answer question task.
        
        Args:
            agent: The agent to assign this task to.
        """
        return Task(
            config=self._tasks_config["answer_question_task"],
            agent=agent,
        )
    
    # ==================== CREW CREATION ====================
    
    def _create_teaching_crew(self, agent: Agent, task: Task) -> Crew:
        """Create a focused mini-crew for a specific operation.
        
        This method creates a crew with just one agent and one task,
        allowing for independent execution of teaching or Q&A.
        
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
    
    # ==================== PUBLIC METHODS ====================
    
    def teach_concept(
        self,
        concept: Concept,
        user_prefs: UserPreferences | None = None,
        module_title: str = "",
        previous_struggles: str = "",
    ) -> str:
        """Generate a comprehensive lesson for a concept.
        
        This method creates a mini-crew with the Knowledge Teacher
        to generate lesson content adapted to the learner's style.
        
        Args:
            concept: The concept to teach.
            user_prefs: User's learning preferences.
            module_title: Title of the current module for context.
            previous_struggles: Any past difficulties the learner
                had with related topics.
        
        Returns:
            Lesson content as a Markdown string.
        
        Raises:
            ValueError: If concept is None or has no title.
            RuntimeError: If lesson generation fails.
        """
        if concept is None:
            raise ValueError("Concept cannot be None")
        if not concept.title or not concept.title.strip():
            raise ValueError("Concept must have a title")
        
        # Set defaults
        if user_prefs is None:
            user_prefs = UserPreferences()
        
        # Create the agent and task
        teacher = self._create_knowledge_teacher()
        task = self._create_teach_concept_task(teacher)
        
        # Create the crew
        crew = self._create_teaching_crew(teacher, task)
        
        # Prepare inputs using centralized formatters from memory_manager
        inputs = {
            "concept_title": concept.title,
            "concept_content": concept.content or "No additional content provided.",
            "learning_style": format_learning_style(user_prefs.learning_style),
            "experience_level": format_experience_level(user_prefs.experience_level),
            "module_title": module_title or "Current Module",
            "previous_struggles": previous_struggles or "No previous struggles noted.",
        }
        
        # Execute the crew
        result = crew.kickoff(inputs=inputs)
        
        return result.raw
    
    def answer_question(
        self,
        question: str,
        concept: Concept,
        lesson_content: str = "",
        chat_history: list[dict[str, str]] | None = None,
        user_prefs: UserPreferences | None = None,
    ) -> str:
        """Answer a learner's question about the current concept.
        
        This method creates a mini-crew with the Q&A Mentor
        to provide a helpful, encouraging answer.
        
        Args:
            question: The learner's question.
            concept: The concept currently being studied.
            lesson_content: The lesson content that was just shown.
            chat_history: Recent Q&A exchanges for context.
            user_prefs: User's learning preferences.
        
        Returns:
            Answer as a Markdown string.
        
        Raises:
            ValueError: If question is empty or concept is None.
            RuntimeError: If answer generation fails.
        """
        if not question or not question.strip():
            raise ValueError("Question cannot be empty")
        if concept is None:
            raise ValueError("Concept cannot be None")
        
        # Set defaults
        if user_prefs is None:
            user_prefs = UserPreferences()
        if chat_history is None:
            chat_history = []
        
        # Create the agent and task
        mentor = self._create_qa_mentor()
        task = self._create_answer_question_task(mentor)
        
        # Create the crew
        crew = self._create_teaching_crew(mentor, task)
        
        # Prepare inputs using centralized formatters from memory_manager
        inputs = {
            "question": question.strip(),
            "concept_title": concept.title,
            "concept_content": concept.content or "No additional content provided.",
            "lesson_content": lesson_content or "No lesson content available.",
            "chat_history": format_chat_history(chat_history),
            "learning_style": format_learning_style(user_prefs.learning_style),
            "experience_level": format_experience_level(user_prefs.experience_level),
        }
        
        # Execute the crew
        result = crew.kickoff(inputs=inputs)
        
        return result.raw
