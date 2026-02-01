# Open Source LLM Inference & Fine-Tuning

Run open-source LLMs locally on DGX Spark with **vLLM** (via Docker) for inference and **Unsloth** for fine-tuning.

## Features

- **High-Performance Inference**: vLLM with continuous batching for hundreds of concurrent requests
- **OpenAI-Compatible API**: Drop-in replacement for OpenAI API calls
- **Fine-Tuning**: Efficient LoRA/QLoRA training with Unsloth (2-4x speedup)
- **Docker-Based**: NVIDIA's official vLLM container with CUDA 13.1 support

## System Requirements

| Component | Details |
|-----------|---------|
| System | NVIDIA DGX Spark |
| GPU | NVIDIA GB10 (Grace Blackwell) |
| Memory | 128 GB LPDDR5x unified memory |
| Bandwidth | 273 GB/s |
| Compute | sm_121 (12.1) |
| CUDA | 13.0+ |
| Container | `nvcr.io/nvidia/vllm:25.12-py3` |

## Prerequisites

```bash
# Docker must be installed with NVIDIA Container Toolkit
docker --version
nvidia-smi

# Add yourself to docker group (if needed)
sudo usermod -aG docker $USER
# Then logout and login, or use: newgrp docker
```

---

## Quick Start

### Option 1: Single Large Model (Recommended)

Run one 70B model with full GPU allocation:

```bash
cd 6-open-source

# Start Llama 3.3 70B on port 8000
docker compose -f docker-compose-single.yml up -d

# Check status
docker logs -f vllm-llama-70b

# Stop
docker compose -f docker-compose-single.yml down
```

### Option 2: Two Medium Models (Recommended for Multi-Model)

Run Mistral-Small 24B + Qwen3 32B simultaneously (both NVFP4):

```bash
# IMPORTANT: Start models sequentially to avoid memory contention!
# Start Mistral first (smaller model)
docker compose -f docker-compose-dual-medium.yml up -d mistral-24b

# Wait for Mistral to be ready (check health endpoint)
while ! curl -s http://localhost:8000/health > /dev/null 2>&1; do
  echo "Waiting for Mistral..."; sleep 15
done
echo "Mistral ready!"

# Now start Qwen3
docker compose -f docker-compose-dual-medium.yml up -d qwen3-32b

# Check status
docker ps
docker logs vllm-mistral-24b
docker logs vllm-qwen3-32b

# Stop
docker compose -f docker-compose-dual-medium.yml down
```

> **⚠️ Sequential Startup Required**: Both models share the same GPU memory. Starting them simultaneously causes memory contention. Always start the smaller model (Mistral) first, wait until ready, then start the larger model (Qwen3).

### Using the Helper Script

```bash
# Start (single model)
./start_docker.sh start single

# Start (dual medium models)
./start_docker.sh start dual

# Check status
./start_docker.sh status

# View logs
./start_docker.sh logs

# Stop all
./start_docker.sh stop
```

---

## Model Configurations

### Single Model (85% GPU)

Best for maximum quality with one large model:

| Model | VRAM Used | Context | Use Case |
|-------|-----------|---------|----------|
| Llama 3.3 70B NVFP4 | ~50 GB | 8K tokens | General reasoning |
| Qwen 2.5 72B AWQ | ~50 GB | 8K tokens | Multilingual + code |
| DeepSeek V3 (smaller) | ~50 GB | 8K tokens | Code generation |

### Dual Medium Models (30% + 35% GPU)

Best for running two capable models from different providers:

| Model | Port | Weights | Allocation | Context |
|-------|------|---------|------------|---------|
| Mistral-Small 24B NVFP4 | 8000 | ~15 GB | 30% (~38 GB) | 32K tokens |
| Qwen3 32B NVFP4 | 8001 | ~20 GB | 35% (~45 GB) | 32K tokens |

**Configuration**: Optimized for sequential processing (one request at a time) with long context windows.

**Model Strengths:**
- **Mistral-Small 24B (RedHatAI)**: European languages, fast inference, general reasoning
- **Qwen3 32B (Alibaba/NVIDIA)**: Coding, math, multilingual, thinking/reasoning

> **Note**: Both models use NVFP4 quantization for optimal Blackwell GPU performance. Sequential startup is required to avoid memory contention. The `max-num-seqs=1` setting allows maximum context length per request.

---

## API Usage

### Health Check

```bash
# Check if server is ready
curl http://localhost:8000/health

# List available models
curl http://localhost:8000/v1/models
```

### Python Client

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="EMPTY",
)

response = client.chat.completions.create(
    model="RedHatAI/Llama-3.3-70B-Instruct-NVFP4",  # Use actual model name
    messages=[{"role": "user", "content": "Explain quantum computing in simple terms."}],
    max_tokens=500,
)
print(response.choices[0].message.content)
```

### Concurrent Requests

```python
import asyncio
from openai import AsyncOpenAI

client = AsyncOpenAI(base_url="http://localhost:8000/v1", api_key="EMPTY")

async def batch_inference(prompts):
    tasks = [
        client.chat.completions.create(
            model="RedHatAI/Llama-3.3-70B-Instruct-NVFP4",
            messages=[{"role": "user", "content": p}],
        )
        for p in prompts
    ]
    return await asyncio.gather(*tasks)

# Process 50 prompts concurrently
results = asyncio.run(batch_inference([f"Question {i}" for i in range(50)]))
```

### Multi-Model Requests (Dual Mode)

```python
from openai import OpenAI

# Different clients for different models
mistral = OpenAI(base_url="http://localhost:8000/v1", api_key="EMPTY")
qwen = OpenAI(base_url="http://localhost:8001/v1", api_key="EMPTY")

# Use the right model for each task
general_response = mistral.chat.completions.create(
    model="RedHatAI/Mistral-Small-3.2-24B-Instruct-2506-NVFP4",
    messages=[{"role": "user", "content": "Explain this concept..."}],
)
coding_response = qwen.chat.completions.create(
    model="nvidia/Qwen3-32B-NVFP4",
    messages=[{"role": "user", "content": "Write a Python function..."}],
)
```

### Test Script

```bash
# Run inference tests
python test_inference.py
```

---

## Fine-Tuning with Unsloth

Unsloth provides 2-4x faster fine-tuning with 60% less memory.

### Important: Stop Inference First

```bash
# Fine-tuning needs full GPU access
docker compose -f docker-compose-single.yml down
```

### Setup Fine-Tuning Environment

```bash
# Create a separate venv for fine-tuning
python -m venv .venv-finetune
source .venv-finetune/bin/activate

# Install Unsloth
pip install "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"
pip install xformers trl peft accelerate bitsandbytes datasets
```

### Run Fine-Tuning

```bash
# Edit finetune_template.py with your settings
python finetune_template.py
```

### Fine-Tuning Configuration

Edit `finetune_template.py`:

```python
# Model to fine-tune
BASE_MODEL = "unsloth/Llama-3.1-8B-Instruct"

# LoRA settings
LORA_R = 16          # Rank (8-64, higher = more capacity)
LORA_ALPHA = 16      # Scaling factor
LOAD_IN_4BIT = True  # QLoRA for memory efficiency

# Training
BATCH_SIZE = 2
GRADIENT_ACCUMULATION = 4
LEARNING_RATE = 2e-4
NUM_EPOCHS = 3
```

### Supported Base Models

| Model | Unsloth ID | Notes |
|-------|------------|-------|
| Llama 3.2 3B | `unsloth/Llama-3.2-3B-Instruct` | Fast for testing |
| Llama 3.1 8B | `unsloth/Llama-3.1-8B-Instruct` | Good balance |
| Qwen 2.5 7B | `unsloth/Qwen2.5-7B-Instruct` | Strong multilingual |
| Mistral 7B | `unsloth/Mistral-7B-Instruct-v0.3` | Fast inference |

---

## File Structure

```
6-open-source/
├── docker-compose-single.yml      # Single 70B model (Llama 3.3 70B NVFP4)
├── docker-compose-dual-medium.yml # Two medium models (Mistral 24B + Qwen3 32B)
├── start_docker.sh                # Docker management script (handles sequential startup)
├── test_inference.py              # API test suite
├── finetune_template.py           # Unsloth fine-tuning template
├── email_battle_open_source/      # CrewAI Email Battle using local models
│   ├── src/email_battle/          # Flow and crew definitions
│   ├── email_battle_result.txt    # Latest battle output
│   └── README.md                  # Project documentation
└── README.md                      # This file
```

---

## Customizing Docker Compose

### Change Model

Edit `docker-compose-single.yml`:

```yaml
command: >
  vllm serve Qwen/Qwen2.5-72B-Instruct-AWQ  # Change model here
  --host 0.0.0.0
  --port 8000
  --gpu-memory-utilization 0.85
  --max-num-seqs 128
  --max-model-len 8192
  --dtype auto
  --enforce-eager
  --quantization awq  # Add if using AWQ model
```

### Key Parameters

| Parameter | Description | Single Mode | Dual Mode |
|-----------|-------------|-------------|-----------|
| `--gpu-memory-utilization` | % of VRAM to use | 0.85 | 0.30-0.35 |
| `--max-num-seqs` | Max concurrent sequences | 128 | 1 |
| `--max-model-len` | Max context length | 8192 | 32768 |
| `--enforce-eager` | Required for Blackwell | Always | Always |
| `--trust-remote-code` | Allow custom model code | If needed | If needed |

> **Dual Model Memory**: For dual models, we use `max-num-seqs=1` (sequential processing) which allows long 32K context windows within the lower memory allocation. This is ideal for agentic workflows like CrewAI where only one model processes at a time.

---

## Troubleshooting

### Container Won't Start

```bash
# Check container logs
docker logs vllm-llama-70b

# Verify GPU access
docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi
```

### Out of Memory

- Reduce `--gpu-memory-utilization`
- Reduce `--max-model-len` (e.g., 4096)
- Use quantized models (AWQ/NVFP4)
- Use smaller model

### Model Download Slow

Models are cached in `~/.cache/huggingface`. First download takes time but subsequent starts are fast.

```bash
# Pre-download a model
docker run --rm -v ~/.cache/huggingface:/root/.cache/huggingface \
  nvcr.io/nvidia/vllm:25.12-py3 \
  huggingface-cli download RedHatAI/Llama-3.3-70B-Instruct-NVFP4
```

### Port Already in Use

```bash
# Find process using port
lsof -i :8000

# Or change port in docker-compose file
```

### Permission Denied (Docker)

```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Apply changes (logout/login or use newgrp)
newgrp docker
```

---

## Workflow Summary

```
┌─────────────────────────────────────────────────────────────┐
│                   Unified Memory (128 GB)                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  INFERENCE MODE              FINE-TUNING MODE               │
│  ──────────────              ─────────────────              │
│  ┌─────────────┐             ┌─────────────────┐            │
│  │ vLLM Docker │             │                 │            │
│  │             │             │   Unsloth       │            │
│  │ Single 70B  │             │   Training      │            │
│  │ (85% GPU)   │     OR      │   (90% GPU)     │            │
│  │             │             │                 │            │
│  │ - or -      │             │                 │            │
│  │ Mistral 24B │             │                 │            │
│  │ + Qwen3 32B │             │                 │            │
│  │ (65% GPU)   │             │                 │            │
│  └─────────────┘             └─────────────────┘            │
│                                                             │
│  ./start_docker.sh start     python finetune_template.py    │
│                                                             │
└─────────────────────────────────────────────────────────────┘

⚠️  Stop inference containers before fine-tuning!
```
