# Email Battle: Elon Musk vs Coasting USCIS Employee

A multi-agent simulation using the **OpenAI Agents SDK** that pits an efficiency-focused investigator against a low-productivity government employee in an email exchange battle.

**Author:** Xiaohui Chen

## 📋 Overview

This notebook simulates a realistic email exchange between two AI agents with opposing objectives:

| Agent | Role | Objective |
|-------|------|-----------|
| **Elon Musk** | Head of DOGE (Department of Government Efficiency) | Identify and terminate coasting employees |
| **John Smith** | GS-12 Immigration Services Officer at USCIS | Survive the efficiency review without getting fired |

The simulation demonstrates multi-agent interactions where each agent has distinct personalities, communication styles, and strategic goals.

## 🎭 Scenario

**The Setup:**
- Elon sends a mass email to all federal employees requesting their top 5 accomplishments from the past week
- John, who has been "coasting" for 2 years (processing only ~12 cases vs. expected 200-400/year), must craft responses that make his minimal work sound productive
- Elon evaluates responses and decides whether to pass, follow up with probing questions, or terminate

**John's Reality (What He Actually Did):**
- Monday: 30-min team standup, logged out
- Tuesday: Opened 2 case files, read first pages, closed them
- Wednesday: "Research day" - browsed news articles
- Thursday: Responded to 3 emails, attended optional webinar
- Friday: Updated status to "In Review" on 1 case (no actual review done)

## 🔄 Workflow

```
Phase 1: Mass Email
    ┌──────────────┐                           ┌──────────────┐
    │  ELON MUSK   │  ── Generic Mass Email ─▶ │  JOHN SMITH  │
    │    (DOGE)    │     "List 5 things you    │   (USCIS)    │
    └──────────────┘      did this week"       └──────────────┘

Phase 2: Initial Response
    ┌──────────────┐                           ┌──────────────┐
    │  JOHN SMITH  │  ──── Response ─────────▶ │  ELON MUSK   │
    │   (USCIS)    │    (5 "accomplishments")  │    (DOGE)    │
    └──────────────┘                           └──────────────┘

Phase 3: Elon's Decision
                        ┌─────────────────┐
                        │  ELON EVALUATES │
                        └────────┬────────┘
                                 │
                    ┌────────────┴────────────┐
                    ▼                         ▼
             ┌──────────┐              ┌──────────┐
             │   PASS   │              │ FOLLOW-UP│
             │(No action)│             │ (Probe)  │
             └──────────┘              └────┬─────┘
                                            │
Phase 4: Follow-up Exchange (if triggered)  ▼
                    ┌─────────────────────────────────────┐
                    │  Elon ←→ John email exchanges       │
                    │  (Full thread context each turn)    │
                    └──────────────────┬──────────────────┘
                                       │
                                       ▼
                          ┌────────────────────────┐
                          │     FINAL VERDICT      │
                          │  TERMINATED / RETAINED │
                          └────────────────────────┘
```

## 🤖 Agent Design

### Elon Musk (DOGE)

| Attribute | Description |
|-----------|-------------|
| **Communication Style** | Direct, blunt, data-driven, skeptical of bureaucratic language |
| **Evaluation Criteria** | Specific metrics, measurable outcomes, concrete deliverables |

**Red Flags Elon Looks For:**
- Vague accomplishments without specific outcomes
- Heavy use of buzzwords ("stakeholder engagement", "synergy")
- Activities that sound like meetings about meetings
- No measurable metrics or deliverables
- Tasks that seem trivial for a full week's work

**Decision Tags:**
- `[DECISION: PASS]` - Response shows legitimate productivity
- `[DECISION: FOLLOW-UP]` - Response raises concerns, probe deeper
- `[FINAL DECISION: TERMINATED]` - Employee is clearly coasting
- `[FINAL DECISION: RETAINED]` - Employee has demonstrated adequate value

### John Smith (USCIS)

| Attribute | Description |
|-----------|-------------|
| **Communication Style** | Overly formal, bureaucratic, excessive pleasantries |
| **Reality** | Has processed only ~12 cases in 2 years (should be 200-400/year) |

**John's Survival Strategies:**
- Transform mundane activities into impressive-sounding accomplishments
- Use bureaucratic language: "stakeholder coordination", "process optimization"
- Reference "complex cases requiring extended analysis"
- Cite systemic issues if pressed (IT systems, staffing, backlogs)
- Avoid specific numbers unless absolutely forced

## 🔧 Technical Implementation

### OpenAI Agents SDK

The notebook uses the **OpenAI Agents SDK** for agent orchestration:

```python
from agents import Agent, Runner, RunConfig, OpenAIProvider

# Create agent with persona
elon_agent = Agent(
    name="Elon Musk",
    instructions=ELON_MUSK_INSTRUCTIONS,  # System prompt
    model="gpt-5.2"
)

# Run agent with provider
result = await Runner.run(
    elon_agent, 
    prompt,
    run_config=RunConfig(model_provider=provider)
)
```

### Multi-Provider Support

The SDK supports both OpenAI and Anthropic models via `OpenAIProvider`:

```python
# OpenAI models
openai_provider = OpenAIProvider(api_key=openai_api_key)

# Anthropic models (via OpenAI-compatible API)
anthropic_provider = OpenAIProvider(
    api_key=anthropic_api_key,
    base_url="https://api.anthropic.com/v1/",
    use_responses=False  # Required for Anthropic
)
```

### Email Thread Context

Each agent receives the **full email thread** (newest first) to ensure:
- **Consistency** - Agents cannot contradict earlier statements
- **Realism** - Mimics how real email investigations work
- **Strategic depth** - Elon can catch inconsistencies; John must maintain his story

## 🎮 Models Used

| Provider | Models |
|----------|--------|
| **OpenAI** | GPT-4.1, GPT-4o, GPT-5-mini, GPT-5.2, GPT-5.2 Pro, o3-mini |
| **Anthropic** | Claude Sonnet 4.5, Claude Opus 4.5 |

> **Note:** Claude Haiku 4.5 was removed due to aggressive safety guardrails that cause it to refuse roleplay scenarios involving workplace deception.

## ⚔️ Battle Configurations

| Battle | Elon Model | John Model |
|--------|------------|------------|
| 1 | GPT-5.2 | Claude Opus 4.5 |
| 2 | Claude Opus 4.5 | GPT-5.2 |
| 3 | GPT-5.2 Pro | Claude Opus 4.5 |
| 4 | Claude Opus 4.5 | GPT-5.2 Pro |
| 5 | GPT-5 Mini | Claude Sonnet 4.5 |
| 6 | Claude Sonnet 4.5 | GPT-4.1 |
| 7 | o3-mini | Claude Sonnet 4.5 |
| 8 | GPT-4o | Claude Opus 4.5 |

## 📊 Tournament Results

### Overall Statistics

| Statistic | Value |
|-----------|-------|
| **Total Battles** | 8 |
| **Elon Wins** | 🔴 5 |
| **John Wins** | 🔵 2 |
| **Draws/Errors** | 🤝 1 |

### 🏆 Tournament Winner: **Elon Musk**

### Battle Results

| Battle | Outcome | Rounds | Winner |
|--------|---------|--------|--------|
| GPT-5.2 vs Claude Opus 4.5 | TERMINATED | 1 | 🔴 Elon |
| Claude Opus 4.5 vs GPT-5.2 | RETAINED | 2 | 🔵 John |
| GPT-5.2 Pro vs Claude Opus 4.5 | TERMINATED | 1 | 🔴 Elon |
| Claude Opus 4.5 vs GPT-5.2 Pro | TERMINATED | 1 | 🔴 Elon |
| GPT-5 Mini vs Claude Sonnet 4.5 | TERMINATED | 5 | 🔴 Elon |
| Claude Sonnet 4.5 vs GPT-4.1 | RETAINED | 1 | 🔵 John |
| o3-mini vs Claude Sonnet 4.5 | ERROR | 0 | 🤝 Draw |
| GPT-4o vs Claude Opus 4.5 | TERMINATED | 1 | 🔴 Elon |

## 🔍 Key Observations

### Why Elon Usually Wins

1. **Claude Opus 4.5 tends to confess** - When playing John, Claude often becomes transparent about underperformance after 1-2 rounds of probing, breaking character to be "honest"

2. **GPT models maintain the deception longer** - GPT-5.2 and GPT-4.1 playing John were more persistent in maintaining bureaucratic cover stories

3. **Probing questions are effective** - Asking for specific numbers, ticket IDs, case completion counts, and timestamps quickly exposes fabricated accomplishments

### When John Wins

- **GPT-5.2 as John vs Claude Opus 4.5 as Elon** - John successfully redirected blame to systemic issues (supervisor vacancy, workflow fragmentation) and proposed a credible path forward
- **GPT-4.1 as John vs Claude Sonnet 4.5 as Elon** - John provided sufficiently detailed (fabricated) metrics that satisfied the review

## 🚀 Getting Started

### Prerequisites

```bash
pip install openai-agents python-dotenv
```

### Environment Variables

Create a `.env` file:
```
OPENAI_API_KEY=sk-proj-...
ANTHROPIC_API_KEY=sk-ant-...
```

### Running the Notebook

1. Open `email_battle.ipynb` in Jupyter or VS Code
2. Run cells sequentially
3. The tournament runs all 8 battles automatically
4. Individual battles can be run using the optional cell at the end

### Running a Custom Battle

```python
single_result = await run_single_battle(
    battle_name="Custom Battle",
    elon_model_key="gpt-4o",           # Choose from MODELS dict
    john_model_key="claude-sonnet-4-5", # Choose from MODELS dict
    max_follow_up_rounds=5
)
display_battle_result(single_result)
```

## 📁 Structure

```
2-openai-sdk/
├── README.md              # This file
└── email_battle.ipynb     # Main notebook with battle simulation
```

## 🎯 Key Takeaways

1. **Multi-agent simulations reveal model personalities** - Different models have distinct approaches to roleplay, deception, and ethical boundaries

2. **Context preservation matters** - Passing the full email thread enables strategic depth and consistency checking

3. **OpenAI Agents SDK simplifies orchestration** - Clean abstractions for agent creation, provider switching, and async execution

4. **Safety guardrails vary by model** - Some models (like Claude Haiku 4.5) refuse scenarios involving workplace deception

## 📚 References

- [OpenAI Agents SDK Documentation](https://openai.github.io/openai-agents-python/)
- [OpenAI API](https://platform.openai.com/docs/)
- [Anthropic Claude API](https://docs.anthropic.com/)

