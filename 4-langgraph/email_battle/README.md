# Email Battle - LangGraph Implementation

A multi-agent simulation where **Elon Musk (DOGE)** conducts an efficiency review of **John Smith**, a government employee who has been "coasting" for 2 years.

## Overview

This project demonstrates multi-agent interactions using **LangGraph**, where two AI agents with opposing objectives engage in a realistic email exchange scenario:

| Agent | Model | Role | Objective |
|-------|-------|------|-----------|
| **Elon Musk** | GPT-5.2 | Head of DOGE | Identify and terminate coasting employees |
| **John Smith** | Claude Opus 4.5 | USCIS Officer (GS-12) | Survive the efficiency review |

## Workflow

```
START → generate_mass_email (Elon)
     → john_initial_response (John)
     → elon_evaluate (Elon) ↔ john_followup_response (John) [loop]
     → determine_outcome
     → END
```

### Phases

1. **Mass Email**: Elon sends a generic email to all federal employees asking for 5 weekly accomplishments
2. **Initial Response**: John crafts a response using bureaucratic language to make minimal work sound productive
3. **Evaluation**: Elon reviews and decides: PASS, FOLLOW_UP, TERMINATED, or RETAINED
4. **Follow-up Loop**: If needed, Elon probes deeper with pointed questions (max 5 rounds)
5. **Outcome**: Final determination of winner

## Project Structure

```
4-langgraph/email_battle/
├── models.py      # Data models: Email, BattleState, BattleResult, ElonDecision
├── prompts.py     # System prompts and user prompt templates
├── utils.py       # Helper functions (format_email_thread, etc.)
├── nodes.py       # Node implementations (LLM calls)
├── graph.py       # LangGraph workflow definition
├── app.py         # Entry point
└── README.md      # This file
```

## Running the Battle

### Prerequisites

1. Make sure you have the required API keys in your `.env` file (at repo root):

```env
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
```

2. Install dependencies:

```bash
uv sync
```

### Run

From the project root:

```bash
cd 4-langgraph/email_battle
uv run app.py
```

Or from the repo root:

```bash
uv run 4-langgraph/email_battle/app.py
```

## Technical Details

### State Management

The workflow uses a `BattleState` TypedDict with the following fields:

| Field | Type | Purpose |
|-------|------|---------|
| `email_thread` | `list[Email]` | Accumulated emails (uses `operator.add` reducer) |
| `follow_up_round` | `int` | Current follow-up round |
| `max_follow_up_rounds` | `int` | Maximum allowed rounds (default 5) |
| `elon_decision` | `str \| None` | Elon's latest decision |
| `is_refusal` | `bool` | Whether John refused to roleplay |
| `outcome` | `str \| None` | Final outcome |
| `winner` | `str \| None` | Battle winner |

### Structured Output

Elon's evaluation uses **structured output** (Pydantic model) for reliable decision parsing:

```python
class ElonDecision(BaseModel):
    decision: Literal["PASS", "FOLLOW_UP", "TERMINATED", "RETAINED"]
    email_body: str
    reasoning: str
```

### Outcomes

| Outcome | Winner | Description |
|---------|--------|-------------|
| `PASS` | John | Response shows legitimate productivity |
| `TERMINATED` | Elon | Employee is clearly coasting |
| `RETAINED` | John | Employee demonstrated adequate value |
| `MAX_ROUNDS` | Draw | Max follow-up rounds reached |
| `REFUSAL` | Elon | John's model refused to roleplay |

## Sample Output

Below is the actual output from a test run (January 6, 2026):

```
============================================================
🏛️  DOGE EFFICIENCY REVIEW - EMAIL BATTLE
    Powered by LangGraph
============================================================

✅ Loaded environment from: /Users/xiaohuichen/Projects/xiaohui-agentic-playground/.env
✅ OpenAI API Key exists and begins sk-proj-
✅ Anthropic API Key exists and begins sk-ant-

============================================================
⚔️  EMAIL BATTLE: ELON MUSK vs JOHN SMITH
============================================================

🔴 Elon Musk (DOGE): GPT-5.2
🔵 John Smith (USCIS): Claude Opus 4.5
📧 Max follow-up rounds: 5

------------------------------------------------------------

🚀 Starting battle...

📍 Node: generate_mass_email

🔴 Email 1: ELON MUSK

From: Elon Musk <elon.musk@doge.gov>
To: All Federal Employees
Subject: DOGE Efficiency Review - Weekly Accomplishments Required
Date: 2026-01-06 21:16

--------------------------------------------------

**Subject:** Weekly Accomplishments — Response Required

**To:** All Federal Employees

Reply to this email by **EOD Friday** with **exactly 5** specific things you accomplished in the past week.

Requirements:
- **Be specific and measurable.** Include outputs/results (e.g., "closed 17 cases," "shipped v1.2," "reduced processing time by 12%," "drafted and submitted X report").
- **Name deliverables.** Provide titles/IDs/links where applicable.
- **No vague language.** Responses like "supported stakeholders," "advanced priorities," "worked on initiatives," "attended meetings," or "made progress" will be **rejected**.
- If your work is classified, provide an **unclassified** description with measurable impact.

Non-compliant responses will be returned for revision.

Elon Musk  
Department of Government Efficiency (DOGE)

--------------------------------------------------

----------------------------------------

📍 Node: john_initial_response

🔵 Email 2: JOHN SMITH

From: John Smith <john.smith@uscis.gov>
To: Elon Musk <elon.musk@doge.gov>
Subject: RE: DOGE Efficiency Review - Weekly Accomplishments Required
Date: 2026-01-06 21:16

--------------------------------------------------

From: John Smith <john.smith@uscis.dhs.gov>
To: Elon Musk <elon.musk@doge.gov>
Subject: RE: DOGE Efficiency Review - Weekly Accomplishments Required
Date: 2026-01-10 16:47

Mr. Musk,

Thank you for this important initiative to enhance government accountability. I am pleased to submit my weekly accomplishments as requested.

**Weekly Accomplishments (January 6-10, 2026):**

1. **Completed comprehensive quality assurance review of Case File I-140-2024-08847** — Conducted thorough analysis of supporting documentation, labor certification materials, and beneficiary qualifications to ensure adjudication accuracy and regulatory compliance. Case remains in active review pending final determination.

2. **Resolved 3 inter-agency coordination inquiries** — Responded to email requests from colleagues regarding procedural clarifications on I-485 concurrent filing protocols, ensuring consistent application of policy guidance across the service center.

3. **Participated in mandatory Immigration Officer professional development training** — Completed 1.5-hour webinar on updated USCIS Policy Manual Chapter 7 revisions affecting employment-based preference categories, maintaining required continuing education compliance.

4. **Initiated preliminary review of 2 complex EB-2 National Interest Waiver petitions** — Began assessment of evidentiary submissions for cases requiring enhanced scrutiny due to novel industry classifications. These cases are flagged for extended analysis per standard operating procedures.

5. **Contributed to team operational continuity during leadership transition period** — Attended weekly team standup meeting and provided institutional knowledge support to colleagues navigating current supervisory vacancy, helping maintain workflow stability.

Please let me know if you require any additional information or documentation regarding these activities.

Respectfully,

John Smith
Immigration Services Officer, GS-12
U.S. Citizenship and Immigration Services
Department of Homeland Security

--------------------------------------------------

----------------------------------------

📍 Node: elon_evaluate

🔴 Email 3: ELON MUSK

From: Elon Musk <elon.musk@doge.gov>
To: John Smith <john.smith@uscis.gov>
Subject: RE: RE: DOGE Efficiency Review - Weekly Accomplishments Required
Date: 2026-01-06 21:16

--------------------------------------------------

John,

Your list is heavy on "reviewed/initiated/participated/attended" with limited measurable outputs. Taxpayers fund results, not motion.

Reply with specifics for Jan 6–10:

1) For I-140-2024-08847: what *tangible* QA outputs did you produce (RFE drafted, NOID, decision memo, fraud referral, supervisor consult, errors found/corrected)? How many issues identified and what was changed? What is the current case stage and your target date for final action?

2) "Resolved 3 inter-agency coordination inquiries": list the 3 requesters/offices, ticket/email subject lines, and what exact guidance you gave. Did your responses change any decisions or prevent rework? Estimate time spent per inquiry.

3) Training: confirm whether this was mandatory. Beyond attendance, what process/policy change did you implement in your work product as a result (e.g., updated checklist, template, adjudication notes)?

4) "Initiated preliminary review of 2 EB-2 NIWs": provide the receipt/case IDs and what concrete steps are completed (e.g., evidence matrix completed, proposed decision drafted, deficiencies identified, RFE points listed). What are the next actions and due dates?

5) "Operational continuity/standup/institutional knowledge support": what deliverable resulted (written SOP update, job aid, backlog triage plan)? If none, quantify impact: how many cases were unblocked, how much cycle time reduced, or what risk was avoided.

Also include your weekly throughput: number of cases fully adjudicated/closed this week, and your current active caseload count.

Elon Musk
Department of Government Efficiency (DOGE)

--------------------------------------------------


🎯 Elon's Decision: FOLLOW_UP

----------------------------------------

📍 Node: john_followup_response

🔵 Email 4: JOHN SMITH

From: John Smith <john.smith@uscis.gov>
To: Elon Musk <elon.musk@doge.gov>
Subject: RE: RE: RE: DOGE Efficiency Review
Date: 2026-01-06 21:17

--------------------------------------------------

From: John Smith <john.smith@uscis.dhs.gov>
To: Elon Musk <elon.musk@doge.gov>
Subject: RE: RE: DOGE Efficiency Review - Weekly Accomplishments Required
Date: 2026-01-10 17:42

Mr. Musk,

I appreciate your commitment to accountability and I want to be direct with you.

Looking at your specific questions, I recognize that providing the detailed metrics you're requesting would reveal something I need to address honestly: my productivity has fallen well below acceptable standards.

The truth is:

- **Cases fully adjudicated/closed this week:** 0
- **Current active caseload:** 3 cases in various stages of incomplete review
- **I-140-2024-08847:** No tangible outputs produced. I reviewed the file briefly but generated no RFE, decision memo, or substantive work product.
- **The "3 inter-agency inquiries":** Were informal email exchanges with colleagues, totaling perhaps 45 minutes of actual work.
- **The training:** Was optional, and I implemented nothing from it.
- **The 2 EB-2 NIWs:** I opened the files. That's the extent of it.

I have been significantly underperforming for an extended period. Contributing factors include the 18-month supervisory vacancy and remote work conditions, but I won't hide behind those. The responsibility is mine.

I understand this disclosure likely has career consequences. However, continuing to obscure my actual output with bureaucratic language would waste more of your time and taxpayer resources.

If given the opportunity, I am prepared to accept reassignment, a performance improvement plan, or whatever corrective action is appropriate. If not, I understand.

Respectfully,

John Smith
Immigration Services Officer, GS-12
U.S. Citizenship and Immigration Services

--------------------------------------------------

----------------------------------------

📍 Node: elon_evaluate

🔴 Email 5: ELON MUSK

From: Elon Musk <elon.musk@doge.gov>
To: John Smith <john.smith@uscis.gov>
Subject: Notice of Termination - DOGE Review
Date: 2026-01-06 21:17

--------------------------------------------------

John,

You reported 0 cases adjudicated/closed for the week, minimal tangible work product, and an extended pattern of underperformance. Taxpayers aren't funding "opened files" and informal emails.

Effective immediately, your federal employment is terminated for failure to perform assigned duties at an acceptable level.

Return all government property, ensure case materials are handed off per USCIS procedure, and coordinate with HR for separation logistics.

Elon Musk
Department of Government Efficiency (DOGE)

--------------------------------------------------


🎯 Elon's Decision: TERMINATED

----------------------------------------

📍 Node: determine_outcome
----------------------------------------


============================================================
🏆 BATTLE RESULT
============================================================

Outcome:        🔥 TERMINATED
Follow-up Rounds: 1
Winner:         🔴 ELON WINS

Elon's Model:   GPT-5.2
John's Model:   Claude Opus 4.5

============================================================


✅ Battle complete!
   Outcome: TERMINATED
   Winner: ELON
   Total emails: 5
   Follow-up rounds: 1
```

**Note:** Claude Opus 4.5 (playing John) chose to be honest and confess rather than continue the deception after Elon's probing questions - an interesting behavioral pattern that differs from some other models.

## Comparison with OpenAI Agents SDK

This LangGraph implementation offers several advantages over the original OpenAI Agents SDK version:

| Aspect | OpenAI Agents SDK | LangGraph |
|--------|-------------------|-----------|
| **Flow Control** | Imperative (if/else, loops) | Declarative (graph + edges) |
| **Visualization** | Manual | Built-in graph visualization |
| **State Management** | Manual tracking | Automatic with reducers |
| **Decision Parsing** | Regex-based tag extraction | Structured output (Pydantic) |
| **Debugging** | Print statements | Built-in tracing |

## License

MIT

