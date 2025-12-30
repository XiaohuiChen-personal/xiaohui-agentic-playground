"""
Smart Shopping Assistant Crew

A multi-agent crew for product search, review analysis, and shopping recommendations.
Uses the Real-Time Product Search API via RapidAPI for product data.

Agents:
    - Concierge: Orchestrates requests and synthesizes responses
    - Product Specialist: Searches products and compares prices
    - Review Analyst: Analyzes customer reviews and sentiment
"""

from typing import List

from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task

from smart_shopping_assistant.tools.custom_tool import (
    search_products_tool,
    get_product_details_tool,
    get_product_reviews_tool,
    analyze_sentiment_tool,
)


@CrewBase
class SmartShoppingAssistantCrew:
    """
    Smart Shopping Assistant Crew
    
    A multi-agent system for helping users find, compare, and research products.
    
    Architecture:
        - Concierge Agent: Main orchestrator, synthesizes responses
        - Product Specialist: Product search and price comparison
        - Review Analyst: Review fetching and sentiment analysis
    
    The Flow (in main.py) determines which tasks to run based on user intent.
    """

    agents: List[BaseAgent]
    tasks: List[Task]

    # YAML configuration files
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    # ==================== AGENTS ====================

    @agent
    def concierge(self) -> Agent:
        """
        Shopping Assistant Concierge
        
        The main orchestrator that synthesizes information from specialists
        and presents it to users in a friendly, helpful manner.
        """
        return Agent(
            config=self.agents_config["concierge"],  # type: ignore[index]
            verbose=True,
        )

    @agent
    def product_specialist(self) -> Agent:
        """
        Product Search Specialist
        
        Expert at finding and comparing products across multiple retailers.
        Has access to search_products and get_product_details tools.
        """
        return Agent(
            config=self.agents_config["product_specialist"],  # type: ignore[index]
            tools=[search_products_tool, get_product_details_tool],
            verbose=True,
        )

    @agent
    def review_analyst(self) -> Agent:
        """
        Review Analysis Specialist
        
        Expert at analyzing customer reviews and extracting sentiment insights.
        Has access to search_products, get_product_reviews, and analyze_sentiment tools.
        """
        return Agent(
            config=self.agents_config["review_analyst"],  # type: ignore[index]
            tools=[search_products_tool, get_product_reviews_tool, analyze_sentiment_tool],
            verbose=True,
        )

    # ==================== TASKS ====================

    @task
    def classify_intent_task(self) -> Task:
        """
        Classify user intent to determine which specialist to route to.
        
        This replaces the Concierge's dynamic handoff decision from the OpenAI SDK.
        The Concierge agent analyzes the user query and determines:
        - product_search: Route to Product Specialist
        - review_analysis: Route to Review Analyst
        - general: No specialist needed (respond directly)
        
        Note: Just like in OpenAI SDK, only ONE specialist is routed to at a time.
        If a request involves both products AND reviews, product_search is prioritized.
        """
        return Task(
            config=self.tasks_config["classify_intent_task"],  # type: ignore[index]
        )

    @task
    def search_products_task(self) -> Task:
        """
        Search for products matching user criteria.
        
        Uses the Product Specialist to search across multiple retailers
        and return products with prices, ratings, and store information.
        """
        return Task(
            config=self.tasks_config["search_products_task"],  # type: ignore[index]
        )

    @task
    def get_product_details_task(self) -> Task:
        """
        Get detailed specifications and price comparison for a specific product.
        
        Uses the Product Specialist to retrieve full specs, all prices,
        and availability information.
        """
        return Task(
            config=self.tasks_config["get_product_details_task"],  # type: ignore[index]
        )

    @task
    def analyze_reviews_task(self) -> Task:
        """
        Analyze customer reviews for a product.
        
        Uses the Review Analyst to fetch reviews, analyze sentiment,
        and extract pros, cons, and red flags.
        """
        return Task(
            config=self.tasks_config["analyze_reviews_task"],  # type: ignore[index]
        )

    @task
    def synthesize_response_task(self) -> Task:
        """
        Synthesize specialist findings into a user-friendly response.
        
        Uses the Concierge to organize information and provide
        clear recommendations to the user.
        """
        return Task(
            config=self.tasks_config["synthesize_response_task"],  # type: ignore[index]
        )

    # ==================== CREW ====================

    @crew
    def crew(self) -> Crew:
        """
        Creates the Smart Shopping Assistant Crew
        
        The crew uses a sequential process by default, but the Flow
        in main.py determines which specific tasks to run based on
        user intent (product_search or review_analysis). Just like
        the OpenAI SDK, only one specialist handles each request.
        """
        return Crew(
            agents=self.agents,  # Automatically created by the @agent decorator
            tasks=self.tasks,  # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
        )
