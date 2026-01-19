"""New Course page for Sensei.

This module provides the course creation page with:
- Topic input field
- Generate button
- Loading state with progress indicator
- Course outline preview
- Start Learning button
"""

from typing import Any, Callable

import streamlit as st

from sensei.models.schemas import Course
from sensei.ui.components import render_sidebar


def render_new_course_page(
    current_page: str = "new_course",
    on_navigate: Callable[[str], None] | None = None,
    on_generate: Callable[[str], Course | None] | None = None,
    on_start_learning: Callable[[str], None] | None = None,
    generated_course: Course | None = None,
    is_generating: bool = False,
    generation_status: str = "",
) -> None:
    """Render the new course creation page.
    
    Args:
        current_page: Current page for sidebar highlighting.
        on_navigate: Callback for sidebar navigation.
        on_generate: Callback to generate course. Takes topic string, returns Course.
        on_start_learning: Callback when Start Learning is clicked. Takes course_id.
        generated_course: Previously generated course to display (for persistence).
        is_generating: Whether course generation is in progress.
        generation_status: Status message during generation.
    
    Example:
        ```python
        render_new_course_page(
            on_generate=lambda topic: course_service.create_course(topic),
            on_start_learning=lambda cid: navigate_to_learning(cid),
        )
        ```
    """
    # Render sidebar
    render_sidebar(current_page=current_page, on_navigate=on_navigate)
    
    # Page header
    _render_header()
    
    # Topic input section
    topic = _render_topic_input()
    
    # Generate button and status
    should_generate = _render_generate_button(
        topic=topic,
        is_generating=is_generating,
    )
    
    # Handle generation
    if should_generate and on_generate and topic:
        with st.spinner("🗺️ Curriculum Architect is planning your course..."):
            try:
                generated_course = on_generate(topic)
            except Exception as e:
                st.error(f"❌ Failed to generate course: {str(e)}")
                generated_course = None
    
    # Show loading state
    if is_generating:
        _render_loading_state(generation_status)
    
    # Course preview (if generated)
    if generated_course:
        _render_course_preview(
            course=generated_course,
            on_start_learning=on_start_learning,
        )


def _render_header() -> None:
    """Render the page header."""
    st.markdown(
        """
        <div style="
            padding: 1.5rem 0;
            margin-bottom: 1rem;
        ">
            <h1 style="margin: 0; font-size: 2rem;">
                ➕ Create New Course
            </h1>
            <p style="color: #666; margin-top: 0.5rem;">
                Tell Sensei what you want to learn, and AI will create a personalized curriculum for you.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_topic_input() -> str:
    """Render the topic input field.
    
    Returns:
        The entered topic string.
    """
    st.markdown("### What would you like to learn?")
    
    topic = st.text_input(
        label="Topic",
        placeholder="e.g., Python Programming, Machine Learning, CUDA C...",
        key="new_course_topic",
        label_visibility="collapsed",
    )
    
    # Example suggestions
    st.markdown(
        """
        <p style="color: #6c757d; font-size: 0.9rem; margin-top: 0.5rem;">
            💡 Examples: Python Basics, Machine Learning, React Development, 
            Data Structures, Kubernetes, CUDA C Programming
        </p>
        """,
        unsafe_allow_html=True,
    )
    
    return topic


def _render_generate_button(
    topic: str,
    is_generating: bool,
) -> bool:
    """Render the generate button.
    
    Args:
        topic: Current topic input value.
        is_generating: Whether generation is in progress.
    
    Returns:
        True if button was clicked and generation should start.
    """
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([0.3, 0.4, 0.3])
    
    with col2:
        # Button is disabled if topic is empty or already generating
        disabled = not topic.strip() or is_generating
        button_label = "⏳ Generating..." if is_generating else "🚀 Generate Curriculum"
        
        clicked = st.button(
            button_label,
            key="generate_curriculum_btn",
            disabled=disabled,
            use_container_width=True,
            type="primary",
        )
        
        return clicked and not is_generating


def _render_loading_state(status: str = "") -> None:
    """Render the loading state during course generation.
    
    Args:
        status: Current status message.
    """
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, #e8f4fd 0%, #f0f7ff 100%);
            border: 1px solid #b8daff;
            border-radius: 10px;
            padding: 1.5rem;
            margin: 1rem 0;
            text-align: center;
        ">
            <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">🗺️</div>
            <div style="font-size: 1.1rem; font-weight: 500; color: #004085;">
                {status or "Generating your personalized curriculum..."}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    st.progress(0.5, text="Creating module structure...")


def _render_course_preview(
    course: Course,
    on_start_learning: Callable[[str], None] | None = None,
) -> None:
    """Render the course preview after generation.
    
    Args:
        course: The generated Course object.
        on_start_learning: Callback when Start Learning is clicked.
    """
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Success banner
    st.markdown(
        """
        <div style="
            background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
            border: 1px solid #28a745;
            border-radius: 10px;
            padding: 1rem;
            margin-bottom: 1rem;
            text-align: center;
        ">
            <span style="font-size: 1.5rem;">✅</span>
            <span style="font-size: 1.1rem; font-weight: 500; color: #155724; margin-left: 0.5rem;">
                Course Created!
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # Course summary
    total_modules = len(course.modules) if course.modules else 0
    total_concepts = course.total_concepts
    estimated_hours = sum(
        m.estimated_minutes for m in (course.modules or [])
    ) / 60
    
    st.markdown(f"### 📚 {course.title}")
    st.markdown(f"*{course.description}*" if course.description else "")
    
    # Stats row
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Modules", total_modules)
    with col2:
        st.metric("Concepts", total_concepts)
    with col3:
        st.metric("Est. Hours", f"{estimated_hours:.1f}")
    
    # Module outline
    st.markdown("#### Course Outline")
    
    for i, module in enumerate(course.modules or []):
        with st.expander(f"📖 Module {i + 1}: {module.title}", expanded=i == 0):
            if module.description:
                st.markdown(f"*{module.description}*")
            
            st.markdown("**Concepts:**")
            for concept in (module.concepts or []):
                st.markdown(f"- {concept.title}")
    
    # Start Learning button
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([0.25, 0.5, 0.25])
    with col2:
        if st.button(
            "📖 Start Learning",
            key="start_learning_btn",
            use_container_width=True,
            type="primary",
        ):
            if on_start_learning:
                on_start_learning(course.id)


def render_new_course_with_services(
    course_service,
    user_service=None,
    on_navigate: Callable[[str], None] | None = None,
    on_course_created: Callable[[Course], None] | None = None,
    on_start_learning: Callable[[str], None] | None = None,
) -> None:
    """Render the new course page with full service integration.
    
    This function manages the course generation state and handles
    the full flow from topic input to course creation.
    
    Args:
        course_service: CourseService instance for course creation.
        user_service: Optional UserService for user preferences.
        on_navigate: Navigation callback.
        on_course_created: Callback when a course is successfully created.
        on_start_learning: Callback when Start Learning is clicked.
    
    Example:
        ```python
        render_new_course_with_services(
            course_service=CourseService(),
            on_navigate=lambda page: set_page(page),
            on_start_learning=lambda cid: go_to_learning(cid),
        )
        ```
    """
    # Initialize session state for this page
    if "generated_course" not in st.session_state:
        st.session_state["generated_course"] = None
    if "is_generating" not in st.session_state:
        st.session_state["is_generating"] = False
    
    def generate_course(topic: str) -> Course | None:
        """Generate a course for the given topic."""
        st.session_state["is_generating"] = True
        
        try:
            # Get user preferences if service available
            user_prefs = None
            if user_service:
                user_prefs = user_service.get_preferences()
            
            # Create the course
            course = course_service.create_course(topic, user_prefs)
            
            st.session_state["generated_course"] = course
            st.session_state["is_generating"] = False
            
            # Notify callback
            if on_course_created:
                on_course_created(course)
            
            return course
            
        except Exception as e:
            st.session_state["is_generating"] = False
            raise e
    
    render_new_course_page(
        current_page="new_course",
        on_navigate=on_navigate,
        on_generate=generate_course,
        on_start_learning=on_start_learning,
        generated_course=st.session_state.get("generated_course"),
        is_generating=st.session_state.get("is_generating", False),
    )
