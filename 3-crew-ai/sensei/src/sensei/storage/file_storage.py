"""JSON file storage operations for Sensei.

This module provides file-based storage operations for courses,
user preferences, and other JSON-serializable data.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from sensei.models.enums import ExperienceLevel, LearningStyle
from sensei.utils.constants import (
    CHAT_HISTORY_PATH,
    COURSES_DIR,
    DATA_DIR,
    USER_PREFERENCES_PATH,
)


def ensure_data_directories() -> None:
    """Create data directories if they don't exist.
    
    Creates:
        - data/
        - data/courses/
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    COURSES_DIR.mkdir(parents=True, exist_ok=True)


def _serialize_datetime(obj: Any) -> str:
    """JSON serializer for datetime objects."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


# ============================================================================
# Course Storage
# ============================================================================

def save_course(course: dict[str, Any]) -> None:
    """Save a course to a JSON file.
    
    Args:
        course: Course dictionary containing at least an 'id' key.
    
    Raises:
        ValueError: If course doesn't have an 'id' key.
    """
    if "id" not in course:
        raise ValueError("Course must have an 'id' key")
    
    ensure_data_directories()
    
    course_path = COURSES_DIR / f"{course['id']}.json"
    with open(course_path, "w", encoding="utf-8") as f:
        json.dump(course, f, indent=2, default=_serialize_datetime)


def load_course(course_id: str) -> dict[str, Any] | None:
    """Load a course from a JSON file.
    
    Args:
        course_id: The unique identifier for the course.
    
    Returns:
        Course dictionary if found, None otherwise.
    """
    course_path = COURSES_DIR / f"{course_id}.json"
    
    if not course_path.exists():
        return None
    
    with open(course_path, "r", encoding="utf-8") as f:
        return json.load(f)


def list_courses() -> list[str]:
    """List all course IDs.
    
    Returns:
        List of course IDs (filenames without .json extension).
    """
    ensure_data_directories()
    
    course_files = COURSES_DIR.glob("*.json")
    return [f.stem for f in course_files]


def list_courses_with_metadata() -> list[dict[str, Any]]:
    """List all courses with basic metadata.
    
    Returns:
        List of dictionaries containing course metadata including:
        - id, title, description, created_at
        - total_modules, total_concepts (for progress display)
    """
    courses = []
    for course_id in list_courses():
        course = load_course(course_id)
        if course:
            courses.append({
                "id": course.get("id", course_id),
                "title": course.get("title", "Untitled"),
                "description": course.get("description", ""),
                "created_at": course.get("created_at"),
                "total_modules": _count_modules(course),
                "total_concepts": _count_concepts(course),
            })
    return courses


def _count_modules(course: dict[str, Any]) -> int:
    """Count total modules in a course."""
    return len(course.get("modules", []))


def _count_concepts(course: dict[str, Any]) -> int:
    """Count total concepts in a course."""
    total = 0
    for module in course.get("modules", []):
        total += len(module.get("concepts", []))
    return total


def delete_course(course_id: str) -> bool:
    """Delete a course JSON file.
    
    Args:
        course_id: The unique identifier for the course.
    
    Returns:
        True if the file was deleted, False if it didn't exist.
    """
    course_path = COURSES_DIR / f"{course_id}.json"
    
    if not course_path.exists():
        return False
    
    course_path.unlink()
    return True


def course_exists(course_id: str) -> bool:
    """Check if a course exists.
    
    Args:
        course_id: The unique identifier for the course.
    
    Returns:
        True if the course file exists, False otherwise.
    """
    course_path = COURSES_DIR / f"{course_id}.json"
    return course_path.exists()


def get_course_structure(course_id: str) -> dict[str, Any] | None:
    """Get course structure summary (modules and concept counts).
    
    Args:
        course_id: The unique identifier for the course.
    
    Returns:
        Dictionary with course structure info, None if course doesn't exist.
    """
    course = load_course(course_id)
    if not course:
        return None
    
    modules = []
    for idx, module in enumerate(course.get("modules", [])):
        modules.append({
            "id": module.get("id"),
            "title": module.get("title", f"Module {idx + 1}"),
            "order": module.get("order", idx),
            "concept_count": len(module.get("concepts", [])),
            "estimated_minutes": module.get("estimated_minutes", 30),
        })
    
    return {
        "id": course.get("id"),
        "title": course.get("title"),
        "total_modules": len(modules),
        "total_concepts": _count_concepts(course),
        "modules": modules,
    }


def get_module(course_id: str, module_idx: int) -> dict[str, Any] | None:
    """Get a specific module from a course by index.
    
    Args:
        course_id: The unique identifier for the course.
        module_idx: Zero-based index of the module.
    
    Returns:
        Module dictionary if found, None otherwise.
    """
    course = load_course(course_id)
    if not course:
        return None
    
    modules = course.get("modules", [])
    if module_idx < 0 or module_idx >= len(modules):
        return None
    
    return modules[module_idx]


def get_concept(
    course_id: str,
    module_idx: int,
    concept_idx: int,
) -> dict[str, Any] | None:
    """Get a specific concept from a course.
    
    Args:
        course_id: The unique identifier for the course.
        module_idx: Zero-based index of the module.
        concept_idx: Zero-based index of the concept within the module.
    
    Returns:
        Concept dictionary if found, None otherwise.
    """
    module = get_module(course_id, module_idx)
    if not module:
        return None
    
    concepts = module.get("concepts", [])
    if concept_idx < 0 or concept_idx >= len(concepts):
        return None
    
    return concepts[concept_idx]


def get_concept_with_context(
    course_id: str,
    module_idx: int,
    concept_idx: int,
) -> dict[str, Any] | None:
    """Get a concept with navigation context.
    
    Returns concept along with module info and navigation flags.
    
    Args:
        course_id: The unique identifier for the course.
        module_idx: Zero-based index of the module.
        concept_idx: Zero-based index of the concept.
    
    Returns:
        Dictionary with concept, module info, and navigation context.
    """
    course = load_course(course_id)
    if not course:
        return None
    
    modules = course.get("modules", [])
    if module_idx < 0 or module_idx >= len(modules):
        return None
    
    module = modules[module_idx]
    concepts = module.get("concepts", [])
    if concept_idx < 0 or concept_idx >= len(concepts):
        return None
    
    concept = concepts[concept_idx]
    
    return {
        "concept": concept,
        "module": {
            "id": module.get("id"),
            "title": module.get("title"),
            "idx": module_idx,
        },
        "course": {
            "id": course.get("id"),
            "title": course.get("title"),
        },
        "navigation": {
            "concept_idx": concept_idx,
            "total_concepts_in_module": len(concepts),
            "module_idx": module_idx,
            "total_modules": len(modules),
            "has_previous": concept_idx > 0 or module_idx > 0,
            "has_next": concept_idx < len(concepts) - 1 or module_idx < len(modules) - 1,
            "is_module_complete": concept_idx == len(concepts) - 1,
            "is_course_complete": (
                module_idx == len(modules) - 1 and 
                concept_idx == len(concepts) - 1
            ),
        },
    }


def update_course(course_id: str, updates: dict[str, Any]) -> bool:
    """Update specific fields of a course.
    
    Args:
        course_id: The unique identifier for the course.
        updates: Dictionary of fields to update.
    
    Returns:
        True if course was updated, False if course doesn't exist.
    """
    course = load_course(course_id)
    if not course:
        return False
    
    course.update(updates)
    save_course(course)
    return True


# ============================================================================
# User Preferences Storage
# ============================================================================

def save_user_preferences(preferences: dict[str, Any]) -> None:
    """Save user preferences to a JSON file.
    
    Args:
        preferences: Dictionary of user preferences.
    """
    ensure_data_directories()
    
    with open(USER_PREFERENCES_PATH, "w", encoding="utf-8") as f:
        json.dump(preferences, f, indent=2, default=_serialize_datetime)


def load_user_preferences() -> dict[str, Any]:
    """Load user preferences from a JSON file.
    
    Validates enum values on load to handle corrupted or legacy data.
    
    Returns:
        User preferences dictionary. Returns defaults if file doesn't exist.
    """
    if not USER_PREFERENCES_PATH.exists():
        return get_default_preferences()
    
    try:
        with open(USER_PREFERENCES_PATH, "r", encoding="utf-8") as f:
            raw_prefs = json.load(f)
            return validate_user_preferences(raw_prefs)
    except (json.JSONDecodeError, IOError):
        return get_default_preferences()


def get_default_preferences() -> dict[str, Any]:
    """Get default user preferences.
    
    Uses enum values as the single source of truth for defaults.
    
    Returns:
        Dictionary with default preference values.
    """
    return {
        "name": "",
        "learning_style": str(LearningStyle.READING),
        "session_length_minutes": 30,
        "experience_level": str(ExperienceLevel.BEGINNER),
        "goals": "",
        "is_onboarded": False,
    }


def validate_user_preferences(preferences: dict[str, Any]) -> dict[str, Any]:
    """Validate and normalize user preferences.
    
    Ensures enum values are valid, falling back to defaults if not.
    This provides defensive handling of corrupted or legacy data.
    
    Args:
        preferences: Raw preferences dictionary from storage.
    
    Returns:
        Validated preferences with guaranteed valid enum values.
    """
    validated = dict(preferences)
    
    # Validate learning_style
    try:
        LearningStyle(validated.get("learning_style", ""))
    except ValueError:
        validated["learning_style"] = str(LearningStyle.READING)
    
    # Validate experience_level
    try:
        ExperienceLevel(validated.get("experience_level", ""))
    except ValueError:
        validated["experience_level"] = str(ExperienceLevel.BEGINNER)
    
    return validated


def user_preferences_exist() -> bool:
    """Check if user preferences file exists.
    
    Returns:
        True if preferences file exists, False otherwise.
    """
    return USER_PREFERENCES_PATH.exists()


def delete_user_preferences() -> bool:
    """Delete user preferences file.
    
    Returns:
        True if file was deleted, False if it didn't exist.
    """
    if not USER_PREFERENCES_PATH.exists():
        return False
    
    USER_PREFERENCES_PATH.unlink()
    return True


def update_user_preferences(updates: dict[str, Any]) -> dict[str, Any]:
    """Update specific fields in user preferences.
    
    Loads existing preferences, merges with updates, and saves.
    Used by Settings page for partial preference updates.
    
    Args:
        updates: Dictionary of fields to update.
    
    Returns:
        The updated preferences dictionary.
    """
    preferences = load_user_preferences()
    preferences.update(updates)
    save_user_preferences(preferences)
    return preferences


# ============================================================================
# Chat History Storage
# ============================================================================

def save_chat_history(
    course_id: str,
    messages: list[dict[str, Any]],
) -> None:
    """Save chat history for a course.
    
    Args:
        course_id: The course identifier.
        messages: List of chat message dictionaries.
    """
    ensure_data_directories()
    
    # Load existing history
    all_history = _load_all_chat_history()
    
    # Update history for this course
    all_history[course_id] = messages
    
    with open(CHAT_HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(all_history, f, indent=2, default=_serialize_datetime)


def load_chat_history(course_id: str) -> list[dict[str, Any]]:
    """Load chat history for a course.
    
    Args:
        course_id: The course identifier.
    
    Returns:
        List of chat message dictionaries, empty list if not found.
    """
    all_history = _load_all_chat_history()
    return all_history.get(course_id, [])


def _load_all_chat_history() -> dict[str, list[dict[str, Any]]]:
    """Load all chat history from file."""
    if not CHAT_HISTORY_PATH.exists():
        return {}
    
    try:
        with open(CHAT_HISTORY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def clear_chat_history(course_id: str) -> bool:
    """Clear chat history for a specific course.
    
    Args:
        course_id: The course identifier.
    
    Returns:
        True if history was cleared, False if it didn't exist.
    """
    all_history = _load_all_chat_history()
    
    if course_id not in all_history:
        return False
    
    del all_history[course_id]
    
    with open(CHAT_HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(all_history, f, indent=2)
    
    return True


def clear_all_chat_history() -> None:
    """Clear all chat history."""
    if CHAT_HISTORY_PATH.exists():
        CHAT_HISTORY_PATH.unlink()


def append_chat_message(course_id: str, message: dict[str, Any]) -> int:
    """Append a single message to chat history.
    
    Used by the Q&A chat interface to add messages one at a time.
    
    Args:
        course_id: The course identifier.
        message: Chat message dict with 'role' and 'content' keys.
    
    Returns:
        The new total number of messages for this course.
    """
    history = load_chat_history(course_id)
    history.append(message)
    save_chat_history(course_id, history)
    return len(history)


def get_chat_history_count(course_id: str) -> int:
    """Get the number of chat messages for a course.
    
    Args:
        course_id: The course identifier.
    
    Returns:
        Number of messages in the chat history.
    """
    return len(load_chat_history(course_id))
