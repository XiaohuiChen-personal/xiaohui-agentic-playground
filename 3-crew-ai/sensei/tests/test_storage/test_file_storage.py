"""Unit tests for sensei.storage.file_storage module.

Tests cover 100% of file storage operations including:
- Course CRUD operations
- User preferences management
- Chat history management
- Course structure navigation
"""

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from sensei.storage import file_storage as fs


class TestEnsureDataDirectories:
    """Tests for ensure_data_directories function."""
    
    def test_creates_data_and_courses_dirs(self, mock_file_storage_paths):
        """ensure_data_directories should create data and courses directories."""
        # Clear directories to test creation
        paths = mock_file_storage_paths
        if paths["courses_dir"].exists():
            paths["courses_dir"].rmdir()
        if paths["data_dir"].exists():
            paths["data_dir"].rmdir()
        
        fs.ensure_data_directories()
        
        assert paths["data_dir"].exists()
        assert paths["courses_dir"].exists()
    
    def test_handles_existing_directories(self, mock_file_storage_paths):
        """ensure_data_directories should handle already existing directories."""
        paths = mock_file_storage_paths
        
        # Directories already exist from fixture
        assert paths["data_dir"].exists()
        assert paths["courses_dir"].exists()
        
        # Should not raise
        fs.ensure_data_directories()
        
        assert paths["data_dir"].exists()
        assert paths["courses_dir"].exists()


class TestSerializeDatetime:
    """Tests for _serialize_datetime helper function."""
    
    def test_serializes_datetime(self):
        """_serialize_datetime should convert datetime to ISO string."""
        dt = datetime(2026, 1, 10, 14, 30, 0)
        result = fs._serialize_datetime(dt)
        assert result == "2026-01-10T14:30:00"
    
    def test_raises_for_non_datetime(self):
        """_serialize_datetime should raise TypeError for non-datetime."""
        with pytest.raises(TypeError, match="not JSON serializable"):
            fs._serialize_datetime("not a datetime")
        
        with pytest.raises(TypeError):
            fs._serialize_datetime(123)


class TestCourseStorage:
    """Tests for course storage operations."""
    
    def test_save_course_creates_file(
        self, mock_file_storage_paths, mock_course_data
    ):
        """save_course should create a JSON file for the course."""
        fs.save_course(mock_course_data)
        
        course_path = mock_file_storage_paths["courses_dir"] / f"{mock_course_data['id']}.json"
        assert course_path.exists()
        
        with open(course_path) as f:
            saved = json.load(f)
        
        assert saved["id"] == mock_course_data["id"]
        assert saved["title"] == mock_course_data["title"]
    
    def test_save_course_raises_without_id(self, mock_file_storage_paths):
        """save_course should raise ValueError if course has no id."""
        with pytest.raises(ValueError, match="must have an 'id' key"):
            fs.save_course({"title": "No ID Course"})
    
    def test_save_course_serializes_datetime(self, mock_file_storage_paths):
        """save_course should serialize datetime objects."""
        course = {
            "id": "test-datetime",
            "title": "Test",
            "created_at": datetime(2026, 1, 10, 10, 0, 0),
        }
        
        fs.save_course(course)
        
        loaded = fs.load_course("test-datetime")
        assert loaded["created_at"] == "2026-01-10T10:00:00"
    
    def test_save_course_overwrites_existing(
        self, mock_file_storage_paths, mock_course_data
    ):
        """save_course should overwrite existing course file."""
        fs.save_course(mock_course_data)
        
        # Update and save again
        mock_course_data["title"] = "Updated Title"
        fs.save_course(mock_course_data)
        
        loaded = fs.load_course(mock_course_data["id"])
        assert loaded["title"] == "Updated Title"
    
    def test_load_course_returns_course(
        self, mock_file_storage_paths, mock_course_data
    ):
        """load_course should return the course dictionary."""
        fs.save_course(mock_course_data)
        
        loaded = fs.load_course(mock_course_data["id"])
        
        assert loaded is not None
        assert loaded["id"] == mock_course_data["id"]
        assert loaded["title"] == mock_course_data["title"]
        assert len(loaded["modules"]) == len(mock_course_data["modules"])
    
    def test_load_course_returns_none_for_nonexistent(
        self, mock_file_storage_paths
    ):
        """load_course should return None for non-existent course."""
        result = fs.load_course("nonexistent-course")
        assert result is None
    
    def test_list_courses_returns_course_ids(
        self, mock_file_storage_paths, mock_course_data
    ):
        """list_courses should return list of course IDs."""
        fs.save_course(mock_course_data)
        fs.save_course({"id": "course-2", "title": "Course 2"})
        fs.save_course({"id": "course-3", "title": "Course 3"})
        
        course_ids = fs.list_courses()
        
        assert len(course_ids) == 3
        assert mock_course_data["id"] in course_ids
        assert "course-2" in course_ids
        assert "course-3" in course_ids
    
    def test_list_courses_empty_directory(self, mock_file_storage_paths):
        """list_courses should return empty list when no courses exist."""
        course_ids = fs.list_courses()
        assert course_ids == []
    
    def test_list_courses_with_metadata(
        self, mock_file_storage_paths, mock_course_data
    ):
        """list_courses_with_metadata should return course metadata."""
        fs.save_course(mock_course_data)
        
        courses = fs.list_courses_with_metadata()
        
        assert len(courses) == 1
        course = courses[0]
        assert course["id"] == mock_course_data["id"]
        assert course["title"] == mock_course_data["title"]
        assert course["description"] == mock_course_data["description"]
        assert course["total_modules"] == 2
        assert course["total_concepts"] == 3  # 2 + 1 concepts
    
    def test_list_courses_with_metadata_handles_missing_fields(
        self, mock_file_storage_paths
    ):
        """list_courses_with_metadata should handle courses with missing fields."""
        # Minimal course
        fs.save_course({"id": "minimal-course"})
        
        courses = fs.list_courses_with_metadata()
        
        assert len(courses) == 1
        course = courses[0]
        assert course["id"] == "minimal-course"
        assert course["title"] == "Untitled"
        assert course["description"] == ""
        assert course["total_modules"] == 0
        assert course["total_concepts"] == 0
    
    def test_delete_course_removes_file(
        self, mock_file_storage_paths, mock_course_data
    ):
        """delete_course should remove the course file."""
        fs.save_course(mock_course_data)
        course_path = mock_file_storage_paths["courses_dir"] / f"{mock_course_data['id']}.json"
        assert course_path.exists()
        
        result = fs.delete_course(mock_course_data["id"])
        
        assert result is True
        assert not course_path.exists()
    
    def test_delete_course_returns_false_for_nonexistent(
        self, mock_file_storage_paths
    ):
        """delete_course should return False for non-existent course."""
        result = fs.delete_course("nonexistent")
        assert result is False
    
    def test_course_exists_returns_true_for_existing(
        self, mock_file_storage_paths, mock_course_data
    ):
        """course_exists should return True for existing course."""
        fs.save_course(mock_course_data)
        
        assert fs.course_exists(mock_course_data["id"]) is True
    
    def test_course_exists_returns_false_for_nonexistent(
        self, mock_file_storage_paths
    ):
        """course_exists should return False for non-existent course."""
        assert fs.course_exists("nonexistent") is False


class TestCourseStructureNavigation:
    """Tests for course structure navigation functions."""
    
    def test_get_course_structure_returns_structure(
        self, mock_file_storage_paths, mock_course_data
    ):
        """get_course_structure should return course structure summary."""
        fs.save_course(mock_course_data)
        
        structure = fs.get_course_structure(mock_course_data["id"])
        
        assert structure is not None
        assert structure["id"] == mock_course_data["id"]
        assert structure["title"] == mock_course_data["title"]
        assert structure["total_modules"] == 2
        assert structure["total_concepts"] == 3
        assert len(structure["modules"]) == 2
        
        # Check first module details
        mod1 = structure["modules"][0]
        assert mod1["id"] == "module-1"
        assert mod1["title"] == "Module 1"
        assert mod1["concept_count"] == 2
    
    def test_get_course_structure_returns_none_for_nonexistent(
        self, mock_file_storage_paths
    ):
        """get_course_structure should return None for non-existent course."""
        result = fs.get_course_structure("nonexistent")
        assert result is None
    
    def test_get_module_returns_module(
        self, mock_file_storage_paths, mock_course_data
    ):
        """get_module should return the module at the given index."""
        fs.save_course(mock_course_data)
        
        module = fs.get_module(mock_course_data["id"], 0)
        
        assert module is not None
        assert module["id"] == "module-1"
        assert module["title"] == "Module 1"
        assert len(module["concepts"]) == 2
    
    def test_get_module_second_module(
        self, mock_file_storage_paths, mock_course_data
    ):
        """get_module should return correct module for other indices."""
        fs.save_course(mock_course_data)
        
        module = fs.get_module(mock_course_data["id"], 1)
        
        assert module is not None
        assert module["id"] == "module-2"
    
    def test_get_module_returns_none_for_nonexistent_course(
        self, mock_file_storage_paths
    ):
        """get_module should return None for non-existent course."""
        result = fs.get_module("nonexistent", 0)
        assert result is None
    
    def test_get_module_returns_none_for_invalid_index(
        self, mock_file_storage_paths, mock_course_data
    ):
        """get_module should return None for out-of-range index."""
        fs.save_course(mock_course_data)
        
        assert fs.get_module(mock_course_data["id"], -1) is None
        assert fs.get_module(mock_course_data["id"], 99) is None
    
    def test_get_concept_returns_concept(
        self, mock_file_storage_paths, mock_course_data
    ):
        """get_concept should return the concept at the given indices."""
        fs.save_course(mock_course_data)
        
        concept = fs.get_concept(mock_course_data["id"], 0, 1)
        
        assert concept is not None
        assert concept["id"] == "concept-2"
        assert concept["title"] == "Concept 2"
    
    def test_get_concept_returns_none_for_nonexistent_course(
        self, mock_file_storage_paths
    ):
        """get_concept should return None for non-existent course."""
        result = fs.get_concept("nonexistent", 0, 0)
        assert result is None
    
    def test_get_concept_returns_none_for_invalid_module_index(
        self, mock_file_storage_paths, mock_course_data
    ):
        """get_concept should return None for invalid module index."""
        fs.save_course(mock_course_data)
        
        assert fs.get_concept(mock_course_data["id"], 99, 0) is None
    
    def test_get_concept_returns_none_for_invalid_concept_index(
        self, mock_file_storage_paths, mock_course_data
    ):
        """get_concept should return None for invalid concept index."""
        fs.save_course(mock_course_data)
        
        assert fs.get_concept(mock_course_data["id"], 0, -1) is None
        assert fs.get_concept(mock_course_data["id"], 0, 99) is None
    
    def test_get_concept_with_context_returns_full_context(
        self, mock_file_storage_paths, mock_course_data
    ):
        """get_concept_with_context should return concept with navigation info."""
        fs.save_course(mock_course_data)
        
        result = fs.get_concept_with_context(mock_course_data["id"], 0, 0)
        
        assert result is not None
        assert result["concept"]["id"] == "concept-1"
        assert result["module"]["id"] == "module-1"
        assert result["module"]["idx"] == 0
        assert result["course"]["id"] == mock_course_data["id"]
        
        # Check navigation info
        nav = result["navigation"]
        assert nav["concept_idx"] == 0
        assert nav["total_concepts_in_module"] == 2
        assert nav["module_idx"] == 0
        assert nav["total_modules"] == 2
        assert nav["has_previous"] is False
        assert nav["has_next"] is True
        assert nav["is_module_complete"] is False
        assert nav["is_course_complete"] is False
    
    def test_get_concept_with_context_last_concept_in_module(
        self, mock_file_storage_paths, mock_course_data
    ):
        """get_concept_with_context should detect last concept in module."""
        fs.save_course(mock_course_data)
        
        result = fs.get_concept_with_context(mock_course_data["id"], 0, 1)
        
        nav = result["navigation"]
        assert nav["has_previous"] is True
        assert nav["has_next"] is True  # Still has next module
        assert nav["is_module_complete"] is True
        assert nav["is_course_complete"] is False
    
    def test_get_concept_with_context_last_concept_in_course(
        self, mock_file_storage_paths, mock_course_data
    ):
        """get_concept_with_context should detect last concept in course."""
        fs.save_course(mock_course_data)
        
        # Last module (1), last concept (0 - only one concept)
        result = fs.get_concept_with_context(mock_course_data["id"], 1, 0)
        
        nav = result["navigation"]
        assert nav["has_previous"] is True
        assert nav["has_next"] is False
        assert nav["is_module_complete"] is True
        assert nav["is_course_complete"] is True
    
    def test_get_concept_with_context_returns_none_for_nonexistent_course(
        self, mock_file_storage_paths
    ):
        """get_concept_with_context should return None for non-existent course."""
        result = fs.get_concept_with_context("nonexistent", 0, 0)
        assert result is None
    
    def test_get_concept_with_context_returns_none_for_invalid_module(
        self, mock_file_storage_paths, mock_course_data
    ):
        """get_concept_with_context should return None for invalid module index."""
        fs.save_course(mock_course_data)
        
        result = fs.get_concept_with_context(mock_course_data["id"], 99, 0)
        assert result is None
    
    def test_get_concept_with_context_returns_none_for_invalid_concept(
        self, mock_file_storage_paths, mock_course_data
    ):
        """get_concept_with_context should return None for invalid concept index."""
        fs.save_course(mock_course_data)
        
        result = fs.get_concept_with_context(mock_course_data["id"], 0, 99)
        assert result is None
    
    def test_update_course_updates_fields(
        self, mock_file_storage_paths, mock_course_data
    ):
        """update_course should update specified fields."""
        fs.save_course(mock_course_data)
        
        result = fs.update_course(
            mock_course_data["id"],
            {"title": "Updated Title", "description": "New description"}
        )
        
        assert result is True
        
        loaded = fs.load_course(mock_course_data["id"])
        assert loaded["title"] == "Updated Title"
        assert loaded["description"] == "New description"
        # Original fields should remain
        assert loaded["id"] == mock_course_data["id"]
    
    def test_update_course_returns_false_for_nonexistent(
        self, mock_file_storage_paths
    ):
        """update_course should return False for non-existent course."""
        result = fs.update_course("nonexistent", {"title": "New"})
        assert result is False


class TestCountHelpers:
    """Tests for _count_modules and _count_concepts helper functions."""
    
    def test_count_modules(self, mock_course_data):
        """_count_modules should return correct module count."""
        assert fs._count_modules(mock_course_data) == 2
    
    def test_count_modules_empty(self):
        """_count_modules should return 0 for no modules."""
        assert fs._count_modules({}) == 0
        assert fs._count_modules({"modules": []}) == 0
    
    def test_count_concepts(self, mock_course_data):
        """_count_concepts should return total concept count."""
        assert fs._count_concepts(mock_course_data) == 3  # 2 + 1
    
    def test_count_concepts_empty(self):
        """_count_concepts should return 0 for no concepts."""
        assert fs._count_concepts({}) == 0
        assert fs._count_concepts({"modules": []}) == 0
        assert fs._count_concepts({"modules": [{"concepts": []}]}) == 0


class TestUserPreferencesStorage:
    """Tests for user preferences storage operations."""
    
    def test_save_user_preferences_creates_file(
        self, mock_file_storage_paths, mock_user_preferences
    ):
        """save_user_preferences should create preferences file."""
        fs.save_user_preferences(mock_user_preferences)
        
        prefs_path = mock_file_storage_paths["user_preferences_path"]
        assert prefs_path.exists()
        
        with open(prefs_path) as f:
            saved = json.load(f)
        
        assert saved["name"] == mock_user_preferences["name"]
    
    def test_save_user_preferences_with_datetime(self, mock_file_storage_paths):
        """save_user_preferences should serialize datetime objects."""
        prefs = {
            "name": "Test",
            "updated_at": datetime(2026, 1, 10, 10, 0, 0),
        }
        
        fs.save_user_preferences(prefs)
        
        loaded = fs.load_user_preferences()
        assert loaded["updated_at"] == "2026-01-10T10:00:00"
    
    def test_load_user_preferences_returns_saved(
        self, mock_file_storage_paths, mock_user_preferences
    ):
        """load_user_preferences should return saved preferences."""
        fs.save_user_preferences(mock_user_preferences)
        
        loaded = fs.load_user_preferences()
        
        assert loaded["name"] == mock_user_preferences["name"]
        assert loaded["learning_style"] == mock_user_preferences["learning_style"]
    
    def test_load_user_preferences_returns_defaults_if_not_exists(
        self, mock_file_storage_paths
    ):
        """load_user_preferences should return defaults if file doesn't exist."""
        loaded = fs.load_user_preferences()
        defaults = fs.get_default_preferences()
        
        assert loaded == defaults
    
    def test_load_user_preferences_returns_defaults_on_json_error(
        self, mock_file_storage_paths
    ):
        """load_user_preferences should return defaults on JSON decode error."""
        prefs_path = mock_file_storage_paths["user_preferences_path"]
        with open(prefs_path, "w") as f:
            f.write("invalid json {{{")
        
        loaded = fs.load_user_preferences()
        defaults = fs.get_default_preferences()
        
        assert loaded == defaults
    
    def test_get_default_preferences_returns_expected_structure(self):
        """get_default_preferences should return expected default values."""
        defaults = fs.get_default_preferences()
        
        assert defaults["name"] == ""
        assert defaults["learning_style"] == "reading"
        assert defaults["session_length_minutes"] == 30
        assert defaults["experience_level"] == "beginner"
        assert defaults["goals"] == ""
        assert defaults["is_onboarded"] is False
    
    def test_user_preferences_exist_returns_true_when_exists(
        self, mock_file_storage_paths, mock_user_preferences
    ):
        """user_preferences_exist should return True when file exists."""
        fs.save_user_preferences(mock_user_preferences)
        
        assert fs.user_preferences_exist() is True
    
    def test_user_preferences_exist_returns_false_when_not_exists(
        self, mock_file_storage_paths
    ):
        """user_preferences_exist should return False when file doesn't exist."""
        assert fs.user_preferences_exist() is False
    
    def test_delete_user_preferences_removes_file(
        self, mock_file_storage_paths, mock_user_preferences
    ):
        """delete_user_preferences should remove the file."""
        fs.save_user_preferences(mock_user_preferences)
        assert fs.user_preferences_exist()
        
        result = fs.delete_user_preferences()
        
        assert result is True
        assert not fs.user_preferences_exist()
    
    def test_delete_user_preferences_returns_false_if_not_exists(
        self, mock_file_storage_paths
    ):
        """delete_user_preferences should return False if file doesn't exist."""
        result = fs.delete_user_preferences()
        assert result is False
    
    def test_update_user_preferences_partial_update(
        self, mock_file_storage_paths, mock_user_preferences
    ):
        """update_user_preferences should update only specified fields."""
        fs.save_user_preferences(mock_user_preferences)
        
        result = fs.update_user_preferences({
            "name": "Updated Name",
            "session_length_minutes": 45,
        })
        
        # Updated fields should be changed
        assert result["name"] == "Updated Name"
        assert result["session_length_minutes"] == 45
        # Original fields should remain
        assert result["learning_style"] == mock_user_preferences["learning_style"]
        assert result["experience_level"] == mock_user_preferences["experience_level"]
    
    def test_update_user_preferences_creates_if_not_exists(
        self, mock_file_storage_paths
    ):
        """update_user_preferences should create with defaults if no file exists."""
        result = fs.update_user_preferences({"name": "New User"})
        
        # Should have the update
        assert result["name"] == "New User"
        # Should have defaults for other fields
        assert result["learning_style"] == "reading"
        assert result["is_onboarded"] is False
    
    def test_update_user_preferences_persists_changes(
        self, mock_file_storage_paths, mock_user_preferences
    ):
        """update_user_preferences should persist changes to file."""
        fs.save_user_preferences(mock_user_preferences)
        
        fs.update_user_preferences({"goals": "New learning goal"})
        
        # Verify persistence by loading again
        loaded = fs.load_user_preferences()
        assert loaded["goals"] == "New learning goal"
    
    def test_update_user_preferences_returns_full_preferences(
        self, mock_file_storage_paths
    ):
        """update_user_preferences should return the complete preferences dict."""
        result = fs.update_user_preferences({"is_onboarded": True})
        
        # Should contain all default fields plus update
        assert "name" in result
        assert "learning_style" in result
        assert "session_length_minutes" in result
        assert "experience_level" in result
        assert "goals" in result
        assert result["is_onboarded"] is True


class TestChatHistoryStorage:
    """Tests for chat history storage operations."""
    
    def test_save_chat_history_creates_file(
        self, mock_file_storage_paths, mock_chat_messages
    ):
        """save_chat_history should create chat history file."""
        fs.save_chat_history("course-1", mock_chat_messages)
        
        chat_path = mock_file_storage_paths["chat_history_path"]
        assert chat_path.exists()
    
    def test_save_chat_history_stores_per_course(
        self, mock_file_storage_paths, mock_chat_messages
    ):
        """save_chat_history should store messages per course."""
        fs.save_chat_history("course-1", mock_chat_messages)
        fs.save_chat_history("course-2", [{"role": "user", "content": "Different"}])
        
        history1 = fs.load_chat_history("course-1")
        history2 = fs.load_chat_history("course-2")
        
        assert len(history1) == 4
        assert len(history2) == 1
    
    def test_save_chat_history_with_datetime(self, mock_file_storage_paths):
        """save_chat_history should serialize datetime objects."""
        messages = [
            {"role": "user", "content": "Hello", "timestamp": datetime(2026, 1, 10)}
        ]
        
        fs.save_chat_history("course-1", messages)
        
        loaded = fs.load_chat_history("course-1")
        assert loaded[0]["timestamp"] == "2026-01-10T00:00:00"
    
    def test_save_chat_history_overwrites_for_course(
        self, mock_file_storage_paths, mock_chat_messages
    ):
        """save_chat_history should overwrite messages for the same course."""
        fs.save_chat_history("course-1", mock_chat_messages)
        fs.save_chat_history("course-1", [{"role": "user", "content": "New"}])
        
        history = fs.load_chat_history("course-1")
        
        assert len(history) == 1
        assert history[0]["content"] == "New"
    
    def test_load_chat_history_returns_messages(
        self, mock_file_storage_paths, mock_chat_messages
    ):
        """load_chat_history should return saved messages."""
        fs.save_chat_history("course-1", mock_chat_messages)
        
        history = fs.load_chat_history("course-1")
        
        assert len(history) == 4
        assert history[0]["role"] == "user"
        assert history[0]["content"] == "What is machine learning?"
    
    def test_load_chat_history_returns_empty_for_nonexistent(
        self, mock_file_storage_paths
    ):
        """load_chat_history should return empty list for non-existent course."""
        history = fs.load_chat_history("nonexistent")
        assert history == []
    
    def test_load_all_chat_history_returns_empty_when_no_file(
        self, mock_file_storage_paths
    ):
        """_load_all_chat_history should return empty dict when no file."""
        result = fs._load_all_chat_history()
        assert result == {}
    
    def test_load_all_chat_history_handles_json_error(
        self, mock_file_storage_paths
    ):
        """_load_all_chat_history should return empty dict on JSON error."""
        chat_path = mock_file_storage_paths["chat_history_path"]
        with open(chat_path, "w") as f:
            f.write("invalid json")
        
        result = fs._load_all_chat_history()
        assert result == {}
    
    def test_clear_chat_history_removes_course_history(
        self, mock_file_storage_paths, mock_chat_messages
    ):
        """clear_chat_history should remove history for specific course."""
        fs.save_chat_history("course-1", mock_chat_messages)
        fs.save_chat_history("course-2", [{"role": "user", "content": "Keep"}])
        
        result = fs.clear_chat_history("course-1")
        
        assert result is True
        assert fs.load_chat_history("course-1") == []
        assert len(fs.load_chat_history("course-2")) == 1
    
    def test_clear_chat_history_returns_false_for_nonexistent(
        self, mock_file_storage_paths
    ):
        """clear_chat_history should return False for non-existent course."""
        result = fs.clear_chat_history("nonexistent")
        assert result is False
    
    def test_clear_all_chat_history_removes_file(
        self, mock_file_storage_paths, mock_chat_messages
    ):
        """clear_all_chat_history should remove the entire chat history file."""
        fs.save_chat_history("course-1", mock_chat_messages)
        chat_path = mock_file_storage_paths["chat_history_path"]
        assert chat_path.exists()
        
        fs.clear_all_chat_history()
        
        assert not chat_path.exists()
    
    def test_clear_all_chat_history_handles_no_file(self, mock_file_storage_paths):
        """clear_all_chat_history should handle case when file doesn't exist."""
        # Should not raise
        fs.clear_all_chat_history()
    
    def test_append_chat_message_adds_to_history(
        self, mock_file_storage_paths, mock_chat_messages
    ):
        """append_chat_message should add a single message to history."""
        fs.save_chat_history("course-1", mock_chat_messages)
        
        new_message = {"role": "user", "content": "New question?"}
        count = fs.append_chat_message("course-1", new_message)
        
        assert count == 5  # 4 original + 1 new
        
        history = fs.load_chat_history("course-1")
        assert len(history) == 5
        assert history[-1]["content"] == "New question?"
    
    def test_append_chat_message_creates_history_if_not_exists(
        self, mock_file_storage_paths
    ):
        """append_chat_message should create history if it doesn't exist."""
        message = {"role": "user", "content": "First message"}
        count = fs.append_chat_message("new-course", message)
        
        assert count == 1
        
        history = fs.load_chat_history("new-course")
        assert len(history) == 1
        assert history[0]["content"] == "First message"
    
    def test_append_chat_message_preserves_other_courses(
        self, mock_file_storage_paths, mock_chat_messages
    ):
        """append_chat_message should not affect other courses' history."""
        fs.save_chat_history("course-1", mock_chat_messages)
        fs.save_chat_history("course-2", [{"role": "user", "content": "Other"}])
        
        fs.append_chat_message("course-1", {"role": "user", "content": "New"})
        
        # course-2 should be unchanged
        history2 = fs.load_chat_history("course-2")
        assert len(history2) == 1
        assert history2[0]["content"] == "Other"
    
    def test_append_chat_message_returns_new_count(self, mock_file_storage_paths):
        """append_chat_message should return the new message count."""
        for i in range(3):
            count = fs.append_chat_message(
                "course-1",
                {"role": "user", "content": f"Message {i}"}
            )
            assert count == i + 1
    
    def test_get_chat_history_count_returns_count(
        self, mock_file_storage_paths, mock_chat_messages
    ):
        """get_chat_history_count should return the number of messages."""
        fs.save_chat_history("course-1", mock_chat_messages)
        
        count = fs.get_chat_history_count("course-1")
        
        assert count == 4
    
    def test_get_chat_history_count_returns_zero_for_nonexistent(
        self, mock_file_storage_paths
    ):
        """get_chat_history_count should return 0 for non-existent course."""
        count = fs.get_chat_history_count("nonexistent")
        assert count == 0
    
    def test_get_chat_history_count_returns_zero_for_empty(
        self, mock_file_storage_paths
    ):
        """get_chat_history_count should return 0 for empty history."""
        fs.save_chat_history("course-1", [])
        
        count = fs.get_chat_history_count("course-1")
        assert count == 0
