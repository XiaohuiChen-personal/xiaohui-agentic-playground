"""
Data preparation utilities for AG News fine-tuning.

This package provides tools to convert the AG News dataset
to the chat messages format for fine-tuning.
"""

from .config import (
    NewsCategory,
    ClassificationResult,
    SYSTEM_PROMPT,
    create_user_prompt,
    LABEL_NAMES,
    LABEL_TO_CATEGORY,
    CATEGORY_TO_LABEL,
)

from .convert_dataset import (
    convert_example,
    convert_dataset,
    save_jsonl,
)

__all__ = [
    # Config
    "NewsCategory",
    "ClassificationResult",
    "SYSTEM_PROMPT",
    "create_user_prompt",
    "LABEL_NAMES",
    "LABEL_TO_CATEGORY",
    "CATEGORY_TO_LABEL",
    # Conversion
    "convert_example",
    "convert_dataset",
    "save_jsonl",
]
