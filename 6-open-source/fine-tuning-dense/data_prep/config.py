"""
Configuration constants for AG News classification fine-tuning.

These constants are used consistently across:
- Data preparation (converting to fine-tuning format)
- Base model evaluation
- Fine-tuned model evaluation
"""

from enum import Enum
from pydantic import BaseModel


# =============================================================================
# Output Schema (Pydantic)
# =============================================================================

class NewsCategory(str, Enum):
    """The four categories in AG News dataset."""
    world = "World"
    sports = "Sports"
    business = "Business"
    sci_tech = "Sci/Tech"


class ClassificationResult(BaseModel):
    """Expected output format for classification."""
    category: NewsCategory


# =============================================================================
# Label Mappings
# =============================================================================

# AG News dataset uses integer labels 0-3
LABEL_NAMES = {
    0: "World",
    1: "Sports",
    2: "Business",
    3: "Sci/Tech"
}

# Map integer labels to NewsCategory enum
LABEL_TO_CATEGORY = {
    0: NewsCategory.world,
    1: NewsCategory.sports,
    2: NewsCategory.business,
    3: NewsCategory.sci_tech
}

# Reverse mapping
CATEGORY_TO_LABEL = {v: k for k, v in LABEL_TO_CATEGORY.items()}


# =============================================================================
# Prompts
# =============================================================================

SYSTEM_PROMPT = """You are a news article classifier. Your task is to categorize news articles into exactly one of four categories:

- World: News about politics, government, elections, diplomacy, conflicts, and public affairs (domestic or international)
- Sports: News about athletic events, games, players, teams, coaches, tournaments, and championships
- Business: News about companies, markets, finance, economy, trade, corporate activities, and business services
- Sci/Tech: News about technology products, software, hardware, scientific research, gadgets, and tech innovations

Rules:
- Focus on the PRIMARY topic of the article
- Ignore HTML artifacts (like #39; or &lt;b&gt;) - they are formatting errors
- If an article is truncated, classify based on the available content
- When a topic spans multiple categories, choose the one that best represents the main focus"""


def create_user_prompt(article_text: str) -> str:
    """Create the user prompt for classification."""
    return f"Classify the following news article:\n\n{article_text}"


# =============================================================================
# Dataset Info
# =============================================================================

DATASET_NAME = "ag_news"
TRAIN_SIZE = 120000
TEST_SIZE = 7600
NUM_CLASSES = 4
