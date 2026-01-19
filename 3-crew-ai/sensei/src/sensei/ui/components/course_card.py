"""Course card component for Sensei.

This module provides a card-style display for courses showing:
- Course title and description
- Progress bar visualization
- Current module information
- Action buttons (Continue, Review, Delete)
"""

from typing import Any, Callable

import streamlit as st

from sensei.models.schemas import Progress
from sensei.utils.formatters import format_percentage


def render_course_card(
    course: dict[str, Any],
    progress: Progress | None = None,
    on_continue: Callable[[str], None] | None = None,
    on_review: Callable[[str], None] | None = None,
    on_delete: Callable[[str], None] | None = None,
    show_delete: bool = False,
) -> None:
    """Render a course card with progress and actions.
    
    Args:
        course: Course data dictionary with id, title, description, etc.
        progress: Optional Progress object for the course.
        on_continue: Callback when Continue/Start button is clicked.
        on_review: Callback when Review button is clicked.
        on_delete: Callback when Delete button is clicked.
        show_delete: Whether to show the delete button.
    
    Example:
        ```python
        render_course_card(
            course={"id": "course-123", "title": "Python Basics"},
            progress=Progress(course_id="course-123", completion_percentage=0.75),
            on_continue=lambda cid: start_learning(cid),
        )
        ```
    """
    course_id = course.get("id", "")
    title = course.get("title", "Untitled Course")
    description = course.get("description", "")
    total_modules = course.get("total_modules", 0)
    total_concepts = course.get("total_concepts", 0)
    
    # Get progress values
    if progress:
        completion = progress.completion_percentage
        current_module = progress.current_module_idx
        is_complete = progress.is_complete
    else:
        completion = 0.0
        current_module = 0
        is_complete = False
    
    # Card container
    with st.container():
        st.markdown(
            f"""
            <div style="
                border: 1px solid #e0e0e0;
                border-radius: 10px;
                padding: 1.5rem;
                margin-bottom: 1rem;
                background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            ">
            """,
            unsafe_allow_html=True,
        )
        
        # Header row with title and completion badge
        col1, col2 = st.columns([0.85, 0.15])
        
        with col1:
            # Course icon based on topic (simple heuristic)
            icon = _get_course_icon(title)
            st.markdown(f"### {icon} {title}")
        
        with col2:
            if is_complete:
                st.markdown(
                    "<span style='color: #28a745; font-size: 1.5rem;'>✅</span>",
                    unsafe_allow_html=True,
                )
        
        # Description (truncated if too long)
        if description:
            truncated = description[:150] + "..." if len(description) > 150 else description
            st.markdown(f"*{truncated}*")
        
        # Progress bar
        st.progress(completion, text=f"{format_percentage(completion)} complete")
        
        # Stats row
        col1, col2, col3 = st.columns(3)
        
        # Get completion counts from progress
        modules_done = progress.modules_completed if progress else 0
        concepts_done = progress.concepts_completed if progress else 0
        
        with col1:
            st.metric("Modules", f"{modules_done}/{total_modules}")
        
        with col2:
            st.metric("Concepts", f"{concepts_done}/{total_concepts}")
        
        with col3:
            if progress and progress.time_spent_minutes > 0:
                hours = progress.time_spent_minutes / 60
                st.metric("Time", f"{hours:.1f}h")
            else:
                st.metric("Time", "—")
        
        # Current position info (if in progress)
        if not is_complete and completion > 0:
            st.caption(f"📍 Module {current_module + 1} of {total_modules}")
        
        # Action buttons
        st.markdown("<div style='margin-top: 1rem;'>", unsafe_allow_html=True)
        
        button_cols = st.columns([1, 1, 1] if show_delete else [1, 1])
        
        with button_cols[0]:
            if is_complete:
                if st.button(
                    "📖 Review",
                    key=f"review_{course_id}",
                    use_container_width=True,
                ):
                    if on_review:
                        on_review(course_id)
                    elif on_continue:
                        on_continue(course_id)
            elif completion > 0:
                if st.button(
                    "▶ Continue",
                    key=f"continue_{course_id}",
                    use_container_width=True,
                    type="primary",
                ):
                    if on_continue:
                        on_continue(course_id)
            else:
                if st.button(
                    "🚀 Start",
                    key=f"start_{course_id}",
                    use_container_width=True,
                    type="primary",
                ):
                    if on_continue:
                        on_continue(course_id)
        
        with button_cols[1]:
            if is_complete:
                if st.button(
                    "▶ Continue",
                    key=f"continue_complete_{course_id}",
                    use_container_width=True,
                ):
                    if on_continue:
                        on_continue(course_id)
            else:
                if st.button(
                    "📊 Details",
                    key=f"details_{course_id}",
                    use_container_width=True,
                ):
                    # Toggle details display
                    _show_course_details(course, progress)
        
        if show_delete and len(button_cols) > 2:
            with button_cols[2]:
                if st.button(
                    "🗑️ Delete",
                    key=f"delete_{course_id}",
                    use_container_width=True,
                ):
                    if on_delete:
                        on_delete(course_id)
        
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)


def render_course_card_compact(
    course: dict[str, Any],
    progress: Progress | None = None,
    on_click: Callable[[str], None] | None = None,
) -> None:
    """Render a compact course card (for lists/grids).
    
    A smaller version of the course card suitable for dense layouts.
    
    Args:
        course: Course data dictionary.
        progress: Optional Progress object.
        on_click: Callback when card is clicked.
    """
    course_id = course.get("id", "")
    title = course.get("title", "Untitled")
    
    if progress:
        completion = progress.completion_percentage
        is_complete = progress.is_complete
    else:
        completion = 0.0
        is_complete = False
    
    icon = _get_course_icon(title)
    status_icon = "✅" if is_complete else ""
    
    # Simple card with button
    with st.container():
        if st.button(
            f"{icon} {title} {status_icon}",
            key=f"card_{course_id}",
            use_container_width=True,
        ):
            if on_click:
                on_click(course_id)
        
        st.progress(completion)


def render_empty_course_state(
    on_create: Callable[[], None] | None = None,
) -> None:
    """Render empty state when no courses exist.
    
    Shows a friendly message encouraging the user to create their first course.
    
    Args:
        on_create: Callback when Create Course button is clicked.
    """
    st.markdown(
        """
        <div style="
            text-align: center;
            padding: 3rem;
            border: 2px dashed #dee2e6;
            border-radius: 10px;
            background: #f8f9fa;
            margin: 2rem 0;
        ">
            <span style="font-size: 4rem;">📚</span>
            <h2 style="color: #495057; margin-top: 1rem;">No Courses Yet</h2>
            <p style="color: #6c757d; max-width: 400px; margin: 1rem auto;">
                Start your learning journey by creating your first course!
                Sensei will generate a personalized curriculum just for you.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button(
            "➕ Create Your First Course",
            key="create_first_course",
            use_container_width=True,
            type="primary",
        ):
            if on_create:
                on_create()


def _get_course_icon(title: str) -> str:
    """Get an appropriate icon based on course title.
    
    Simple heuristic matching keywords to icons.
    Order matters - more specific patterns are checked first.
    
    Args:
        title: The course title.
    
    Returns:
        An emoji icon string.
    """
    title_lower = title.lower()
    
    # Web/frameworks (check Vue/Angular BEFORE js to avoid false matches)
    if "vue" in title_lower:
        return "💚"
    if "angular" in title_lower:
        return "🅰️"
    if "react" in title_lower:
        return "⚛️"
    
    # Programming languages
    if "python" in title_lower:
        return "🐍"
    if "typescript" in title_lower or " ts " in title_lower or title_lower.endswith(" ts"):
        return "🔷"
    if "javascript" in title_lower or " js " in title_lower or title_lower.endswith(" js"):
        return "🟨"
    if "java" in title_lower and "javascript" not in title_lower:
        return "☕"
    if "rust" in title_lower:
        return "🦀"
    if "golang" in title_lower or " go " in title_lower or title_lower.startswith("go "):
        return "🐹"
    if "c++" in title_lower or "cpp" in title_lower:
        return "⚡"
    if "c#" in title_lower or "csharp" in title_lower:
        return "🎯"
    if "cuda" in title_lower or "gpu" in title_lower:
        return "🖥️"
    
    # Web
    if "web" in title_lower or "html" in title_lower or "css" in title_lower:
        return "🌐"
    
    # Database (check before "data" to avoid false matches)
    if "sql" in title_lower or "database" in title_lower:
        return "🗄️"
    
    # Data/AI
    if "machine learning" in title_lower or " ml " in title_lower or title_lower.startswith("ml "):
        return "🤖"
    if "ai" in title_lower or "artificial intelligence" in title_lower:
        return "🧠"
    if "data" in title_lower:
        return "📊"
    
    # DevOps/Cloud
    if "docker" in title_lower or "kubernetes" in title_lower:
        return "🐳"
    if "cloud" in title_lower or "aws" in title_lower or "azure" in title_lower:
        return "☁️"
    if "devops" in title_lower:
        return "🔧"
    
    # Security
    if "security" in title_lower or "cyber" in title_lower:
        return "🔒"
    
    # Default
    return "📖"


def _show_course_details(
    course: dict[str, Any],
    progress: Progress | None,
) -> None:
    """Show detailed course information in an expander.
    
    Args:
        course: Course data dictionary.
        progress: Optional Progress object.
    """
    with st.expander("📋 Course Details", expanded=True):
        # Full description
        description = course.get("description", "No description available.")
        st.markdown(description)
        
        # Module list
        modules = course.get("modules", [])
        if modules:
            st.markdown("#### Modules")
            for idx, module in enumerate(modules):
                module_title = module.get("title", f"Module {idx + 1}")
                concept_count = len(module.get("concepts", []))
                est_time = module.get("estimated_minutes", 30)
                
                # Check if module is completed
                if progress and idx < progress.modules_completed:
                    status = "✅"
                elif progress and idx == progress.current_module_idx:
                    status = "▶"
                else:
                    status = "○"
                
                st.markdown(
                    f"{status} **{module_title}** ({concept_count} concepts, ~{est_time}min)"
                )
        
        # Progress details
        if progress:
            st.markdown("#### Progress Details")
            col1, col2 = st.columns(2)
            with col1:
                st.metric(
                    "Concepts Completed",
                    f"{progress.concepts_completed}/{progress.total_concepts}"
                )
            with col2:
                st.metric(
                    "Time Invested",
                    f"{progress.time_spent_minutes} min"
                )
