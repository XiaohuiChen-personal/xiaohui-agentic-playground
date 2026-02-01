# Single Model Speed Tests

Performance benchmarks of single models on DGX Spark with 128 GB unified memory.

## Test Results Summary

| Model | Architecture | Active Params | Avg TTFT | Avg TPS | Relative Speed |
|-------|--------------|---------------|----------|---------|----------------|
| **GPT-OSS-20B** | **MoE** | **3.6B** | **0.141s** | **15.5** | **4.0x faster** |
| Mistral-24B | Dense | 24B | 0.138s | 9.8 | 2.5x faster |
| Llama-70B | Dense | 70B | 0.540s | 3.9 | 1.0x (baseline) |

---

## GPT-OSS-20B Speed Test

📁 `speed_test_gpt.ipynb`

Performance benchmark of **openai/gpt-oss-20b** (Mixture of Experts) on DGX Spark.

### Setup

| Property | Value |
|----------|-------|
| **Model** | openai/gpt-oss-20b |
| **Architecture** | Mixture of Experts (MoE) |
| **Total Parameters** | 21B |
| **Active Parameters** | 3.6B per token |
| **Quantization** | MXFP4 (native 4-bit) |
| **Weights Size** | ~41 GB (download) / ~14 GB (loaded) |
| **Context Window** | 131,072 tokens (128K max) |

### Configuration

| Setting | Value |
|---------|-------|
| GPU Memory Utilization | 85% |
| Max Concurrent Sequences | 32 |
| Context Length | 32,768 tokens |
| CUDA Graphs | Enabled (full + piecewise) |
| Chunked Prefill | Enabled |

### Results

| Metric | Expected | Actual | Status |
|--------|----------|--------|--------|
| **Avg TPS** | 15-25 | **15.5** | ✅ Met expectation |
| **Avg TTFT** | 0.1-0.2s | **0.141s** | ✅ Met expectation |
| **vs Mistral-24B** | Faster | **+58%** | ✅ Exceeded |
| **vs Llama-70B** | 4-6x faster | **4x faster** | ✅ Met expectation |

### Per-Test Results

| Test | TTFT (s) | Total Time (s) | TPS |
|------|----------|----------------|-----|
| Short Prompt, Short Response | 0.120 | 1.36 | 5.6 |
| Short Prompt, Long Response | 0.147 | 14.13 | **27.3** |
| Long Prompt, Short Response | 0.137 | 2.78 | 3.8 |
| Code Generation | 0.160 | 10.85 | 16.5 |
| Reasoning Task | 0.141 | 10.98 | **24.2** |

### Why GPT-OSS-20B is Fast

1. **MoE Architecture** - Only 3.6B parameters active per token (vs 70B for Llama)
2. **Memory Efficient** - ~6x less memory bandwidth required than Llama-70B
3. **Optimized Kernels** - Marlin backend + FlashInfer autotuning
4. **Chain-of-Thought** - Built-in reasoning with visible thought process

### Key Findings

- **MoE delivers as promised** - 4x faster than dense 70B model
- **Best sustained generation** - 27.3 TPS on long-form output
- **Strong reasoning** - 24.2 TPS with chain-of-thought enabled
- **Trade-off** - Higher hallucination rate, verify factual claims

---

## Llama-70B Speed Test

📁 `speed_test.ipynb`

Performance benchmark of **Llama-3.3-70B-Instruct-NVFP4** with CUDA graphs optimization.

### Setup

| Property | Value |
|----------|-------|
| **Model** | Llama-3.3-70B-Instruct-NVFP4 |
| **Architecture** | Dense Transformer |
| **Parameters** | 70B |
| **Quantization** | NVFP4 (4-bit) |
| **Weights Size** | ~40 GB |

### Configuration

| Setting | Value |
|---------|-------|
| GPU Memory Utilization | 85% |
| Max Concurrent Sequences | 128 |
| Context Length | 8,192 tokens |
| CUDA Graphs | Enabled (removed `--enforce-eager`) |

### Results

| Metric | Expected | Actual | Status |
|--------|----------|--------|--------|
| **Avg TPS** | 12-15+ | **3.9** | ❌ Far below expectation |
| **Avg TTFT** | ~0.14s | **0.54s** | ❌ 4x slower |
| **vs Mistral-24B** | +20-40% | **-59.7%** | ❌ Much slower |

### Per-Test Results

| Test | TTFT (s) | Total Time (s) | TPS |
|------|----------|----------------|-----|
| Short Prompt, Short Response | 1.278 | 7.1 | 4.6 |
| Short Prompt, Long Response | 0.303 | 139.5 | 4.1 |
| Long Prompt, Short Response | 0.519 | 10.7 | 4.1 |
| Code Generation | 0.295 | 73.5 | 3.4 |
| Reasoning Task | 0.309 | 105.1 | 3.5 |

### Why Expectations Were Not Met

1. **Model Size Dominates** - 70B model requires 2.7x more memory reads than 24B
2. **Memory Bandwidth Bottleneck** - DGX Spark unified memory (~0.5-1 TB/s) limits throughput
3. **CUDA Graphs Marginal** - Minimal benefit when workload is memory-bound
4. **3.9 TPS is realistic** - Near hardware limit for 70B on this platform

---

## Recommendations

| Use Case | Recommended Model | TPS | Notes |
|----------|-------------------|-----|-------|
| **Speed + Reasoning** | GPT-OSS-20B | 15.5 | Best balance, MoE efficiency |
| **Fast General Tasks** | Mistral-24B | 9.8 | Reliable, no hallucination issues |
| **Maximum Quality** | Llama-70B | 3.9 | Accept slower speed |
| **Complex Reasoning** | GPT-OSS-20B | 15.5 | Chain-of-thought built-in |
| **Factual Accuracy** | Llama-70B or Mistral-24B | - | GPT-OSS has higher hallucination |

## Running the Tests

### GPT-OSS-20B

```bash
cd 6-open-source
./start_docker.sh start gpt-oss
jupyter notebook single_model_speed_test/speed_test_gpt.ipynb
```

### Llama-70B

```bash
cd 6-open-source
./start_docker.sh start single
jupyter notebook single_model_speed_test/speed_test.ipynb
```

## Files

- `speed_test.ipynb` - Llama-70B benchmark notebook
- `speed_test_gpt.ipynb` - GPT-OSS-20B benchmark notebook
- `speed_test_results.png` - Llama-70B visualization
- `speed_test_gpt_results.png` - GPT-OSS-20B visualization
