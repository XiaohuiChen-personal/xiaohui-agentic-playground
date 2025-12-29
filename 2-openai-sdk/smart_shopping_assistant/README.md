# Smart Shopping Assistant

A **multi-agent shopping assistant** built with the **OpenAI Agents SDK** that demonstrates tools, handoffs, and orchestration patterns.

## Overview

This project showcases how to build a collaborative AI system where specialized agents work together to help users find, compare, and research products. The system uses:

- **Tools** - Function calling to interact with external APIs
- **Handoffs** - Native SDK mechanism for agent-to-agent delegation
- **Bidirectional Orchestration** - Specialists hand back to the orchestrator for response synthesis

## Architecture

```
                              ┌─────────────────────┐
                              │        USER         │
                              └──────────┬──────────┘
                                         │
                                         ▼
                              ┌─────────────────────┐
                              │  🎯 CONCIERGE       │◄────────────────┐
                              │    (gpt-5.2-pro)    │                 │
                              │    Orchestrator     │                 │
                              └──────────┬──────────┘                 │
                                         │                            │
                           ┌─────────────┴─────────────┐              │
                           │         HANDOFF           │              │
                           ▼                           ▼              │
                ┌─────────────────────┐     ┌─────────────────────┐   │
                │ 🔍 PRODUCT          │     │ ⭐ REVIEW           │   │
                │    SPECIALIST       │     │    ANALYST          │   │
                │    (gpt-5.2)        │     │    (gpt-5.2)        │   │
                │                     │     │                     │   │
                │ Tools:              │     │ Tools:              │   │
                │ • search_products   │     │ • search_products   │   │
                │ • get_product_      │     │ • get_product_      │   │
                │   details           │     │   reviews           │   │
                │                     │     │ • analyze_sentiment │   │
                └──────────┬──────────┘     └──────────┬──────────┘   │
                           │                           │              │
                           └───────────────────────────┘              │
                                         │                            │
                                         └──── HANDOFF BACK ──────────┘
```

## Agents

| Agent | Model | Role | Tools |
|-------|-------|------|-------|
| **Concierge** | `gpt-5.2-pro` | Orchestrator - routes requests and synthesizes responses | None (handoffs only) |
| **Product Specialist** | `gpt-5.2` | Searches products, compares prices, gets specifications | `search_products`, `get_product_details` |
| **Review Analyst** | `gpt-5.2` | Fetches and analyzes customer reviews | `search_products`, `get_product_reviews`, `analyze_sentiment` |

## Tools

### Product Specialist Tools

| Tool | API Endpoint | Description |
|------|--------------|-------------|
| `search_products` | `/search-v2` | Search for products with filters (price, condition, sort) |
| `get_product_details` | `/product-details-v2` | Get full specifications and offers for a product |

### Review Analyst Tools

| Tool | API Endpoint | Description |
|------|--------------|-------------|
| `search_products` | `/search-v2` | Find product to get valid `product_id` |
| `get_product_reviews` | `/product-reviews-v2` | Fetch customer reviews for a product |
| `analyze_sentiment` | Local | Analyze review text for sentiment, pros/cons, themes |

## Data Source

All product data is retrieved from the **Real-Time Product Search API** (via RapidAPI), which aggregates results from Google Shopping across multiple retailers including:

- Amazon
- Best Buy
- Walmart
- Target
- And 100+ more retailers

## Key Features

### Bidirectional Handoffs

Unlike simple one-way handoffs, this system uses **bidirectional handoffs** where:
1. Concierge can hand off to specialists
2. Specialists hand back to Concierge with results
3. Concierge synthesizes and presents to user

This pattern enables:
- ✅ Multi-step workflows (search → review → recommendation)
- ✅ Conversation context preservation
- ✅ Unified user experience through the Concierge

### Native SDK Handoffs

Uses the OpenAI Agents SDK's native `handoffs` parameter instead of custom routing logic:

```python
# Concierge can hand off to specialists
concierge = Agent(
    name="Concierge",
    handoffs=[product_specialist, review_analyst],
)

# Specialists hand back to Concierge
product_specialist.handoffs = [concierge]
review_analyst.handoffs = [concierge]
```

### Tracing Support

Full tracing integration with OpenAI's trace viewer:

```python
with trace("Shopping Assistant"):
    result = await Runner.run(
        starting_agent=concierge,
        input=user_query,
        run_config=run_config
    )
```

## Example Interactions

### Product Search
```
User: "Find me wireless headphones under $100 with noise cancellation"

→ Concierge → Product Specialist
  • search_products(query="wireless headphones noise cancellation", max_price=100)
→ Product Specialist → Concierge
→ User gets: Top 5 products with prices, ratings, and store links
```

### Review Analysis
```
User: "What do reviews say about the Sony WH-1000XM4?"

→ Concierge → Review Analyst
  • search_products(query="Sony WH-1000XM4") → gets product_id
  • get_product_reviews(product_id) → fetches reviews
  • analyze_sentiment(reviews) → extracts insights
→ Review Analyst → Concierge
→ User gets: Pros, cons, common themes, and recommendation
```

## Prerequisites

- Python 3.12+
- OpenAI API key (`OPENAI_API_KEY`)
- RapidAPI key (`RAPID_API_KEY`) with access to Real-Time Product Search API

## Setup

1. Ensure you have the virtual environment activated:
   ```bash
   source .venv/bin/activate
   ```

2. Create a `.env` file in the repo root with your API keys:
   ```
   OPENAI_API_KEY=your_openai_key
   RAPID_API_KEY=your_rapidapi_key
   ```

3. Open the notebook and run cells sequentially

## Notebook Structure

| Cell | Content |
|------|---------|
| 1 | Overview and architecture diagram |
| 2 | Concierge Agent low-level design |
| 3 | Product Specialist low-level design |
| 4 | Review Analyst low-level design |
| 5 | Environment variable loading |
| 6 | Product Specialist tools implementation |
| 7 | Product Specialist tools test |
| 8 | Review Analyst tools implementation |
| 9 | Review Analyst tools test |
| 10 | Agent definitions |
| 11 | Runner and tracing utilities |
| 12 | Test: Single query |
| 13 | Test: Multi-agent handoff |
| 14 | Test results summary |

## Lessons Learned

### Bidirectional Handoffs Require Same Provider

Native SDK handoffs between different providers (OpenAI ↔ Anthropic) fail due to conversation history ID format mismatches. All agents must use the same provider for bidirectional handoffs.

### API Parameter Validation

The Real-Time Product Search API v2 has strict parameter validation:
- `sort_by`: Only `BEST_MATCH`, `LOWEST_PRICE`, `HIGHEST_PRICE`, `TOP_RATED`
- `product_id`: Must be the exact ID from search results (format: `catalogid:...,gpcid:...`)

### Self-Sufficient Specialists

Adding `search_products` to the Review Analyst enables it to find products independently, rather than requiring a `product_id` from a prior Product Specialist search.

## Related Projects

- [Email Battle (OpenAI SDK)](../email_battle/) - Multi-agent adversarial simulation
- [Agentic Workflow Patterns](../../1-agentic-workflow/) - Design pattern comparisons

