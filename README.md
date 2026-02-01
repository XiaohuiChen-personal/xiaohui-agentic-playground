# xiaohui-agentic-playground

A playground for exploring agentic AI systems and workflow patterns.

## Overview

This repository contains experiments with different agentic design patterns for building LLM-powered applications, using multiple frameworks:

- **OpenAI Agents SDK** - Native multi-agent support with handoffs and tools
- **CrewAI** - YAML-based agent/task configuration with Flow orchestration
- **LangGraph** - Stateful graph-based workflows with explicit nodes and edges
- **AutoGen** - Microsoft's multi-agent conversation framework
- **vLLM + Open Source Models** - Local inference with Qwen3, Mistral, Llama on DGX Spark

**Patterns explored:**
- **Prompt Chaining** - Decomposing complex tasks into sequential subtasks
- **Routing** - Dynamically directing inputs to specialized handlers
- **Orchestrator-Worker** - Coordinating multiple specialized workers
- **Multi-Agent Adversarial Simulation** - Agents with opposing objectives engaging in realistic exchanges

## Prerequisites

- **Python 3.12+**
- **[UV](https://docs.astral.sh/uv/)** - Fast Python package installer and resolver
- **API Keys** - OpenAI, Anthropic, and Google AI API keys

## Quick Start

### 1. Install UV (if not already installed)

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or with Homebrew (macOS)
brew install uv
```

### 2. Clone the Repository

```bash
git clone https://github.com/XiaohuiChen-personal/xiaohui-agentic-playground.git
cd xiaohui-agentic-playground
```

### 3. Create Virtual Environment

```bash
uv venv --python 3.12
```

### 4. Activate the Virtual Environment

```bash
# macOS/Linux
source .venv/bin/activate

# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# Windows (CMD)
.venv\Scripts\activate.bat
```

### 5. Install Dependencies

```bash
uv sync
```

### 6. Set Up Environment Variables

Create a `.env` file in the project root with your API keys:

```bash
# Create .env file
cp .env.example .env

# Edit .env with your actual API keys
```

Your `.env` file should contain:

```
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GOOGLE_API_KEY=your_google_api_key_here
RAPID_API_KEY=your_rapid_api_key_here
```

### 7. Register the Kernel for Jupyter

To use this virtual environment in Jupyter notebooks:

```bash
python -m ipykernel install --user --name=xiaohui-agentic-playground --display-name="Python (agentic-playground)"
```

### 8. Run Notebooks

Open the notebooks in VS Code, Cursor, or JupyterLab and select the `Python (agentic-playground)` kernel.

## Project Structure

```
xiaohui-agentic-playground/
├── 1-agentic-workflow/
│   ├── agentic_systems.ipynb    # Agentic patterns for classification
│   └── README.md                # Detailed documentation
├── 2-openai-sdk/
│   ├── email_battle/
│   │   ├── email_battle.ipynb   # Multi-agent adversarial simulation
│   │   └── README.md            # Detailed documentation
│   └── smart_shopping_assistant/
│       ├── smart_shopping_assistant.ipynb  # Multi-agent shopping assistant
│       └── README.md            # Detailed documentation
├── 3-crew-ai/
│   ├── email_battle/            # CrewAI implementation
│   │   └── README.md            # Detailed documentation
│   ├── smart_shopping_assistant/ # CrewAI Flow implementation
│   │   └── README.md            # Detailed documentation
│   └── sensei/                  # AI-powered adaptive learning tutor
│       ├── src/sensei/          # Main application code
│       ├── tests/               # Comprehensive test suite
│       ├── docs/                # Design documents & screenshots
│       └── README.md            # Detailed documentation
├── 4-langgraph/
│   └── email_battle/            # LangGraph implementation
│       ├── models.py            # Data models and state
│       ├── prompts.py           # System and user prompts
│       ├── nodes.py             # Node implementations
│       ├── graph.py             # Graph definition
│       ├── app.py               # Entry point
│       └── README.md            # Detailed documentation
├── 5-autogen/
│   └── email_battle/            # AutoGen implementation
│       ├── email_battle_autogen.ipynb  # Notebook implementation
│       └── README.md            # Detailed documentation
├── 6-open-source/
│   ├── docker-compose-*.yml     # vLLM container configurations
│   ├── start_docker.sh          # Docker management script
│   ├── email_battle_open_source/ # Email Battle with local models
│   │   ├── src/email_battle/    # CrewAI Flow implementation
│   │   └── README.md            # Detailed documentation
│   ├── dual_model_speed_test/   # Speed comparison tests
│   │   ├── speed_test.ipynb     # Benchmark notebook
│   │   └── README.md            # Test results documentation
│   ├── single_model_speed_test/ # Single model benchmarks
│   │   ├── speed_test.ipynb     # Llama-70B benchmark
│   │   ├── speed_test_gpt.ipynb # GPT-OSS-20B benchmark (fastest)
│   │   └── README.md            # Test results documentation
│   └── README.md                # vLLM setup documentation
├── .env.example                 # Template for environment variables
├── .gitignore
├── pyproject.toml               # Project dependencies (UV/pip)
├── uv.lock                      # Locked dependencies
└── README.md
```

## Dependencies

| Package | Purpose |
|---------|---------|
| `openai` | OpenAI API client |
| `anthropic` | Anthropic API client |
| `openai-agents` | OpenAI Agents SDK for multi-agent workflows |
| `langgraph` | LangGraph for stateful graph-based workflows |
| `langchain` | LangChain core library |
| `langchain-openai` | LangChain OpenAI integration |
| `langchain-anthropic` | LangChain Anthropic integration |
| `autogen-agentchat` | Microsoft AutoGen agent chat capabilities |
| `autogen-core` | Microsoft AutoGen core framework |
| `autogen-ext` | Microsoft AutoGen extensions |
| `python-dotenv` | Load environment variables from `.env` |
| `crewai` | CrewAI multi-agent framework |
| `streamlit` | Web application framework for Sensei UI |
| `litellm` | Universal LLM interface (OpenAI, Anthropic, Google, local) |
| `vllm` | High-throughput LLM inference (via Docker) |
| `datasets` | HuggingFace Datasets (for AG News dataset) |
| `scikit-learn` | Metrics and evaluation |
| `ipykernel` | Jupyter kernel support |

## Adding New Dependencies

```bash
# Add a runtime dependency
uv add <package-name>

# Add a development dependency
uv add --dev <package-name>
```

## 📂 Projects

### 1. Agentic Workflow Design Patterns

📁 [`1-agentic-workflow/`](1-agentic-workflow/)

Explores and compares **5 agentic workflow design patterns** using the AG News dataset for multi-class text classification:

| Pattern | Description | Best Accuracy |
|---------|-------------|---------------|
| Prompt Chaining | Sequential pipeline with entity extraction → analysis → classification | 83% |
| Routing | Intelligent router directs input to specialized expert agents | 80% |
| Parallelization | Multiple agents process simultaneously, results aggregated | 77% |
| Orchestrator-Worker | Central orchestrator coordinates specialized worker agents | 77% |
| Evaluator-Optimizer | Iterative refinement with evaluation and self-critique | 73% |

➡️ **[See full documentation](1-agentic-workflow/README.md)**

---

### 2. Email Battle (OpenAI Agents SDK)

📁 [`2-openai-sdk/email_battle/`](2-openai-sdk/email_battle/)

A **multi-agent adversarial simulation** using the OpenAI Agents SDK. Two AI agents with opposing objectives engage in a realistic email exchange:

| Agent | Role | Objective |
|-------|------|-----------|
| **Elon Musk (DOGE)** | Head of Department of Government Efficiency | Identify and terminate coasting employees |
| **John Smith (USCIS)** | GS-12 Immigration Services Officer | Survive the efficiency review |

Features tournament-style battles across 8 model combinations (GPT-5.2, Claude Opus 4.5, etc.) with full email thread context preservation.

➡️ **[See full documentation](2-openai-sdk/email_battle/README.md)**

---

### 3. Smart Shopping Assistant (OpenAI Agents SDK)

📁 [`2-openai-sdk/smart_shopping_assistant/`](2-openai-sdk/smart_shopping_assistant/)

A **multi-agent shopping assistant** demonstrating **tools**, **handoffs**, and **orchestration** patterns. Specialized agents collaborate to help users find, compare, and research products.

| Agent | Model | Role |
|-------|-------|------|
| **Concierge** | `gpt-5.2-pro` | Orchestrator - routes requests and synthesizes responses |
| **Product Specialist** | `gpt-5.2` | Searches products, compares prices, gets specifications |
| **Review Analyst** | `gpt-5.2` | Fetches and analyzes customer reviews |

**Key Features:**
- Bidirectional handoffs (specialists hand back to orchestrator)
- Native OpenAI SDK handoffs
- Real-Time Product Search API integration
- Full tracing support

➡️ **[See full documentation](2-openai-sdk/smart_shopping_assistant/README.md)**

---

### 4. Email Battle (CrewAI)

📁 [`3-crew-ai/email_battle/`](3-crew-ai/email_battle/)

The same Email Battle scenario implemented using the **CrewAI framework**, demonstrating an alternative approach to multi-agent orchestration with YAML-based agent/task configuration.

➡️ **[See full documentation](3-crew-ai/email_battle/README.md)**

---

### 5. Smart Shopping Assistant (CrewAI Flow)

📁 [`3-crew-ai/smart_shopping_assistant/`](3-crew-ai/smart_shopping_assistant/)

The Smart Shopping Assistant reimplemented using **CrewAI Flow**, demonstrating how to translate OpenAI SDK handoffs into CrewAI's flow-based orchestration.

| Agent | Model | Role |
|-------|-------|------|
| **Concierge** | `openai/gpt-5.2` | Orchestrator - classifies intent and synthesizes responses |
| **Product Specialist** | `anthropic/claude-opus-4-5-20251101` | Searches products, compares prices |
| **Review Analyst** | `anthropic/claude-opus-4-5-20251101` | Fetches and analyzes customer reviews |

**Key Features:**
- CrewAI Flow with `@start()`, `@listen()`, and `@router()` decorators
- LLM-based intent classification (not rule-based)
- One specialist at a time routing (matching OpenAI SDK behavior)
- Multi-provider support (OpenAI + Anthropic)
- Real-Time Product Search API integration

➡️ **[See full documentation](3-crew-ai/smart_shopping_assistant/README.md)**

---

### 6. Sensei - AI-Powered Adaptive Learning Tutor (CrewAI)

📁 [`3-crew-ai/sensei/`](3-crew-ai/sensei/)

An **intelligent tutoring system** that creates personalized learning experiences using CrewAI's multi-agent framework. Tell Sensei what you want to learn, and it generates a structured curriculum, teaches concepts interactively, answers questions, and assesses understanding through adaptive quizzes.

| Crew | Agents | Models | Purpose |
|------|--------|--------|---------|
| **Curriculum Crew** | Curriculum Architect, Content Researcher | Claude Opus 4.5, Gemini 3 Pro | Plans course structure and expands modules in parallel |
| **Teaching Crew** | Knowledge Teacher, Q&A Mentor | Claude Opus 4.5, GPT 5.2 | Generates lessons and answers student questions |
| **Assessment Crew** | Quiz Designer, Performance Analyst | Claude Opus 4.5, GPT 5.2 | Creates quizzes and provides intelligent feedback |

**Key Features:**
- 📚 Custom curriculum generation for any topic
- 🎓 Interactive lessons with code examples and key takeaways
- 💬 "Ask Sensei Anything" Q&A during learning
- 📝 Adaptive quizzes with multiple question types
- 📊 Intelligent feedback identifying strengths and weak areas
- 📈 Progress tracking across all courses

**Tech Stack:** CrewAI • Streamlit • Claude Opus 4.5 • GPT 5.2 • Gemini 3 Pro • Pydantic • SQLite

**Run:**
```bash
cd 3-crew-ai/sensei
uv sync
uv run streamlit run src/sensei/app.py
```

➡️ **[See full documentation](3-crew-ai/sensei/README.md)**

---

### 7. Email Battle (LangGraph)

📁 [`4-langgraph/email_battle/`](4-langgraph/email_battle/)

The Email Battle scenario reimplemented using **LangGraph**, demonstrating stateful graph-based workflows with explicit nodes and edges.

| Agent | Model | Role |
|-------|-------|------|
| **Elon Musk (DOGE)** | `gpt-5.2` | Head of Department of Government Efficiency |
| **John Smith (USCIS)** | `claude-opus-4-5-20251101` | GS-12 Immigration Services Officer (coasting) |

**Key Features:**
- Declarative graph-based workflow (vs imperative control flow)
- State management with reducers (`operator.add` for email accumulation)
- Structured output for reliable decision parsing (Pydantic models)
- Conditional edges for dynamic routing based on decisions
- Streaming execution for real-time progress display
- Clean separation: models, prompts, nodes, graph, utils

**Workflow:**
```
START → generate_mass_email (Elon)
     → john_initial_response (John)
     → elon_evaluate (Elon) ↔ john_followup_response (John) [loop]
     → determine_outcome
     → END
```

**Run:**
```bash
cd 4-langgraph/email_battle
uv run python app.py
```

➡️ **[See full documentation](4-langgraph/email_battle/README.md)**

---

### 8. Email Battle (AutoGen)

📁 [`5-autogen/email_battle/`](5-autogen/email_battle/)

The Email Battle scenario reimplemented using **Microsoft AutoGen 0.7**, demonstrating multi-agent conversations with `AssistantAgent` and model client integrations.

| Agent | Model | Role |
|-------|-------|------|
| **Elon Musk (DOGE)** | `claude-opus-4-5-20251101` | Head of Department of Government Efficiency |
| **John Smith (USCIS)** | `gpt-5.2` | GS-12 Immigration Services Officer (coasting) |

**Key Features:**
- `AssistantAgent` for LLM-powered agents with system messages
- Multi-provider support via `OpenAIChatCompletionClient` and `AnthropicChatCompletionClient`
- Manual orchestration for decision-based flow control
- Beautiful markdown output in Jupyter notebook
- Comprehensive email thread formatting and decision parsing

**Notable Finding:** GPT-5.2 (playing John) triggered safety guardrails and broke character, while Claude Opus 4.5 (playing Elon) stayed in character and used this as evidence for termination.

**Run:**
Open `5-autogen/email_battle/email_battle_autogen.ipynb` in Jupyter and run all cells.

➡️ **[See full documentation](5-autogen/email_battle/README.md)**

---

### 9. Open Source LLM Inference (vLLM)

📁 [`6-open-source/`](6-open-source/)

Run **open-source LLMs locally** on NVIDIA DGX Spark using **vLLM** with Docker.

| Configuration | Models | TPS | Use Case |
|---------------|--------|-----|----------|
| **GPT-OSS** | GPT-OSS-20B (MoE) | **15.5** | Fastest + reasoning |
| **Single** | Llama 3.3 70B NVFP4 | 3.9 | Maximum quality |
| **Dual** | Mistral-24B + Qwen3-32B | 9.8 / 8.2 | Multi-agent (CrewAI) |

**Key Features:**
- OpenAI-compatible API (drop-in replacement)
- GPT-OSS-20B: MoE architecture, 4x faster than dense models
- NVFP4/MXFP4 quantization for Blackwell GPUs
- Up to 128K context windows
- Fine-tuning support with Unsloth

**Quick Start:**
```bash
cd 6-open-source
./start_docker.sh start gpt-oss  # Fastest (GPT-OSS-20B)
./start_docker.sh start dual     # Multi-model (Mistral + Qwen)
./start_docker.sh status         # Check health
```

➡️ **[See full documentation](6-open-source/README.md)**

---

### 10. Email Battle (Open Source Models)

📁 [`6-open-source/email_battle_open_source/`](6-open-source/email_battle_open_source/)

The Email Battle scenario running entirely on **local open-source models** via vLLM - no API costs, full privacy.

| Agent | Model | Port | Strengths |
|-------|-------|------|-----------|
| **Elon Musk (DOGE)** | Qwen3-32B-NVFP4 | 8001 | Reasoning, analysis, probing questions |
| **John Smith (USCIS)** | Mistral-Small-24B-NVFP4 | 8000 | Language generation, bureaucratic style |

**Latest Battle Results:**
- **Winner:** Elon Musk (TERMINATED)
- **Rounds:** 4 follow-up rounds, 11 total emails
- **Runtime:** ~12 minutes on DGX Spark

**Key Features:**
- CrewAI Flow orchestration with local LLMs
- 32K context window for full email thread
- Qwen3 thinking mode disabled for cleaner output
- Zero API costs

**Run:**
```bash
cd 6-open-source
./start_docker.sh start dual    # Start models first
cd email_battle_open_source
crewai run
```

➡️ **[See full documentation](6-open-source/email_battle_open_source/README.md)**

---

### 11. Dual Model Speed Test

📁 [`6-open-source/dual_model_speed_test/`](6-open-source/dual_model_speed_test/)

Performance benchmarks comparing **Mistral-Small-24B** and **Qwen3-32B** running concurrently on DGX Spark.

| Metric | Mistral-24B | Qwen3-32B | Winner |
|--------|-------------|-----------|--------|
| **Avg TTFT** | 0.138s | 0.169s | Mistral (18% faster) |
| **Avg Total Time** | 23.3s | 39.4s | Mistral (41% faster) |
| **Avg TPS** | 9.8 | 8.2 | Mistral (20% faster) |

**Test Scenarios:**
1. Short Prompt, Short Response - Baseline latency
2. Short Prompt, Long Response - Sustained throughput
3. Long Prompt, Short Response - Prefill speed
4. Code Generation - Programming tasks
5. Reasoning Task - Multi-step logic problems

**Key Findings:**
- **Mistral-24B is significantly faster** across all metrics
- **Qwen3-32B uses chain-of-thought by default** (`<think>` tags), generating 5-10x more tokens
- Both achieve sub-200ms TTFT for interactive applications
- Qwen3's longer times reflect more reasoning work, not just slower generation

**Recommendations:**
| Use Case | Model |
|----------|-------|
| Quick responses / General tasks | Mistral-24B |
| Complex reasoning / Math | Qwen3-32B |
| Latency-sensitive agents | Mistral-24B |
| Accuracy-critical tasks | Qwen3-32B |

**Run:**
```bash
cd 6-open-source
./start_docker.sh start dual
jupyter notebook dual_model_speed_test/speed_test.ipynb
```

➡️ **[See full documentation](6-open-source/dual_model_speed_test/README.md)**

---

### 12. Single Model Speed Tests

📁 [`6-open-source/single_model_speed_test/`](6-open-source/single_model_speed_test/)

Performance benchmarks of single models on DGX Spark.

#### GPT-OSS-20B (MoE) - Fastest ⚡

| Metric | Expected | Actual | Status |
|--------|----------|--------|--------|
| **Avg TPS** | 15-25 | **15.5** | ✅ Met expectation |
| **Avg TTFT** | 0.1-0.2s | **0.141s** | ✅ Met expectation |
| **vs Llama-70B** | 4-6x faster | **4x faster** | ✅ Met expectation |

**Key Features:**
- MoE architecture (only 3.6B active params per token)
- 128K context window
- Built-in chain-of-thought reasoning
- Apache 2.0 license for fine-tuning

**Run:**
```bash
cd 6-open-source
./start_docker.sh start gpt-oss
jupyter notebook single_model_speed_test/speed_test_gpt.ipynb
```

#### Llama-70B (Dense)

| Metric | Expected | Actual | Status |
|--------|----------|--------|--------|
| **Avg TPS** | 12-15+ | **3.9** | ❌ Below expectation |
| **Avg TTFT** | ~0.14s | **0.54s** | ❌ 4x slower |

**Key Findings:**
- **3.9 TPS is near the hardware limit** for 70B on DGX Spark unified memory
- **Model size dominates** - Memory bandwidth is the bottleneck

**Run:**
```bash
cd 6-open-source
./start_docker.sh start single
jupyter notebook single_model_speed_test/speed_test.ipynb
```

#### Model Comparison

| Model | Architecture | Active Params | Avg TPS | Relative Speed |
|-------|--------------|---------------|---------|----------------|
| **GPT-OSS-20B** | **MoE** | **3.6B** | **15.5** | **4.0x faster** |
| Mistral-24B | Dense | 24B | 9.8 | 2.5x faster |
| Llama-70B | Dense | 70B | 3.9 | 1.0x (baseline) |

**Recommendations:**
| Use Case | Model | TPS |
|----------|-------|-----|
| Speed + Reasoning | GPT-OSS-20B | 15.5 |
| Fast General Tasks | Mistral-24B | 9.8 |
| Maximum Quality | Llama-70B | 3.9 |

➡️ **[See full documentation](6-open-source/single_model_speed_test/README.md)**

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
