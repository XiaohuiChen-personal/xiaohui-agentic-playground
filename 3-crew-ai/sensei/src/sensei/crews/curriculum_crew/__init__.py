"""Curriculum Crew - Creates course structures and curricula.

This crew is responsible for creating comprehensive learning curricula
when a user wants to learn a new topic. It uses a Flow-based architecture
for parallel module expansion.
"""

from sensei.crews.curriculum_crew.curriculum_crew import CurriculumCrew, CurriculumFlow

__all__ = ["CurriculumCrew", "CurriculumFlow"]
