"""
LangGraph workflow definition for the Email Battle.

This module contains:
- Routing functions for conditional edges
- Graph construction and compilation
- The compiled workflow application
"""

from typing import Literal

from langgraph.graph import END, START, StateGraph

from models import BattleState
from nodes import (
    determine_outcome,
    elon_evaluate,
    generate_mass_email,
    john_followup_response,
    john_initial_response,
)


def route_after_john_initial(
    state: BattleState,
) -> Literal["determine_outcome", "elon_evaluate"]:
    """
    Route after John's initial response.
    
    Args:
        state: Current battle state
    
    Returns:
        Next node name: "determine_outcome" if refusal, "elon_evaluate" otherwise
    """
    if state.get("is_refusal", False):
        return "determine_outcome"
    return "elon_evaluate"


def route_after_elon_evaluate(
    state: BattleState,
) -> Literal["determine_outcome", "john_followup_response"]:
    """
    Route after Elon's evaluation.
    
    Args:
        state: Current battle state with elon_decision
    
    Returns:
        Next node name based on Elon's decision
    """
    decision = state.get("elon_decision")
    
    if decision == "PASS":
        return "determine_outcome"
    elif decision == "FOLLOW_UP":
        return "john_followup_response"
    elif decision in ("TERMINATED", "RETAINED"):
        return "determine_outcome"
    else:
        # Default to determine_outcome for unknown decisions
        return "determine_outcome"


def route_after_john_followup(
    state: BattleState,
) -> Literal["determine_outcome", "elon_evaluate"]:
    """
    Route after John's follow-up response.
    
    Checks for:
    1. Refusal (John broke character)
    2. Max rounds reached
    3. Continue to Elon's evaluation
    
    Args:
        state: Current battle state
    
    Returns:
        Next node name
    """
    # Check for refusal
    if state.get("is_refusal", False):
        return "determine_outcome"
    
    # Check for max rounds
    if state["follow_up_round"] >= state["max_follow_up_rounds"]:
        return "determine_outcome"
    
    # Continue the loop
    return "elon_evaluate"


def create_email_battle_graph() -> StateGraph:
    """
    Create the Email Battle LangGraph workflow.
    
    Graph structure:
    
    START → generate_mass_email → john_initial_response
         → [route] → elon_evaluate ↔ john_followup_response (loop)
         → determine_outcome → END
    
    Returns:
        Compiled StateGraph application
    """
    # Create the graph with our state schema
    graph = StateGraph(BattleState)
    
    # Add all nodes
    graph.add_node("generate_mass_email", generate_mass_email)
    graph.add_node("john_initial_response", john_initial_response)
    graph.add_node("elon_evaluate", elon_evaluate)
    graph.add_node("john_followup_response", john_followup_response)
    graph.add_node("determine_outcome", determine_outcome)
    
    # Add edges
    # START → generate_mass_email
    graph.add_edge(START, "generate_mass_email")
    
    # generate_mass_email → john_initial_response (always)
    graph.add_edge("generate_mass_email", "john_initial_response")
    
    # john_initial_response → conditional routing
    graph.add_conditional_edges(
        "john_initial_response",
        route_after_john_initial,
        {
            "determine_outcome": "determine_outcome",
            "elon_evaluate": "elon_evaluate",
        }
    )
    
    # elon_evaluate → conditional routing
    graph.add_conditional_edges(
        "elon_evaluate",
        route_after_elon_evaluate,
        {
            "determine_outcome": "determine_outcome",
            "john_followup_response": "john_followup_response",
        }
    )
    
    # john_followup_response → conditional routing (can loop back)
    graph.add_conditional_edges(
        "john_followup_response",
        route_after_john_followup,
        {
            "determine_outcome": "determine_outcome",
            "elon_evaluate": "elon_evaluate",
        }
    )
    
    # determine_outcome → END
    graph.add_edge("determine_outcome", END)
    
    return graph


def compile_graph():
    """
    Create and compile the Email Battle graph.
    
    Returns:
        Compiled LangGraph application ready to run
    """
    graph = create_email_battle_graph()
    return graph.compile()


# Create the compiled application
# This can be imported and used directly
email_battle_app = compile_graph()

