# xiaohui-agentic-playground

A playground for agentic experiments.

## Prerequisites

- Python 3.12+
- [UV](https://docs.astral.sh/uv/) (fast Python package installer)

### Install UV

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or with Homebrew
brew install uv
```

## Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/jack25409440/xiaohui-agentic-playground.git
   cd xiaohui-agentic-playground
   ```

2. **Create a virtual environment with Python 3.12**
   ```bash
   uv venv --python 3.12
   ```

3. **Activate the virtual environment**
   ```bash
   # macOS/Linux
   source .venv/bin/activate

   # Windows
   .venv\Scripts\activate
   ```

4. **Install dependencies**
   ```bash
   uv sync
   ```

## Adding Dependencies

To add new packages:

```bash
uv add <package-name>
```

For development dependencies:

```bash
uv add --dev <package-name>
```

## Environment Variables

Copy the example environment file and fill in your values:

```bash
cp .env.example .env
```

Then edit `.env` with your API keys and configuration.
