"""Progress page for Sensei.

This module provides the progress overview page with:
- Overall learning statistics
- Per-course progress bars
- Quiz history table
- Weak areas summary
"""

from typing import Any, Callable

import streamlit as st

from sensei.models.schemas import LearningStats, Progress, QuizResult
from sensei.ui.components import render_sidebar
from sensei.utils.formatters import format_date, format_percentage


def render_progress_page(
    stats: LearningStats | None = None,
    course_progress: list[dict[str, Any]] | None = None,
    quiz_history: list[QuizResult] | None = None,
    current_page: str = "progress",
    on_navigate: Callable[[str], None] | None = None,
    on_course_click: Callable[[str], None] | None = None,
) -> None:
    """Render the progress overview page.
    
    Args:
        stats: Overall learning statistics.
        course_progress: List of course progress dicts with course info and progress.
        quiz_history: List of quiz results across all courses.
        current_page: Current page for sidebar highlighting.
        on_navigate: Callback for sidebar navigation.
        on_course_click: Callback when a course is clicked.
    
    Example:
        ```python
        render_progress_page(
            stats=progress_service.get_learning_stats(),
            course_progress=progress_service.get_all_progress_with_courses(),
            quiz_history=progress_service.get_all_quiz_history(),
        )
        ```
    """
    course_progress = course_progress or []
    quiz_history = quiz_history or []
    
    # Render sidebar
    render_sidebar(current_page=current_page, on_navigate=on_navigate)
    
    # Page header
    _render_header()
    
    # Overall stats section
    _render_stats_section(stats)
    
    st.divider()
    
    # Course progress section
    _render_course_progress_section(course_progress, on_course_click)
    
    st.divider()
    
    # Quiz history section
    _render_quiz_history_section(quiz_history)


def _render_header() -> None:
    """Render the page header."""
    st.markdown(
        """
        <div style="padding: 1rem 0; margin-bottom: 0.5rem;">
            <h1 style="margin: 0; font-size: 1.75rem;">📊 Your Learning Progress</h1>
            <p style="color: #666; margin-top: 0.25rem;">
                Track your learning journey and achievements
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_stats_section(stats: LearningStats | None) -> None:
    """Render the overall statistics section.
    
    Args:
        stats: Learning statistics object.
    """
    st.markdown("### Overall Statistics")
    
    if not stats:
        stats = LearningStats()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        _render_stat_card(
            icon="📚",
            value=str(stats.total_courses),
            label="Courses",
            sublabel="enrolled",
        )
    
    with col2:
        _render_stat_card(
            icon="💡",
            value=f"{stats.concepts_mastered}/{stats.total_concepts}" if stats.total_concepts > 0 else "0",
            label="Concepts",
            sublabel="mastered",
        )
    
    with col3:
        _render_stat_card(
            icon="⏱️",
            value=f"{stats.hours_learned:.1f}",
            label="Hours",
            sublabel="learned",
        )
    
    with col4:
        streak_emoji = "🔥" if stats.current_streak > 0 else "💤"
        _render_stat_card(
            icon=streak_emoji,
            value=str(stats.current_streak),
            label="Day Streak",
            sublabel=f"Best: {stats.longest_streak}",
        )


def _render_stat_card(icon: str, value: str, label: str, sublabel: str = "") -> None:
    """Render a single stat card.
    
    Args:
        icon: Emoji icon.
        value: The statistic value.
        label: Label for the stat.
        sublabel: Secondary label.
    """
    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border-radius: 10px;
            padding: 1rem;
            text-align: center;
            border: 1px solid #dee2e6;
        ">
            <div style="font-size: 1.25rem;">{icon}</div>
            <div style="font-size: 1.5rem; font-weight: 600; color: #212529;">{value}</div>
            <div style="font-size: 0.9rem; color: #495057;">{label}</div>
            <div style="font-size: 0.75rem; color: #6c757d;">{sublabel}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_course_progress_section(
    course_progress: list[dict[str, Any]],
    on_click: Callable[[str], None] | None = None,
) -> None:
    """Render the per-course progress section.
    
    Args:
        course_progress: List of course data with progress info.
        on_click: Callback when course is clicked.
    """
    st.markdown("### Course Progress")
    
    if not course_progress:
        st.markdown(
            """
            <p style="color: #6c757d; font-style: italic;">
                No courses yet. Create a course to start tracking progress!
            </p>
            """,
            unsafe_allow_html=True,
        )
        return
    
    for course_data in course_progress:
        course = course_data.get("course", {})
        progress = course_data.get("progress")
        
        course_id = course.get("id", "")
        title = course.get("title", "Untitled")
        
        # Get progress values
        if progress:
            completion = progress.completion_percentage if hasattr(progress, 'completion_percentage') else 0
            modules_done = progress.modules_completed if hasattr(progress, 'modules_completed') else 0
            total_modules = progress.total_modules if hasattr(progress, 'total_modules') else 0
            concepts_done = progress.concepts_completed if hasattr(progress, 'concepts_completed') else 0
            total_concepts = progress.total_concepts if hasattr(progress, 'total_concepts') else 0
            hours = progress.time_spent_minutes / 60 if hasattr(progress, 'time_spent_minutes') else 0
        else:
            completion = 0
            modules_done = total_modules = concepts_done = total_concepts = 0
            hours = 0
        
        # Course icon
        icon = _get_course_icon(title)
        is_complete = completion >= 1.0
        
        st.markdown(f"#### {icon} {title} {'✅' if is_complete else ''}")
        
        st.progress(completion, text=f"{format_percentage(completion)} complete")
        
        st.markdown(
            f"""
            <p style="color: #6c757d; font-size: 0.9rem; margin-top: -0.5rem;">
                {modules_done}/{total_modules} modules • {concepts_done}/{total_concepts} concepts • {hours:.1f} hrs
            </p>
            """,
            unsafe_allow_html=True,
        )
        
        st.markdown("<br>", unsafe_allow_html=True)


def _get_course_icon(title: str) -> str:
    """Get an icon for a course based on its title."""
    title_lower = title.lower()
    if "python" in title_lower:
        return "🐍"
    elif "cuda" in title_lower or "gpu" in title_lower:
        return "🖥️"
    elif "react" in title_lower:
        return "⚛️"
    elif "javascript" in title_lower or "js" in title_lower:
        return "🟨"
    elif "machine learning" in title_lower or "ml" in title_lower:
        return "🤖"
    elif "data" in title_lower:
        return "📊"
    else:
        return "📚"


def _render_quiz_history_section(quiz_history: list[QuizResult]) -> None:
    """Render the quiz history table.
    
    Args:
        quiz_history: List of quiz results.
    """
    st.markdown("### Quiz History")
    
    if not quiz_history:
        st.markdown(
            """
            <p style="color: #6c757d; font-style: italic;">
                No quizzes taken yet. Complete a module to take a quiz!
            </p>
            """,
            unsafe_allow_html=True,
        )
        return
    
    # Build table data
    table_data = []
    for result in quiz_history:
        date_str = format_date(result.completed_at) if hasattr(result, 'completed_at') else "N/A"
        module = result.module_title if hasattr(result, 'module_title') else result.module_id
        score = f"{result.score_percentage}%"
        passed_icon = "✅" if result.passed else "❌"
        
        table_data.append({
            "Date": date_str,
            "Module": module,
            "Score": f"{score} {passed_icon}",
        })
    
    # Display as dataframe
    if table_data:
        st.dataframe(
            table_data,
            use_container_width=True,
            hide_index=True,
        )


def render_progress_with_services(
    progress_service,
    course_service,
    on_navigate: Callable[[str], None] | None = None,
    on_course_click: Callable[[str], None] | None = None,
) -> None:
    """Render the progress page with full service integration.
    
    This function loads all data from services and renders the page.
    
    Args:
        progress_service: ProgressService instance.
        course_service: CourseService instance for course data.
        on_navigate: Navigation callback.
        on_course_click: Course click callback.
    
    Example:
        ```python
        render_progress_with_services(
            progress_service=ProgressService(),
            course_service=CourseService(),
            on_navigate=lambda page: set_page(page),
        )
        ```
    """
    # Get learning stats
    stats = progress_service.get_learning_stats()
    
    # Get all courses and their progress
    courses = course_service.list_courses()
    course_progress = []
    for course in courses:
        course_id = course.get("id", "")
        if course_id:
            progress = progress_service.get_course_progress(course_id)
            course_progress.append({
                "course": course,
                "progress": progress,
            })
    
    # Get all quiz history
    all_quiz_history = []
    for course in courses:
        course_id = course.get("id", "")
        if course_id:
            quiz_history = progress_service.get_quiz_history(course_id)
            all_quiz_history.extend(quiz_history)
    
    # Sort by date, most recent first
    all_quiz_history.sort(
        key=lambda x: x.completed_at if hasattr(x, 'completed_at') else 0,
        reverse=True,
    )
    
    render_progress_page(
        stats=stats,
        course_progress=course_progress,
        quiz_history=all_quiz_history,
        on_navigate=on_navigate,
        on_course_click=on_course_click,
    )
