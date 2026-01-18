# 🥋 Sensei

**Your AI-Powered Adaptive Learning Tutor**

Sensei is an intelligent tutoring system that creates personalized learning experiences using CrewAI agents. Tell Sensei what you want to learn, and it will generate a structured curriculum, teach you concepts interactively, answer your questions, and assess your understanding through adaptive quizzes.

## ✨ Key Features

- 📚 **Custom Curriculum Generation** — AI creates structured courses for any topic
- 🎓 **Interactive Lessons** — Learn concepts with explanations, code examples, and key takeaways
- 💬 **Q&A Support** — Ask clarifying questions anytime during your learning
- 📝 **Adaptive Quizzes** — Test your knowledge with AI-generated assessments
- 📊 **Progress Tracking** — Monitor your learning journey across all courses

## 🚧 Project Status

| Milestone | Description | Status |
|-----------|-------------|--------|
| M1-M2 | Project Setup & Design | ✅ Complete |
| M3 | Data Models & Schemas | ✅ Complete |
| M4 | Service Layer (No AI) | ✅ Complete |
| M5 | CrewAI Crews | ✅ Complete |
| M6 | Service-Crew Integration | ✅ Complete |
| M7-M10 | UI & Polish | ⏳ Planned |

### Current Architecture

- **Curriculum Crew**: Flow-based design with parallel module expansion (Gemini 3 Pro + Claude Opus 4.5)
- **Teaching Crew**: Dynamic task selection for lessons and Q&A (Claude Opus 4.5 + GPT 5.2)
- **Assessment Crew**: Quiz generation and evaluation (Claude Opus 4.5 + GPT 5.2)

See the design documents for architecture details:
- [`BACKEND_DESIGN.md`](./docs/BACKEND_DESIGN.md) — Backend architecture
- [`FRONTEND_DESIGN.md`](./docs/FRONTEND_DESIGN.md) — UI design
- [`PROPOSED_FILE_ARCHITECTURE.md`](./docs/PROPOSED_FILE_ARCHITECTURE.md) — File structure
- [`PLANNING.md`](./docs/PLANNING.md) — Implementation milestones

## 🛠️ Setup

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager

### Installation

```bash
# Clone the repository
cd 3-crew-ai/sensei

# Install dependencies
uv sync

# Copy environment variables
cp ../../.env.example .env
# Edit .env with your API keys
```

### Required API Keys

Set these in your `.env` file:

```bash
# Required for Sensei
OPENAI_API_KEY=your-openai-key        # Q&A Mentor, Performance Analyst, Embeddings
ANTHROPIC_API_KEY=your-anthropic-key  # Content Researcher, Knowledge Teacher, Quiz Designer
GOOGLE_API_KEY=your-google-key        # Curriculum Architect

# Optional: LangSmith tracing
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your-langsmith-key
LANGSMITH_PROJECT=project-sensei
```

## 🧪 Testing

### Run All Unit Tests

```bash
uv run pytest tests/ -v
```

### Run Unit Tests with Coverage

```bash
uv run pytest tests/ --cov=sensei --cov-report=term-missing -v
```

### Run Specific Test Suites

```bash
# Service layer tests
uv run pytest tests/test_services/ -v

# Crew unit tests (mocked LLM)
uv run pytest tests/test_crews/ -v

# Storage layer tests
uv run pytest tests/test_storage/ -v

# Model/Schema tests
uv run pytest tests/test_models/ -v
```

### Run Functional Tests (Real LLM Calls)

> ⚠️ **Note**: Functional tests make actual API calls and require all three API keys.

```bash
# Run all functional tests
uv run pytest tests/test_functional/ -m functional -v -s

# Run specific crew functional test
uv run pytest tests/test_functional/test_curriculum_crew_functional.py -m functional -v -s
uv run pytest tests/test_functional/test_teaching_crew_functional.py -m functional -v -s
uv run pytest tests/test_functional/test_assessment_crew_functional.py -m functional -v -s
```

### Skip Functional Tests (Unit Tests Only)

```bash
uv run pytest tests/ -v --ignore=tests/test_functional/
```

## 📈 Test Coverage

Current coverage for core layers:

| Layer | Coverage |
|-------|----------|
| Models | ~100% |
| Storage | ~95% |
| Services | ~94% |
| Crews | ~90% |
| **Overall** | **~94%** |

---

*Built with [CrewAI](https://www.crewai.com/) and [Streamlit](https://streamlit.io/)*
