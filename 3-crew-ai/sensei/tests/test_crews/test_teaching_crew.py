"""Unit tests for TeachingCrew with mocked LLM.

These tests verify the TeachingCrew's business logic without making
actual LLM API calls. All CrewAI components are mocked to return
predictable outputs.
"""

from unittest.mock import MagicMock, patch

import pytest

from sensei.crews.teaching_crew import TeachingCrew
from sensei.models.enums import ExperienceLevel, LearningStyle
from sensei.models.schemas import Concept, UserPreferences


# ==================== FIXTURES ====================


@pytest.fixture
def sample_concept():
    """Create a sample concept for testing."""
    return Concept(
        title="Variables in Python",
        content="Variables are containers for storing data values.",
        order=0,
    )


@pytest.fixture
def sample_user_prefs():
    """Create sample user preferences."""
    return UserPreferences(
        experience_level=ExperienceLevel.INTERMEDIATE,
        learning_style=LearningStyle.VISUAL,
        goals="Learn Python for data science",
    )


@pytest.fixture
def lesson_output():
    """Return a sample lesson output."""
    return """## Variables in Python

### Introduction
Variables are fundamental building blocks in Python programming.

### Core Explanation
A variable is a named location in memory that stores a value.

### Examples
```python
name = "Alice"
age = 25
```

### Common Mistakes
- Using reserved keywords as variable names
- Forgetting to initialize variables

### Key Takeaways
- **Variables store data**: They hold values in memory
- **Names matter**: Use descriptive names
- **Types are dynamic**: Python infers types automatically
"""


@pytest.fixture
def qa_output():
    """Return a sample Q&A output."""
    return """Great question! 🎉

Variables in Python don't require explicit type declarations because
Python uses **dynamic typing**. This means the type is determined
at runtime based on the value assigned.

```python
x = 5      # x is an integer
x = "hi"   # now x is a string
```

This makes Python more flexible but requires careful attention to
what values you're working with.

Keep exploring! Feel free to ask more questions. 🚀
"""


@pytest.fixture
def mock_agents_config():
    """Return mock agents configuration."""
    return {
        "knowledge_teacher": {
            "role": "Knowledge Teacher",
            "goal": "Create engaging lessons",
            "backstory": "Expert educator",
            "llm": "anthropic/claude-opus-4-5-20251101",
        },
        "qa_mentor": {
            "role": "Q&A Mentor",
            "goal": "Answer questions helpfully",
            "backstory": "Patient mentor",
            "llm": "openai/gpt-5.2",
        },
    }


@pytest.fixture
def mock_tasks_config():
    """Return mock tasks configuration."""
    return {
        "teach_concept_task": {
            "description": "Teach {concept_title}",
            "expected_output": "A markdown lesson",
        },
        "answer_question_task": {
            "description": "Answer: {question}",
            "expected_output": "A helpful answer",
        },
    }


# ==================== TEST: INITIALIZATION ====================


class TestTeachingCrewInit:
    """Tests for TeachingCrew initialization."""
    
    def test_init_loads_configs(self, mock_agents_config, mock_tasks_config):
        """Should load configurations on init."""
        with patch.object(
            TeachingCrew, '_load_yaml',
            side_effect=[mock_agents_config, mock_tasks_config]
        ):
            crew = TeachingCrew()
            
            assert crew._agents_config == mock_agents_config
            assert crew._tasks_config == mock_tasks_config
    
    def test_init_sets_config_dir(self, mock_agents_config, mock_tasks_config):
        """Should set config directory path."""
        with patch.object(
            TeachingCrew, '_load_yaml',
            side_effect=[mock_agents_config, mock_tasks_config]
        ):
            crew = TeachingCrew()
            
            assert crew._config_dir.name == "config"


# ==================== TEST: TEACH CONCEPT ====================


class TestTeachingCrewTeachConcept:
    """Tests for TeachingCrew.teach_concept()."""
    
    def test_teach_concept_returns_lesson(
        self, mock_agents_config, mock_tasks_config, sample_concept, lesson_output
    ):
        """Should return lesson content as string."""
        with patch.object(
            TeachingCrew, '_load_yaml',
            side_effect=[mock_agents_config, mock_tasks_config]
        ):
            crew = TeachingCrew()
        
        with patch.object(crew, '_create_teaching_crew') as mock_create_crew:
            mock_result = MagicMock()
            mock_result.raw = lesson_output
            mock_crew_instance = MagicMock()
            mock_crew_instance.kickoff.return_value = mock_result
            mock_create_crew.return_value = mock_crew_instance
            
            result = crew.teach_concept(sample_concept)
            
            assert isinstance(result, str)
            assert "Variables" in result
    
    def test_teach_concept_passes_inputs(
        self, mock_agents_config, mock_tasks_config, sample_concept,
        sample_user_prefs, lesson_output
    ):
        """Should pass correct inputs to crew."""
        with patch.object(
            TeachingCrew, '_load_yaml',
            side_effect=[mock_agents_config, mock_tasks_config]
        ):
            crew = TeachingCrew()
        
        with patch.object(crew, '_create_teaching_crew') as mock_create_crew:
            mock_result = MagicMock()
            mock_result.raw = lesson_output
            mock_crew_instance = MagicMock()
            mock_crew_instance.kickoff.return_value = mock_result
            mock_create_crew.return_value = mock_crew_instance
            
            crew.teach_concept(
                concept=sample_concept,
                user_prefs=sample_user_prefs,
                module_title="Python Basics",
                previous_struggles="Had trouble with data types",
            )
            
            call_args = mock_crew_instance.kickoff.call_args
            inputs = call_args.kwargs.get("inputs", {})
            
            assert inputs["concept_title"] == "Variables in Python"
            assert inputs["module_title"] == "Python Basics"
            assert "Visual" in inputs["learning_style"]
    
    def test_teach_concept_raises_for_none_concept(
        self, mock_agents_config, mock_tasks_config
    ):
        """Should raise ValueError for None concept."""
        with patch.object(
            TeachingCrew, '_load_yaml',
            side_effect=[mock_agents_config, mock_tasks_config]
        ):
            crew = TeachingCrew()
        
        with pytest.raises(ValueError, match="Concept cannot be None"):
            crew.teach_concept(None)
    
    def test_teach_concept_raises_for_empty_title(
        self, mock_agents_config, mock_tasks_config
    ):
        """Should raise ValueError for concept with empty/whitespace title."""
        with patch.object(
            TeachingCrew, '_load_yaml',
            side_effect=[mock_agents_config, mock_tasks_config]
        ):
            crew = TeachingCrew()
        
        # Create concept, then manually set title to whitespace to test validation
        concept = Concept(title="Temp", content="Some content")
        concept.title = "   "  # Set to whitespace after creation
        
        with pytest.raises(ValueError, match="Concept must have a title"):
            crew.teach_concept(concept)
    
    def test_teach_concept_validates_title_not_whitespace(
        self, mock_agents_config, mock_tasks_config
    ):
        """Should raise ValueError for concept with whitespace-only title."""
        with patch.object(
            TeachingCrew, '_load_yaml',
            side_effect=[mock_agents_config, mock_tasks_config]
        ):
            crew = TeachingCrew()
        
        # Create valid concept then modify title to test the validation logic
        concept = Concept(title="ValidTitle", content="Some content")
        # Manually set title to whitespace to bypass Pydantic initial validation
        object.__setattr__(concept, 'title', "   ")
        
        with pytest.raises(ValueError, match="Concept must have a title"):
            crew.teach_concept(concept)
    
    def test_teach_concept_default_user_prefs(
        self, mock_agents_config, mock_tasks_config, sample_concept, lesson_output
    ):
        """Should use default preferences when not provided."""
        with patch.object(
            TeachingCrew, '_load_yaml',
            side_effect=[mock_agents_config, mock_tasks_config]
        ):
            crew = TeachingCrew()
        
        with patch.object(crew, '_create_teaching_crew') as mock_create_crew:
            mock_result = MagicMock()
            mock_result.raw = lesson_output
            mock_crew_instance = MagicMock()
            mock_crew_instance.kickoff.return_value = mock_result
            mock_create_crew.return_value = mock_crew_instance
            
            crew.teach_concept(sample_concept, user_prefs=None)
            
            call_args = mock_crew_instance.kickoff.call_args
            inputs = call_args.kwargs.get("inputs", {})
            
            # Default is beginner and reading style
            assert "Beginner" in inputs["experience_level"]
    
    def test_teach_concept_default_module_title(
        self, mock_agents_config, mock_tasks_config, sample_concept, lesson_output
    ):
        """Should use default module title when not provided."""
        with patch.object(
            TeachingCrew, '_load_yaml',
            side_effect=[mock_agents_config, mock_tasks_config]
        ):
            crew = TeachingCrew()
        
        with patch.object(crew, '_create_teaching_crew') as mock_create_crew:
            mock_result = MagicMock()
            mock_result.raw = lesson_output
            mock_crew_instance = MagicMock()
            mock_crew_instance.kickoff.return_value = mock_result
            mock_create_crew.return_value = mock_crew_instance
            
            crew.teach_concept(sample_concept, module_title="")
            
            call_args = mock_crew_instance.kickoff.call_args
            inputs = call_args.kwargs.get("inputs", {})
            
            assert inputs["module_title"] == "Current Module"
    
    def test_teach_concept_no_content(
        self, mock_agents_config, mock_tasks_config, lesson_output
    ):
        """Should handle concept with no content."""
        with patch.object(
            TeachingCrew, '_load_yaml',
            side_effect=[mock_agents_config, mock_tasks_config]
        ):
            crew = TeachingCrew()
        
        with patch.object(crew, '_create_teaching_crew') as mock_create_crew:
            mock_result = MagicMock()
            mock_result.raw = lesson_output
            mock_crew_instance = MagicMock()
            mock_crew_instance.kickoff.return_value = mock_result
            mock_create_crew.return_value = mock_crew_instance
            
            concept = Concept(title="Test Concept", content="")
            crew.teach_concept(concept)
            
            call_args = mock_crew_instance.kickoff.call_args
            inputs = call_args.kwargs.get("inputs", {})
            
            assert inputs["concept_content"] == "No additional content provided."


# ==================== TEST: ANSWER QUESTION ====================


class TestTeachingCrewAnswerQuestion:
    """Tests for TeachingCrew.answer_question()."""
    
    def test_answer_question_returns_answer(
        self, mock_agents_config, mock_tasks_config, sample_concept, qa_output
    ):
        """Should return answer as string."""
        with patch.object(
            TeachingCrew, '_load_yaml',
            side_effect=[mock_agents_config, mock_tasks_config]
        ):
            crew = TeachingCrew()
        
        with patch.object(crew, '_create_teaching_crew') as mock_create_crew:
            mock_result = MagicMock()
            mock_result.raw = qa_output
            mock_crew_instance = MagicMock()
            mock_crew_instance.kickoff.return_value = mock_result
            mock_create_crew.return_value = mock_crew_instance
            
            result = crew.answer_question("Why is Python dynamically typed?", sample_concept)
            
            assert isinstance(result, str)
            assert "dynamic" in result.lower()
    
    def test_answer_question_passes_inputs(
        self, mock_agents_config, mock_tasks_config, sample_concept,
        sample_user_prefs, qa_output
    ):
        """Should pass correct inputs to crew."""
        with patch.object(
            TeachingCrew, '_load_yaml',
            side_effect=[mock_agents_config, mock_tasks_config]
        ):
            crew = TeachingCrew()
        
        with patch.object(crew, '_create_teaching_crew') as mock_create_crew:
            mock_result = MagicMock()
            mock_result.raw = qa_output
            mock_crew_instance = MagicMock()
            mock_crew_instance.kickoff.return_value = mock_result
            mock_create_crew.return_value = mock_crew_instance
            
            chat_history = [
                {"role": "user", "content": "What is a variable?"},
                {"role": "assistant", "content": "A variable stores data."},
            ]
            
            crew.answer_question(
                question="Why dynamic typing?",
                concept=sample_concept,
                lesson_content="Lesson about variables",
                chat_history=chat_history,
                user_prefs=sample_user_prefs,
            )
            
            call_args = mock_crew_instance.kickoff.call_args
            inputs = call_args.kwargs.get("inputs", {})
            
            assert inputs["question"] == "Why dynamic typing?"
            assert inputs["concept_title"] == "Variables in Python"
            assert inputs["lesson_content"] == "Lesson about variables"
    
    def test_answer_question_raises_for_empty_question(
        self, mock_agents_config, mock_tasks_config, sample_concept
    ):
        """Should raise ValueError for empty question."""
        with patch.object(
            TeachingCrew, '_load_yaml',
            side_effect=[mock_agents_config, mock_tasks_config]
        ):
            crew = TeachingCrew()
        
        with pytest.raises(ValueError, match="Question cannot be empty"):
            crew.answer_question("", sample_concept)
    
    def test_answer_question_raises_for_whitespace_question(
        self, mock_agents_config, mock_tasks_config, sample_concept
    ):
        """Should raise ValueError for whitespace-only question."""
        with patch.object(
            TeachingCrew, '_load_yaml',
            side_effect=[mock_agents_config, mock_tasks_config]
        ):
            crew = TeachingCrew()
        
        with pytest.raises(ValueError, match="Question cannot be empty"):
            crew.answer_question("   ", sample_concept)
    
    def test_answer_question_raises_for_none_concept(
        self, mock_agents_config, mock_tasks_config
    ):
        """Should raise ValueError for None concept."""
        with patch.object(
            TeachingCrew, '_load_yaml',
            side_effect=[mock_agents_config, mock_tasks_config]
        ):
            crew = TeachingCrew()
        
        with pytest.raises(ValueError, match="Concept cannot be None"):
            crew.answer_question("What is a variable?", None)
    
    def test_answer_question_default_chat_history(
        self, mock_agents_config, mock_tasks_config, sample_concept, qa_output
    ):
        """Should handle empty chat history."""
        with patch.object(
            TeachingCrew, '_load_yaml',
            side_effect=[mock_agents_config, mock_tasks_config]
        ):
            crew = TeachingCrew()
        
        with patch.object(crew, '_create_teaching_crew') as mock_create_crew:
            mock_result = MagicMock()
            mock_result.raw = qa_output
            mock_crew_instance = MagicMock()
            mock_crew_instance.kickoff.return_value = mock_result
            mock_create_crew.return_value = mock_crew_instance
            
            crew.answer_question("Question?", sample_concept, chat_history=None)
            
            call_args = mock_crew_instance.kickoff.call_args
            inputs = call_args.kwargs.get("inputs", {})
            
            # format_chat_history returns "No previous questions in this session."
            assert "No previous questions" in inputs["chat_history"]
    
    def test_answer_question_default_lesson_content(
        self, mock_agents_config, mock_tasks_config, sample_concept, qa_output
    ):
        """Should use default when no lesson content."""
        with patch.object(
            TeachingCrew, '_load_yaml',
            side_effect=[mock_agents_config, mock_tasks_config]
        ):
            crew = TeachingCrew()
        
        with patch.object(crew, '_create_teaching_crew') as mock_create_crew:
            mock_result = MagicMock()
            mock_result.raw = qa_output
            mock_crew_instance = MagicMock()
            mock_crew_instance.kickoff.return_value = mock_result
            mock_create_crew.return_value = mock_crew_instance
            
            crew.answer_question("Question?", sample_concept, lesson_content="")
            
            call_args = mock_crew_instance.kickoff.call_args
            inputs = call_args.kwargs.get("inputs", {})
            
            assert inputs["lesson_content"] == "No lesson content available."
    
    def test_answer_question_strips_question(
        self, mock_agents_config, mock_tasks_config, sample_concept, qa_output
    ):
        """Should strip whitespace from question."""
        with patch.object(
            TeachingCrew, '_load_yaml',
            side_effect=[mock_agents_config, mock_tasks_config]
        ):
            crew = TeachingCrew()
        
        with patch.object(crew, '_create_teaching_crew') as mock_create_crew:
            mock_result = MagicMock()
            mock_result.raw = qa_output
            mock_crew_instance = MagicMock()
            mock_crew_instance.kickoff.return_value = mock_result
            mock_create_crew.return_value = mock_crew_instance
            
            crew.answer_question("  What is this?  ", sample_concept)
            
            call_args = mock_crew_instance.kickoff.call_args
            inputs = call_args.kwargs.get("inputs", {})
            
            assert inputs["question"] == "What is this?"


# ==================== TEST: CREW CREATION ====================


class TestTeachingCrewCreation:
    """Tests for crew and agent creation methods."""
    
    def test_create_knowledge_teacher(
        self, mock_agents_config, mock_tasks_config
    ):
        """Should create knowledge teacher agent with config."""
        with patch.object(
            TeachingCrew, '_load_yaml',
            side_effect=[mock_agents_config, mock_tasks_config]
        ):
            crew = TeachingCrew()
        
        # Patch at the module where it's used (teaching_crew.py imports Agent from crewai)
        with patch('sensei.crews.teaching_crew.teaching_crew.Agent') as mock_agent:
            crew._create_knowledge_teacher()
            
            mock_agent.assert_called_once()
            call_kwargs = mock_agent.call_args.kwargs
            assert call_kwargs["config"] == mock_agents_config["knowledge_teacher"]
            assert call_kwargs["verbose"] is True
    
    def test_create_qa_mentor(
        self, mock_agents_config, mock_tasks_config
    ):
        """Should create Q&A mentor agent with config."""
        with patch.object(
            TeachingCrew, '_load_yaml',
            side_effect=[mock_agents_config, mock_tasks_config]
        ):
            crew = TeachingCrew()
        
        with patch('sensei.crews.teaching_crew.teaching_crew.Agent') as mock_agent:
            crew._create_qa_mentor()
            
            mock_agent.assert_called_once()
            call_kwargs = mock_agent.call_args.kwargs
            assert call_kwargs["config"] == mock_agents_config["qa_mentor"]
    
    def test_create_teaching_crew_uses_memory(
        self, mock_agents_config, mock_tasks_config
    ):
        """Should create crew with memory enabled."""
        with patch.object(
            TeachingCrew, '_load_yaml',
            side_effect=[mock_agents_config, mock_tasks_config]
        ):
            crew_instance = TeachingCrew()
        
        with patch('sensei.crews.teaching_crew.teaching_crew.Crew') as mock_crew:
            mock_agent = MagicMock()
            mock_task = MagicMock()
            
            crew_instance._create_teaching_crew(mock_agent, mock_task)
            
            call_kwargs = mock_crew.call_args.kwargs
            assert call_kwargs["memory"] is True
            assert call_kwargs["verbose"] is True


# ==================== TEST: EDGE CASES ====================


class TestTeachingCrewEdgeCases:
    """Edge case tests for TeachingCrew."""
    
    def test_unicode_in_concept(
        self, mock_agents_config, mock_tasks_config, lesson_output
    ):
        """Should handle unicode in concept."""
        with patch.object(
            TeachingCrew, '_load_yaml',
            side_effect=[mock_agents_config, mock_tasks_config]
        ):
            crew = TeachingCrew()
        
        with patch.object(crew, '_create_teaching_crew') as mock_create_crew:
            mock_result = MagicMock()
            mock_result.raw = lesson_output
            mock_crew_instance = MagicMock()
            mock_crew_instance.kickoff.return_value = mock_result
            mock_create_crew.return_value = mock_crew_instance
            
            concept = Concept(
                title="变量与类型",
                content="Python中的变量是动态类型的。🐍"
            )
            
            result = crew.teach_concept(concept)
            
            assert isinstance(result, str)
    
    def test_long_question(
        self, mock_agents_config, mock_tasks_config, sample_concept, qa_output
    ):
        """Should handle long questions."""
        with patch.object(
            TeachingCrew, '_load_yaml',
            side_effect=[mock_agents_config, mock_tasks_config]
        ):
            crew = TeachingCrew()
        
        with patch.object(crew, '_create_teaching_crew') as mock_create_crew:
            mock_result = MagicMock()
            mock_result.raw = qa_output
            mock_crew_instance = MagicMock()
            mock_crew_instance.kickoff.return_value = mock_result
            mock_create_crew.return_value = mock_crew_instance
            
            long_question = "Why is it that " + "when I " * 100 + "use variables?"
            
            result = crew.answer_question(long_question, sample_concept)
            
            assert isinstance(result, str)
    
    def test_special_characters_in_question(
        self, mock_agents_config, mock_tasks_config, sample_concept, qa_output
    ):
        """Should handle special characters in question."""
        with patch.object(
            TeachingCrew, '_load_yaml',
            side_effect=[mock_agents_config, mock_tasks_config]
        ):
            crew = TeachingCrew()
        
        with patch.object(crew, '_create_teaching_crew') as mock_create_crew:
            mock_result = MagicMock()
            mock_result.raw = qa_output
            mock_crew_instance = MagicMock()
            mock_crew_instance.kickoff.return_value = mock_result
            mock_create_crew.return_value = mock_crew_instance
            
            result = crew.answer_question(
                "What does `x += 1` mean? Is it the same as x = x + 1?",
                sample_concept
            )
            
            assert isinstance(result, str)
    
    def test_all_learning_styles(
        self, mock_agents_config, mock_tasks_config, sample_concept, lesson_output
    ):
        """Should handle all learning styles."""
        for style in LearningStyle:
            with patch.object(
                TeachingCrew, '_load_yaml',
                side_effect=[mock_agents_config, mock_tasks_config]
            ):
                crew = TeachingCrew()
            
            with patch.object(crew, '_create_teaching_crew') as mock_create_crew:
                mock_result = MagicMock()
                mock_result.raw = lesson_output
                mock_crew_instance = MagicMock()
                mock_crew_instance.kickoff.return_value = mock_result
                mock_create_crew.return_value = mock_crew_instance
                
                user_prefs = UserPreferences(learning_style=style)
                result = crew.teach_concept(sample_concept, user_prefs)
                
                assert isinstance(result, str)
    
    def test_large_chat_history(
        self, mock_agents_config, mock_tasks_config, sample_concept, qa_output
    ):
        """Should handle large chat history."""
        with patch.object(
            TeachingCrew, '_load_yaml',
            side_effect=[mock_agents_config, mock_tasks_config]
        ):
            crew = TeachingCrew()
        
        with patch.object(crew, '_create_teaching_crew') as mock_create_crew:
            mock_result = MagicMock()
            mock_result.raw = qa_output
            mock_crew_instance = MagicMock()
            mock_crew_instance.kickoff.return_value = mock_result
            mock_create_crew.return_value = mock_crew_instance
            
            # Create large chat history
            chat_history = [
                {"role": "user" if i % 2 == 0 else "assistant", "content": f"Message {i}"}
                for i in range(50)
            ]
            
            result = crew.answer_question(
                "Next question?",
                sample_concept,
                chat_history=chat_history
            )
            
            assert isinstance(result, str)
