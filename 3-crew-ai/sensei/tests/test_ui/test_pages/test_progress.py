"""Unit tests for progress page."""

from unittest.mock import MagicMock, patch

import pytest

from sensei.models.schemas import LearningStats, Progress, QuizResult


@pytest.fixture
def sample_stats():
    """Sample learning stats."""
    return LearningStats(
        total_courses=3,
        concepts_mastered=25,
        total_concepts=50,
        hours_learned=12.5,
        current_streak=5,
        longest_streak=10,
    )


@pytest.fixture
def sample_course_progress():
    """Sample course progress data."""
    return [
        {
            "course": {"id": "c1", "title": "Python Basics"},
            "progress": Progress(
                course_id="c1",
                completion_percentage=0.75,
                modules_completed=3,
                total_modules=4,
                concepts_completed=12,
                total_concepts=16,
                time_spent_minutes=120,
            ),
        },
        {
            "course": {"id": "c2", "title": "CUDA Programming"},
            "progress": Progress(
                course_id="c2",
                completion_percentage=0.25,
                modules_completed=1,
                total_modules=4,
                concepts_completed=4,
                total_concepts=16,
                time_spent_minutes=60,
            ),
        },
    ]


class TestRenderProgressPage:
    """Tests for render_progress_page function."""

    def test_render_progress_page_basic(self, mock_streamlit):
        """Test rendering progress page without errors."""
        with patch("sensei.ui.pages.progress.st", mock_streamlit):
            with patch("sensei.ui.components.sidebar.st", mock_streamlit):
                from sensei.ui.pages.progress import render_progress_page
                
                render_progress_page()
                
                mock_streamlit.markdown.assert_called()

    def test_render_progress_page_shows_header(self, mock_streamlit):
        """Test page shows header."""
        with patch("sensei.ui.pages.progress.st", mock_streamlit):
            with patch("sensei.ui.components.sidebar.st", mock_streamlit):
                from sensei.ui.pages.progress import render_progress_page
                
                render_progress_page()
                
                calls = mock_streamlit.markdown.call_args_list
                assert any("Progress" in str(c) for c in calls)

    def test_render_progress_page_shows_stats(
        self, mock_streamlit, sample_stats
    ):
        """Test page shows learning stats."""
        with patch("sensei.ui.pages.progress.st", mock_streamlit):
            with patch("sensei.ui.components.sidebar.st", mock_streamlit):
                from sensei.ui.pages.progress import render_progress_page
                
                render_progress_page(stats=sample_stats)
                
                calls = mock_streamlit.markdown.call_args_list
                # Should show stats
                assert any("Courses" in str(c) for c in calls)

    def test_render_progress_page_shows_courses(
        self, mock_streamlit, sample_course_progress
    ):
        """Test page shows course progress."""
        with patch("sensei.ui.pages.progress.st", mock_streamlit):
            with patch("sensei.ui.components.sidebar.st", mock_streamlit):
                from sensei.ui.pages.progress import render_progress_page
                
                render_progress_page(course_progress=sample_course_progress)
                
                mock_streamlit.progress.assert_called()


class TestRenderStatsSection:
    """Tests for _render_stats_section function."""

    def test_render_stats_section_shows_columns(
        self, mock_streamlit, sample_stats
    ):
        """Test stats section creates 4 columns."""
        with patch("sensei.ui.pages.progress.st", mock_streamlit):
            from sensei.ui.pages.progress import _render_stats_section
            
            _render_stats_section(sample_stats)
            
            # Should create 4 columns for stats
            mock_streamlit.columns.assert_called_with(4)

    def test_render_stats_section_handles_none(self, mock_streamlit):
        """Test stats section handles None stats."""
        with patch("sensei.ui.pages.progress.st", mock_streamlit):
            from sensei.ui.pages.progress import _render_stats_section
            
            _render_stats_section(None)
            
            mock_streamlit.markdown.assert_called()


class TestRenderCourseProgressSection:
    """Tests for _render_course_progress_section function."""

    def test_render_course_progress_empty(self, mock_streamlit):
        """Test shows message when no courses."""
        with patch("sensei.ui.pages.progress.st", mock_streamlit):
            from sensei.ui.pages.progress import _render_course_progress_section
            
            _render_course_progress_section([], None)
            
            calls = mock_streamlit.markdown.call_args_list
            assert any("No courses" in str(c) for c in calls)

    def test_render_course_progress_with_courses(
        self, mock_streamlit, sample_course_progress
    ):
        """Test renders progress bars for courses."""
        with patch("sensei.ui.pages.progress.st", mock_streamlit):
            from sensei.ui.pages.progress import _render_course_progress_section
            
            _render_course_progress_section(sample_course_progress, None)
            
            # Should show progress bars
            assert mock_streamlit.progress.call_count >= 2


class TestRenderQuizHistorySection:
    """Tests for _render_quiz_history_section function."""

    def test_render_quiz_history_empty(self, mock_streamlit):
        """Test shows message when no quiz history."""
        with patch("sensei.ui.pages.progress.st", mock_streamlit):
            from sensei.ui.pages.progress import _render_quiz_history_section
            
            _render_quiz_history_section([])
            
            calls = mock_streamlit.markdown.call_args_list
            assert any("No quizzes" in str(c) for c in calls)

    def test_render_quiz_history_with_data(self, mock_streamlit):
        """Test renders dataframe for quiz history."""
        with patch("sensei.ui.pages.progress.st", mock_streamlit):
            from sensei.ui.pages.progress import _render_quiz_history_section
            
            quiz_results = [
                QuizResult(
                    quiz_id="q1",
                    module_id="m1",
                    score=0.85,
                    correct_count=17,
                    total_questions=20,
                    passed=True,
                ),
            ]
            
            _render_quiz_history_section(quiz_results)
            
            mock_streamlit.dataframe.assert_called()


class TestRenderProgressWithServices:
    """Tests for render_progress_with_services function."""

    def test_render_with_services_calls_services(self, mock_streamlit):
        """Test service integration calls correct methods."""
        with patch("sensei.ui.pages.progress.st", mock_streamlit):
            with patch("sensei.ui.components.sidebar.st", mock_streamlit):
                from sensei.ui.pages.progress import render_progress_with_services
                
                mock_progress_service = MagicMock()
                mock_progress_service.get_learning_stats.return_value = LearningStats()
                mock_progress_service.get_course_progress.return_value = Progress(course_id="t")
                mock_progress_service.get_quiz_history.return_value = []
                
                mock_course_service = MagicMock()
                mock_course_service.list_courses.return_value = []
                
                render_progress_with_services(
                    progress_service=mock_progress_service,
                    course_service=mock_course_service,
                )
                
                mock_progress_service.get_learning_stats.assert_called_once()
                mock_course_service.list_courses.assert_called_once()
