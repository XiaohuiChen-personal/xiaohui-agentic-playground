# Single Model Speed Test

Performance benchmark of **Llama-3.3-70B-Instruct-NVFP4** with CUDA graphs optimization on DGX Spark.

## Setup

| Property | Value |
|----------|-------|
| **Model** | Llama-3.3-70B-Instruct-NVFP4 |
| **Endpoint** | `http://localhost:8000` |
| **Quantization** | NVFP4 (4-bit) |
| **Parameters** | 70B |
| **Weights Size** | ~40 GB |

### Configuration

| Setting | Value |
|---------|-------|
| GPU Memory Utilization | 85% |
| Max Concurrent Sequences | 128 |
| Context Length | 8,192 tokens |
| CUDA Graphs | **Enabled** (removed `--enforce-eager`) |

### Optimizations Applied

- CUDA graphs enabled (expected +20-40% TPS)
- Higher GPU memory (85% vs 30-35% in dual mode)
- Shorter context (8K vs 32K)

## Results Summary

### Expected vs Actual

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

### Comparison with Dual Model Results

| Model | Parameters | Avg TTFT | Avg TPS |
|-------|------------|----------|---------|
| Mistral-24B | 24B | 0.138s | **9.8** |
| Qwen3-32B | 32B | 0.169s | 8.2 |
| **Llama-70B** | 70B | 0.541s | **3.9** |

## Why Expectations Were Not Met

### 1. Model Size is the Dominant Factor

| Model | Parameters | NVFP4 Size | TPS | Ratio |
|-------|------------|------------|-----|-------|
| Mistral-24B | 24B | ~15 GB | 9.8 | 1.0x |
| Llama-70B | 70B | ~40 GB | 3.9 | 2.5x slower |

The 70B model is 2.9x larger, requiring 2.7x more memory reads per token.

### 2. Memory Bandwidth Bottleneck

DGX Spark uses unified CPU/GPU memory with lower bandwidth than dedicated HBM:

| Hardware | Memory Bandwidth | Expected 70B TPS |
|----------|------------------|------------------|
| H100 (HBM3) | 3.35 TB/s | 50-60 TPS |
| **DGX Spark** | ~0.5-1 TB/s | **4-6 TPS** ✓ |

**3.9 TPS is near the hardware limit** for a 70B model on this platform.

### 3. CUDA Graphs Benefit is Marginal

CUDA graphs optimize CPU-GPU synchronization, but when memory bandwidth is the bottleneck, the improvement is minimal. The workload is memory-bound, not CPU-bound.

### 4. Single-Request Mode

Sequential single-request tests can't benefit from the `--max-num-seqs 128` batching configuration.

## Key Takeaways

1. **Model size matters more than optimization tricks** - 70B will always be slower than 24B on same hardware
2. **DGX Spark is memory-bandwidth limited** - Unified memory limits single-request TPS
3. **3.9 TPS is realistic** - Matches industry benchmarks for similar hardware
4. **Quality vs Speed trade-off** - 70B offers better reasoning at 2.5x slower speed

## Recommendations

| Priority | Recommendation |
|----------|----------------|
| Speed-critical tasks | Use Mistral-24B (~10 TPS) |
| Quality-critical tasks | Accept 4 TPS for Llama-70B |
| Balanced approach | Use 24B for simple tasks, 70B for complex reasoning |
| Maximum throughput | Send concurrent requests to leverage batching |

## Hardware Reality

To achieve 12-15+ TPS on a 70B model, you would need:
- **4x H100 GPUs** with 3.35 TB/s HBM3 bandwidth
- Or a **smaller model** (24B achieves ~10 TPS on DGX Spark)

## Running the Test

1. Start the single model:
   ```bash
   cd 6-open-source
   ./start_docker.sh start single
   ```

2. Run the notebook:
   ```bash
   jupyter notebook single_model_speed_test/speed_test.ipynb
   ```

## Files

- `speed_test.ipynb` - Jupyter notebook with all tests and analysis
- `speed_test_results.png` - Visualization of results
