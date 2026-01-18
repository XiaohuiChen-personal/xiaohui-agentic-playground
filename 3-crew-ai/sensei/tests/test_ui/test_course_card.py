"""Unit tests for course_card component."""

from unittest.mock import MagicMock, patch

import pytest

from sensei.models.schemas import Progress


class TestRenderCourseCard:
    """Tests for render_course_card function."""

    def test_render_course_card_basic(self, mock_streamlit, sample_course_outline):
        """Test rendering basic course card."""
        with patch("sensei.ui.components.course_card.st", mock_streamlit):
            from sensei.ui.components.course_card import render_course_card
            
            render_course_card(course=sample_course_outline)
            
            # Should render markdown
            mock_streamlit.markdown.assert_called()
            # Should render progress bar
            mock_streamlit.progress.assert_called()

    def test_render_course_card_with_progress_zero(
        self, mock_streamlit, sample_course_outline, sample_progress_zero
    ):
        """Test course card with zero progress."""
        with patch("sensei.ui.components.course_card.st", mock_streamlit):
            from sensei.ui.components.course_card import render_course_card
            
            render_course_card(
                course=sample_course_outline,
                progress=sample_progress_zero,
            )
            
            # Should show Start button (not Continue)
            mock_streamlit.button.assert_called()
            mock_streamlit.progress.assert_called()

    def test_render_course_card_with_progress_partial(
        self, mock_streamlit, sample_course_outline, sample_progress_partial
    ):
        """Test course card with partial progress."""
        with patch("sensei.ui.components.course_card.st", mock_streamlit):
            from sensei.ui.components.course_card import render_course_card
            
            render_course_card(
                course=sample_course_outline,
                progress=sample_progress_partial,
            )
            
            # Should show Continue button
            mock_streamlit.button.assert_called()
            # Should show current position caption
            mock_streamlit.caption.assert_called()

    def test_render_course_card_with_progress_complete(
        self, mock_streamlit, sample_course_outline, sample_progress_complete
    ):
        """Test course card with complete progress."""
        with patch("sensei.ui.components.course_card.st", mock_streamlit):
            from sensei.ui.components.course_card import render_course_card
            
            render_course_card(
                course=sample_course_outline,
                progress=sample_progress_complete,
            )
            
            # Should show completion badge
            mock_streamlit.markdown.assert_called()
            # Should show Review button
            mock_streamlit.button.assert_called()

    def test_render_course_card_continue_callback(
        self, mock_streamlit, sample_course_outline, sample_progress_partial
    ):
        """Test course card continue button callback."""
        # Make the Continue button (first action button for partial progress) return True
        mock_streamlit.button.side_effect = [True, False]
        
        with patch("sensei.ui.components.course_card.st", mock_streamlit):
            from sensei.ui.components.course_card import render_course_card
            
            callback = MagicMock()
            render_course_card(
                course=sample_course_outline,
                progress=sample_progress_partial,
                on_continue=callback,
            )
            
            callback.assert_called_with("test-course-123")

    def test_render_course_card_review_callback(
        self, mock_streamlit, sample_course_outline, sample_progress_complete
    ):
        """Test course card review button callback."""
        mock_streamlit.button.side_effect = [True, False]
        
        with patch("sensei.ui.components.course_card.st", mock_streamlit):
            from sensei.ui.components.course_card import render_course_card
            
            callback = MagicMock()
            render_course_card(
                course=sample_course_outline,
                progress=sample_progress_complete,
                on_review=callback,
            )
            
            callback.assert_called_with("test-course-123")

    def test_render_course_card_review_callback_fallback_to_continue(
        self, mock_streamlit, sample_course_outline, sample_progress_complete
    ):
        """Test that review button falls back to on_continue if on_review not provided."""
        mock_streamlit.button.side_effect = [True, False]
        
        with patch("sensei.ui.components.course_card.st", mock_streamlit):
            from sensei.ui.components.course_card import render_course_card
            
            continue_callback = MagicMock()
            render_course_card(
                course=sample_course_outline,
                progress=sample_progress_complete,
                on_continue=continue_callback,
                on_review=None,
            )
            
            continue_callback.assert_called_with("test-course-123")

    def test_render_course_card_start_callback(
        self, mock_streamlit, sample_course_outline, sample_progress_zero
    ):
        """Test course card start button callback."""
        mock_streamlit.button.side_effect = [True, False]
        
        with patch("sensei.ui.components.course_card.st", mock_streamlit):
            from sensei.ui.components.course_card import render_course_card
            
            callback = MagicMock()
            render_course_card(
                course=sample_course_outline,
                progress=sample_progress_zero,
                on_continue=callback,
            )
            
            callback.assert_called_with("test-course-123")

    def test_render_course_card_delete_button(
        self, mock_streamlit, sample_course_outline
    ):
        """Test course card with delete button shown."""
        # Make delete button the one clicked
        mock_streamlit.button.side_effect = [False, False, True]
        mock_streamlit.columns.return_value = [MagicMock(), MagicMock(), MagicMock()]
        
        with patch("sensei.ui.components.course_card.st", mock_streamlit):
            from sensei.ui.components.course_card import render_course_card
            
            delete_callback = MagicMock()
            render_course_card(
                course=sample_course_outline,
                show_delete=True,
                on_delete=delete_callback,
            )
            
            # Delete callback should be called
            delete_callback.assert_called_with("test-course-123")

    def test_render_course_card_no_description(self, mock_streamlit):
        """Test course card without description."""
        course = {"id": "test-123", "title": "No Description Course"}
        
        with patch("sensei.ui.components.course_card.st", mock_streamlit):
            from sensei.ui.components.course_card import render_course_card
            
            render_course_card(course=course)
            
            # Should render without error
            mock_streamlit.markdown.assert_called()

    def test_render_course_card_long_description_truncated(self, mock_streamlit):
        """Test course card truncates long description."""
        course = {
            "id": "test-123",
            "title": "Long Description",
            "description": "x" * 200,  # Very long description
        }
        
        with patch("sensei.ui.components.course_card.st", mock_streamlit):
            from sensei.ui.components.course_card import render_course_card
            
            render_course_card(course=course)
            
            # Should still render
            mock_streamlit.markdown.assert_called()

    def test_render_course_card_with_time_spent(
        self, mock_streamlit, sample_course_outline, sample_progress_partial
    ):
        """Test course card displays time spent."""
        with patch("sensei.ui.components.course_card.st", mock_streamlit):
            from sensei.ui.components.course_card import render_course_card
            
            render_course_card(
                course=sample_course_outline,
                progress=sample_progress_partial,
            )
            
            # Should show metrics including time
            mock_streamlit.metric.assert_called()

    def test_render_course_card_no_time_spent(
        self, mock_streamlit, sample_course_outline, sample_progress_zero
    ):
        """Test course card with zero time spent shows dash."""
        with patch("sensei.ui.components.course_card.st", mock_streamlit):
            from sensei.ui.components.course_card import render_course_card
            
            render_course_card(
                course=sample_course_outline,
                progress=sample_progress_zero,
            )
            
            mock_streamlit.metric.assert_called()

    def test_render_course_card_details_button(
        self, mock_streamlit, sample_course_outline, sample_progress_partial
    ):
        """Test course card details button."""
        # Make details button (second button) return True
        mock_streamlit.button.side_effect = [False, True]
        
        with patch("sensei.ui.components.course_card.st", mock_streamlit):
            from sensei.ui.components.course_card import render_course_card
            
            render_course_card(
                course=sample_course_outline,
                progress=sample_progress_partial,
            )
            
            # Should show expander for details
            mock_streamlit.expander.assert_called()


class TestRenderCourseCardCompact:
    """Tests for render_course_card_compact function."""

    def test_render_compact_basic(self, mock_streamlit, sample_course_outline):
        """Test compact course card rendering."""
        with patch("sensei.ui.components.course_card.st", mock_streamlit):
            from sensei.ui.components.course_card import render_course_card_compact
            
            render_course_card_compact(course=sample_course_outline)
            
            mock_streamlit.button.assert_called()
            mock_streamlit.progress.assert_called()

    def test_render_compact_with_progress(
        self, mock_streamlit, sample_course_outline, sample_progress_partial
    ):
        """Test compact card with progress."""
        with patch("sensei.ui.components.course_card.st", mock_streamlit):
            from sensei.ui.components.course_card import render_course_card_compact
            
            render_course_card_compact(
                course=sample_course_outline,
                progress=sample_progress_partial,
            )
            
            mock_streamlit.progress.assert_called()

    def test_render_compact_complete(
        self, mock_streamlit, sample_course_outline, sample_progress_complete
    ):
        """Test compact card with completed progress."""
        with patch("sensei.ui.components.course_card.st", mock_streamlit):
            from sensei.ui.components.course_card import render_course_card_compact
            
            render_course_card_compact(
                course=sample_course_outline,
                progress=sample_progress_complete,
            )
            
            # Button should include checkmark
            mock_streamlit.button.assert_called()

    def test_render_compact_click_callback(
        self, mock_streamlit, sample_course_outline
    ):
        """Test compact card click callback."""
        mock_streamlit.button.return_value = True
        
        with patch("sensei.ui.components.course_card.st", mock_streamlit):
            from sensei.ui.components.course_card import render_course_card_compact
            
            callback = MagicMock()
            render_course_card_compact(
                course=sample_course_outline,
                on_click=callback,
            )
            
            callback.assert_called_with("test-course-123")

    def test_render_compact_no_callback(self, mock_streamlit, sample_course_outline):
        """Test compact card without callback."""
        mock_streamlit.button.return_value = True
        
        with patch("sensei.ui.components.course_card.st", mock_streamlit):
            from sensei.ui.components.course_card import render_course_card_compact
            
            # Should not raise error
            render_course_card_compact(
                course=sample_course_outline,
                on_click=None,
            )


class TestRenderEmptyCourseState:
    """Tests for render_empty_course_state function."""

    def test_render_empty_state_basic(self, mock_streamlit):
        """Test empty course state rendering."""
        with patch("sensei.ui.components.course_card.st", mock_streamlit):
            from sensei.ui.components.course_card import render_empty_course_state
            
            render_empty_course_state()
            
            mock_streamlit.markdown.assert_called()
            mock_streamlit.button.assert_called()

    def test_render_empty_state_create_callback(self, mock_streamlit):
        """Test empty state create button callback."""
        mock_streamlit.button.return_value = True
        
        with patch("sensei.ui.components.course_card.st", mock_streamlit):
            from sensei.ui.components.course_card import render_empty_course_state
            
            callback = MagicMock()
            render_empty_course_state(on_create=callback)
            
            callback.assert_called_once()

    def test_render_empty_state_no_callback(self, mock_streamlit):
        """Test empty state without callback."""
        mock_streamlit.button.return_value = True
        
        with patch("sensei.ui.components.course_card.st", mock_streamlit):
            from sensei.ui.components.course_card import render_empty_course_state
            
            # Should not raise error
            render_empty_course_state(on_create=None)


class TestGetCourseIcon:
    """Tests for _get_course_icon helper function."""

    def test_get_icon_python(self):
        """Test Python course icon."""
        from sensei.ui.components.course_card import _get_course_icon
        
        assert _get_course_icon("Python Basics") == "🐍"
        assert _get_course_icon("Learn PYTHON") == "🐍"

    def test_get_icon_javascript(self):
        """Test JavaScript course icon."""
        from sensei.ui.components.course_card import _get_course_icon
        
        assert _get_course_icon("JavaScript Fundamentals") == "🟨"
        assert _get_course_icon("Learn JS ") == "🟨"
        assert _get_course_icon("Modern JS") == "🟨"

    def test_get_icon_typescript(self):
        """Test TypeScript course icon."""
        from sensei.ui.components.course_card import _get_course_icon
        
        assert _get_course_icon("TypeScript Advanced") == "🔷"
        assert _get_course_icon("Learn TS ") == "🔷"
        assert _get_course_icon("Modern TS") == "🔷"

    def test_get_icon_java(self):
        """Test Java course icon (not JavaScript)."""
        from sensei.ui.components.course_card import _get_course_icon
        
        assert _get_course_icon("Java Programming") == "☕"

    def test_get_icon_rust(self):
        """Test Rust course icon."""
        from sensei.ui.components.course_card import _get_course_icon
        
        assert _get_course_icon("Rust Programming") == "🦀"

    def test_get_icon_go(self):
        """Test Go course icon."""
        from sensei.ui.components.course_card import _get_course_icon
        
        assert _get_course_icon("Go Language") == "🐹"
        assert _get_course_icon("Golang Basics") == "🐹"

    def test_get_icon_cpp(self):
        """Test C++ course icon."""
        from sensei.ui.components.course_card import _get_course_icon
        
        assert _get_course_icon("C++ Programming") == "⚡"
        assert _get_course_icon("CPP Advanced") == "⚡"

    def test_get_icon_csharp(self):
        """Test C# course icon."""
        from sensei.ui.components.course_card import _get_course_icon
        
        assert _get_course_icon("C# Development") == "🎯"
        assert _get_course_icon("CSharp Basics") == "🎯"

    def test_get_icon_cuda(self):
        """Test CUDA course icon."""
        from sensei.ui.components.course_card import _get_course_icon
        
        assert _get_course_icon("CUDA C Programming") == "🖥️"
        assert _get_course_icon("GPU Computing") == "🖥️"

    def test_get_icon_react(self):
        """Test React course icon."""
        from sensei.ui.components.course_card import _get_course_icon
        
        assert _get_course_icon("React Fundamentals") == "⚛️"

    def test_get_icon_vue(self):
        """Test Vue course icon."""
        from sensei.ui.components.course_card import _get_course_icon
        
        assert _get_course_icon("Vue.js Basics") == "💚"

    def test_get_icon_angular(self):
        """Test Angular course icon."""
        from sensei.ui.components.course_card import _get_course_icon
        
        assert _get_course_icon("Angular Development") == "🅰️"

    def test_get_icon_web(self):
        """Test web course icon."""
        from sensei.ui.components.course_card import _get_course_icon
        
        assert _get_course_icon("Web Development") == "🌐"
        assert _get_course_icon("HTML CSS Basics") == "🌐"

    def test_get_icon_ml(self):
        """Test machine learning course icon."""
        from sensei.ui.components.course_card import _get_course_icon
        
        assert _get_course_icon("Machine Learning") == "🤖"
        assert _get_course_icon("ML Fundamentals") == "🤖"
        assert _get_course_icon("Deep ML ") == "🤖"

    def test_get_icon_data(self):
        """Test data course icon."""
        from sensei.ui.components.course_card import _get_course_icon
        
        assert _get_course_icon("Data Science") == "📊"

    def test_get_icon_ai(self):
        """Test AI course icon."""
        from sensei.ui.components.course_card import _get_course_icon
        
        assert _get_course_icon("AI Fundamentals") == "🧠"
        assert _get_course_icon("Artificial Intelligence") == "🧠"

    def test_get_icon_docker(self):
        """Test Docker/Kubernetes course icon."""
        from sensei.ui.components.course_card import _get_course_icon
        
        assert _get_course_icon("Docker Basics") == "🐳"
        assert _get_course_icon("Kubernetes") == "🐳"

    def test_get_icon_cloud(self):
        """Test cloud course icon."""
        from sensei.ui.components.course_card import _get_course_icon
        
        assert _get_course_icon("Cloud Computing") == "☁️"
        assert _get_course_icon("AWS Basics") == "☁️"
        assert _get_course_icon("Azure Fundamentals") == "☁️"

    def test_get_icon_devops(self):
        """Test DevOps course icon."""
        from sensei.ui.components.course_card import _get_course_icon
        
        assert _get_course_icon("DevOps Practices") == "🔧"

    def test_get_icon_database(self):
        """Test database course icon."""
        from sensei.ui.components.course_card import _get_course_icon
        
        assert _get_course_icon("SQL Fundamentals") == "🗄️"
        assert _get_course_icon("Database Design") == "🗄️"

    def test_get_icon_security(self):
        """Test security course icon."""
        from sensei.ui.components.course_card import _get_course_icon
        
        assert _get_course_icon("Security Basics") == "🔒"
        assert _get_course_icon("Cyber Security") == "🔒"

    def test_get_icon_default(self):
        """Test default course icon for unknown topics."""
        from sensei.ui.components.course_card import _get_course_icon
        
        assert _get_course_icon("Unknown Topic") == "📖"
        assert _get_course_icon("Random Course") == "📖"


class TestShowCourseDetails:
    """Tests for _show_course_details private function."""

    def test_show_details_basic(
        self, mock_streamlit, sample_course_outline, sample_progress_partial
    ):
        """Test showing course details."""
        with patch("sensei.ui.components.course_card.st", mock_streamlit):
            from sensei.ui.components.course_card import _show_course_details
            
            _show_course_details(sample_course_outline, sample_progress_partial)
            
            mock_streamlit.expander.assert_called()
            mock_streamlit.markdown.assert_called()

    def test_show_details_no_progress(self, mock_streamlit, sample_course_outline):
        """Test showing details without progress."""
        with patch("sensei.ui.components.course_card.st", mock_streamlit):
            from sensei.ui.components.course_card import _show_course_details
            
            _show_course_details(sample_course_outline, None)
            
            mock_streamlit.expander.assert_called()

    def test_show_details_no_modules(self, mock_streamlit):
        """Test showing details for course without modules."""
        course = {"description": "Test course"}
        
        with patch("sensei.ui.components.course_card.st", mock_streamlit):
            from sensei.ui.components.course_card import _show_course_details
            
            _show_course_details(course, None)
            
            mock_streamlit.expander.assert_called()

    def test_show_details_no_description(self, mock_streamlit):
        """Test showing details for course without description."""
        course = {"modules": []}
        
        with patch("sensei.ui.components.course_card.st", mock_streamlit):
            from sensei.ui.components.course_card import _show_course_details
            
            _show_course_details(course, None)
            
            mock_streamlit.expander.assert_called()

    def test_show_details_with_module_statuses(
        self, mock_streamlit, sample_course_outline
    ):
        """Test showing details with various module statuses."""
        # Progress with some modules completed
        progress = Progress(
            course_id="test",
            completion_percentage=0.5,
            modules_completed=1,
            total_modules=3,
            concepts_completed=3,
            total_concepts=9,
            time_spent_minutes=30,
            current_module_idx=1,
            current_concept_idx=0,
        )
        
        with patch("sensei.ui.components.course_card.st", mock_streamlit):
            from sensei.ui.components.course_card import _show_course_details
            
            _show_course_details(sample_course_outline, progress)
            
            mock_streamlit.markdown.assert_called()
            mock_streamlit.metric.assert_called()
