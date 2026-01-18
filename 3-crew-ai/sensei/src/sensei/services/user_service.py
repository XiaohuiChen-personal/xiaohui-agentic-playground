"""User service for managing user preferences and onboarding.

This service provides a clean interface for managing user preferences,
wrapping the file storage operations with proper type conversions.
"""

from sensei.models.schemas import UserPreferences
from sensei.storage.file_storage import (
    load_user_preferences,
    save_user_preferences,
    update_user_preferences,
    user_preferences_exist,
)


class UserService:
    """Service for managing user preferences and onboarding.
    
    This service handles:
    - Loading and saving user preferences
    - Tracking onboarding status
    - Converting between dict and Pydantic models
    
    Example:
        ```python
        service = UserService()
        
        # Check if user needs onboarding
        if not service.is_onboarded():
            prefs = UserPreferences(
                name="Xiaohui",
                learning_style=LearningStyle.HANDS_ON,
                experience_level=ExperienceLevel.INTERMEDIATE,
            )
            service.complete_onboarding(prefs)
        
        # Get current preferences
        prefs = service.get_preferences()
        print(f"Hello, {prefs.name}!")
        ```
    """
    
    def get_preferences(self) -> UserPreferences:
        """Get current user preferences.
        
        Returns:
            UserPreferences object with current settings.
            Returns defaults if no preferences have been saved.
        """
        prefs_dict = load_user_preferences()
        return UserPreferences.from_dict(prefs_dict)
    
    def set_preferences(self, preferences: UserPreferences) -> None:
        """Update user preferences.
        
        Args:
            preferences: UserPreferences object with new settings.
        """
        prefs_dict = preferences.model_dump()
        save_user_preferences(prefs_dict)
    
    def is_onboarded(self) -> bool:
        """Check if user has completed onboarding.
        
        Returns:
            True if user has completed onboarding, False otherwise.
        """
        # First check if preferences file exists
        if not user_preferences_exist():
            return False
        
        prefs_dict = load_user_preferences()
        return prefs_dict.get("is_onboarded", False)
    
    def complete_onboarding(self, preferences: UserPreferences) -> None:
        """Complete onboarding and save initial preferences.
        
        Sets the is_onboarded flag to True and saves all preferences.
        
        Args:
            preferences: UserPreferences object with initial settings.
        """
        # Ensure onboarded flag is set
        preferences.is_onboarded = True
        self.set_preferences(preferences)
    
    def update_preference(self, key: str, value) -> UserPreferences:
        """Update a single preference field.
        
        Convenience method for updating individual settings.
        
        Args:
            key: The preference field name to update.
            value: The new value for the field.
        
        Returns:
            Updated UserPreferences object.
        
        Raises:
            ValueError: If key is not a valid preference field.
        """
        valid_keys = {"name", "learning_style", "session_length_minutes", 
                      "experience_level", "goals", "is_onboarded"}
        if key not in valid_keys:
            raise ValueError(f"Invalid preference key: {key}. Valid keys: {valid_keys}")
        
        updated = update_user_preferences({key: value})
        return UserPreferences.from_dict(updated)
    
    def reset_preferences(self) -> UserPreferences:
        """Reset preferences to defaults.
        
        Note: This also resets the onboarded flag to False.
        
        Returns:
            The default UserPreferences object.
        """
        from sensei.storage.file_storage import get_default_preferences
        
        defaults = get_default_preferences()
        save_user_preferences(defaults)
        return UserPreferences.from_dict(defaults)
