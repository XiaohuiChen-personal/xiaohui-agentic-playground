"""Curriculum Crew - Creates comprehensive learning curricula.

This crew is responsible for creating course structures when a user
wants to learn a new topic. It runs once per course creation and
generates a complete structure of modules and concepts.

Memory Usage:
    This crew uses CrewAI's built-in memory system:
    - Short-term: Passes context between Curriculum Architect and Content Researcher
    - Long-term: Learns patterns (e.g., "beginner users need more foundational modules")
    - Entity: Remembers facts about topics and user preferences
    
    Memory is enabled via `memory=True` in the Crew configuration.
    Embeddings use OpenAI's text-embedding-3-small for semantic search.

Structured Output:
    This crew uses CrewAI's output_pydantic feature for reliable structured output.
    The final task outputs a CourseOutput Pydantic model, which is then converted
    to the full Course model with auto-generated fields (id, created_at, etc.).
"""

from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task

from sensei.models.schemas import (
    Concept,
    Course,
    CourseOutput,
    Module,
    UserPreferences,
)
from sensei.storage.memory_manager import get_openai_embedder_config


@CrewBase
class CurriculumCrew:
    """Curriculum Crew - Creates course structures and curricula.
    
    This crew contains two agents:
    - Curriculum Architect: Plans the overall course structure and modules
    - Content Researcher: Defines detailed concepts for each module
    
    The crew runs sequentially, with the architect creating the course
    skeleton and the researcher filling in the concept details.
    
    Example:
        ```python
        crew = CurriculumCrew()
        course = crew.create_curriculum(
            topic="Python Basics",
            user_prefs=UserPreferences(experience_level="beginner")
        )
        ```
    """
    
    agents: list[BaseAgent]
    tasks: list[Task]
    
    # YAML configuration file paths (relative to this file)
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"
    
    # ==================== AGENTS ====================
    
    @agent
    def curriculum_architect(self) -> Agent:
        """Senior Curriculum Designer agent.
        
        Responsible for:
        - Analyzing topic scope and depth
        - Defining 5-10 modules with learning objectives
        - Ordering modules by prerequisites
        - Estimating time per module
        """
        return Agent(
            config=self.agents_config["curriculum_architect"],  # type: ignore[index]
            verbose=True,
        )
    
    @agent
    def content_researcher(self) -> Agent:
        """Technical Content Specialist agent.
        
        Responsible for:
        - Researching key concepts for each module (3-7 per module)
        - Defining learning points for each concept
        - Identifying common misconceptions
        - Including practical applications
        """
        return Agent(
            config=self.agents_config["content_researcher"],  # type: ignore[index]
            verbose=True,
        )
    
    # ==================== TASKS ====================
    
    @task
    def plan_curriculum_task(self) -> Task:
        """Task to plan the curriculum structure.
        
        Input: Topic and user preferences
        Output: Course skeleton with modules
        """
        return Task(
            config=self.tasks_config["plan_curriculum_task"],  # type: ignore[index]
        )
    
    @task
    def research_content_task(self) -> Task:
        """Task to research and define concepts.
        
        Input: Course skeleton from plan_curriculum_task (via context)
        Output: Complete course with detailed concepts (as CourseOutput Pydantic model)
        
        Uses output_pydantic for reliable structured output from the LLM.
        """
        return Task(
            config=self.tasks_config["research_content_task"],  # type: ignore[index]
            context=[self.plan_curriculum_task()],  # Receive output from first task
            output_pydantic=CourseOutput,  # Structured output!
        )
    
    # ==================== CREW ====================
    
    @crew
    def crew(self) -> Crew:
        """Creates the Curriculum Crew with selective memory.
        
        The crew runs sequentially:
        1. Curriculum Architect plans the structure
        2. Content Researcher fills in concept details
        
        Memory Configuration:
            - Short-term: ENABLED - passes context between agents within this run
            - Long-term: DISABLED - prevents cross-session pattern learning that could
              cause topic drift (e.g., CUDA content appearing in Python courses)
            - Entity: DISABLED - prevents entity extraction from previous runs
              contaminating new curriculum generation
            - Embedder: OpenAI text-embedding-3-small for semantic search
        
        Why Disable Long-term and Entity Memory:
            Curriculum generation should be independent for each topic.
            Entity memory was causing contamination where entities from
            previous courses (e.g., CUDA) would influence new generations.
        """
        return Crew(
            agents=self.agents,  # Automatically created by @agent decorators
            tasks=self.tasks,    # Automatically created by @task decorators
            process=Process.sequential,
            verbose=True,
            # Enable memory with selective configuration
            memory=True,
            memory_config={
                "provider": "mem0",  # Default provider
                "config": {
                    "short_term": {
                        "enabled": True,  # Keep: passes context between agents
                    },
                    "long_term": {
                        "enabled": False,  # Disable: prevents topic drift
                    },
                    "entity": {
                        "enabled": False,  # Disable: prevents contamination
                    },
                },
            },
            # Configure embeddings for semantic memory search
            embedder=get_openai_embedder_config(),
            # Enable tracing for debugging and monitoring
            tracing=True,
        )
    
    # ==================== PUBLIC METHODS ====================
    
    def create_curriculum(
        self,
        topic: str,
        user_prefs: UserPreferences | None = None,
    ) -> Course:
        """Create a comprehensive curriculum for a topic.
        
        This is the main entry point for the Curriculum Crew.
        It kicks off the crew to generate a complete course structure.
        
        Args:
            topic: The subject to create a curriculum for.
            user_prefs: Optional user preferences for personalization.
        
        Returns:
            A Course object with modules and concepts.
        
        Raises:
            ValueError: If topic is empty.
            RuntimeError: If crew execution fails.
        """
        if not topic or not topic.strip():
            raise ValueError("Topic cannot be empty")
        
        # Set default preferences if not provided
        if user_prefs is None:
            user_prefs = UserPreferences()
        
        # Prepare inputs for the crew
        inputs = {
            "topic": topic.strip(),
            "experience_level": user_prefs.experience_level.value,
            "learning_style": user_prefs.learning_style.value,
            "goals": user_prefs.goals or f"Learn {topic}",
        }
        
        # Execute the crew
        result = self.crew().kickoff(inputs=inputs)
        
        # The result.pydantic contains our CourseOutput model
        # Convert it to a full Course object with auto-generated fields
        if result.pydantic:
            return self._output_to_course(result.pydantic)
        
        # Fallback: try to parse raw output (shouldn't happen with output_pydantic)
        raise RuntimeError(
            f"Failed to get structured output from crew. "
            f"Raw output: {result.raw[:500] if result.raw else 'None'}..."
        )
    
    def _output_to_course(self, output: CourseOutput) -> Course:
        """Convert a CourseOutput (LLM output) to a full Course object.
        
        This adds auto-generated fields (id, created_at, status, mastery, etc.)
        to the LLM output.
        
        Args:
            output: The CourseOutput from the LLM.
        
        Returns:
            A full Course object with all fields populated.
        """
        # Build modules with concepts
        modules = []
        for module_output in output.modules:
            # Build concepts for this module
            concepts = []
            for concept_output in module_output.concepts:
                concept = Concept(
                    title=concept_output.title,
                    content=concept_output.content,
                    order=concept_output.order,
                    # id, status, mastery, questions_asked are auto-generated
                )
                concepts.append(concept)
            
            module = Module(
                title=module_output.title,
                description=module_output.description,
                concepts=concepts,
                order=module_output.order,
                estimated_minutes=module_output.estimated_minutes,
                # id is auto-generated
            )
            modules.append(module)
        
        # Build course
        course = Course(
            title=output.title,
            description=output.description,
            modules=modules,
            # id, created_at are auto-generated
        )
        
        return course
