# Fine-Tuning Study Plan for DGX Spark

A comprehensive plan to explore all major fine-tuning types using **Qwen2.5-7B (base)** on DGX Spark (128GB unified memory), with training times calibrated from measured hardware throughput.

---

## Critical: Base Model vs Instruct Model

### Rule: Always Fine-Tune the Base Model

All SFT experiments in this plan use **`Qwen/Qwen2.5-7B`** (the pre-trained base model), **NOT** `Qwen/Qwen2.5-7B-Instruct`.

| Aspect | Base Model (`Qwen2.5-7B`) | Instruct Model (`Qwen2.5-7B-Instruct`) |
|--------|---------------------------|----------------------------------------|
| **Pre-training** | Trained on raw text corpus | Base + SFT + RLHF/DPO |
| **Use for SFT** | **Correct** -- clean learning signal | **Wrong** -- conflicts with existing alignment |
| **Use for DPO** | No (needs SFT first) | No (use your own SFT'd model) |
| **Unsloth name** | `unsloth/Qwen2.5-7B` | `unsloth/Qwen2.5-7B-Instruct` |

### Why Not the Instruct Model?

The standard LLM training pipeline is:

```
Pre-trained Base Model  →  SFT  →  RLHF/DPO  →  Instruct Model
```

When you SFT an Instruct model, you are **double fine-tuning** -- your training data conflicts with the existing SFT+RLHF alignment baked into the model. Research shows this causes:

1. **Catastrophic forgetting** -- the model loses its alignment and safety training
2. **Conflicting training signals** -- your SFT data fights against the instruct tuning
3. **Worse learning** -- instruct models are less effective learners than base models (Shadow-FT, 2025)

**BAAI confirmed this practice**: All Infinity-Instruct models were fine-tuned from base models (Qwen2-7B, Mistral-7B-v0.1, Llama-3.1-8B), never from their Instruct variants.

### Exception: LoRA on Narrow Tasks

For **LoRA/QLoRA on very specific, narrow tasks** (e.g., AG News 4-class classification), using the Instruct model is tolerable because:
- LoRA only modifies ~0.5% of parameters, minimizing forgetting
- The existing instruction-following ability helps with task formatting
- The task is narrow enough that conflicting signals are minimal

However, for all **general capability training** (instruction following, code, math, conversational, etc.), always use the base model.

### Lesson Learned from AG News

The AG News experiments (Phase 1) used `unsloth/Qwen2.5-7B-Instruct` -- this worked acceptably for that narrow classification task with LoRA/QLoRA, but was technically suboptimal for the Full FT run. **All future experiments in this plan use the base model.**

### Throughput Note

The base model (`Qwen2.5-7B`) has the identical architecture and parameter count as the Instruct variant. Training throughput is effectively the same. The measurements from the AG News experiment remain valid for time estimation.

---

## Hardware Capability (Measured)

### DGX Spark Specifications

| Aspect | Spec |
|--------|------|
| **Processor** | NVIDIA GB10 Grace Blackwell Superchip |
| **GPU** | Blackwell architecture, 6,144 CUDA cores, sm_121 |
| **Memory** | 128 GB unified LPDDR5x (GPU reports 119.7 GB usable) |
| **Memory Bandwidth** | 273 GB/s |
| **Peak FP4 (sparse)** | 1 PFLOP |
| **Estimated BF16 Tensor Core** | ~125 TFLOPS peak |

### Measured Training Throughput (AG News, 120K samples, 1 epoch)

*Note: Measured using Qwen2.5-7B-Instruct (AG News experiment). Throughput is identical for the base model since architecture and parameter count are the same.*

| Method | Speed (it/s) | Batch Size | Seq Len | Token Throughput | Memory Used |
|--------|-------------|------------|---------|------------------|-------------|
| **Full FT** | 0.24 | 8 x 2 = 16 | 512 | **~2,000 tok/s** | ~70 GB |
| **LoRA** | 0.36 | 8 x 2 = 16 | 512 | **~3,000 tok/s** | ~20-25 GB |
| **QLoRA** | 0.35 | 8 x 2 = 16 | 512 | **~2,900 tok/s** | ~8-12 GB |

This implies ~72% Model FLOP Utilization (MFU) for Full FT with Unsloth optimizations -- excellent for a single-chip system.

### Throughput Scaling by Sequence Length

Longer sequences reduce per-token throughput due to quadratic attention (mitigated but not eliminated by Flash Attention 2). For Full FT at longer sequences, batch size must also decrease to fit in memory.

| Method | seq 512 | seq 1024 | seq 2048 | seq 4096 |
|--------|---------|----------|----------|----------|
| **LoRA** | 3,000 | ~2,600 | ~2,200 | ~1,650 |
| **Full FT** | 2,000 | ~1,750 | ~1,400 | ~1,000 |

Notes:
- Full FT at seq_len=2048: batch_size drops to 2 (same activation memory as batch=8 @ seq=512)
- Full FT at seq_len=4096: batch_size=1, may need `gradient_checkpointing=True` (adds ~40% overhead)
- LoRA uses ~20-25 GB, so longer sequences remain comfortable with batch=4-8

### Time Estimation Formula

```
Training Hours = (num_samples x avg_tokens_per_sample x num_epochs) / throughput_tok_per_sec / 3600
```

### Key Insight from AG News: LoRA vs Full FT

| Metric | Full FT | LoRA | Winner |
|--------|---------|------|--------|
| Accuracy | 95.18% | 95.45% | **LoRA** |
| Training time | 8h 36m | 5h 51m | **LoRA** (32% faster) |
| Output size | 15.25 GB | 177 MB | **LoRA** (85x smaller) |
| Inference speed | 49.6/s | 41.3/s | Full FT (20% faster) |

**Takeaway**: LoRA is the default recommended method. Full FT is worth considering for tasks where every fraction of a percent matters (code, math) or when standalone deployment (no adapter loading) is required.

---

## Training Time Budget Framework

All experiments are designed to fit within these practical time windows:

| Category | Wall-Clock Time | When to Use |
|----------|----------------|-------------|
| **Quick** | 4-12 hours | Small datasets (<100K), rapid iteration |
| **Medium** | 12-36 hours | Core experiments, most recommended configs |
| **Long** | 36-72 hours | Multi-epoch on larger datasets, maximum quality |
| **Extended** | 72-120 hours | Only if results justify it; preferably LoRA |
| **Not recommended** | >120 hours | Diminishing returns; use cloud GPU instead |

---

## 1. Instruction-Following Fine-Tuning

### Recommended Dataset: **OpenOrca subset** (500K) or **FLAN subset** (500K)

| Aspect | Details |
|--------|---------|
| **Dataset** | `Open-Orca/OpenOrca` (sample 500K) or `Muennighoff/flan` (sample 500K) |
| **Size** | 500K instruction pairs (down from 1.8-4M -- see note) |
| **Avg Tokens** | ~300 per sample |
| **Max Seq Length** | 1024 |
| **Format** | Instruction -> Response |

#### Why 500K, Not 1.8M+?

With the full FLAN (1.8M) at 3 epochs, LoRA would take ~58 hours and Full FT ~86 hours. At 500K, diminishing returns set in -- BAAI's own research shows that carefully selected subsets achieve 95%+ of full dataset performance (their 7M Core uses only 1.4M of 7M samples).

#### Training Time Estimates

| Method | 1 Epoch | 2 Epochs | 3 Epochs | Recommended |
|--------|---------|----------|----------|-------------|
| **LoRA** | ~16h | ~32h | ~48h | 1-2 epochs |
| **Full FT** | ~24h | ~48h | ~71h | 1 epoch |

*Calculation: 500K x 300 tokens = 150M tokens/epoch. LoRA @ 2,600 tok/s; Full FT @ 1,750 tok/s.*

#### Method Recommendation: **LoRA** (1-2 epochs, 16-32 hours)

Full FT at 1 epoch (24h) is also practical if you want a standalone model.

### After Fine-Tuning: What You Get

| Capability | Before | After |
|------------|--------|-------|
| **Task Diversity** | Good at chat | Excellent at 1000+ task types |
| **Zero-shot** | Moderate | Strong generalization to new tasks |
| **Instruction Following** | Sometimes ignores details | Precise instruction adherence |

**Resulting Model:** A general-purpose assistant that excels at following complex, multi-step instructions across diverse domains (translation, summarization, QA, brainstorming, etc.)

**Use Cases:**
- General-purpose AI assistant
- Task automation
- Multi-domain chatbot

---

## 2. Conversational / Chat Fine-Tuning

### Recommended Dataset: **UltraChat** (200K subset)

| Aspect | Details |
|--------|---------|
| **Dataset** | `stingning/ultrachat` (sample 200K from 1.5M) |
| **Size** | 200K multi-turn conversations |
| **Avg Tokens** | ~800 per conversation (multi-turn) |
| **Max Seq Length** | 2048 |
| **Format** | System + User + Assistant turns |

#### Why 200K, Not 1.5M?

Full UltraChat (1.5M x 800 tokens x 2 epochs) would take ~152 hours with LoRA -- over 6 days. The 200K subset covers sufficient conversational diversity while keeping training practical.

**Alternative:** ShareGPT + WildChat combo (~100K, ~15h LoRA)

#### Training Time Estimates

| Method | 1 Epoch | 2 Epochs | Recommended |
|--------|---------|----------|-------------|
| **LoRA** | ~20h | ~40h | 1 epoch |
| **Full FT** | ~30h | ~60h | 1 epoch |

*Calculation: 200K x 800 tokens = 160M tokens/epoch. LoRA @ 2,200 tok/s; Full FT @ 1,400 tok/s (seq 2048).*

#### Method Recommendation: **LoRA** (1 epoch, ~20 hours)

Conversations are long sequences (2048), so Full FT's memory overhead grows. LoRA handles long sequences comfortably with batch=4-8.

### After Fine-Tuning: What You Get

| Capability | Before | After |
|------------|--------|-------|
| **Context Tracking** | Loses track after 3-4 turns | Maintains coherence 10+ turns |
| **Persona Consistency** | Drifts | Stays in character |
| **Engagement** | Generic responses | Natural, engaging dialogue |
| **Clarification** | Assumes | Asks follow-up questions |

**Resulting Model:** A conversational AI that feels natural, remembers context, and engages in meaningful multi-turn dialogue.

**Use Cases:**
- Customer service chatbot
- Virtual companion
- Interview practice bot
- Roleplay / character AI

---

## 3. Code Generation Fine-Tuning

### Recommended Dataset: **Magicoder-OSS-Instruct** (186K) + **CodeFeedback** (60K)

| Aspect | Details |
|--------|---------|
| **Dataset** | `ise-uiuc/Magicoder-OSS-Instruct-75K` + `m-a-p/CodeFeedback-Filtered-Instruction` |
| **Size** | ~250K code instruction samples |
| **Avg Tokens** | ~600 per sample (code is verbose) |
| **Max Seq Length** | 2048 |
| **Languages** | Python, JavaScript, TypeScript, Java, C++, etc. |

#### Training Time Estimates

| Method | 1 Epoch | 2 Epochs | 3 Epochs | Recommended |
|--------|---------|----------|----------|-------------|
| **LoRA** | ~19h | ~38h | ~57h | 2 epochs |
| **Full FT** | ~30h | ~60h | ~89h | 1 epoch |

*Calculation: 250K x 600 tokens = 150M tokens/epoch. LoRA @ 2,200 tok/s; Full FT @ 1,400 tok/s (seq 2048).*

#### Method Recommendation: **LoRA** (2 epochs, ~38 hours) or **Full FT** (1 epoch, ~30 hours)

Code generation benefits from more training epochs since precise syntax matters. Full FT may have a slight edge on code accuracy due to updating all parameters, but LoRA at 2 epochs is a strong choice.

### After Fine-Tuning: What You Get

| Capability | Before | After |
|------------|--------|-------|
| **Code Generation** | Basic | Production-quality code |
| **Bug Fixing** | Often wrong | Accurate diagnosis & fix |
| **Code Explanation** | Surface level | Deep understanding |
| **Multi-language** | Python-focused | Strong across 10+ languages |
| **Best Practices** | Inconsistent | Follows conventions |

**Resulting Model:** A coding assistant comparable to GitHub Copilot that generates, explains, debugs, and refactors code.

**Use Cases:**
- IDE coding assistant
- Code review automation
- Documentation generation
- Test generation

---

## 4. Mathematical Reasoning Fine-Tuning

### Recommended Dataset: **MetaMathQA** (395K)

| Aspect | Details |
|--------|---------|
| **Dataset** | `meta-math/MetaMathQA` |
| **Size** | 395K problems with step-by-step solutions |
| **Avg Tokens** | ~400 per sample (problem + chain-of-thought + answer) |
| **Max Seq Length** | 1024 |
| **Format** | Problem -> Chain-of-thought -> Answer |

#### Supplementary: **GSM8K** (8.5K) + **MATH** (12.5K) for evaluation holdouts

#### Training Time Estimates

| Method | 1 Epoch | 2 Epochs | 3 Epochs | Recommended |
|--------|---------|----------|----------|-------------|
| **LoRA** | ~17h | ~34h | ~51h | 2 epochs |
| **Full FT** | ~25h | ~50h | ~76h | 1-2 epochs |

*Calculation: 395K x 400 tokens = 158M tokens/epoch. LoRA @ 2,600 tok/s; Full FT @ 1,750 tok/s.*

#### Method Recommendation: **LoRA** (2 epochs, ~34 hours) or **Full FT** (1 epoch, ~25 hours)

Math reasoning requires precise step-by-step logic. Full FT's lower training loss may translate to fewer arithmetic errors, making it a viable choice here despite the time premium. The dataset (395K at seq 1024) fits comfortably in Full FT memory.

### After Fine-Tuning: What You Get

| Capability | Before | After |
|------------|--------|-------|
| **Arithmetic** | Makes errors | 95%+ accuracy |
| **Word Problems** | Confused | Step-by-step breakdown |
| **Algebra** | Basic | Handles complex equations |
| **Reasoning Chain** | Skips steps | Shows all work |
| **Self-verification** | None | Checks own answers |

**Resulting Model:** A math tutor that solves problems step-by-step, explains reasoning, and catches its own mistakes.

**Use Cases:**
- Math tutoring
- Homework help
- Scientific computing assistant
- Financial calculations

---

## 5. Medical/Healthcare Fine-Tuning

### Recommended Dataset: **MedInstruct** (52K) + **PubMedQA** (211K) + **Medical Meadow** (160K)

| Aspect | Details |
|--------|---------|
| **Dataset** | Combined medical corpus |
| **Size** | ~400K medical examples |
| **Avg Tokens** | ~400 per sample |
| **Max Seq Length** | 1024 |
| **Format** | Clinical questions, diagnosis, treatment |
| **Caution** | Not for actual medical advice |

#### Training Time Estimates

| Method | 1 Epoch | 2 Epochs | 3 Epochs | Recommended |
|--------|---------|----------|----------|-------------|
| **LoRA** | ~17h | ~34h | ~51h | 1-2 epochs |
| **Full FT** | ~25h | ~51h | ~76h | 1 epoch |

*Calculation: 400K x 400 tokens = 160M tokens/epoch. LoRA @ 2,600 tok/s; Full FT @ 1,750 tok/s.*

#### Method Recommendation: **LoRA** (1-2 epochs, 17-34 hours)

Medical fine-tuning is domain adaptation -- LoRA adapts vocabulary and reasoning patterns effectively. Full FT is overkill here unless you want a standalone medical model.

### After Fine-Tuning: What You Get

| Capability | Before | After |
|------------|--------|-------|
| **Medical Terminology** | Basic | Fluent |
| **Symptom Analysis** | Vague | Systematic differential |
| **Drug Interactions** | Limited | Comprehensive |
| **Clinical Reasoning** | Generic | Evidence-based |
| **Literature Synthesis** | Weak | Summarizes research |

**Resulting Model:** A medical knowledge assistant for healthcare professionals (NOT for diagnosis).

**Use Cases:**
- Medical education
- Literature review assistant
- Clinical documentation help
- Drug information lookup
- **NOT** patient diagnosis

---

## 6. Legal Domain Fine-Tuning

### Recommended Dataset: **LegalBench** (20K) + **CaseHOLD** (53K) + Legal documents

| Aspect | Details |
|--------|---------|
| **Dataset** | `nguha/legalbench` + contract datasets |
| **Size** | ~200K legal examples |
| **Avg Tokens** | ~500 per sample (legal text is verbose) |
| **Max Seq Length** | 2048 |
| **Format** | Legal QA, contract analysis, case reasoning |

#### Training Time Estimates

| Method | 1 Epoch | 2 Epochs | 3 Epochs | Recommended |
|--------|---------|----------|----------|-------------|
| **LoRA** | ~13h | ~25h | ~38h | 2 epochs |
| **Full FT** | ~19h | ~37h | ~56h | 1 epoch |

*Calculation: 200K x 500 tokens = 100M tokens/epoch. LoRA @ 2,200 tok/s; Full FT @ 1,400 tok/s (seq 2048).*

#### Method Recommendation: **LoRA** (2 epochs, ~25 hours) or **Full FT** (1 epoch, ~19 hours)

Legal texts are long but the dataset is moderate (200K). Both methods are practical. Full FT in 1 epoch is the fastest path to a standalone legal model.

### After Fine-Tuning: What You Get

| Capability | Before | After |
|------------|--------|-------|
| **Legal Terminology** | Basic | Professional |
| **Contract Analysis** | Surface | Clause-by-clause |
| **Case Law** | Generic | Cites precedents |
| **Risk Identification** | Misses issues | Comprehensive |
| **Plain Language** | Jargon-heavy | Clear explanations |

**Resulting Model:** A legal research assistant for lawyers (NOT legal advice for public).

**Use Cases:**
- Contract review assistant
- Legal research
- Case summarization
- Compliance checking
- **NOT** legal advice

---

## 7. Preference Alignment (DPO)

### Recommended Dataset: **UltraFeedback** (64K) or **Nectar** (183K)

| Aspect | Details |
|--------|---------|
| **Dataset** | `openbmb/UltraFeedback` |
| **Size** | 64K preference pairs |
| **Avg Tokens** | ~600 per response (x2 for chosen + rejected) |
| **Max Seq Length** | 1024 |
| **Format** | Prompt + Chosen + Rejected |
| **Compute Note** | DPO processes both chosen and rejected per step (~2x SFT compute) |

#### Training Time Estimates

DPO requires forward passes through both the policy model and a frozen reference model for each (chosen, rejected) pair. This roughly doubles the compute per sample compared to standard SFT.

| Method | 1 Epoch | 2 Epochs | 3 Epochs | Recommended |
|--------|---------|----------|----------|-------------|
| **LoRA** | ~16h | ~32h | ~49h | 1-2 epochs |
| **Full FT** | Not recommended for DPO | -- | -- | Use LoRA |

*Calculation: 64K x 1,200 effective tokens x 2 (DPO overhead) = 154M equiv tokens/epoch. LoRA @ 2,600 tok/s.*

#### Method Recommendation: **LoRA only** (1-2 epochs, 16-32 hours)

DPO is almost always applied as LoRA on top of an already SFT-fine-tuned model. Full FT for DPO risks catastrophic forgetting. This is a "Stage 2" fine-tuning -- the pipeline is:

```
Qwen2.5-7B (base) → SFT (from Phase 3) → DPO (this step)
```

The SFT model from one of your earlier experiments (e.g., Instruction Following or Code) becomes the starting point. DPO then aligns the model's outputs with human preferences without undoing the SFT training.

### After Fine-Tuning: What You Get

| Capability | Before | After |
|------------|--------|-------|
| **Response Quality** | Variable | Consistently high |
| **Helpfulness** | Sometimes refuses | Helpful when safe |
| **Harmlessness** | May generate harmful | Refuses appropriately |
| **Honesty** | Can hallucinate | Admits uncertainty |
| **Tone** | Inconsistent | Professional & warm |

**Resulting Model:** An aligned assistant that provides high-quality, safe, and helpful responses.

**Use Cases:**
- Production chatbot
- Customer-facing AI
- Safe AI deployment
- Reducing harmful outputs

---

## 8. Tool Use / Function Calling

### Recommended Dataset: **xLAM Function Calling** (60K)

| Aspect | Details |
|--------|---------|
| **Dataset** | `Salesforce/xlam-function-calling-60k` |
| **Size** | 60K function calling examples |
| **Avg Tokens** | ~500 per sample |
| **Max Seq Length** | 1024 |
| **Format** | User query -> Tool selection -> Parameters -> Result |

#### Training Time Estimates

This is the fastest experiment in the plan -- the ideal "quick win" to start with.

| Method | 1 Epoch | 2 Epochs | 3 Epochs | Recommended |
|--------|---------|----------|----------|-------------|
| **LoRA** | ~3h | ~6h | ~10h | 3 epochs |
| **Full FT** | ~5h | ~10h | ~14h | 2-3 epochs |

*Calculation: 60K x 500 tokens = 30M tokens/epoch. LoRA @ 2,600 tok/s; Full FT @ 1,750 tok/s.*

#### Method Recommendation: **Full FT** (3 epochs, ~14 hours) or **LoRA** (3 epochs, ~10 hours)

With only 60K samples, Full FT is genuinely practical here and completes in under a day. This small dataset benefits from multiple epochs and Full FT's ability to update all parameters. A great candidate for comparing LoRA vs Full FT like you did with AG News.

### After Fine-Tuning: What You Get

| Capability | Before | After |
|------------|--------|-------|
| **Tool Selection** | Guesses | Precise matching |
| **Parameter Extraction** | Misses required | Complete & correct |
| **Multi-tool** | Confused | Chains tools correctly |
| **Error Handling** | Ignores | Graceful recovery |
| **JSON Formatting** | Inconsistent | Always valid |

**Resulting Model:** An AI agent that reliably calls APIs and tools to complete tasks.

**Use Cases:**
- Agentic AI systems
- Workflow automation
- API integration
- Smart home control
- Enterprise automation

---

## 9. Summarization Specialist

### Recommended Dataset: **CNN/DailyMail** (200K subset) + **XSum** (100K subset)

| Aspect | Details |
|--------|---------|
| **Dataset** | `cnn_dailymail` (200K) + `xsum` (100K) |
| **Size** | ~300K summarization pairs (down from 500K+) |
| **Avg Tokens** | ~800 per pair (long document + summary) |
| **Max Seq Length** | 2048 |
| **Format** | Long document -> Concise summary |

#### Why 300K, Not 500K+?

The full CNN/DailyMail + XSum exceeds 500K long-sequence samples. At 800 avg tokens and seq_len 2048, the compute adds up fast. 300K provides excellent coverage of summarization patterns.

#### Training Time Estimates

| Method | 1 Epoch | 2 Epochs | Recommended |
|--------|---------|----------|-------------|
| **LoRA** | ~30h | ~61h | 1 epoch |
| **Full FT** | ~48h | ~95h | 1 epoch (if time permits) |

*Calculation: 300K x 800 tokens = 240M tokens/epoch. LoRA @ 2,200 tok/s; Full FT @ 1,400 tok/s (seq 2048).*

#### Method Recommendation: **LoRA** (1 epoch, ~30 hours)

Long documents (800+ avg tokens at seq 2048) make this one of the more compute-heavy experiments. Full FT at 1 epoch takes 2 full days. LoRA is strongly preferred.

**Alternative for faster iteration:** Use only CNN/DailyMail 200K subset (LoRA ~24h, Full FT ~38h).

### After Fine-Tuning: What You Get

| Capability | Before | After |
|------------|--------|-------|
| **Compression** | Verbose | Highly concise |
| **Key Points** | Misses some | Captures all important |
| **Factuality** | May hallucinate | Faithful to source |
| **Length Control** | Ignores | Respects constraints |
| **Multi-doc** | Weak | Synthesizes multiple sources |

**Resulting Model:** A summarization engine for documents, articles, reports, and books.

**Use Cases:**
- News digest
- Meeting summarization
- Research paper summaries
- Email tl;dr
- Report generation

---

## 10. Creative Writing

### Recommended Dataset: **WritingPrompts** (150K subset) + Fiction datasets

| Aspect | Details |
|--------|---------|
| **Dataset** | `euclaise/writingprompts` (sample 150K) + story datasets |
| **Size** | ~150K creative writing samples (down from 500K) |
| **Avg Tokens** | ~800 per sample (stories are long) |
| **Max Seq Length** | 2048 |
| **Format** | Prompt -> Story/Poetry/Script |

#### Training Time Estimates

| Method | 1 Epoch | 2 Epochs | Recommended |
|--------|---------|----------|-------------|
| **LoRA** | ~15h | ~30h | 1-2 epochs |
| **Full FT** | ~24h | ~48h | 1 epoch |

*Calculation: 150K x 800 tokens = 120M tokens/epoch. LoRA @ 2,200 tok/s; Full FT @ 1,400 tok/s (seq 2048).*

#### Method Recommendation: **LoRA** (1-2 epochs, 15-30 hours)

Creative writing is subjective and doesn't benefit as much from Full FT precision. LoRA captures stylistic patterns effectively.

### After Fine-Tuning: What You Get

| Capability | Before | After |
|------------|--------|-------|
| **Storytelling** | Generic plots | Engaging narratives |
| **Character Voice** | Flat | Distinct personalities |
| **Descriptive Language** | Plain | Vivid & evocative |
| **Genre Adaptation** | Limited | Mystery, sci-fi, romance, etc. |
| **Continuation** | Loses thread | Maintains story arc |

**Resulting Model:** A creative writing assistant for authors, game designers, and content creators.

**Use Cases:**
- Story generation
- Game dialogue
- Marketing copy
- Poetry & lyrics
- Screenwriting assistance

---

## Training Time Summary (Calibrated from Measured DGX Spark Throughput)

All times calculated from AG News benchmark: Full FT ~2,000 tok/s, LoRA ~3,000 tok/s at seq 512, scaled for longer sequences.

| # | Fine-Tuning Type | Dataset Size | Avg Tok | Seq Len | LoRA (rec. epochs) | Full FT (rec. epochs) | Best Method |
|---|------------------|-------------|---------|---------|--------------------|-----------------------|-------------|
| 8 | **Tool Use** | 60K | 500 | 1024 | **~10h** (3 ep) | **~14h** (3 ep) | Either |
| 6 | **Legal** | 200K | 500 | 2048 | **~25h** (2 ep) | **~19h** (1 ep) | Either |
| 1 | **Instruction** | 500K | 300 | 1024 | **~32h** (2 ep) | **~24h** (1 ep) | LoRA |
| 4 | **Math** | 395K | 400 | 1024 | **~34h** (2 ep) | **~25h** (1 ep) | Either |
| 5 | **Medical** | 400K | 400 | 1024 | **~34h** (2 ep) | **~25h** (1 ep) | LoRA |
| 7 | **DPO Alignment** | 64K | 600x2 | 1024 | **~32h** (2 ep) | N/A | LoRA only |
| 2 | **Conversational** | 200K | 800 | 2048 | **~20h** (1 ep) | **~30h** (1 ep) | LoRA |
| 10 | **Creative Writing** | 150K | 800 | 2048 | **~30h** (2 ep) | **~24h** (1 ep) | LoRA |
| 3 | **Code** | 250K | 600 | 2048 | **~38h** (2 ep) | **~30h** (1 ep) | LoRA |
| 9 | **Summarization** | 300K | 800 | 2048 | **~30h** (1 ep) | **~48h** (1 ep) | LoRA |

### Quick Reference: Sorted by Training Time (LoRA)

| Time Bucket | Experiments |
|-------------|------------|
| **Under 12h** | Tool Use (10h) |
| **12-24h** | Conversational (20h), Legal (25h, or 13h 1-epoch) |
| **24-36h** | Instruction (32h), Math (34h), Medical (34h), Creative (30h), Summarization (30h), DPO (32h) |
| **36-48h** | Code (38h) |

### Full FT Viability Assessment

| Experiment | Full FT Feasible? | Why |
|------------|-------------------|-----|
| **Tool Use (60K)** | Excellent | Small dataset, 14h for 3 epochs |
| **Legal (200K)** | Good | 19h at 1 epoch, moderate size |
| **Instruction (500K)** | Good | 24h at 1 epoch |
| **Math (395K)** | Good | 25h at 1 epoch, precision matters |
| **Medical (400K)** | Feasible | 25h at 1 epoch |
| **Code (250K)** | Feasible | 30h at 1 epoch, seq 2048 |
| **Conversational (200K)** | Feasible | 30h at 1 epoch, seq 2048 |
| **Creative (150K)** | Feasible | 24h at 1 epoch |
| **Summarization (300K)** | Marginal | 48h at 1 epoch, long sequences |
| **DPO (64K)** | Not recommended | Catastrophic forgetting risk |

---

## Benchmarking & Evaluation

### General Approach

```
1. Evaluate BASE model on benchmark -> Record scores
2. Fine-tune on training data
3. Evaluate FINE-TUNED model on SAME benchmark -> Compare improvement
```

### Evaluation Tool Setup

```bash
# Install lm-evaluation-harness (primary tool)
pip install lm-eval

# Install bigcode-evaluation-harness (for code)
pip install bigcode-eval-harness

# Install rouge for summarization
pip install rouge-score
```

---

### Benchmarks by Fine-Tuning Type

#### 1. Instruction-Following

| Benchmark | What it Measures | Size | Expected Improvement |
|-----------|------------------|------|---------------------|
| **IFEval** | Instruction following precision | 500 | 40-50% -> 70-80% |
| **MT-Bench** | Multi-turn instruction quality | 80 | 5-6 -> 7-8 (out of 10) |
| **AlpacaEval** | Instruction response quality | 805 | Win-rate +20-30% |

```bash
# Run evaluation
lm_eval --model vllm --model_args pretrained=your_model --tasks ifeval --batch_size 8
```

---

#### 2. Conversational / Chat

| Benchmark | What it Measures | Size | Expected Improvement |
|-----------|------------------|------|---------------------|
| **MT-Bench** | Multi-turn coherence | 80 | 5-6 -> 7-8 |
| **CoQA** | Conversational QA | 8K | 60-70% -> 80-85% |

```python
# Custom evaluation metrics
- Context retention accuracy (does it remember earlier turns?)
- Persona consistency score
- Response relevance (embedding similarity)
```

---

#### 3. Code Generation

| Benchmark | What it Measures | Size | Expected Improvement |
|-----------|------------------|------|---------------------|
| **HumanEval** | Python code generation | 164 | pass@1: 30-40% -> 50-60% |
| **MBPP** | Python basics | 974 | pass@1: 40-50% -> 60-70% |
| **MultiPL-E** | Multi-language code | 1K+ | Varies by language |

```bash
# Using bigcode-evaluation-harness
accelerate launch main.py \
  --model your_model \
  --tasks humaneval \
  --allow_code_execution \
  --metric_output_path results.json
```

---

#### 4. Mathematical Reasoning

| Benchmark | What it Measures | Difficulty | Expected Improvement |
|-----------|------------------|------------|---------------------|
| **GSM8K** | Grade school math | Easy | 50-60% -> 75-85% |
| **MATH** | Competition math | Hard | 15-25% -> 35-45% |
| **MMLU-Math** | Math knowledge | Medium | +10-15% |

```bash
lm_eval --model vllm --model_args pretrained=your_model \
  --tasks gsm8k,math_algebra,math_geometry --batch_size 8
```

---

#### 5. Medical Domain

| Benchmark | What it Measures | Size | Expected Improvement |
|-----------|------------------|------|---------------------|
| **MedQA (USMLE)** | Medical licensing exam | 1.3K | 40-50% -> 60-70% |
| **PubMedQA** | Research comprehension | 1K | 55-65% -> 75-85% |
| **MedMCQA** | Medical knowledge | 4.2K | +15-20% |

```bash
lm_eval --model vllm --model_args pretrained=your_model \
  --tasks medqa,pubmedqa,medmcqa --batch_size 8
```

---

#### 6. Legal Domain

| Benchmark | What it Measures | Size | Expected Improvement |
|-----------|------------------|------|---------------------|
| **LegalBench** | Legal reasoning | 162 tasks | +15-25% average |
| **CaseHOLD** | Case holding ID | 53K | 50-60% -> 70-80% |
| **ContractNLI** | Contract understanding | 607 | +20-30% |

```bash
lm_eval --model vllm --model_args pretrained=your_model \
  --tasks legalbench --batch_size 8
```

---

#### 7. DPO Alignment

| Benchmark | What it Measures | Expected Improvement |
|-----------|------------------|---------------------|
| **TruthfulQA** | Truthfulness | 35-45% -> 55-65% |
| **ToxiGen** | Toxicity avoidance | Toxicity: 5-10% -> <1% |
| **AlpacaEval** | Overall quality | Win-rate: 10-20% -> 30-50% |
| **BBQ** | Bias detection | +10-15% |

```bash
lm_eval --model vllm --model_args pretrained=your_model \
  --tasks truthfulqa,toxigen --batch_size 8
```

---

#### 8. Tool Use / Function Calling

| Benchmark | What it Measures | Expected Improvement |
|-----------|------------------|---------------------|
| **Berkeley Function Calling** | API call accuracy | Tool selection: 60-70% -> 90-95% |
| **ToolBench** | Multi-tool planning | Parameter extraction: 50-60% -> 85-90% |
| **Nexus Function Calling** | Complex calls | JSON validity: 70-80% -> 98-99% |

```python
# Custom evaluation
def evaluate_tool_use(model, test_cases):
    metrics = {
        "tool_selection_accuracy": 0,
        "parameter_extraction_accuracy": 0,
        "json_validity": 0,
        "end_to_end_success": 0
    }
    # ... evaluate each metric
    return metrics
```

---

#### 9. Summarization

| Benchmark | What it Measures | Metric | Expected Improvement |
|-----------|------------------|--------|---------------------|
| **CNN/DailyMail** | News summarization | ROUGE-1/2/L | ROUGE-1: 35-40 -> 45-50 |
| **XSum** | Extreme summarization | ROUGE | ROUGE-L: 30-35 -> 40-45 |
| **SummEval** | Human quality | Coherence, Fluency | +1-2 points |

```python
from rouge_score import rouge_scorer

scorer = rouge_scorer.RougeScorer(['rouge1', 'rouge2', 'rougeL'])
# Compare generated summary with reference
score = scorer.score(reference_summary, generated_summary)
```

---

#### 10. Creative Writing

| Benchmark | What it Measures | Method | Expected Improvement |
|-----------|------------------|--------|---------------------|
| **WritingPrompts Eval** | Story quality | GPT-4 judge | +1-2 points (out of 5) |
| **StoryCloze** | Narrative coherence | MC accuracy | 70-75% -> 85-90% |
| **Human Eval** | Creativity rating | Crowdsource | Subjective |

```python
# GPT-4 as judge
def evaluate_creative(model, prompts):
    for prompt in prompts:
        story = model.generate(prompt)
        judgment = gpt4.evaluate(
            story, 
            criteria=["creativity", "coherence", "engagement", "grammar"]
        )
    return avg_scores
```

---

### Quick Benchmark Reference Table

| Fine-Tuning Type | Primary Benchmark | Secondary | Tool | Expected Gain |
|------------------|-------------------|-----------|------|---------------|
| Instruction | IFEval | MT-Bench | lm-eval | +30% |
| Conversational | MT-Bench | CoQA | Custom | +2 points |
| Code | HumanEval | MBPP | bigcode-eval | +20% pass@1 |
| Math | GSM8K | MATH | lm-eval | +25% |
| Medical | MedQA | PubMedQA | lm-eval | +20% |
| Legal | LegalBench | CaseHOLD | lm-eval | +20% |
| DPO | TruthfulQA | AlpacaEval | lm-eval | +20% |
| Tool Use | Berkeley FC | ToolBench | Custom | +30% |
| Summarization | ROUGE | SummEval | rouge_score | +10 ROUGE |
| Creative | GPT-4 Judge | StoryCloze | Custom | +15% |

---

### Benchmark Workflow Template

```python
# Template for each experiment
import json
from datetime import datetime

def run_experiment(experiment_name, model_path, tasks):
    results = {
        "experiment": experiment_name,
        "model": model_path,
        "timestamp": datetime.now().isoformat(),
        "base_model_scores": {},
        "finetuned_scores": {},
        "improvement": {}
    }
    
    # 1. Evaluate base model
    results["base_model_scores"] = evaluate(BASE_MODEL, tasks)
    
    # 2. Fine-tune (done separately)
    
    # 3. Evaluate fine-tuned model
    results["finetuned_scores"] = evaluate(model_path, tasks)
    
    # 4. Calculate improvement
    for task in tasks:
        base = results["base_model_scores"][task]
        ft = results["finetuned_scores"][task]
        results["improvement"][task] = {
            "absolute": ft - base,
            "relative": (ft - base) / base * 100
        }
    
    # 5. Save results
    with open(f"results/{experiment_name}.json", "w") as f:
        json.dump(results, f, indent=2)
    
    return results
```

---

## Recommended Order

### Phase 1: Foundation (Completed)

1. Classification (AG News) -- All three methods compared
   - QLoRA: 95.14% accuracy, 6h, ~10 GB memory
   - LoRA: 95.45% accuracy, 5h 51m, ~25 GB memory
   - Full FT: 95.18% accuracy, 8h 36m, ~70 GB memory
   - **Key learning**: LoRA matched Full FT; throughput calibrated
   - **Note**: AG News used the Instruct model (`Qwen2.5-7B-Instruct`) -- acceptable for narrow LoRA tasks but all future experiments use the **base model** (`Qwen2.5-7B`)

### Phase 2: Quick Wins (Start Here)

2. **Tool Use** (60K, ~10-14h) -- Fastest experiment, most practical for agentic AI
   - Ideal for comparing LoRA vs Full FT again (small dataset, both methods under 14h)
   - Directly applicable to building AI agents

### Phase 3: Core Capabilities (1-2 days each)

3. **Math Reasoning** (395K, ~25-34h) -- Measurable improvement, clear benchmarks (GSM8K, MATH)
4. **Code Generation** (250K, ~30-38h) -- High practical value, clear evaluation (HumanEval, MBPP)
5. **Instruction Following** (500K, ~24-32h) -- Broad capability improvement

### Phase 4: Alignment

6. **DPO Alignment** (64K, ~16-32h) -- Apply on top of best SFT model from Phase 3
   - Pipeline: `Qwen2.5-7B (base) → SFT (Phase 3) → DPO (this step)`
   - Prerequisite: Complete at least one SFT experiment first
   - Do NOT apply DPO directly to the base model or the official Instruct model

### Phase 5: Domain Specialization (Pick based on interest)

7. **Legal** (200K, ~19-25h) -- Moderate size, strong domain impact
8. **Medical** (400K, ~25-34h) -- Domain expertise, clear benchmarks
9. **Conversational** (200K, ~20-30h) -- Multi-turn coherence

### Phase 6: Extended Experiments (Optional)

10. **Summarization** (300K, ~30-48h) -- Long sequences, compute-heavy
11. **Creative Writing** (150K, ~15-24h) -- Fun exploration, subjective evaluation

### Total Estimated Time (All Experiments)

| Approach | Experiments | Total Time | Calendar Days |
|----------|-------------|------------|---------------|
| **LoRA only (recommended)** | All 10 | ~273 hours | ~11-12 days continuous |
| **Full FT only** | 9 (no DPO) | ~261 hours | ~11 days continuous |
| **Mix (LoRA + Full FT quick wins)** | All 10 | ~280 hours | ~12 days continuous |
| **Core only (Phase 2-3)** | 4 experiments | ~100-120 hours | ~4-5 days |

---

## Practical Tips for DGX Spark Training

### Memory Management

| Seq Length | Full FT Batch Size | LoRA Batch Size | Gradient Checkpointing |
|------------|-------------------|-----------------|----------------------|
| 512 | 8 | 8 | Not needed |
| 1024 | 4 | 8 | Not needed |
| 2048 | 2 | 4-8 | Full FT: consider enabling |
| 4096 | 1 | 2-4 | Full FT: required |

### Recommended Training Config by Experiment

```python
# IMPORTANT: Always use the base model for SFT, not the Instruct variant
MODEL_NAME = "unsloth/Qwen2.5-7B"  # Base model -- NOT "unsloth/Qwen2.5-7B-Instruct"

# Short sequences (seq_len <= 1024): Tool Use, Instruction, Math, Medical, DPO
BATCH_SIZE = 8 if lora else 4
GRADIENT_ACCUMULATION_STEPS = 2
MAX_SEQ_LENGTH = 1024
gradient_checkpointing = False

# Long sequences (seq_len = 2048): Code, Conversational, Legal, Summarization, Creative
BATCH_SIZE = 4 if lora else 2
GRADIENT_ACCUMULATION_STEPS = 4 if lora else 8
MAX_SEQ_LENGTH = 2048
gradient_checkpointing = False if lora else True  # Enable for Full FT if OOM
```

### Checkpointing Strategy

- Save every 500-1000 steps for experiments > 12 hours
- Keep `save_total_limit=2` to avoid filling disk (each Full FT checkpoint is ~15 GB)
- For multi-day runs, enable auto-resume from checkpoint

### When to Stop Early

- If validation loss plateaus for >500 steps, consider stopping
- 1 epoch is often sufficient for datasets > 200K samples
- Multiple epochs mainly help for small datasets (<100K)

---

## Quick Start Commands

```bash
# Start fine-tuning container
cd ~/Projects/xiaohui-agentic-playground/6-open-source
./start_docker.sh start finetune

# Each experiment will have its own notebook in:
# fine-tuning-dense/experiments/
#   ├── 01_tool_use/           # ~10-14h (start here)
#   ├── 02_math_reasoning/     # ~25-34h
#   ├── 03_code_generation/    # ~30-38h
#   ├── 04_instruction/        # ~24-32h
#   ├── 05_dpo_alignment/      # ~16-32h (after SFT)
#   ├── 06_legal/              # ~19-25h
#   ├── 07_medical/            # ~25-34h
#   ├── 08_conversational/     # ~20-30h
#   ├── 09_summarization/      # ~30-48h
#   └── 10_creative_writing/   # ~15-24h
```

---

## What's Next?

**Recommended next experiment:** Tool Use (60K examples, ~10-14 hours)

This is the fastest meaningful experiment and the most practical for building AI agents. It's also an excellent candidate for comparing LoRA vs Full FT again since both methods complete in under 14 hours.
