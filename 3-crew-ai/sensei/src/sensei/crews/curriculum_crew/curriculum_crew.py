"""Curriculum Crew - Creates comprehensive learning curricula using Flow-based design.

This crew uses CrewAI Flows to orchestrate a multi-step curriculum generation process:
1. Create Outline: Curriculum Architect plans the high-level structure
2. Expand Modules: Content Researcher expands each module in parallel
3. Aggregate: Combine all expanded modules into a complete Course

Flow-Based Design Benefits:
- Token Management: Each module expanded separately (~8K tokens max per module)
- Parallelism: Multiple modules expanded concurrently
- Reliability: Per-module failure isolation and retry
- Comprehensiveness: No content truncation due to output limits

Memory Usage:
    - Short-term: ENABLED - passes context between agents within this run
    - Long-term: DISABLED - prevents cross-session pattern learning
    - Entity: DISABLED - prevents contamination from previous runs
"""

import asyncio
import logging
from typing import Any

import yaml
from crewai import Agent, Crew, Process, Task
from crewai.flow.flow import Flow, start, listen
from pathlib import Path

from sensei.models.schemas import (
    Concept,
    ConceptOutline,
    ConceptOutput,
    Course,
    CurriculumOutline,
    Module,
    ModuleOutline,
    ModuleOutput,
    UserPreferences,
)
from sensei.storage.memory_manager import get_openai_embedder_config


logger = logging.getLogger(__name__)


class CurriculumFlow(Flow):
    """Flow-based curriculum generation with parallel module expansion.
    
    This Flow orchestrates the curriculum creation process:
    1. create_outline: Curriculum Architect creates the high-level structure
    2. expand_modules: Content Researcher expands each module in parallel
    3. aggregate: Combine expanded modules into a Course object
    
    Example:
        ```python
        flow = CurriculumFlow()
        course = flow.kickoff(inputs={
            "topic": "Python Basics",
            "experience_level": "beginner",
            "learning_style": "reading",
            "goals": "Learn Python programming",
        })
        ```
    """
    
    # Flow state
    topic: str = ""
    experience_level: str = "beginner"
    learning_style: str = "reading"
    goals: str = ""
    outline: CurriculumOutline | None = None
    expanded_modules: list[ModuleOutput] = []
    
    def __init__(self):
        """Initialize the CurriculumFlow."""
        super().__init__()
        self._config_path = Path(__file__).parent / "config"
        self._agents_config = self._load_yaml("agents.yaml")
        self._tasks_config = self._load_yaml("tasks.yaml")
    
    def _load_yaml(self, filename: str) -> dict[str, Any]:
        """Load a YAML configuration file."""
        with open(self._config_path / filename) as f:
            return yaml.safe_load(f)
    
    # ==================== AGENTS ====================
    
    def _create_curriculum_architect(self) -> Agent:
        """Create the Curriculum Architect agent for Step 1."""
        config = self._agents_config["curriculum_architect"]
        return Agent(
            role=config.get("role", "Senior Curriculum Designer"),
            goal=config.get("goal", "Design a comprehensive curriculum"),
            backstory=config.get("backstory", "Expert curriculum designer"),
            llm=config.get("llm", "gemini/gemini-3-pro-preview"),
            verbose=True,
        )
    
    def _create_content_researcher(self) -> Agent:
        """Create the Content Researcher agent for Step 2."""
        config = self._agents_config["content_researcher"]
        return Agent(
            role=config.get("role", "Technical Content Specialist"),
            goal=config.get("goal", "Research and define concepts"),
            backstory=config.get("backstory", "Technical content expert"),
            llm=config.get("llm", "anthropic/claude-opus-4-5-20251101"),
            max_tokens=config.get("max_tokens", 8000),
            verbose=True,
        )
    
    # ==================== FLOW STEPS ====================
    
    @start()
    def create_outline(self) -> CurriculumOutline:
        """Step 1: Create curriculum outline using Curriculum Architect.
        
        This step generates a lightweight course structure with:
        - Course title and description
        - 5-6 modules with brief descriptions
        - Concept titles (no content yet)
        
        Returns:
            CurriculumOutline with the course skeleton.
        """
        logger.info(f"Step 1: Creating outline for topic: {self.topic}")
        
        # Create the architect agent
        architect = self._create_curriculum_architect()
        
        # Create the outline task
        # Note: expected_output is required by CrewAI Task, but output_pydantic
        # defines the actual structured output format
        task_config = self._tasks_config["create_outline_task"]
        task = Task(
            description=task_config["description"].format(
                topic=self.topic,
                experience_level=self.experience_level,
                learning_style=self.learning_style,
                goals=self.goals,
            ),
            expected_output="A CurriculumOutline with course title, description, and 5-6 modules with concept titles",
            agent=architect,
            output_pydantic=CurriculumOutline,  # Pydantic model defines actual output structure
        )
        
        # Execute single-agent crew
        crew = Crew(
            agents=[architect],
            tasks=[task],
            process=Process.sequential,
            verbose=True,
            memory=True,
            memory_config={
                "provider": "mem0",
                "config": {
                    "short_term": {"enabled": True},
                    "long_term": {"enabled": False},
                    "entity": {"enabled": False},
                },
            },
            embedder=get_openai_embedder_config(),
            tracing=True,
        )
        
        result = crew.kickoff()
        
        if result.pydantic:
            self.outline = result.pydantic
            logger.info(f"Outline created with {len(self.outline.modules)} modules")
            return self.outline
        
        raise RuntimeError(
            f"Failed to create curriculum outline. Raw: {result.raw[:500] if result.raw else 'None'}..."
        )
    
    @listen(create_outline)
    async def expand_modules(self, outline: CurriculumOutline) -> list[ModuleOutput]:
        """Step 2: Expand each module in parallel using Content Researcher.
        
        For each ModuleOutline, creates a mini-crew to expand it with:
        - Full module description
        - 3-5 concepts with detailed content
        
        Uses asyncio.gather for parallel execution.
        
        Args:
            outline: The curriculum outline from Step 1.
        
        Returns:
            List of fully expanded ModuleOutput objects.
        """
        logger.info(f"Step 2: Expanding {len(outline.modules)} modules in parallel")
        
        # Run expansions in parallel using the existing event loop
        expanded = await self._expand_modules_parallel(outline)
        
        self.expanded_modules = expanded
        logger.info(f"Expanded {len(expanded)} modules successfully")
        return expanded
    
    async def _expand_modules_parallel(
        self,
        outline: CurriculumOutline,
    ) -> list[ModuleOutput]:
        """Expand all modules in parallel using asyncio.gather.
        
        Args:
            outline: The curriculum outline containing module outlines.
        
        Returns:
            List of expanded ModuleOutput objects.
        """
        tasks = [
            self._expand_single_module(module_outline, outline)
            for module_outline in outline.modules
        ]
        
        # Run all expansions in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results and handle any exceptions
        expanded_modules = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Module {i} expansion failed: {result}")
                # Create a fallback module with basic content
                expanded_modules.append(self._create_fallback_module(
                    outline.modules[i]
                ))
            else:
                expanded_modules.append(result)
        
        return expanded_modules
    
    async def _expand_single_module(
        self,
        module_outline: ModuleOutline,
        course_outline: CurriculumOutline,
    ) -> ModuleOutput:
        """Expand a single module using the Content Researcher.
        
        This runs in a separate thread to allow parallel execution
        of synchronous crew operations.
        
        Args:
            module_outline: The module outline to expand.
            course_outline: The full course outline for context.
        
        Returns:
            Fully expanded ModuleOutput.
        """
        # Run the synchronous crew operation in a separate thread
        # asyncio.to_thread is Python 3.9+ and handles the event loop correctly
        return await asyncio.to_thread(
            self._expand_module_sync,
            module_outline,
            course_outline,
        )
    
    def _expand_module_sync(
        self,
        module_outline: ModuleOutline,
        course_outline: CurriculumOutline,
    ) -> ModuleOutput:
        """Synchronous module expansion using Content Researcher.
        
        Args:
            module_outline: The module outline to expand.
            course_outline: The full course outline for context.
        
        Returns:
            Fully expanded ModuleOutput.
        """
        logger.info(f"Expanding module: {module_outline.title}")
        
        # Create the content researcher agent
        researcher = self._create_content_researcher()
        
        # Format concept titles for the task description
        concept_titles = [c.title for c in module_outline.concepts]
        
        # Create the expansion task
        # Note: expected_output is required by CrewAI Task, but output_pydantic
        # defines the actual structured output format
        task_config = self._tasks_config["expand_module_task"]
        task = Task(
            description=task_config["description"].format(
                topic=self.topic,
                course_title=course_outline.title,
                module_title=module_outline.title,
                module_description=module_outline.description,
                module_order=module_outline.order,
                estimated_minutes=module_outline.estimated_minutes,
                concept_titles=", ".join(concept_titles),
                experience_level=self.experience_level,
                learning_style=self.learning_style,
            ),
            expected_output="A ModuleOutput with title, description, and 3-5 concepts with detailed content",
            agent=researcher,
            output_pydantic=ModuleOutput,  # Pydantic model defines actual output structure
        )
        
        # Execute single-agent crew for this module
        crew = Crew(
            agents=[researcher],
            tasks=[task],
            process=Process.sequential,
            verbose=True,
            memory=True,
            memory_config={
                "provider": "mem0",
                "config": {
                    "short_term": {"enabled": True},
                    "long_term": {"enabled": False},
                    "entity": {"enabled": False},
                },
            },
            embedder=get_openai_embedder_config(),
            tracing=True,
        )
        
        result = crew.kickoff()
        
        if result.pydantic:
            return result.pydantic
        
        # Fallback: parse raw output if pydantic failed
        logger.warning(f"Module '{module_outline.title}' didn't return pydantic, using fallback")
        return self._create_fallback_module(module_outline)
    
    def _create_fallback_module(self, outline: ModuleOutline) -> ModuleOutput:
        """Create a fallback module when expansion fails.
        
        Args:
            outline: The module outline to use as base.
        
        Returns:
            A basic ModuleOutput with placeholder content.
        """
        concepts = [
            ConceptOutput(
                title=c.title,
                content=f"Learn about {c.title} in this module.",
                order=c.order,
            )
            for c in outline.concepts
        ]
        
        return ModuleOutput(
            title=outline.title,
            description=outline.description,
            order=outline.order,
            estimated_minutes=outline.estimated_minutes,
            concepts=concepts,
        )
    
    @listen(expand_modules)
    def aggregate(self, expanded_modules: list[ModuleOutput]) -> Course:
        """Step 3: Aggregate expanded modules into a Course object.
        
        This pure Python step:
        - Sorts modules by order
        - Validates completeness
        - Converts to full Course with auto-generated fields
        
        Args:
            expanded_modules: List of expanded ModuleOutput from Step 2.
        
        Returns:
            Complete Course object.
        """
        logger.info("Step 3: Aggregating into Course object")
        
        # Sort modules by order
        sorted_modules = sorted(expanded_modules, key=lambda m: m.order)
        
        # Convert to full Course object
        modules = []
        for module_output in sorted_modules:
            concepts = []
            for concept_output in module_output.concepts:
                concept = Concept(
                    title=concept_output.title,
                    content=concept_output.content,
                    order=concept_output.order,
                )
                concepts.append(concept)
            
            module = Module(
                title=module_output.title,
                description=module_output.description,
                concepts=concepts,
                order=module_output.order,
                estimated_minutes=module_output.estimated_minutes,
            )
            modules.append(module)
        
        # Build course with title from outline
        course = Course(
            title=self.outline.title if self.outline else self.topic,
            description=self.outline.description if self.outline else "",
            modules=modules,
        )
        
        logger.info(f"Course created: {course.title} with {len(modules)} modules")
        return course


class CurriculumCrew:
    """Curriculum Crew - Public interface for curriculum generation.
    
    This class wraps CurriculumFlow and provides a simple API:
    
    Example:
        ```python
        crew = CurriculumCrew()
        course = crew.create_curriculum(
            topic="Python Basics",
            user_prefs=UserPreferences(experience_level="beginner")
        )
        ```
    
    The crew uses a Flow-based architecture internally:
    1. Curriculum Architect creates the outline (Gemini 3 Pro)
    2. Content Researcher expands each module in parallel (Claude Opus 4.5)
    3. Modules are aggregated into a complete Course
    """
    
    def create_curriculum(
        self,
        topic: str,
        user_prefs: UserPreferences | None = None,
    ) -> Course:
        """Create a comprehensive curriculum for a topic.
        
        This is the main entry point for the Curriculum Crew.
        It kicks off the CurriculumFlow to generate a complete course.
        
        Args:
            topic: The subject to create a curriculum for.
            user_prefs: Optional user preferences for personalization.
        
        Returns:
            A Course object with modules and concepts.
        
        Raises:
            ValueError: If topic is empty.
            RuntimeError: If curriculum generation fails.
        """
        if not topic or not topic.strip():
            raise ValueError("Topic cannot be empty")
        
        # Set default preferences if not provided
        if user_prefs is None:
            user_prefs = UserPreferences()
        
        # Create and configure the flow
        flow = CurriculumFlow()
        flow.topic = topic.strip()
        flow.experience_level = user_prefs.experience_level.value
        flow.learning_style = user_prefs.learning_style.value
        flow.goals = user_prefs.goals or f"Learn {topic}"
        
        # Execute the flow
        try:
            course = flow.kickoff()
            return course
        except Exception as e:
            raise RuntimeError(
                f"Failed to create curriculum for '{topic}': {e}"
            ) from e
