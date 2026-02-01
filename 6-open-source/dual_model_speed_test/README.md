# Dual Model Speed Test

Performance comparison between **Mistral-Small-24B** and **Qwen3-32B** running on DGX Spark with 128 GB unified memory.

## Setup

| Model | Endpoint | Quantization | Weights | GPU Allocation |
|-------|----------|--------------|---------|----------------|
| Mistral-Small-24B | `localhost:8000` | NVFP4 | ~15 GB | 30% (~38 GB) |
| Qwen3-32B | `localhost:8001` | NVFP4 | ~20 GB | 35% (~45 GB) |

**Configuration:**
- Context Length: 32,768 tokens
- Concurrent Requests: 1 per model
- Runtime: NVIDIA vLLM container (`nvcr.io/nvidia/vllm:25.12-py3`)

## Metrics Captured

| Metric | Description |
|--------|-------------|
| **TTFT** | Time to First Token - latency before first token appears |
| **TPS** | Tokens Per Second - generation throughput |
| **Total Time** | End-to-end response time |

## Test Scenarios

1. **Short Prompt, Short Response** - Baseline latency (simple factual question)
2. **Short Prompt, Long Response** - Sustained throughput (detailed explanation)
3. **Long Prompt, Short Response** - Prefill speed (~2000 token context)
4. **Code Generation** - Programming task (Python function implementation)
5. **Reasoning Task** - Multi-step math word problem

## Results Summary

### Overall Averages

| Metric | Mistral-24B | Qwen3-32B | Difference |
|--------|-------------|-----------|------------|
| **Avg TTFT** | 0.138s | 0.169s | Mistral 18% faster |
| **Avg Total Time** | 23.3s | 39.4s | Mistral 41% faster |
| **Avg TPS** | 9.8 | 8.2 | Mistral 20% faster |

### Per-Test Results

| Test | Model | TTFT (s) | Total Time (s) | TPS |
|------|-------|----------|----------------|-----|
| Short Prompt, Short Response | Mistral-24B | 0.182 | 0.78 | 11.7 |
| | Qwen3-32B | 0.136 | 10.70 | 9.9 |
| Short Prompt, Long Response | Mistral-24B | 0.105 | 47.70 | 11.2 |
| | Qwen3-32B | 0.151 | 67.65 | 8.1 |
| Long Prompt, Short Response | Mistral-24B | 0.181 | 1.39 | 8.3 |
| | Qwen3-32B | 0.262 | 14.00 | 7.4 |
| Code Generation | Mistral-24B | 0.116 | 30.08 | 9.0 |
| | Qwen3-32B | 0.143 | 53.08 | 8.0 |
| Reasoning Task | Mistral-24B | 0.104 | 36.38 | 9.0 |
| | Qwen3-32B | 0.151 | 51.71 | 7.5 |

## Key Findings

### 1. Mistral-24B is Significantly Faster

Mistral outperforms Qwen3 across all speed metrics:
- ~18% faster time to first token
- ~41% faster total response time
- ~20% higher tokens per second

### 2. Qwen3-32B Uses Chain-of-Thought by Default

Qwen3 includes `<think>` tags with detailed reasoning in its responses. This means:
- **5-10x more tokens** generated for simple questions
- Longer total times reflect more reasoning work, not just slower generation
- Example: Simple factual question → Mistral: 7 tokens, Qwen3: 105 tokens

### 3. TTFT is Comparable

Both models achieve sub-200ms TTFT on average, making them suitable for interactive applications.

### 4. Raw Generation Speed is Similar

When accounting for output length, both operate in the 8-12 TPS range. Mistral maintains a ~20% advantage.

## Recommendations

| Use Case | Recommended Model | Reason |
|----------|-------------------|--------|
| Quick responses / General tasks | Mistral-24B | Faster, more concise |
| Complex reasoning / Math | Qwen3-32B | Built-in chain-of-thought |
| Code generation | Either | Both produce quality code |
| Latency-sensitive agents | Mistral-24B | Lower TTFT and total time |
| Accuracy-critical tasks | Qwen3-32B | Explicit reasoning may reduce errors |

## Running the Tests

1. Start the dual model setup:
   ```bash
   cd 6-open-source
   ./start_docker.sh start dual
   ```

2. Run the notebook:
   ```bash
   jupyter notebook speed_test.ipynb
   ```

## Files

- `speed_test.ipynb` - Jupyter notebook with all tests and visualizations
- `speed_test_results.png` - Bar chart comparison of metrics
