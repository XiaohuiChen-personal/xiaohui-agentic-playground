# 🥋 Sensei - Proposed File Architecture

> **Version:** 1.0  
> **Last Updated:** January 2026  
> **Status:** Design Phase

---

## Table of Contents

1. [Overview](#1-overview)
2. [Complete File Structure](#2-complete-file-structure)
3. [Directory Breakdown](#3-directory-breakdown)
   - [3.1 Root Directory](#31-root-directory)
   - [3.2 Source Directory](#32-source-directory)
   - [3.3 Crews Directory](#33-crews-directory)
   - [3.4 Services Directory](#34-services-directory)
   - [3.5 Models Directory](#35-models-directory)
   - [3.6 Storage Directory](#36-storage-directory)
   - [3.7 UI Directory](#37-ui-directory)
   - [3.8 Data Directory](#38-data-directory)
4. [File Descriptions](#4-file-descriptions)
5. [Import Structure](#5-import-structure)

---

## 1. Overview

This document defines the file architecture for the Sensei project based on the designs in:
- `BACKEND_DESIGN.md` - Backend architecture with 3 crews, 5 services, and storage layer
- `FRONTEND_DESIGN.md` - Streamlit UI with 6 pages and reusable components

The architecture follows Python best practices with clear separation of concerns.

---

## 2. Complete File Structure

```
sensei/
│
├── pyproject.toml                          # Project dependencies and metadata
├── README.md                               # Project documentation
│
├── docs/                                   # 📖 Design Documentation
│   ├── BACKEND_DESIGN.md                   # Backend design document
│   ├── FRONTEND_DESIGN.md                  # Frontend design document
│   ├── PROPOSED_FILE_ARCHITECTURE.md       # This file
│   └── PLANNING.md                         # Implementation milestones
│
├── src/
│   └── sensei/
│       │
│       ├── __init__.py                     # Package initialization
│       ├── app.py                          # 🎯 Main Streamlit entry point
│       │
│       ├── crews/                          # 🤖 CrewAI Crews
│       │   ├── __init__.py
│       │   │
│       │   ├── curriculum_crew/            # Course creation crew
│       │   │   ├── __init__.py
│       │   │   ├── curriculum_crew.py      # Crew definition
│       │   │   └── config/
│       │   │       ├── agents.yaml         # Agent definitions
│       │   │       └── tasks.yaml          # Task definitions
│       │   │
│       │   ├── teaching_crew/              # Learning session crew
│       │   │   ├── __init__.py
│       │   │   ├── teaching_crew.py        # Crew definition
│       │   │   └── config/
│       │   │       ├── agents.yaml         # Agent definitions
│       │   │       └── tasks.yaml          # Task definitions
│       │   │
│       │   └── assessment_crew/            # Quiz and evaluation crew
│       │       ├── __init__.py
│       │       ├── assessment_crew.py      # Crew definition
│       │       └── config/
│       │           ├── agents.yaml         # Agent definitions
│       │           └── tasks.yaml          # Task definitions
│       │
│       ├── services/                       # 📦 Business Logic Services
│       │   ├── __init__.py
│       │   ├── course_service.py           # Course management
│       │   ├── learning_service.py         # Learning session management
│       │   ├── quiz_service.py             # Quiz generation and evaluation
│       │   ├── progress_service.py         # Progress tracking
│       │   └── user_service.py             # User preferences management
│       │
│       ├── models/                         # 📊 Data Models
│       │   ├── __init__.py
│       │   ├── schemas.py                  # Pydantic models (Course, Module, etc.)
│       │   └── enums.py                    # Enumerations (LearningStyle, etc.)
│       │
│       ├── storage/                        # 💾 Data Persistence
│       │   ├── __init__.py
│       │   ├── database.py                 # SQLite database operations
│       │   ├── file_storage.py             # JSON file operations
│       │   └── memory_manager.py           # CrewAI memory configuration
│       │
│       ├── ui/                             # 🎨 Streamlit UI Components
│       │   ├── __init__.py
│       │   │
│       │   ├── components/                 # Reusable UI components
│       │   │   ├── __init__.py
│       │   │   ├── sidebar.py              # Navigation sidebar
│       │   │   ├── header.py               # Page headers
│       │   │   ├── course_card.py          # Course display card
│       │   │   ├── progress_bar.py         # Progress indicator
│       │   │   ├── concept_viewer.py       # Lesson content display
│       │   │   ├── chat_interface.py       # Q&A chat component
│       │   │   ├── quiz_question.py        # Quiz question display
│       │   │   └── stats_card.py           # Statistics cards
│       │   │
│       │   └── pages/                      # Page implementations
│       │       ├── __init__.py
│       │       ├── dashboard.py            # Main dashboard
│       │       ├── new_course.py           # Course creation
│       │       ├── learning.py             # Learning session
│       │       ├── quiz.py                 # Quiz interface
│       │       ├── progress.py             # Progress overview
│       │       ├── settings.py             # User settings
│       │       └── onboarding.py           # First-time user setup
│       │
│       └── utils/                          # 🔧 Utilities
│           ├── __init__.py
│           ├── state.py                    # Session state helpers
│           ├── formatters.py               # Display formatters
│           └── constants.py                # App constants
│
├── data/                                   # 📁 Runtime Data (gitignored)
│   ├── courses/                            # Course JSON files
│   │   └── {course_id}.json
│   ├── sensei.db                           # SQLite database
│   ├── user_preferences.json               # User settings
│   └── chat_history.json                   # Q&A logs
│
└── tests/                                  # 🧪 Test Suite
    ├── __init__.py
    ├── conftest.py                         # Shared fixtures and pytest config
    ├── test_crews/
    │   ├── __init__.py
    │   ├── test_curriculum_crew.py
    │   ├── test_teaching_crew.py
    │   └── test_assessment_crew.py
    ├── test_services/
    │   ├── __init__.py
    │   ├── test_course_service.py
    │   ├── test_learning_service.py
    │   ├── test_quiz_service.py
    │   ├── test_progress_service.py
    │   └── test_user_service.py
    ├── test_storage/
    │   ├── __init__.py
    │   ├── test_database.py
    │   └── test_file_storage.py
    └── test_functional/                    # 🔥 Functional tests (real LLM)
        ├── __init__.py
        ├── test_curriculum_crew_functional.py
        ├── test_teaching_crew_functional.py
        └── test_assessment_crew_functional.py
```

---

## 3. Directory Breakdown

### 3.1 Root Directory

```
sensei/
├── pyproject.toml                 # uv/pip dependencies, project metadata
├── README.md                      # How to install and run
└── docs/                          # Design documentation
    ├── BACKEND_DESIGN.md
    ├── FRONTEND_DESIGN.md
    ├── PROPOSED_FILE_ARCHITECTURE.md
    └── PLANNING.md
```

| File | Purpose |
|------|---------|
| `pyproject.toml` | Project dependencies (crewai, streamlit, pydantic, etc.) |
| `README.md` | Installation instructions, usage guide |
| `docs/*.md` | Architecture and planning documentation |

---

### 3.2 Source Directory

```
src/
└── sensei/
    ├── __init__.py                # Package init, version info
    └── app.py                     # Streamlit entry point
```

| File | Purpose |
|------|---------|
| `__init__.py` | Package initialization, exports |
| `app.py` | Main Streamlit app entry point, routing |

**`app.py` Responsibilities:**
- Initialize Streamlit page config
- Set up session state
- Route to appropriate page based on navigation
- Initialize services on app start

---

### 3.3 Crews Directory

```
crews/
├── __init__.py
│
├── curriculum_crew/
│   ├── __init__.py
│   ├── curriculum_crew.py
│   └── config/
│       ├── agents.yaml
│       └── tasks.yaml
│
├── teaching_crew/
│   ├── __init__.py
│   ├── teaching_crew.py
│   └── config/
│       ├── agents.yaml
│       └── tasks.yaml
│
└── assessment_crew/
    ├── __init__.py
    ├── assessment_crew.py
    └── config/
        ├── agents.yaml
        └── tasks.yaml
```

| Crew | Files | Agents |
|------|-------|--------|
| **Curriculum Crew** | `curriculum_crew.py` | Curriculum Architect, Content Researcher |
| **Teaching Crew** | `teaching_crew.py` | Knowledge Teacher, Q&A Mentor |
| **Assessment Crew** | `assessment_crew.py` | Quiz Designer, Performance Analyst |

**Config Files:**

`agents.yaml` structure:
```yaml
agent_name:
  role: "Role description"
  goal: "Agent's goal"
  backstory: "Agent's backstory"
```

`tasks.yaml` structure:
```yaml
task_name:
  description: "Task description"
  expected_output: "What the task should produce"
  agent: agent_name
```

---

### 3.4 Services Directory

```
services/
├── __init__.py
├── course_service.py
├── learning_service.py
├── quiz_service.py
├── progress_service.py
└── user_service.py
```

| Service | Responsibility | Crews Used |
|---------|----------------|------------|
| `course_service.py` | Create, list, get, delete courses | Curriculum Crew |
| `learning_service.py` | Manage learning sessions, Q&A | Teaching Crew |
| `quiz_service.py` | Generate quizzes, evaluate answers | Assessment Crew |
| `progress_service.py` | Track completion, statistics | None (data only) |
| `user_service.py` | Manage user preferences | None (data only) |

---

### 3.5 Models Directory

```
models/
├── __init__.py
├── schemas.py
└── enums.py
```

| File | Contents |
|------|----------|
| `schemas.py` | Pydantic models: `Course`, `Module`, `Concept`, `Quiz`, `QuizQuestion`, `Progress`, `QuizResult`, `UserPreferences`, `LearningSession` |
| `enums.py` | Enumerations: `LearningStyle`, `ConceptStatus`, `ExperienceLevel` |

---

### 3.6 Storage Directory

```
storage/
├── __init__.py
├── database.py
├── file_storage.py
└── memory_manager.py
```

| File | Purpose |
|------|---------|
| `database.py` | SQLite operations (progress, quiz results, sessions) |
| `file_storage.py` | JSON file operations (courses, user prefs) |
| `memory_manager.py` | CrewAI memory configuration and initialization |

---

### 3.7 UI Directory

```
ui/
├── __init__.py
│
├── components/
│   ├── __init__.py
│   ├── sidebar.py
│   ├── header.py
│   ├── course_card.py
│   ├── progress_bar.py
│   ├── concept_viewer.py
│   ├── chat_interface.py
│   ├── quiz_question.py
│   └── stats_card.py
│
└── pages/
    ├── __init__.py
    ├── dashboard.py
    ├── new_course.py
    ├── learning.py
    ├── quiz.py
    ├── progress.py
    ├── settings.py
    └── onboarding.py
```

**Components:**

| Component | Purpose | Used In |
|-----------|---------|---------|
| `sidebar.py` | Navigation menu | All pages |
| `header.py` | Page title, breadcrumbs | All pages |
| `course_card.py` | Course display with progress | Dashboard |
| `progress_bar.py` | Visual progress indicator | Learning, Dashboard |
| `concept_viewer.py` | Markdown lesson display | Learning |
| `chat_interface.py` | Q&A chat | Learning |
| `quiz_question.py` | Quiz question with options | Quiz |
| `stats_card.py` | Statistics display | Dashboard, Progress |

**Pages:**

| Page | Purpose | Services Used |
|------|---------|---------------|
| `dashboard.py` | Course overview, stats | CourseService, ProgressService |
| `new_course.py` | Create new course | CourseService |
| `learning.py` | Learning session | LearningService |
| `quiz.py` | Take quiz | QuizService |
| `progress.py` | Progress overview | ProgressService |
| `settings.py` | User preferences | UserService |
| `onboarding.py` | First-time setup | UserService |

---

### 3.8 Data Directory

```
data/                              # Runtime data (gitignored)
├── courses/
│   ├── cuda-c-123.json
│   ├── python-basics-456.json
│   └── ...
├── sensei.db
├── user_preferences.json
└── chat_history.json
```

| File/Directory | Contents | Storage Type |
|----------------|----------|--------------|
| `courses/` | Course JSON files with modules and concepts | Entity Memory |
| `sensei.db` | SQLite database (progress, quiz results) | Long-Term Memory |
| `user_preferences.json` | User settings and profile | User Memory |
| `chat_history.json` | Q&A conversation logs | Short-Term (persisted) |

---

## 4. File Descriptions

### Core Files

| File Path | Description |
|-----------|-------------|
| `src/sensei/app.py` | Main Streamlit application entry point. Handles page routing, session state initialization, and service bootstrapping. |
| `src/sensei/crews/curriculum_crew/curriculum_crew.py` | Defines the Curriculum Crew with Curriculum Architect and Content Researcher agents. Creates course structures. |
| `src/sensei/crews/teaching_crew/teaching_crew.py` | Defines the Teaching Crew with Knowledge Teacher and Q&A Mentor agents. Handles lesson delivery and Q&A. |
| `src/sensei/crews/assessment_crew/assessment_crew.py` | Defines the Assessment Crew with Quiz Designer and Performance Analyst agents. Creates and evaluates quizzes. |
| `src/sensei/services/course_service.py` | Business logic for course management. Interfaces with Curriculum Crew and file storage. |
| `src/sensei/services/learning_service.py` | Manages learning sessions. Interfaces with Teaching Crew for lesson generation and Q&A. |
| `src/sensei/services/quiz_service.py` | Handles quiz generation and evaluation. Interfaces with Assessment Crew. |
| `src/sensei/services/progress_service.py` | Tracks and retrieves learning progress. Interfaces with SQLite database. |
| `src/sensei/services/user_service.py` | Manages user preferences. Interfaces with JSON file storage. |
| `src/sensei/models/schemas.py` | Pydantic models for all data structures (Course, Module, Concept, etc.). |
| `src/sensei/storage/database.py` | SQLite database operations for progress tracking and quiz results. |
| `src/sensei/storage/file_storage.py` | JSON file operations for courses and user preferences. |
| `src/sensei/storage/memory_manager.py` | CrewAI memory system configuration and initialization. |

### UI Files

| File Path | Description |
|-----------|-------------|
| `src/sensei/ui/pages/dashboard.py` | Main dashboard showing courses, stats, and quick actions. |
| `src/sensei/ui/pages/new_course.py` | Course creation page with topic input and curriculum generation. |
| `src/sensei/ui/pages/learning.py` | Learning session page with concept viewer, navigation, and Q&A chat. |
| `src/sensei/ui/pages/quiz.py` | Quiz interface with questions, answer submission, and results display. |
| `src/sensei/ui/pages/progress.py` | Progress overview showing all courses, stats, and quiz history. |
| `src/sensei/ui/pages/settings.py` | User settings page for preferences and learning style. |
| `src/sensei/ui/pages/onboarding.py` | First-time user onboarding flow. |
| `src/sensei/ui/components/sidebar.py` | Navigation sidebar component used across all pages. |
| `src/sensei/ui/components/concept_viewer.py` | Markdown renderer for lesson content with code highlighting. |
| `src/sensei/ui/components/chat_interface.py` | Chat component for Q&A interactions with Sensei. |

### Test Files

| File Path | Description |
|-----------|-------------|
| `tests/conftest.py` | Shared pytest fixtures, mock LLM configurations, and test utilities. |
| `tests/test_crews/test_*.py` | Unit tests for crews with mocked LLM responses. |
| `tests/test_services/test_*.py` | Unit and integration tests for service layer. |
| `tests/test_storage/test_*.py` | Unit tests for database and file storage operations. |
| `tests/test_functional/test_*_functional.py` | **Functional tests with real LLM API calls.** Tests AI output quality and are run manually or pre-release. Marked with `@pytest.mark.functional`. |

---

## 5. Import Structure

### How Components Connect

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           IMPORT HIERARCHY                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│                              app.py                                         │
│                                │                                            │
│              ┌─────────────────┼─────────────────┐                         │
│              │                 │                 │                         │
│              ▼                 ▼                 ▼                         │
│         ui/pages/         services/         utils/                        │
│              │                 │                 │                         │
│              │                 │                 │                         │
│              ▼                 ▼                 │                         │
│       ui/components/       crews/               │                         │
│              │                 │                 │                         │
│              │                 │                 │                         │
│              └────────┬────────┴─────────┬──────┘                         │
│                       │                  │                                 │
│                       ▼                  ▼                                 │
│                   models/            storage/                              │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Example Imports

**`app.py`:**
```python
from sensei.ui.pages import dashboard, learning, quiz, settings
from sensei.services import CourseService, LearningService
from sensei.utils.state import initialize_session_state
```

**`ui/pages/learning.py`:**
```python
from sensei.ui.components import sidebar, header, concept_viewer, chat_interface
from sensei.services import LearningService
from sensei.models.schemas import LearningSession, Concept
```

**`services/course_service.py`:**
```python
from sensei.crews.curriculum_crew import CurriculumCrew
from sensei.storage import file_storage, database
from sensei.models.schemas import Course, Module, Concept
```

**`crews/curriculum_crew/curriculum_crew.py`:**
```python
from crewai import Agent, Task, Crew
from sensei.models.schemas import Course
from sensei.storage.memory_manager import get_memory_config
```

---

## Appendix: File Count Summary

| Category | File Count |
|----------|------------|
| Root configs | 2 |
| Docs | 4 |
| Core (`__init__.py`) | 15 |
| Crews | 6 (+ 6 yaml configs) |
| Services | 5 |
| Models | 2 |
| Storage | 3 |
| UI Components | 8 |
| UI Pages | 7 |
| Utils | 3 |
| Tests (Unit/Integration) | 12 |
| Tests (Functional) | 5 |
| **Total** | **~77 files** |

---

*End of Document*

