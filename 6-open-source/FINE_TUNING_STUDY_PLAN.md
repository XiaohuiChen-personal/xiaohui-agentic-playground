# Fine-Tuning Study Plan for DGX Spark

A comprehensive plan to explore all major fine-tuning types using Qwen2.5-7B on DGX Spark (128GB unified memory).

## Hardware Capability

| Aspect | DGX Spark Spec |
|--------|---------------|
| Memory | 128 GB unified |
| Full Fine-Tuning | ✅ Qwen 7B fits comfortably |
| LoRA/QLoRA | ✅ Can handle larger batch sizes |
| Dataset Size | Can load 1M+ examples in memory |

---

## 1. Instruction-Following Fine-Tuning

### Recommended Dataset: **FLAN Collection** (1.8M examples)

| Aspect | Details |
|--------|---------|
| **Dataset** | `Muennighoff/flan` or `Open-Orca/OpenOrca` (4M) |
| **Size** | 1.8M - 4M instruction pairs |
| **Format** | Instruction → Response |
| **Training Time** | ~24-48 hours (LoRA), ~72+ hours (Full) |

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

### Recommended Dataset: **UltraChat** (1.5M conversations)

| Aspect | Details |
|--------|---------|
| **Dataset** | `stingning/ultrachat` |
| **Size** | 1.5M multi-turn conversations |
| **Format** | System + User + Assistant turns |
| **Training Time** | ~30-40 hours (LoRA) |

### Alternative: **ShareGPT + WildChat Combo** (~1.1M)

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

### Recommended Dataset: **The Stack Dedup** (subset) or **Magicoder-OSS-Instruct** (186K)

| Aspect | Details |
|--------|---------|
| **Dataset** | `bigcode/starcoderdata` (subset) or `ise-uiuc/Magicoder-OSS-Instruct-75K` |
| **Size** | 500K - 1M code samples |
| **Format** | Instruction + Code or Code completion |
| **Languages** | Python, JavaScript, TypeScript, Java, C++, etc. |
| **Training Time** | ~20-30 hours (LoRA) |

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

### Recommended Dataset: **MetaMathQA** (395K) + **MATH** (12.5K) + **GSM8K** (8.5K)

| Aspect | Details |
|--------|---------|
| **Dataset** | `meta-math/MetaMathQA` |
| **Size** | 395K problems with step-by-step solutions |
| **Format** | Problem → Chain-of-thought → Answer |
| **Training Time** | ~15-20 hours (LoRA) |

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
| **Format** | Clinical questions, diagnosis, treatment |
| **Training Time** | ~15-20 hours (LoRA) |
| **Caution** | ⚠️ Not for actual medical advice |

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
| **Format** | Legal QA, contract analysis, case reasoning |
| **Training Time** | ~10-15 hours (LoRA) |

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
| **Format** | Prompt + Chosen + Rejected |
| **Training Time** | ~8-12 hours (LoRA with DPO) |

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

### Recommended Dataset: **ToolBench** (16K) + **Gorilla API** (11K) + **APIGen**

| Aspect | Details |
|--------|---------|
| **Dataset** | `Salesforce/xlam-function-calling-60k` |
| **Size** | 60K function calling examples |
| **Format** | User query → Tool selection → Parameters → Result |
| **Training Time** | ~8-10 hours (LoRA) |

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

### Recommended Dataset: **CNN/DailyMail** (300K) + **XSum** (227K) + **BookSum**

| Aspect | Details |
|--------|---------|
| **Dataset** | `cnn_dailymail` + `xsum` |
| **Size** | ~500K summarization pairs |
| **Format** | Long document → Concise summary |
| **Training Time** | ~20-25 hours (LoRA) |

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

### Recommended Dataset: **WritingPrompts** (300K) + Fiction datasets

| Aspect | Details |
|--------|---------|
| **Dataset** | `euclaise/writingprompts` + story datasets |
| **Size** | ~500K creative writing samples |
| **Format** | Prompt → Story/Poetry/Script |
| **Training Time** | ~20-25 hours (LoRA) |

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

## Training Time Estimates (Qwen 7B on DGX Spark)

| Fine-Tuning Type | Dataset Size | LoRA Time | Full FT Time |
|------------------|--------------|-----------|--------------|
| Instruction (FLAN) | 1.8M | ~40h | ~100h+ |
| Conversational | 1.5M | ~35h | ~90h |
| Code | 500K | ~25h | ~60h |
| Math Reasoning | 400K | ~20h | ~50h |
| Medical | 400K | ~20h | ~50h |
| Legal | 200K | ~12h | ~30h |
| DPO Alignment | 64K | ~10h | N/A |
| Tool Use | 60K | ~8h | ~20h |
| Summarization | 500K | ~25h | ~60h |
| Creative Writing | 500K | ~25h | ~60h |

---

## Benchmarking & Evaluation

### General Approach

```
1. Evaluate BASE model on benchmark → Record scores
2. Fine-tune on training data
3. Evaluate FINE-TUNED model on SAME benchmark → Compare improvement
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
| **IFEval** | Instruction following precision | 500 | 40-50% → 70-80% |
| **MT-Bench** | Multi-turn instruction quality | 80 | 5-6 → 7-8 (out of 10) |
| **AlpacaEval** | Instruction response quality | 805 | Win-rate +20-30% |

```bash
# Run evaluation
lm_eval --model vllm --model_args pretrained=your_model --tasks ifeval --batch_size 8
```

---

#### 2. Conversational / Chat

| Benchmark | What it Measures | Size | Expected Improvement |
|-----------|------------------|------|---------------------|
| **MT-Bench** | Multi-turn coherence | 80 | 5-6 → 7-8 |
| **CoQA** | Conversational QA | 8K | 60-70% → 80-85% |

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
| **HumanEval** | Python code generation | 164 | pass@1: 30-40% → 50-60% |
| **MBPP** | Python basics | 974 | pass@1: 40-50% → 60-70% |
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
| **GSM8K** | Grade school math | Easy | 50-60% → 75-85% |
| **MATH** | Competition math | Hard | 15-25% → 35-45% |
| **MMLU-Math** | Math knowledge | Medium | +10-15% |

```bash
lm_eval --model vllm --model_args pretrained=your_model \
  --tasks gsm8k,math_algebra,math_geometry --batch_size 8
```

---

#### 5. Medical Domain

| Benchmark | What it Measures | Size | Expected Improvement |
|-----------|------------------|------|---------------------|
| **MedQA (USMLE)** | Medical licensing exam | 1.3K | 40-50% → 60-70% |
| **PubMedQA** | Research comprehension | 1K | 55-65% → 75-85% |
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
| **CaseHOLD** | Case holding ID | 53K | 50-60% → 70-80% |
| **ContractNLI** | Contract understanding | 607 | +20-30% |

```bash
lm_eval --model vllm --model_args pretrained=your_model \
  --tasks legalbench --batch_size 8
```

---

#### 7. DPO Alignment

| Benchmark | What it Measures | Expected Improvement |
|-----------|------------------|---------------------|
| **TruthfulQA** | Truthfulness | 35-45% → 55-65% |
| **ToxiGen** | Toxicity avoidance | Toxicity: 5-10% → <1% |
| **AlpacaEval** | Overall quality | Win-rate: 10-20% → 30-50% |
| **BBQ** | Bias detection | +10-15% |

```bash
lm_eval --model vllm --model_args pretrained=your_model \
  --tasks truthfulqa,toxigen --batch_size 8
```

---

#### 8. Tool Use / Function Calling

| Benchmark | What it Measures | Expected Improvement |
|-----------|------------------|---------------------|
| **Berkeley Function Calling** | API call accuracy | Tool selection: 60-70% → 90-95% |
| **ToolBench** | Multi-tool planning | Parameter extraction: 50-60% → 85-90% |
| **Nexus Function Calling** | Complex calls | JSON validity: 70-80% → 98-99% |

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
| **CNN/DailyMail** | News summarization | ROUGE-1/2/L | ROUGE-1: 35-40 → 45-50 |
| **XSum** | Extreme summarization | ROUGE | ROUGE-L: 30-35 → 40-45 |
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
| **StoryCloze** | Narrative coherence | MC accuracy | 70-75% → 85-90% |
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

### Phase 1: Foundation (What you're doing now)
1. ✅ Classification (AG News) - Done with QLoRA (95.14%)
2. 🔄 LoRA comparison - In progress
3. ⏳ Full fine-tuning comparison

### Phase 2: Core Capabilities
4. **Tool Use** (60K) - Most practical for agentic AI
5. **Code Generation** (500K) - High value, clear evaluation
6. **Math Reasoning** (400K) - Measurable improvement

### Phase 3: Alignment & Quality
7. **DPO Alignment** (64K) - Makes model safer & better
8. **Conversational** (1.5M) - Multi-turn coherence

### Phase 4: Domain Specialization
9. **Summarization** (500K) - Clear use case
10. **Medical/Legal** - Domain expertise

### Phase 5: Creative
11. **Creative Writing** - Fun exploration

---

## Quick Start Commands

```bash
# Start fine-tuning container
cd ~/Projects/xiaohui-agentic-playground/6-open-source
./start_docker.sh start finetune

# Each experiment will have its own notebook in:
# fine-tuning-dense/experiments/
#   ├── 01_instruction_flan/
#   ├── 02_conversational/
#   ├── 03_code_generation/
#   ├── 04_math_reasoning/
#   ├── 05_medical/
#   ├── 06_legal/
#   ├── 07_dpo_alignment/
#   ├── 08_tool_use/
#   ├── 09_summarization/
#   └── 10_creative_writing/
```

---

## What's Next?

After completing the AG News experiments (QLoRA, LoRA, Full), which fine-tuning type would you like to tackle first?

**Recommended next:** Tool Use (60K examples, ~8 hours) - Most practical for building AI agents!
