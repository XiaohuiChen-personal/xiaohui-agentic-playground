"""Unit tests for the main Sensei application entry point."""

from unittest.mock import MagicMock, patch

import pytest


class TestPageConfiguration:
    """Tests for page configuration constants."""
    
    def test_page_title_constant(self):
        """Test page title is set correctly."""
        from sensei.app import PAGE_TITLE
        
        assert PAGE_TITLE == "Sensei - AI Learning Tutor"
    
    def test_page_icon_constant(self):
        """Test page icon is set correctly."""
        from sensei.app import PAGE_ICON
        
        assert PAGE_ICON == "🥋"
    
    def test_page_layout_constant(self):
        """Test page layout is set correctly."""
        from sensei.app import PAGE_LAYOUT
        
        assert PAGE_LAYOUT == "wide"
    
    def test_valid_pages_contains_all_pages(self):
        """Test VALID_PAGES contains all expected pages."""
        from sensei.app import VALID_PAGES
        
        expected_pages = {
            "dashboard",
            "new_course",
            "learning",
            "quiz",
            "progress",
            "settings",
            "onboarding",
        }
        
        assert VALID_PAGES == expected_pages


class TestConfigurePage:
    """Tests for configure_page function."""
    
    @patch("sensei.app.st")
    def test_configure_page_calls_set_page_config(self, mock_st):
        """Test that configure_page calls st.set_page_config with correct params."""
        from sensei.app import configure_page
        
        configure_page()
        
        mock_st.set_page_config.assert_called_once_with(
            page_title="Sensei - AI Learning Tutor",
            page_icon="🥋",
            layout="wide",
            initial_sidebar_state="expanded",
        )


class TestInitializeServices:
    """Tests for service initialization."""
    
    @patch("sensei.app.st")
    @patch("sensei.app.UserService")
    @patch("sensei.app.ProgressService")
    @patch("sensei.app.CourseService")
    @patch("sensei.app.LearningService")
    @patch("sensei.app.QuizService")
    def test_initialize_services_creates_all_services(
        self,
        mock_quiz,
        mock_learning,
        mock_course,
        mock_progress,
        mock_user,
        mock_st,
    ):
        """Test that initialize_services creates all 5 services."""
        from sensei.app import initialize_services
        
        mock_st.session_state = {}
        
        services = initialize_services()
        
        assert "user" in services
        assert "progress" in services
        assert "course" in services
        assert "learning" in services
        assert "quiz" in services
        
        mock_user.assert_called_once()
        mock_progress.assert_called_once()
        mock_course.assert_called_once_with(use_ai=True)
        mock_learning.assert_called_once_with(use_ai=True)
        mock_quiz.assert_called_once_with(use_ai=True)
    
    @patch("sensei.app.st")
    def test_initialize_services_reuses_existing(self, mock_st):
        """Test that initialize_services returns cached services."""
        from sensei.app import initialize_services
        
        existing_services = {"user": "mock_user", "progress": "mock_progress"}
        mock_st.session_state = {"services": existing_services}
        
        services = initialize_services()
        
        assert services == existing_services


class TestGetService:
    """Tests for get_service function."""
    
    @patch("sensei.app.st")
    @patch("sensei.app.initialize_services")
    def test_get_service_returns_service(self, mock_init, mock_st):
        """Test get_service returns the requested service."""
        from sensei.app import get_service
        
        mock_user = MagicMock()
        mock_init.return_value = {"user": mock_user}
        
        result = get_service("user")
        
        assert result == mock_user
    
    @patch("sensei.app.st")
    @patch("sensei.app.initialize_services")
    def test_get_service_raises_for_invalid_name(self, mock_init, mock_st):
        """Test get_service raises KeyError for invalid service name."""
        from sensei.app import get_service
        
        mock_init.return_value = {}
        
        with pytest.raises(KeyError):
            get_service("invalid_service")


class TestNavigateTo:
    """Tests for navigation function."""
    
    @patch("sensei.app.st")
    def test_navigate_to_updates_current_page(self, mock_st):
        """Test navigate_to updates session state and reruns."""
        from sensei.app import navigate_to
        
        mock_st.session_state = {"ui": {"current_page": "dashboard"}}
        
        navigate_to("settings")
        
        assert mock_st.session_state["ui"]["current_page"] == "settings"
        mock_st.rerun.assert_called_once()
    
    @patch("sensei.app.st")
    def test_navigate_to_invalid_page_shows_error(self, mock_st):
        """Test navigate_to shows error for invalid page."""
        from sensei.app import navigate_to
        
        mock_st.session_state = {"ui": {"current_page": "dashboard"}}
        
        navigate_to("invalid_page")
        
        mock_st.error.assert_called_once()
        mock_st.rerun.assert_not_called()


class TestGetCurrentPage:
    """Tests for get_current_page function."""
    
    @patch("sensei.app.st")
    def test_get_current_page_returns_current_page(self, mock_st):
        """Test get_current_page returns the current page from state."""
        from sensei.app import get_current_page
        
        mock_st.session_state = {"ui": {"current_page": "learning"}}
        
        result = get_current_page()
        
        assert result == "learning"
    
    @patch("sensei.app.st")
    def test_get_current_page_defaults_to_dashboard(self, mock_st):
        """Test get_current_page defaults to dashboard when not set."""
        from sensei.app import get_current_page
        
        mock_st.session_state = {}
        
        result = get_current_page()
        
        assert result == "dashboard"
    
    @patch("sensei.app.st")
    def test_get_current_page_with_empty_ui(self, mock_st):
        """Test get_current_page handles empty ui dict."""
        from sensei.app import get_current_page
        
        mock_st.session_state = {"ui": {}}
        
        result = get_current_page()
        
        assert result == "dashboard"


class TestCheckOnboarding:
    """Tests for check_onboarding function."""
    
    @patch("sensei.app.get_service")
    def test_check_onboarding_returns_true_when_onboarded(self, mock_get_service):
        """Test check_onboarding returns True when user is onboarded."""
        from sensei.app import check_onboarding
        
        mock_user_service = MagicMock()
        mock_user_service.is_onboarded.return_value = True
        mock_get_service.return_value = mock_user_service
        
        result = check_onboarding()
        
        assert result is True
        mock_get_service.assert_called_once_with("user")
    
    @patch("sensei.app.get_service")
    def test_check_onboarding_returns_false_when_not_onboarded(self, mock_get_service):
        """Test check_onboarding returns False when user is not onboarded."""
        from sensei.app import check_onboarding
        
        mock_user_service = MagicMock()
        mock_user_service.is_onboarded.return_value = False
        mock_get_service.return_value = mock_user_service
        
        result = check_onboarding()
        
        assert result is False


class TestRenderCurrentPage:
    """Tests for render_current_page function."""
    
    @patch("sensei.app.render_dashboard_page")
    @patch("sensei.app.get_service")
    @patch("sensei.app.get_current_page")
    def test_render_dashboard_page(
        self,
        mock_get_page,
        mock_get_service,
        mock_render_dashboard,
    ):
        """Test dashboard page is rendered correctly."""
        from sensei.app import render_current_page
        
        mock_get_page.return_value = "dashboard"
        mock_user = MagicMock()
        mock_course = MagicMock()
        mock_progress = MagicMock()
        
        def get_service_side_effect(name):
            return {
                "user": mock_user,
                "course": mock_course,
                "progress": mock_progress,
                "learning": MagicMock(),
                "quiz": MagicMock(),
            }[name]
        
        mock_get_service.side_effect = get_service_side_effect
        
        render_current_page()
        
        mock_render_dashboard.assert_called_once()
        call_kwargs = mock_render_dashboard.call_args[1]
        assert call_kwargs["user_service"] == mock_user
        assert call_kwargs["course_service"] == mock_course
        assert call_kwargs["progress_service"] == mock_progress
    
    @patch("sensei.app.render_new_course_with_services")
    @patch("sensei.app.get_service")
    @patch("sensei.app.get_current_page")
    def test_render_new_course_page(
        self,
        mock_get_page,
        mock_get_service,
        mock_render_new_course,
    ):
        """Test new course page is rendered correctly."""
        from sensei.app import render_current_page
        
        mock_get_page.return_value = "new_course"
        mock_services = {
            "user": MagicMock(),
            "course": MagicMock(),
            "progress": MagicMock(),
            "learning": MagicMock(),
            "quiz": MagicMock(),
        }
        mock_get_service.side_effect = lambda name: mock_services[name]
        
        render_current_page()
        
        mock_render_new_course.assert_called_once()
    
    @patch("sensei.app.st")
    @patch("sensei.app.render_learning_with_services")
    @patch("sensei.app.get_service")
    @patch("sensei.app.get_current_page")
    def test_render_learning_page_with_course(
        self,
        mock_get_page,
        mock_get_service,
        mock_render_learning,
        mock_st,
    ):
        """Test learning page is rendered when course is selected."""
        from sensei.app import render_current_page
        
        mock_get_page.return_value = "learning"
        mock_st.session_state = {
            "courses": {"current_course_id": "course-123"},
            "quiz": {},
        }
        mock_learning = MagicMock()
        mock_learning.is_session_active = True
        mock_learning.current_session = MagicMock(current_module_idx=0)
        
        mock_services = {
            "user": MagicMock(),
            "course": MagicMock(),
            "progress": MagicMock(),
            "learning": mock_learning,
            "quiz": MagicMock(),
        }
        mock_get_service.side_effect = lambda name: mock_services[name]
        
        render_current_page()
        
        mock_render_learning.assert_called_once()
        call_kwargs = mock_render_learning.call_args[1]
        assert call_kwargs["course_id"] == "course-123"
    
    @patch("sensei.app.st")
    @patch("sensei.app.render_learning_with_services")
    @patch("sensei.app.get_service")
    @patch("sensei.app.get_current_page")
    def test_render_learning_page_without_course_shows_warning(
        self,
        mock_get_page,
        mock_get_service,
        mock_render_learning,
        mock_st,
    ):
        """Test learning page shows warning when no course selected."""
        from sensei.app import render_current_page
        
        mock_get_page.return_value = "learning"
        mock_st.session_state = {"courses": {}, "quiz": {}}
        mock_st.button.return_value = False
        
        mock_services = {
            "user": MagicMock(),
            "course": MagicMock(),
            "progress": MagicMock(),
            "learning": MagicMock(),
            "quiz": MagicMock(),
        }
        mock_get_service.side_effect = lambda name: mock_services[name]
        
        render_current_page()
        
        mock_st.warning.assert_called_once()
        mock_render_learning.assert_not_called()
    
    @patch("sensei.app.render_progress_with_services")
    @patch("sensei.app.get_service")
    @patch("sensei.app.get_current_page")
    def test_render_progress_page(
        self,
        mock_get_page,
        mock_get_service,
        mock_render_progress,
    ):
        """Test progress page is rendered correctly."""
        from sensei.app import render_current_page
        
        mock_get_page.return_value = "progress"
        mock_services = {
            "user": MagicMock(),
            "course": MagicMock(),
            "progress": MagicMock(),
            "learning": MagicMock(),
            "quiz": MagicMock(),
        }
        mock_get_service.side_effect = lambda name: mock_services[name]
        
        render_current_page()
        
        mock_render_progress.assert_called_once()
    
    @patch("sensei.app.render_settings_with_services")
    @patch("sensei.app.get_service")
    @patch("sensei.app.get_current_page")
    def test_render_settings_page(
        self,
        mock_get_page,
        mock_get_service,
        mock_render_settings,
    ):
        """Test settings page is rendered correctly."""
        from sensei.app import render_current_page
        
        mock_get_page.return_value = "settings"
        mock_services = {
            "user": MagicMock(),
            "course": MagicMock(),
            "progress": MagicMock(),
            "learning": MagicMock(),
            "quiz": MagicMock(),
        }
        mock_get_service.side_effect = lambda name: mock_services[name]
        
        render_current_page()
        
        mock_render_settings.assert_called_once()
    
    @patch("sensei.app.render_onboarding_with_services")
    @patch("sensei.app.get_service")
    @patch("sensei.app.get_current_page")
    def test_render_onboarding_page(
        self,
        mock_get_page,
        mock_get_service,
        mock_render_onboarding,
    ):
        """Test onboarding page is rendered correctly."""
        from sensei.app import render_current_page
        
        mock_get_page.return_value = "onboarding"
        mock_services = {
            "user": MagicMock(),
            "course": MagicMock(),
            "progress": MagicMock(),
            "learning": MagicMock(),
            "quiz": MagicMock(),
        }
        mock_get_service.side_effect = lambda name: mock_services[name]
        
        render_current_page()
        
        mock_render_onboarding.assert_called_once()


class TestMainFunction:
    """Tests for main application entry point."""
    
    @patch("sensei.app.render_current_page")
    @patch("sensei.app.check_onboarding")
    @patch("sensei.app.initialize_services")
    @patch("sensei.app.initialize_session_state")
    @patch("sensei.app.load_environment")
    @patch("sensei.app.configure_page")
    @patch("sensei.app.st")
    def test_main_calls_all_initialization_functions(
        self,
        mock_st,
        mock_configure,
        mock_load_env,
        mock_init_state,
        mock_init_services,
        mock_check_onboarding,
        mock_render,
    ):
        """Test main calls all initialization functions in order."""
        from sensei.app import main
        
        mock_st.session_state = {"ui": {"current_page": "dashboard"}}
        mock_check_onboarding.return_value = True
        
        main()
        
        mock_configure.assert_called_once()
        mock_load_env.assert_called_once()
        mock_init_state.assert_called_once()
        mock_init_services.assert_called_once()
        mock_check_onboarding.assert_called_once()
        mock_render.assert_called_once()
    
    @patch("sensei.app.render_current_page")
    @patch("sensei.app.check_onboarding")
    @patch("sensei.app.initialize_services")
    @patch("sensei.app.initialize_session_state")
    @patch("sensei.app.load_environment")
    @patch("sensei.app.configure_page")
    @patch("sensei.app.st")
    def test_main_redirects_to_onboarding_for_new_users(
        self,
        mock_st,
        mock_configure,
        mock_load_env,
        mock_init_state,
        mock_init_services,
        mock_check_onboarding,
        mock_render,
    ):
        """Test main redirects to onboarding for new users."""
        from sensei.app import main
        
        mock_st.session_state = {"ui": {"current_page": "dashboard"}}
        mock_check_onboarding.return_value = False
        
        main()
        
        assert mock_st.session_state["ui"]["current_page"] == "onboarding"
    
    @patch("sensei.app.render_current_page")
    @patch("sensei.app.check_onboarding")
    @patch("sensei.app.initialize_services")
    @patch("sensei.app.initialize_session_state")
    @patch("sensei.app.load_environment")
    @patch("sensei.app.configure_page")
    @patch("sensei.app.st")
    def test_main_handles_errors_gracefully(
        self,
        mock_st,
        mock_configure,
        mock_load_env,
        mock_init_state,
        mock_init_services,
        mock_check_onboarding,
        mock_render,
    ):
        """Test main handles errors and shows recovery option."""
        from sensei.app import main
        
        mock_st.session_state = {"ui": {"current_page": "dashboard"}}
        mock_check_onboarding.return_value = True
        mock_render.side_effect = Exception("Test error")
        mock_st.button.return_value = False
        
        main()
        
        mock_st.error.assert_called_with("An unexpected error occurred.")
        mock_st.exception.assert_called_once()
    
    @patch("sensei.app.render_current_page")
    @patch("sensei.app.check_onboarding")
    @patch("sensei.app.initialize_services")
    @patch("sensei.app.initialize_session_state")
    @patch("sensei.app.load_environment")
    @patch("sensei.app.configure_page")
    @patch("sensei.app.st")
    def test_main_error_recovery_button_redirects_to_dashboard(
        self,
        mock_st,
        mock_configure,
        mock_load_env,
        mock_init_state,
        mock_init_services,
        mock_check_onboarding,
        mock_render,
    ):
        """Test error recovery button redirects to dashboard."""
        from sensei.app import main
        
        mock_st.session_state = {"ui": {"current_page": "learning"}}
        mock_check_onboarding.return_value = True
        mock_render.side_effect = Exception("Test error")
        mock_st.button.return_value = True  # User clicks recovery button
        
        main()
        
        assert mock_st.session_state["ui"]["current_page"] == "dashboard"
        mock_st.rerun.assert_called_once()


class TestNavigationCallbacks:
    """Tests for navigation callback functions."""
    
    @patch("sensei.app.st")
    @patch("sensei.app.render_dashboard_page")
    @patch("sensei.app.get_service")
    @patch("sensei.app.get_current_page")
    def test_on_continue_course_callback(
        self,
        mock_get_page,
        mock_get_service,
        mock_render_dashboard,
        mock_st,
    ):
        """Test on_continue_course sets course ID and navigates to learning."""
        from sensei.app import render_current_page
        
        mock_get_page.return_value = "dashboard"
        mock_st.session_state = {"courses": {}, "ui": {"current_page": "dashboard"}}
        
        mock_services = {
            "user": MagicMock(),
            "course": MagicMock(),
            "progress": MagicMock(),
            "learning": MagicMock(),
            "quiz": MagicMock(),
        }
        mock_get_service.side_effect = lambda name: mock_services[name]
        
        render_current_page()
        
        # Get the callback and call it
        call_kwargs = mock_render_dashboard.call_args[1]
        on_continue = call_kwargs["on_continue_course"]
        
        on_continue("course-123")
        
        assert mock_st.session_state["courses"]["current_course_id"] == "course-123"
    
    @patch("sensei.app.st")
    @patch("sensei.app.render_dashboard_page")
    @patch("sensei.app.get_service")
    @patch("sensei.app.get_current_page")
    def test_on_new_course_clears_generated_course(
        self,
        mock_get_page,
        mock_get_service,
        mock_render_dashboard,
        mock_st,
    ):
        """Test on_new_course clears generated course from session."""
        from sensei.app import render_current_page
        
        mock_get_page.return_value = "dashboard"
        mock_st.session_state = {
            "courses": {},
            "ui": {"current_page": "dashboard"},
            "generated_course": {"id": "old-course"},
        }
        
        mock_services = {
            "user": MagicMock(),
            "course": MagicMock(),
            "progress": MagicMock(),
            "learning": MagicMock(),
            "quiz": MagicMock(),
        }
        mock_get_service.side_effect = lambda name: mock_services[name]
        
        render_current_page()
        
        # Get the callback and call it
        call_kwargs = mock_render_dashboard.call_args[1]
        on_new_course = call_kwargs["on_new_course"]
        
        on_new_course()
        
        assert "generated_course" not in mock_st.session_state


class TestQuizPageIntegration:
    """Tests for quiz page routing and integration."""
    
    @patch("sensei.app.st")
    @patch("sensei.app.render_quiz_with_services")
    @patch("sensei.app.get_service")
    @patch("sensei.app.get_current_page")
    def test_render_quiz_page_with_course(
        self,
        mock_get_page,
        mock_get_service,
        mock_render_quiz,
        mock_st,
    ):
        """Test quiz page renders with course from session."""
        from sensei.app import render_current_page
        
        mock_get_page.return_value = "quiz"
        mock_st.session_state = {
            "quiz": {"course_id": "course-123", "module_idx": 2},
            "courses": {},
        }
        
        mock_services = {
            "user": MagicMock(),
            "course": MagicMock(),
            "progress": MagicMock(),
            "learning": MagicMock(),
            "quiz": MagicMock(),
        }
        mock_get_service.side_effect = lambda name: mock_services[name]
        
        render_current_page()
        
        mock_render_quiz.assert_called_once()
        call_kwargs = mock_render_quiz.call_args[1]
        assert call_kwargs["course_id"] == "course-123"
        assert call_kwargs["module_idx"] == 2
    
    @patch("sensei.app.st")
    @patch("sensei.app.render_quiz_with_services")
    @patch("sensei.app.get_service")
    @patch("sensei.app.get_current_page")
    def test_render_quiz_page_without_course_shows_warning(
        self,
        mock_get_page,
        mock_get_service,
        mock_render_quiz,
        mock_st,
    ):
        """Test quiz page shows warning when no course selected."""
        from sensei.app import render_current_page
        
        mock_get_page.return_value = "quiz"
        mock_st.session_state = {"quiz": {}, "courses": {}}
        mock_st.button.return_value = False
        
        mock_services = {
            "user": MagicMock(),
            "course": MagicMock(),
            "progress": MagicMock(),
            "learning": MagicMock(),
            "quiz": MagicMock(),
        }
        mock_get_service.side_effect = lambda name: mock_services[name]
        
        render_current_page()
        
        mock_st.warning.assert_called_once()
        mock_render_quiz.assert_not_called()
    
    @patch("sensei.app.st")
    @patch("sensei.app.render_quiz_with_services")
    @patch("sensei.app.get_service")
    @patch("sensei.app.get_current_page")
    def test_render_quiz_page_falls_back_to_courses_state(
        self,
        mock_get_page,
        mock_get_service,
        mock_render_quiz,
        mock_st,
    ):
        """Test quiz page falls back to current_course_id if quiz course_id not set."""
        from sensei.app import render_current_page
        
        mock_get_page.return_value = "quiz"
        mock_st.session_state = {
            "quiz": {},  # No course_id in quiz state
            "courses": {"current_course_id": "fallback-course"},
        }
        
        mock_services = {
            "user": MagicMock(),
            "course": MagicMock(),
            "progress": MagicMock(),
            "learning": MagicMock(),
            "quiz": MagicMock(),
        }
        mock_get_service.side_effect = lambda name: mock_services[name]
        
        render_current_page()
        
        mock_render_quiz.assert_called_once()
        call_kwargs = mock_render_quiz.call_args[1]
        assert call_kwargs["course_id"] == "fallback-course"
