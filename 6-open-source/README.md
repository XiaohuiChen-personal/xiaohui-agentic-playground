# Open Source LLM Inference & Fine-Tuning

Run open-source LLMs locally on DGX Spark with **vLLM** (via Docker) for inference and **Unsloth** for fine-tuning (Full/LoRA/QLoRA).

## Features

- **High-Performance Inference**: vLLM with continuous batching for hundreds of concurrent requests
- **OpenAI-Compatible API**: Drop-in replacement for OpenAI API calls
- **Full Fine-Tuning**: Train 7B models in ~10 hours with Unsloth optimizations
- **LoRA/QLoRA**: Parameter-efficient fine-tuning with Unsloth (2x faster)
- **Docker-Based**: All containers optimized for Blackwell GB10 (sm_121)

## System Requirements

| Component | Details |
|-----------|---------|
| System | NVIDIA DGX Spark |
| GPU | NVIDIA GB10 (Grace Blackwell) |
| Memory | 128 GB LPDDR5x unified memory |
| Bandwidth | 273 GB/s |
| Compute | sm_121 (12.1) |
| CUDA | 13.0+ |
| Inference Container | `nvcr.io/nvidia/vllm:25.12-py3` |
| Training Container | `unsloth-dgx-spark:latest` (built from Dockerfile) |

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

### Option 1: GPT-OSS-20B (Recommended - Fastest)

Run **GPT-OSS-20B** (Mixture of Experts) - the fastest model on DGX Spark:

```bash
cd 6-open-source

# Start GPT-OSS-20B on port 8000
./start_docker.sh start gpt-oss

# Check status
./start_docker.sh status

# Stop
./start_docker.sh stop
```

**Why GPT-OSS-20B?**
- **15.5 TPS** (4x faster than Llama-70B, 58% faster than Mistral-24B)
- Only 3.6B active parameters per token (MoE architecture)
- 128K context window
- Built-in chain-of-thought reasoning
- Apache 2.0 license for fine-tuning

### Option 2: Single Large Model (Llama 70B)

Run one 70B model with full GPU allocation:

```bash
cd 6-open-source

# Start Llama 3.3 70B on port 8000
./start_docker.sh start single

# Check status
./start_docker.sh status

# Stop
./start_docker.sh stop
```

### Option 3: Two Medium Models (Multi-Model)

Run Mistral-Small 24B + Qwen3 32B simultaneously (both NVFP4):

```bash
# Start both models (sequential startup for memory management)
./start_docker.sh start dual

# Check status
./start_docker.sh status

# Stop
./start_docker.sh stop
```

### Option 4: Qwen2.5-7B (Fine-Tuning Practice)

Run **Qwen2.5-7B** (Dense) - ideal for fine-tuning experiments:

```bash
cd 6-open-source

# Start Qwen2.5-7B on port 8000
./start_docker.sh start qwen7b

# Check status
./start_docker.sh status

# Stop
./start_docker.sh stop
```

### Using the Helper Script

```bash
# Inference modes
./start_docker.sh start gpt-oss   # Fastest inference (GPT-OSS-20B)
./start_docker.sh start qwen7b    # Fine-tuning practice (Qwen2.5-7B)
./start_docker.sh start single    # Maximum quality (Llama 70B)
./start_docker.sh start dual      # Multi-agent (Mistral + Qwen3)

# Training mode
./start_docker.sh start finetune  # All fine-tuning methods

# Management
./start_docker.sh status          # Check health
./start_docker.sh logs            # View logs
./start_docker.sh stop            # Stop all
```

---

## Model Configurations

### GPT-OSS-20B (85% GPU) - Fastest

| Model | Architecture | Active Params | Context | TPS | Use Case |
|-------|--------------|---------------|---------|-----|----------|
| **openai/gpt-oss-20b** | MoE | 3.6B | 32K (128K max) | **15.5** | Speed + reasoning |

### Qwen2.5-7B (85% GPU) - Fine-Tuning Practice

| Model | Architecture | Parameters | Context | Est. TPS | Use Case |
|-------|--------------|------------|---------|----------|----------|
| **Qwen/Qwen2.5-7B-Instruct** | Dense | 7B | 32K (128K max) | **25-40** | Fine-tuning baseline |

### Single Dense Model (85% GPU)

| Model | VRAM Used | Context | TPS | Use Case |
|-------|-----------|---------|-----|----------|
| Llama 3.3 70B NVFP4 | ~50 GB | 8K tokens | 3.9 | Highest quality |

### Dual Medium Models (30% + 35% GPU)

| Model | Port | Weights | Allocation | Context |
|-------|------|---------|------------|---------|
| Mistral-Small 24B NVFP4 | 8000 | ~15 GB | 30% (~38 GB) | 32K tokens |
| Qwen3 32B NVFP4 | 8001 | ~20 GB | 35% (~45 GB) | 32K tokens |

---

## Fine-Tuning

All fine-tuning methods use a single optimized Docker container with Unsloth.

### Quick Start

```bash
# Stop any running inference containers
./start_docker.sh stop

# Start the fine-tuning container with Jupyter Lab
./start_docker.sh start finetune

# Access Jupyter at http://localhost:8888

# Choose your notebook:
# - Full Fine-Tuning: fine_tuning_full.ipynb or fine_tuning_full_unsloth.ipynb
# - LoRA:             fine_tuning_lora.ipynb
# - QLoRA:            fine_tuning_qlora.ipynb
```

### Why Unsloth Docker?

| Aspect | venv (pip install) | Unsloth Docker |
|--------|-------------------|----------------|
| **TFLOPS** | 4.5 (3.6% of peak) | 38.2 (30.6% of peak) |
| **Training time** | 50-60+ hours | ~10 hours |
| sm_121 support | ⚠️ Fallback kernels | ✅ Native |
| xformers | ❌ Compilation fails | ✅ v0.0.33 compiled |
| Flash Attention 2 | ❌ | ✅ |

The DGX Spark's GB10 (sm_121) requires optimized containers for full performance.

### Fine-Tuning Methods Comparison

| Method | Memory | Time | Output | Best For |
|--------|--------|------|--------|----------|
| **Full Fine-Tuning** | ~70 GB | ~10 hours | ~14 GB | Maximum quality |
| **LoRA** | ~25 GB | ~4-6 hours | ~200 MB | Good balance |
| **QLoRA** | ~12 GB | ~6-8 hours | ~200 MB | Memory constrained |

### Current Experiment Results

| Aspect | Details |
|--------|---------|
| Model | Qwen2.5-7B-Instruct |
| Task | AG News 4-class classification |
| Dataset | 120K training examples |
| Base accuracy | 78.63% |
| **Fine-tuned accuracy** | **88.33%** (+9.70pp) |

**Key Achievement**: Sci/Tech F1 improved from 46.37% to 90.04% (+43.67pp)!

➡️ **[See detailed fine-tuning documentation](fine-tuning-dense/README.md)**

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

---

## File Structure

```
6-open-source/
├── docker-compose-gpt-oss.yml     # GPT-OSS-20B MoE (fastest - 15.5 TPS)
├── docker-compose-qwen7b.yml      # Qwen2.5-7B (fine-tuning inference)
├── docker-compose-single.yml      # Single 70B model (Llama 3.3 70B NVFP4)
├── docker-compose-dual-medium.yml # Two medium models (Mistral 24B + Qwen3 32B)
├── docker-compose-finetune.yml    # Fine-tuning container (Unsloth optimized)
├── start_docker.sh                # Docker management script
├── test_inference.py              # API test suite
├── finetune_template.py           # Unsloth fine-tuning template
├── fine-tuning-dense/             # All fine-tuning experiments
│   ├── Dockerfile.dgx-spark       # DGX Spark optimized Dockerfile
│   ├── fine_tuning_full.ipynb     # Full fine-tuning notebook
│   ├── fine_tuning_full_unsloth.ipynb # Full fine-tuning (Unsloth)
│   ├── fine_tuning_lora.ipynb     # LoRA notebook
│   ├── fine_tuning_qlora.ipynb    # QLoRA notebook
│   ├── base_model_performance.ipynb  # Base model evaluation
│   ├── checkpoints/               # Fine-tuned model weights
│   ├── adapters/                  # LoRA adapter weights
│   ├── datasets/                  # Training datasets (120K examples)
│   ├── data_prep/                 # Dataset preparation scripts
│   └── README.md                  # Fine-tuning documentation
├── email_battle_open_source/      # CrewAI Email Battle using local models
├── single_model_speed_test/       # Speed test benchmarks
├── dual_model_speed_test/         # Dual model benchmarks
└── README.md                      # This file
```

---

## Workflow Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                     Unified Memory (128 GB)                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  INFERENCE MODE                 TRAINING MODE                    │
│  ──────────────                 ─────────────                    │
│  ┌─────────────┐                ┌─────────────────┐              │
│  │ vLLM Docker │                │ Unsloth Docker  │              │
│  │             │                │                 │              │
│  │ GPT-OSS-20B │                │ Full Fine-Tune  │              │
│  │ (85% GPU)   │                │ LoRA / QLoRA    │              │
│  │             │      OR        │                 │              │
│  │ - or -      │                │ All methods in  │              │
│  │ Qwen2.5-7B  │                │ one container!  │              │
│  │ Mistral-24B │                │                 │              │
│  │ Llama-70B   │                │ (90% GPU)       │              │
│  └─────────────┘                └─────────────────┘              │
│                                                                  │
│  ./start_docker.sh start       ./start_docker.sh start finetune │
│           gpt-oss              → Open http://localhost:8888     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

⚠️  Only ONE mode can run at a time - stop inference before training!
```

### Docker Commands Reference

| Action | Command |
|--------|---------|
| Start GPT-OSS-20B (fastest) | `./start_docker.sh start gpt-oss` |
| Start Qwen2.5-7B (fine-tuning inference) | `./start_docker.sh start qwen7b` |
| Start fine-tuning container | `./start_docker.sh start finetune` |
| Build fine-tuning image | `./start_docker.sh build finetune` |
| Check status | `./start_docker.sh status` |
| View logs | `./start_docker.sh logs` |
| Stop all | `./start_docker.sh stop` |

---

## Troubleshooting

### Container Won't Start

```bash
# Check container logs
docker logs pytorch-finetune

# Verify GPU access
docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi
```

### Out of Memory

- Reduce `--gpu-memory-utilization`
- Reduce `--max-model-len` (e.g., 4096)
- Use quantized models (AWQ/NVFP4)
- Use smaller model or QLoRA

### Model Download Slow

Models are cached in `~/.cache/huggingface`. First download takes time but subsequent starts are fast.

### Permission Denied (Docker)

```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Apply changes (logout/login or use newgrp)
newgrp docker
```
