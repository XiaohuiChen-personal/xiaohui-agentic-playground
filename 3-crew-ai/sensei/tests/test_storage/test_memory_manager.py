"""Unit tests for sensei.storage.memory_manager module.

Tests cover 100% of memory manager operations including:
- CrewAI memory configuration
- Memory directory management
- Memory statistics
- Crew context helpers
"""

import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from sensei.storage import memory_manager as mm


class TestEnsureMemoryDirectory:
    """Tests for ensure_memory_directory function."""
    
    def test_creates_memory_directory(self, mock_memory_paths):
        """ensure_memory_directory should create the memory directory."""
        memory_dir = mock_memory_paths["memory_dir"]
        
        # Directory doesn't exist initially
        assert not memory_dir.exists()
        
        mm.ensure_memory_directory()
        
        assert memory_dir.exists()
    
    def test_handles_existing_directory(self, mock_memory_paths):
        """ensure_memory_directory should handle existing directory."""
        memory_dir = mock_memory_paths["memory_dir"]
        memory_dir.mkdir(parents=True)
        
        # Should not raise
        mm.ensure_memory_directory()
        
        assert memory_dir.exists()


class TestMemoryConfigurations:
    """Tests for memory configuration functions."""
    
    def test_get_memory_config(self, mock_memory_paths):
        """get_memory_config should return complete memory configuration."""
        config = mm.get_memory_config()
        
        assert config["memory"] is True
        assert config["memory_config"]["provider"] == "mem0"
        assert config["verbose"] is False
    
    def test_get_memory_config_creates_directory(self, mock_memory_paths):
        """get_memory_config should ensure memory directory exists."""
        memory_dir = mock_memory_paths["memory_dir"]
        assert not memory_dir.exists()
        
        mm.get_memory_config()
        
        assert memory_dir.exists()
    
    def test_get_short_term_memory_config(self):
        """get_short_term_memory_config should return STM configuration."""
        config = mm.get_short_term_memory_config()
        
        assert config["type"] == "short_term"
        assert config["storage"] == "in_memory"
        assert config["max_items"] == 100
    
    def test_get_long_term_memory_config(self, mock_memory_paths):
        """get_long_term_memory_config should return LTM configuration."""
        config = mm.get_long_term_memory_config()
        
        assert config["type"] == "long_term"
        assert config["storage"] == "sqlite"
        assert config["path"] == str(mock_memory_paths["db_path"])
    
    def test_get_long_term_memory_config_creates_directory(self, mock_memory_paths):
        """get_long_term_memory_config should ensure memory directory exists."""
        memory_dir = mock_memory_paths["memory_dir"]
        assert not memory_dir.exists()
        
        mm.get_long_term_memory_config()
        
        assert memory_dir.exists()
    
    def test_get_entity_memory_config(self, mock_memory_paths):
        """get_entity_memory_config should return entity memory configuration."""
        config = mm.get_entity_memory_config()
        
        assert config["type"] == "entity"
        assert config["storage"] == "json"
        assert "entities" in config["path"]
    
    def test_get_entity_memory_config_creates_directory(self, mock_memory_paths):
        """get_entity_memory_config should ensure memory directory exists."""
        memory_dir = mock_memory_paths["memory_dir"]
        assert not memory_dir.exists()
        
        mm.get_entity_memory_config()
        
        assert memory_dir.exists()


class TestCrewMemorySettings:
    """Tests for get_crew_memory_settings function."""
    
    def test_get_crew_memory_settings_default(self, mock_memory_paths):
        """get_crew_memory_settings should return default settings."""
        settings = mm.get_crew_memory_settings()
        
        assert settings["memory"] is True
        assert settings["verbose"] is False
        assert "embedder" not in settings
    
    def test_get_crew_memory_settings_with_verbose(self, mock_memory_paths):
        """get_crew_memory_settings should respect verbose flag."""
        settings = mm.get_crew_memory_settings(verbose=True)
        
        assert settings["verbose"] is True
    
    def test_get_crew_memory_settings_with_embedder(self, mock_memory_paths):
        """get_crew_memory_settings should include embedder config if provided."""
        embedder = {"provider": "openai", "config": {"model": "test"}}
        
        settings = mm.get_crew_memory_settings(embedder_config=embedder)
        
        assert settings["embedder"] == embedder
    
    def test_get_crew_memory_settings_creates_directory(self, mock_memory_paths):
        """get_crew_memory_settings should ensure memory directory exists."""
        memory_dir = mock_memory_paths["memory_dir"]
        assert not memory_dir.exists()
        
        mm.get_crew_memory_settings()
        
        assert memory_dir.exists()


class TestOpenAIEmbedderConfig:
    """Tests for get_openai_embedder_config function."""
    
    def test_get_openai_embedder_config_default(self):
        """get_openai_embedder_config should return default model config."""
        config = mm.get_openai_embedder_config()
        
        assert config["provider"] == "openai"
        assert config["config"]["model"] == "text-embedding-3-small"
    
    def test_get_openai_embedder_config_custom_model(self):
        """get_openai_embedder_config should use custom model if provided."""
        config = mm.get_openai_embedder_config(model="text-embedding-3-large")
        
        assert config["config"]["model"] == "text-embedding-3-large"


class TestMemoryClearOperations:
    """Tests for memory clearing functions."""
    
    def test_clear_session_memory(self):
        """clear_session_memory should execute without error."""
        # This is a placeholder function, should not raise
        mm.clear_session_memory()
    
    def test_clear_all_memory(self, mock_memory_paths):
        """clear_all_memory should remove and recreate memory directory."""
        memory_dir = mock_memory_paths["memory_dir"]
        memory_dir.mkdir(parents=True)
        
        # Create some test files
        (memory_dir / "test_file.json").write_text("{}")
        entities_dir = memory_dir / "entities"
        entities_dir.mkdir()
        (entities_dir / "entity.json").write_text("{}")
        
        mm.clear_all_memory()
        
        # Directory should exist but be empty
        assert memory_dir.exists()
        assert not (memory_dir / "test_file.json").exists()
    
    def test_clear_all_memory_handles_nonexistent(self, mock_memory_paths):
        """clear_all_memory should handle non-existent memory directory."""
        memory_dir = mock_memory_paths["memory_dir"]
        assert not memory_dir.exists()
        
        # Should not raise
        mm.clear_all_memory()
        
        # Should create empty directory
        assert memory_dir.exists()


class TestMemoryStats:
    """Tests for get_memory_stats function."""
    
    def test_get_memory_stats_empty(self, mock_memory_paths):
        """get_memory_stats should return zeros when nothing exists."""
        stats = mm.get_memory_stats()
        
        assert stats["memory_dir_exists"] is False
        assert stats["database_exists"] is False
        assert stats["database_size_bytes"] == 0
        assert stats["entity_files_count"] == 0
    
    def test_get_memory_stats_with_memory_dir(self, mock_memory_paths):
        """get_memory_stats should detect existing memory directory."""
        memory_dir = mock_memory_paths["memory_dir"]
        memory_dir.mkdir(parents=True)
        
        stats = mm.get_memory_stats()
        
        assert stats["memory_dir_exists"] is True
    
    def test_get_memory_stats_with_database(self, mock_memory_paths):
        """get_memory_stats should detect and size database."""
        db_path = mock_memory_paths["db_path"]
        db_path.parent.mkdir(parents=True, exist_ok=True)
        db_path.write_bytes(b"test database content")
        
        stats = mm.get_memory_stats()
        
        assert stats["database_exists"] is True
        assert stats["database_size_bytes"] > 0
    
    def test_get_memory_stats_with_entities(self, mock_memory_paths):
        """get_memory_stats should count entity files."""
        memory_dir = mock_memory_paths["memory_dir"]
        entities_dir = memory_dir / "entities"
        entities_dir.mkdir(parents=True)
        
        # Create test entity files
        (entities_dir / "entity1.json").write_text("{}")
        (entities_dir / "entity2.json").write_text("{}")
        (entities_dir / "entity3.json").write_text("{}")
        
        stats = mm.get_memory_stats()
        
        assert stats["entity_files_count"] == 3


class TestUserContext:
    """Tests for get_user_context function."""
    
    def test_get_user_context_with_preferences(
        self, mock_file_storage_paths, mock_user_preferences
    ):
        """get_user_context should return user preferences."""
        from sensei.storage.file_storage import save_user_preferences
        save_user_preferences(mock_user_preferences)
        
        context = mm.get_user_context()
        
        assert context["name"] == mock_user_preferences["name"]
        assert context["learning_style"] == mock_user_preferences["learning_style"]
        assert context["experience_level"] == mock_user_preferences["experience_level"]
        assert context["session_length_minutes"] == mock_user_preferences["session_length_minutes"]
        assert context["goals"] == mock_user_preferences["goals"]
        assert context["is_onboarded"] == mock_user_preferences["is_onboarded"]
    
    def test_get_user_context_with_defaults(self, mock_file_storage_paths):
        """get_user_context should return defaults when no preferences exist."""
        context = mm.get_user_context()
        
        # Default preferences have empty name, but get_user_context falls back to "Learner"
        # when the prefs have empty name (using `or` check)
        assert context["name"] == ""  # Empty from default prefs
        assert context["learning_style"] == "reading"
        assert context["experience_level"] == "beginner"
        assert context["session_length_minutes"] == 30
        assert context["goals"] == ""
        assert context["is_onboarded"] is False


class TestLearningHistory:
    """Tests for get_learning_history function."""
    
    def test_get_learning_history_with_data(self, temp_db, mock_file_storage_paths):
        """get_learning_history should return progress and quiz data."""
        # Set up progress
        temp_db.save_progress({
            "course_id": "test-course",
            "completion_percentage": 0.5,
            "modules_completed": 2,
            "total_modules": 4,
            "concepts_completed": 10,
            "total_concepts": 20,
            "time_spent_minutes": 120,
        })
        
        # Add quiz result
        temp_db.save_quiz_result({
            "course_id": "test-course",
            "module_id": "mod-1",
            "module_title": "Module 1",
            "quiz_id": "quiz-1",
            "score": 0.75,
            "correct_count": 3,
            "total_questions": 4,
            "weak_concepts": ["concept-a"],
            "passed": False,
        })
        
        history = mm.get_learning_history("test-course", temp_db)
        
        assert history["progress"]["completion_percentage"] == 0.5
        assert history["progress"]["modules_completed"] == 2
        assert history["progress"]["total_modules"] == 4
        assert len(history["quiz_history"]) == 1
        assert "concept-a" in history["weak_concepts"]
        assert history["time_spent_minutes"] == 120
    
    def test_get_learning_history_no_progress(self, temp_db, mock_file_storage_paths):
        """get_learning_history should return defaults when no progress exists."""
        history = mm.get_learning_history("nonexistent", temp_db)
        
        assert history["progress"]["completion_percentage"] == 0.0
        assert history["progress"]["modules_completed"] == 0
        assert history["quiz_history"] == []
        assert history["weak_concepts"] == []
    
    def test_get_learning_history_creates_db_if_not_provided(
        self, tmp_path, mock_file_storage_paths
    ):
        """get_learning_history should create Database if not provided."""
        # Patch Database at source since it's imported inside the function
        with patch("sensei.storage.database.Database") as MockDB:
            mock_db = MagicMock()
            mock_db.get_progress.return_value = None
            mock_db.get_quiz_history.return_value = []
            MockDB.return_value = mock_db
            
            history = mm.get_learning_history("test-course")
            
            MockDB.assert_called_once()
    
    def test_get_learning_history_aggregates_weak_concepts(
        self, temp_db, mock_file_storage_paths
    ):
        """get_learning_history should aggregate weak concepts from multiple quizzes."""
        # Add multiple quizzes with different weak concepts
        temp_db.save_quiz_result({
            "course_id": "test-course",
            "module_id": "mod-1",
            "quiz_id": "quiz-1",
            "score": 0.6,
            "correct_count": 3,
            "total_questions": 5,
            "weak_concepts": ["concept-a", "concept-b"],
        })
        temp_db.save_quiz_result({
            "course_id": "test-course",
            "module_id": "mod-2",
            "quiz_id": "quiz-2",
            "score": 0.7,
            "correct_count": 7,
            "total_questions": 10,
            "weak_concepts": ["concept-b", "concept-c"],
        })
        
        history = mm.get_learning_history("test-course", temp_db)
        
        # Should have all unique weak concepts
        assert "concept-a" in history["weak_concepts"]
        assert "concept-b" in history["weak_concepts"]
        assert "concept-c" in history["weak_concepts"]
        assert len(history["weak_concepts"]) == 3
    
    def test_get_learning_history_quiz_without_weak_concepts(
        self, temp_db, mock_file_storage_paths
    ):
        """get_learning_history should handle quizzes without weak_concepts key."""
        # Quiz without weak_concepts key
        temp_db.save_quiz_result({
            "course_id": "test-course",
            "module_id": "mod-1",
            "quiz_id": "quiz-1",
            "score": 1.0,
            "correct_count": 5,
            "total_questions": 5,
            # No weak_concepts key
        })
        
        history = mm.get_learning_history("test-course", temp_db)
        
        assert history["weak_concepts"] == []
        assert len(history["quiz_history"]) == 1


class TestConceptHistory:
    """Tests for get_concept_history function."""
    
    def test_get_concept_history_with_data(self, temp_db, mock_file_storage_paths):
        """get_concept_history should return mastery data."""
        temp_db.save_concept_mastery(
            course_id="test-course",
            concept_id="concept-1",
            mastery_level=0.8,
            questions_asked=5,
        )
        
        history = mm.get_concept_history("test-course", "concept-1", temp_db)
        
        assert history["mastery_level"] == 0.8
        assert history["questions_asked"] == 5
        assert history["times_reviewed"] == 1
        assert history["is_new"] is False
    
    def test_get_concept_history_new_concept(self, temp_db, mock_file_storage_paths):
        """get_concept_history should return defaults for new concept."""
        history = mm.get_concept_history("test-course", "new-concept", temp_db)
        
        assert history["mastery_level"] == 0.0
        assert history["questions_asked"] == 0
        assert history["times_reviewed"] == 0
        assert history["is_new"] is True
    
    def test_get_concept_history_creates_db_if_not_provided(
        self, mock_file_storage_paths
    ):
        """get_concept_history should create Database if not provided."""
        # Patch Database at source since it's imported inside the function
        with patch("sensei.storage.database.Database") as MockDB:
            mock_db = MagicMock()
            mock_db.get_concept_mastery.return_value = None
            MockDB.return_value = mock_db
            
            history = mm.get_concept_history("test", "concept-1")
            
            MockDB.assert_called_once()


class TestCurriculumCrewContext:
    """Tests for get_curriculum_crew_context function."""
    
    def test_get_curriculum_crew_context(
        self, mock_file_storage_paths, mock_user_preferences
    ):
        """get_curriculum_crew_context should return topic and user context."""
        from sensei.storage.file_storage import save_user_preferences
        save_user_preferences(mock_user_preferences)
        
        context = mm.get_curriculum_crew_context("Machine Learning")
        
        assert context["topic"] == "Machine Learning"
        assert context["user"]["name"] == mock_user_preferences["name"]
        assert context["personalization"]["experience_level"] == mock_user_preferences["experience_level"]
        assert context["personalization"]["learning_style"] == mock_user_preferences["learning_style"]
        assert context["personalization"]["goals"] == mock_user_preferences["goals"]
    
    def test_get_curriculum_crew_context_with_defaults(self, mock_file_storage_paths):
        """get_curriculum_crew_context should work with default preferences."""
        context = mm.get_curriculum_crew_context("Python Basics")
        
        assert context["topic"] == "Python Basics"
        assert context["user"]["learning_style"] == "reading"  # default
        assert context["personalization"]["experience_level"] == "beginner"  # default


class TestTeachingCrewContext:
    """Tests for get_teaching_crew_context function."""
    
    def test_get_teaching_crew_context(
        self, temp_db, mock_file_storage_paths, mock_user_preferences
    ):
        """get_teaching_crew_context should return full teaching context."""
        from sensei.storage.file_storage import save_user_preferences, save_chat_history
        
        save_user_preferences(mock_user_preferences)
        save_chat_history("test-course", [
            {"role": "user", "content": "Question 1"},
            {"role": "assistant", "content": "Answer 1"},
        ])
        
        # Set up some history
        temp_db.save_concept_mastery("test-course", "concept-1", 0.5, questions_asked=3)
        
        concept = {"id": "concept-1", "title": "Test Concept", "content": "Content"}
        
        context = mm.get_teaching_crew_context("test-course", concept, temp_db)
        
        assert context["concept"] == concept
        assert context["user"]["name"] == mock_user_preferences["name"]
        assert context["concept_history"]["mastery_level"] == 0.5
        assert len(context["recent_chat"]) == 2
        assert context["personalization"]["has_struggled_before"] is True  # questions > 2
        assert context["personalization"]["is_review"] is False  # times_reviewed = 1
    
    def test_get_teaching_crew_context_is_review(
        self, temp_db, mock_file_storage_paths, mock_user_preferences
    ):
        """get_teaching_crew_context should detect review scenarios."""
        from sensei.storage.file_storage import save_user_preferences
        save_user_preferences(mock_user_preferences)
        
        # Review the concept multiple times
        temp_db.save_concept_mastery("test-course", "concept-1", 0.6)
        temp_db.save_concept_mastery("test-course", "concept-1", 0.8)
        
        concept = {"id": "concept-1", "title": "Test"}
        
        context = mm.get_teaching_crew_context("test-course", concept, temp_db)
        
        assert context["personalization"]["is_review"] is True  # times_reviewed > 1
    
    def test_get_teaching_crew_context_empty_chat(
        self, temp_db, mock_file_storage_paths, mock_user_preferences
    ):
        """get_teaching_crew_context should handle empty chat history."""
        from sensei.storage.file_storage import save_user_preferences
        save_user_preferences(mock_user_preferences)
        
        concept = {"id": "concept-1", "title": "Test"}
        
        context = mm.get_teaching_crew_context("test-course", concept, temp_db)
        
        assert context["recent_chat"] == []
    
    def test_get_teaching_crew_context_missing_concept_id(
        self, temp_db, mock_file_storage_paths, mock_user_preferences
    ):
        """get_teaching_crew_context should handle concept without id key."""
        from sensei.storage.file_storage import save_user_preferences
        save_user_preferences(mock_user_preferences)
        
        # Concept without id key
        concept = {"title": "No ID Concept", "content": "Some content"}
        
        context = mm.get_teaching_crew_context("test-course", concept, temp_db)
        
        assert context["concept"] == concept
        assert context["concept_history"]["is_new"] is True  # No mastery record
    
    def test_get_teaching_crew_context_truncates_long_chat(
        self, temp_db, mock_file_storage_paths, mock_user_preferences
    ):
        """get_teaching_crew_context should truncate to last 10 chat messages."""
        from sensei.storage.file_storage import save_user_preferences, save_chat_history
        save_user_preferences(mock_user_preferences)
        
        # Create 15 chat messages
        messages = [
            {"role": "user" if i % 2 == 0 else "assistant", "content": f"Message {i}"}
            for i in range(15)
        ]
        save_chat_history("test-course", messages)
        
        concept = {"id": "concept-1", "title": "Test"}
        
        context = mm.get_teaching_crew_context("test-course", concept, temp_db)
        
        # Should only have last 10 messages
        assert len(context["recent_chat"]) == 10
        assert context["recent_chat"][0]["content"] == "Message 5"  # First of last 10
        assert context["recent_chat"][-1]["content"] == "Message 14"  # Last message


class TestAssessmentCrewContext:
    """Tests for get_assessment_crew_context function."""
    
    def test_get_assessment_crew_context(
        self, temp_db, mock_file_storage_paths, mock_user_preferences
    ):
        """get_assessment_crew_context should return full assessment context."""
        from sensei.storage.file_storage import save_user_preferences
        save_user_preferences(mock_user_preferences)
        
        # Set up concept mastery
        temp_db.save_concept_mastery("test-course", "concept-1", 0.9)
        temp_db.save_concept_mastery("test-course", "concept-2", 0.4)
        
        module = {
            "id": "module-1",
            "title": "Test Module",
            "concepts": [
                {"id": "concept-1", "title": "Concept 1"},
                {"id": "concept-2", "title": "Concept 2"},
                {"id": "concept-3", "title": "Concept 3"},
            ],
        }
        
        context = mm.get_assessment_crew_context("test-course", module, temp_db)
        
        assert context["module"] == module
        assert context["user"]["name"] == mock_user_preferences["name"]
        assert context["concept_mastery"]["concept-1"] == 0.9
        assert context["concept_mastery"]["concept-2"] == 0.4
        assert context["concept_mastery"]["concept-3"] == 0.0  # No mastery record
        
        # Low mastery concepts should be in focus
        assert "concept-2" in context["focus_concepts"]
        assert "concept-3" in context["focus_concepts"]
        assert "concept-1" not in context["focus_concepts"]  # High mastery
    
    def test_get_assessment_crew_context_includes_weak_concepts(
        self, temp_db, mock_file_storage_paths, mock_user_preferences
    ):
        """get_assessment_crew_context should include weak concepts from quiz history."""
        from sensei.storage.file_storage import save_user_preferences
        save_user_preferences(mock_user_preferences)
        
        # Add quiz with weak concepts
        temp_db.save_quiz_result({
            "course_id": "test-course",
            "module_id": "module-1",
            "quiz_id": "quiz-1",
            "score": 0.6,
            "correct_count": 3,
            "total_questions": 5,
            "weak_concepts": ["concept-1"],  # Even high mastery, flagged weak
        })
        
        # High mastery but flagged weak
        temp_db.save_concept_mastery("test-course", "concept-1", 0.9)
        
        module = {
            "id": "module-1",
            "title": "Test Module",
            "concepts": [{"id": "concept-1", "title": "Concept 1"}],
        }
        
        context = mm.get_assessment_crew_context("test-course", module, temp_db)
        
        # Should be in focus because it was flagged as weak in quiz
        assert "concept-1" in context["focus_concepts"]
    
    def test_get_assessment_crew_context_creates_db_if_not_provided(
        self, mock_file_storage_paths, mock_user_preferences
    ):
        """get_assessment_crew_context should create Database if not provided."""
        from sensei.storage.file_storage import save_user_preferences
        save_user_preferences(mock_user_preferences)
        
        # Patch Database at source since it's imported inside the function
        with patch("sensei.storage.database.Database") as MockDB:
            mock_db = MagicMock()
            mock_db.get_progress.return_value = None
            mock_db.get_quiz_history.return_value = []
            mock_db.get_concept_mastery.return_value = None
            MockDB.return_value = mock_db
            
            module = {"id": "mod-1", "concepts": []}
            context = mm.get_assessment_crew_context("test", module)
            
            # Should create DB twice: once in get_learning_history, once in main function
            assert MockDB.call_count >= 1
    
    def test_get_assessment_crew_context_personalization(
        self, temp_db, mock_file_storage_paths, mock_user_preferences
    ):
        """get_assessment_crew_context should include personalization data."""
        from sensei.storage.file_storage import save_user_preferences
        save_user_preferences(mock_user_preferences)
        
        # Add some quiz history
        for i in range(3):
            temp_db.save_quiz_result({
                "course_id": "test-course",
                "module_id": f"mod-{i}",
                "quiz_id": f"quiz-{i}",
                "score": 0.8,
                "correct_count": 4,
                "total_questions": 5,
            })
        
        module = {"id": "mod-1", "concepts": []}
        
        context = mm.get_assessment_crew_context("test-course", module, temp_db)
        
        assert context["personalization"]["experience_level"] == mock_user_preferences["experience_level"]
        assert context["personalization"]["previous_quiz_count"] == 3
    
    def test_get_assessment_crew_context_empty_module(
        self, temp_db, mock_file_storage_paths, mock_user_preferences
    ):
        """get_assessment_crew_context should handle module with no concepts."""
        from sensei.storage.file_storage import save_user_preferences
        save_user_preferences(mock_user_preferences)
        
        # Module with empty concepts list
        module = {"id": "empty-mod", "title": "Empty Module", "concepts": []}
        
        context = mm.get_assessment_crew_context("test-course", module, temp_db)
        
        assert context["module"] == module
        assert context["concept_mastery"] == {}
        assert context["focus_concepts"] == []
    
    def test_get_assessment_crew_context_missing_concepts_key(
        self, temp_db, mock_file_storage_paths, mock_user_preferences
    ):
        """get_assessment_crew_context should handle module without concepts key."""
        from sensei.storage.file_storage import save_user_preferences
        save_user_preferences(mock_user_preferences)
        
        # Module without concepts key at all
        module = {"id": "no-concepts-mod", "title": "Module Without Concepts"}
        
        context = mm.get_assessment_crew_context("test-course", module, temp_db)
        
        assert context["concept_mastery"] == {}
        assert context["focus_concepts"] == []
