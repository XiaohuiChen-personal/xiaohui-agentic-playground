"""Storage layer for Sensei.

This module provides data persistence functionality including:
- SQLite database operations (progress, quiz results)
- JSON file storage (courses, user preferences)
- CrewAI memory configuration
"""

from sensei.storage.database import Database
from sensei.storage.file_storage import (
    append_chat_message,
    clear_all_chat_history,
    clear_chat_history,
    course_exists,
    delete_course,
    delete_user_preferences,
    ensure_data_directories,
    get_chat_history_count,
    get_concept,
    get_concept_with_context,
    get_course_structure,
    get_default_preferences,
    get_module,
    list_courses,
    list_courses_with_metadata,
    load_chat_history,
    load_course,
    load_user_preferences,
    save_chat_history,
    save_course,
    save_user_preferences,
    update_course,
    update_user_preferences,
    user_preferences_exist,
    validate_user_preferences,
)
from sensei.storage.memory_manager import (
    clear_all_memory,
    clear_session_memory,
    get_assessment_crew_context,
    get_concept_history,
    get_crew_memory_settings,
    get_curriculum_crew_context,
    get_entity_memory_config,
    get_learning_history,
    get_long_term_memory_config,
    get_memory_config,
    get_memory_stats,
    get_openai_embedder_config,
    get_short_term_memory_config,
    get_teaching_crew_context,
    get_user_context,
)

__all__ = [
    # Database
    "Database",
    # File storage - Course operations
    "ensure_data_directories",
    "save_course",
    "load_course",
    "list_courses",
    "list_courses_with_metadata",
    "delete_course",
    "course_exists",
    "update_course",
    "get_course_structure",
    "get_module",
    "get_concept",
    "get_concept_with_context",
    # File storage - User preferences
    "save_user_preferences",
    "load_user_preferences",
    "get_default_preferences",
    "user_preferences_exist",
    "delete_user_preferences",
    "update_user_preferences",
    "validate_user_preferences",
    # File storage - Chat history
    "save_chat_history",
    "load_chat_history",
    "clear_chat_history",
    "clear_all_chat_history",
    "append_chat_message",
    "get_chat_history_count",
    # Memory manager - CrewAI configuration
    "get_memory_config",
    "get_short_term_memory_config",
    "get_long_term_memory_config",
    "get_entity_memory_config",
    "get_crew_memory_settings",
    "get_openai_embedder_config",
    "clear_session_memory",
    "clear_all_memory",
    "get_memory_stats",
    # Memory manager - Crew context helpers
    "get_user_context",
    "get_learning_history",
    "get_concept_history",
    "get_curriculum_crew_context",
    "get_teaching_crew_context",
    "get_assessment_crew_context",
]
