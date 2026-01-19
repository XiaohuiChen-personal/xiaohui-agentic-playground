"""Streamlit page implementations for Sensei.

This module provides the page-level UI components:
- Dashboard: Main landing page with courses and stats
- New Course: Course creation page
- Learning: Active learning session page
- Quiz: Quiz assessment page
- Progress: Progress overview page
- Settings: User preferences page
- Onboarding: First-time user setup page
"""

from sensei.ui.pages.dashboard import render_dashboard, render_dashboard_page
from sensei.ui.pages.new_course import (
    render_new_course_page,
    render_new_course_with_services,
)
from sensei.ui.pages.learning import (
    render_learning_page,
    render_learning_with_services,
)
from sensei.ui.pages.quiz import (
    render_quiz_page,
    render_quiz_with_services,
)
from sensei.ui.pages.progress import (
    render_progress_page,
    render_progress_with_services,
)
from sensei.ui.pages.settings import (
    render_settings_page,
    render_settings_with_services,
)
from sensei.ui.pages.onboarding import (
    render_onboarding_page,
    render_onboarding_with_services,
)

__all__ = [
    # Dashboard
    "render_dashboard",
    "render_dashboard_page",
    # New Course
    "render_new_course_page",
    "render_new_course_with_services",
    # Learning
    "render_learning_page",
    "render_learning_with_services",
    # Quiz
    "render_quiz_page",
    "render_quiz_with_services",
    # Progress
    "render_progress_page",
    "render_progress_with_services",
    # Settings
    "render_settings_page",
    "render_settings_with_services",
    # Onboarding
    "render_onboarding_page",
    "render_onboarding_with_services",
]
