"""Unit tests for learning page."""

from unittest.mock import MagicMock, patch

import pytest

from sensei.models.schemas import ChatMessage, ConceptLesson, LearningSession
from sensei.models.enums import MessageRole


@pytest.fixture
def sample_concept_lesson():
    """Sample ConceptLesson for testing."""
    return ConceptLesson(
        concept_id="c1",
        concept_title="Variables in Python",
        lesson_content="# Variables\n\nA variable stores data...",
        module_title="Module 1: Introduction",
        module_idx=0,
        concept_idx=1,
        total_concepts_in_module=5,
        has_previous=True,
        has_next=True,
        is_module_complete=False,
    )


@pytest.fixture
def sample_concept_lesson_module_end():
    """Sample ConceptLesson at module end."""
    return ConceptLesson(
        concept_id="c5",
        concept_title="Summary",
        lesson_content="# Summary\n\nIn this module...",
        module_title="Module 1: Introduction",
        module_idx=0,
        concept_idx=4,
        total_concepts_in_module=5,
        has_previous=True,
        has_next=False,
        is_module_complete=True,
    )


@pytest.fixture
def sample_chat_history():
    """Sample chat history for testing."""
    return [
        ChatMessage(role=MessageRole.USER, content="What is a variable?"),
        ChatMessage(
            role=MessageRole.ASSISTANT,
            content="A variable is a named storage location...",
        ),
    ]


class TestRenderLearningPage:
    """Tests for render_learning_page function."""

    def test_render_learning_page_basic(self, mock_streamlit):
        """Test rendering learning page without errors."""
        with patch("sensei.ui.pages.learning.st", mock_streamlit):
            with patch("sensei.ui.components.sidebar.st", mock_streamlit):
                with patch("sensei.ui.components.concept_viewer.st", mock_streamlit):
                    with patch("sensei.ui.components.chat_interface.st", mock_streamlit):
                        from sensei.ui.pages.learning import render_learning_page
                        
                        render_learning_page(
                            course_title="Test Course",
                        )
                        
                        mock_streamlit.markdown.assert_called()

    def test_render_learning_page_with_concept(
        self, mock_streamlit, sample_concept_lesson
    ):
        """Test page renders concept content."""
        with patch("sensei.ui.pages.learning.st", mock_streamlit):
            with patch("sensei.ui.components.sidebar.st", mock_streamlit):
                with patch("sensei.ui.components.concept_viewer.st", mock_streamlit):
                    with patch("sensei.ui.components.chat_interface.st", mock_streamlit):
                        from sensei.ui.pages.learning import render_learning_page
                        
                        render_learning_page(
                            course_title="Python Basics",
                            concept_lesson=sample_concept_lesson,
                        )
                        
                        calls = mock_streamlit.markdown.call_args_list
                        # Should show course title
                        assert any("Python Basics" in str(c) for c in calls)

    def test_render_learning_page_shows_progress(
        self, mock_streamlit, sample_concept_lesson
    ):
        """Test page shows progress indicator."""
        with patch("sensei.ui.pages.learning.st", mock_streamlit):
            with patch("sensei.ui.components.sidebar.st", mock_streamlit):
                with patch("sensei.ui.components.concept_viewer.st", mock_streamlit):
                    with patch("sensei.ui.components.chat_interface.st", mock_streamlit):
                        from sensei.ui.pages.learning import render_learning_page
                        
                        render_learning_page(
                            concept_lesson=sample_concept_lesson,
                        )
                        
                        mock_streamlit.progress.assert_called()

    def test_render_learning_page_shows_chat_input(
        self, mock_streamlit, sample_concept_lesson
    ):
        """Test page shows chat input for Q&A."""
        with patch("sensei.ui.pages.learning.st", mock_streamlit):
            with patch("sensei.ui.components.sidebar.st", mock_streamlit):
                with patch("sensei.ui.components.concept_viewer.st", mock_streamlit):
                    with patch("sensei.ui.components.chat_interface.st", mock_streamlit):
                        from sensei.ui.pages.learning import render_learning_page
                        
                        render_learning_page(
                            concept_lesson=sample_concept_lesson,
                        )
                        
                        mock_streamlit.chat_input.assert_called()

    def test_render_learning_page_shows_quiz_button_at_module_end(
        self, mock_streamlit, sample_concept_lesson_module_end
    ):
        """Test page shows Take Quiz button when module is complete."""
        with patch("sensei.ui.pages.learning.st", mock_streamlit):
            with patch("sensei.ui.components.sidebar.st", mock_streamlit):
                with patch("sensei.ui.components.concept_viewer.st", mock_streamlit):
                    with patch("sensei.ui.components.chat_interface.st", mock_streamlit):
                        from sensei.ui.pages.learning import render_learning_page
                        
                        render_learning_page(
                            concept_lesson=sample_concept_lesson_module_end,
                            is_module_complete=True,
                        )
                        
                        button_calls = [
                            c for c in mock_streamlit.button.call_args_list
                            if "Take Quiz" in str(c)
                        ]
                        assert len(button_calls) > 0

    def test_render_learning_page_quiz_callback(
        self, mock_streamlit, sample_concept_lesson_module_end
    ):
        """Test Take Quiz button triggers callback."""
        def button_side_effect(*args, **kwargs):
            if "take_quiz" in kwargs.get("key", ""):
                return True
            return False
        
        mock_streamlit.button.side_effect = button_side_effect
        
        with patch("sensei.ui.pages.learning.st", mock_streamlit):
            with patch("sensei.ui.components.sidebar.st", mock_streamlit):
                with patch("sensei.ui.components.concept_viewer.st", mock_streamlit):
                    with patch("sensei.ui.components.chat_interface.st", mock_streamlit):
                        from sensei.ui.pages.learning import render_learning_page
                        
                        callback = MagicMock()
                        
                        render_learning_page(
                            concept_lesson=sample_concept_lesson_module_end,
                            is_module_complete=True,
                            on_take_quiz=callback,
                        )
                        
                        callback.assert_called_once()

    def test_render_learning_page_navigation_callbacks(
        self, mock_streamlit, sample_concept_lesson
    ):
        """Test navigation callbacks are passed to concept viewer."""
        with patch("sensei.ui.pages.learning.st", mock_streamlit):
            with patch("sensei.ui.components.sidebar.st", mock_streamlit):
                with patch("sensei.ui.components.concept_viewer.st", mock_streamlit):
                    with patch("sensei.ui.components.chat_interface.st", mock_streamlit):
                        with patch(
                            "sensei.ui.pages.learning.render_concept_with_navigation"
                        ) as mock_nav:
                            from sensei.ui.pages.learning import render_learning_page
                            
                            prev_callback = MagicMock()
                            next_callback = MagicMock()
                            
                            render_learning_page(
                                concept_lesson=sample_concept_lesson,
                                on_previous=prev_callback,
                                on_next=next_callback,
                            )
                            
                            mock_nav.assert_called_once()
                            call_kwargs = mock_nav.call_args[1]
                            assert call_kwargs.get("on_previous") == prev_callback
                            assert call_kwargs.get("on_next") == next_callback


class TestRenderHeader:
    """Tests for _render_header function."""

    def test_render_header_shows_course_title(
        self, mock_streamlit, sample_concept_lesson
    ):
        """Test header shows course title."""
        with patch("sensei.ui.pages.learning.st", mock_streamlit):
            from sensei.ui.pages.learning import _render_header
            
            _render_header("Python Basics", sample_concept_lesson)
            
            calls = mock_streamlit.markdown.call_args_list
            assert any("Python Basics" in str(c) for c in calls)

    def test_render_header_shows_module_title(
        self, mock_streamlit, sample_concept_lesson
    ):
        """Test header shows module title."""
        with patch("sensei.ui.pages.learning.st", mock_streamlit):
            from sensei.ui.pages.learning import _render_header
            
            _render_header("Python Basics", sample_concept_lesson)
            
            calls = mock_streamlit.markdown.call_args_list
            assert any("Module 1" in str(c) for c in calls)


class TestRenderProgressBar:
    """Tests for _render_progress_bar function."""

    def test_render_progress_bar_shows_dots(
        self, mock_streamlit, sample_concept_lesson
    ):
        """Test progress bar shows dot indicators."""
        with patch("sensei.ui.pages.learning.st", mock_streamlit):
            from sensei.ui.pages.learning import _render_progress_bar
            
            _render_progress_bar(sample_concept_lesson)
            
            calls = mock_streamlit.markdown.call_args_list
            # Should have dots (●○)
            assert any("●" in str(c) or "○" in str(c) for c in calls)

    def test_render_progress_bar_shows_progress(
        self, mock_streamlit, sample_concept_lesson
    ):
        """Test progress bar shows st.progress."""
        with patch("sensei.ui.pages.learning.st", mock_streamlit):
            from sensei.ui.pages.learning import _render_progress_bar
            
            _render_progress_bar(sample_concept_lesson)
            
            mock_streamlit.progress.assert_called()

    def test_render_progress_bar_handles_none(self, mock_streamlit):
        """Test progress bar handles None lesson."""
        with patch("sensei.ui.pages.learning.st", mock_streamlit):
            from sensei.ui.pages.learning import _render_progress_bar
            
            _render_progress_bar(None)
            
            # Should not call progress when no lesson
            mock_streamlit.progress.assert_not_called()


class TestRenderConceptSection:
    """Tests for _render_concept_section function."""

    def test_render_concept_section_calls_component(
        self, mock_streamlit, sample_concept_lesson
    ):
        """Test concept section uses render_concept_with_navigation."""
        with patch("sensei.ui.pages.learning.st", mock_streamlit):
            with patch("sensei.ui.components.concept_viewer.st", mock_streamlit):
                with patch(
                    "sensei.ui.pages.learning.render_concept_with_navigation"
                ) as mock_render:
                    from sensei.ui.pages.learning import _render_concept_section
                    
                    _render_concept_section(
                        sample_concept_lesson,
                        on_previous=None,
                        on_next=None,
                    )
                    
                    mock_render.assert_called_once()


class TestRenderChatSection:
    """Tests for _render_chat_section function."""

    def test_render_chat_section_shows_input(self, mock_streamlit):
        """Test chat section shows chat input."""
        with patch("sensei.ui.pages.learning.st", mock_streamlit):
            with patch("sensei.ui.components.chat_interface.st", mock_streamlit):
                from sensei.ui.pages.learning import _render_chat_section
                
                _render_chat_section(messages=[], on_ask_question=None)
                
                mock_streamlit.chat_input.assert_called()

    def test_render_chat_section_shows_history(
        self, mock_streamlit, sample_chat_history
    ):
        """Test chat section shows message history."""
        with patch("sensei.ui.pages.learning.st", mock_streamlit):
            with patch("sensei.ui.components.chat_interface.st", mock_streamlit):
                with patch(
                    "sensei.ui.pages.learning.render_chat_with_form"
                ) as mock_chat:
                    from sensei.ui.pages.learning import _render_chat_section
                    
                    _render_chat_section(
                        messages=sample_chat_history,
                        on_ask_question=None,
                    )
                    
                    # Should show expander with history
                    mock_streamlit.expander.assert_called()


class TestRenderModuleCompleteSection:
    """Tests for _render_module_complete_section function."""

    def test_quiz_not_taken_shows_take_quiz_message(self, mock_streamlit):
        """Test quiz not taken shows module complete and take quiz button."""
        with patch("sensei.ui.pages.learning.st", mock_streamlit):
            from sensei.ui.pages.learning import _render_module_complete_section
            
            _render_module_complete_section(
                quiz_passed=None,  # Not taken
                is_last_module=False,
                on_take_quiz=None,
                on_next_module=None,
            )
            
            calls = mock_streamlit.markdown.call_args_list
            assert any("Module Complete" in str(c) for c in calls)

    def test_quiz_not_taken_shows_take_quiz_button(self, mock_streamlit):
        """Test quiz not taken shows Take Quiz button."""
        with patch("sensei.ui.pages.learning.st", mock_streamlit):
            from sensei.ui.pages.learning import _render_module_complete_section
            
            _render_module_complete_section(
                quiz_passed=None,
                is_last_module=False,
                on_take_quiz=None,
                on_next_module=None,
            )
            
            button_calls = [
                c for c in mock_streamlit.button.call_args_list
                if "Take Quiz" in str(c)
            ]
            assert len(button_calls) > 0

    def test_quiz_not_taken_callback(self, mock_streamlit):
        """Test Take Quiz button triggers callback."""
        mock_streamlit.button.return_value = True
        
        with patch("sensei.ui.pages.learning.st", mock_streamlit):
            from sensei.ui.pages.learning import _render_module_complete_section
            
            callback = MagicMock()
            _render_module_complete_section(
                quiz_passed=None,
                is_last_module=False,
                on_take_quiz=callback,
                on_next_module=None,
            )
            
            callback.assert_called_once()

    def test_quiz_passed_shows_continue_button(self, mock_streamlit):
        """Test quiz passed shows Continue to Next Module button."""
        with patch("sensei.ui.pages.learning.st", mock_streamlit):
            from sensei.ui.pages.learning import _render_module_complete_section
            
            _render_module_complete_section(
                quiz_passed=True,
                is_last_module=False,
                on_take_quiz=None,
                on_next_module=None,
            )
            
            calls = mock_streamlit.markdown.call_args_list
            assert any("Quiz Passed" in str(c) for c in calls)
            
            button_calls = [
                c for c in mock_streamlit.button.call_args_list
                if "Continue to Next Module" in str(c)
            ]
            assert len(button_calls) > 0

    def test_quiz_passed_next_module_callback(self, mock_streamlit):
        """Test Continue to Next Module triggers callback."""
        mock_streamlit.button.return_value = True
        
        with patch("sensei.ui.pages.learning.st", mock_streamlit):
            from sensei.ui.pages.learning import _render_module_complete_section
            
            callback = MagicMock()
            _render_module_complete_section(
                quiz_passed=True,
                is_last_module=False,
                on_take_quiz=None,
                on_next_module=callback,
            )
            
            callback.assert_called_once()

    def test_quiz_passed_last_module_shows_course_complete(self, mock_streamlit):
        """Test last module shows Course Complete message."""
        with patch("sensei.ui.pages.learning.st", mock_streamlit):
            from sensei.ui.pages.learning import _render_module_complete_section
            
            _render_module_complete_section(
                quiz_passed=True,
                is_last_module=True,
                on_take_quiz=None,
                on_next_module=None,
            )
            
            calls = mock_streamlit.markdown.call_args_list
            assert any("Course Complete" in str(c) for c in calls)
            
            button_calls = [
                c for c in mock_streamlit.button.call_args_list
                if "Dashboard" in str(c)
            ]
            assert len(button_calls) > 0

    def test_quiz_failed_shows_retake_button(self, mock_streamlit):
        """Test quiz failed shows Retake Quiz button."""
        with patch("sensei.ui.pages.learning.st", mock_streamlit):
            from sensei.ui.pages.learning import _render_module_complete_section
            
            _render_module_complete_section(
                quiz_passed=False,
                is_last_module=False,
                on_take_quiz=None,
                on_next_module=None,
            )
            
            calls = mock_streamlit.markdown.call_args_list
            assert any("Keep Practicing" in str(c) for c in calls)
            
            button_calls = [
                c for c in mock_streamlit.button.call_args_list
                if "Retake Quiz" in str(c)
            ]
            assert len(button_calls) > 0

    def test_quiz_failed_retake_callback(self, mock_streamlit):
        """Test Retake Quiz button triggers on_take_quiz callback."""
        mock_streamlit.button.return_value = True
        
        with patch("sensei.ui.pages.learning.st", mock_streamlit):
            from sensei.ui.pages.learning import _render_module_complete_section
            
            callback = MagicMock()
            _render_module_complete_section(
                quiz_passed=False,
                is_last_module=False,
                on_take_quiz=callback,
                on_next_module=None,
            )
            
            callback.assert_called_once()


class TestRenderLearningWithServices:
    """Tests for render_learning_with_services function."""

    def test_render_with_services_starts_session(self, mock_streamlit):
        """Test service integration starts session for course."""
        with patch("sensei.ui.pages.learning.st", mock_streamlit):
            with patch("sensei.ui.components.sidebar.st", mock_streamlit):
                with patch("sensei.ui.components.concept_viewer.st", mock_streamlit):
                    with patch("sensei.ui.components.chat_interface.st", mock_streamlit):
                        from sensei.ui.pages.learning import render_learning_with_services
                        from sensei.models.schemas import ConceptLesson, LearningSession
                        
                        mock_learning_service = MagicMock()
                        mock_learning_service.is_session_active = False
                        mock_learning_service.current_session = LearningSession(
                            course_id="test"
                        )
                        mock_learning_service.get_current_concept.return_value = ConceptLesson(
                            concept_id="c1",
                            concept_title="Test",
                            lesson_content="Content",
                        )
                        mock_learning_service.is_module_complete.return_value = False
                        mock_learning_service.course_data = {"title": "Test"}
                        
                        # After start_session, is_session_active should be True
                        def start_side_effect(course_id):
                            mock_learning_service.is_session_active = True
                        
                        mock_learning_service.start_session.side_effect = start_side_effect
                        
                        render_learning_with_services(
                            learning_service=mock_learning_service,
                            course_id="test-course",
                        )
                        
                        mock_learning_service.start_session.assert_called_with("test-course")

    def test_render_with_services_no_session_error(self, mock_streamlit):
        """Test shows error when no active session."""
        with patch("sensei.ui.pages.learning.st", mock_streamlit):
            with patch("sensei.ui.components.sidebar.st", mock_streamlit):
                with patch("sensei.ui.components.concept_viewer.st", mock_streamlit):
                    with patch("sensei.ui.components.chat_interface.st", mock_streamlit):
                        from sensei.ui.pages.learning import render_learning_with_services
                        
                        mock_learning_service = MagicMock()
                        mock_learning_service.is_session_active = False
                        
                        render_learning_with_services(
                            learning_service=mock_learning_service,
                        )
                        
                        mock_streamlit.error.assert_called()

    def test_render_with_services_uses_user_prefs(self, mock_streamlit):
        """Test service integration uses user preferences."""
        with patch("sensei.ui.pages.learning.st", mock_streamlit):
            with patch("sensei.ui.components.sidebar.st", mock_streamlit):
                with patch("sensei.ui.components.concept_viewer.st", mock_streamlit):
                    with patch("sensei.ui.components.chat_interface.st", mock_streamlit):
                        from sensei.ui.pages.learning import render_learning_with_services
                        from sensei.models.schemas import (
                            ConceptLesson, LearningSession, UserPreferences
                        )
                        
                        mock_learning_service = MagicMock()
                        mock_learning_service.is_session_active = True
                        mock_learning_service.current_session = LearningSession(
                            course_id="test"
                        )
                        mock_learning_service.get_current_concept.return_value = ConceptLesson(
                            concept_id="c1",
                            concept_title="Test",
                            lesson_content="Content",
                        )
                        mock_learning_service.is_module_complete.return_value = False
                        mock_learning_service.course_data = {"title": "Test"}
                        
                        mock_user_service = MagicMock()
                        mock_user_service.get_preferences.return_value = UserPreferences()
                        
                        render_learning_with_services(
                            learning_service=mock_learning_service,
                            user_service=mock_user_service,
                        )
                        
                        mock_user_service.get_preferences.assert_called_once()

    def test_render_with_services_uses_course_data_property(self, mock_streamlit):
        """Test service integration uses public course_data property."""
        with patch("sensei.ui.pages.learning.st", mock_streamlit):
            with patch("sensei.ui.components.sidebar.st", mock_streamlit):
                with patch("sensei.ui.components.concept_viewer.st", mock_streamlit):
                    with patch("sensei.ui.components.chat_interface.st", mock_streamlit):
                        with patch(
                            "sensei.ui.pages.learning.render_learning_page"
                        ) as mock_render:
                            from sensei.ui.pages.learning import render_learning_with_services
                            from sensei.models.schemas import ConceptLesson, LearningSession
                            
                            mock_learning_service = MagicMock()
                            mock_learning_service.is_session_active = True
                            mock_learning_service.current_session = LearningSession(
                                course_id="test"
                            )
                            mock_learning_service.get_current_concept.return_value = ConceptLesson(
                                concept_id="c1",
                                concept_title="Test",
                                lesson_content="Content",
                            )
                            mock_learning_service.is_module_complete.return_value = False
                            # Set course_data as a property (not _course_data)
                            mock_learning_service.course_data = {
                                "title": "Test Course",
                                "modules": [{"title": "Module 1"}],
                            }
                            
                            render_learning_with_services(
                                learning_service=mock_learning_service,
                            )
                            
                            # Verify render_learning_page was called with course_outline from course_data
                            mock_render.assert_called_once()
                            call_kwargs = mock_render.call_args[1]
                            assert call_kwargs["course_outline"] == mock_learning_service.course_data
                            assert call_kwargs["course_title"] == "Test Course"

    def test_render_with_services_shows_spinner_during_lesson_generation(
        self, mock_streamlit
    ):
        """Test spinner is shown during initial lesson loading."""
        with patch("sensei.ui.pages.learning.st", mock_streamlit):
            with patch("sensei.ui.components.sidebar.st", mock_streamlit):
                with patch("sensei.ui.components.concept_viewer.st", mock_streamlit):
                    with patch("sensei.ui.components.chat_interface.st", mock_streamlit):
                        from sensei.ui.pages.learning import render_learning_with_services
                        from sensei.models.schemas import ConceptLesson, LearningSession
                        
                        mock_learning_service = MagicMock()
                        mock_learning_service.is_session_active = True
                        mock_learning_service.current_session = LearningSession(
                            course_id="test"
                        )
                        mock_learning_service.get_current_concept.return_value = ConceptLesson(
                            concept_id="c1",
                            concept_title="Test",
                            lesson_content="Content",
                        )
                        mock_learning_service.is_module_complete.return_value = False
                        mock_learning_service.course_data = {"title": "Test"}
                        
                        render_learning_with_services(
                            learning_service=mock_learning_service,
                        )
                        
                        # Verify spinner was called during lesson loading
                        mock_streamlit.spinner.assert_called()
                        spinner_calls = mock_streamlit.spinner.call_args_list
                        # Initial load uses "Loading lesson..." spinner
                        assert any("Loading lesson" in str(c) for c in spinner_calls)

    def test_render_with_services_shows_loading_state_during_navigation(
        self, mock_streamlit
    ):
        """Test loading state is shown when navigating between concepts."""
        # Set the navigating flag to True
        mock_streamlit.session_state = {"learning_is_navigating": True}
        
        with patch("sensei.ui.pages.learning.st", mock_streamlit):
            with patch("sensei.ui.pages.learning.render_loading_state") as mock_loading:
                with patch("sensei.ui.components.sidebar.st", mock_streamlit):
                    from sensei.ui.pages.learning import render_learning_with_services
                    from sensei.models.schemas import ConceptLesson, LearningSession
                    
                    mock_learning_service = MagicMock()
                    mock_learning_service.is_session_active = True
                    mock_learning_service.current_session = LearningSession(
                        course_id="test"
                    )
                    mock_learning_service.get_current_concept.return_value = ConceptLesson(
                        concept_id="c1",
                        concept_title="Test",
                        lesson_content="Content",
                    )
                    
                    render_learning_with_services(
                        learning_service=mock_learning_service,
                    )
                    
                    # Verify render_loading_state was called during navigation
                    mock_loading.assert_called_once()
                    call_kwargs = mock_loading.call_args[1]
                    assert "next concept" in call_kwargs["message"]


class TestRenderChatSection:
    """Tests for _render_chat_section function loading state."""

    def test_render_chat_section_shows_spinner_for_qa(
        self, mock_streamlit, sample_chat_history
    ):
        """Test spinner is shown when asking a question."""
        # Simulate chat input returning a question
        mock_streamlit.chat_input.return_value = "What is a variable?"
        
        with patch("sensei.ui.pages.learning.st", mock_streamlit):
            with patch("sensei.ui.components.chat_interface.st", mock_streamlit):
                from sensei.ui.pages.learning import _render_chat_section
                
                callback = MagicMock(return_value="Answer")
                
                # The function will call spinner for the question
                _render_chat_section(
                    messages=sample_chat_history,
                    on_ask_question=callback,
                )
                
                # Verify spinner was called with Sensei thinking message
                mock_streamlit.spinner.assert_called()
                spinner_calls = mock_streamlit.spinner.call_args_list
                assert any("Sensei is thinking" in str(c) for c in spinner_calls)
