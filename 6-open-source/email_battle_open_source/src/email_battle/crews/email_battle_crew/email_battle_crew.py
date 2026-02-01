"""Email Battle Crew using local open-source LLMs via vLLM.

Models:
- Elon Musk: Qwen3-32B (port 8001) - Strong reasoning and analysis
- John Smith: Mistral-Small-24B (port 8000) - General tasks and language
"""

from typing import List

from crewai import Agent, Crew, LLM, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task


# Local vLLM server configurations
# With 32K context, we can use higher max_tokens for fuller responses

QWEN_LLM = LLM(
    model="openai/nvidia/Qwen3-32B-NVFP4",
    base_url="http://localhost:8001/v1",
    api_key="EMPTY",
    temperature=0.7,
    max_tokens=2048,  # Increased with 32K context support
    # Disable Qwen3's thinking mode for faster responses
    extra_body={"chat_template_kwargs": {"enable_thinking": False}},
)

MISTRAL_LLM = LLM(
    model="openai/RedHatAI/Mistral-Small-3.2-24B-Instruct-2506-NVFP4",
    base_url="http://localhost:8000/v1",
    api_key="EMPTY",
    temperature=0.7,
    max_tokens=2048,  # Increased with 32K context support
)


@CrewBase
class EmailBattleCrew:
    """Email Battle Crew - Using local open-source LLMs.
    
    Simulates email exchanges between:
    - Elon Musk (DOGE) using Qwen3-32B
    - John Smith (USCIS) using Mistral-Small-24B
    """

    agents: List[BaseAgent]
    tasks: List[Task]

    # YAML configuration files
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    # ==================== AGENTS ====================

    @agent
    def elon_musk(self) -> Agent:
        """Head of Department of Government Efficiency (DOGE).
        
        Uses Qwen3-32B for strong reasoning and probing questions.
        """
        return Agent(
            config=self.agents_config["elon_musk"],  # type: ignore[index]
            llm=QWEN_LLM,
            verbose=False,  # Disabled for faster execution
        )

    @agent
    def john_smith(self) -> Agent:
        """GS-12 Immigration Services Officer at USCIS.
        
        Uses Mistral-Small-24B for bureaucratic language generation.
        """
        return Agent(
            config=self.agents_config["john_smith"],  # type: ignore[index]
            llm=MISTRAL_LLM,
            verbose=False,  # Disabled for faster execution
        )

    # ==================== TASKS ====================

    @task
    def send_mass_email(self) -> Task:
        """Elon sends mass email requesting 5 accomplishments."""
        return Task(
            config=self.tasks_config["send_mass_email"],  # type: ignore[index]
        )

    @task
    def reply_to_mass_email(self) -> Task:
        """John replies to the mass email with his 'accomplishments'."""
        return Task(
            config=self.tasks_config["reply_to_mass_email"],  # type: ignore[index]
        )

    @task
    def evaluate_initial_response(self) -> Task:
        """Elon evaluates John's response and decides: PASS or FOLLOW-UP."""
        return Task(
            config=self.tasks_config["evaluate_initial_response"],  # type: ignore[index]
        )

    @task
    def john_follow_up_response(self) -> Task:
        """John responds to Elon's follow-up questions."""
        return Task(
            config=self.tasks_config["john_follow_up_response"],  # type: ignore[index]
        )

    @task
    def elon_follow_up_evaluation(self) -> Task:
        """Elon evaluates follow-up and decides: FOLLOW-UP, TERMINATED, or RETAINED."""
        return Task(
            config=self.tasks_config["elon_follow_up_evaluation"],  # type: ignore[index]
        )

    # ==================== CREW ====================

    @crew
    def crew(self) -> Crew:
        """Creates the Email Battle Crew."""
        return Crew(
            agents=self.agents,  # Automatically created by the @agent decorator
            tasks=self.tasks,  # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=False,  # Disabled for faster execution
        )
