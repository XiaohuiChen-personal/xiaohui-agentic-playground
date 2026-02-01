# Email Battle: Open Source Edition

A CrewAI Flow simulation using **local open-source LLMs** via vLLM for a government efficiency review email exchange between **Elon Musk** (Head of DOGE) and **John Smith** (a coasting USCIS employee).

## Latest Battle Results

| Metric | Value |
|--------|-------|
| **Winner** | 🔴 Elon Musk (DOGE) |
| **Decision** | TERMINATED |
| **Total Rounds** | 4 |
| **Total Emails** | 11 |
| **Runtime** | ~12 minutes |

**Summary**: John Smith was terminated after 4 rounds of follow-up. Despite providing case IDs and claiming a "25% reduction in processing time," Elon found his responses filled with "vague descriptions, systemic excuses, and generalized statements." John's consistent deflection to "outdated IT systems" and "lack of supervision" failed to satisfy DOGE's demand for measurable, numerical outcomes.

## Overview

This is the open-source version of the Email Battle project, running entirely on local models:

| Character | Model | Port | Strengths |
|-----------|-------|------|-----------|
| **Elon Musk** | Qwen3-32B-NVFP4 | 8001 | Reasoning, analysis, probing questions |
| **John Smith** | Mistral-Small-24B-NVFP4 | 8000 | Language generation, bureaucratic style |

The battle can go up to **5 follow-up rounds** before a final decision is made.

## Prerequisites

### 1. Start the Local vLLM Models

Before running the email battle, ensure both models are running:

```bash
# From the 6-open-source directory
cd ../  # Go to 6-open-source

# Start both models (handles sequential startup automatically)
./start_docker.sh start dual

# Verify both models are ready
./start_docker.sh status
```

Expected output:
```
Port 8000: ● Ready (RedHatAI/Mistral-Small-3.2-24B-Instruct-2506-NVFP4)
Port 8001: ● Ready (nvidia/Qwen3-32B-NVFP4)
```

### 2. Install Dependencies

```bash
cd email_battle_open_source

# Install uv if not already installed
pip install uv

# Install project dependencies
crewai install
```

## Running the Battle

```bash
crewai run
```

Or directly with Python:

```bash
cd src
python -m email_battle.main
```

## Possible Outcomes

| Decision | Winner | Description |
|----------|--------|-------------|
| `PASS` | John | Initial response accepted, no follow-up needed |
| `RETAINED` | John | Employee demonstrated adequate value after scrutiny |
| `TERMINATED` | Elon | Employee identified as coasting and fired |
| `MAX_ROUNDS` | Draw | 5 rounds completed without clear decision |

## Project Structure

```
email_battle_open_source/
├── src/email_battle/
│   ├── main.py                          # Flow orchestration (EmailBattleFlow)
│   ├── crews/
│   │   └── email_battle_crew/
│   │       ├── config/
│   │       │   ├── agents.yaml          # Agent definitions (Elon & John)
│   │       │   └── tasks.yaml           # Task definitions (5 tasks)
│   │       └── email_battle_crew.py     # CrewBase class with LLM configs
│   └── tools/                           # Custom tools (unused)
├── email_battle_result.txt              # Output from last run
├── pyproject.toml                       # Dependencies
└── README.md                            # This file
```

## Flow Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                   EMAIL BATTLE FLOW (Open Source)                │
└─────────────────────────────────────────────────────────────────┘

    ┌──────────────────────┐
    │  @start              │
    │  elon_sends_mass_    │──────────────────┐
    │  email (Qwen3)       │                  │
    └──────────────────────┘                  ▼
                                    ┌──────────────────────┐
                                    │  @listen             │
                                    │  john_replies_to_    │
                                    │  mass_email (Mistral)│
                                    └──────────┬───────────┘
                                               │
                                               ▼
                                    ┌──────────────────────┐
                                    │  @listen             │
                                    │  elon_evaluates_     │
                                    │  initial (Qwen3)     │
                                    └──────────┬───────────┘
                                               │
                                               ▼
                                    ┌──────────────────────┐
                                    │  @router             │
                                    │  PASS → end_battle   │
                                    │  FOLLOW-UP → loop    │
                                    └──────────┬───────────┘
                                               │
                         ┌─────────────────────┼─────────────────────┐
                         ▼                     │                     ▼
              ┌─────────────────┐              │          ┌─────────────────┐
              │  john_follow_up │              │          │  end_battle     │
              │  (Mistral)      │◄─────────────┘          │  conclude       │
              └────────┬────────┘                         └─────────────────┘
                       │
                       ▼
              ┌─────────────────┐
              │  elon_evaluate_ │
              │  follow_up      │
              │  (Qwen3)        │───────► (loop back or end)
              └─────────────────┘
```

## Model Configuration

The LLM configuration is in `email_battle_crew.py`:

```python
# Qwen3-32B for Elon (strong reasoning)
QWEN_LLM = LLM(
    model="openai/nvidia/Qwen3-32B-NVFP4",
    base_url="http://localhost:8001/v1",
    api_key="EMPTY",
    temperature=0.7,
    max_tokens=2048,
    # Disable Qwen3's thinking mode for cleaner output
    extra_body={"chat_template_kwargs": {"enable_thinking": False}},
)

# Mistral-24B for John (language generation)
MISTRAL_LLM = LLM(
    model="openai/RedHatAI/Mistral-Small-3.2-24B-Instruct-2506-NVFP4",
    base_url="http://localhost:8000/v1",
    api_key="EMPTY",
    temperature=0.7,
    max_tokens=2048,
)
```

### vLLM Server Configuration

Both models run with **32K context windows** to support long email threads:

| Parameter | Mistral-24B | Qwen3-32B |
|-----------|-------------|-----------|
| `gpu-memory-utilization` | 0.30 | 0.35 |
| `max-num-seqs` | 1 | 1 |
| `max-model-len` | 32768 | 32768 |

This configuration is optimized for CrewAI's sequential processing (one agent at a time) on DGX Spark's 128 GB unified memory.

## Sample Output

```
🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀
STARTING EMAIL BATTLE: Elon Musk vs John Smith
Using Local Open-Source Models via vLLM
🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀

📡 Model Configuration:
   Elon Musk: Qwen3-32B-NVFP4 @ http://localhost:8001
   John Smith: Mistral-Small-24B-NVFP4 @ http://localhost:8000

============================================================
📧 PHASE 1: Elon Musk sends mass email (Qwen3-32B)
============================================================
✅ Mass email sent:
**Subject: Week 51 Productivity Report – 5 Specific Accomplishments Required**
...

============================================================
📧 PHASE 2: John Smith replies to mass email (Mistral-24B)
============================================================
✅ John's reply:
Subject: RE: Week 51 Productivity Report – 5 Specific Accomplishments
Dear Mr. Musk,
...

============================================================
📧 FOLLOW-UP ROUND 1-4: Back and forth exchanges
============================================================
🔍 Decision parsed: FOLLOW-UP
🔄 FOLLOW-UP - Continuing to round 2
...

🏆 EMAIL BATTLE CONCLUDED
============================================================

📊 FINAL RESULTS:
   Decision: TERMINATED
   Winner: ELON
   Total Rounds: 4
   Total Emails: 11

🤖 MODELS USED:
   Elon (DOGE): Qwen3-32B-NVFP4 (localhost:8001)
   John (USCIS): Mistral-Small-24B-NVFP4 (localhost:8000)

📧 EMAIL THREAD SUMMARY:
   1. 🔴 ELON: DOGE Efficiency Review - Weekly Accomplishments Re...
   2. 🔵 JOHN: RE: DOGE Efficiency Review - Weekly Accomplishment...
   3. 🔴 ELON: RE: RE: DOGE Efficiency Review - Follow-up Require...
   4. 🔵 JOHN: RE: RE: RE: DOGE Efficiency Review...
   ...
   11. 🔴 ELON: Notice of Termination - DOGE Review...

💾 Full results saved to: email_battle_result.txt
```

## Comparison with Cloud Version

| Aspect | Cloud Version | Open Source Version |
|--------|---------------|---------------------|
| Elon's Model | GPT-5.2 | Qwen3-32B-NVFP4 |
| John's Model | Claude Opus 4.5 | Mistral-Small-24B-NVFP4 |
| API Cost | ~$2-5 per battle | Free (local) |
| Latency | Network dependent | ~60-90s per email (sequential) |
| Context Window | Model dependent | 32K tokens |
| Privacy | Data sent to cloud | Fully local |
| Hardware | None required | DGX Spark (128 GB unified memory) |

## Troubleshooting

### Models Not Responding

```bash
# Check if models are running
curl http://localhost:8000/health
curl http://localhost:8001/health

# If not, start them
cd ..  # Go to 6-open-source
./start_docker.sh start dual
```

### Connection Refused

Ensure the vLLM containers are running:

```bash
docker ps | grep vllm
```

### Out of Memory

If running on limited hardware, adjust parameters in `docker-compose-dual-medium.yml`:

```yaml
# Reduce context window (default: 32768)
--max-model-len 8192

# Reduce memory allocation
--gpu-memory-utilization 0.25
```

### Context Length Exceeded

If you see errors like "maximum context length exceeded", the email thread has grown too long. Options:
1. Reduce `MAX_FOLLOW_UP_ROUNDS` in `main.py`
2. Increase `--max-model-len` in docker-compose (requires more memory)
3. Limit context with `max_emails` parameter in `format_email_thread()` (not recommended)

## Support

- [CrewAI Documentation](https://docs.crewai.com)
- [vLLM Documentation](https://docs.vllm.ai)
- [Qwen3 Model Card](https://huggingface.co/nvidia/Qwen3-32B-NVFP4)
- [Mistral Model Card](https://huggingface.co/RedHatAI/Mistral-Small-3.2-24B-Instruct-2506-NVFP4)
