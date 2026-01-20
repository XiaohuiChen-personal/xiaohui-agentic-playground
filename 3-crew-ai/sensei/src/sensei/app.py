"""Main Streamlit application entry point for Sensei.

This module provides the main application with:
- Page configuration setup
- Session state initialization
- Service instantiation
- Page routing logic
- Error handling wrapper

Run with:
    streamlit run src/sensei/app.py
"""

# IMPORTANT: Disable CrewAI telemetry BEFORE any imports
# CrewAI's telemetry tries to register signal handlers, which fails in Streamlit
# because Streamlit runs app code in a non-main thread.
import os
os.environ["CREWAI_TELEMETRY_ENABLED"] = "false"
os.environ["OTEL_SDK_DISABLED"] = "true"

import streamlit as st

from sensei.services import (
    CourseService,
    LearningService,
    ProgressService,
    QuizService,
    UserService,
)
from sensei.ui.pages import (
    render_dashboard_page,
    render_learning_with_services,
    render_new_course_with_services,
    render_onboarding_with_services,
    render_progress_with_services,
    render_quiz_with_services,
    render_settings_with_services,
)
from sensei.utils.constants import load_environment
from sensei.utils.state import initialize_session_state


# Page configuration constants
PAGE_TITLE = "Sensei - AI Learning Tutor"
PAGE_ICON = "🥋"
PAGE_LAYOUT = "wide"

# Valid page identifiers
VALID_PAGES = {
    "dashboard",
    "new_course",
    "learning",
    "quiz",
    "progress",
    "settings",
    "onboarding",
}


def configure_page() -> None:
    """Configure the Streamlit page settings.
    
    Must be called as the first Streamlit command in the app.
    """
    st.set_page_config(
        page_title=PAGE_TITLE,
        page_icon=PAGE_ICON,
        layout=PAGE_LAYOUT,
        initial_sidebar_state="expanded",
    )


def initialize_services() -> dict:
    """Initialize and return all services.
    
    Services are cached in session state to persist across reruns.
    
    Returns:
        Dictionary containing all service instances.
    """
    if "services" not in st.session_state or not st.session_state["services"]:
        st.session_state["services"] = {
            "user": UserService(),
            "progress": ProgressService(),
            "course": CourseService(use_ai=True),
            "learning": LearningService(use_ai=True),
            "quiz": QuizService(use_ai=True),
        }
    
    return st.session_state["services"]


def get_service(name: str):
    """Get a specific service by name.
    
    Args:
        name: Service name ('user', 'progress', 'course', 'learning', 'quiz').
    
    Returns:
        The requested service instance.
    
    Raises:
        KeyError: If service name is invalid.
    """
    services = initialize_services()
    return services[name]


def navigate_to(page: str) -> None:
    """Navigate to a specific page.
    
    Args:
        page: Page identifier (must be in VALID_PAGES).
    """
    if page not in VALID_PAGES:
        st.error(f"Invalid page: {page}")
        return
    
    st.session_state["ui"]["current_page"] = page
    st.rerun()


def get_current_page() -> str:
    """Get the current page identifier.
    
    Returns:
        Current page name, defaults to 'dashboard'.
    """
    return st.session_state.get("ui", {}).get("current_page", "dashboard")


def check_onboarding() -> bool:
    """Check if the user has completed onboarding.
    
    Returns:
        True if user is onboarded, False otherwise.
    """
    user_service = get_service("user")
    return user_service.is_onboarded()


def render_current_page() -> None:
    """Render the current page based on routing state."""
    current_page = get_current_page()
    
    # Get services
    user_service = get_service("user")
    course_service = get_service("course")
    progress_service = get_service("progress")
    learning_service = get_service("learning")
    quiz_service = get_service("quiz")
    
    # Define common callbacks
    def on_navigate(page: str) -> None:
        navigate_to(page)
    
    def on_continue_course(course_id: str) -> None:
        st.session_state["courses"]["current_course_id"] = course_id
        navigate_to("learning")
    
    def on_review_course(course_id: str) -> None:
        st.session_state["courses"]["current_course_id"] = course_id
        navigate_to("learning")
    
    def on_new_course() -> None:
        # Clear any previous generated course
        if "generated_course" in st.session_state:
            del st.session_state["generated_course"]
        navigate_to("new_course")
    
    def on_start_learning(course_id: str) -> None:
        st.session_state["courses"]["current_course_id"] = course_id
        navigate_to("learning")
    
    def on_take_quiz(course_id: str, module_idx: int) -> None:
        st.session_state["quiz"]["course_id"] = course_id
        st.session_state["quiz"]["module_idx"] = module_idx
        # Flag to indicate user explicitly wants a fresh quiz
        st.session_state["quiz"]["force_new"] = True
        navigate_to("quiz")
    
    def on_continue_learning_after_quiz() -> None:
        navigate_to("learning")
    
    def on_onboarding_complete() -> None:
        navigate_to("dashboard")
    
    # Route to appropriate page
    if current_page == "dashboard":
        render_dashboard_page(
            user_service=user_service,
            course_service=course_service,
            progress_service=progress_service,
            on_navigate=on_navigate,
            on_continue_course=on_continue_course,
            on_review_course=on_review_course,
            on_new_course=on_new_course,
        )
    
    elif current_page == "new_course":
        render_new_course_with_services(
            course_service=course_service,
            user_service=user_service,
            on_navigate=on_navigate,
            on_start_learning=on_start_learning,
        )
    
    elif current_page == "learning":
        course_id = st.session_state.get("courses", {}).get("current_course_id")
        
        if not course_id:
            st.warning("No course selected. Please select a course from the dashboard.")
            if st.button("Go to Dashboard"):
                navigate_to("dashboard")
            return
        
        # Get current module index for quiz navigation
        current_module = 0
        if learning_service.is_session_active and learning_service.current_session:
            current_module = learning_service.current_session.current_module_idx
        
        render_learning_with_services(
            learning_service=learning_service,
            user_service=user_service,
            course_id=course_id,
            on_navigate=on_navigate,
            on_take_quiz=lambda: on_take_quiz(course_id, current_module),
        )
    
    elif current_page == "quiz":
        course_id = st.session_state.get("quiz", {}).get(
            "course_id",
            st.session_state.get("courses", {}).get("current_course_id"),
        )
        module_idx = st.session_state.get("quiz", {}).get("module_idx", 0)
        
        if not course_id:
            st.warning("No course selected for quiz. Please start from a learning session.")
            if st.button("Go to Dashboard"):
                navigate_to("dashboard")
            return
        
        render_quiz_with_services(
            quiz_service=quiz_service,
            user_service=user_service,
            course_id=course_id,
            module_idx=module_idx,
            on_navigate=on_navigate,
            on_continue_learning=on_continue_learning_after_quiz,
        )
    
    elif current_page == "progress":
        render_progress_with_services(
            progress_service=progress_service,
            course_service=course_service,
            on_navigate=on_navigate,
        )
    
    elif current_page == "settings":
        render_settings_with_services(
            user_service=user_service,
            on_navigate=on_navigate,
        )
    
    elif current_page == "onboarding":
        render_onboarding_with_services(
            user_service=user_service,
            on_complete=on_onboarding_complete,
        )
    
    else:
        st.error(f"Unknown page: {current_page}")
        navigate_to("dashboard")


def main() -> None:
    """Main application entry point."""
    # Configure page (must be first)
    configure_page()
    
    # Load environment variables (API keys, tracing)
    load_environment()
    
    # Initialize session state
    initialize_session_state()
    
    # Initialize services
    initialize_services()
    
    # Check onboarding status
    if not check_onboarding():
        # Force onboarding page for new users
        st.session_state["ui"]["current_page"] = "onboarding"
    
    # Render current page with error handling
    try:
        render_current_page()
    except Exception as e:
        st.error("An unexpected error occurred.")
        st.exception(e)
        
        # Provide recovery option
        if st.button("Return to Dashboard"):
            st.session_state["ui"]["current_page"] = "dashboard"
            st.rerun()


if __name__ == "__main__":
    main()
