"""Onboarding page for Sensei.

This module provides the first-time user setup page with:
- Welcome screen
- Step-by-step preference collection
- Progress through steps
- Complete button
"""

from typing import Callable

import streamlit as st

from sensei.models.enums import ExperienceLevel, LearningStyle
from sensei.models.schemas import UserPreferences


def render_onboarding_page(
    current_step: int = 0,
    on_complete: Callable[[UserPreferences], None] | None = None,
) -> None:
    """Render the onboarding page.
    
    Args:
        current_step: Current step in the onboarding flow (0-3).
        on_complete: Callback when onboarding is completed with preferences.
    
    Example:
        ```python
        render_onboarding_page(
            current_step=0,
            on_complete=lambda prefs: user_service.complete_onboarding(prefs),
        )
        ```
    """
    # Initialize session state for onboarding data
    if "onboarding_name" not in st.session_state:
        st.session_state["onboarding_name"] = ""
    if "onboarding_style" not in st.session_state:
        st.session_state["onboarding_style"] = LearningStyle.READING
    if "onboarding_experience" not in st.session_state:
        st.session_state["onboarding_experience"] = ExperienceLevel.BEGINNER
    if "onboarding_goals" not in st.session_state:
        st.session_state["onboarding_goals"] = ""
    if "onboarding_step" not in st.session_state:
        st.session_state["onboarding_step"] = current_step
    
    current = st.session_state["onboarding_step"]
    
    # Centered layout
    col1, col2, col3 = st.columns([0.15, 0.7, 0.15])
    
    with col2:
        # Header with logo
        st.markdown(
            """
            <div style="text-align: center; padding: 2rem 0;">
                <span style="font-size: 4rem;">🥋</span>
                <h1 style="margin: 0.5rem 0; font-size: 2.5rem;">Welcome to Sensei</h1>
                <p style="color: #666; font-size: 1.1rem;">
                    Your AI-powered learning companion
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
        # Progress indicator
        _render_progress_indicator(current)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Step content
        if current == 0:
            _render_step_name()
        elif current == 1:
            _render_step_learning_style()
        elif current == 2:
            _render_step_experience()
        elif current == 3:
            _render_step_goals()
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Navigation buttons
        _render_navigation(current, on_complete)


def _render_progress_indicator(current_step: int) -> None:
    """Render the step progress indicator.
    
    Args:
        current_step: Current step (0-3).
    """
    steps = ["Name", "Style", "Experience", "Goals"]
    
    dots = ""
    for i, step in enumerate(steps):
        if i < current_step:
            dots += f"<span style='color: #28a745;'>✅</span> "
        elif i == current_step:
            dots += f"<span style='color: #007bff;'>●</span> "
        else:
            dots += f"<span style='color: #dee2e6;'>○</span> "
    
    st.markdown(
        f"""
        <div style="text-align: center; margin: 1rem 0;">
            <div style="font-size: 1.5rem; letter-spacing: 8px;">{dots}</div>
            <p style="color: #6c757d; margin-top: 0.5rem;">
                Step {current_step + 1} of 4: {steps[current_step]}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_step_name() -> None:
    """Render the name input step."""
    st.markdown(
        """
        <div style="text-align: center; margin-bottom: 1.5rem;">
            <h2 style="margin: 0;">What's your name?</h2>
            <p style="color: #666;">This is how Sensei will greet you.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    name = st.text_input(
        "Name",
        value=st.session_state["onboarding_name"],
        placeholder="Enter your name",
        key="onboarding_name_input",
        label_visibility="collapsed",
    )
    st.session_state["onboarding_name"] = name


def _render_step_learning_style() -> None:
    """Render the learning style selection step."""
    st.markdown(
        """
        <div style="text-align: center; margin-bottom: 1.5rem;">
            <h2 style="margin: 0;">How do you learn best?</h2>
            <p style="color: #666;">Sensei will adapt to your learning style.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    style_options = {
        LearningStyle.VISUAL: ("👁️ Visual", "Diagrams, images, and visual explanations"),
        LearningStyle.READING: ("📖 Reading", "Text-based explanations and documentation"),
        LearningStyle.HANDS_ON: ("💻 Hands-on", "Code examples and interactive exercises"),
    }
    
    current_idx = list(LearningStyle).index(st.session_state["onboarding_style"])
    
    for i, (style, (label, desc)) in enumerate(style_options.items()):
        is_selected = style == st.session_state["onboarding_style"]
        border_color = "#007bff" if is_selected else "#dee2e6"
        bg_color = "#e7f1ff" if is_selected else "#f8f9fa"
        
        if st.button(
            f"{label}\n{desc}",
            key=f"style_{style.value}",
            use_container_width=True,
        ):
            st.session_state["onboarding_style"] = style
            st.rerun()


def _render_step_experience() -> None:
    """Render the experience level selection step."""
    st.markdown(
        """
        <div style="text-align: center; margin-bottom: 1.5rem;">
            <h2 style="margin: 0;">What's your experience level?</h2>
            <p style="color: #666;">This helps Sensei adjust the difficulty.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    exp_options = {
        ExperienceLevel.BEGINNER: ("🌱 Beginner", "New to programming or this topic"),
        ExperienceLevel.INTERMEDIATE: ("🌿 Intermediate", "Some experience, looking to grow"),
        ExperienceLevel.ADVANCED: ("🌳 Advanced", "Experienced, want to master"),
    }
    
    for exp, (label, desc) in exp_options.items():
        if st.button(
            f"{label}\n{desc}",
            key=f"exp_{exp.value}",
            use_container_width=True,
        ):
            st.session_state["onboarding_experience"] = exp
            st.rerun()


def _render_step_goals() -> None:
    """Render the goals input step."""
    st.markdown(
        """
        <div style="text-align: center; margin-bottom: 1.5rem;">
            <h2 style="margin: 0;">What do you want to achieve?</h2>
            <p style="color: #666;">Share your learning goals with Sensei.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    goals = st.text_area(
        "Goals",
        value=st.session_state["onboarding_goals"],
        placeholder="e.g., Learn Python for data science, Master GPU programming...",
        key="onboarding_goals_input",
        label_visibility="collapsed",
        height=100,
    )
    st.session_state["onboarding_goals"] = goals


def _render_navigation(
    current_step: int,
    on_complete: Callable[[UserPreferences], None] | None,
) -> None:
    """Render the navigation buttons.
    
    Args:
        current_step: Current step.
        on_complete: Completion callback.
    """
    col1, col2 = st.columns(2)
    
    with col1:
        if current_step > 0:
            if st.button("← Back", use_container_width=True):
                st.session_state["onboarding_step"] = current_step - 1
                st.rerun()
    
    with col2:
        if current_step < 3:
            # Validate current step before allowing next
            can_proceed = True
            if current_step == 0 and not st.session_state["onboarding_name"].strip():
                can_proceed = False
            
            if st.button(
                "Next →",
                use_container_width=True,
                type="primary",
                disabled=not can_proceed,
            ):
                st.session_state["onboarding_step"] = current_step + 1
                st.rerun()
        else:
            # Complete button on last step
            if st.button(
                "🎉 Get Started",
                use_container_width=True,
                type="primary",
            ):
                # Create preferences
                prefs = UserPreferences(
                    name=st.session_state["onboarding_name"] or "Learner",
                    learning_style=st.session_state["onboarding_style"],
                    experience_level=st.session_state["onboarding_experience"],
                    goals=st.session_state["onboarding_goals"],
                    is_onboarded=True,
                )
                
                if on_complete:
                    on_complete(prefs)
                
                # Clear onboarding state
                for key in ["onboarding_name", "onboarding_style", "onboarding_experience", 
                           "onboarding_goals", "onboarding_step"]:
                    if key in st.session_state:
                        del st.session_state[key]


def render_onboarding_with_services(
    user_service,
    on_complete: Callable[[], None] | None = None,
) -> None:
    """Render the onboarding page with full service integration.
    
    Args:
        user_service: UserService instance.
        on_complete: Callback after onboarding is saved.
    
    Example:
        ```python
        render_onboarding_with_services(
            user_service=UserService(),
            on_complete=lambda: navigate_to_dashboard(),
        )
        ```
    """
    def handle_complete(prefs: UserPreferences):
        user_service.complete_onboarding(prefs)
        if on_complete:
            on_complete()
    
    render_onboarding_page(on_complete=handle_complete)
