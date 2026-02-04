# Fine-Tuning Qwen2.5-7B on AG News

This folder contains fine-tuning experiments for Qwen2.5-7B-Instruct on the AG News text classification dataset. Three methods are supported: **Full Fine-Tuning**, **LoRA**, and **QLoRA** - all using Unsloth's DGX Spark optimized Docker image.

## Results Summary

### QLoRA Fine-Tuning (Completed)

| Metric | Base Model | QLoRA Fine-Tuned | Improvement |
|--------|------------|------------------|-------------|
| **Accuracy** | 78.76% | **95.14%** | **+16.38%** |
| **F1 (macro)** | 77.97% | **95.13%** | **+17.16%** |
| **Sci/Tech F1** | 62.06% | **~93.2%** | **+31.14%** |
| **Business Precision** | 63.66% | **~95.8%** | **+32.14%** |

| Training Aspect | Value |
|-----------------|-------|
| **Training Time** | ~6 hours |
| **Final Loss** | 0.4625 |
| **Adapter Size** | 177.42 MB |
| **Trainable Parameters** | 40.4M (0.53% of 7.6B) |
| **Inference Throughput** | 33.6 articles/second (vLLM) |

### LoRA Fine-Tuning
*Pending*

### Full Fine-Tuning
*Pending - will be re-run*

---

## Quick Comparison: Three Fine-Tuning Methods

| Method | Parameters Updated | Memory | Training Time | Output Size | Best For |
|--------|-------------------|--------|---------------|-------------|----------|
| **Full** | 7.6B (100%) | ~70 GB | ~10 hours | ~14 GB | Maximum accuracy |
| **LoRA** | ~70M (1%) | ~20-25 GB | ~4-6 hours | ~200 MB | Good accuracy, faster |
| **QLoRA** | ~70M (1%) | ~8-12 GB | ~6-8 hours | ~200 MB | Memory-constrained |

---

## Quick Start

### Training (All Methods)

All three methods use the same Docker container with Unsloth optimizations:

```bash
cd ~/Projects/xiaohui-agentic-playground/6-open-source

# Start the fine-tuning container (Jupyter on port 8888)
./start_docker.sh start finetune

# Open http://localhost:8888

# Choose your notebook:
# - Full Fine-Tuning: fine_tuning_full_unsloth.ipynb
# - LoRA:             fine_tuning_lora.ipynb
# - QLoRA:            fine_tuning_qlora.ipynb
```

### Inference with QLoRA Adapter

```bash
# Start vLLM with QLoRA adapter loaded
./start_docker.sh start qwen7b-qlora

# Use the API with model="qlora-ag-news"
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qlora-ag-news",
    "messages": [{"role": "user", "content": "Classify: Apple releases new iPhone"}]
  }'
```

### Common Commands

```bash
# Check status
./start_docker.sh status

# View logs
./start_docker.sh logs finetune

# Stop container
./start_docker.sh stop

# Rebuild image (if needed)
./start_docker.sh build finetune
```

---

## When to Use Each Method

### Full Fine-Tuning
- **Use when**: Maximum accuracy is critical, you have ~70+ GB GPU memory
- **Pros**: Best possible quality, all parameters optimized for your task
- **Cons**: Longest training time, largest output, risk of overfitting
- **Notebook**: `fine_tuning_full_unsloth.ipynb`

### LoRA (Low-Rank Adaptation)
- **Use when**: Good accuracy with faster training, ~20-25 GB GPU memory
- **Pros**: 2-4x faster, small adapter files, easy to swap adapters
- **Cons**: Slightly lower accuracy ceiling than full fine-tuning
- **Notebook**: `fine_tuning_lora.ipynb`

### QLoRA (Quantized LoRA)
- **Use when**: Memory is limited (~8-12 GB), or fine-tuning larger models
- **Pros**: Most memory-efficient, enables fine-tuning models that wouldn't otherwise fit
- **Cons**: Potential quality loss from 4-bit quantization (though results show excellent performance)
- **Notebook**: `fine_tuning_qlora.ipynb`
- **Results**: **95.14% accuracy** - exceeds all targets!

---

## Code Difference: LoRA vs QLoRA

The only difference is how you load the model:

```python
from unsloth import FastLanguageModel

# LoRA (16-bit base model)
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="unsloth/Qwen2.5-7B-Instruct",
    load_in_4bit=False,  # Full precision base model
    use_exact_model_name=True,
)

# QLoRA (4-bit quantized base model)
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="unsloth/Qwen2.5-7B-Instruct",
    load_in_4bit=True,   # 4-bit quantized base model
    use_exact_model_name=True,
)

# Both use the same LoRA configuration
model = FastLanguageModel.get_peft_model(
    model,
    r=16,                # LoRA rank
    lora_alpha=32,       # LoRA scaling
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    use_gradient_checkpointing=False,  # Disabled for speed on DGX Spark
)
```

---

## QLoRA Results Detail

### Per-Category Performance

| Category | Correct | Total | Accuracy | Notes |
|----------|---------|-------|----------|-------|
| **World** | 1,818 | 1,900 | 95.7% | Excellent |
| **Sports** | 1,894 | 1,900 | **99.7%** | Near-perfect |
| **Business** | 1,690 | 1,900 | 88.9% | Most challenging |
| **Sci/Tech** | 1,829 | 1,900 | 96.3% | Massive improvement |

### Key Achievements

1. **All Targets Exceeded**: 95.14% accuracy vs 85% target
2. **Sci/Tech Transformed**: From 46.8% recall (base) to 96.3% recall
3. **Sports Near-Perfect**: 99.7% accuracy (1,894/1,900)
4. **Efficient Training**: Only 0.53% of parameters trained

### Remaining Challenge

- **Business-Sci/Tech Confusion**: 155 Business articles misclassified as Sci/Tech
- This represents inherent overlap (e.g., "Apple stock rises after iPhone launch" - both Business and Tech)

---

## Docker Container

All fine-tuning methods use the same optimized Docker container:

| Aspect | Details |
|--------|---------|
| **Image** | `unsloth-dgx-spark:latest` |
| **Base** | `nvcr.io/nvidia/pytorch:25.11-py3` |
| **Port** | 8888 (Jupyter Lab) |
| **Command** | `./start_docker.sh start finetune` |

### Key Optimizations (Built into Image)

| Optimization | Benefit |
|--------------|---------|
| Triton compiled for Blackwell (sm_121) | Native GPU kernels |
| xformers v0.0.33 compiled for sm_121 | Efficient attention |
| Unsloth optimized kernels | 2x faster training |
| Flash Attention 2 | Memory-efficient attention |
| bitsandbytes | 4-bit quantization for QLoRA |

### First-Time Build

The first time you run `./start_docker.sh start finetune`, it builds the optimized image:

- **Build time**: ~8-10 minutes (compiling Triton and xformers from source)
- **Subsequent starts**: <10 seconds (uses cached image)

---

## File Structure

```
6-open-source/
├── fine-tuning-dense/                   # All fine-tuning experiments (this folder)
│   ├── Dockerfile.dgx-spark             # DGX Spark optimized Dockerfile
│   ├── fine_tuning_full_unsloth.ipynb   # Full fine-tuning (Unsloth optimized)
│   ├── fine_tuning_lora.ipynb           # LoRA fine-tuning
│   ├── fine_tuning_qlora.ipynb          # QLoRA fine-tuning
│   ├── base_model_performance.ipynb     # Base model evaluation (78.76% accuracy)
│   ├── qlora_fine_tuning_performance.ipynb # QLoRA evaluation (95.14% accuracy)
│   ├── checkpoints/                     # Full fine-tuned model weights
│   ├── adapters/                        # LoRA/QLoRA adapter output
│   │   └── qwen7b-ag-news-qlora/        # QLoRA adapter (177 MB)
│   ├── datasets/                        # Prepared training data (train.jsonl)
│   └── README.md                        # This file
│
├── docker-compose-finetune.yml          # Fine-tuning container config
├── docker-compose-qwen7b.yml            # Inference container (base + LoRA)
└── start_docker.sh                      # Container management script
```

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

---

## Troubleshooting

### Out of Memory (OOM)

If you encounter OOM errors:

1. **Use QLoRA** instead of LoRA or Full fine-tuning
2. **Reduce batch size**: `BATCH_SIZE = 4` (and increase `GRADIENT_ACCUMULATION_STEPS = 8`)
3. **Enable gradient checkpointing**: `use_gradient_checkpointing="unsloth"`
4. **Stop other processes**: `./start_docker.sh stop` before training

### Slow Training

If training is slower than expected:

1. **Verify Docker container**: Check that you're running inside the Unsloth container
2. **Check GPU utilization**: `nvidia-smi` should show ~95% utilization
3. **Ensure Unsloth optimizations**: Use `FastLanguageModel` not `AutoModelForCausalLM`
4. **Disable gradient checkpointing**: For DGX Spark with ample memory, set `use_gradient_checkpointing=False`

### Container Issues

```bash
# Restart the container
./start_docker.sh stop
./start_docker.sh start finetune

# Check logs
./start_docker.sh logs finetune

# Rebuild image
./start_docker.sh build finetune

# Verify GPU access
docker exec pytorch-finetune nvidia-smi
```

---

## References

- [Qwen2.5 Model Card](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct)
- [AG News Dataset](https://huggingface.co/datasets/ag_news)
- [Unsloth Documentation](https://docs.unsloth.ai/)
- [Unsloth DGX Spark Guide](https://docs.unsloth.ai/basics/fine-tuning-llms-with-nvidia-dgx-spark-and-unsloth)
- [TRL Documentation](https://huggingface.co/docs/trl)
- [NVIDIA PyTorch Container](https://catalog.ngc.nvidia.com/orgs/nvidia/containers/pytorch)
