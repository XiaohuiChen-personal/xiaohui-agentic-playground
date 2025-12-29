# xiaohui-agentic-playground

A playground for exploring agentic AI systems and workflow patterns.

## Overview

This repository contains experiments with different agentic design patterns for building LLM-powered applications, including:

- **Prompt Chaining** - Decomposing complex tasks into sequential subtasks
- **Routing** - Dynamically directing inputs to specialized handlers
- **Orchestrator-Worker** - Coordinating multiple specialized workers
- **Multi-Agent Adversarial Simulation** - Agents with opposing objectives engaging in realistic exchanges

## Prerequisites

- **Python 3.12+**
- **[UV](https://docs.astral.sh/uv/)** - Fast Python package installer and resolver
- **API Keys** - OpenAI and Anthropic API keys

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
│   └── email_battle/            # CrewAI implementation
│       └── README.md            # Detailed documentation
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
| `python-dotenv` | Load environment variables from `.env` |
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

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
