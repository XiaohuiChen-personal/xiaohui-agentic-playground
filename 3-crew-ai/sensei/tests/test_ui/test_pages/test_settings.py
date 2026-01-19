"""Unit tests for settings page."""

from unittest.mock import MagicMock, patch

import pytest

from sensei.models.enums import ExperienceLevel, LearningStyle
from sensei.models.schemas import UserPreferences


@pytest.fixture
def sample_preferences():
    """Sample user preferences."""
    return UserPreferences(
        name="Test User",
        learning_style=LearningStyle.HANDS_ON,
        session_length_minutes=45,
        experience_level=ExperienceLevel.INTERMEDIATE,
        goals="Learn GPU programming",
        is_onboarded=True,
    )


class TestRenderSettingsPage:
    """Tests for render_settings_page function."""

    def test_render_settings_page_basic(self, mock_streamlit):
        """Test rendering settings page without errors."""
        with patch("sensei.ui.pages.settings.st", mock_streamlit):
            with patch("sensei.ui.components.sidebar.st", mock_streamlit):
                from sensei.ui.pages.settings import render_settings_page
                
                render_settings_page()
                
                mock_streamlit.markdown.assert_called()

    def test_render_settings_page_shows_header(self, mock_streamlit):
        """Test page shows header."""
        with patch("sensei.ui.pages.settings.st", mock_streamlit):
            with patch("sensei.ui.components.sidebar.st", mock_streamlit):
                from sensei.ui.pages.settings import render_settings_page
                
                render_settings_page()
                
                calls = mock_streamlit.markdown.call_args_list
                assert any("Settings" in str(c) for c in calls)

    def test_render_settings_page_shows_form(self, mock_streamlit):
        """Test page shows settings form."""
        with patch("sensei.ui.pages.settings.st", mock_streamlit):
            with patch("sensei.ui.components.sidebar.st", mock_streamlit):
                from sensei.ui.pages.settings import render_settings_page
                
                render_settings_page()
                
                mock_streamlit.form.assert_called()

    def test_render_settings_page_populates_values(
        self, mock_streamlit, sample_preferences
    ):
        """Test page populates form with existing preferences."""
        with patch("sensei.ui.pages.settings.st", mock_streamlit):
            with patch("sensei.ui.components.sidebar.st", mock_streamlit):
                from sensei.ui.pages.settings import render_settings_page
                
                render_settings_page(preferences=sample_preferences)
                
                # Should show text input for name
                mock_streamlit.text_input.assert_called()
                # Should show radio for learning style
                mock_streamlit.radio.assert_called()

    def test_render_settings_page_shows_save_button(
        self, mock_streamlit, sample_preferences
    ):
        """Test page shows save button."""
        with patch("sensei.ui.pages.settings.st", mock_streamlit):
            with patch("sensei.ui.components.sidebar.st", mock_streamlit):
                from sensei.ui.pages.settings import render_settings_page
                
                render_settings_page(preferences=sample_preferences)
                
                mock_streamlit.form_submit_button.assert_called()


class TestRenderHeader:
    """Tests for _render_header function."""

    def test_render_header_content(self, mock_streamlit):
        """Test header shows expected content."""
        with patch("sensei.ui.pages.settings.st", mock_streamlit):
            from sensei.ui.pages.settings import _render_header
            
            _render_header()
            
            calls = mock_streamlit.markdown.call_args_list
            assert any("Settings" in str(c) for c in calls)


class TestRenderSettingsWithServices:
    """Tests for render_settings_with_services function."""

    def test_render_with_services_loads_prefs(self, mock_streamlit):
        """Test service integration loads preferences."""
        with patch("sensei.ui.pages.settings.st", mock_streamlit):
            with patch("sensei.ui.components.sidebar.st", mock_streamlit):
                from sensei.ui.pages.settings import render_settings_with_services
                
                mock_user_service = MagicMock()
                mock_user_service.get_preferences.return_value = UserPreferences()
                
                render_settings_with_services(
                    user_service=mock_user_service,
                )
                
                mock_user_service.get_preferences.assert_called_once()
