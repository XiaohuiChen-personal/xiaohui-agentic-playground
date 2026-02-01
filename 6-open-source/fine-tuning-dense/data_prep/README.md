# AG News Data Preparation

This package converts the AG News dataset to the chat messages format for fine-tuning instruction-tuned models.

## Output Format

Each example is converted to a conversation with system, user, and assistant messages:

```json
{
    "messages": [
        {
            "role": "system",
            "content": "You are a news article classifier..."
        },
        {
            "role": "user",
            "content": "Classify the following news article:\n\nWall St. Bears Claw Back Into the Black (Reuters)..."
        },
        {
            "role": "assistant",
            "content": "{\"category\": \"Business\"}"
        }
    ]
}
```

## Usage

### Convert Full Training Set (120K samples)

```bash
cd data_prep
python convert_dataset.py
```

Output: `../datasets/train.jsonl` (~85 MB)

### Convert Subset for Quick Experiments

```bash
# 10K samples (~7 MB)
python convert_dataset.py --subset 10000

# 1K samples (~700 KB)
python convert_dataset.py --subset 1000
```

### Convert Test Set

```bash
python convert_dataset.py --split test
```

### Custom Output Path

```bash
python convert_dataset.py --output /path/to/custom.jsonl
```

### View Statistics Only

```bash
python convert_dataset.py --stats-only --output ../datasets/train.jsonl
```

## Files

- `config.py` - Prompts, schemas, and constants (shared with evaluation)
- `convert_dataset.py` - Main conversion script
- `__init__.py` - Package exports

## Configuration

The prompts and schema in `config.py` match those used in:
- Base model evaluation (`base_model_performance.ipynb`)
- Fine-tuned model evaluation (future)

This ensures consistency between training and inference.

## Output Statistics

Full training set conversion produces:
- 120,000 examples
- ~85 MB file size
- Balanced classes (30K per category)
- ~70 tokens per example (user + assistant)
