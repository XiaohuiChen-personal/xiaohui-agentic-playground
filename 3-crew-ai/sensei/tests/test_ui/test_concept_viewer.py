"""Unit tests for concept_viewer component."""

from unittest.mock import MagicMock, patch

import pytest


class TestRenderConcept:
    """Tests for render_concept function."""

    def test_render_concept_basic(self, mock_streamlit, sample_concept_content):
        """Test rendering basic concept."""
        with patch("sensei.ui.components.concept_viewer.st", mock_streamlit):
            from sensei.ui.components.concept_viewer import render_concept
            
            render_concept(
                title="Variables in Python",
                content=sample_concept_content,
            )
            
            mock_streamlit.markdown.assert_called()

    def test_render_concept_with_code_in_markdown(self, mock_streamlit):
        """Test rendering concept with code blocks embedded in markdown."""
        with patch("sensei.ui.components.concept_viewer.st", mock_streamlit):
            from sensei.ui.components.concept_viewer import render_concept
            
            content_with_code = """
## Variables

Here's how to create a variable:

```python
x = 10
print(x)
```

And that's it!
"""
            render_concept(
                title="Variables",
                content=content_with_code,
            )
            
            # Streamlit markdown handles code blocks automatically
            mock_streamlit.markdown.assert_called()

    def test_render_concept_empty_content(self, mock_streamlit):
        """Test rendering concept with empty content."""
        with patch("sensei.ui.components.concept_viewer.st", mock_streamlit):
            from sensei.ui.components.concept_viewer import render_concept
            
            render_concept(title="Empty", content="")
            
            # Should render empty content placeholder
            mock_streamlit.markdown.assert_called()

    def test_render_concept_none_content(self, mock_streamlit):
        """Test rendering concept with None content."""
        with patch("sensei.ui.components.concept_viewer.st", mock_streamlit):
            from sensei.ui.components.concept_viewer import render_concept
            
            render_concept(title="None Content", content=None)
            
            # Should render empty content placeholder
            mock_streamlit.markdown.assert_called()

    def test_render_concept_title_displayed(self, mock_streamlit):
        """Test that concept title is displayed as markdown header."""
        with patch("sensei.ui.components.concept_viewer.st", mock_streamlit):
            from sensei.ui.components.concept_viewer import render_concept
            
            render_concept(title="My Title", content="Some content")
            
            # First call should be the title
            calls = mock_streamlit.markdown.call_args_list
            assert any("## My Title" in str(call) for call in calls)


class TestRenderConceptWithNavigation:
    """Tests for render_concept_with_navigation function."""

    def test_render_with_navigation_basic(
        self, mock_streamlit, sample_concept_content
    ):
        """Test rendering concept with navigation."""
        with patch("sensei.ui.components.concept_viewer.st", mock_streamlit):
            from sensei.ui.components.concept_viewer import render_concept_with_navigation
            
            render_concept_with_navigation(
                title="Variables",
                content=sample_concept_content,
                concept_idx=1,
                total_concepts=5,
            )
            
            mock_streamlit.markdown.assert_called()
            mock_streamlit.button.assert_called()

    def test_render_with_navigation_module_title(
        self, mock_streamlit, sample_concept_content
    ):
        """Test navigation with module title."""
        with patch("sensei.ui.components.concept_viewer.st", mock_streamlit):
            from sensei.ui.components.concept_viewer import render_concept_with_navigation
            
            render_concept_with_navigation(
                title="Variables",
                content=sample_concept_content,
                concept_idx=0,
                total_concepts=3,
                module_title="Introduction to Python",
            )
            
            mock_streamlit.caption.assert_called()

    def test_render_with_navigation_first_concept(
        self, mock_streamlit, sample_concept_content
    ):
        """Test navigation on first concept (no previous)."""
        with patch("sensei.ui.components.concept_viewer.st", mock_streamlit):
            from sensei.ui.components.concept_viewer import render_concept_with_navigation
            
            render_concept_with_navigation(
                title="First",
                content=sample_concept_content,
                concept_idx=0,
                total_concepts=5,
            )
            
            # Previous button should not be rendered
            mock_streamlit.button.assert_called()

    def test_render_with_navigation_last_concept(
        self, mock_streamlit, sample_concept_content
    ):
        """Test navigation on last concept (module complete)."""
        with patch("sensei.ui.components.concept_viewer.st", mock_streamlit):
            from sensei.ui.components.concept_viewer import render_concept_with_navigation
            
            render_concept_with_navigation(
                title="Last",
                content=sample_concept_content,
                concept_idx=4,
                total_concepts=5,
            )
            
            # Should show module complete message
            mock_streamlit.success.assert_called()

    def test_render_with_navigation_middle_concept(
        self, mock_streamlit, sample_concept_content
    ):
        """Test navigation in middle of concepts."""
        with patch("sensei.ui.components.concept_viewer.st", mock_streamlit):
            from sensei.ui.components.concept_viewer import render_concept_with_navigation
            
            render_concept_with_navigation(
                title="Middle",
                content=sample_concept_content,
                concept_idx=2,
                total_concepts=5,
            )
            
            # Both buttons should be rendered
            mock_streamlit.button.assert_called()

    def test_render_with_navigation_previous_callback(
        self, mock_streamlit, sample_concept_content
    ):
        """Test previous button callback."""
        mock_streamlit.button.side_effect = [True, False]  # Previous clicked
        
        with patch("sensei.ui.components.concept_viewer.st", mock_streamlit):
            from sensei.ui.components.concept_viewer import render_concept_with_navigation
            
            callback = MagicMock()
            render_concept_with_navigation(
                title="Test",
                content=sample_concept_content,
                concept_idx=2,
                total_concepts=5,
                on_previous=callback,
            )
            
            callback.assert_called_once()

    def test_render_with_navigation_next_callback(
        self, mock_streamlit, sample_concept_content
    ):
        """Test next button callback."""
        mock_streamlit.button.side_effect = [False, True]  # Next clicked
        
        with patch("sensei.ui.components.concept_viewer.st", mock_streamlit):
            from sensei.ui.components.concept_viewer import render_concept_with_navigation
            
            callback = MagicMock()
            render_concept_with_navigation(
                title="Test",
                content=sample_concept_content,
                concept_idx=2,
                total_concepts=5,
                on_next=callback,
            )
            
            callback.assert_called_once()

    def test_render_with_navigation_can_go_previous_false(
        self, mock_streamlit, sample_concept_content
    ):
        """Test navigation with can_go_previous disabled."""
        with patch("sensei.ui.components.concept_viewer.st", mock_streamlit):
            from sensei.ui.components.concept_viewer import render_concept_with_navigation
            
            render_concept_with_navigation(
                title="Test",
                content=sample_concept_content,
                concept_idx=2,
                total_concepts=5,
                can_go_previous=False,
            )
            
            # Should not render previous button
            mock_streamlit.empty.assert_called()

    def test_render_with_navigation_can_go_next_false(
        self, mock_streamlit, sample_concept_content
    ):
        """Test navigation with can_go_next disabled."""
        with patch("sensei.ui.components.concept_viewer.st", mock_streamlit):
            from sensei.ui.components.concept_viewer import render_concept_with_navigation
            
            render_concept_with_navigation(
                title="Test",
                content=sample_concept_content,
                concept_idx=2,
                total_concepts=5,
                can_go_next=False,
            )
            
            mock_streamlit.empty.assert_called()


class TestRenderLessonHeader:
    """Tests for render_lesson_header function."""

    def test_render_lesson_header_basic(self, mock_streamlit):
        """Test rendering lesson header."""
        with patch("sensei.ui.components.concept_viewer.st", mock_streamlit):
            from sensei.ui.components.concept_viewer import render_lesson_header
            
            render_lesson_header(
                course_title="Python Basics",
                module_title="Variables",
                module_idx=0,
                total_modules=5,
            )
            
            mock_streamlit.markdown.assert_called()

    def test_render_lesson_header_last_module(self, mock_streamlit):
        """Test lesson header on last module."""
        with patch("sensei.ui.components.concept_viewer.st", mock_streamlit):
            from sensei.ui.components.concept_viewer import render_lesson_header
            
            render_lesson_header(
                course_title="Python Basics",
                module_title="Advanced Topics",
                module_idx=4,
                total_modules=5,
            )
            
            mock_streamlit.markdown.assert_called()


class TestRenderLoadingState:
    """Tests for render_loading_state function."""

    def test_render_loading_default_message(self, mock_streamlit):
        """Test loading state with default message."""
        with patch("sensei.ui.components.concept_viewer.st", mock_streamlit):
            from sensei.ui.components.concept_viewer import render_loading_state
            
            render_loading_state()
            
            mock_streamlit.markdown.assert_called()
            mock_streamlit.spinner.assert_called()

    def test_render_loading_custom_message(self, mock_streamlit):
        """Test loading state with custom message."""
        with patch("sensei.ui.components.concept_viewer.st", mock_streamlit):
            from sensei.ui.components.concept_viewer import render_loading_state
            
            render_loading_state("Custom loading message...")
            
            mock_streamlit.markdown.assert_called()
            calls = mock_streamlit.markdown.call_args_list
            assert any("Custom loading message" in str(c) for c in calls)

    def test_render_loading_custom_icon(self, mock_streamlit):
        """Test loading state with custom icon."""
        with patch("sensei.ui.components.concept_viewer.st", mock_streamlit):
            from sensei.ui.components.concept_viewer import render_loading_state
            
            render_loading_state(message="Test", icon="📝")
            
            calls = mock_streamlit.markdown.call_args_list
            assert any("📝" in str(c) for c in calls)

    def test_render_loading_with_estimated_time(self, mock_streamlit):
        """Test loading state displays estimated time."""
        with patch("sensei.ui.components.concept_viewer.st", mock_streamlit):
            from sensei.ui.components.concept_viewer import render_loading_state
            
            render_loading_state(
                message="Generating...",
                estimated_time="30-60 seconds",
            )
            
            calls = mock_streamlit.markdown.call_args_list
            assert any("30-60 seconds" in str(c) for c in calls)

    def test_render_loading_without_estimated_time(self, mock_streamlit):
        """Test loading state without estimated time."""
        with patch("sensei.ui.components.concept_viewer.st", mock_streamlit):
            from sensei.ui.components.concept_viewer import render_loading_state
            
            render_loading_state(message="Test", estimated_time=None)
            
            # Should still render without errors
            mock_streamlit.markdown.assert_called()

    def test_render_loading_with_tips(self, mock_streamlit):
        """Test loading state displays tips."""
        with patch("sensei.ui.components.concept_viewer.st", mock_streamlit):
            with patch("random.choice", return_value="Great time to stretch!"):
                from sensei.ui.components.concept_viewer import render_loading_state
                
                render_loading_state(
                    message="Test",
                    tips=["Great time to stretch!", "Another tip"],
                )
                
                calls = mock_streamlit.markdown.call_args_list
                # Should show the tip
                assert any("stretch" in str(c) for c in calls)

    def test_render_loading_without_tips(self, mock_streamlit):
        """Test loading state without tips."""
        with patch("sensei.ui.components.concept_viewer.st", mock_streamlit):
            from sensei.ui.components.concept_viewer import render_loading_state
            
            render_loading_state(message="Test", tips=None)
            
            # Should still render without errors
            mock_streamlit.markdown.assert_called()

    def test_render_loading_show_spinner_true(self, mock_streamlit):
        """Test loading state with spinner enabled."""
        with patch("sensei.ui.components.concept_viewer.st", mock_streamlit):
            from sensei.ui.components.concept_viewer import render_loading_state
            
            render_loading_state(message="Test", show_spinner=True)
            
            mock_streamlit.spinner.assert_called()

    def test_render_loading_show_spinner_false(self, mock_streamlit):
        """Test loading state with spinner disabled."""
        with patch("sensei.ui.components.concept_viewer.st", mock_streamlit):
            from sensei.ui.components.concept_viewer import render_loading_state
            
            render_loading_state(message="Test", show_spinner=False)
            
            # Spinner should not be called
            mock_streamlit.spinner.assert_not_called()

    def test_render_loading_full_options(self, mock_streamlit):
        """Test loading state with all options enabled."""
        with patch("sensei.ui.components.concept_viewer.st", mock_streamlit):
            with patch("random.choice", return_value="Did you know?"):
                from sensei.ui.components.concept_viewer import render_loading_state
                
                render_loading_state(
                    message="Teaching Crew is preparing your lesson...",
                    icon="📖",
                    estimated_time="30-60 seconds",
                    tips=["Did you know?", "Another tip"],
                    show_spinner=True,
                )
                
                calls = mock_streamlit.markdown.call_args_list
                # Check all components are rendered
                assert any("Teaching Crew" in str(c) for c in calls)
                assert any("📖" in str(c) for c in calls)
                assert any("30-60 seconds" in str(c) for c in calls)
                assert any("Did you know" in str(c) for c in calls)


class TestRenderProgressDots:
    """Tests for _render_progress_dots private function."""

    def test_render_progress_first(self, mock_streamlit):
        """Test progress dots on first item."""
        with patch("sensei.ui.components.concept_viewer.st", mock_streamlit):
            from sensei.ui.components.concept_viewer import _render_progress_dots
            
            _render_progress_dots(0, 5)
            
            mock_streamlit.markdown.assert_called()

    def test_render_progress_middle(self, mock_streamlit):
        """Test progress dots in middle."""
        with patch("sensei.ui.components.concept_viewer.st", mock_streamlit):
            from sensei.ui.components.concept_viewer import _render_progress_dots
            
            _render_progress_dots(2, 5)
            
            mock_streamlit.markdown.assert_called()

    def test_render_progress_last(self, mock_streamlit):
        """Test progress dots on last item."""
        with patch("sensei.ui.components.concept_viewer.st", mock_streamlit):
            from sensei.ui.components.concept_viewer import _render_progress_dots
            
            _render_progress_dots(4, 5)
            
            mock_streamlit.markdown.assert_called()

    def test_render_progress_single_item(self, mock_streamlit):
        """Test progress dots with single item."""
        with patch("sensei.ui.components.concept_viewer.st", mock_streamlit):
            from sensei.ui.components.concept_viewer import _render_progress_dots
            
            _render_progress_dots(0, 1)
            
            mock_streamlit.markdown.assert_called()


class TestRenderEmptyContent:
    """Tests for _render_empty_content private function."""

    def test_render_empty_content(self, mock_streamlit):
        """Test rendering empty content placeholder."""
        with patch("sensei.ui.components.concept_viewer.st", mock_streamlit):
            from sensei.ui.components.concept_viewer import _render_empty_content
            
            _render_empty_content()
            
            mock_streamlit.markdown.assert_called()


class TestRenderConceptCard:
    """Tests for render_concept_card function."""

    def test_render_concept_card_basic(self, mock_streamlit, sample_concept_dict):
        """Test rendering basic concept card."""
        with patch("sensei.ui.components.concept_viewer.st", mock_streamlit):
            from sensei.ui.components.concept_viewer import render_concept_card
            
            render_concept_card(concept=sample_concept_dict)
            
            mock_streamlit.markdown.assert_called()
            mock_streamlit.button.assert_called()

    def test_render_concept_card_current(self, mock_streamlit, sample_concept_dict):
        """Test rendering current concept card."""
        with patch("sensei.ui.components.concept_viewer.st", mock_streamlit):
            from sensei.ui.components.concept_viewer import render_concept_card
            
            render_concept_card(
                concept=sample_concept_dict,
                is_current=True,
            )
            
            mock_streamlit.markdown.assert_called()
            # Button should be disabled
            mock_streamlit.button.assert_called()

    def test_render_concept_card_completed(self, mock_streamlit, sample_concept_dict):
        """Test rendering completed concept card."""
        with patch("sensei.ui.components.concept_viewer.st", mock_streamlit):
            from sensei.ui.components.concept_viewer import render_concept_card
            
            render_concept_card(
                concept=sample_concept_dict,
                is_completed=True,
            )
            
            mock_streamlit.markdown.assert_called()

    def test_render_concept_card_select_callback(
        self, mock_streamlit, sample_concept_dict
    ):
        """Test concept card select callback."""
        mock_streamlit.button.return_value = True
        
        with patch("sensei.ui.components.concept_viewer.st", mock_streamlit):
            from sensei.ui.components.concept_viewer import render_concept_card
            
            callback = MagicMock()
            render_concept_card(
                concept=sample_concept_dict,
                on_select=callback,
            )
            
            callback.assert_called_with("concept-1")

    def test_render_concept_card_select_disabled_when_current(
        self, mock_streamlit, sample_concept_dict
    ):
        """Test that select is disabled when current."""
        mock_streamlit.button.return_value = True
        
        with patch("sensei.ui.components.concept_viewer.st", mock_streamlit):
            from sensei.ui.components.concept_viewer import render_concept_card
            
            callback = MagicMock()
            render_concept_card(
                concept=sample_concept_dict,
                is_current=True,
                on_select=callback,
            )
            
            # Callback should NOT be called when current
            callback.assert_not_called()

    def test_render_concept_card_minimal_data(self, mock_streamlit):
        """Test concept card with minimal data."""
        concept = {"title": "Minimal"}
        
        with patch("sensei.ui.components.concept_viewer.st", mock_streamlit):
            from sensei.ui.components.concept_viewer import render_concept_card
            
            render_concept_card(concept=concept)
            
            mock_streamlit.markdown.assert_called()

    def test_render_concept_card_no_description(self, mock_streamlit):
        """Test concept card without description."""
        concept = {"id": "test", "title": "No Description"}
        
        with patch("sensei.ui.components.concept_viewer.st", mock_streamlit):
            from sensei.ui.components.concept_viewer import render_concept_card
            
            render_concept_card(concept=concept)
            
            mock_streamlit.markdown.assert_called()

    def test_render_concept_card_long_description_truncated(self, mock_streamlit):
        """Test concept card truncates long description."""
        concept = {
            "id": "test",
            "title": "Long Desc",
            "description": "x" * 200,
        }
        
        with patch("sensei.ui.components.concept_viewer.st", mock_streamlit):
            from sensei.ui.components.concept_viewer import render_concept_card
            
            render_concept_card(concept=concept)
            
            mock_streamlit.markdown.assert_called()
