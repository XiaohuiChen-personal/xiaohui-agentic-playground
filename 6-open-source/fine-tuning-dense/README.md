# Full Fine-Tuning: Qwen2.5-7B on AG News

This folder contains a complete **full fine-tuning** experiment training Qwen2.5-7B-Instruct on the AG News text classification dataset using NVIDIA's optimized PyTorch Docker container.

## Overview

| Aspect | Details |
|--------|---------|
| **Model** | Qwen/Qwen2.5-7B-Instruct (7.62B parameters) |
| **Task** | 4-class text classification (World, Sports, Business, Sci/Tech) |
| **Dataset** | AG News (120K training examples) |
| **Method** | Full fine-tuning (100% of parameters updated) |
| **Hardware** | NVIDIA DGX Spark (GB10, 128 GB unified memory) |
| **Container** | `nvcr.io/nvidia/pytorch:25.11-py3` |

---

## Why Full Fine-Tuning?

| Aspect | Full Fine-Tuning | LoRA/QLoRA |
|--------|------------------|------------|
| Parameters updated | 7,615,616,512 (100%) | ~70M (1%) |
| Memory required | ~60-70 GB | ~16-24 GB |
| Training time | ~10 hours | 2-4 hours |
| Output size | ~14 GB | ~200 MB |
| Quality potential | Highest | Good |
| Risk of overfitting | Higher | Lower |

Full fine-tuning is ideal when you need **maximum accuracy** and have sufficient compute resources.

---

## Performance Optimizations

This experiment implements **5 key optimizations** for DGX Spark:

### 1. NVIDIA Docker Container (Critical)

Using `nvcr.io/nvidia/pytorch:25.11-py3` instead of pip-installed PyTorch:

| Metric | venv (pip install) | Docker Container |
|--------|-------------------|------------------|
| **TFLOPS** | 4.5 (3.6% of peak) | 38.2 (30.6% of peak) |
| **sm_121 support** | ⚠️ Partial (fallback kernels) | ✅ Native |
| **Flash Attention 2** | ❌ Not available | ✅ Compiled for Blackwell |
| **Transformer Engine** | ❌ Not available | ✅ FP8 support |
| **Training time** | 50-60+ hours | ~10 hours |

**Why the difference?** The GB10 (sm_121) is a new GPU architecture. Pip-installed PyTorch only has binary-compatible kernels (sm_120), running at ~3.6% efficiency. NVIDIA's container has optimized kernels.

### 2. cuDNN Benchmark Mode

```python
torch.backends.cudnn.benchmark = True
```

- **Impact**: 5-10% speedup
- **Why**: Auto-tunes convolution algorithms for consistent input sizes (512 tokens)

### 3. Sequence Packing

```python
SFTConfig(packing=True, ...)
```

- **Impact**: 30-40% speedup (biggest impact!)
- **Why**: Average sequence is ~120 tokens, padded to 512. Without packing, 75% of compute is wasted on padding. Packing combines multiple sequences into one batch.

| Metric | Without Packing | With Packing |
|--------|-----------------|--------------|
| Steps | 3,750 | 1,965 |
| Tokens/batch | ~120 (avg) | 512 (full) |
| Wasted compute | ~75% | ~0% |

### 4. Flash Attention 2

```python
model = AutoModelForCausalLM.from_pretrained(
    ...,
    attn_implementation="flash_attention_2",
)
```

- **Impact**: 10-15% speedup
- **Why**: Memory-efficient attention with optimized CUDA kernels for Blackwell

### 5. Optimized Batch Configuration

```python
BATCH_SIZE = 8  # Per device
GRADIENT_ACCUMULATION_STEPS = 4  # Effective batch = 32
DATALOADER_NUM_WORKERS = 4  # Parallel data loading
```

- **Impact**: 10-15% speedup
- **Why**: Larger batches = better GPU utilization, fewer gradient sync points

---

## Training Results

### Performance

| Metric | Value |
|--------|-------|
| **GPU Utilization** | 95% |
| **Training Speed** | 0.05 it/s |
| **Total Steps** | 1,965 |
| **Training Time** | ~10-11 hours |
| **Final Loss** | TBD (training in progress) |

### Comparison to Baseline

| Setup | Training Time | Speedup |
|-------|---------------|---------|
| venv (no optimizations) | ~50-60 hours | 1x |
| Docker (no optimizations) | ~15 hours | 3-4x |
| Docker + all optimizations | **~10 hours** | **5-6x** |

---

## File Structure

```
fine-tuning-dense/
├── fine_tuning_full.ipynb        # Main training notebook (run in Docker)
├── base_model_performance.ipynb  # Base model evaluation (78.63% accuracy)
├── base_model_results.json       # Detailed evaluation metrics
├── checkpoints/                  # Fine-tuned model weights
│   └── qwen7b-ag-news-full/      # Training checkpoints
│       └── final/                # Final model (after training)
├── adapters/                     # LoRA adapter weights (for future use)
├── datasets/                     # Prepared training data
│   └── train.jsonl               # 120K examples in chat format
├── data_prep/                    # Dataset preparation scripts
│   ├── convert_dataset.py        # Convert AG News to chat format
│   ├── config.py                 # Prompts and category definitions
│   └── README.md                 # Data preparation docs
├── *.png                         # Visualizations (confusion matrix, etc.)
└── README.md                     # This file
```

---

## Quick Start

### 1. Start the Training Container

```bash
cd ~/Projects/xiaohui-agentic-playground/6-open-source

# Stop any running inference containers
./start_docker.sh stop

# Start the training container with Jupyter Lab
./start_docker.sh start finetune
```

### 2. Access Jupyter Lab

Open http://localhost:8888 in your browser.

### 3. Run the Notebook

Navigate to `fine_tuning_full.ipynb` and run all cells.

### 4. Monitor Progress

```bash
# Check container status
./start_docker.sh status

# View logs
./start_docker.sh logs finetune

# Check GPU usage
nvidia-smi
```

---

## Training Configuration

### Hyperparameters

| Parameter | Value | Explanation |
|-----------|-------|-------------|
| `learning_rate` | 2e-5 | Lower than LoRA (updates all params) |
| `num_train_epochs` | 1 | Full fine-tuning often needs fewer epochs |
| `per_device_train_batch_size` | 8 | Optimized for DGX Spark |
| `gradient_accumulation_steps` | 4 | Effective batch = 32 |
| `max_seq_length` | 512 | Sufficient for AG News (~120 avg tokens) |
| `gradient_checkpointing` | True | Essential for 7B model |
| `bf16` | True | BFloat16 for speed + stability |
| `packing` | True | Pack multiple sequences per batch |

### Memory Breakdown

| Component | Memory |
|-----------|--------|
| Model weights (BF16) | ~15 GB |
| Adam optimizer states | ~30 GB |
| Gradients | ~15 GB |
| **Base total** | **~60 GB** |
| Activations (with checkpointing) | ~10-20 GB |
| **Total during training** | **~70-80 GB** |

---

## Dataset Details

### AG News Classification

| Category | Training Examples | Description |
|----------|-------------------|-------------|
| World | 30,000 | Politics, government, international affairs |
| Sports | 30,000 | Athletic events, games, teams |
| Business | 30,000 | Companies, markets, finance |
| Sci/Tech | 30,000 | Technology, scientific research |
| **Total** | **120,000** | |

### Data Format

```json
{
  "messages": [
    {"role": "system", "content": "You are a news article classifier..."},
    {"role": "user", "content": "Classify the following news article:\n\n[article text]"},
    {"role": "assistant", "content": "{\"category\":\"World\"}"}
  ]
}
```

### Base Model Performance

Before fine-tuning, Qwen2.5-7B achieved:

| Metric | Value |
|--------|-------|
| Accuracy | 78.63% |
| F1 (macro) | 77.80% |
| World F1 | 83.78% |
| Sports F1 | 96.72% |
| Business F1 | 84.35% |
| **Sci/Tech F1** | **46.37%** (weak point) |

**Target after fine-tuning**: 85-92% accuracy, improved Sci/Tech classification.

---

## Docker Container Details

### Why NVIDIA's PyTorch Container?

The container `nvcr.io/nvidia/pytorch:25.11-py3` provides:

1. **Native sm_121 kernels** - Compiled for Blackwell GB10
2. **Flash Attention 2** - Optimized for long sequences
3. **Transformer Engine 2.9+** - FP8 support for future optimization
4. **Triton 3.5** - Custom kernel compilation
5. **CUDA 13.0** - Latest CUDA features

### Container Configuration

```yaml
# docker-compose-finetune.yml
services:
  finetune:
    image: nvcr.io/nvidia/pytorch:25.11-py3
    ports:
      - "8888:8888"    # Jupyter Lab
      - "6006:6006"    # TensorBoard
    volumes:
      - ./fine-tuning-dense:/fine-tuning
      - ~/.cache/huggingface:/root/.cache/huggingface
    working_dir: /fine-tuning
    shm_size: '32gb'
```

---

## Troubleshooting

### Out of Memory (OOM)

If you encounter OOM errors:

1. **Reduce batch size**: `BATCH_SIZE = 4` (and increase `GRADIENT_ACCUMULATION_STEPS = 8`)
2. **Ensure gradient checkpointing is enabled**: `USE_GRADIENT_CHECKPOINTING = True`
3. **Stop other processes**: `./start_docker.sh stop` before training

### Slow Training

If training is slower than expected:

1. **Verify Docker container**: Check that you're running inside the NVIDIA container
2. **Check GPU utilization**: `nvidia-smi` should show ~95% utilization
3. **Enable all optimizations**: cuDNN benchmark, packing, Flash Attention 2

### Container Issues

```bash
# Restart the container
./start_docker.sh stop
./start_docker.sh start finetune

# Check logs
./start_docker.sh logs finetune

# Verify GPU access
docker exec pytorch-finetune nvidia-smi
```

---

## Next Steps

After training completes:

1. **Evaluate the fine-tuned model** on the test set
2. **Compare accuracy** with base model (78.63%)
3. **Serve with vLLM** for inference
4. **Try LoRA/QLoRA** for comparison

---

## References

- [Qwen2.5 Model Card](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct)
- [AG News Dataset](https://huggingface.co/datasets/ag_news)
- [TRL Documentation](https://huggingface.co/docs/trl)
- [NVIDIA PyTorch Container](https://catalog.ngc.nvidia.com/orgs/nvidia/containers/pytorch)
- [DGX Spark Documentation](https://docs.nvidia.com/dgx/dgx-spark)
