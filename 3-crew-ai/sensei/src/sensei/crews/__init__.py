"""CrewAI crews for Sensei.

This module provides the AI crews that power Sensei's learning features:
- CurriculumCrew: Creates course structures and curricula
- TeachingCrew: Delivers lessons and answers questions
- AssessmentCrew: Creates and evaluates quizzes
"""

from sensei.crews.assessment_crew import AssessmentCrew
from sensei.crews.curriculum_crew import CurriculumCrew
from sensei.crews.teaching_crew import TeachingCrew

__all__ = [
    "AssessmentCrew",
    "CurriculumCrew",
    "TeachingCrew",
]
