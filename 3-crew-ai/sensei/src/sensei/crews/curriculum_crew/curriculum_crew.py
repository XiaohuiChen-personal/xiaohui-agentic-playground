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
"""

import json
from typing import Any

from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task

from sensei.models.schemas import Concept, Course, Module, UserPreferences
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
        
        Input: Course skeleton from plan_curriculum_task
        Output: Complete course with detailed concepts
        """
        return Task(
            config=self.tasks_config["research_content_task"],  # type: ignore[index]
        )
    
    # ==================== CREW ====================
    
    @crew
    def crew(self) -> Crew:
        """Creates the Curriculum Crew with memory enabled.
        
        The crew runs sequentially:
        1. Curriculum Architect plans the structure
        2. Content Researcher fills in concept details
        
        Memory Configuration:
            - memory=True: Enables CrewAI's built-in memory system
            - Short-term: Context passes automatically between agents
            - Long-term: Patterns learned across curriculum generations
            - Entity: Facts about topics extracted and stored
            - Embedder: OpenAI text-embedding-3-small for semantic search
        
        Benefits of Memory:
            - Architect's output is automatically available to Researcher
            - Crew learns which curriculum structures work best
            - Better personalization based on remembered user patterns
        """
        return Crew(
            agents=self.agents,  # Automatically created by @agent decorators
            tasks=self.tasks,    # Automatically created by @task decorators
            process=Process.sequential,
            verbose=True,
            # Enable CrewAI memory system
            memory=True,
            # Configure embeddings for semantic memory search
            embedder=get_openai_embedder_config(),
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
        
        # Parse the result into a Course object
        return self._parse_crew_output(result.raw, topic)
    
    def _parse_crew_output(self, raw_output: str, topic: str) -> Course:
        """Parse the crew's raw output into a Course object.
        
        The crew outputs JSON, which we parse and convert to our
        Pydantic models.
        
        Args:
            raw_output: The raw string output from the crew.
            topic: The original topic (for fallback title).
        
        Returns:
            A Course object.
        
        Raises:
            RuntimeError: If parsing fails.
        """
        try:
            # Extract JSON from the output
            # The output might have text before/after the JSON
            json_str = self._extract_json(raw_output)
            data = json.loads(json_str)
            
            # Convert to Course object
            return self._dict_to_course(data, topic)
            
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            raise RuntimeError(
                f"Failed to parse crew output: {e}\n"
                f"Raw output: {raw_output[:500]}..."
            ) from e
    
    def _extract_json(self, text: str) -> str:
        """Extract JSON object from text that may contain other content.
        
        Finds the outermost JSON object in the text.
        
        Args:
            text: Text potentially containing JSON.
        
        Returns:
            The extracted JSON string.
        
        Raises:
            ValueError: If no JSON object is found.
        """
        # Find the first { and last }
        start = text.find("{")
        end = text.rfind("}")
        
        if start == -1 or end == -1 or start >= end:
            raise ValueError("No JSON object found in output")
        
        return text[start:end + 1]
    
    def _dict_to_course(self, data: dict[str, Any], fallback_topic: str) -> Course:
        """Convert a dictionary to a Course object.
        
        Args:
            data: Dictionary from parsed JSON.
            fallback_topic: Topic to use if title is missing.
        
        Returns:
            A Course object with modules and concepts.
        """
        # Build modules
        modules = []
        for module_data in data.get("modules", []):
            # Build concepts for this module
            concepts = []
            for concept_data in module_data.get("concepts", []):
                concept = Concept(
                    title=concept_data.get("title", "Untitled Concept"),
                    content=concept_data.get("content", ""),
                    order=concept_data.get("order", len(concepts)),
                )
                concepts.append(concept)
            
            module = Module(
                title=module_data.get("title", f"Module {len(modules) + 1}"),
                description=module_data.get("description", ""),
                concepts=concepts,
                order=module_data.get("order", len(modules)),
                estimated_minutes=module_data.get("estimated_minutes", 60),
            )
            modules.append(module)
        
        # Build course
        course = Course(
            title=data.get("title", fallback_topic),
            description=data.get("description", f"A course about {fallback_topic}"),
            modules=modules,
        )
        
        return course
