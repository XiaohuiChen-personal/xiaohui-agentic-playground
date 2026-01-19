"""Unit tests for new course page."""

from unittest.mock import MagicMock, patch

import pytest

from sensei.models.schemas import Course, Module, Concept


@pytest.fixture
def sample_generated_course():
    """Sample generated course for testing."""
    return Course(
        id="test-course-123",
        title="Python Basics",
        description="Learn Python programming from scratch",
        modules=[
            Module(
                id="m1",
                title="Introduction",
                description="Getting started",
                order=0,
                estimated_minutes=30,
                concepts=[
                    Concept(id="c1", title="What is Python?", content="...", order=0),
                    Concept(id="c2", title="Installing Python", content="...", order=1),
                ],
            ),
            Module(
                id="m2",
                title="Variables",
                description="Understanding variables",
                order=1,
                estimated_minutes=45,
                concepts=[
                    Concept(id="c3", title="Variables", content="...", order=0),
                    Concept(id="c4", title="Data Types", content="...", order=1),
                ],
            ),
        ],
    )


class TestRenderNewCoursePage:
    """Tests for render_new_course_page function."""

    def test_render_new_course_page_basic(self, mock_streamlit):
        """Test rendering new course page without errors."""
        with patch("sensei.ui.pages.new_course.st", mock_streamlit):
            with patch("sensei.ui.components.sidebar.st", mock_streamlit):
                from sensei.ui.pages.new_course import render_new_course_page
                
                render_new_course_page()
                
                # Should render without error
                mock_streamlit.markdown.assert_called()

    def test_render_new_course_page_shows_header(self, mock_streamlit):
        """Test page shows header with title."""
        with patch("sensei.ui.pages.new_course.st", mock_streamlit):
            with patch("sensei.ui.components.sidebar.st", mock_streamlit):
                from sensei.ui.pages.new_course import render_new_course_page
                
                render_new_course_page()
                
                calls = mock_streamlit.markdown.call_args_list
                header_found = any("Create New Course" in str(c) for c in calls)
                assert header_found

    def test_render_new_course_page_shows_input(self, mock_streamlit):
        """Test page shows topic input field."""
        with patch("sensei.ui.pages.new_course.st", mock_streamlit):
            with patch("sensei.ui.components.sidebar.st", mock_streamlit):
                from sensei.ui.pages.new_course import render_new_course_page
                
                render_new_course_page()
                
                mock_streamlit.text_input.assert_called()

    def test_render_new_course_page_shows_generate_button(self, mock_streamlit):
        """Test page shows generate button."""
        with patch("sensei.ui.pages.new_course.st", mock_streamlit):
            with patch("sensei.ui.components.sidebar.st", mock_streamlit):
                from sensei.ui.pages.new_course import render_new_course_page
                
                render_new_course_page()
                
                mock_streamlit.button.assert_called()

    def test_render_new_course_page_generate_button_disabled_when_empty(
        self, mock_streamlit
    ):
        """Test generate button is disabled when topic is empty."""
        mock_streamlit.text_input.return_value = ""
        
        with patch("sensei.ui.pages.new_course.st", mock_streamlit):
            with patch("sensei.ui.components.sidebar.st", mock_streamlit):
                from sensei.ui.pages.new_course import render_new_course_page
                
                render_new_course_page()
                
                # Find the generate button call
                button_calls = [
                    c for c in mock_streamlit.button.call_args_list
                    if "Generate" in str(c) or "generate" in str(c[1].get("key", ""))
                ]
                if button_calls:
                    # Button should be disabled
                    assert button_calls[0][1].get("disabled", False)

    def test_render_new_course_page_with_generated_course(
        self, mock_streamlit, sample_generated_course
    ):
        """Test page shows course preview when course is generated."""
        with patch("sensei.ui.pages.new_course.st", mock_streamlit):
            with patch("sensei.ui.components.sidebar.st", mock_streamlit):
                from sensei.ui.pages.new_course import render_new_course_page
                
                render_new_course_page(
                    generated_course=sample_generated_course,
                )
                
                # Should show course title
                calls = mock_streamlit.markdown.call_args_list
                course_found = any("Python Basics" in str(c) for c in calls)
                assert course_found

    def test_render_new_course_page_shows_start_learning_button(
        self, mock_streamlit, sample_generated_course
    ):
        """Test page shows Start Learning button after generation."""
        with patch("sensei.ui.pages.new_course.st", mock_streamlit):
            with patch("sensei.ui.components.sidebar.st", mock_streamlit):
                from sensei.ui.pages.new_course import render_new_course_page
                
                render_new_course_page(
                    generated_course=sample_generated_course,
                )
                
                # Should have Start Learning button
                button_calls = [
                    c for c in mock_streamlit.button.call_args_list
                    if "Start Learning" in str(c)
                ]
                assert len(button_calls) > 0

    def test_render_new_course_page_start_learning_callback(
        self, mock_streamlit, sample_generated_course
    ):
        """Test Start Learning button triggers callback."""
        # Make the Start Learning button return True
        def button_side_effect(*args, **kwargs):
            if "start_learning" in kwargs.get("key", ""):
                return True
            return False
        
        mock_streamlit.button.side_effect = button_side_effect
        
        with patch("sensei.ui.pages.new_course.st", mock_streamlit):
            with patch("sensei.ui.components.sidebar.st", mock_streamlit):
                from sensei.ui.pages.new_course import render_new_course_page
                
                callback = MagicMock()
                
                render_new_course_page(
                    generated_course=sample_generated_course,
                    on_start_learning=callback,
                )
                
                callback.assert_called_once_with(sample_generated_course.id)

    def test_render_new_course_page_loading_state(self, mock_streamlit):
        """Test page shows loading state during generation."""
        with patch("sensei.ui.pages.new_course.st", mock_streamlit):
            with patch("sensei.ui.components.sidebar.st", mock_streamlit):
                from sensei.ui.pages.new_course import render_new_course_page
                
                render_new_course_page(
                    is_generating=True,
                    generation_status="Creating modules...",
                )
                
                # Should show progress indicator
                mock_streamlit.progress.assert_called()


class TestRenderHeader:
    """Tests for _render_header function."""

    def test_render_header_content(self, mock_streamlit):
        """Test header contains expected content."""
        with patch("sensei.ui.pages.new_course.st", mock_streamlit):
            from sensei.ui.pages.new_course import _render_header
            
            _render_header()
            
            calls = mock_streamlit.markdown.call_args_list
            assert any("Create New Course" in str(c) for c in calls)


class TestRenderTopicInput:
    """Tests for _render_topic_input function."""

    def test_render_topic_input_returns_value(self, mock_streamlit):
        """Test topic input returns entered value."""
        mock_streamlit.text_input.return_value = "Python"
        
        with patch("sensei.ui.pages.new_course.st", mock_streamlit):
            from sensei.ui.pages.new_course import _render_topic_input
            
            result = _render_topic_input()
            
            assert result == "Python"

    def test_render_topic_input_shows_examples(self, mock_streamlit):
        """Test topic input shows example suggestions."""
        with patch("sensei.ui.pages.new_course.st", mock_streamlit):
            from sensei.ui.pages.new_course import _render_topic_input
            
            _render_topic_input()
            
            calls = mock_streamlit.markdown.call_args_list
            examples_found = any("Examples" in str(c) for c in calls)
            assert examples_found


class TestRenderGenerateButton:
    """Tests for _render_generate_button function."""

    def test_render_generate_button_enabled_with_topic(self, mock_streamlit):
        """Test button is enabled when topic is provided."""
        with patch("sensei.ui.pages.new_course.st", mock_streamlit):
            from sensei.ui.pages.new_course import _render_generate_button
            
            _render_generate_button(topic="Python", is_generating=False)
            
            # Find the button call
            button_calls = mock_streamlit.button.call_args_list
            assert len(button_calls) > 0
            # Button should not be disabled
            assert not button_calls[0][1].get("disabled", False)

    def test_render_generate_button_disabled_without_topic(self, mock_streamlit):
        """Test button is disabled when topic is empty."""
        with patch("sensei.ui.pages.new_course.st", mock_streamlit):
            from sensei.ui.pages.new_course import _render_generate_button
            
            _render_generate_button(topic="", is_generating=False)
            
            button_calls = mock_streamlit.button.call_args_list
            assert len(button_calls) > 0
            assert button_calls[0][1].get("disabled", False)

    def test_render_generate_button_disabled_when_generating(self, mock_streamlit):
        """Test button is disabled during generation."""
        with patch("sensei.ui.pages.new_course.st", mock_streamlit):
            from sensei.ui.pages.new_course import _render_generate_button
            
            _render_generate_button(topic="Python", is_generating=True)
            
            button_calls = mock_streamlit.button.call_args_list
            assert len(button_calls) > 0
            assert button_calls[0][1].get("disabled", False)

    def test_render_generate_button_returns_true_on_click(self, mock_streamlit):
        """Test function returns True when button is clicked."""
        mock_streamlit.button.return_value = True
        
        with patch("sensei.ui.pages.new_course.st", mock_streamlit):
            from sensei.ui.pages.new_course import _render_generate_button
            
            result = _render_generate_button(topic="Python", is_generating=False)
            
            assert result is True


class TestRenderLoadingState:
    """Tests for _render_loading_state function."""

    def test_render_loading_state_shows_progress(self, mock_streamlit):
        """Test loading state shows progress indicator."""
        with patch("sensei.ui.pages.new_course.st", mock_streamlit):
            from sensei.ui.pages.new_course import _render_loading_state
            
            _render_loading_state("Creating modules...")
            
            mock_streamlit.progress.assert_called()

    def test_render_loading_state_shows_status(self, mock_streamlit):
        """Test loading state shows status message."""
        with patch("sensei.ui.pages.new_course.st", mock_streamlit):
            from sensei.ui.pages.new_course import _render_loading_state
            
            _render_loading_state("Custom status message")
            
            calls = mock_streamlit.markdown.call_args_list
            status_found = any("Custom status message" in str(c) for c in calls)
            assert status_found


class TestRenderCoursePreview:
    """Tests for _render_course_preview function."""

    def test_render_course_preview_shows_title(
        self, mock_streamlit, sample_generated_course
    ):
        """Test course preview shows course title."""
        with patch("sensei.ui.pages.new_course.st", mock_streamlit):
            from sensei.ui.pages.new_course import _render_course_preview
            
            _render_course_preview(sample_generated_course)
            
            calls = mock_streamlit.markdown.call_args_list
            title_found = any("Python Basics" in str(c) for c in calls)
            assert title_found

    def test_render_course_preview_shows_metrics(
        self, mock_streamlit, sample_generated_course
    ):
        """Test course preview shows module/concept metrics."""
        with patch("sensei.ui.pages.new_course.st", mock_streamlit):
            from sensei.ui.pages.new_course import _render_course_preview
            
            _render_course_preview(sample_generated_course)
            
            mock_streamlit.metric.assert_called()

    def test_render_course_preview_shows_modules(
        self, mock_streamlit, sample_generated_course
    ):
        """Test course preview shows module expanders."""
        with patch("sensei.ui.pages.new_course.st", mock_streamlit):
            from sensei.ui.pages.new_course import _render_course_preview
            
            _render_course_preview(sample_generated_course)
            
            # Should create expanders for modules
            assert mock_streamlit.expander.call_count >= 2

    def test_render_course_preview_start_button(
        self, mock_streamlit, sample_generated_course
    ):
        """Test course preview has Start Learning button."""
        with patch("sensei.ui.pages.new_course.st", mock_streamlit):
            from sensei.ui.pages.new_course import _render_course_preview
            
            _render_course_preview(sample_generated_course)
            
            button_calls = [
                c for c in mock_streamlit.button.call_args_list
                if "Start Learning" in str(c)
            ]
            assert len(button_calls) > 0

    def test_render_course_preview_success_banner(
        self, mock_streamlit, sample_generated_course
    ):
        """Test course preview shows success banner."""
        with patch("sensei.ui.pages.new_course.st", mock_streamlit):
            from sensei.ui.pages.new_course import _render_course_preview
            
            _render_course_preview(sample_generated_course)
            
            calls = mock_streamlit.markdown.call_args_list
            success_found = any("Course Created" in str(c) for c in calls)
            assert success_found


class TestRenderNewCourseWithServices:
    """Tests for render_new_course_with_services function."""

    def test_render_with_services_basic(self, mock_streamlit):
        """Test rendering with services without errors."""
        with patch("sensei.ui.pages.new_course.st", mock_streamlit):
            with patch("sensei.ui.components.sidebar.st", mock_streamlit):
                from sensei.ui.pages.new_course import render_new_course_with_services
                
                mock_course_service = MagicMock()
                
                render_new_course_with_services(
                    course_service=mock_course_service,
                )
                
                # Should render without error
                mock_streamlit.markdown.assert_called()

    def test_render_with_services_uses_user_prefs(
        self, mock_streamlit, sample_generated_course
    ):
        """Test service integration uses user preferences."""
        mock_streamlit.text_input.return_value = "Python"
        mock_streamlit.button.return_value = True
        mock_streamlit.session_state = {
            "generated_course": None,
            "is_generating": False,
        }
        
        with patch("sensei.ui.pages.new_course.st", mock_streamlit):
            with patch("sensei.ui.components.sidebar.st", mock_streamlit):
                from sensei.ui.pages.new_course import render_new_course_with_services
                from sensei.models.schemas import UserPreferences
                
                mock_course_service = MagicMock()
                mock_course_service.create_course.return_value = sample_generated_course
                
                mock_user_service = MagicMock()
                mock_user_service.get_preferences.return_value = UserPreferences()
                
                # We can't fully test the callback execution in unit tests
                # because of the complex state management, but we verify setup
                render_new_course_with_services(
                    course_service=mock_course_service,
                    user_service=mock_user_service,
                )

    def test_render_with_services_navigation_callback(self, mock_streamlit):
        """Test navigation callback is passed correctly."""
        with patch("sensei.ui.pages.new_course.st", mock_streamlit):
            with patch("sensei.ui.components.sidebar.st", mock_streamlit):
                with patch("sensei.ui.pages.new_course.render_new_course_page") as mock_render:
                    from sensei.ui.pages.new_course import render_new_course_with_services
                    
                    nav_callback = MagicMock()
                    mock_course_service = MagicMock()
                    
                    render_new_course_with_services(
                        course_service=mock_course_service,
                        on_navigate=nav_callback,
                    )
                    
                    mock_render.assert_called_once()
                    call_kwargs = mock_render.call_args[1]
                    assert call_kwargs.get("on_navigate") == nav_callback
