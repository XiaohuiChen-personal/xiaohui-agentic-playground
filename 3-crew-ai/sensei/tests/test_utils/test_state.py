"""Unit tests for session state utilities.

These tests mock Streamlit's session_state to test the state management
functions without running Streamlit.
"""

from unittest.mock import MagicMock, patch

import pytest


# ==================== FIXTURES ====================


@pytest.fixture
def mock_session_state():
    """Create a mock session_state that behaves like a dict with attribute access."""
    class MockSessionState(dict):
        """A dict that also supports attribute access like Streamlit's session_state."""
        def __getattr__(self, key):
            try:
                return self[key]
            except KeyError:
                raise AttributeError(f"'MockSessionState' has no attribute '{key}'")
        
        def __setattr__(self, key, value):
            self[key] = value
        
        def __delattr__(self, key):
            try:
                del self[key]
            except KeyError:
                raise AttributeError(f"'MockSessionState' has no attribute '{key}'")
    
    return MockSessionState()


# ==================== TEST: INITIALIZE SESSION STATE ====================


class TestInitializeSessionState:
    """Tests for initialize_session_state()."""
    
    def test_initializes_all_default_keys(self, mock_session_state):
        """Should initialize all expected default keys."""
        with patch('sensei.utils.state.st') as mock_st:
            mock_st.session_state = mock_session_state
            
            from sensei.utils.state import initialize_session_state
            initialize_session_state()
            
            # Check all expected keys exist
            assert "services" in mock_session_state
            assert "user" in mock_session_state
            assert "courses" in mock_session_state
            assert "learning" in mock_session_state
            assert "quiz" in mock_session_state
            assert "ui" in mock_session_state
    
    def test_initializes_nested_user_state(self, mock_session_state):
        """Should initialize nested user state with defaults."""
        with patch('sensei.utils.state.st') as mock_st:
            mock_st.session_state = mock_session_state
            
            from sensei.utils.state import initialize_session_state
            initialize_session_state()
            
            assert mock_session_state["user"]["preferences"] is None
            assert mock_session_state["user"]["is_onboarded"] is False
    
    def test_initializes_nested_courses_state(self, mock_session_state):
        """Should initialize nested courses state with defaults."""
        with patch('sensei.utils.state.st') as mock_st:
            mock_st.session_state = mock_session_state
            
            from sensei.utils.state import initialize_session_state
            initialize_session_state()
            
            assert mock_session_state["courses"]["list"] == []
            assert mock_session_state["courses"]["current_course_id"] is None
    
    def test_initializes_nested_learning_state(self, mock_session_state):
        """Should initialize nested learning state with defaults."""
        with patch('sensei.utils.state.st') as mock_st:
            mock_st.session_state = mock_session_state
            
            from sensei.utils.state import initialize_session_state
            initialize_session_state()
            
            assert mock_session_state["learning"]["session"] is None
            assert mock_session_state["learning"]["current_concept"] is None
            assert mock_session_state["learning"]["chat_history"] == []
            assert mock_session_state["learning"]["module_complete"] is False
    
    def test_initializes_nested_quiz_state(self, mock_session_state):
        """Should initialize nested quiz state with defaults."""
        with patch('sensei.utils.state.st') as mock_st:
            mock_st.session_state = mock_session_state
            
            from sensei.utils.state import initialize_session_state
            initialize_session_state()
            
            assert mock_session_state["quiz"]["current_quiz"] is None
            assert mock_session_state["quiz"]["current_question_idx"] == 0
            assert mock_session_state["quiz"]["answers"] == {}
            assert mock_session_state["quiz"]["results"] is None
    
    def test_initializes_nested_ui_state(self, mock_session_state):
        """Should initialize nested UI state with defaults."""
        with patch('sensei.utils.state.st') as mock_st:
            mock_st.session_state = mock_session_state
            
            from sensei.utils.state import initialize_session_state
            initialize_session_state()
            
            assert mock_session_state["ui"]["current_page"] == "dashboard"
            assert mock_session_state["ui"]["sidebar_expanded"] is True
            assert mock_session_state["ui"]["show_course_outline"] is False
    
    def test_does_not_overwrite_existing_keys(self, mock_session_state):
        """Should not overwrite keys that already exist."""
        with patch('sensei.utils.state.st') as mock_st:
            mock_session_state["user"] = {"preferences": "custom", "is_onboarded": True}
            mock_st.session_state = mock_session_state
            
            from sensei.utils.state import initialize_session_state
            initialize_session_state()
            
            # Should preserve existing values
            assert mock_session_state["user"]["preferences"] == "custom"
            assert mock_session_state["user"]["is_onboarded"] is True


# ==================== TEST: GET STATE ====================


class TestGetState:
    """Tests for get_state()."""
    
    def test_get_top_level_key(self, mock_session_state):
        """Should get a top-level key."""
        with patch('sensei.utils.state.st') as mock_st:
            mock_session_state["my_key"] = "my_value"
            mock_st.session_state = mock_session_state
            
            from sensei.utils.state import get_state
            result = get_state("my_key")
            
            assert result == "my_value"
    
    def test_get_nested_key_with_dot_notation(self, mock_session_state):
        """Should get a nested key using dot notation."""
        with patch('sensei.utils.state.st') as mock_st:
            mock_session_state["user"] = {"preferences": {"theme": "dark"}}
            mock_st.session_state = mock_session_state
            
            from sensei.utils.state import get_state
            result = get_state("user.preferences.theme")
            
            assert result == "dark"
    
    def test_get_missing_key_returns_default(self, mock_session_state):
        """Should return default for missing key."""
        with patch('sensei.utils.state.st') as mock_st:
            mock_st.session_state = mock_session_state
            
            from sensei.utils.state import get_state
            result = get_state("missing_key", "default_value")
            
            assert result == "default_value"
    
    def test_get_missing_key_returns_none_by_default(self, mock_session_state):
        """Should return None for missing key when no default specified."""
        with patch('sensei.utils.state.st') as mock_st:
            mock_st.session_state = mock_session_state
            
            from sensei.utils.state import get_state
            result = get_state("missing_key")
            
            assert result is None
    
    def test_get_nested_missing_key_returns_default(self, mock_session_state):
        """Should return default for missing nested key."""
        with patch('sensei.utils.state.st') as mock_st:
            mock_session_state["user"] = {}
            mock_st.session_state = mock_session_state
            
            from sensei.utils.state import get_state
            result = get_state("user.missing.deep", "fallback")
            
            assert result == "fallback"
    
    def test_get_value_that_is_none(self, mock_session_state):
        """Should return default when value is None."""
        with patch('sensei.utils.state.st') as mock_st:
            mock_session_state["key"] = None
            mock_st.session_state = mock_session_state
            
            from sensei.utils.state import get_state
            result = get_state("key", "default")
            
            assert result == "default"
    
    def test_get_from_object_with_attribute(self, mock_session_state):
        """Should get attribute from object."""
        with patch('sensei.utils.state.st') as mock_st:
            obj = MagicMock()
            obj.nested_attr = "attr_value"
            mock_session_state["obj"] = obj
            mock_st.session_state = mock_session_state
            
            from sensei.utils.state import get_state
            result = get_state("obj.nested_attr")
            
            assert result == "attr_value"


# ==================== TEST: SET STATE ====================


class TestSetState:
    """Tests for set_state()."""
    
    def test_set_top_level_key(self, mock_session_state):
        """Should set a top-level key."""
        with patch('sensei.utils.state.st') as mock_st:
            mock_st.session_state = mock_session_state
            
            from sensei.utils.state import set_state
            set_state("new_key", "new_value")
            
            assert mock_session_state["new_key"] == "new_value"
    
    def test_set_nested_key_with_dot_notation(self, mock_session_state):
        """Should set a nested key using dot notation."""
        with patch('sensei.utils.state.st') as mock_st:
            mock_session_state["user"] = {"preferences": {}}
            mock_st.session_state = mock_session_state
            
            from sensei.utils.state import set_state
            set_state("user.preferences.theme", "dark")
            
            assert mock_session_state["user"]["preferences"]["theme"] == "dark"
    
    def test_set_creates_intermediate_dicts(self, mock_session_state):
        """Should create intermediate dicts if they don't exist."""
        with patch('sensei.utils.state.st') as mock_st:
            mock_st.session_state = mock_session_state
            
            from sensei.utils.state import set_state
            set_state("deep.nested.path", "value")
            
            assert mock_session_state["deep"]["nested"]["path"] == "value"
    
    def test_set_overwrites_existing_value(self, mock_session_state):
        """Should overwrite existing values."""
        with patch('sensei.utils.state.st') as mock_st:
            mock_session_state["key"] = "old_value"
            mock_st.session_state = mock_session_state
            
            from sensei.utils.state import set_state
            set_state("key", "new_value")
            
            assert mock_session_state["key"] == "new_value"
    
    def test_set_complex_value(self, mock_session_state):
        """Should set complex values like dicts and lists."""
        with patch('sensei.utils.state.st') as mock_st:
            mock_st.session_state = mock_session_state
            
            from sensei.utils.state import set_state
            set_state("complex", {"a": [1, 2, 3], "b": {"nested": True}})
            
            assert mock_session_state["complex"]["a"] == [1, 2, 3]
            assert mock_session_state["complex"]["b"]["nested"] is True
    
    def test_set_on_object_attribute(self, mock_session_state):
        """Should set attribute on object."""
        with patch('sensei.utils.state.st') as mock_st:
            obj = MagicMock()
            mock_session_state["obj"] = obj
            mock_st.session_state = mock_session_state
            
            from sensei.utils.state import set_state
            set_state("obj.new_attr", "value")
            
            assert obj.new_attr == "value"


# ==================== TEST: CLEAR STATE ====================


class TestClearState:
    """Tests for clear_state()."""
    
    def test_clear_top_level_key(self, mock_session_state):
        """Should remove a top-level key."""
        with patch('sensei.utils.state.st') as mock_st:
            mock_session_state["key_to_remove"] = "value"
            mock_st.session_state = mock_session_state
            
            from sensei.utils.state import clear_state
            clear_state("key_to_remove")
            
            assert "key_to_remove" not in mock_session_state
    
    def test_clear_nested_key_with_dot_notation(self, mock_session_state):
        """Should remove a nested key using dot notation."""
        with patch('sensei.utils.state.st') as mock_st:
            mock_session_state["user"] = {"preferences": {"theme": "dark", "lang": "en"}}
            mock_st.session_state = mock_session_state
            
            from sensei.utils.state import clear_state
            clear_state("user.preferences.theme")
            
            assert "theme" not in mock_session_state["user"]["preferences"]
            assert mock_session_state["user"]["preferences"]["lang"] == "en"
    
    def test_clear_missing_key_does_nothing(self, mock_session_state):
        """Should silently do nothing for missing key."""
        with patch('sensei.utils.state.st') as mock_st:
            mock_st.session_state = mock_session_state
            
            from sensei.utils.state import clear_state
            # Should not raise
            clear_state("nonexistent_key")
    
    def test_clear_missing_nested_key_does_nothing(self, mock_session_state):
        """Should silently do nothing for missing nested key."""
        with patch('sensei.utils.state.st') as mock_st:
            mock_session_state["user"] = {}
            mock_st.session_state = mock_session_state
            
            from sensei.utils.state import clear_state
            # Should not raise
            clear_state("user.nonexistent.deep")
    
    def test_clear_attribute_from_object(self, mock_session_state):
        """Should delete attribute from object."""
        with patch('sensei.utils.state.st') as mock_st:
            class SimpleObj:
                def __init__(self):
                    self.to_delete = "value"
            
            obj = SimpleObj()
            mock_session_state["obj"] = obj
            mock_st.session_state = mock_session_state
            
            from sensei.utils.state import clear_state
            clear_state("obj.to_delete")
            
            assert not hasattr(obj, "to_delete")
    
    def test_clear_with_none_in_path(self, mock_session_state):
        """Should handle None in path gracefully."""
        with patch('sensei.utils.state.st') as mock_st:
            mock_session_state["parent"] = None
            mock_st.session_state = mock_session_state
            
            from sensei.utils.state import clear_state
            # Should not raise
            clear_state("parent.child.deep")


# ==================== TEST: EDGE CASES ====================


class TestStateEdgeCases:
    """Edge case tests for state utilities."""
    
    def test_empty_key(self, mock_session_state):
        """Should handle empty key."""
        with patch('sensei.utils.state.st') as mock_st:
            mock_st.session_state = mock_session_state
            
            from sensei.utils.state import get_state, set_state
            
            set_state("", "value")
            result = get_state("")
            
            assert result == "value"
    
    def test_deeply_nested_key(self, mock_session_state):
        """Should handle deeply nested keys."""
        with patch('sensei.utils.state.st') as mock_st:
            mock_st.session_state = mock_session_state
            
            from sensei.utils.state import set_state, get_state
            
            # Create a deeply nested structure
            set_state("a.b.c.d.e", "deep_value")
            
            # The value should be accessible
            assert mock_session_state["a"]["b"]["c"]["d"]["e"] == "deep_value"
            assert get_state("a.b.c.d.e") == "deep_value"
    
    def test_multiple_operations_on_same_key(self, mock_session_state):
        """Should handle multiple operations on the same key."""
        with patch('sensei.utils.state.st') as mock_st:
            mock_st.session_state = mock_session_state
            
            from sensei.utils.state import set_state, get_state, clear_state
            
            # Set
            set_state("key", "value1")
            assert get_state("key") == "value1"
            
            # Update
            set_state("key", "value2")
            assert get_state("key") == "value2"
            
            # Clear
            clear_state("key")
            assert get_state("key") is None
    
    def test_numeric_string_key(self, mock_session_state):
        """Should handle numeric string keys."""
        with patch('sensei.utils.state.st') as mock_st:
            mock_st.session_state = mock_session_state
            
            from sensei.utils.state import set_state, get_state
            
            set_state("items.0", "first")
            assert get_state("items.0") == "first"
    
    def test_special_characters_in_key(self, mock_session_state):
        """Should handle special characters in keys."""
        with patch('sensei.utils.state.st') as mock_st:
            mock_st.session_state = mock_session_state
            
            from sensei.utils.state import set_state, get_state
            
            set_state("key_with_underscore", "value")
            assert get_state("key_with_underscore") == "value"
            
            set_state("key-with-dash", "value2")
            assert get_state("key-with-dash") == "value2"
