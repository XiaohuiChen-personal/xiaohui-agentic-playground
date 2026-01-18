"""Unit tests for UserService."""

import pytest
from pathlib import Path

from sensei.models.enums import ExperienceLevel, LearningStyle
from sensei.models.schemas import UserPreferences
from sensei.services.user_service import UserService


class TestUserServiceGetPreferences:
    """Tests for UserService.get_preferences()."""
    
    def test_get_preferences_returns_defaults_when_no_file(
        self, mock_file_storage_paths
    ):
        """Should return default preferences when no file exists."""
        service = UserService()
        prefs = service.get_preferences()
        
        assert isinstance(prefs, UserPreferences)
        assert prefs.name == ""
        assert prefs.learning_style == LearningStyle.READING
        assert prefs.experience_level == ExperienceLevel.BEGINNER
        assert prefs.session_length_minutes == 30
        assert prefs.is_onboarded is False
    
    def test_get_preferences_returns_saved_values(
        self, mock_file_storage_paths
    ):
        """Should return saved preferences when file exists."""
        service = UserService()
        
        # Save some preferences first
        prefs = UserPreferences(
            name="Test User",
            learning_style=LearningStyle.VISUAL,
            experience_level=ExperienceLevel.ADVANCED,
            session_length_minutes=60,
            goals="Learn AI",
            is_onboarded=True,
        )
        service.set_preferences(prefs)
        
        # Get them back
        loaded = service.get_preferences()
        
        assert loaded.name == "Test User"
        assert loaded.learning_style == LearningStyle.VISUAL
        assert loaded.experience_level == ExperienceLevel.ADVANCED
        assert loaded.session_length_minutes == 60
        assert loaded.goals == "Learn AI"
        assert loaded.is_onboarded is True


class TestUserServiceSetPreferences:
    """Tests for UserService.set_preferences()."""
    
    def test_set_preferences_saves_all_fields(
        self, mock_file_storage_paths
    ):
        """Should save all preference fields correctly."""
        service = UserService()
        
        prefs = UserPreferences(
            name="Xiaohui",
            learning_style=LearningStyle.HANDS_ON,
            experience_level=ExperienceLevel.INTERMEDIATE,
            session_length_minutes=45,
            goals="Master CrewAI",
            is_onboarded=True,
        )
        service.set_preferences(prefs)
        
        # Verify by loading directly from file
        from sensei.storage.file_storage import load_user_preferences
        saved = load_user_preferences()
        
        assert saved["name"] == "Xiaohui"
        assert saved["learning_style"] == "hands_on"
        assert saved["experience_level"] == "intermediate"
        assert saved["session_length_minutes"] == 45
        assert saved["goals"] == "Master CrewAI"
        assert saved["is_onboarded"] is True
    
    def test_set_preferences_overwrites_existing(
        self, mock_file_storage_paths
    ):
        """Should overwrite existing preferences."""
        service = UserService()
        
        # Set initial preferences
        prefs1 = UserPreferences(name="User1", goals="Goal1")
        service.set_preferences(prefs1)
        
        # Overwrite with new preferences
        prefs2 = UserPreferences(name="User2", goals="Goal2")
        service.set_preferences(prefs2)
        
        # Verify overwrite
        loaded = service.get_preferences()
        assert loaded.name == "User2"
        assert loaded.goals == "Goal2"


class TestUserServiceIsOnboarded:
    """Tests for UserService.is_onboarded()."""
    
    def test_is_onboarded_returns_false_when_no_file(
        self, mock_file_storage_paths
    ):
        """Should return False when no preferences file exists."""
        service = UserService()
        assert service.is_onboarded() is False
    
    def test_is_onboarded_returns_false_when_not_onboarded(
        self, mock_file_storage_paths
    ):
        """Should return False when is_onboarded flag is False."""
        service = UserService()
        
        prefs = UserPreferences(name="Test", is_onboarded=False)
        service.set_preferences(prefs)
        
        assert service.is_onboarded() is False
    
    def test_is_onboarded_returns_true_when_onboarded(
        self, mock_file_storage_paths
    ):
        """Should return True when is_onboarded flag is True."""
        service = UserService()
        
        prefs = UserPreferences(name="Test", is_onboarded=True)
        service.set_preferences(prefs)
        
        assert service.is_onboarded() is True


class TestUserServiceCompleteOnboarding:
    """Tests for UserService.complete_onboarding()."""
    
    def test_complete_onboarding_sets_onboarded_flag(
        self, mock_file_storage_paths
    ):
        """Should set is_onboarded to True."""
        service = UserService()
        
        prefs = UserPreferences(
            name="New User",
            learning_style=LearningStyle.READING,
            is_onboarded=False,  # Explicitly False
        )
        service.complete_onboarding(prefs)
        
        assert service.is_onboarded() is True
    
    def test_complete_onboarding_saves_all_preferences(
        self, mock_file_storage_paths
    ):
        """Should save all preferences during onboarding."""
        service = UserService()
        
        prefs = UserPreferences(
            name="New Learner",
            learning_style=LearningStyle.VISUAL,
            experience_level=ExperienceLevel.BEGINNER,
            session_length_minutes=20,
            goals="Learn Python",
        )
        service.complete_onboarding(prefs)
        
        loaded = service.get_preferences()
        assert loaded.name == "New Learner"
        assert loaded.learning_style == LearningStyle.VISUAL
        assert loaded.experience_level == ExperienceLevel.BEGINNER
        assert loaded.session_length_minutes == 20
        assert loaded.goals == "Learn Python"
        assert loaded.is_onboarded is True


class TestUserServiceUpdatePreference:
    """Tests for UserService.update_preference()."""
    
    def test_update_preference_updates_single_field(
        self, mock_file_storage_paths
    ):
        """Should update only the specified field."""
        service = UserService()
        
        # Set initial preferences
        prefs = UserPreferences(name="Original", goals="Original Goal")
        service.set_preferences(prefs)
        
        # Update single field
        updated = service.update_preference("name", "Updated")
        
        assert updated.name == "Updated"
        assert updated.goals == "Original Goal"  # Unchanged
    
    def test_update_preference_returns_updated_preferences(
        self, mock_file_storage_paths
    ):
        """Should return the updated UserPreferences object."""
        service = UserService()
        
        prefs = UserPreferences(session_length_minutes=30)
        service.set_preferences(prefs)
        
        updated = service.update_preference("session_length_minutes", 60)
        
        assert isinstance(updated, UserPreferences)
        assert updated.session_length_minutes == 60
    
    def test_update_preference_raises_for_invalid_key(
        self, mock_file_storage_paths
    ):
        """Should raise ValueError for invalid preference key."""
        service = UserService()
        
        with pytest.raises(ValueError, match="Invalid preference key"):
            service.update_preference("invalid_key", "value")
    
    def test_update_preference_valid_keys(
        self, mock_file_storage_paths
    ):
        """Should accept all valid preference keys."""
        service = UserService()
        prefs = UserPreferences()
        service.set_preferences(prefs)
        
        valid_updates = [
            ("name", "Test"),
            ("learning_style", "visual"),
            ("session_length_minutes", 45),
            ("experience_level", "advanced"),
            ("goals", "New Goal"),
            ("is_onboarded", True),
        ]
        
        for key, value in valid_updates:
            # Should not raise
            service.update_preference(key, value)


class TestUserServiceResetPreferences:
    """Tests for UserService.reset_preferences()."""
    
    def test_reset_preferences_returns_defaults(
        self, mock_file_storage_paths
    ):
        """Should return default preferences after reset."""
        service = UserService()
        
        # Set custom preferences
        prefs = UserPreferences(
            name="Custom User",
            learning_style=LearningStyle.VISUAL,
            is_onboarded=True,
        )
        service.set_preferences(prefs)
        
        # Reset
        defaults = service.reset_preferences()
        
        assert defaults.name == ""
        assert defaults.learning_style == LearningStyle.READING
        assert defaults.is_onboarded is False
    
    def test_reset_preferences_clears_onboarded_flag(
        self, mock_file_storage_paths
    ):
        """Should reset is_onboarded to False."""
        service = UserService()
        
        # Complete onboarding
        prefs = UserPreferences(name="User", is_onboarded=True)
        service.set_preferences(prefs)
        assert service.is_onboarded() is True
        
        # Reset
        service.reset_preferences()
        
        assert service.is_onboarded() is False
    
    def test_reset_preferences_persists_defaults(
        self, mock_file_storage_paths
    ):
        """Should persist default values to storage."""
        service = UserService()
        
        # Set and reset
        prefs = UserPreferences(name="User")
        service.set_preferences(prefs)
        service.reset_preferences()
        
        # Create new service instance and verify
        new_service = UserService()
        loaded = new_service.get_preferences()
        
        assert loaded.name == ""
        assert loaded.is_onboarded is False
