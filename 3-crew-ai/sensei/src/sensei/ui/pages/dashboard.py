"""Dashboard page for Sensei.

This module provides the main dashboard showing:
- Welcome message with user name
- Quick stats cards (courses, concepts, hours)
- Course list with progress
- New course button
"""

from typing import Any, Callable

import streamlit as st

from sensei.models.schemas import Progress
from sensei.ui.components import render_course_card, render_empty_course_state, render_sidebar
from sensei.utils.formatters import format_duration


def render_dashboard(
    user_name: str = "Learner",
    courses: list[dict[str, Any]] | None = None,
    progress_map: dict[str, Progress] | None = None,
    stats: dict[str, Any] | None = None,
    current_page: str = "dashboard",
    on_navigate: Callable[[str], None] | None = None,
    on_continue_course: Callable[[str], None] | None = None,
    on_review_course: Callable[[str], None] | None = None,
    on_delete_course: Callable[[str], None] | None = None,
    on_new_course: Callable[[], None] | None = None,
    show_delete: bool = False,
) -> None:
    """Render the main dashboard page.
    
    Args:
        user_name: User's display name for welcome message.
        courses: List of course dictionaries.
        progress_map: Dict mapping course_id to Progress objects.
        stats: Learning statistics dict with total_courses, concepts_mastered, hours_learned.
        current_page: Current page for sidebar highlighting.
        on_navigate: Callback for sidebar navigation.
        on_continue_course: Callback when Continue is clicked on a course.
        on_review_course: Callback when Review is clicked on a course.
        on_delete_course: Callback when Delete is clicked on a course.
        on_new_course: Callback when New Course button is clicked.
        show_delete: Whether to show delete buttons on course cards.
    
    Example:
        ```python
        render_dashboard(
            user_name="Xiaohui",
            courses=course_service.list_courses(),
            progress_map=progress_service.get_all_progress_map(),
            stats=progress_service.get_learning_stats(),
            on_continue_course=lambda cid: navigate_to_learning(cid),
            on_new_course=lambda: navigate_to_new_course(),
        )
        ```
    """
    courses = courses or []
    progress_map = progress_map or {}
    stats = stats or {"total_courses": 0, "concepts_mastered": 0, "hours_learned": 0}
    
    # Render sidebar
    render_sidebar(current_page=current_page, on_navigate=on_navigate)
    
    # Main content area
    _render_header(user_name)
    _render_stats_row(stats)
    _render_courses_section(
        courses=courses,
        progress_map=progress_map,
        on_continue=on_continue_course,
        on_review=on_review_course,
        on_delete=on_delete_course,
        on_new_course=on_new_course,
        show_delete=show_delete,
    )


def _render_header(user_name: str) -> None:
    """Render the welcome header.
    
    Args:
        user_name: User's display name.
    """
    st.markdown(
        f"""
        <div style="
            padding: 1.5rem 0;
            margin-bottom: 1rem;
        ">
            <h1 style="margin: 0; font-size: 2rem;">
                👋 Welcome back, {user_name}!
            </h1>
            <p style="color: #666; margin-top: 0.5rem;">
                Continue your learning journey
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_stats_row(stats: dict[str, Any]) -> None:
    """Render the quick stats cards row.
    
    Args:
        stats: Dictionary with total_courses, concepts_mastered, hours_learned.
    """
    col1, col2, col3 = st.columns(3)
    
    with col1:
        _render_stat_card(
            icon="📚",
            value=str(stats.get("total_courses", 0)),
            label="Courses",
        )
    
    with col2:
        _render_stat_card(
            icon="💡",
            value=str(stats.get("concepts_mastered", 0)),
            label="Concepts Mastered",
        )
    
    with col3:
        hours = stats.get("hours_learned", 0)
        # Format as hours with one decimal
        if isinstance(hours, (int, float)):
            hours_display = f"{hours:.1f}"
        else:
            hours_display = str(hours)
        _render_stat_card(
            icon="⏱️",
            value=hours_display,
            label="Hours Learned",
        )
    
    st.markdown("<br>", unsafe_allow_html=True)


def _render_stat_card(icon: str, value: str, label: str) -> None:
    """Render a single stat card.
    
    Args:
        icon: Emoji icon for the stat.
        value: The statistic value.
        label: Label describing the stat.
    """
    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border-radius: 10px;
            padding: 1.25rem;
            text-align: center;
            border: 1px solid #dee2e6;
        ">
            <div style="font-size: 1.5rem; margin-bottom: 0.25rem;">{icon}</div>
            <div style="font-size: 1.75rem; font-weight: 600; color: #212529;">{value}</div>
            <div style="font-size: 0.85rem; color: #6c757d;">{label}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_courses_section(
    courses: list[dict[str, Any]],
    progress_map: dict[str, Progress],
    on_continue: Callable[[str], None] | None,
    on_review: Callable[[str], None] | None,
    on_delete: Callable[[str], None] | None,
    on_new_course: Callable[[], None] | None,
    show_delete: bool,
) -> None:
    """Render the courses section with header and course cards.
    
    Args:
        courses: List of course dictionaries.
        progress_map: Dict mapping course_id to Progress.
        on_continue: Continue callback.
        on_review: Review callback.
        on_delete: Delete callback.
        on_new_course: New course callback.
        show_delete: Whether to show delete buttons.
    """
    # Section header with New Course button
    col1, col2 = st.columns([0.7, 0.3])
    
    with col1:
        st.markdown("### My Courses")
    
    with col2:
        if on_new_course:
            if st.button("➕ New Course", key="dashboard_new_course", use_container_width=True):
                on_new_course()
    
    st.markdown("<hr style='margin: 0.5rem 0 1rem 0;'>", unsafe_allow_html=True)
    
    # Empty state or course list
    if not courses:
        render_empty_course_state(on_create=on_new_course)
    else:
        # Render course cards
        for course in courses:
            course_id = course.get("id", "")
            progress = progress_map.get(course_id)
            
            render_course_card(
                course=course,
                progress=progress,
                on_continue=on_continue,
                on_review=on_review,
                on_delete=on_delete,
                show_delete=show_delete,
            )


def render_dashboard_page(
    user_service,
    course_service,
    progress_service,
    on_navigate: Callable[[str], None] | None = None,
    on_continue_course: Callable[[str], None] | None = None,
    on_review_course: Callable[[str], None] | None = None,
    on_new_course: Callable[[], None] | None = None,
) -> None:
    """Convenience function to render the dashboard with service integration.
    
    This function handles all the data loading from services and renders
    the dashboard with proper callbacks.
    
    Args:
        user_service: UserService instance for user preferences.
        course_service: CourseService instance for course data.
        progress_service: ProgressService instance for progress data.
        on_navigate: Navigation callback.
        on_continue_course: Continue course callback.
        on_review_course: Review course callback (for completed courses).
        on_new_course: New course callback.
    
    Example:
        ```python
        from sensei.services import UserService, CourseService, ProgressService
        
        render_dashboard_page(
            user_service=UserService(),
            course_service=CourseService(use_ai=False),
            progress_service=ProgressService(),
            on_navigate=lambda page: set_page(page),
            on_continue_course=lambda cid: start_learning(cid),
            on_review_course=lambda cid: review_course(cid),
            on_new_course=lambda: go_to_new_course(),
        )
        ```
    """
    # Load data from services
    user_prefs = user_service.get_preferences()
    courses = course_service.list_courses()
    
    # Build progress map
    progress_map = {}
    for course in courses:
        course_id = course.get("id", "")
        if course_id:
            progress_map[course_id] = progress_service.get_course_progress(course_id)
    
    # Get learning stats
    stats = progress_service.get_learning_stats()
    stats_dict = {
        "total_courses": stats.total_courses,
        "concepts_mastered": stats.concepts_mastered,
        "hours_learned": stats.hours_learned,
    }
    
    # Render dashboard
    render_dashboard(
        user_name=user_prefs.name,
        courses=courses,
        progress_map=progress_map,
        stats=stats_dict,
        current_page="dashboard",
        on_navigate=on_navigate,
        on_continue_course=on_continue_course,
        on_review_course=on_review_course,
        on_new_course=on_new_course,
    )
