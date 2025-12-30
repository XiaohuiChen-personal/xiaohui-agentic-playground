#!/usr/bin/env python
"""
Smart Shopping Assistant Flow

A multi-agent shopping assistant that helps users find, compare, and research products.
Uses CrewAI Flow to orchestrate between specialists based on user intent.

Flow Architecture:
    1. receive_user_query: Entry point, stores user query in state
    2. classify_intent: Concierge agent analyzes query and decides routing (LLM-based)
    3. Route to ONE specialist: Product Specialist OR Review Analyst
    4. synthesize_response: Concierge combines results into user-friendly response
    5. save_results: Persist results to output file

Mapping from OpenAI SDK Handoffs:
    - Concierge routing → Concierge runs classify_intent_task (LLM decides)
    - transfer_to_product_specialist → return "product_search"
    - transfer_to_review_analyst → return "review_analysis"
    - Specialist results → state.product_results / state.review_results
    - Concierge synthesis → synthesize_response step

Note: Just like the OpenAI SDK, only ONE specialist handles each request.
If a request mentions both products and reviews, product_search is prioritized.
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Literal, Optional

from dotenv import load_dotenv
from pydantic import BaseModel

from crewai import Crew, Process
from crewai.flow import Flow, listen, or_, router, start

from smart_shopping_assistant.crews.smart_shopping_assistant_crew.smart_shopping_assistant_crew import (
    SmartShoppingAssistantCrew,
)

# Load .env from workspace root (4 levels up from this file)
root_env_path = Path(__file__).resolve().parents[4] / ".env"
load_dotenv(root_env_path)

# Output directory for results
OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


# =============================================================================
# State Model
# =============================================================================

class ShoppingAssistantState(BaseModel):
    """
    State for the Smart Shopping Assistant Flow.
    
    This replaces the conversation context that was maintained through
    handoffs in the OpenAI SDK version.
    """
    
    # User input
    user_query: str = ""
    
    # Intent classification (determined by Concierge agent, just like OpenAI SDK)
    # - product_search: User wants to find/compare products (→ Product Specialist)
    # - review_analysis: User wants to understand reviews/sentiment (→ Review Analyst)
    # - general: General question, no specialist needed
    # NOTE: No "both" option - OpenAI SDK handles one specialist at a time
    intent: Literal["product_search", "review_analysis", "general"] = "general"
    
    # Concierge's reasoning for the classification
    intent_reasoning: str = ""
    
    # Extracted parameters from user query (by Concierge)
    product_name: Optional[str] = None
    product_id: Optional[str] = None  # If provided from previous search
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    focus_area: Optional[str] = None  # For review analysis (e.g., "battery", "comfort")
    
    # Results from specialists (replaces handoff return values)
    product_results: str = ""
    review_results: str = ""
    
    # Final synthesized response
    final_response: str = ""
    
    # Metadata
    timestamp: str = ""


# =============================================================================
# Intent Parsing Helper
# =============================================================================

def parse_concierge_intent(response: str) -> dict:
    """
    Parse the Concierge agent's intent classification response.
    
    The Concierge outputs a JSON response with intent and parameters.
    This function extracts and validates that JSON.
    
    Args:
        response: Raw response from Concierge's classify_intent_task
        
    Returns:
        dict with 'intent', 'reasoning', and 'parameters'
    """
    result = {
        "intent": "general",
        "reasoning": "",
        "parameters": {
            "price_min": None,
            "price_max": None,
            "focus_area": None,
        }
    }
    
    # Try to extract JSON from the response
    # The response might have markdown code blocks or extra text
    json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
    if json_match:
        json_str = json_match.group(1)
    else:
        # Try to find raw JSON object
        json_match = re.search(r'\{[^{}]*"intent"[^{}]*\}', response, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
        else:
            # Fallback: try the whole response
            json_str = response
    
    try:
        parsed = json.loads(json_str)
        
        # Extract intent
        intent = parsed.get("intent", "general").lower()
        if intent in ["product_search", "review_analysis", "general"]:
            result["intent"] = intent
        elif intent == "both":
            # OpenAI SDK handles one specialist at a time
            # If "both" is returned, prioritize product_search first
            result["intent"] = "product_search"
        
        # Extract reasoning
        result["reasoning"] = parsed.get("reasoning", "")
        
        # Extract parameters
        params = parsed.get("parameters", {})
        if params:
            result["parameters"]["price_min"] = params.get("price_min")
            result["parameters"]["price_max"] = params.get("price_max")
            result["parameters"]["focus_area"] = params.get("focus_area")
            
    except json.JSONDecodeError:
        # If JSON parsing fails, try to extract intent from text
        response_lower = response.lower()
        if "product_search" in response_lower:
            result["intent"] = "product_search"
        elif "review_analysis" in response_lower:
            result["intent"] = "review_analysis"
        elif "both" in response_lower:
            # OpenAI SDK handles one specialist at a time - prioritize product_search
            result["intent"] = "product_search"
        
        result["reasoning"] = "Extracted from text (JSON parsing failed)"
    
    return result


# =============================================================================
# Smart Shopping Assistant Flow
# =============================================================================

class SmartShoppingAssistantFlow(Flow[ShoppingAssistantState]):
    """
    Flow that orchestrates the Smart Shopping Assistant.
    
    This replicates the OpenAI SDK's dynamic routing pattern:
    - Concierge agent analyzes user intent (LLM-based, not rule-based)
    - Routes to appropriate specialist(s) based on Concierge's decision
    - Specialists execute their tasks with tools
    - Concierge synthesizes the final response
    """

    def __init__(self):
        super().__init__()
        self._crew = SmartShoppingAssistantCrew()

    # ==================== STEP 1: RECEIVE USER QUERY ====================

    @start()
    def receive_user_query(self, user_query: str = None):
        """
        Entry point - receive and store the user's query.
        
        In OpenAI SDK, this was handled by the Concierge agent receiving
        the user message. Here, we explicitly store it in state.
        """
        print("\n" + "=" * 60)
        print("🛒 SMART SHOPPING ASSISTANT")
        print("=" * 60)
        
        # Handle input from different sources
        if user_query:
            self.state.user_query = user_query
        
        self.state.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        print(f"\n👤 USER QUERY:")
        print(f"   {self.state.user_query}")
        print()

    # ==================== STEP 2: CONCIERGE CLASSIFIES INTENT ====================

    @listen(receive_user_query)
    def concierge_classifies_intent(self):
        """
        Concierge agent analyzes the query and decides which specialist to route to.
        
        This is the KEY DIFFERENCE from rule-based classification:
        - In OpenAI SDK: Concierge agent analyzed intent and called transfer_to_*
        - In CrewAI Flow: Concierge runs classify_intent_task (LLM decides routing)
        
        The Concierge agent uses its understanding of the query to determine:
        - product_search: Route to Product Specialist
        - review_analysis: Route to Review Analyst  
        - general: Handle directly without specialists
        
        Note: Just like OpenAI SDK, only ONE specialist is routed at a time.
        """
        print("=" * 60)
        print("🎯 CONCIERGE: Analyzing user intent...")
        print("=" * 60)
        
        # Run the Concierge's classify_intent_task
        # This is the LLM-based classification, just like in OpenAI SDK
        result = Crew(
            agents=[self._crew.concierge()],
            tasks=[self._crew.classify_intent_task()],
            process=Process.sequential,
            verbose=True,
        ).kickoff(inputs={
            "user_query": self.state.user_query,
        })
        
        # Parse the Concierge's response
        classification = parse_concierge_intent(result.raw)
        
        # Update state with Concierge's decision
        self.state.intent = classification["intent"]
        self.state.intent_reasoning = classification["reasoning"]
        self.state.price_min = classification["parameters"]["price_min"]
        self.state.price_max = classification["parameters"]["price_max"]
        self.state.focus_area = classification["parameters"]["focus_area"]
        
        print(f"\n✅ Concierge Decision:")
        print(f"   Intent: {self.state.intent}")
        print(f"   Reasoning: {self.state.intent_reasoning}")
        if self.state.price_max:
            print(f"   Max Price: ${self.state.price_max}")
        if self.state.price_min:
            print(f"   Min Price: ${self.state.price_min}")
        if self.state.focus_area:
            print(f"   Focus Area: {self.state.focus_area}")
        print()

    # ==================== STEP 3: ROUTER BASED ON CONCIERGE DECISION ====================

    @router(concierge_classifies_intent)
    def route_to_specialist(self) -> str:
        """
        Route to the appropriate specialist based on Concierge's intent classification.
        
        This is where the Concierge's LLM decision gets translated into flow routing.
        """
        print(f"🔀 Routing to: {self.state.intent}")
        return self.state.intent

    # ==================== STEP 4A: PRODUCT SEARCH ====================

    @listen("product_search")
    def execute_product_search(self):
        """
        Execute product search using the Product Specialist.
        
        This replaces: Concierge → transfer_to_product_specialist → search_products
        """
        print("=" * 60)
        print("🔍 PRODUCT SPECIALIST: Searching products...")
        print("=" * 60)
        
        # Run the product search task
        result = Crew(
            agents=[self._crew.product_specialist()],
            tasks=[self._crew.search_products_task()],
            process=Process.sequential,
            verbose=True,
        ).kickoff(inputs={
            "user_query": self.state.user_query,
        })
        
        self.state.product_results = result.raw
        print(f"\n✅ Product search complete")

    # ==================== STEP 4B: REVIEW ANALYSIS ====================

    @listen("review_analysis")
    def execute_review_analysis(self):
        """
        Execute review analysis using the Review Analyst.
        
        This replaces: Concierge → transfer_to_review_analyst → analyze reviews
        """
        print("=" * 60)
        print("⭐ REVIEW ANALYST: Analyzing reviews...")
        print("=" * 60)
        
        # Run the review analysis task
        result = Crew(
            agents=[self._crew.review_analyst()],
            tasks=[self._crew.analyze_reviews_task()],
            process=Process.sequential,
            verbose=True,
        ).kickoff(inputs={
            "product_name": self.state.user_query,  # Extract product from query
            "product_id": self.state.product_id or "",
            "focus_area": self.state.focus_area or "general",
        })
        
        self.state.review_results = result.raw
        print(f"\n✅ Review analysis complete")

    # ==================== STEP 4C: GENERAL (NO SPECIALIST) ====================

    @listen("general")
    def handle_general_query(self):
        """
        Handle general queries that don't need specialists.
        
        In OpenAI SDK, Concierge would respond directly without handoffs.
        """
        print("=" * 60)
        print("💬 GENERAL QUERY: No specialist needed")
        print("=" * 60)
        
        self.state.final_response = (
            "I'm your Smart Shopping Assistant! I can help you:\n\n"
            "🔍 **Find Products**: Tell me what you're looking for, including any "
            "budget constraints (e.g., 'Find me wireless headphones under $100')\n\n"
            "⭐ **Analyze Reviews**: Ask about what customers say about a product "
            "(e.g., 'What do reviews say about the Sony WH-1000XM4?')\n\n"
            "📊 **Compare Prices**: I can show you prices from different stores\n\n"
            "What would you like to explore today?"
        )

    # ==================== STEP 4D: SYNTHESIZE RESPONSE ====================

    @listen(or_(execute_product_search, execute_review_analysis))
    def synthesize_response(self):
        """
        Synthesize specialist results into a user-friendly response.
        
        This replaces: Specialist → transfer_to_concierge → Concierge synthesis
        
        In OpenAI SDK, specialists would hand back to Concierge with their
        results in the conversation context. The Concierge would then
        synthesize and present to the user.
        """
        print("\n" + "=" * 60)
        print("🎯 CONCIERGE: Synthesizing response...")
        print("=" * 60)
        
        # Prepare specialist results for synthesis
        specialist_results = []
        
        if self.state.product_results:
            specialist_results.append(
                f"## Product Search Results\n\n{self.state.product_results}"
            )
        
        if self.state.review_results:
            specialist_results.append(
                f"## Review Analysis Results\n\n{self.state.review_results}"
            )
        
        combined_results = "\n\n---\n\n".join(specialist_results)
        
        # Run the synthesis task
        result = Crew(
            agents=[self._crew.concierge()],
            tasks=[self._crew.synthesize_response_task()],
            process=Process.sequential,
            verbose=True,
        ).kickoff(inputs={
            "user_query": self.state.user_query,
            "specialist_results": combined_results,
        })
        
        self.state.final_response = result.raw
        print(f"\n✅ Response synthesized")

    # ==================== STEP 5: SAVE RESULTS ====================

    @listen(or_(synthesize_response, handle_general_query))
    def save_results(self):
        """
        Save the results to the output directory.
        """
        print("\n" + "=" * 60)
        print("💾 Saving results...")
        print("=" * 60)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = OUTPUT_DIR / f"shopping_result_{timestamp}.txt"
        
        # Write results
        with open(output_file, "w") as f:
            f.write("=" * 60 + "\n")
            f.write("SMART SHOPPING ASSISTANT RESULTS\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Timestamp: {self.state.timestamp}\n")
            f.write(f"Intent: {self.state.intent}\n")
            f.write(f"Concierge Reasoning: {self.state.intent_reasoning}\n")
            f.write(f"Query: {self.state.user_query}\n\n")
            f.write("-" * 60 + "\n")
            f.write("RESPONSE:\n")
            f.write("-" * 60 + "\n\n")
            f.write(self.state.final_response)
            
            if self.state.product_results:
                f.write("\n\n" + "-" * 60 + "\n")
                f.write("RAW PRODUCT RESULTS:\n")
                f.write("-" * 60 + "\n\n")
                f.write(self.state.product_results)
            
            if self.state.review_results:
                f.write("\n\n" + "-" * 60 + "\n")
                f.write("RAW REVIEW RESULTS:\n")
                f.write("-" * 60 + "\n\n")
                f.write(self.state.review_results)
        
        print(f"   Saved to: {output_file}")
        
        # Print final response
        print("\n" + "=" * 60)
        print("🤖 FINAL RESPONSE:")
        print("=" * 60)
        print(self.state.final_response)
        print("\n" + "=" * 60)


# =============================================================================
# Entry Points
# =============================================================================

def kickoff(user_query: str = None):
    """
    Run the Smart Shopping Assistant with a user query.
    
    Args:
        user_query: The user's shopping question/request.
                   If not provided, uses a default test query.
    """
    if user_query is None:
        # Default test query
        user_query = "Find me wireless headphones under $100 with good reviews"
    
    print("\n" + "🚀" * 20)
    print("STARTING SMART SHOPPING ASSISTANT")
    print("🚀" * 20 + "\n")
    
    flow = SmartShoppingAssistantFlow()
    flow.kickoff(inputs={"user_query": user_query})
    
    return flow.state


def plot():
    """Generate a visual plot of the flow."""
    flow = SmartShoppingAssistantFlow()
    flow.plot()


def run_with_trigger():
    """
    Run the flow with trigger payload from command line.
    
    Usage:
        python main.py '{"user_query": "Find laptops under $1000"}'
    """
    if len(sys.argv) < 2:
        raise Exception(
            "No trigger payload provided. "
            "Usage: python main.py '{\"user_query\": \"your query here\"}'"
        )
    
    try:
        trigger_payload = json.loads(sys.argv[1])
    except json.JSONDecodeError:
        raise Exception("Invalid JSON payload provided as argument")
    
    user_query = trigger_payload.get("user_query", "")
    if not user_query:
        raise Exception("No 'user_query' found in trigger payload")
    
    return kickoff(user_query)


if __name__ == "__main__":
    # Run with default query or from command line
    if len(sys.argv) > 1:
        run_with_trigger()
    else:
        kickoff()
