"""Sidebar navigation component for Sensei.

This module provides the navigation sidebar with:
- Navigation links to main pages
- Current page highlighting
- Course outline display during learning sessions
"""

from typing import Any, Callable

import streamlit as st

from sensei.models.enums import ConceptStatus


def render_sidebar(
    current_page: str = "dashboard",
    on_navigate: Callable[[str], None] | None = None,
    course_outline: dict[str, Any] | None = None,
    current_module_idx: int = 0,
    current_concept_idx: int = 0,
) -> str | None:
    """Render the navigation sidebar.
    
    Args:
        current_page: The currently active page for highlighting.
        on_navigate: Callback function when navigation link is clicked.
            Receives the page name as argument.
        course_outline: Optional course structure for learning mode display.
            Should contain 'title' and 'modules' with concepts.
        current_module_idx: Current module index (for learning mode).
        current_concept_idx: Current concept index (for learning mode).
    
    Returns:
        The selected page name if navigation occurred, None otherwise.
    
    Example:
        ```python
        selected = render_sidebar(
            current_page="dashboard",
            on_navigate=lambda page: st.session_state.update(current_page=page)
        )
        ```
    """
    with st.sidebar:
        # App title/logo
        st.markdown(
            """
            <div style="text-align: center; padding: 1rem 0; margin-bottom: 1rem;">
                <span style="font-size: 2.5rem;">🥋</span>
                <h1 style="margin: 0; font-size: 1.5rem; font-weight: 600;">Sensei</h1>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
        st.divider()
        
        # Navigation section
        selected_page = _render_navigation(current_page, on_navigate)
        
        # Course outline (only shown during learning)
        if course_outline:
            st.divider()
            _render_course_outline(
                course_outline,
                current_module_idx,
                current_concept_idx,
            )
        
        return selected_page


def _render_navigation(
    current_page: str,
    on_navigate: Callable[[str], None] | None,
) -> str | None:
    """Render navigation links.
    
    Args:
        current_page: Currently active page.
        on_navigate: Navigation callback.
    
    Returns:
        Selected page if changed, None otherwise.
    """
    # Define navigation items
    nav_items = [
        {"key": "dashboard", "icon": "📚", "label": "Dashboard"},
        {"key": "new_course", "icon": "➕", "label": "New Course"},
        {"key": "progress", "icon": "📊", "label": "Progress"},
        {"key": "settings", "icon": "⚙️", "label": "Settings"},
    ]
    
    selected = None
    
    for item in nav_items:
        is_active = current_page == item["key"]
        
        # Style for active vs inactive
        if is_active:
            button_type = "primary"
        else:
            button_type = "secondary"
        
        # Create button
        col1, col2 = st.columns([0.2, 0.8])
        with col1:
            st.markdown(f"<span style='font-size: 1.2rem;'>{item['icon']}</span>", unsafe_allow_html=True)
        with col2:
            if st.button(
                item["label"],
                key=f"nav_{item['key']}",
                use_container_width=True,
                type=button_type,
            ):
                selected = item["key"]
                if on_navigate:
                    on_navigate(item["key"])
    
    return selected


def _render_course_outline(
    course: dict[str, Any],
    current_module_idx: int,
    current_concept_idx: int,
) -> None:
    """Render course outline for learning mode.
    
    Shows modules and concepts with completion status.
    
    Args:
        course: Course data with modules and concepts.
        current_module_idx: Index of current module.
        current_concept_idx: Index of current concept.
    """
    st.markdown("### Course Outline")
    
    course_title = course.get("title", "Course")
    st.markdown(f"**{course_title}**")
    
    modules = course.get("modules", [])
    
    for module_idx, module in enumerate(modules):
        module_title = module.get("title", f"Module {module_idx + 1}")
        concepts = module.get("concepts", [])
        
        # Determine module status
        if module_idx < current_module_idx:
            # Completed module
            module_icon = "✅"
            module_style = "color: #28a745;"
        elif module_idx == current_module_idx:
            # Current module
            module_icon = "▶"
            module_style = "color: #007bff; font-weight: 600;"
        else:
            # Future module
            module_icon = "○"
            module_style = "color: #6c757d;"
        
        # Module header
        with st.expander(
            f"{module_icon} {module_title}",
            expanded=(module_idx == current_module_idx),
        ):
            for concept_idx, concept in enumerate(concepts):
                concept_title = concept.get("title", f"Concept {concept_idx + 1}")
                concept_status = concept.get("status", ConceptStatus.NOT_STARTED.value)
                
                # Determine concept status
                if module_idx < current_module_idx:
                    # In completed module
                    concept_icon = "✅"
                elif module_idx == current_module_idx:
                    if concept_idx < current_concept_idx:
                        concept_icon = "✅"
                    elif concept_idx == current_concept_idx:
                        concept_icon = "▶"
                    else:
                        concept_icon = "•"
                else:
                    concept_icon = "•"
                
                # Display concept
                st.markdown(
                    f"<span style='margin-left: 1rem;'>{concept_icon} {concept_title}</span>",
                    unsafe_allow_html=True,
                )


def render_simple_sidebar(current_page: str = "dashboard") -> str:
    """Render a simplified sidebar without callbacks.
    
    Uses Streamlit's native radio button for navigation.
    Returns the selected page name.
    
    Args:
        current_page: The currently selected page.
    
    Returns:
        The selected page name.
    
    Example:
        ```python
        page = render_simple_sidebar("dashboard")
        if page == "dashboard":
            render_dashboard()
        ```
    """
    with st.sidebar:
        # App title/logo
        st.markdown(
            """
            <div style="text-align: center; padding: 1rem 0;">
                <span style="font-size: 2.5rem;">🥋</span>
                <h1 style="margin: 0; font-size: 1.5rem; font-weight: 600;">Sensei</h1>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
        st.divider()
        
        # Navigation using radio buttons
        pages = {
            "📚 Dashboard": "dashboard",
            "➕ New Course": "new_course",
            "📊 Progress": "progress",
            "⚙️ Settings": "settings",
        }
        
        # Find current label from page key
        current_label = next(
            (label for label, key in pages.items() if key == current_page),
            "📚 Dashboard"
        )
        
        selected_label = st.radio(
            "Navigation",
            options=list(pages.keys()),
            index=list(pages.keys()).index(current_label),
            label_visibility="collapsed",
        )
        
        return pages[selected_label]


def render_learning_sidebar(
    course: dict[str, Any],
    current_module_idx: int,
    current_concept_idx: int,
    on_back: Callable[[], None] | None = None,
) -> None:
    """Render sidebar specifically for learning mode.
    
    Shows course outline with current position and a back button.
    
    Args:
        course: Course data with modules and concepts.
        current_module_idx: Index of current module.
        current_concept_idx: Index of current concept.
        on_back: Callback when back button is clicked.
    """
    with st.sidebar:
        # Back button
        if st.button("← Back to Dashboard", key="back_to_dashboard"):
            if on_back:
                on_back()
        
        st.divider()
        
        # Course title
        course_title = course.get("title", "Course")
        st.markdown(f"## {course_title}")
        
        st.divider()
        
        # Module/concept outline
        _render_course_outline(course, current_module_idx, current_concept_idx)
