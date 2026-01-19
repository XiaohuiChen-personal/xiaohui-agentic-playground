"""Settings page for Sensei.

This module provides the user preferences page with:
- Name input
- Learning style selector
- Session length selector
- Experience level selector
- Goals text area
- Save button
"""

from typing import Callable

import streamlit as st

from sensei.models.enums import ExperienceLevel, LearningStyle
from sensei.models.schemas import UserPreferences
from sensei.ui.components import render_sidebar


def render_settings_page(
    preferences: UserPreferences | None = None,
    current_page: str = "settings",
    on_navigate: Callable[[str], None] | None = None,
    on_save: Callable[[UserPreferences], None] | None = None,
) -> None:
    """Render the settings page.
    
    Args:
        preferences: Current user preferences to populate form.
        current_page: Current page for sidebar highlighting.
        on_navigate: Callback for sidebar navigation.
        on_save: Callback when preferences are saved.
    
    Example:
        ```python
        render_settings_page(
            preferences=user_service.get_preferences(),
            on_save=lambda prefs: user_service.set_preferences(prefs),
        )
        ```
    """
    # Default preferences
    if not preferences:
        preferences = UserPreferences()
    
    # Render sidebar
    render_sidebar(current_page=current_page, on_navigate=on_navigate)
    
    # Page header
    _render_header()
    
    # Settings form
    with st.form("settings_form"):
        # Profile section
        st.markdown("### 👤 Profile")
        
        name = st.text_input(
            "Name",
            value=preferences.name,
            placeholder="Enter your name",
            help="This is how Sensei will address you.",
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Learning preferences section
        st.markdown("### 📚 Learning Preferences")
        
        # Learning style
        learning_style_options = {
            LearningStyle.VISUAL: "Visual (diagrams, images)",
            LearningStyle.READING: "Reading (text explanations)",
            LearningStyle.HANDS_ON: "Hands-on (code examples)",
        }
        
        current_style_idx = list(LearningStyle).index(preferences.learning_style)
        learning_style = st.radio(
            "Learning Style",
            options=list(learning_style_options.keys()),
            format_func=lambda x: learning_style_options[x],
            index=current_style_idx,
            help="How do you prefer to learn?",
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Session length
        session_options = [15, 30, 45, 60, 90, 120]
        session_labels = {
            15: "15 minutes",
            30: "30 minutes",
            45: "45 minutes",
            60: "1 hour",
            90: "1.5 hours",
            120: "2 hours",
        }
        
        current_session = preferences.session_length_minutes
        if current_session not in session_options:
            current_session = 30
        
        session_length = st.selectbox(
            "Preferred Session Length",
            options=session_options,
            format_func=lambda x: session_labels.get(x, f"{x} minutes"),
            index=session_options.index(current_session),
            help="How long do you prefer to study in one session?",
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Experience level
        experience_options = {
            ExperienceLevel.BEGINNER: "Beginner",
            ExperienceLevel.INTERMEDIATE: "Intermediate",
            ExperienceLevel.ADVANCED: "Advanced",
        }
        
        current_exp_idx = list(ExperienceLevel).index(preferences.experience_level)
        experience_level = st.radio(
            "Experience Level",
            options=list(experience_options.keys()),
            format_func=lambda x: experience_options[x],
            index=current_exp_idx,
            help="Your general programming/learning experience.",
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Learning goals section
        st.markdown("### 🎯 Learning Goals")
        
        goals = st.text_area(
            "What are your learning goals?",
            value=preferences.goals or "",
            placeholder="e.g., Learn GPU programming for ML projects",
            help="What do you hope to achieve with Sensei?",
            height=100,
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Submit button
        col1, col2, col3 = st.columns([0.3, 0.4, 0.3])
        with col2:
            submitted = st.form_submit_button(
                "💾 Save Settings",
                use_container_width=True,
                type="primary",
            )
        
        if submitted:
            # Create updated preferences
            new_prefs = UserPreferences(
                name=name or "Learner",
                learning_style=learning_style,
                session_length_minutes=session_length,
                experience_level=experience_level,
                goals=goals or "",
                is_onboarded=preferences.is_onboarded,
            )
            
            if on_save:
                on_save(new_prefs)
            
            st.success("✅ Settings saved successfully!")


def _render_header() -> None:
    """Render the page header."""
    st.markdown(
        """
        <div style="padding: 1rem 0; margin-bottom: 0.5rem;">
            <h1 style="margin: 0; font-size: 1.75rem;">⚙️ Settings</h1>
            <p style="color: #666; margin-top: 0.25rem;">
                Customize your learning experience
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_settings_with_services(
    user_service,
    on_navigate: Callable[[str], None] | None = None,
) -> None:
    """Render the settings page with full service integration.
    
    Args:
        user_service: UserService instance.
        on_navigate: Navigation callback.
    
    Example:
        ```python
        render_settings_with_services(
            user_service=UserService(),
            on_navigate=lambda page: set_page(page),
        )
        ```
    """
    preferences = user_service.get_preferences()
    
    def handle_save(new_prefs: UserPreferences):
        user_service.set_preferences(new_prefs)
    
    render_settings_page(
        preferences=preferences,
        on_navigate=on_navigate,
        on_save=handle_save,
    )
