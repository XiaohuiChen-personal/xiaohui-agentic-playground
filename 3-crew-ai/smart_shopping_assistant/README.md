# Smart Shopping Assistant

A multi-agent shopping assistant built with **CrewAI Flow** that helps users find, compare, and research products. This project replicates the functionality of the OpenAI Agents SDK version in `2-openai-sdk/smart_shopping_assistant/`.

## Architecture

```
                          ┌─────────────────────┐
                          │        USER         │
                          └──────────┬──────────┘
                                     │ ① Query
                                     ▼
                          ┌─────────────────────┐
                          │  🎯 CONCIERGE       │◄────────────────────┐
                          │  (Orchestrator)     │                     │
                          │  - Classifies intent│                     │
                          │  - Synthesizes      │                     │
                          │    responses        │                     │
                          └──────────┬──────────┘                     │
                                     │ ② Route                        │
                    ┌────────────────┴────────────────┐               │
                    ▼                                 ▼               │
         ┌─────────────────────┐          ┌─────────────────────┐    │
         │ 🔍 PRODUCT          │          │ ⭐ REVIEW           │    │
         │    SPECIALIST       │          │    ANALYST          │    │
         │                     │          │                     │    │
         │ • search_products   │          │ • search_products   │    │ ③ Results
         │ • get_product_      │          │ • get_product_      │    │
         │   details           │          │   reviews           │    │
         │                     │          │ • analyze_sentiment │    │
         └──────────┬──────────┘          └──────────┬──────────┘    │
                    │                                 │               │
                    └─────────────────────────────────┘───────────────┘
                                     │
                                     │ ④ Synthesize
                                     ▼
                          ┌─────────────────────┐
                          │  🎯 CONCIERGE       │
                          │  (Synthesis)        │
                          │  - Formats response │
                          │  - Offers next steps│
                          └──────────┬──────────┘
                                     │ ⑤ Response
                                     ▼
                          ┌─────────────────────┐
                          │        USER         │
                          └─────────────────────┘
```

**Flow:**
1. User sends a request to the Concierge
2. Concierge analyzes intent and routes to the appropriate specialist
3. Specialist uses tools and returns results to Concierge
4. Concierge synthesizes the results into a user-friendly response
5. Final response is delivered to the user

### Agents

| Agent | Model | Role |
|-------|-------|------|
| **Concierge** | `openai/gpt-5.2` | Orchestrates requests, classifies intent, synthesizes responses |
| **Product Specialist** | `anthropic/claude-opus-4-5-20251101` | Searches products, compares prices, gets specifications |
| **Review Analyst** | `anthropic/claude-opus-4-5-20251101` | Fetches reviews, analyzes sentiment, extracts pros/cons |

### Flow

1. **receive_user_query** - Entry point, stores user query
2. **concierge_classifies_intent** - LLM-based intent classification (not rule-based)
3. **route_to_specialist** - Routes to ONE specialist at a time
4. **execute_product_search** OR **execute_review_analysis** - Specialist execution
5. **synthesize_response** - Concierge formats final response
6. **save_results** - Persists results to output file

## Installation

Ensure you have Python >=3.10 <3.14 installed. This project uses [UV](https://docs.astral.sh/uv/) for dependency management.

```bash
# Install uv if not already installed
pip install uv

# Navigate to project directory
cd 3-crew-ai/smart_shopping_assistant

# Install dependencies
uv sync
```

### Environment Variables

The project loads API keys from the workspace root `.env` file (two levels up):

```
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
RAPID_API_KEY=your_rapidapi_key
```

**Note:** Do NOT create a local `.env` file in this project directory - it will override the workspace root keys.

## Running the Project

### Option 1: Using CrewAI CLI

```bash
cd 3-crew-ai/smart_shopping_assistant
crewai run
```

### Option 2: Using Python directly

```bash
cd 3-crew-ai/smart_shopping_assistant
uv run python -c "
from smart_shopping_assistant.main import kickoff
result = kickoff('Find me wireless headphones under \$100')
print(result.final_response)
"
```

### Option 3: Custom query via command line

```bash
cd 3-crew-ai/smart_shopping_assistant
uv run python -m smart_shopping_assistant.main '{"user_query": "Search for gaming laptops under $1500"}'
```

## Test Cases & Results

The following test cases were run to validate the implementation matches the OpenAI SDK version:

### Test Case 1: Product Search (General)

**Query:** `"Search for the top 5 over-ear wireless headphones under $100 with noise cancellation"`

| Metric | Result |
|--------|--------|
| **Status** | ✅ PASS |
| **Intent Classified** | `product_search` |
| **Specialist Used** | Product Specialist |
| **Response Length** | 2,896 characters |

**Flow Execution:**
```
✅ receive_user_query
✅ concierge_classifies_intent → product_search
✅ route_to_specialist
✅ execute_product_search
✅ synthesize_response
✅ save_results
```

### Test Case 2: Product Search (Specific Item)

**Query:** `"Search for Sony WH-1000XM4 headphones and show me the top 3 results with prices"`

| Metric | Result |
|--------|--------|
| **Status** | ✅ PASS |
| **Intent Classified** | `product_search` |
| **Specialist Used** | Product Specialist |
| **Response Length** | 2,095 characters |

**Response included:**
- Top 3 product listings with prices
- Store information (Best Buy)
- Ratings and review counts
- Best value recommendation

### Test Case 3: Review Analysis

**Query:** `"What do the reviews say about the Sony WH-1000XM4? Give me the pros and cons."`

| Metric | Result |
|--------|--------|
| **Status** | ✅ PASS |
| **Intent Classified** | `review_analysis` |
| **Specialist Used** | Review Analyst |
| **Response Length** | 4,764 characters |

**Flow Execution:**
```
✅ receive_user_query
✅ concierge_classifies_intent → review_analysis
✅ route_to_specialist
✅ execute_review_analysis
✅ synthesize_response
✅ save_results
```

**Response included:**
- Overall sentiment analysis
- Top pros (ANC quality, battery life, comfort, sound quality)
- Top cons (hinge durability, call quality, touch controls)
- Red flags (hinge breakage, charging issues)
- Purchase recommendations

## Test Summary

| Test | Query Type | Intent | Status |
|------|-----------|--------|--------|
| 1 | Product search (general) | `product_search` | ✅ PASS |
| 2 | Product search (specific) | `product_search` | ✅ PASS |
| 3 | Review analysis | `review_analysis` | ✅ PASS |

**All 3 test cases passed successfully**, demonstrating that:
- ✅ Concierge correctly classifies user intent using LLM
- ✅ Only ONE specialist is routed to at a time (matching OpenAI SDK behavior)
- ✅ Product Specialist correctly uses `search_products` tool
- ✅ Review Analyst correctly uses `search_products` → `get_product_reviews` → `analyze_sentiment` workflow
- ✅ Concierge synthesizes specialist results into user-friendly responses

## Output Files

Results are saved to `src/smart_shopping_assistant/output/` with filenames like:
- `shopping_result_20251229_225253.txt`

Each file contains:
- Timestamp and intent classification
- Concierge's reasoning
- Final synthesized response
- Raw specialist results

## Key Differences from OpenAI SDK Version

| Aspect | OpenAI SDK | CrewAI Flow |
|--------|------------|-------------|
| **Handoffs** | Native `transfer_to_*` functions | `@router()` decorator with string routes |
| **State** | Conversation context | Pydantic `BaseModel` state |
| **Intent Classification** | Concierge LLM decides | Concierge runs `classify_intent_task` |
| **Multi-event listening** | N/A | `@listen(or_(a, b))` |
| **Result synthesis** | Implicit in handoff | Explicit `synthesize_response` step |

## Project Structure

```
smart_shopping_assistant/
├── src/smart_shopping_assistant/
│   ├── main.py                 # Flow definition
│   ├── output/                 # Saved results
│   ├── crews/
│   │   └── smart_shopping_assistant_crew/
│   │       ├── config/
│   │       │   ├── agents.yaml # Agent definitions
│   │       │   └── tasks.yaml  # Task definitions
│   │       └── smart_shopping_assistant_crew.py
│   └── tools/
│       └── custom_tool.py      # RapidAPI tools
├── pyproject.toml
└── README.md
```

## Support

For questions about CrewAI:
- [CrewAI Documentation](https://docs.crewai.com)
- [CrewAI GitHub](https://github.com/joaomdmoura/crewai)
- [CrewAI Discord](https://discord.com/invite/X4JWnZnxPb)
