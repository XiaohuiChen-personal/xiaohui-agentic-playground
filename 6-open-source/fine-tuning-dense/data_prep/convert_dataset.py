#!/usr/bin/env python3
"""
Convert AG News dataset to fine-tuning format.

This script converts the AG News training data to the chat messages format
suitable for fine-tuning instruction-tuned models like Qwen2.5-7B.

Output format (JSONL):
{
    "messages": [
        {"role": "system", "content": "<system prompt>"},
        {"role": "user", "content": "Classify the following news article:\n\n<article>"},
        {"role": "assistant", "content": '{"category": "Business"}'}
    ]
}

Usage:
    python convert_dataset.py                    # Convert full dataset
    python convert_dataset.py --subset 10000    # Convert 10K samples
    python convert_dataset.py --help            # Show help
"""

import argparse
import json
import random
from pathlib import Path
from typing import Iterator

from datasets import load_dataset
from tqdm import tqdm

from config import (
    SYSTEM_PROMPT,
    create_user_prompt,
    LABEL_TO_CATEGORY,
    ClassificationResult,
    LABEL_NAMES,
)


def convert_example(example: dict) -> dict:
    """
    Convert a single AG News example to chat messages format.
    
    Args:
        example: Dict with 'text' and 'label' keys from AG News dataset
        
    Returns:
        Dict with 'messages' key containing the conversation
    """
    # Get the category from the label
    category = LABEL_TO_CATEGORY[example["label"]]
    
    # Create the expected output
    output = ClassificationResult(category=category)
    
    return {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": create_user_prompt(example["text"])},
            {"role": "assistant", "content": output.model_dump_json()}
        ]
    }


def convert_dataset(
    split: str = "train",
    subset_size: int | None = None,
    seed: int = 42,
    shuffle: bool = True
) -> Iterator[dict]:
    """
    Convert AG News dataset split to fine-tuning format.
    
    Args:
        split: Dataset split ('train' or 'test')
        subset_size: If set, only convert this many samples
        seed: Random seed for shuffling
        shuffle: Whether to shuffle before subsetting
        
    Yields:
        Converted examples in chat messages format
    """
    print(f"Loading AG News dataset ({split} split)...")
    dataset = load_dataset("ag_news", split=split)
    
    # Convert to list for shuffling/subsetting
    data = list(dataset)
    
    if shuffle:
        random.seed(seed)
        random.shuffle(data)
    
    if subset_size:
        data = data[:subset_size]
        print(f"Using subset of {subset_size:,} samples")
    else:
        print(f"Converting all {len(data):,} samples")
    
    for example in data:
        yield convert_example(example)


def save_jsonl(data: Iterator[dict], output_path: Path, total: int | None = None):
    """
    Save data to JSONL file with progress bar.
    
    Args:
        data: Iterator of examples to save
        output_path: Path to output file
        total: Total count for progress bar (optional)
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for example in tqdm(data, total=total, desc=f"Writing {output_path.name}"):
            f.write(json.dumps(example, ensure_ascii=False) + '\n')
    
    print(f"✓ Saved to {output_path}")


def get_dataset_stats(path: Path) -> dict:
    """Get statistics from a JSONL dataset file."""
    stats = {
        "total_examples": 0,
        "category_counts": {name: 0 for name in LABEL_NAMES.values()},
        "avg_user_tokens": 0,
        "avg_assistant_tokens": 0,
    }
    
    total_user_chars = 0
    total_assistant_chars = 0
    
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            example = json.loads(line)
            stats["total_examples"] += 1
            
            # Count categories
            assistant_content = example["messages"][2]["content"]
            result = json.loads(assistant_content)
            category = result["category"]
            stats["category_counts"][category] += 1
            
            # Estimate token counts (rough: ~4 chars per token)
            user_content = example["messages"][1]["content"]
            total_user_chars += len(user_content)
            total_assistant_chars += len(assistant_content)
    
    if stats["total_examples"] > 0:
        stats["avg_user_tokens"] = int(total_user_chars / stats["total_examples"] / 4)
        stats["avg_assistant_tokens"] = int(total_assistant_chars / stats["total_examples"] / 4)
    
    return stats


def print_stats(stats: dict):
    """Print dataset statistics."""
    print("\n" + "=" * 60)
    print("DATASET STATISTICS")
    print("=" * 60)
    print(f"\nTotal examples: {stats['total_examples']:,}")
    print(f"\nCategory distribution:")
    for category, count in stats["category_counts"].items():
        pct = count / stats["total_examples"] * 100 if stats["total_examples"] > 0 else 0
        print(f"  {category:<12}: {count:>6,} ({pct:>5.1f}%)")
    print(f"\nEstimated tokens per example:")
    print(f"  User message:      ~{stats['avg_user_tokens']} tokens")
    print(f"  Assistant message: ~{stats['avg_assistant_tokens']} tokens")
    print(f"  Total per example: ~{stats['avg_user_tokens'] + stats['avg_assistant_tokens'] + 50} tokens (incl. system)")


def main():
    parser = argparse.ArgumentParser(
        description="Convert AG News dataset to fine-tuning format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python convert_dataset.py                     # Full training set (120K)
  python convert_dataset.py --subset 10000      # 10K samples for quick experiments
  python convert_dataset.py --subset 1000       # 1K samples for testing
  python convert_dataset.py --output custom.jsonl  # Custom output path
        """
    )
    parser.add_argument(
        "--subset", 
        type=int, 
        default=None,
        help="Number of samples to convert (default: all)"
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default=None,
        help="Output file path (default: ../datasets/train.jsonl or train_<N>.jsonl)"
    )
    parser.add_argument(
        "--seed", 
        type=int, 
        default=42,
        help="Random seed for shuffling (default: 42)"
    )
    parser.add_argument(
        "--no-shuffle", 
        action="store_true",
        help="Don't shuffle the dataset"
    )
    parser.add_argument(
        "--split",
        type=str,
        default="train",
        choices=["train", "test"],
        help="Dataset split to convert (default: train)"
    )
    parser.add_argument(
        "--stats-only",
        action="store_true",
        help="Only show statistics for existing output file"
    )
    
    args = parser.parse_args()
    
    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        datasets_dir = Path(__file__).parent.parent / "datasets"
        if args.subset:
            output_path = datasets_dir / f"{args.split}_{args.subset}.jsonl"
        else:
            output_path = datasets_dir / f"{args.split}.jsonl"
    
    # Stats only mode
    if args.stats_only:
        if not output_path.exists():
            print(f"Error: File not found: {output_path}")
            return
        stats = get_dataset_stats(output_path)
        print_stats(stats)
        return
    
    # Convert dataset
    print("=" * 60)
    print("AG NEWS DATASET CONVERSION")
    print("=" * 60)
    print(f"\nSplit: {args.split}")
    print(f"Subset: {args.subset if args.subset else 'Full dataset'}")
    print(f"Output: {output_path}")
    print(f"Seed: {args.seed}")
    print(f"Shuffle: {not args.no_shuffle}")
    
    # Determine total for progress bar
    if args.split == "train":
        total = args.subset if args.subset else 120000
    else:
        total = args.subset if args.subset else 7600
    
    # Convert and save
    data = convert_dataset(
        split=args.split,
        subset_size=args.subset,
        seed=args.seed,
        shuffle=not args.no_shuffle
    )
    save_jsonl(data, output_path, total=total)
    
    # Show statistics
    stats = get_dataset_stats(output_path)
    print_stats(stats)
    
    print("\n" + "=" * 60)
    print("CONVERSION COMPLETE")
    print("=" * 60)
    print(f"\n✓ Output file: {output_path}")
    print(f"✓ File size: {output_path.stat().st_size / 1024 / 1024:.1f} MB")


if __name__ == "__main__":
    main()
