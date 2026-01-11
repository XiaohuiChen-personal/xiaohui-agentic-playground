# 🥋 Sensei - Implementation Planning Document

> **Version:** 1.0  
> **Last Updated:** January 2026  
> **Status:** Planning Phase

---

## Table of Contents

1. [Overview](#1-overview)
2. [Milestone Summary](#2-milestone-summary)
3. [Milestone 1: Project Foundation](#3-milestone-1-project-foundation)
4. [Milestone 2: Storage Layer](#4-milestone-2-storage-layer)
5. [Milestone 3: Data Models & Schemas](#5-milestone-3-data-models--schemas)
6. [Milestone 4: Service Layer (No AI)](#6-milestone-4-service-layer-no-ai)
7. [Milestone 5: CrewAI Crews](#7-milestone-5-crewai-crews)
8. [Milestone 6: Service-Crew Integration](#8-milestone-6-service-crew-integration)
9. [Milestone 7: UI Components](#9-milestone-7-ui-components)
10. [Milestone 8: UI Pages](#10-milestone-8-ui-pages)
11. [Milestone 9: End-to-End Integration](#11-milestone-9-end-to-end-integration)
12. [Milestone 10: Polish & Documentation](#12-milestone-10-polish--documentation)
13. [Testing Strategy](#13-testing-strategy)
14. [Risk & Dependencies](#14-risk--dependencies)

---

## 1. Overview

This document breaks down the Sensei implementation into **10 milestones** with testable subtasks. Each subtask is designed to be independently verifiable through unit tests, integration tests, and where applicable, functional tests.

### Guiding Principles

| Principle | Description |
|-----------|-------------|
| **Bottom-Up** | Build foundational layers first (models → storage → services → crews → UI) |
| **Testable Increments** | Each subtask produces testable code |
| **Mock Dependencies** | Use mocks for untested dependencies during development |
| **Integration Points** | Explicit integration testing at layer boundaries |
| **Functional Verification** | Dedicated tests with real LLM to verify AI output quality |

### Test Type Definitions

| Test Type | Description | LLM Mocked? |
|-----------|-------------|-------------|
| **Unit** | Tests single function/class in isolation | ✅ Yes |
| **Integration** | Tests multiple components working together | ✅ Yes |
| **Functional** | Tests AI output quality with real LLM calls | ❌ No (Real API) |
| **E2E** | Tests complete user flows through the application | ❌ No (Real API) |
| **Manual** | Visual/UX verification requiring human judgment | N/A |

---

## 2. Milestone Summary

| Milestone | Name | Subtasks | Est. Effort | Dependencies |
|-----------|------|----------|-------------|--------------|
| **M1** | Project Foundation | 4 | 2 hours | None |
| **M2** | Storage Layer | 3 | 4 hours | M1 |
| **M3** | Data Models & Schemas | 4 | 3 hours | M1 |
| **M4** | Service Layer (No AI) | 5 | 6 hours | M2, M3 |
| **M5** | CrewAI Crews | 6 | 8 hours | M3 |
| **M6** | Service-Crew Integration | 4 | 6 hours | M4, M5 |
| **M7** | UI Components | 5 | 5 hours | M3 |
| **M8** | UI Pages | 7 | 8 hours | M4, M7 |
| **M9** | End-to-End Integration | 4 | 6 hours | M6, M8 |
| **M10** | Polish & Documentation | 4 | 4 hours | M9 |

**Total Estimated Effort: ~52 hours**

---

## 3. Milestone 1: Project Foundation

### Objective
Set up the project structure, dependencies, and basic configuration.

---

### Subtask 1.1: Initialize Project Structure

**Description:**  
Create the project directory structure as defined in `PROPOSED_FILE_ARCHITECTURE.md`. Set up `pyproject.toml` with all required dependencies.

**Deliverables:**
- Complete directory structure with empty `__init__.py` files
- `pyproject.toml` with dependencies (crewai, streamlit, pydantic, etc.)
- `.gitignore` for data directory

**Test Plan:**

| Test Type | Test Case | Expected Result |
|-----------|-----------|-----------------|
| Unit | Import `sensei` package | No import errors |
| Unit | Verify directory structure exists | All directories present |
| Integration | Run `uv sync` | Dependencies installed successfully |

---

### Subtask 1.2: Create Utility Constants

**Description:**  
Implement `utils/constants.py` with application-wide constants (paths, defaults, thresholds).

**Deliverables:**
- `DATA_DIR` path constant
- `COURSES_DIR` path constant
- `DATABASE_PATH` constant
- `DEFAULT_SESSION_LENGTH` constant
- `QUIZ_PASS_THRESHOLD` constant (0.8)

**Test Plan:**

| Test Type | Test Case | Expected Result |
|-----------|-----------|-----------------|
| Unit | Access `DATA_DIR` constant | Returns valid path string |
| Unit | Access `QUIZ_PASS_THRESHOLD` | Returns 0.8 |
| Unit | Constants are immutable | Cannot reassign values |

---

### Subtask 1.3: Create Session State Utilities

**Description:**  
Implement `utils/state.py` with helpers for Streamlit session state management.

**Deliverables:**
- `initialize_session_state()` function
- `get_state(key, default)` function
- `set_state(key, value)` function
- `clear_state(key)` function

**Test Plan:**

| Test Type | Test Case | Expected Result |
|-----------|-----------|-----------------|
| Unit | `get_state` with default | Returns default when key missing |
| Unit | `set_state` then `get_state` | Returns set value |
| Unit | `clear_state` removes key | Key no longer exists |
| Unit | `initialize_session_state` sets defaults | All default keys present |

---

### Subtask 1.4: Create Display Formatters

**Description:**  
Implement `utils/formatters.py` with display formatting utilities.

**Deliverables:**
- `format_duration(minutes)` → "1h 30m"
- `format_percentage(value)` → "75%"
- `format_date(datetime)` → "Jan 10, 2026"
- `truncate_text(text, max_length)` → "Text..."

**Test Plan:**

| Test Type | Test Case | Expected Result |
|-----------|-----------|-----------------|
| Unit | `format_duration(90)` | "1h 30m" |
| Unit | `format_duration(45)` | "45m" |
| Unit | `format_percentage(0.75)` | "75%" |
| Unit | `format_date` with datetime | Formatted string |
| Unit | `truncate_text` long text | Truncated with "..." |
| Unit | `truncate_text` short text | Original text |

---

## 4. Milestone 2: Storage Layer

### Objective
Implement data persistence layer for SQLite and JSON file storage.

---

### Subtask 2.1: Implement Database Operations

**Description:**  
Implement `storage/database.py` with SQLite operations for progress tracking and quiz results.

**Deliverables:**
- `Database` class with connection management
- `initialize_tables()` - Create schema
- `save_progress(progress)` - Insert/update progress
- `get_progress(course_id)` - Retrieve progress
- `save_quiz_result(result)` - Insert quiz result
- `get_quiz_history(course_id)` - Retrieve quiz history
- `get_all_progress()` - List all progress records

**Test Plan:**

| Test Type | Test Case | Expected Result |
|-----------|-----------|-----------------|
| Unit | `initialize_tables` creates schema | Tables exist in DB |
| Unit | `save_progress` new record | Record inserted |
| Unit | `save_progress` existing record | Record updated |
| Unit | `get_progress` existing | Returns progress dict |
| Unit | `get_progress` non-existing | Returns None |
| Unit | `save_quiz_result` | Record inserted with timestamp |
| Unit | `get_quiz_history` | Returns list sorted by date |
| Integration | Full CRUD cycle | Data persists across operations |

---

### Subtask 2.2: Implement File Storage Operations

**Description:**  
Implement `storage/file_storage.py` with JSON file operations for courses and user preferences.

**Deliverables:**
- `save_course(course)` - Save course to JSON
- `load_course(course_id)` - Load course from JSON
- `list_courses()` - List all course files
- `delete_course(course_id)` - Remove course file
- `save_user_preferences(prefs)` - Save user prefs
- `load_user_preferences()` - Load user prefs
- `ensure_data_directories()` - Create data dirs if missing

**Test Plan:**

| Test Type | Test Case | Expected Result |
|-----------|-----------|-----------------|
| Unit | `save_course` creates file | JSON file exists |
| Unit | `load_course` existing | Returns course dict |
| Unit | `load_course` non-existing | Returns None |
| Unit | `list_courses` with files | Returns list of IDs |
| Unit | `list_courses` empty dir | Returns empty list |
| Unit | `delete_course` | File removed |
| Unit | `save_user_preferences` | JSON file created |
| Unit | `load_user_preferences` missing | Returns defaults |
| Integration | Save then load course | Data integrity maintained |

---

### Subtask 2.3: Implement Memory Manager

**Description:**  
Implement `storage/memory_manager.py` with CrewAI memory configuration.

**Deliverables:**
- `get_memory_config()` - Returns CrewAI memory settings
- `get_short_term_memory()` - Configure STM
- `get_long_term_memory()` - Configure LTM with SQLite
- `get_entity_memory()` - Configure entity memory
- `clear_session_memory()` - Clear STM for new session

**Test Plan:**

| Test Type | Test Case | Expected Result |
|-----------|-----------|-----------------|
| Unit | `get_memory_config` returns dict | Valid config structure |
| Unit | Config contains required keys | All memory types present |
| Unit | `clear_session_memory` | STM cleared |
| Integration | Memory config works with CrewAI | No errors on crew init |

---

## 5. Milestone 3: Data Models & Schemas

### Objective
Implement Pydantic models for all data structures.

---

### Subtask 3.1: Implement Enumerations

**Description:**  
Implement `models/enums.py` with all enumeration types.

**Deliverables:**
- `LearningStyle` enum (VISUAL, READING, HANDS_ON)
- `ConceptStatus` enum (NOT_STARTED, IN_PROGRESS, COMPLETED, NEEDS_REVIEW)
- `ExperienceLevel` enum (BEGINNER, INTERMEDIATE, ADVANCED)
- `QuestionType` enum (MULTIPLE_CHOICE, TRUE_FALSE, CODE, OPEN_ENDED)

**Test Plan:**

| Test Type | Test Case | Expected Result |
|-----------|-----------|-----------------|
| Unit | Access enum values | Valid enum members |
| Unit | Enum serialization | Converts to string |
| Unit | Enum from string | Creates enum from value |
| Unit | Invalid enum value | Raises ValueError |

---

### Subtask 3.2: Implement Core Schemas

**Description:**  
Implement `models/schemas.py` with core Pydantic models for courses.

**Deliverables:**
- `Concept` model (id, title, content, order, status, mastery, questions_asked)
- `Module` model (id, title, description, concepts, order, estimated_minutes)
- `Course` model (id, title, description, modules, created_at, total_concepts)

**Test Plan:**

| Test Type | Test Case | Expected Result |
|-----------|-----------|-----------------|
| Unit | Create valid `Concept` | Instance created |
| Unit | Create `Concept` missing required | ValidationError |
| Unit | Create valid `Module` with concepts | Instance with nested concepts |
| Unit | Create valid `Course` | Instance with nested modules |
| Unit | `Course` to dict | Valid dict representation |
| Unit | `Course` from dict | Valid instance |
| Unit | Default values applied | Defaults set correctly |

---

### Subtask 3.3: Implement Quiz Schemas

**Description:**  
Implement quiz-related Pydantic models.

**Deliverables:**
- `QuizQuestion` model (id, question, options, correct_answer, explanation, concept_id, difficulty)
- `Quiz` model (id, module_id, questions, created_at)
- `QuizResult` model (quiz_id, score, correct_count, total_questions, weak_concepts, feedback, completed_at)
- `AnswerResult` model (question_id, is_correct, correct_answer, explanation)

**Test Plan:**

| Test Type | Test Case | Expected Result |
|-----------|-----------|-----------------|
| Unit | Create `QuizQuestion` | Valid instance |
| Unit | Create `Quiz` with questions | Nested questions valid |
| Unit | Create `QuizResult` | Score between 0-1 |
| Unit | `QuizResult` score validation | Rejects invalid scores |
| Unit | Serialization round-trip | Data integrity maintained |

---

### Subtask 3.4: Implement User & Session Schemas

**Description:**  
Implement user preference and session Pydantic models.

**Deliverables:**
- `UserPreferences` model (name, learning_style, session_length_minutes, experience_level, goals)
- `LearningSession` model (course_id, current_module_idx, current_concept_idx, started_at, chat_history)
- `ChatMessage` model (role, content, timestamp)
- `Progress` model (course_id, completion_percentage, concepts_completed, total_concepts, time_spent_minutes, last_accessed)

**Test Plan:**

| Test Type | Test Case | Expected Result |
|-----------|-----------|-----------------|
| Unit | Create `UserPreferences` | Valid instance |
| Unit | Default `learning_style` | READING by default |
| Unit | Create `LearningSession` | Valid instance |
| Unit | Add `ChatMessage` to session | Chat history updated |
| Unit | `Progress` percentage validation | Between 0-100 |
| Unit | Serialization to JSON | Valid JSON output |

---

## 6. Milestone 4: Service Layer (No AI)

### Objective
Implement business logic services with storage integration, but without AI crews (use mocks/stubs).

---

### Subtask 4.1: Implement User Service

**Description:**  
Implement `services/user_service.py` for user preference management.

**Deliverables:**
- `UserService` class
- `get_preferences()` → UserPreferences
- `set_preferences(prefs)` → None
- `is_onboarded()` → bool
- `complete_onboarding(prefs)` → None

**Test Plan:**

| Test Type | Test Case | Expected Result |
|-----------|-----------|-----------------|
| Unit | `get_preferences` no file | Returns defaults |
| Unit | `set_preferences` | Saves to file |
| Unit | `get_preferences` after set | Returns saved prefs |
| Unit | `is_onboarded` false | Returns False initially |
| Unit | `complete_onboarding` | Sets onboarded flag |
| Integration | Preferences persist | Data survives restart |

---

### Subtask 4.2: Implement Progress Service

**Description:**  
Implement `services/progress_service.py` for progress tracking.

**Deliverables:**
- `ProgressService` class
- `get_course_progress(course_id)` → Progress
- `update_progress(course_id, concepts_completed)` → None
- `get_all_progress()` → List[Progress]
- `get_learning_stats()` → dict (total courses, concepts, hours)
- `get_quiz_history(course_id)` → List[QuizResult]

**Test Plan:**

| Test Type | Test Case | Expected Result |
|-----------|-----------|-----------------|
| Unit | `get_course_progress` new course | Returns 0% progress |
| Unit | `update_progress` | Progress updated |
| Unit | `get_all_progress` | Returns list |
| Unit | `get_learning_stats` | Returns stats dict |
| Unit | `get_quiz_history` | Returns sorted list |
| Integration | Progress updates persist | Database correctly updated |

---

### Subtask 4.3: Implement Course Service (Stub)

**Description:**  
Implement `services/course_service.py` with stub for curriculum generation.

**Deliverables:**
- `CourseService` class
- `create_course(topic)` → Course (stub returns mock course)
- `list_courses()` → List[Course]
- `get_course(course_id)` → Course
- `delete_course(course_id)` → bool
- `_generate_course_stub(topic)` → Course (for testing)

**Test Plan:**

| Test Type | Test Case | Expected Result |
|-----------|-----------|-----------------|
| Unit | `create_course` with stub | Returns mock course |
| Unit | `list_courses` empty | Returns empty list |
| Unit | `list_courses` with courses | Returns course list |
| Unit | `get_course` existing | Returns course |
| Unit | `get_course` non-existing | Returns None |
| Unit | `delete_course` | Removes course |
| Integration | Create then list | Course appears in list |

---

### Subtask 4.4: Implement Learning Service (Stub)

**Description:**  
Implement `services/learning_service.py` with stub for lesson generation.

**Deliverables:**
- `LearningService` class
- `start_session(course_id)` → LearningSession
- `get_current_concept()` → dict (concept + lesson content)
- `next_concept()` → dict
- `previous_concept()` → dict
- `ask_question(question)` → str (stub response)
- `end_session()` → dict (summary)
- `is_module_complete()` → bool

**Test Plan:**

| Test Type | Test Case | Expected Result |
|-----------|-----------|-----------------|
| Unit | `start_session` | Creates session |
| Unit | `get_current_concept` | Returns concept dict |
| Unit | `next_concept` | Advances index |
| Unit | `next_concept` at end | Returns None or stays |
| Unit | `previous_concept` | Decrements index |
| Unit | `ask_question` stub | Returns stub answer |
| Unit | `is_module_complete` | Correct boolean |
| Integration | Full session flow | Navigate through concepts |

---

### Subtask 4.5: Implement Quiz Service (Stub)

**Description:**  
Implement `services/quiz_service.py` with stub for quiz generation.

**Deliverables:**
- `QuizService` class
- `generate_quiz(module_id)` → Quiz (stub returns mock quiz)
- `submit_answer(question_id, answer)` → AnswerResult
- `get_results()` → QuizResult
- `is_passed()` → bool
- `get_weak_concepts()` → List[str]

**Test Plan:**

| Test Type | Test Case | Expected Result |
|-----------|-----------|-----------------|
| Unit | `generate_quiz` stub | Returns mock quiz |
| Unit | `submit_answer` correct | is_correct = True |
| Unit | `submit_answer` incorrect | is_correct = False |
| Unit | `get_results` | Returns score and feedback |
| Unit | `is_passed` above threshold | Returns True |
| Unit | `is_passed` below threshold | Returns False |
| Unit | `get_weak_concepts` | Returns concept IDs |
| Integration | Complete quiz flow | Results saved to DB |

---

## 7. Milestone 5: CrewAI Crews

### Objective
Implement the three CrewAI crews with agents and tasks.

---

### Subtask 5.1: Implement Curriculum Crew Agents Config

**Description:**  
Create agent configurations for Curriculum Crew in YAML.

**Deliverables:**
- `curriculum_crew/config/agents.yaml` with:
  - `curriculum_architect` agent definition
  - `content_researcher` agent definition

**Test Plan:**

| Test Type | Test Case | Expected Result |
|-----------|-----------|-----------------|
| Unit | YAML is valid | Parses without error |
| Unit | Required fields present | role, goal, backstory exist |
| Unit | Agent names match expected | curriculum_architect, content_researcher |

---

### Subtask 5.2: Implement Curriculum Crew Tasks Config

**Description:**  
Create task configurations for Curriculum Crew in YAML.

**Deliverables:**
- `curriculum_crew/config/tasks.yaml` with:
  - `plan_curriculum_task` definition
  - `research_content_task` definition

**Test Plan:**

| Test Type | Test Case | Expected Result |
|-----------|-----------|-----------------|
| Unit | YAML is valid | Parses without error |
| Unit | Required fields present | description, expected_output, agent |
| Unit | Agent references valid | Match agent names |

---

### Subtask 5.3: Implement Curriculum Crew Class

**Description:**  
Implement `curriculum_crew/curriculum_crew.py` crew class.

**Deliverables:**
- `CurriculumCrew` class
- `__init__()` - Load configs, create agents
- `create_curriculum(topic, user_prefs)` → Course
- Agent and task creation methods

**Test Plan:**

| Test Type | Test Case | Expected Result |
|-----------|-----------|-----------------|
| Unit | Instantiate crew | No errors |
| Unit | Agents created | 2 agents exist |
| Unit | Tasks created | 2 tasks exist |
| Integration | `create_curriculum` | Returns valid Course (mocked LLM) |
| Integration | Output structure valid | Course has modules and concepts |

---

### Subtask 5.4: Implement Teaching Crew

**Description:**  
Implement Teaching Crew with agents, tasks, and crew class.

**Deliverables:**
- `teaching_crew/config/agents.yaml` (knowledge_teacher, qa_mentor)
- `teaching_crew/config/tasks.yaml` (teach_concept_task, answer_question_task)
- `teaching_crew/teaching_crew.py` with:
  - `TeachingCrew` class
  - `teach_concept(concept, user_prefs)` → str (lesson)
  - `answer_question(question, context)` → str (answer)

**Test Plan:**

| Test Type | Test Case | Expected Result |
|-----------|-----------|-----------------|
| Unit | YAML configs valid | Parse without error |
| Unit | Instantiate crew | No errors |
| Unit | Agents created | 2 agents exist |
| Integration | `teach_concept` | Returns markdown lesson |
| Integration | `answer_question` | Returns answer string |

---

### Subtask 5.5: Implement Assessment Crew

**Description:**  
Implement Assessment Crew with agents, tasks, and crew class.

**Deliverables:**
- `assessment_crew/config/agents.yaml` (quiz_designer, performance_analyst)
- `assessment_crew/config/tasks.yaml` (generate_quiz_task, evaluate_quiz_task)
- `assessment_crew/assessment_crew.py` with:
  - `AssessmentCrew` class
  - `generate_quiz(module, weak_concepts)` → Quiz
  - `evaluate_answers(quiz, answers)` → QuizResult

**Test Plan:**

| Test Type | Test Case | Expected Result |
|-----------|-----------|-----------------|
| Unit | YAML configs valid | Parse without error |
| Unit | Instantiate crew | No errors |
| Unit | Agents created | 2 agents exist |
| Integration | `generate_quiz` | Returns valid Quiz |
| Integration | `evaluate_answers` | Returns QuizResult |

---

### Subtask 5.6: Implement Crew Unit Tests with Mocked LLM

**Description:**  
Create comprehensive unit tests for all crews using mocked LLM responses.

**Deliverables:**
- `tests/test_crews/test_curriculum_crew.py`
- `tests/test_crews/test_teaching_crew.py`
- `tests/test_crews/test_assessment_crew.py`
- Mock LLM fixtures for predictable outputs

**Test Plan:**

| Test Type | Test Case | Expected Result |
|-----------|-----------|-----------------|
| Unit | Mocked curriculum generation | Returns expected structure |
| Unit | Mocked lesson generation | Returns markdown |
| Unit | Mocked quiz generation | Returns Quiz with questions |
| Unit | Mocked evaluation | Returns correct scores |

---

## 8. Milestone 6: Service-Crew Integration

### Objective
Replace service stubs with actual CrewAI crew calls.

---

### Subtask 6.1: Integrate Course Service with Curriculum Crew

**Description:**  
Update `CourseService` to use `CurriculumCrew` for course generation.

**Deliverables:**
- Remove `_generate_course_stub`
- Inject `CurriculumCrew` dependency
- `create_course` calls `CurriculumCrew.create_curriculum`
- Error handling for crew failures

**Test Plan:**

| Test Type | Test Case | Expected Result |
|-----------|-----------|-----------------|
| Unit | `create_course` with mocked crew | Returns Course |
| Unit | Crew failure handling | Raises appropriate error |
| Integration | Full course creation | Course saved to storage |
| Integration | Course structure valid | Modules and concepts present |

---

### Subtask 6.2: Integrate Learning Service with Teaching Crew

**Description:**  
Update `LearningService` to use `TeachingCrew` for lessons and Q&A.

**Deliverables:**
- Inject `TeachingCrew` dependency
- `get_current_concept` calls `TeachingCrew.teach_concept`
- `ask_question` calls `TeachingCrew.answer_question`
- Cache lesson content in session

**Test Plan:**

| Test Type | Test Case | Expected Result |
|-----------|-----------|-----------------|
| Unit | `get_current_concept` with mocked crew | Returns lesson |
| Unit | `ask_question` with mocked crew | Returns answer |
| Unit | Lesson caching | Same lesson on re-request |
| Integration | Full session with crews | Lessons generated correctly |

---

### Subtask 6.3: Integrate Quiz Service with Assessment Crew

**Description:**  
Update `QuizService` to use `AssessmentCrew` for quiz generation and evaluation.

**Deliverables:**
- Inject `AssessmentCrew` dependency
- `generate_quiz` calls `AssessmentCrew.generate_quiz`
- `get_results` calls `AssessmentCrew.evaluate_answers`
- Save results to database

**Test Plan:**

| Test Type | Test Case | Expected Result |
|-----------|-----------|-----------------|
| Unit | `generate_quiz` with mocked crew | Returns Quiz |
| Unit | `get_results` with mocked crew | Returns QuizResult |
| Integration | Full quiz flow | Results saved correctly |
| Integration | Weak concepts identified | Correct concepts flagged |

---

### Subtask 6.4: Functional Tests with Real LLM

**Description:**  
Create functional tests that call actual LLM APIs to verify AI-generated content quality. These tests are separate from unit/integration tests and should be run manually or in pre-release.

> ⚠️ **Note:** Functional tests incur real API costs and are non-deterministic. They should be run sparingly and results evaluated qualitatively.

**Deliverables:**
- `tests/test_functional/test_curriculum_crew_functional.py`
- `tests/test_functional/test_teaching_crew_functional.py`
- `tests/test_functional/test_assessment_crew_functional.py`
- Test configuration for API keys
- Pytest markers to skip in CI (`@pytest.mark.functional`)

**Test Plan:**

| Test Type | Test Case | Expected Result |
|-----------|-----------|-----------------|
| Functional | Curriculum Crew generates course for "Python Basics" | Course has 5+ modules, each with 3+ concepts |
| Functional | Curriculum Crew generates course for "CUDA C" | Course structure is logical and progressive |
| Functional | Teaching Crew explains "for loops" concept | Lesson contains explanation, code example, key takeaways |
| Functional | Teaching Crew answers "why use loops?" | Answer is relevant, clear, and educational |
| Functional | Assessment Crew generates quiz for module | Quiz has 5+ questions covering module concepts |
| Functional | Assessment Crew evaluates correct answers | Returns high score with positive feedback |
| Functional | Assessment Crew evaluates incorrect answers | Identifies weak concepts correctly |
| Functional | Q&A response is contextually relevant | Answer relates to current lesson topic |
| Functional | Generated content is appropriate length | Not too short (< 100 words) or too long (> 2000 words) |
| Functional | Code examples in lessons are syntactically valid | Code can be parsed without errors |

**Evaluation Criteria (Non-Deterministic):**

Since LLM outputs vary, functional tests should verify:

| Criterion | How to Verify |
|-----------|---------------|
| **Structure** | Output matches expected schema (Course, Quiz, etc.) |
| **Completeness** | Required fields are populated, not empty |
| **Relevance** | Content relates to input topic |
| **Quality** | Content is coherent (manual review) |
| **Safety** | No inappropriate content |

**Running Functional Tests:**

```bash
# Run functional tests only (requires OPENAI_API_KEY)
pytest tests/test_functional/ -v -m functional

# Skip functional tests in CI
pytest --ignore=tests/test_functional/
```

---

## 9. Milestone 7: UI Components

### Objective
Implement reusable Streamlit UI components.

---

### Subtask 7.1: Implement Sidebar Component

**Description:**  
Implement `ui/components/sidebar.py` navigation sidebar.

**Deliverables:**
- `render_sidebar()` function
- Navigation links (Dashboard, New Course, Progress, Settings)
- Current page highlight
- Course outline display (when in learning mode)

**Test Plan:**

| Test Type | Test Case | Expected Result |
|-----------|-----------|-----------------|
| Unit | `render_sidebar` returns None | Renders without error |
| Unit | Navigation items present | All links rendered |
| Unit | Course outline conditionally shown | Only in learning mode |
| Manual | Visual inspection | Correct styling |

---

### Subtask 7.2: Implement Course Card Component

**Description:**  
Implement `ui/components/course_card.py` for course display.

**Deliverables:**
- `render_course_card(course, progress)` function
- Shows course title, description
- Progress bar visualization
- Action buttons (Continue, Review)

**Test Plan:**

| Test Type | Test Case | Expected Result |
|-----------|-----------|-----------------|
| Unit | Render with 0% progress | Shows "Start" button |
| Unit | Render with 50% progress | Shows "Continue" button |
| Unit | Render with 100% progress | Shows "Review" button |
| Unit | Progress bar correct | Percentage matches |

---

### Subtask 7.3: Implement Concept Viewer Component

**Description:**  
Implement `ui/components/concept_viewer.py` for lesson display.

**Deliverables:**
- `render_concept(title, content)` function
- Markdown rendering
- Code syntax highlighting
- Key takeaways section

**Test Plan:**

| Test Type | Test Case | Expected Result |
|-----------|-----------|-----------------|
| Unit | Render markdown content | Renders correctly |
| Unit | Render code blocks | Syntax highlighted |
| Unit | Empty content handling | Shows placeholder |

---

### Subtask 7.4: Implement Chat Interface Component

**Description:**  
Implement `ui/components/chat_interface.py` for Q&A.

**Deliverables:**
- `render_chat(messages, on_send)` function
- Message history display
- Input field with send button
- User/assistant message styling

**Test Plan:**

| Test Type | Test Case | Expected Result |
|-----------|-----------|-----------------|
| Unit | Render empty history | Shows placeholder |
| Unit | Render with messages | All messages displayed |
| Unit | Message roles styled differently | User vs assistant styling |
| Unit | Input field present | Can type and submit |

---

### Subtask 7.5: Implement Quiz Question Component

**Description:**  
Implement `ui/components/quiz_question.py` for quiz display.

**Deliverables:**
- `render_question(question, on_answer)` function
- Question text display
- Multiple choice options
- Submit button
- Feedback display (after answer)

**Test Plan:**

| Test Type | Test Case | Expected Result |
|-----------|-----------|-----------------|
| Unit | Render multiple choice | Options displayed |
| Unit | Option selection | Selected state tracked |
| Unit | Submit calls callback | on_answer invoked |
| Unit | Feedback shown | After submission |

---

## 10. Milestone 8: UI Pages

### Objective
Implement all Streamlit pages using components and services.

---

### Subtask 8.1: Implement Dashboard Page

**Description:**  
Implement `ui/pages/dashboard.py` main dashboard.

**Deliverables:**
- Welcome message with user name
- Quick stats cards (courses, concepts, hours)
- Course list with progress
- "New Course" button

**Test Plan:**

| Test Type | Test Case | Expected Result |
|-----------|-----------|-----------------|
| Unit | Render with no courses | Shows empty state |
| Unit | Render with courses | Course cards displayed |
| Unit | Stats calculated correctly | Accurate numbers |
| Integration | Navigation to New Course | Redirects correctly |

---

### Subtask 8.2: Implement New Course Page

**Description:**  
Implement `ui/pages/new_course.py` for course creation.

**Deliverables:**
- Topic input field
- Generate button
- Loading state with progress
- Course outline preview
- "Start Learning" button

**Test Plan:**

| Test Type | Test Case | Expected Result |
|-----------|-----------|-----------------|
| Unit | Empty input validation | Button disabled |
| Unit | Loading state | Progress indicator shown |
| Unit | Course generated | Outline displayed |
| Integration | Full creation flow | Course saved, redirects |

---

### Subtask 8.3: Implement Learning Page

**Description:**  
Implement `ui/pages/learning.py` for learning sessions.

**Deliverables:**
- Concept viewer with lesson content
- Previous/Next navigation
- Chat interface for Q&A
- "Take Quiz" button at module end
- Progress indicator

**Test Plan:**

| Test Type | Test Case | Expected Result |
|-----------|-----------|-----------------|
| Unit | Load concept content | Lesson displayed |
| Unit | Navigate next | Advances to next concept |
| Unit | Navigate previous | Goes back |
| Unit | Q&A submission | Answer displayed |
| Unit | Module complete | Quiz button shown |
| Integration | Full learning session | Progress updated |

---

### Subtask 8.4: Implement Quiz Page

**Description:**  
Implement `ui/pages/quiz.py` for assessments.

**Deliverables:**
- Quiz question display
- Answer submission
- Question navigation
- Results display
- Pass/Fail messaging
- "Continue" or "Review" options

**Test Plan:**

| Test Type | Test Case | Expected Result |
|-----------|-----------|-----------------|
| Unit | Load quiz | Questions displayed |
| Unit | Submit answer | Feedback shown |
| Unit | Complete quiz | Results page shown |
| Unit | Pass score | Success message |
| Unit | Fail score | Review recommendation |
| Integration | Full quiz flow | Results saved |

---

### Subtask 8.5: Implement Progress Page

**Description:**  
Implement `ui/pages/progress.py` for progress overview.

**Deliverables:**
- Overall stats display
- Per-course progress bars
- Quiz history table
- Weak areas summary

**Test Plan:**

| Test Type | Test Case | Expected Result |
|-----------|-----------|-----------------|
| Unit | Render stats | Correct calculations |
| Unit | Progress bars | Accurate percentages |
| Unit | Quiz history | Sorted by date |
| Unit | Weak areas | Concepts listed |

---

### Subtask 8.6: Implement Settings Page

**Description:**  
Implement `ui/pages/settings.py` for user preferences.

**Deliverables:**
- Name input
- Learning style selector
- Session length selector
- Experience level selector
- Goals text area
- Save button

**Test Plan:**

| Test Type | Test Case | Expected Result |
|-----------|-----------|-----------------|
| Unit | Load existing prefs | Fields populated |
| Unit | Change and save | Preferences updated |
| Unit | Validation | Required fields enforced |
| Integration | Prefs persist | Saved to file |

---

### Subtask 8.7: Implement Onboarding Page

**Description:**  
Implement `ui/pages/onboarding.py` for first-time users.

**Deliverables:**
- Welcome screen
- Step-by-step preference collection
- Progress through steps
- Complete button

**Test Plan:**

| Test Type | Test Case | Expected Result |
|-----------|-----------|-----------------|
| Unit | Show only for new users | Conditional display |
| Unit | Step navigation | Progress through steps |
| Unit | Complete onboarding | Redirects to dashboard |
| Integration | Prefs saved | User marked as onboarded |

---

## 11. Milestone 9: End-to-End Integration

### Objective
Connect all layers and verify complete user flows work correctly.

---

### Subtask 9.1: Main App Entry Point

**Description:**  
Implement `app.py` with routing and initialization.

**Deliverables:**
- Page config setup
- Session state initialization
- Service instantiation
- Page routing logic
- Error handling wrapper

**Test Plan:**

| Test Type | Test Case | Expected Result |
|-----------|-----------|-----------------|
| Unit | App starts without error | No exceptions |
| Unit | Services initialized | All services available |
| Unit | Routing works | Correct page displayed |
| Integration | Full app startup | Dashboard shown |

---

### Subtask 9.2: End-to-End Course Creation Flow

**Description:**  
Test complete flow from topic input to course creation.

**Test Plan:**

| Test Type | Test Case | Expected Result |
|-----------|-----------|-----------------|
| E2E | Enter topic, generate course | Course created and saved |
| E2E | Course appears in dashboard | Listed with 0% progress |
| E2E | Course structure complete | Modules and concepts present |
| E2E | Can start learning | Learning page loads |

---

### Subtask 9.3: End-to-End Learning Flow

**Description:**  
Test complete learning session flow.

**Test Plan:**

| Test Type | Test Case | Expected Result |
|-----------|-----------|-----------------|
| E2E | Start learning session | First concept displayed |
| E2E | Navigate through concepts | All concepts accessible |
| E2E | Ask question | Answer returned |
| E2E | Complete module | Quiz button appears |
| E2E | Progress updates | Dashboard shows progress |

---

### Subtask 9.4: End-to-End Quiz Flow

**Description:**  
Test complete quiz and evaluation flow.

**Test Plan:**

| Test Type | Test Case | Expected Result |
|-----------|-----------|-----------------|
| E2E | Take quiz | Questions displayed |
| E2E | Submit all answers | Results shown |
| E2E | Pass quiz | Next module unlocked |
| E2E | Fail quiz | Review recommended |
| E2E | Quiz history | Saved to progress page |

---

## 12. Milestone 10: Polish & Documentation

### Objective
Final polish, error handling, and documentation.

---

### Subtask 10.1: Error Handling & Edge Cases

**Description:**  
Add comprehensive error handling throughout the application.

**Deliverables:**
- Service error handling
- UI error displays
- Graceful degradation
- Retry logic for AI calls

**Test Plan:**

| Test Type | Test Case | Expected Result |
|-----------|-----------|-----------------|
| Unit | Service throws exception | Caught and handled |
| Unit | AI call fails | User-friendly error |
| Unit | Invalid data | Validation errors shown |
| Integration | Network failure | App remains functional |

---

### Subtask 10.2: Loading States & UX Polish

**Description:**  
Add loading indicators and polish user experience.

**Deliverables:**
- Loading spinners for AI operations
- Progress bars for long operations
- Smooth transitions
- Helpful empty states

**Test Plan:**

| Test Type | Test Case | Expected Result |
|-----------|-----------|-----------------|
| Manual | Course generation | Loading indicator visible |
| Manual | Quiz generation | Progress shown |
| Manual | Empty course list | Helpful message displayed |

---

### Subtask 10.3: README Documentation

**Description:**  
Create comprehensive README with installation and usage instructions.

**Deliverables:**
- Project description
- Installation instructions
- Configuration (API keys)
- Usage guide
- Screenshots
- Troubleshooting

**Test Plan:**

| Test Type | Test Case | Expected Result |
|-----------|-----------|-----------------|
| Manual | Follow install steps | App runs successfully |
| Manual | Follow usage guide | Can complete basic flow |

---

### Subtask 10.4: Final Integration Test Suite

**Description:**  
Create comprehensive integration test suite for CI/CD.

**Deliverables:**
- Automated E2E tests
- Test fixtures and mocks
- CI configuration
- Test coverage report

**Test Plan:**

| Test Type | Test Case | Expected Result |
|-----------|-----------|-----------------|
| Integration | All tests pass | 100% pass rate |
| Integration | Coverage > 80% | Adequate coverage |
| CI | Tests run in CI | No failures |

---

## 13. Testing Strategy

### Test Pyramid

```
                    ┌─────────────┐
                    │    E2E      │  Few, slow, highest confidence
                    │   Tests     │
                    ├─────────────┤
                    │ Functional  │  Few, slow, tests real AI
                    │   Tests     │
                    ├─────────────┤
                    │ Integration │  Some, medium speed
                    │   Tests     │
                    ├─────────────┤
                    │             │
                    │    Unit     │  Many, fast, isolated
                    │   Tests     │
                    │             │
                    └─────────────┘
```

### Test Categories

| Category | Scope | Speed | Mocking | LLM Calls |
|----------|-------|-------|---------|-----------|
| **Unit** | Single function/class | Fast | All dependencies | ❌ Mocked |
| **Integration** | Multiple components | Medium | External only (LLM) | ❌ Mocked |
| **Functional** | Crew + Real LLM | Slow | None for LLM | ✅ Real |
| **E2E** | Full user flow | Slow | Minimal | ✅ Real |

### Key Distinction: Integration vs Functional

| Aspect | Integration Test | Functional Test |
|--------|------------------|-----------------|
| **LLM** | Mocked with fixtures | Real API calls |
| **Purpose** | Verify component wiring | Verify AI output quality |
| **Speed** | Medium (no API calls) | Slow (API latency) |
| **Cost** | Free | Incurs token costs |
| **When to Run** | Every commit | Pre-release, manual |
| **Deterministic** | Yes (mocked responses) | No (LLM may vary) |

### Mocking Strategy

| Component | Unit Tests | Integration Tests | Functional Tests |
|-----------|------------|-------------------|------------------|
| **LLM Calls** | Mocked | Mocked | **Real** |
| **File System** | Mocked (temp dirs) | Mocked (temp dirs) | Real |
| **Database** | In-memory SQLite | In-memory SQLite | Real SQLite |
| **CrewAI** | Mock crew outputs | Mock LLM only | **Real crews** |

---

## 14. Risk & Dependencies

### Technical Risks

| Risk | Mitigation |
|------|------------|
| CrewAI API changes | Pin version, monitor releases |
| LLM rate limits | Implement retry with backoff |
| Token costs during dev | Use mocks for unit tests |
| Memory persistence issues | Thorough storage testing |

### Dependencies

| Dependency | Required For | Risk Level |
|------------|--------------|------------|
| `crewai` | All AI functionality | Medium |
| `streamlit` | UI | Low |
| `pydantic` | Data validation | Low |
| `openai` | LLM access | Medium |

---

## Appendix: Milestone Checklist

```
□ Milestone 1: Project Foundation
  □ 1.1 Initialize Project Structure
  □ 1.2 Create Utility Constants
  □ 1.3 Create Session State Utilities
  □ 1.4 Create Display Formatters

□ Milestone 2: Storage Layer
  □ 2.1 Implement Database Operations
  □ 2.2 Implement File Storage Operations
  □ 2.3 Implement Memory Manager

□ Milestone 3: Data Models & Schemas
  □ 3.1 Implement Enumerations
  □ 3.2 Implement Core Schemas
  □ 3.3 Implement Quiz Schemas
  □ 3.4 Implement User & Session Schemas

□ Milestone 4: Service Layer (No AI)
  □ 4.1 Implement User Service
  □ 4.2 Implement Progress Service
  □ 4.3 Implement Course Service (Stub)
  □ 4.4 Implement Learning Service (Stub)
  □ 4.5 Implement Quiz Service (Stub)

□ Milestone 5: CrewAI Crews
  □ 5.1 Implement Curriculum Crew Agents Config
  □ 5.2 Implement Curriculum Crew Tasks Config
  □ 5.3 Implement Curriculum Crew Class
  □ 5.4 Implement Teaching Crew
  □ 5.5 Implement Assessment Crew
  □ 5.6 Implement Crew Unit Tests

□ Milestone 6: Service-Crew Integration
  □ 6.1 Integrate Course Service with Curriculum Crew
  □ 6.2 Integrate Learning Service with Teaching Crew
  □ 6.3 Integrate Quiz Service with Assessment Crew
  □ 6.4 Functional Tests with Real LLM

□ Milestone 7: UI Components
  □ 7.1 Implement Sidebar Component
  □ 7.2 Implement Course Card Component
  □ 7.3 Implement Concept Viewer Component
  □ 7.4 Implement Chat Interface Component
  □ 7.5 Implement Quiz Question Component

□ Milestone 8: UI Pages
  □ 8.1 Implement Dashboard Page
  □ 8.2 Implement New Course Page
  □ 8.3 Implement Learning Page
  □ 8.4 Implement Quiz Page
  □ 8.5 Implement Progress Page
  □ 8.6 Implement Settings Page
  □ 8.7 Implement Onboarding Page

□ Milestone 9: End-to-End Integration
  □ 9.1 Main App Entry Point
  □ 9.2 End-to-End Course Creation Flow
  □ 9.3 End-to-End Learning Flow
  □ 9.4 End-to-End Quiz Flow

□ Milestone 10: Polish & Documentation
  □ 10.1 Error Handling & Edge Cases
  □ 10.2 Loading States & UX Polish
  □ 10.3 README Documentation
  □ 10.4 Final Integration Test Suite
```

---

*End of Document*

