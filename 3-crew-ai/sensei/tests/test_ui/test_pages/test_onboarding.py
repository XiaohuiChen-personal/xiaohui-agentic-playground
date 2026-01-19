"""Unit tests for onboarding page."""

from unittest.mock import MagicMock, patch

import pytest

from sensei.models.enums import ExperienceLevel, LearningStyle
from sensei.models.schemas import UserPreferences


class TestRenderOnboardingPage:
    """Tests for render_onboarding_page function."""

    def test_render_onboarding_page_basic(self, mock_streamlit):
        """Test rendering onboarding page without errors."""
        with patch("sensei.ui.pages.onboarding.st", mock_streamlit):
            from sensei.ui.pages.onboarding import render_onboarding_page
            
            render_onboarding_page()
            
            mock_streamlit.markdown.assert_called()

    def test_render_onboarding_page_shows_welcome(self, mock_streamlit):
        """Test page shows welcome message."""
        with patch("sensei.ui.pages.onboarding.st", mock_streamlit):
            from sensei.ui.pages.onboarding import render_onboarding_page
            
            render_onboarding_page()
            
            calls = mock_streamlit.markdown.call_args_list
            assert any("Welcome" in str(c) for c in calls)

    def test_render_onboarding_page_shows_step_name(self, mock_streamlit):
        """Test first step shows name input."""
        with patch("sensei.ui.pages.onboarding.st", mock_streamlit):
            from sensei.ui.pages.onboarding import render_onboarding_page
            
            render_onboarding_page(current_step=0)
            
            calls = mock_streamlit.markdown.call_args_list
            assert any("name" in str(c).lower() for c in calls)

    def test_render_onboarding_page_shows_progress_indicator(self, mock_streamlit):
        """Test page shows step progress."""
        with patch("sensei.ui.pages.onboarding.st", mock_streamlit):
            from sensei.ui.pages.onboarding import render_onboarding_page
            
            render_onboarding_page(current_step=1)
            
            calls = mock_streamlit.markdown.call_args_list
            assert any("Step" in str(c) for c in calls)

    def test_render_onboarding_page_navigation_buttons(self, mock_streamlit):
        """Test page shows navigation buttons."""
        with patch("sensei.ui.pages.onboarding.st", mock_streamlit):
            from sensei.ui.pages.onboarding import render_onboarding_page
            
            render_onboarding_page(current_step=1)
            
            mock_streamlit.button.assert_called()


class TestRenderProgressIndicator:
    """Tests for _render_progress_indicator function."""

    def test_render_progress_indicator_step_0(self, mock_streamlit):
        """Test progress indicator at step 0."""
        with patch("sensei.ui.pages.onboarding.st", mock_streamlit):
            from sensei.ui.pages.onboarding import _render_progress_indicator
            
            _render_progress_indicator(0)
            
            calls = mock_streamlit.markdown.call_args_list
            assert any("Step 1" in str(c) for c in calls)

    def test_render_progress_indicator_step_3(self, mock_streamlit):
        """Test progress indicator at last step."""
        with patch("sensei.ui.pages.onboarding.st", mock_streamlit):
            from sensei.ui.pages.onboarding import _render_progress_indicator
            
            _render_progress_indicator(3)
            
            calls = mock_streamlit.markdown.call_args_list
            assert any("Step 4" in str(c) for c in calls)


class TestRenderStepName:
    """Tests for _render_step_name function."""

    def test_render_step_name_shows_input(self, mock_streamlit):
        """Test name step shows text input."""
        # Initialize required session state
        mock_streamlit.session_state = {"onboarding_name": ""}
        
        with patch("sensei.ui.pages.onboarding.st", mock_streamlit):
            from sensei.ui.pages.onboarding import _render_step_name
            
            _render_step_name()
            
            mock_streamlit.text_input.assert_called()


class TestRenderStepLearningStyle:
    """Tests for _render_step_learning_style function."""

    def test_render_step_learning_style_shows_options(self, mock_streamlit):
        """Test learning style step shows options."""
        # Initialize required session state
        mock_streamlit.session_state = {
            "onboarding_style": LearningStyle.READING
        }
        
        with patch("sensei.ui.pages.onboarding.st", mock_streamlit):
            from sensei.ui.pages.onboarding import _render_step_learning_style
            
            _render_step_learning_style()
            
            # Should show buttons for each style
            mock_streamlit.button.assert_called()


class TestRenderStepExperience:
    """Tests for _render_step_experience function."""

    def test_render_step_experience_shows_options(self, mock_streamlit):
        """Test experience step shows options."""
        with patch("sensei.ui.pages.onboarding.st", mock_streamlit):
            from sensei.ui.pages.onboarding import _render_step_experience
            
            _render_step_experience()
            
            mock_streamlit.button.assert_called()


class TestRenderStepGoals:
    """Tests for _render_step_goals function."""

    def test_render_step_goals_shows_textarea(self, mock_streamlit):
        """Test goals step shows text area."""
        # Initialize required session state
        mock_streamlit.session_state = {"onboarding_goals": ""}
        
        with patch("sensei.ui.pages.onboarding.st", mock_streamlit):
            from sensei.ui.pages.onboarding import _render_step_goals
            
            _render_step_goals()
            
            mock_streamlit.text_area.assert_called()


class TestRenderOnboardingWithServices:
    """Tests for render_onboarding_with_services function."""

    def test_render_with_services_basic(self, mock_streamlit):
        """Test service integration works."""
        with patch("sensei.ui.pages.onboarding.st", mock_streamlit):
            from sensei.ui.pages.onboarding import render_onboarding_with_services
            
            mock_user_service = MagicMock()
            
            render_onboarding_with_services(
                user_service=mock_user_service,
            )
            
            # Should render without error
            mock_streamlit.markdown.assert_called()
