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

> **⚠️ Under Development**
> 
> Foundation and storage layer complete. AI crews and UI in progress.

See the design documents for architecture details:
- [`BACKEND_DESIGN.md`](./docs/BACKEND_DESIGN.md) — Backend architecture
- [`FRONTEND_DESIGN.md`](./docs/FRONTEND_DESIGN.md) — UI design
- [`PROPOSED_FILE_ARCHITECTURE.md`](./docs/PROPOSED_FILE_ARCHITECTURE.md) — File structure
- [`PLANNING.md`](./docs/PLANNING.md) — Implementation milestones

## 🧪 Testing

**Run all unit tests:**
```bash
uv run pytest tests/ -v
```

**Run unit tests with coverage:**
```bash
uv run pytest tests/ --cov=sensei --cov-report=term-missing
```

**Run integration tests (coming soon):**
```bash
uv run pytest tests/ -m integration -v
```

**Run end-to-end tests (coming soon):**
```bash
uv run pytest tests/ -m e2e -v
```

---

*Built with [CrewAI](https://www.crewai.com/) and [Streamlit](https://streamlit.io/)*

