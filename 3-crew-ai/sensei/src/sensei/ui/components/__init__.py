"""Reusable UI components for Sensei.

This module provides Streamlit UI components for building the Sensei interface.

Components:
- sidebar: Navigation sidebar with page links and course outline
- course_card: Course display cards with progress and actions
- concept_viewer: Lesson content display with markdown and code
- chat_interface: Q&A chat interface with message history
- quiz_question: Quiz question display with answer options and feedback
"""

from sensei.ui.components.sidebar import (
    render_sidebar,
    render_simple_sidebar,
    render_learning_sidebar,
)
from sensei.ui.components.course_card import (
    render_course_card,
    render_course_card_compact,
    render_empty_course_state,
)
from sensei.ui.components.concept_viewer import (
    render_concept,
    render_concept_with_navigation,
    render_lesson_header,
    render_loading_state,
    render_concept_card,
)
from sensei.ui.components.chat_interface import (
    render_chat,
    render_chat_compact,
    render_typing_indicator,
    render_chat_error,
    render_chat_with_form,
)
from sensei.ui.components.quiz_question import (
    render_question,
    render_quiz_progress,
    render_quiz_results,
    render_question_review,
    render_quiz_header,
    render_quiz_intro,
)

__all__ = [
    # Sidebar
    "render_sidebar",
    "render_simple_sidebar",
    "render_learning_sidebar",
    # Course Card
    "render_course_card",
    "render_course_card_compact",
    "render_empty_course_state",
    # Concept Viewer
    "render_concept",
    "render_concept_with_navigation",
    "render_lesson_header",
    "render_loading_state",
    "render_concept_card",
    # Chat Interface
    "render_chat",
    "render_chat_compact",
    "render_typing_indicator",
    "render_chat_error",
    "render_chat_with_form",
    # Quiz Question
    "render_question",
    "render_quiz_progress",
    "render_quiz_results",
    "render_question_review",
    "render_quiz_header",
    "render_quiz_intro",
]
