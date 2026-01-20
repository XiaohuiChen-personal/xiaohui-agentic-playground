"""Learning page for Sensei.

This module provides the main learning interface with:
- Course outline in sidebar
- Concept viewer with lesson content
- Previous/Next navigation
- Chat interface for Q&A
- Take Quiz button at module end
"""

from typing import Any, Callable

import streamlit as st

from sensei.models.schemas import ChatMessage, ConceptLesson
from sensei.ui.components import (
    render_chat_with_form,
    render_concept_with_navigation,
    render_learning_sidebar,
    render_loading_state,
)

# Educational tips shown during AI operations
LESSON_GENERATION_TIPS = [
    "Teaching Crew is crafting personalized explanations for you.",
    "Each lesson is tailored to your learning style.",
    "Great time to review what you learned in the previous concept!",
    "The AI is preparing code examples specific to your level.",
]

QA_TIPS = [
    "Sensei is thinking about the best way to explain this.",
    "Good questions lead to deeper understanding!",
    "The AI is considering your learning history for context.",
]


def render_learning_page(
    course_title: str = "",
    concept_lesson: ConceptLesson | None = None,
    chat_messages: list[ChatMessage] | None = None,
    course_outline: dict[str, Any] | None = None,
    current_module_idx: int = 0,
    current_concept_idx: int = 0,
    total_modules: int = 0,
    is_module_complete: bool = False,
    is_loading: bool = False,
    quiz_passed: bool | None = None,
    on_navigate: Callable[[str], None] | None = None,
    on_previous: Callable[[], None] | None = None,
    on_next: Callable[[], None] | None = None,
    on_ask_question: Callable[[str], str] | None = None,
    on_take_quiz: Callable[[], None] | None = None,
    on_next_module: Callable[[], None] | None = None,
) -> None:
    """Render the learning session page.
    
    Args:
        course_title: Title of the current course.
        concept_lesson: Current ConceptLesson with content.
        chat_messages: List of chat messages for Q&A history.
        course_outline: Course structure for sidebar navigation.
        current_module_idx: Current module index.
        current_concept_idx: Current concept index within module.
        total_modules: Total number of modules in the course.
        is_module_complete: Whether current module is at last concept.
        is_loading: Whether a navigation operation is in progress.
        quiz_passed: Quiz status for current module (None=not taken, True=passed, False=failed).
        on_navigate: Callback for sidebar navigation.
        on_previous: Callback when Previous button is clicked.
        on_next: Callback when Next button is clicked.
        on_ask_question: Callback for Q&A. Takes question, returns answer.
        on_take_quiz: Callback when Take Quiz button is clicked.
        on_next_module: Callback when Continue to Next Module is clicked.
    
    Example:
        ```python
        render_learning_page(
            course_title="Python Basics",
            concept_lesson=learning_service.get_current_concept(),
            chat_messages=learning_service.get_chat_history(),
            on_previous=lambda: learning_service.previous_concept(),
            on_next=lambda: learning_service.next_concept(),
            on_ask_question=lambda q: learning_service.ask_question(q),
            on_take_quiz=lambda: navigate_to_quiz(),
        )
        ```
    """
    chat_messages = chat_messages or []
    
    # Render sidebar with course outline
    if course_outline:
        render_learning_sidebar(
            course=course_outline,
            current_module_idx=current_module_idx,
            current_concept_idx=current_concept_idx,
            on_back=lambda: on_navigate("dashboard") if on_navigate else None,
        )
    
    # Main content area
    _render_header(course_title, concept_lesson)
    _render_progress_bar(concept_lesson)
    
    # Concept content
    if concept_lesson:
        _render_concept_section(
            concept_lesson=concept_lesson,
            on_previous=on_previous,
            on_next=on_next,
            is_loading=is_loading,
        )
    else:
        _render_no_content_state()
    
    st.divider()
    
    # Chat section
    _render_chat_section(
        messages=chat_messages,
        on_ask_question=on_ask_question,
    )
    
    # Take Quiz / Next Module section (when module is complete)
    if is_module_complete:
        is_last_module = current_module_idx >= total_modules - 1 if total_modules > 0 else False
        _render_module_complete_section(
            quiz_passed=quiz_passed,
            is_last_module=is_last_module,
            on_take_quiz=on_take_quiz,
            on_next_module=on_next_module,
        )


def _render_header(
    course_title: str,
    concept_lesson: ConceptLesson | None,
) -> None:
    """Render the page header with course and module info.
    
    Args:
        course_title: Title of the course.
        concept_lesson: Current lesson for module info.
    """
    module_title = concept_lesson.module_title if concept_lesson else ""
    
    st.markdown(
        f"""
        <div style="padding: 1rem 0; margin-bottom: 0.5rem;">
            <h1 style="margin: 0; font-size: 1.75rem;">📚 {course_title}</h1>
            <p style="color: #666; margin-top: 0.25rem; font-size: 1.1rem;">
                {module_title}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_progress_bar(concept_lesson: ConceptLesson | None) -> None:
    """Render the concept progress indicator.
    
    Args:
        concept_lesson: Current lesson with progress info.
    """
    if not concept_lesson:
        return
    
    concept_idx = concept_lesson.concept_idx
    total = concept_lesson.total_concepts_in_module
    
    if total > 0:
        progress = (concept_idx + 1) / total
        # Create visual dots
        dots = ""
        for i in range(total):
            if i <= concept_idx:
                dots += "●"
            else:
                dots += "○"
        
        st.markdown(
            f"""
            <div style="
                margin-bottom: 1rem;
                display: flex;
                align-items: center;
                gap: 0.5rem;
            ">
                <span style="color: #6c757d; font-size: 0.9rem;">
                    Concept {concept_idx + 1} of {total}
                </span>
                <span style="color: #007bff; letter-spacing: 2px;">
                    {dots}
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.progress(progress)


def _render_concept_section(
    concept_lesson: ConceptLesson,
    on_previous: Callable[[], None] | None,
    on_next: Callable[[], None] | None,
    is_loading: bool = False,
) -> None:
    """Render the concept content with navigation.
    
    Args:
        concept_lesson: Current lesson content.
        on_previous: Previous button callback.
        on_next: Next button callback.
        is_loading: Whether a navigation operation is in progress.
    """
    render_concept_with_navigation(
        title=concept_lesson.concept_title,
        content=concept_lesson.lesson_content,
        concept_idx=concept_lesson.concept_idx,
        total_concepts=concept_lesson.total_concepts_in_module,
        module_title=concept_lesson.module_title,
        on_previous=on_previous,
        on_next=on_next,
        can_go_previous=concept_lesson.has_previous,
        can_go_next=concept_lesson.has_next,
        is_loading=is_loading,
    )


def _render_no_content_state() -> None:
    """Render placeholder when no concept is loaded."""
    st.markdown(
        """
        <div style="
            text-align: center;
            padding: 3rem;
            color: #6c757d;
        ">
            <span style="font-size: 3rem;">📖</span>
            <p>Loading lesson content...</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_chat_section(
    messages: list[ChatMessage],
    on_ask_question: Callable[[str], str] | None,
) -> None:
    """Render the Q&A chat section.
    
    Args:
        messages: Chat message history.
        on_ask_question: Callback to handle questions.
    """
    st.markdown("### 💬 Ask Sensei a Question")
    
    # Use chat input for question submission
    question = st.chat_input(
        placeholder="Type your question about this concept...",
        key="learning_chat_input",
    )
    
    # Handle question submission
    if question and on_ask_question:
        with st.spinner("🤔 Sensei is thinking..."):
            try:
                on_ask_question(question)
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
    
    # Display chat history (most recent first in expandable area)
    if messages:
        with st.expander("📜 Chat History", expanded=True):
            render_chat_with_form(
                messages=messages,
                on_send=None,  # We use st.chat_input above instead
            )
    else:
        st.markdown(
            """
            <p style="color: #6c757d; font-style: italic;">
                Ask any question about the current concept. Sensei is here to help!
            </p>
            """,
            unsafe_allow_html=True,
        )


def _render_module_complete_section(
    quiz_passed: bool | None,
    is_last_module: bool,
    on_take_quiz: Callable[[], None] | None,
    on_next_module: Callable[[], None] | None,
) -> None:
    """Render the module completion section with quiz/next module options.
    
    Based on FRONTEND_DESIGN.md Section 6.3 Quiz Flow:
    - If quiz not taken (quiz_passed=None): Show "Take Quiz" button
    - If quiz passed (quiz_passed=True): Show "Continue to Next Module" button
    - If quiz failed (quiz_passed=False): Show "Retake Quiz" and review options
    
    Args:
        quiz_passed: Quiz status (None=not taken, True=passed, False=failed).
        is_last_module: Whether this is the last module in the course.
        on_take_quiz: Callback when Take Quiz is clicked.
        on_next_module: Callback when Continue to Next Module is clicked.
    """
    st.markdown("<br>", unsafe_allow_html=True)
    
    if quiz_passed is True:
        # Quiz passed - show celebration and next module button
        if is_last_module:
            # Course complete!
            st.markdown(
                """
                <div style="
                    background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
                    border: 1px solid #28a745;
                    border-radius: 10px;
                    padding: 1.5rem;
                    margin: 1rem 0;
                    text-align: center;
                ">
                    <span style="font-size: 2rem;">🎉</span>
                    <h3 style="margin: 0.5rem 0; color: #155724;">Course Complete!</h3>
                    <p style="color: #495057; margin-bottom: 1rem;">
                        Congratulations! You've completed all modules in this course.
                        Well done on your learning journey!
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            col1, col2, col3 = st.columns([0.25, 0.5, 0.25])
            with col2:
                if st.button(
                    "🏠 Back to Dashboard",
                    key="back_to_dashboard_btn",
                    use_container_width=True,
                    type="primary",
                ):
                    if on_next_module:
                        # Use on_next_module callback which will navigate to dashboard
                        on_next_module()
        else:
            # More modules to go
            st.markdown(
                """
                <div style="
                    background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
                    border: 1px solid #28a745;
                    border-radius: 10px;
                    padding: 1.5rem;
                    margin: 1rem 0;
                    text-align: center;
                ">
                    <span style="font-size: 2rem;">🎉</span>
                    <h3 style="margin: 0.5rem 0; color: #155724;">Quiz Passed!</h3>
                    <p style="color: #495057; margin-bottom: 1rem;">
                        Excellent work! You're ready to move on to the next module.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            col1, col2, col3 = st.columns([0.25, 0.5, 0.25])
            with col2:
                if st.button(
                    "▶ Continue to Next Module",
                    key="next_module_btn",
                    use_container_width=True,
                    type="primary",
                ):
                    if on_next_module:
                        on_next_module()
    
    elif quiz_passed is False:
        # Quiz failed - show retake option
        st.markdown(
            """
            <div style="
                background: linear-gradient(135deg, #fff3cd 0%, #ffeeba 100%);
                border: 1px solid #ffc107;
                border-radius: 10px;
                padding: 1.5rem;
                margin: 1rem 0;
                text-align: center;
            ">
                <span style="font-size: 2rem;">📚</span>
                <h3 style="margin: 0.5rem 0; color: #856404;">Keep Practicing!</h3>
                <p style="color: #495057; margin-bottom: 1rem;">
                    Review the concepts and try the quiz again when you're ready.
                    You need 80% to pass.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        col1, col2, col3 = st.columns([0.25, 0.5, 0.25])
        with col2:
            if st.button(
                "🔄 Retake Quiz",
                key="retake_quiz_btn",
                use_container_width=True,
                type="primary",
            ):
                if on_take_quiz:
                    on_take_quiz()
    
    else:
        # Quiz not taken yet - show take quiz prompt
        st.markdown(
            """
            <div style="
                background: linear-gradient(135deg, #e8f4fd 0%, #d4edda 100%);
                border: 1px solid #28a745;
                border-radius: 10px;
                padding: 1.5rem;
                margin: 1rem 0;
                text-align: center;
            ">
                <span style="font-size: 2rem;">🎯</span>
                <h3 style="margin: 0.5rem 0; color: #155724;">Module Complete!</h3>
                <p style="color: #495057; margin-bottom: 1rem;">
                    Great job! You've finished all concepts in this module.
                    Take a quiz to test your understanding.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
        col1, col2, col3 = st.columns([0.25, 0.5, 0.25])
        with col2:
            if st.button(
                "📝 Take Quiz",
                key="take_quiz_btn",
                use_container_width=True,
                type="primary",
            ):
                if on_take_quiz:
                    on_take_quiz()


def render_learning_with_services(
    learning_service,
    user_service=None,
    course_id: str | None = None,
    on_navigate: Callable[[str], None] | None = None,
    on_take_quiz: Callable[[], None] | None = None,
) -> None:
    """Render the learning page with full service integration.
    
    This function manages the learning session state and handles
    navigation, Q&A, and progress tracking.
    
    Args:
        learning_service: LearningService instance.
        user_service: Optional UserService for preferences.
        course_id: Course ID to learn (starts/resumes session).
        on_navigate: Navigation callback.
        on_take_quiz: Callback when Take Quiz is clicked.
    
    Example:
        ```python
        render_learning_with_services(
            learning_service=LearningService(),
            course_id="python-basics-123",
            on_navigate=lambda page: set_page(page),
            on_take_quiz=lambda: navigate_to_quiz(),
        )
        ```
    """
    # Initialize loading state
    if "learning_is_navigating" not in st.session_state:
        st.session_state["learning_is_navigating"] = False
    
    # Start or resume session if needed
    if course_id and not learning_service.is_session_active:
        try:
            learning_service.start_session(course_id)
        except ValueError as e:
            st.error(f"❌ Failed to load course: {str(e)}")
            return
    
    if not learning_service.is_session_active:
        st.error("❌ No active learning session. Please select a course.")
        return
    
    # Get user preferences
    user_prefs = None
    if user_service:
        user_prefs = user_service.get_preferences()
    
    # Get current session state
    session = learning_service.current_session
    
    # Check if we're currently navigating (loading new concept)
    is_navigating = st.session_state.get("learning_is_navigating", False)
    
    # Get current concept with loading state
    if is_navigating:
        # Show loading state during navigation
        render_loading_state(
            message="Teaching Crew is preparing the next concept...",
            icon="📖",
            estimated_time="30-60 seconds",
            tips=LESSON_GENERATION_TIPS,
            show_spinner=True,
        )
        # Get the concept (AI call happens here)
        try:
            concept_lesson = learning_service.get_current_concept(user_prefs)
            # Clear navigation flag after successful load
            st.session_state["learning_is_navigating"] = False
            st.rerun()
        except Exception as e:
            st.error(f"❌ Error loading concept: {str(e)}")
            st.session_state["learning_is_navigating"] = False
            return
        return  # Don't render the rest during loading
    else:
        # Normal load
        with st.spinner("📖 Loading lesson..."):
            try:
                concept_lesson = learning_service.get_current_concept(user_prefs)
            except Exception as e:
                st.error(f"❌ Error loading concept: {str(e)}")
                concept_lesson = None
    
    # Get chat history
    chat_messages = session.chat_history if session else []
    
    # Get course outline for sidebar
    course_outline = learning_service.course_data
    
    # Get total modules from course outline
    total_modules = len(course_outline.get("modules", [])) if course_outline else 0
    
    # Get current module info for quiz status check
    current_module_idx = session.current_module_idx if session else 0
    current_module = None
    if course_outline and "modules" in course_outline:
        modules = course_outline["modules"]
        if 0 <= current_module_idx < len(modules):
            current_module = modules[current_module_idx]
    
    # Check quiz status for current module
    quiz_passed = None
    if current_module and course_id:
        module_id = current_module.get("id", f"module-{current_module_idx}")
        # Use getattr for backward compatibility with cached service instances
        # that may not have the new method after hot reload
        if hasattr(learning_service._db, "is_module_quiz_passed"):
            quiz_passed = learning_service._db.is_module_quiz_passed(course_id, module_id)
        else:
            # Fallback: check quiz history manually
            history = learning_service._db.get_quiz_history(course_id)
            for result in history:
                if result.get("module_id") == module_id:
                    quiz_passed = result.get("passed", False)
                    break
    
    # Define callbacks with loading state
    def handle_previous():
        # Set loading state before navigation
        st.session_state["learning_is_navigating"] = True
        # Note: Don't clear cache - previously viewed concepts should use cached lessons
        learning_service.previous_concept()
        st.rerun()
    
    def handle_next():
        # Set loading state before navigation
        st.session_state["learning_is_navigating"] = True
        # Note: Don't clear cache - the new concept won't be in cache anyway,
        # and previously viewed concepts should remain cached
        learning_service.next_concept()
        st.rerun()
    
    def handle_question(question: str) -> str:
        return learning_service.ask_question(question, user_prefs)
    
    def handle_next_module():
        # Navigate to next module or dashboard if course complete
        is_last_module = current_module_idx >= total_modules - 1 if total_modules > 0 else True
        if is_last_module:
            # Course complete - go to dashboard
            if on_navigate:
                on_navigate("dashboard")
        else:
            # Set loading state and advance to next module
            st.session_state["learning_is_navigating"] = True
            learning_service.next_module()
            st.rerun()
    
    # Render the page (is_loading=False since loading state is handled above)
    render_learning_page(
        course_title=course_outline.get("title", "") if course_outline else "",
        concept_lesson=concept_lesson,
        chat_messages=chat_messages,
        course_outline=course_outline,
        current_module_idx=current_module_idx,
        current_concept_idx=session.current_concept_idx if session else 0,
        total_modules=total_modules,
        is_module_complete=learning_service.is_module_complete() if concept_lesson else False,
        is_loading=False,  # Loading state is handled by render_loading_state above
        quiz_passed=quiz_passed,
        on_navigate=on_navigate,
        on_previous=handle_previous,
        on_next=handle_next,
        on_ask_question=handle_question,
        on_take_quiz=on_take_quiz,
        on_next_module=handle_next_module,
    )
