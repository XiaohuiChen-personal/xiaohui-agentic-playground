# xiaohui-agentic-playground

A playground for exploring agentic AI systems and workflow patterns.

## Overview

This repository contains experiments with different agentic design patterns for building LLM-powered applications, including:

- **Prompt Chaining** - Decomposing complex tasks into sequential subtasks
- **Routing** - Dynamically directing inputs to specialized handlers
- **Orchestrator-Worker** - Coordinating multiple specialized workers

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
git clone https://github.com/jack25409440/xiaohui-agentic-playground.git
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
│   └── agentic_systems.ipynb    # Main notebook with agentic patterns
├── .env.example                  # Template for environment variables
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

## Notebooks

### 1. Agentic Systems (`1-agentic-workflow/agentic_systems.ipynb`)

Explores different agentic workflow patterns using news classification as a benchmark:

- **Prompt Chaining**: Multi-step extraction → analysis → classification pipeline
- **Routing**: Dynamic routing to specialized classifiers based on content
- **Orchestrator-Worker**: Parallel worker evaluation with orchestrator synthesis

Uses the [AG News dataset](https://huggingface.co/datasets/ag_news) with 4 categories: World, Sports, Business, Sci/Tech.

## License

MIT
