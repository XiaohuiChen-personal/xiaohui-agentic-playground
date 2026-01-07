"""
Email Battle - LangGraph Implementation

A multi-agent simulation demonstrating LangGraph workflows
where Elon Musk (DOGE) conducts an efficiency review of
John Smith, a coasting government employee.
"""

from .models import BattleResult, BattleState, Email, ElonDecision
from .graph import email_battle_app, create_email_battle_graph

__all__ = [
    "BattleResult",
    "BattleState", 
    "Email",
    "ElonDecision",
    "email_battle_app",
    "create_email_battle_graph",
]

