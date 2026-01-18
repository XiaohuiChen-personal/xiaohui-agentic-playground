"""Unit tests for sidebar component."""

from unittest.mock import MagicMock, patch, call

import pytest


class TestRenderSidebar:
    """Tests for render_sidebar function."""

    def test_render_sidebar_default_page(self, mock_streamlit):
        """Test rendering sidebar with default dashboard page."""
        with patch("sensei.ui.components.sidebar.st", mock_streamlit):
            from sensei.ui.components.sidebar import render_sidebar
            
            result = render_sidebar()
            
            # Should use sidebar context
            mock_streamlit.sidebar.__enter__.assert_called()
            # Should render markdown for logo
            mock_streamlit.markdown.assert_called()
            # Should render divider
            mock_streamlit.divider.assert_called()
            # Should not return navigation (no button clicked)
            assert result is None

    def test_render_sidebar_with_current_page(self, mock_streamlit):
        """Test rendering sidebar with specific current page."""
        with patch("sensei.ui.components.sidebar.st", mock_streamlit):
            from sensei.ui.components.sidebar import render_sidebar
            
            result = render_sidebar(current_page="settings")
            
            # Should render without error
            assert result is None

    def test_render_sidebar_with_callback(self, mock_streamlit):
        """Test rendering sidebar with navigation callback."""
        with patch("sensei.ui.components.sidebar.st", mock_streamlit):
            from sensei.ui.components.sidebar import render_sidebar
            
            callback = MagicMock()
            result = render_sidebar(current_page="dashboard", on_navigate=callback)
            
            # Callback should not be called (no button clicked)
            callback.assert_not_called()
            assert result is None

    def test_render_sidebar_button_click(self, mock_streamlit):
        """Test sidebar navigation when button is clicked."""
        mock_streamlit.button.return_value = True
        
        with patch("sensei.ui.components.sidebar.st", mock_streamlit):
            from sensei.ui.components.sidebar import render_sidebar
            
            callback = MagicMock()
            result = render_sidebar(current_page="dashboard", on_navigate=callback)
            
            # Button click should trigger callback
            assert callback.called
            # Result should be the clicked page
            assert result is not None

    def test_render_sidebar_with_course_outline(self, mock_streamlit, sample_course_outline):
        """Test rendering sidebar with course outline in learning mode."""
        with patch("sensei.ui.components.sidebar.st", mock_streamlit):
            from sensei.ui.components.sidebar import render_sidebar
            
            result = render_sidebar(
                current_page="learning",
                course_outline=sample_course_outline,
                current_module_idx=0,
                current_concept_idx=1,
            )
            
            # Should render expanders for modules
            mock_streamlit.expander.assert_called()
            assert result is None

    def test_render_sidebar_with_course_outline_completed_module(
        self, mock_streamlit, sample_course_outline
    ):
        """Test sidebar with completed module highlighted."""
        with patch("sensei.ui.components.sidebar.st", mock_streamlit):
            from sensei.ui.components.sidebar import render_sidebar
            
            render_sidebar(
                current_page="learning",
                course_outline=sample_course_outline,
                current_module_idx=2,  # Third module (modules 0,1 completed)
                current_concept_idx=0,
            )
            
            # Should render without error
            mock_streamlit.expander.assert_called()

    def test_render_sidebar_with_empty_course_outline(self, mock_streamlit):
        """Test sidebar with course outline but no modules."""
        with patch("sensei.ui.components.sidebar.st", mock_streamlit):
            from sensei.ui.components.sidebar import render_sidebar
            
            empty_course = {"title": "Empty Course", "modules": []}
            render_sidebar(
                current_page="learning",
                course_outline=empty_course,
            )
            
            # Should handle empty modules gracefully
            mock_streamlit.markdown.assert_called()

    def test_render_sidebar_course_outline_missing_title(self, mock_streamlit):
        """Test sidebar with course outline missing title."""
        with patch("sensei.ui.components.sidebar.st", mock_streamlit):
            from sensei.ui.components.sidebar import render_sidebar
            
            course = {"modules": []}
            render_sidebar(
                current_page="learning",
                course_outline=course,
            )
            
            # Should use default title
            mock_streamlit.markdown.assert_called()


class TestRenderSimpleSidebar:
    """Tests for render_simple_sidebar function."""

    def test_render_simple_sidebar_default(self, mock_streamlit):
        """Test simple sidebar with default dashboard page."""
        mock_streamlit.radio.return_value = "📚 Dashboard"
        
        with patch("sensei.ui.components.sidebar.st", mock_streamlit):
            from sensei.ui.components.sidebar import render_simple_sidebar
            
            result = render_simple_sidebar()
            
            # Should return dashboard page
            assert result == "dashboard"
            # Should use radio button
            mock_streamlit.radio.assert_called()

    def test_render_simple_sidebar_settings_selected(self, mock_streamlit):
        """Test simple sidebar with settings page selected."""
        mock_streamlit.radio.return_value = "⚙️ Settings"
        
        with patch("sensei.ui.components.sidebar.st", mock_streamlit):
            from sensei.ui.components.sidebar import render_simple_sidebar
            
            result = render_simple_sidebar(current_page="settings")
            
            assert result == "settings"

    def test_render_simple_sidebar_new_course_selected(self, mock_streamlit):
        """Test simple sidebar with new course page selected."""
        mock_streamlit.radio.return_value = "➕ New Course"
        
        with patch("sensei.ui.components.sidebar.st", mock_streamlit):
            from sensei.ui.components.sidebar import render_simple_sidebar
            
            result = render_simple_sidebar()
            
            assert result == "new_course"

    def test_render_simple_sidebar_progress_selected(self, mock_streamlit):
        """Test simple sidebar with progress page selected."""
        mock_streamlit.radio.return_value = "📊 Progress"
        
        with patch("sensei.ui.components.sidebar.st", mock_streamlit):
            from sensei.ui.components.sidebar import render_simple_sidebar
            
            result = render_simple_sidebar()
            
            assert result == "progress"

    def test_render_simple_sidebar_unknown_page(self, mock_streamlit):
        """Test simple sidebar with unknown current page falls back to dashboard."""
        mock_streamlit.radio.return_value = "📚 Dashboard"
        
        with patch("sensei.ui.components.sidebar.st", mock_streamlit):
            from sensei.ui.components.sidebar import render_simple_sidebar
            
            result = render_simple_sidebar(current_page="unknown_page")
            
            # Should still work and default to dashboard
            assert result == "dashboard"


class TestRenderLearningSidebar:
    """Tests for render_learning_sidebar function."""

    def test_render_learning_sidebar_basic(self, mock_streamlit, sample_course_outline):
        """Test learning sidebar with basic course data."""
        with patch("sensei.ui.components.sidebar.st", mock_streamlit):
            from sensei.ui.components.sidebar import render_learning_sidebar
            
            render_learning_sidebar(
                course=sample_course_outline,
                current_module_idx=0,
                current_concept_idx=0,
            )
            
            # Should render back button
            mock_streamlit.button.assert_called()
            # Should render dividers
            mock_streamlit.divider.assert_called()

    def test_render_learning_sidebar_with_back_callback(
        self, mock_streamlit, sample_course_outline
    ):
        """Test learning sidebar back button callback."""
        mock_streamlit.button.return_value = True
        
        with patch("sensei.ui.components.sidebar.st", mock_streamlit):
            from sensei.ui.components.sidebar import render_learning_sidebar
            
            callback = MagicMock()
            render_learning_sidebar(
                course=sample_course_outline,
                current_module_idx=0,
                current_concept_idx=0,
                on_back=callback,
            )
            
            # Callback should be triggered
            callback.assert_called_once()

    def test_render_learning_sidebar_no_callback(
        self, mock_streamlit, sample_course_outline
    ):
        """Test learning sidebar without back callback."""
        mock_streamlit.button.return_value = True
        
        with patch("sensei.ui.components.sidebar.st", mock_streamlit):
            from sensei.ui.components.sidebar import render_learning_sidebar
            
            # Should not raise error when no callback provided
            render_learning_sidebar(
                course=sample_course_outline,
                current_module_idx=0,
                current_concept_idx=0,
                on_back=None,
            )

    def test_render_learning_sidebar_middle_module(
        self, mock_streamlit, sample_course_outline
    ):
        """Test learning sidebar in middle of course."""
        with patch("sensei.ui.components.sidebar.st", mock_streamlit):
            from sensei.ui.components.sidebar import render_learning_sidebar
            
            render_learning_sidebar(
                course=sample_course_outline,
                current_module_idx=1,
                current_concept_idx=2,
            )
            
            # Should render without error
            mock_streamlit.expander.assert_called()

    def test_render_learning_sidebar_last_module(
        self, mock_streamlit, sample_course_outline
    ):
        """Test learning sidebar on last module."""
        with patch("sensei.ui.components.sidebar.st", mock_streamlit):
            from sensei.ui.components.sidebar import render_learning_sidebar
            
            render_learning_sidebar(
                course=sample_course_outline,
                current_module_idx=2,
                current_concept_idx=2,
            )
            
            mock_streamlit.expander.assert_called()


class TestRenderCourseOutlinePrivate:
    """Tests for _render_course_outline private function."""

    def test_render_course_outline_all_modules_completed(
        self, mock_streamlit, sample_course_outline
    ):
        """Test course outline when all modules are completed."""
        with patch("sensei.ui.components.sidebar.st", mock_streamlit):
            from sensei.ui.components.sidebar import _render_course_outline
            
            # Module idx beyond all modules means all completed
            _render_course_outline(
                course=sample_course_outline,
                current_module_idx=3,  # Beyond last module
                current_concept_idx=0,
            )
            
            mock_streamlit.expander.assert_called()

    def test_render_course_outline_concept_status_from_value(
        self, mock_streamlit
    ):
        """Test course outline with concept status as string value."""
        course = {
            "title": "Test Course",
            "modules": [
                {
                    "title": "Module 1",
                    "concepts": [
                        {"title": "Concept 1", "status": "completed"},
                        {"title": "Concept 2", "status": "in_progress"},
                        {"title": "Concept 3", "status": "not_started"},
                    ],
                }
            ],
        }
        
        with patch("sensei.ui.components.sidebar.st", mock_streamlit):
            from sensei.ui.components.sidebar import _render_course_outline
            
            _render_course_outline(
                course=course,
                current_module_idx=0,
                current_concept_idx=1,
            )
            
            mock_streamlit.markdown.assert_called()

    def test_render_course_outline_missing_concept_status(self, mock_streamlit):
        """Test course outline when concept has no status field."""
        course = {
            "title": "Test",
            "modules": [
                {
                    "title": "Module 1",
                    "concepts": [{"title": "No Status Concept"}],
                }
            ],
        }
        
        with patch("sensei.ui.components.sidebar.st", mock_streamlit):
            from sensei.ui.components.sidebar import _render_course_outline
            
            _render_course_outline(course, 0, 0)
            
            # Should handle missing status gracefully
            mock_streamlit.markdown.assert_called()

    def test_render_course_outline_missing_module_title(self, mock_streamlit):
        """Test course outline when module has no title."""
        course = {
            "title": "Test",
            "modules": [
                {"concepts": [{"title": "Concept"}]}
            ],
        }
        
        with patch("sensei.ui.components.sidebar.st", mock_streamlit):
            from sensei.ui.components.sidebar import _render_course_outline
            
            _render_course_outline(course, 0, 0)
            
            # Should use default title
            mock_streamlit.expander.assert_called()

    def test_render_course_outline_missing_concept_title(self, mock_streamlit):
        """Test course outline when concept has no title."""
        course = {
            "title": "Test",
            "modules": [
                {"title": "Module 1", "concepts": [{}]}
            ],
        }
        
        with patch("sensei.ui.components.sidebar.st", mock_streamlit):
            from sensei.ui.components.sidebar import _render_course_outline
            
            _render_course_outline(course, 0, 0)
            
            mock_streamlit.markdown.assert_called()


class TestRenderNavigationPrivate:
    """Tests for _render_navigation private function."""

    def test_render_navigation_all_pages(self, mock_streamlit):
        """Test navigation renders all pages."""
        with patch("sensei.ui.components.sidebar.st", mock_streamlit):
            from sensei.ui.components.sidebar import _render_navigation
            
            result = _render_navigation("dashboard", None)
            
            # Should render buttons for each nav item
            assert mock_streamlit.button.call_count >= 4
            assert result is None

    def test_render_navigation_with_callback_triggered(self, mock_streamlit):
        """Test navigation callback is triggered on button click."""
        mock_streamlit.button.return_value = True
        
        with patch("sensei.ui.components.sidebar.st", mock_streamlit):
            from sensei.ui.components.sidebar import _render_navigation
            
            callback = MagicMock()
            result = _render_navigation("dashboard", callback)
            
            # Callback should be called
            assert callback.called
            # Result should be the selected page
            assert result is not None

    def test_render_navigation_active_page_primary_type(self, mock_streamlit):
        """Test that active page button has primary type."""
        button_calls = []
        
        def track_button(*args, **kwargs):
            button_calls.append(kwargs)
            return False
        
        mock_streamlit.button.side_effect = track_button
        
        with patch("sensei.ui.components.sidebar.st", mock_streamlit):
            from sensei.ui.components.sidebar import _render_navigation
            
            _render_navigation("dashboard", None)
            
            # At least one button should have type="primary"
            primary_buttons = [c for c in button_calls if c.get("type") == "primary"]
            assert len(primary_buttons) >= 1
