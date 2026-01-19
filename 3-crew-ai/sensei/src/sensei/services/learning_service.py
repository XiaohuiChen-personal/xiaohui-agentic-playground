"""Learning service for managing learning sessions.

This service manages active learning sessions, including navigation
through concepts and Q&A interactions. Lesson generation uses the
TeachingCrew for AI-powered content, with stub fallbacks for testing.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sensei.models.enums import ConceptStatus, MessageRole
from sensei.models.schemas import (
    ChatMessage,
    Concept,
    ConceptLesson,
    LearningSession,
    UserPreferences,
)
from sensei.storage.database import Database
from sensei.storage.file_storage import (
    append_chat_message,
    get_concept_with_context,
    get_module,
    load_chat_history,
    load_course,
    load_user_preferences,
    save_chat_history,
)
from sensei.storage.memory_manager import format_previous_struggles

if TYPE_CHECKING:
    from sensei.crews.teaching_crew import TeachingCrew


class LearningService:
    """Service for managing learning sessions.
    
    This service handles:
    - Starting and ending learning sessions
    - Navigating between concepts (next/previous)
    - Generating lesson content (AI-powered via TeachingCrew)
    - Q&A interactions (AI-powered via TeachingCrew)
    - Session state management
    
    The service supports two modes:
    - AI mode (default): Uses TeachingCrew for intelligent content
    - Stub mode: Uses static templates for testing without LLM calls
    
    Example:
        ```python
        # With AI (production)
        service = LearningService()
        session = service.start_session("course-123")
        lesson = service.get_current_concept()
        answer = service.ask_question("What does this mean?")
        
        # Without AI (testing)
        service = LearningService(use_ai=False)
        ```
    """
    
    def __init__(
        self,
        database: Database | None = None,
        teaching_crew: "TeachingCrew | None" = None,
        use_ai: bool = True,
    ):
        """Initialize the learning service.
        
        Args:
            database: Optional Database instance.
            teaching_crew: Optional TeachingCrew instance for AI generation.
                If not provided and use_ai=True, will be created on demand.
            use_ai: Whether to use AI for lesson/answer generation.
                Set to False for testing without LLM calls.
        """
        self._db = database or Database()
        self._teaching_crew = teaching_crew
        self._use_ai = use_ai
        self._session: LearningSession | None = None
        self._course_data: dict[str, Any] | None = None
        self._db_session_id: int | None = None
        
        # Cache for lesson content to avoid regeneration
        self._lesson_cache: dict[str, str] = {}
    
    @property
    def is_session_active(self) -> bool:
        """Check if a learning session is currently active."""
        return self._session is not None
    
    @property
    def current_session(self) -> LearningSession | None:
        """Get the current session if active."""
        return self._session
    
    def start_session(self, course_id: str) -> LearningSession:
        """Start or resume a learning session for a course.
        
        If progress exists, resumes from the last position.
        Otherwise, starts from the beginning.
        
        Args:
            course_id: The unique identifier for the course.
        
        Returns:
            LearningSession object with current state.
        
        Raises:
            ValueError: If course doesn't exist.
        """
        # Load course data
        course = load_course(course_id)
        if course is None:
            raise ValueError(f"Course not found: {course_id}")
        
        self._course_data = course
        
        # Get existing progress to determine position
        progress = self._db.get_progress(course_id)
        
        if progress:
            module_idx = progress.get("current_module_idx", 0)
            concept_idx = progress.get("current_concept_idx", 0)
        else:
            module_idx = 0
            concept_idx = 0
        
        # Load existing chat history
        chat_history = load_chat_history(course_id)
        chat_messages = [
            ChatMessage(
                role=MessageRole(msg.get("role", "user")),
                content=msg.get("content", ""),
                timestamp=datetime.fromisoformat(msg["timestamp"])
                    if "timestamp" in msg else datetime.now(),
            )
            for msg in chat_history
        ]
        
        # Create session
        self._session = LearningSession(
            course_id=course_id,
            current_module_idx=module_idx,
            current_concept_idx=concept_idx,
            chat_history=chat_messages,
        )
        
        # Start database session for tracking
        self._db_session_id = self._db.start_learning_session(course_id)
        
        return self._session
    
    def get_current_concept(
        self,
        user_prefs: UserPreferences | None = None,
    ) -> ConceptLesson:
        """Get the current concept with generated lesson content.
        
        When use_ai=True, this uses the TeachingCrew to generate
        personalized lesson content. When use_ai=False, it uses
        stub content for testing.
        
        Args:
            user_prefs: Optional user preferences for personalization.
                If not provided, will attempt to load from storage.
        
        Returns:
            ConceptLesson with concept info and lesson content.
        
        Raises:
            RuntimeError: If no session is active or concept not found.
        """
        if not self._session or not self._course_data:
            raise RuntimeError("No active learning session")
        
        # Get concept with navigation context
        context = get_concept_with_context(
            self._session.course_id,
            self._session.current_module_idx,
            self._session.current_concept_idx,
        )
        
        if context is None:
            raise RuntimeError("Could not load current concept")
        
        concept = context["concept"]
        module = context["module"]
        nav = context["navigation"]
        
        # Get or generate lesson content
        concept_id = concept.get("id", "")
        
        # Check cache first
        if concept_id in self._lesson_cache:
            lesson_content = self._lesson_cache[concept_id]
        elif self._use_ai:
            # Generate with AI
            if user_prefs is None:
                prefs_dict = load_user_preferences()
                user_prefs = (
                    UserPreferences(**prefs_dict) if prefs_dict else UserPreferences()
                )
            lesson_content = self._generate_lesson_with_ai(
                concept, module, user_prefs
            )
            # Cache the generated lesson
            self._lesson_cache[concept_id] = lesson_content
        else:
            # Use stub
            lesson_content = self._generate_lesson_stub(concept, module)
        
        return ConceptLesson(
            concept_id=concept_id,
            concept_title=concept.get("title", ""),
            lesson_content=lesson_content,
            module_title=module.get("title", ""),
            module_idx=self._session.current_module_idx,
            concept_idx=self._session.current_concept_idx,
            total_concepts_in_module=nav.get("total_concepts_in_module", 0),
            has_previous=nav.get("has_previous", False),
            has_next=nav.get("has_next", True),
            is_module_complete=nav.get("is_module_complete", False),
        )
    
    def _generate_lesson_with_ai(
        self,
        concept: dict[str, Any],
        module: dict[str, Any],
        user_prefs: UserPreferences,
    ) -> str:
        """Generate lesson content using the TeachingCrew.
        
        Args:
            concept: Concept dictionary from course data.
            module: Module dictionary containing the concept.
            user_prefs: User preferences for personalization.
        
        Returns:
            Generated lesson content as Markdown string.
        
        Raises:
            RuntimeError: If lesson generation fails.
        """
        # Lazy initialization of TeachingCrew
        if self._teaching_crew is None:
            from sensei.crews.teaching_crew import TeachingCrew
            self._teaching_crew = TeachingCrew()
        
        # Convert concept dict to Concept object
        concept_obj = Concept(
            id=concept.get("id", ""),
            title=concept.get("title", ""),
            content=concept.get("content", ""),
            order=concept.get("order", 0),
        )
        
        # Get previous struggles for context
        concept_id = concept.get("id", "")
        if self._session and concept_id:
            mastery_data = self._db.get_concept_mastery(
                self._session.course_id, concept_id
            )
            # Format mastery data as struggle context
            if mastery_data:
                previous_struggles = format_previous_struggles(mastery_data)
            else:
                previous_struggles = ""
        else:
            previous_struggles = ""
        
        try:
            return self._teaching_crew.teach_concept(
                concept=concept_obj,
                user_prefs=user_prefs,
                module_title=module.get("title", ""),
                previous_struggles=previous_struggles,
            )
        except Exception as e:
            raise RuntimeError(
                f"Failed to generate lesson for '{concept_obj.title}': {e}"
            ) from e
    
    def next_concept(self) -> ConceptLesson | None:
        """Navigate to the next concept.
        
        Advances to the next concept in the current module,
        or to the first concept of the next module if at module end.
        
        Returns:
            ConceptLesson for the next concept, or None if at course end.
        
        Raises:
            RuntimeError: If no session is active.
        """
        if not self._session or not self._course_data:
            raise RuntimeError("No active learning session")
        
        modules = self._course_data.get("modules", [])
        total_modules = len(modules)
        
        current_module = modules[self._session.current_module_idx]
        total_concepts = len(current_module.get("concepts", []))
        
        # Try to advance
        advanced = self._session.advance_concept(total_concepts, total_modules)
        
        if not advanced:
            # At end of course
            return None
        
        # Save progress
        self._save_current_progress()
        
        return self.get_current_concept()
    
    def previous_concept(self) -> ConceptLesson | None:
        """Navigate to the previous concept.
        
        Goes back to the previous concept in the current module,
        or to the last concept of the previous module.
        
        Returns:
            ConceptLesson for the previous concept, or None if at start.
        
        Raises:
            RuntimeError: If no session is active.
        """
        if not self._session or not self._course_data:
            raise RuntimeError("No active learning session")
        
        # Check if at the very start
        if (self._session.current_module_idx == 0 and 
            self._session.current_concept_idx == 0):
            return None
        
        # Save module index BEFORE going back to detect module boundary crossing
        module_before = self._session.current_module_idx
        
        went_back = self._session.go_back_concept()
        
        if not went_back:
            return None
        
        # Only adjust if we ACTUALLY crossed a module boundary
        # (module index decreased, meaning we went to a previous module)
        if self._session.current_module_idx < module_before:
            # We crossed to a previous module, adjust to its last concept
            # go_back_concept() sets concept_idx to 0, but we need the last concept
            modules = self._course_data.get("modules", [])
            prev_module = modules[self._session.current_module_idx]
            last_concept_idx = len(prev_module.get("concepts", [])) - 1
            if last_concept_idx >= 0:
                self._session.current_concept_idx = last_concept_idx
        
        return self.get_current_concept()
    
    def ask_question(
        self,
        question: str,
        user_prefs: UserPreferences | None = None,
    ) -> str:
        """Ask a question about the current concept.
        
        When use_ai=True, this uses the TeachingCrew Q&A Mentor
        to provide personalized answers. When use_ai=False, it
        uses stub responses for testing.
        
        Args:
            question: The user's question.
            user_prefs: Optional user preferences for personalization.
                If not provided, will attempt to load from storage.
        
        Returns:
            AI-generated answer.
        
        Raises:
            RuntimeError: If no session is active.
            ValueError: If question is empty or whitespace only.
        """
        if not self._session or not self._course_data:
            raise RuntimeError("No active learning session")
        
        # Validate question is not empty
        if not question or not question.strip():
            raise ValueError("Question cannot be empty")
        
        # Create user message
        user_msg = ChatMessage.user_message(question)
        self._session.add_message(user_msg)
        
        # Generate answer
        if self._use_ai:
            if user_prefs is None:
                prefs_dict = load_user_preferences()
                user_prefs = (
                    UserPreferences(**prefs_dict) if prefs_dict else UserPreferences()
                )
            answer = self._generate_answer_with_ai(question, user_prefs)
        else:
            answer = self._generate_answer_stub(question)
        
        # Create assistant message
        assistant_msg = ChatMessage.assistant_message(answer)
        self._session.chat_history.append(assistant_msg)
        
        # Save chat history
        self._save_chat_history()
        
        # Track concept mastery (questions indicate potential confusion)
        self._track_question_asked()
        
        return answer
    
    def _generate_answer_with_ai(
        self,
        question: str,
        user_prefs: UserPreferences,
    ) -> str:
        """Generate an answer using the TeachingCrew Q&A Mentor.
        
        Args:
            question: The user's question.
            user_prefs: User preferences for personalization.
        
        Returns:
            Generated answer as Markdown string.
        
        Raises:
            RuntimeError: If answer generation fails.
        """
        if not self._session or not self._course_data:
            raise RuntimeError("No active learning session")
        
        # Lazy initialization of TeachingCrew
        if self._teaching_crew is None:
            from sensei.crews.teaching_crew import TeachingCrew
            self._teaching_crew = TeachingCrew()
        
        # Get current concept
        modules = self._course_data.get("modules", [])
        module = modules[self._session.current_module_idx]
        concepts = module.get("concepts", [])
        concept_dict = concepts[self._session.current_concept_idx]
        
        # Convert to Concept object
        concept_obj = Concept(
            id=concept_dict.get("id", ""),
            title=concept_dict.get("title", ""),
            content=concept_dict.get("content", ""),
            order=concept_dict.get("order", 0),
        )
        
        # Get cached lesson content
        concept_id = concept_dict.get("id", "")
        lesson_content = self._lesson_cache.get(concept_id, "")
        
        # Format chat history for context
        chat_history = [
            {"role": msg.role.value, "content": msg.content}
            for msg in self._session.chat_history[-10:]  # Last 10 messages
        ]
        
        try:
            return self._teaching_crew.answer_question(
                question=question,
                concept=concept_obj,
                lesson_content=lesson_content,
                chat_history=chat_history,
                user_prefs=user_prefs,
            )
        except Exception as e:
            raise RuntimeError(
                f"Failed to generate answer for question: {e}"
            ) from e
    
    def end_session(self) -> dict[str, Any]:
        """End the current learning session.
        
        Saves progress and returns a session summary.
        
        Returns:
            Dictionary with session summary including:
            - duration_minutes
            - concepts_covered
            - questions_asked
        
        Raises:
            RuntimeError: If no session is active.
        """
        if not self._session:
            raise RuntimeError("No active learning session")
        
        # Calculate duration
        duration = datetime.now() - self._session.started_at
        duration_minutes = int(duration.total_seconds() / 60)
        
        # End database session
        if self._db_session_id:
            self._db.end_learning_session(
                self._db_session_id,
                concepts_covered=self._session.concepts_covered,
                questions_asked=self._session.questions_asked,
            )
        
        # Save final progress
        self._save_current_progress(time_spent=duration_minutes)
        
        # Build summary
        summary = {
            "course_id": self._session.course_id,
            "duration_minutes": duration_minutes,
            "concepts_covered": self._session.concepts_covered,
            "questions_asked": self._session.questions_asked,
            "final_position": {
                "module_idx": self._session.current_module_idx,
                "concept_idx": self._session.current_concept_idx,
            },
        }
        
        # Clear session and cache
        self._session = None
        self._course_data = None
        self._db_session_id = None
        self._lesson_cache = {}
        
        return summary
    
    def clear_lesson_cache(self) -> None:
        """Clear the lesson content cache.
        
        Useful when user preferences change and lessons
        need to be regenerated.
        """
        self._lesson_cache = {}
    
    def is_module_complete(self) -> bool:
        """Check if current module is complete.
        
        Returns:
            True if at the last concept of the current module.
        
        Raises:
            RuntimeError: If no session is active.
        """
        if not self._session or not self._course_data:
            raise RuntimeError("No active learning session")
        
        modules = self._course_data.get("modules", [])
        current_module = modules[self._session.current_module_idx]
        total_concepts = len(current_module.get("concepts", []))
        
        return self._session.current_concept_idx == total_concepts - 1
    
    def get_module_progress(self) -> dict[str, Any]:
        """Get progress within the current module.
        
        Returns:
            Dictionary with module progress info.
        """
        if not self._session or not self._course_data:
            raise RuntimeError("No active learning session")
        
        modules = self._course_data.get("modules", [])
        current_module = modules[self._session.current_module_idx]
        total_concepts = len(current_module.get("concepts", []))
        
        return {
            "module_idx": self._session.current_module_idx,
            "module_title": current_module.get("title", ""),
            "current_concept_idx": self._session.current_concept_idx,
            "total_concepts": total_concepts,
            "completion_percentage": (self._session.current_concept_idx + 1) / total_concepts
                if total_concepts > 0 else 0.0,
        }
    
    def _save_current_progress(self, time_spent: int = 0) -> None:
        """Save current session progress to database."""
        if not self._session or not self._course_data:
            return
        
        # Count total concepts in course
        total_concepts = sum(
            len(m.get("concepts", []))
            for m in self._course_data.get("modules", [])
        )
        
        # Count completed concepts (all concepts before current position)
        completed = 0
        for idx, module in enumerate(self._course_data.get("modules", [])):
            if idx < self._session.current_module_idx:
                completed += len(module.get("concepts", []))
            elif idx == self._session.current_module_idx:
                completed += self._session.current_concept_idx
        
        # Get existing time
        existing = self._db.get_progress(self._session.course_id)
        existing_time = existing.get("time_spent_minutes", 0) if existing else 0
        
        progress_dict = {
            "course_id": self._session.course_id,
            "completion_percentage": completed / total_concepts if total_concepts > 0 else 0.0,
            "modules_completed": self._session.current_module_idx,
            "total_modules": len(self._course_data.get("modules", [])),
            "concepts_completed": completed,
            "total_concepts": total_concepts,
            "current_module_idx": self._session.current_module_idx,
            "current_concept_idx": self._session.current_concept_idx,
            "time_spent_minutes": existing_time + time_spent,
        }
        
        self._db.save_progress(progress_dict)
    
    def _save_chat_history(self) -> None:
        """Save chat history to file storage."""
        if not self._session:
            return
        
        messages = [msg.model_dump() for msg in self._session.chat_history]
        save_chat_history(self._session.course_id, messages)
    
    def _track_question_asked(self) -> None:
        """Track that a question was asked about current concept."""
        if not self._session or not self._course_data:
            return
        
        # Get current concept
        modules = self._course_data.get("modules", [])
        module = modules[self._session.current_module_idx]
        concepts = module.get("concepts", [])
        concept = concepts[self._session.current_concept_idx]
        concept_id = concept.get("id", "")
        
        if concept_id:
            # Update concept mastery (lower because questions indicate confusion)
            self._db.save_concept_mastery(
                self._session.course_id,
                concept_id,
                mastery_level=0.3,  # Questions suggest incomplete understanding
                questions_asked=1,
            )
    
    def _generate_lesson_stub(
        self,
        concept: dict[str, Any],
        module: dict[str, Any],
    ) -> str:
        """Generate stub lesson content for a concept.
        
        Note: Will be replaced by TeachingCrew in Milestone 6.
        """
        title = concept.get("title", "Concept")
        content = concept.get("content", "")
        module_title = module.get("title", "Module")
        
        return f"""## {title}

{content}

### Overview

In this lesson, we'll explore **{title}** as part of the {module_title} module.

### Key Points

- Understanding {title} is fundamental to mastering this topic
- This concept builds upon what you've learned previously
- Practice is essential for truly grasping this material

### Explanation

{title} is an important concept that you'll use frequently. Let's break it down:

1. **What it is**: {title} refers to a core principle in this domain
2. **Why it matters**: Understanding this will help you build more complex solutions
3. **How to apply it**: You'll see examples of this throughout your learning journey

### Example

Here's a simple demonstration of {title} in action:

```python
# Example code demonstrating {title}
def example():
    \"\"\"Demonstrates the concept of {title}.\"\"\"
    print("This is a placeholder example")
    return "Success!"
```

### Summary

You've now learned about **{title}**. This knowledge will be essential as you continue through the course.

---
*💡 Tip: If you have questions, use the chat below to ask Sensei!*
"""
    
    def _generate_answer_stub(self, question: str) -> str:
        """Generate stub answer for a question.
        
        Note: Will be replaced by TeachingCrew in Milestone 6.
        """
        return f"""Great question! 🎯

You asked: "{question}"

This is a placeholder response. In the full version, Sensei's Teaching Crew will provide a detailed, personalized answer based on:

- Your current concept and progress
- Your learning style preferences
- The context of what you're learning

For now, here are some general tips:
1. Review the lesson content above
2. Try working through the examples
3. Practice applying the concept in your own projects

Keep up the great work! 💪
"""
