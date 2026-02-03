# Fine-Tuning Qwen2.5-7B on AG News

This folder contains fine-tuning experiments for Qwen2.5-7B-Instruct on the AG News text classification dataset. Three methods are supported: **Full Fine-Tuning**, **LoRA**, and **QLoRA** - all using Unsloth's DGX Spark optimized Docker image.

## Quick Comparison: Three Fine-Tuning Methods

| Method | Parameters Updated | Memory | Training Time | Output Size | Best For |
|--------|-------------------|--------|---------------|-------------|----------|
| **Full** | 7.6B (100%) | ~70 GB | ~10 hours | ~14 GB | Maximum accuracy |
| **LoRA** | ~70M (1%) | ~20-25 GB | ~4-6 hours | ~200 MB | Good accuracy, faster |
| **QLoRA** | ~70M (1%) | ~8-12 GB | ~6-8 hours | ~200 MB | Memory-constrained |

---

## Quick Start

All three methods use the same Docker container with Unsloth optimizations:

```bash
cd ~/Projects/xiaohui-agentic-playground/6-open-source

# Start the fine-tuning container (Jupyter on port 8888)
./start_docker.sh start finetune

# Open http://localhost:8888

# Choose your notebook:
# - Full Fine-Tuning: fine_tuning_full.ipynb or fine_tuning_full_unsloth.ipynb
# - LoRA:             fine_tuning_lora.ipynb
# - QLoRA:            fine_tuning_qlora.ipynb
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

## Results: Full Fine-Tuning (Completed)

| Aspect | Details |
|--------|---------|
| **Model** | Qwen/Qwen2.5-7B-Instruct (7.62B parameters) |
| **Task** | 4-class text classification (World, Sports, Business, Sci/Tech) |
| **Dataset** | AG News (120K training, 7.6K test) |
| **Method** | Full fine-tuning (100% of parameters updated) |
| **Result** | **88.33% accuracy** (+9.70pp improvement) |
| **Hardware** | NVIDIA DGX Spark (GB10, 128 GB unified memory) |
| **Training Time** | ~10 hours (with optimizations) |
| **Container** | `unsloth-dgx-spark:latest` |

---

## When to Use Each Method

### Full Fine-Tuning
- **Use when**: Maximum accuracy is critical, you have ~70+ GB GPU memory
- **Pros**: Best possible quality, all parameters optimized for your task
- **Cons**: Longest training time, largest output, risk of overfitting
- **Notebook**: `fine_tuning_full.ipynb` or `fine_tuning_full_unsloth.ipynb`

### LoRA (Low-Rank Adaptation)
- **Use when**: Good accuracy with faster training, ~20-25 GB GPU memory
- **Pros**: 2-4x faster, small adapter files, easy to swap adapters
- **Cons**: Slightly lower accuracy ceiling than full fine-tuning
- **Notebook**: `fine_tuning_lora.ipynb`

### QLoRA (Quantized LoRA)
- **Use when**: Memory is limited (~8-12 GB), or fine-tuning larger models
- **Pros**: Most memory-efficient, enables fine-tuning models that wouldn't otherwise fit
- **Cons**: Potential quality loss from 4-bit quantization
- **Notebook**: `fine_tuning_qlora.ipynb`

---

## Code Difference: LoRA vs QLoRA

The only difference is how you load the model:

```python
from unsloth import FastLanguageModel

# LoRA (16-bit base model)
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="unsloth/Qwen2.5-7B-Instruct",
    load_in_4bit=False,  # Full precision base model
)

# QLoRA (4-bit quantized base model)
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="unsloth/Qwen2.5-7B-Instruct",
    load_in_4bit=True,   # 4-bit quantized base model
)

# Both use the same LoRA configuration
model = FastLanguageModel.get_peft_model(
    model,
    r=16,                # LoRA rank
    lora_alpha=32,       # LoRA scaling
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    use_gradient_checkpointing="unsloth",  # 30% less VRAM
)
```

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

To explicitly rebuild:
```bash
./start_docker.sh build finetune
```

---

## Performance Optimizations

This experiment implements **5 key optimizations** for DGX Spark:

### 1. Unsloth Docker Container (Critical)

Using `unsloth-dgx-spark:latest` instead of pip-installed packages:

| Metric | venv (pip install) | Docker Container |
|--------|-------------------|------------------|
| **TFLOPS** | 4.5 (3.6% of peak) | 38.2 (30.6% of peak) |
| **sm_121 support** | ⚠️ Partial (fallback kernels) | ✅ Native |
| **Flash Attention 2** | ❌ Not available | ✅ Compiled for Blackwell |
| **xformers** | ❌ Compilation fails | ✅ v0.0.33 compiled |
| **Training time** | 50-60+ hours | ~10 hours |

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
- **Why**: Average sequence is ~120 tokens, padded to 512. Without packing, 75% of compute is wasted on padding.

### 4. Flash Attention 2

```python
# Built into Unsloth's FastLanguageModel
model, tokenizer = FastLanguageModel.from_pretrained(...)
```

- **Impact**: 10-15% speedup
- **Why**: Memory-efficient attention with optimized CUDA kernels for Blackwell

### 5. Unsloth Gradient Checkpointing

```python
model = FastLanguageModel.get_peft_model(
    model,
    use_gradient_checkpointing="unsloth",  # 30% less VRAM
)
```

- **Impact**: 30% less memory, 2x larger batch possible
- **Why**: Unsloth's optimized checkpointing with minimal recomputation overhead

---

## Training Results

### Fine-Tuned Model Performance

| Metric | Base Model | Fine-Tuned | Improvement |
|--------|------------|------------|-------------|
| **Accuracy** | 78.63% | **88.33%** | **+9.70pp** |
| **F1 (macro)** | 77.80% | **88.38%** | **+10.58pp** |
| **World F1** | 83.78% | 86.10% | +2.32pp |
| **Sports F1** | 96.72% | 89.91% | -6.81pp |
| **Business F1** | 84.35% | 87.48% | +3.13pp |
| **Sci/Tech F1** | 46.37% | **90.04%** | **+43.67pp** |

### Training Statistics

| Metric | Value |
|--------|-------|
| **GPU Utilization** | 95% |
| **Training Speed** | 0.05 it/s |
| **Total Steps** | 1,965 |
| **Training Time** | ~10 hours |
| **Final Loss** | ~0.45 |

---

## File Structure

```
6-open-source/
├── fine-tuning-dense/                   # All fine-tuning experiments (this folder)
│   ├── Dockerfile.dgx-spark             # DGX Spark optimized Dockerfile
│   ├── fine_tuning_full.ipynb           # Full fine-tuning (original)
│   ├── fine_tuning_full_unsloth.ipynb   # Full fine-tuning (Unsloth optimized)
│   ├── fine_tuning_lora.ipynb           # LoRA fine-tuning
│   ├── fine_tuning_qlora.ipynb          # QLoRA fine-tuning
│   ├── base_model_performance.ipynb     # Base model evaluation (78.63% accuracy)
│   ├── full_finetuning_performance.ipynb # Fine-tuned model evaluation
│   ├── checkpoints/                     # Fine-tuned model weights (~14 GB)
│   ├── adapters/                        # LoRA adapter output (~200 MB)
│   ├── datasets/                        # Prepared training data (train.jsonl)
│   ├── data_prep/                       # Dataset preparation scripts
│   └── README.md                        # This file
│
├── docker-compose-finetune.yml          # Fine-tuning container config
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
3. **Ensure gradient checkpointing is enabled**: `use_gradient_checkpointing="unsloth"`
4. **Stop other processes**: `./start_docker.sh stop` before training

### Slow Training

If training is slower than expected:

1. **Verify Docker container**: Check that you're running inside the Unsloth container
2. **Check GPU utilization**: `nvidia-smi` should show ~95% utilization
3. **Ensure Unsloth optimizations**: Use `FastLanguageModel` not `AutoModelForCausalLM`

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

## Results Summary

### What Worked Well

1. **Sci/Tech Classification Fixed**: The biggest weakness (46.37% F1) became the strongest category (90.04% F1)
2. **Overall Accuracy Improved**: 78.63% → 88.33% (+9.70pp), exceeding the 85-92% target
3. **Balanced Performance**: All categories now between 86-90% F1 (previously 46-97% range)
4. **Training Efficiency**: 5-6x speedup with Docker + Unsloth optimizations

### Trade-offs

- **Sports F1 decreased**: 96.72% → 89.91% (-6.81pp). The base model was over-confident on Sports while failing on Sci/Tech. The fine-tuned model is more balanced.

### Next Steps

1. ✅ **Completed**: Full fine-tuning with 88.33% accuracy
2. **Ready**: Run LoRA/QLoRA on same dataset to compare accuracy vs training time
3. **Deploy**: Serve the fine-tuned model with vLLM for production use
4. **Iterate**: Consider 2 epochs to potentially recover some Sports performance

---

## References

- [Qwen2.5 Model Card](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct)
- [AG News Dataset](https://huggingface.co/datasets/ag_news)
- [Unsloth Documentation](https://docs.unsloth.ai/)
- [Unsloth DGX Spark Guide](https://docs.unsloth.ai/basics/fine-tuning-llms-with-nvidia-dgx-spark-and-unsloth)
- [TRL Documentation](https://huggingface.co/docs/trl)
- [NVIDIA PyTorch Container](https://catalog.ngc.nvidia.com/orgs/nvidia/containers/pytorch)
