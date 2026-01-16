"""CrewAI memory configuration for Sensei.

This module provides memory configuration for CrewAI crews,
including short-term, long-term, and entity memory settings.

It also provides helper functions to gather context from our
storage layer (database.py, file_storage.py) for crew execution.
"""

from pathlib import Path
from typing import Any, TYPE_CHECKING

from sensei.models.enums import ExperienceLevel, LearningStyle
from sensei.utils.constants import DATA_DIR, DATABASE_PATH

if TYPE_CHECKING:
    from sensei.storage.database import Database


# Path for CrewAI's internal memory storage
MEMORY_DIR = DATA_DIR / "memory"


def ensure_memory_directory() -> None:
    """Create memory directory if it doesn't exist."""
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)


def get_memory_config() -> dict[str, Any]:
    """Get the complete memory configuration for CrewAI crews.
    
    This configuration enables all memory types:
    - Short-term memory: For current session context
    - Long-term memory: For persistent learning across sessions
    - Entity memory: For course, module, and concept information
    
    Returns:
        Dictionary with memory configuration settings.
    """
    ensure_memory_directory()
    
    return {
        "memory": True,  # Enable memory system
        "memory_config": {
            "provider": "mem0",  # CrewAI's default memory provider
        },
        "verbose": False,
    }


def get_short_term_memory_config() -> dict[str, Any]:
    """Get configuration for short-term memory.
    
    Short-term memory stores:
    - Current lesson content being displayed
    - Chat history (Q&A) for this session
    - Questions asked (indicates confusion points)
    - Current position (module index, concept index)
    
    Returns:
        Short-term memory configuration dictionary.
    """
    return {
        "type": "short_term",
        "storage": "in_memory",
        "max_items": 100,
    }


def get_long_term_memory_config() -> dict[str, Any]:
    """Get configuration for long-term memory.
    
    Long-term memory stores:
    - Quiz scores over time
    - Concepts frequently struggled with
    - Learning velocity patterns
    - Time spent per topic
    
    Uses SQLite for persistence.
    
    Returns:
        Long-term memory configuration dictionary.
    """
    ensure_memory_directory()
    
    return {
        "type": "long_term",
        "storage": "sqlite",
        "path": str(DATABASE_PATH),
    }


def get_entity_memory_config() -> dict[str, Any]:
    """Get configuration for entity memory.
    
    Entity memory stores:
    - Courses (id, title, description)
    - Modules (id, title, order, concepts)
    - Concepts (id, title, content, mastery level)
    - Questions asked per concept
    
    Returns:
        Entity memory configuration dictionary.
    """
    ensure_memory_directory()
    
    return {
        "type": "entity",
        "storage": "json",
        "path": str(MEMORY_DIR / "entities"),
    }


def get_crew_memory_settings(
    verbose: bool = False,
    embedder_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Get complete memory settings for a CrewAI crew.
    
    This function returns the settings that should be passed
    to a Crew's constructor to enable memory.
    
    Args:
        verbose: Whether to enable verbose memory logging.
        embedder_config: Optional custom embedder configuration.
    
    Returns:
        Dictionary of memory settings for Crew initialization.
    
    Example:
        ```python
        from sensei.storage.memory_manager import get_crew_memory_settings
        
        crew = Crew(
            agents=[...],
            tasks=[...],
            **get_crew_memory_settings()
        )
        ```
    """
    ensure_memory_directory()
    
    settings = {
        "memory": True,
        "verbose": verbose,
    }
    
    if embedder_config:
        settings["embedder"] = embedder_config
    
    return settings


def get_openai_embedder_config(model: str = "text-embedding-3-small") -> dict[str, Any]:
    """Get OpenAI embedder configuration for semantic memory.
    
    Args:
        model: The OpenAI embedding model to use.
    
    Returns:
        Embedder configuration dictionary.
    """
    return {
        "provider": "openai",
        "config": {
            "model": model,
        },
    }


def clear_session_memory() -> None:
    """Clear short-term memory for a new session.
    
    This should be called when starting a fresh learning session
    to ensure clean context.
    
    Note: This clears in-memory state. The actual CrewAI short-term
    memory is managed by CrewAI itself and resets between crew runs.
    """
    # Short-term memory in CrewAI is automatically cleared between crew executions
    # This function is provided for explicit control if needed
    pass


def clear_all_memory() -> None:
    """Clear all persistent memory data.
    
    Warning: This will delete all learning history and entity data.
    Use with caution.
    """
    import shutil
    
    if MEMORY_DIR.exists():
        shutil.rmtree(MEMORY_DIR)
    
    ensure_memory_directory()


def get_memory_stats() -> dict[str, Any]:
    """Get statistics about memory usage.
    
    Returns:
        Dictionary with memory statistics.
    """
    stats = {
        "memory_dir_exists": MEMORY_DIR.exists(),
        "database_exists": DATABASE_PATH.exists(),
        "database_size_bytes": 0,
        "entity_files_count": 0,
    }
    
    if DATABASE_PATH.exists():
        stats["database_size_bytes"] = DATABASE_PATH.stat().st_size
    
    entities_dir = MEMORY_DIR / "entities"
    if entities_dir.exists():
        stats["entity_files_count"] = len(list(entities_dir.glob("*.json")))
    
    return stats


# =============================================================================
# Crew Context Helpers
# =============================================================================
# These functions gather context from our storage layer for crew execution.
# They help crews make personalized decisions based on user history.

def get_user_context() -> dict[str, Any]:
    """Get user context for crew personalization.
    
    Returns user preferences and profile information that crews
    can use to personalize their output.
    
    Note: Uses enum default values as single source of truth.
    The load_user_preferences() function now validates enum values,
    so defaults here are only for extra safety.
    
    Returns:
        Dictionary with user context including:
        - name, learning_style, experience_level, goals
        - is_onboarded flag
    """
    from sensei.storage.file_storage import load_user_preferences
    
    prefs = load_user_preferences()
    return {
        "name": prefs.get("name", "Learner"),
        "learning_style": prefs.get("learning_style", str(LearningStyle.READING)),
        "experience_level": prefs.get("experience_level", str(ExperienceLevel.BEGINNER)),
        "session_length_minutes": prefs.get("session_length_minutes", 30),
        "goals": prefs.get("goals", ""),
        "is_onboarded": prefs.get("is_onboarded", False),
    }


def get_learning_history(
    course_id: str,
    db: "Database | None" = None,
) -> dict[str, Any]:
    """Get learning history for a course.
    
    Provides crews with historical data about the learner's
    performance to enable adaptive teaching.
    
    Args:
        course_id: The course identifier.
        db: Optional database instance. Creates one if not provided.
    
    Returns:
        Dictionary with learning history including:
        - progress (completion %, modules/concepts completed)
        - quiz_history (recent quiz results)
        - weak_concepts (concepts that need review)
        - time_spent_minutes
    """
    from sensei.storage.database import Database
    
    if db is None:
        db = Database()
    
    # Get progress
    progress = db.get_progress(course_id)
    if progress is None:
        progress = {
            "completion_percentage": 0.0,
            "modules_completed": 0,
            "total_modules": 0,
            "concepts_completed": 0,
            "total_concepts": 0,
            "time_spent_minutes": 0,
        }
    
    # Get quiz history
    quiz_history = db.get_quiz_history(course_id)
    
    # Extract weak concepts from recent quizzes
    weak_concepts = set()
    for quiz in quiz_history[:5]:  # Last 5 quizzes
        if quiz.get("weak_concepts"):
            weak_concepts.update(quiz["weak_concepts"])
    
    return {
        "progress": {
            "completion_percentage": progress.get("completion_percentage", 0.0),
            "modules_completed": progress.get("modules_completed", 0),
            "total_modules": progress.get("total_modules", 0),
            "concepts_completed": progress.get("concepts_completed", 0),
            "total_concepts": progress.get("total_concepts", 0),
        },
        "quiz_history": [
            {
                "module_title": q.get("module_title", ""),
                "score": q.get("score", 0),
                "passed": q.get("passed", False),
                "completed_at": q.get("completed_at", ""),
            }
            for q in quiz_history[:5]
        ],
        "weak_concepts": list(weak_concepts),
        "time_spent_minutes": progress.get("time_spent_minutes", 0),
    }


def get_concept_history(
    course_id: str,
    concept_id: str,
    db: "Database | None" = None,
) -> dict[str, Any]:
    """Get learning history for a specific concept.
    
    Used by Teaching Crew to know if the learner has struggled
    with this concept before.
    
    Args:
        course_id: The course identifier.
        concept_id: The concept identifier.
        db: Optional database instance.
    
    Returns:
        Dictionary with concept history including:
        - mastery_level (0.0 - 1.0)
        - questions_asked (number of Q&A interactions)
        - times_reviewed (how many times concept was viewed)
    """
    from sensei.storage.database import Database
    
    if db is None:
        db = Database()
    
    mastery = db.get_concept_mastery(course_id, concept_id)
    
    if mastery is None:
        return {
            "mastery_level": 0.0,
            "questions_asked": 0,
            "times_reviewed": 0,
            "is_new": True,
        }
    
    return {
        "mastery_level": mastery.get("mastery_level", 0.0),
        "questions_asked": mastery.get("questions_asked", 0),
        "times_reviewed": mastery.get("times_reviewed", 0),
        "is_new": False,
    }


def get_curriculum_crew_context(topic: str) -> dict[str, Any]:
    """Get context for Curriculum Crew execution.
    
    Gathers all necessary context for creating a new course.
    
    Args:
        topic: The topic to create a course for.
    
    Returns:
        Dictionary with context for curriculum generation.
    """
    user_ctx = get_user_context()
    
    return {
        "topic": topic,
        "user": user_ctx,
        "personalization": {
            "experience_level": user_ctx["experience_level"],
            "learning_style": user_ctx["learning_style"],
            "goals": user_ctx["goals"],
        },
    }


def get_teaching_crew_context(
    course_id: str,
    concept: dict[str, Any],
    db: "Database | None" = None,
) -> dict[str, Any]:
    """Get context for Teaching Crew execution.
    
    Gathers all necessary context for teaching a concept,
    including user preferences and past struggles.
    
    Args:
        course_id: The course identifier.
        concept: The concept dictionary (id, title, content).
        db: Optional database instance.
    
    Returns:
        Dictionary with context for lesson generation.
    """
    from sensei.storage.file_storage import load_chat_history
    
    user_ctx = get_user_context()
    concept_history = get_concept_history(
        course_id, 
        concept.get("id", ""), 
        db
    )
    learning_history = get_learning_history(course_id, db)
    
    # Get recent chat for this course (for Q&A context)
    chat_history = load_chat_history(course_id)
    recent_chat = chat_history[-10:] if chat_history else []
    
    return {
        "concept": concept,
        "user": user_ctx,
        "concept_history": concept_history,
        "learning_history": learning_history,
        "recent_chat": recent_chat,
        "personalization": {
            "learning_style": user_ctx["learning_style"],
            "experience_level": user_ctx["experience_level"],
            "has_struggled_before": concept_history["questions_asked"] > 2,
            "is_review": concept_history["times_reviewed"] > 1,
        },
    }


def get_assessment_crew_context(
    course_id: str,
    module: dict[str, Any],
    db: "Database | None" = None,
) -> dict[str, Any]:
    """Get context for Assessment Crew execution.
    
    Gathers all necessary context for generating a quiz,
    including weak concepts that need more testing.
    
    Args:
        course_id: The course identifier.
        module: The module dictionary (id, title, concepts).
        db: Optional database instance.
    
    Returns:
        Dictionary with context for quiz generation.
    """
    user_ctx = get_user_context()
    learning_history = get_learning_history(course_id, db)
    
    # Get mastery levels for all concepts in the module
    from sensei.storage.database import Database
    if db is None:
        db = Database()
    
    concept_mastery = {}
    for concept in module.get("concepts", []):
        concept_id = concept.get("id", "")
        mastery = db.get_concept_mastery(course_id, concept_id)
        if mastery:
            concept_mastery[concept_id] = mastery.get("mastery_level", 0.0)
        else:
            concept_mastery[concept_id] = 0.0
    
    # Find concepts that need more focus (low mastery or flagged as weak)
    focus_concepts = [
        cid for cid, level in concept_mastery.items()
        if level < 0.7 or cid in learning_history["weak_concepts"]
    ]
    
    return {
        "module": module,
        "user": user_ctx,
        "learning_history": learning_history,
        "concept_mastery": concept_mastery,
        "focus_concepts": focus_concepts,
        "personalization": {
            "experience_level": user_ctx["experience_level"],
            "previous_quiz_count": len(learning_history["quiz_history"]),
        },
    }
