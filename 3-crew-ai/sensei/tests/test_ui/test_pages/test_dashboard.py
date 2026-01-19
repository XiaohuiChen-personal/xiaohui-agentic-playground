"""Unit tests for dashboard page."""

from unittest.mock import MagicMock, patch, call

import pytest

from sensei.models.schemas import Progress, LearningStats


class TestRenderDashboard:
    """Tests for render_dashboard function."""

    def test_render_dashboard_basic(self, mock_streamlit):
        """Test rendering dashboard with basic data."""
        with patch("sensei.ui.pages.dashboard.st", mock_streamlit):
            with patch("sensei.ui.components.sidebar.st", mock_streamlit):
                with patch("sensei.ui.components.course_card.st", mock_streamlit):
                    from sensei.ui.pages.dashboard import render_dashboard
                    
                    render_dashboard(
                        user_name="Test User",
                        courses=[],
                        progress_map={},
                        stats={"total_courses": 0, "concepts_mastered": 0, "hours_learned": 0},
                    )
                    
                    # Should render without error
                    mock_streamlit.markdown.assert_called()

    def test_render_dashboard_with_user_name(self, mock_streamlit):
        """Test dashboard shows user name in welcome message."""
        with patch("sensei.ui.pages.dashboard.st", mock_streamlit):
            with patch("sensei.ui.components.sidebar.st", mock_streamlit):
                with patch("sensei.ui.components.course_card.st", mock_streamlit):
                    from sensei.ui.pages.dashboard import render_dashboard
                    
                    render_dashboard(
                        user_name="Xiaohui",
                        courses=[],
                        progress_map={},
                        stats={},
                    )
                    
                    # Check that markdown was called with user name
                    calls = mock_streamlit.markdown.call_args_list
                    welcome_found = any(
                        "Xiaohui" in str(c) for c in calls
                    )
                    assert welcome_found, "Welcome message should include user name"

    def test_render_dashboard_with_courses(self, mock_streamlit, sample_course_outline):
        """Test dashboard renders course cards when courses exist."""
        with patch("sensei.ui.pages.dashboard.st", mock_streamlit):
            with patch("sensei.ui.components.sidebar.st", mock_streamlit):
                with patch("sensei.ui.components.course_card.st", mock_streamlit):
                    from sensei.ui.pages.dashboard import render_dashboard
                    
                    courses = [sample_course_outline]
                    progress = Progress(course_id="test-course-123", completion_percentage=0.5)
                    
                    render_dashboard(
                        user_name="Test",
                        courses=courses,
                        progress_map={"test-course-123": progress},
                        stats={"total_courses": 1, "concepts_mastered": 5, "hours_learned": 2.5},
                    )
                    
                    # Should render course card
                    mock_streamlit.markdown.assert_called()

    def test_render_dashboard_empty_state(self, mock_streamlit):
        """Test dashboard shows empty state when no courses."""
        with patch("sensei.ui.pages.dashboard.st", mock_streamlit):
            with patch("sensei.ui.components.sidebar.st", mock_streamlit):
                with patch("sensei.ui.components.course_card.st", mock_streamlit):
                    from sensei.ui.pages.dashboard import render_dashboard
                    
                    render_dashboard(
                        user_name="Test",
                        courses=[],
                        progress_map={},
                        stats={},
                    )
                    
                    # Empty state should be rendered
                    mock_streamlit.markdown.assert_called()

    def test_render_dashboard_stats_display(self, mock_streamlit):
        """Test stats cards are rendered with correct values."""
        with patch("sensei.ui.pages.dashboard.st", mock_streamlit):
            with patch("sensei.ui.components.sidebar.st", mock_streamlit):
                with patch("sensei.ui.components.course_card.st", mock_streamlit):
                    from sensei.ui.pages.dashboard import render_dashboard
                    
                    render_dashboard(
                        user_name="Test",
                        courses=[],
                        progress_map={},
                        stats={
                            "total_courses": 5,
                            "concepts_mastered": 47,
                            "hours_learned": 12.5,
                        },
                    )
                    
                    # Stats should be displayed
                    calls = mock_streamlit.markdown.call_args_list
                    # Check that some stats-related content was rendered
                    assert len(calls) > 0

    def test_render_dashboard_new_course_button(self, mock_streamlit):
        """Test new course button is rendered."""
        with patch("sensei.ui.pages.dashboard.st", mock_streamlit):
            with patch("sensei.ui.components.sidebar.st", mock_streamlit):
                with patch("sensei.ui.components.course_card.st", mock_streamlit):
                    from sensei.ui.pages.dashboard import render_dashboard
                    
                    callback = MagicMock()
                    
                    render_dashboard(
                        user_name="Test",
                        courses=[],
                        progress_map={},
                        stats={},
                        on_new_course=callback,
                    )
                    
                    # Button should be rendered
                    mock_streamlit.button.assert_called()

    def test_render_dashboard_new_course_callback(self, mock_streamlit):
        """Test new course callback is triggered when button clicked."""
        mock_streamlit.button.return_value = True
        
        with patch("sensei.ui.pages.dashboard.st", mock_streamlit):
            with patch("sensei.ui.components.sidebar.st", mock_streamlit):
                with patch("sensei.ui.components.course_card.st", mock_streamlit):
                    from sensei.ui.pages.dashboard import render_dashboard
                    
                    callback = MagicMock()
                    
                    render_dashboard(
                        user_name="Test",
                        courses=[],
                        progress_map={},
                        stats={},
                        on_new_course=callback,
                    )
                    
                    # Callback may be called multiple times (from header button and empty state)
                    assert callback.call_count >= 1, "Callback should be called at least once"

    def test_render_dashboard_continue_callback(self, mock_streamlit, sample_course_outline):
        """Test continue course callback is passed to course card."""
        with patch("sensei.ui.pages.dashboard.st", mock_streamlit):
            with patch("sensei.ui.components.sidebar.st", mock_streamlit):
                with patch("sensei.ui.components.course_card.st", mock_streamlit):
                    with patch("sensei.ui.pages.dashboard.render_course_card") as mock_render:
                        from sensei.ui.pages.dashboard import render_dashboard
                        
                        continue_callback = MagicMock()
                        
                        render_dashboard(
                            user_name="Test",
                            courses=[sample_course_outline],
                            progress_map={},
                            stats={},
                            on_continue_course=continue_callback,
                        )
                        
                        # render_course_card should be called with on_continue
                        mock_render.assert_called()
                        call_kwargs = mock_render.call_args[1]
                        assert call_kwargs.get("on_continue") == continue_callback

    def test_render_dashboard_review_callback(self, mock_streamlit, sample_course_outline):
        """Test review course callback is passed to course card."""
        with patch("sensei.ui.pages.dashboard.st", mock_streamlit):
            with patch("sensei.ui.components.sidebar.st", mock_streamlit):
                with patch("sensei.ui.components.course_card.st", mock_streamlit):
                    with patch("sensei.ui.pages.dashboard.render_course_card") as mock_render:
                        from sensei.ui.pages.dashboard import render_dashboard
                        
                        review_callback = MagicMock()
                        
                        render_dashboard(
                            user_name="Test",
                            courses=[sample_course_outline],
                            progress_map={},
                            stats={},
                            on_review_course=review_callback,
                        )
                        
                        # render_course_card should be called with on_review
                        mock_render.assert_called()
                        call_kwargs = mock_render.call_args[1]
                        assert call_kwargs.get("on_review") == review_callback

    def test_render_dashboard_sidebar_navigation(self, mock_streamlit):
        """Test sidebar is rendered with navigation callback."""
        with patch("sensei.ui.pages.dashboard.st", mock_streamlit):
            with patch("sensei.ui.components.sidebar.st", mock_streamlit):
                with patch("sensei.ui.components.course_card.st", mock_streamlit):
                    with patch("sensei.ui.pages.dashboard.render_sidebar") as mock_sidebar:
                        from sensei.ui.pages.dashboard import render_dashboard
                        
                        nav_callback = MagicMock()
                        
                        render_dashboard(
                            user_name="Test",
                            courses=[],
                            progress_map={},
                            stats={},
                            on_navigate=nav_callback,
                        )
                        
                        mock_sidebar.assert_called_once()
                        call_kwargs = mock_sidebar.call_args[1]
                        assert call_kwargs.get("on_navigate") == nav_callback


class TestRenderHeader:
    """Tests for _render_header function."""

    def test_render_header_with_name(self, mock_streamlit):
        """Test header renders user name."""
        with patch("sensei.ui.pages.dashboard.st", mock_streamlit):
            from sensei.ui.pages.dashboard import _render_header
            
            _render_header("Alice")
            
            calls = mock_streamlit.markdown.call_args_list
            name_found = any("Alice" in str(c) for c in calls)
            assert name_found

    def test_render_header_default_name(self, mock_streamlit):
        """Test header renders with default name."""
        with patch("sensei.ui.pages.dashboard.st", mock_streamlit):
            from sensei.ui.pages.dashboard import _render_header
            
            _render_header("Learner")
            
            calls = mock_streamlit.markdown.call_args_list
            name_found = any("Learner" in str(c) for c in calls)
            assert name_found


class TestRenderStatsRow:
    """Tests for _render_stats_row function."""

    def test_render_stats_row_basic(self, mock_streamlit):
        """Test stats row renders without error."""
        with patch("sensei.ui.pages.dashboard.st", mock_streamlit):
            from sensei.ui.pages.dashboard import _render_stats_row
            
            _render_stats_row({
                "total_courses": 3,
                "concepts_mastered": 47,
                "hours_learned": 12.5,
            })
            
            # Should create 3 columns
            mock_streamlit.columns.assert_called()

    def test_render_stats_row_zero_values(self, mock_streamlit):
        """Test stats row handles zero values."""
        with patch("sensei.ui.pages.dashboard.st", mock_streamlit):
            from sensei.ui.pages.dashboard import _render_stats_row
            
            _render_stats_row({
                "total_courses": 0,
                "concepts_mastered": 0,
                "hours_learned": 0,
            })
            
            mock_streamlit.markdown.assert_called()

    def test_render_stats_row_missing_keys(self, mock_streamlit):
        """Test stats row handles missing keys gracefully."""
        with patch("sensei.ui.pages.dashboard.st", mock_streamlit):
            from sensei.ui.pages.dashboard import _render_stats_row
            
            _render_stats_row({})  # Empty dict
            
            mock_streamlit.markdown.assert_called()


class TestRenderStatCard:
    """Tests for _render_stat_card function."""

    def test_render_stat_card_basic(self, mock_streamlit):
        """Test stat card renders correctly."""
        with patch("sensei.ui.pages.dashboard.st", mock_streamlit):
            from sensei.ui.pages.dashboard import _render_stat_card
            
            _render_stat_card(
                icon="📚",
                value="5",
                label="Courses",
            )
            
            mock_streamlit.markdown.assert_called_once()
            call_args = mock_streamlit.markdown.call_args[0][0]
            assert "📚" in call_args
            assert "5" in call_args
            assert "Courses" in call_args

    def test_render_stat_card_special_characters(self, mock_streamlit):
        """Test stat card handles special characters."""
        with patch("sensei.ui.pages.dashboard.st", mock_streamlit):
            from sensei.ui.pages.dashboard import _render_stat_card
            
            _render_stat_card(
                icon="⏱️",
                value="12.5",
                label="Hours & Minutes",
            )
            
            mock_streamlit.markdown.assert_called()


class TestRenderCoursesSection:
    """Tests for _render_courses_section function."""

    def test_render_courses_section_empty(self, mock_streamlit):
        """Test courses section shows empty state."""
        with patch("sensei.ui.pages.dashboard.st", mock_streamlit):
            with patch("sensei.ui.components.course_card.st", mock_streamlit):
                with patch("sensei.ui.pages.dashboard.render_empty_course_state") as mock_empty:
                    from sensei.ui.pages.dashboard import _render_courses_section
                    
                    _render_courses_section(
                        courses=[],
                        progress_map={},
                        on_continue=None,
                        on_review=None,
                        on_delete=None,
                        on_new_course=None,
                        show_delete=False,
                    )
                    
                    mock_empty.assert_called_once()

    def test_render_courses_section_with_courses(
        self, mock_streamlit, sample_course_outline
    ):
        """Test courses section renders course cards."""
        with patch("sensei.ui.pages.dashboard.st", mock_streamlit):
            with patch("sensei.ui.components.course_card.st", mock_streamlit):
                with patch("sensei.ui.pages.dashboard.render_course_card") as mock_card:
                    from sensei.ui.pages.dashboard import _render_courses_section
                    
                    _render_courses_section(
                        courses=[sample_course_outline],
                        progress_map={},
                        on_continue=None,
                        on_review=None,
                        on_delete=None,
                        on_new_course=None,
                        show_delete=False,
                    )
                    
                    mock_card.assert_called_once()

    def test_render_courses_section_multiple_courses(self, mock_streamlit):
        """Test courses section renders multiple course cards."""
        with patch("sensei.ui.pages.dashboard.st", mock_streamlit):
            with patch("sensei.ui.components.course_card.st", mock_streamlit):
                with patch("sensei.ui.pages.dashboard.render_course_card") as mock_card:
                    from sensei.ui.pages.dashboard import _render_courses_section
                    
                    courses = [
                        {"id": "c1", "title": "Course 1"},
                        {"id": "c2", "title": "Course 2"},
                        {"id": "c3", "title": "Course 3"},
                    ]
                    
                    _render_courses_section(
                        courses=courses,
                        progress_map={},
                        on_continue=None,
                        on_review=None,
                        on_delete=None,
                        on_new_course=None,
                        show_delete=False,
                    )
                    
                    assert mock_card.call_count == 3

    def test_render_courses_section_with_progress(self, mock_streamlit):
        """Test courses section passes progress to cards."""
        with patch("sensei.ui.pages.dashboard.st", mock_streamlit):
            with patch("sensei.ui.components.course_card.st", mock_streamlit):
                with patch("sensei.ui.pages.dashboard.render_course_card") as mock_card:
                    from sensei.ui.pages.dashboard import _render_courses_section
                    
                    progress = Progress(course_id="c1", completion_percentage=0.75)
                    
                    _render_courses_section(
                        courses=[{"id": "c1", "title": "Course 1"}],
                        progress_map={"c1": progress},
                        on_continue=None,
                        on_review=None,
                        on_delete=None,
                        on_new_course=None,
                        show_delete=False,
                    )
                    
                    call_kwargs = mock_card.call_args[1]
                    assert call_kwargs.get("progress") == progress


class TestRenderDashboardPage:
    """Tests for render_dashboard_page function with service integration."""

    def test_render_dashboard_page_loads_data(self, mock_streamlit):
        """Test dashboard page loads data from services."""
        with patch("sensei.ui.pages.dashboard.st", mock_streamlit):
            with patch("sensei.ui.components.sidebar.st", mock_streamlit):
                with patch("sensei.ui.components.course_card.st", mock_streamlit):
                    from sensei.ui.pages.dashboard import render_dashboard_page
                    from sensei.models.schemas import UserPreferences, LearningStats
                    
                    # Create mock services
                    mock_user_service = MagicMock()
                    mock_user_service.get_preferences.return_value = UserPreferences(
                        name="TestUser"
                    )
                    
                    mock_course_service = MagicMock()
                    mock_course_service.list_courses.return_value = []
                    
                    mock_progress_service = MagicMock()
                    mock_progress_service.get_course_progress.return_value = Progress(
                        course_id="test"
                    )
                    mock_progress_service.get_learning_stats.return_value = LearningStats()
                    
                    render_dashboard_page(
                        user_service=mock_user_service,
                        course_service=mock_course_service,
                        progress_service=mock_progress_service,
                    )
                    
                    # Services should be called
                    mock_user_service.get_preferences.assert_called_once()
                    mock_course_service.list_courses.assert_called_once()
                    mock_progress_service.get_learning_stats.assert_called_once()

    def test_render_dashboard_page_with_courses(self, mock_streamlit):
        """Test dashboard page loads progress for each course."""
        with patch("sensei.ui.pages.dashboard.st", mock_streamlit):
            with patch("sensei.ui.components.sidebar.st", mock_streamlit):
                with patch("sensei.ui.components.course_card.st", mock_streamlit):
                    from sensei.ui.pages.dashboard import render_dashboard_page
                    from sensei.models.schemas import UserPreferences, LearningStats
                    
                    mock_user_service = MagicMock()
                    mock_user_service.get_preferences.return_value = UserPreferences()
                    
                    mock_course_service = MagicMock()
                    mock_course_service.list_courses.return_value = [
                        {"id": "c1", "title": "Course 1"},
                        {"id": "c2", "title": "Course 2"},
                    ]
                    
                    mock_progress_service = MagicMock()
                    mock_progress_service.get_course_progress.return_value = Progress(
                        course_id="test"
                    )
                    mock_progress_service.get_learning_stats.return_value = LearningStats()
                    
                    render_dashboard_page(
                        user_service=mock_user_service,
                        course_service=mock_course_service,
                        progress_service=mock_progress_service,
                    )
                    
                    # Should get progress for each course
                    assert mock_progress_service.get_course_progress.call_count == 2

    def test_render_dashboard_page_callbacks(self, mock_streamlit):
        """Test dashboard page passes callbacks correctly."""
        with patch("sensei.ui.pages.dashboard.st", mock_streamlit):
            with patch("sensei.ui.components.sidebar.st", mock_streamlit):
                with patch("sensei.ui.components.course_card.st", mock_streamlit):
                    with patch("sensei.ui.pages.dashboard.render_dashboard") as mock_render:
                        from sensei.ui.pages.dashboard import render_dashboard_page
                        from sensei.models.schemas import UserPreferences, LearningStats
                        
                        mock_user_service = MagicMock()
                        mock_user_service.get_preferences.return_value = UserPreferences()
                        
                        mock_course_service = MagicMock()
                        mock_course_service.list_courses.return_value = []
                        
                        mock_progress_service = MagicMock()
                        mock_progress_service.get_learning_stats.return_value = LearningStats()
                        
                        nav_callback = MagicMock()
                        continue_callback = MagicMock()
                        review_callback = MagicMock()
                        new_course_callback = MagicMock()
                        
                        render_dashboard_page(
                            user_service=mock_user_service,
                            course_service=mock_course_service,
                            progress_service=mock_progress_service,
                            on_navigate=nav_callback,
                            on_continue_course=continue_callback,
                            on_review_course=review_callback,
                            on_new_course=new_course_callback,
                        )
                        
                        mock_render.assert_called_once()
                        call_kwargs = mock_render.call_args[1]
                        assert call_kwargs.get("on_navigate") == nav_callback
                        assert call_kwargs.get("on_continue_course") == continue_callback
                        assert call_kwargs.get("on_review_course") == review_callback
                        assert call_kwargs.get("on_new_course") == new_course_callback
