#!/usr/bin/env python3
"""
Fine-tuning template using Unsloth for efficient LLM training.
Supports LoRA/QLoRA fine-tuning with 2-4x speedup and 60% memory reduction.

Usage:
    uv run --extra finetune python finetune_template.py

Before running:
    1. Stop any running vLLM servers to free GPU memory
    2. Prepare your dataset (see examples below)
    3. Configure the settings in this file
"""

import os
from typing import Optional

# ============================================================================
# CONFIGURATION - Modify these settings for your use case
# ============================================================================

# Model to fine-tune (Unsloth optimized models recommended)
BASE_MODEL = "unsloth/Llama-3.2-3B-Instruct"  # Fast for testing
# BASE_MODEL = "unsloth/Llama-3.1-8B-Instruct"  # Good balance
# BASE_MODEL = "unsloth/Qwen2.5-7B-Instruct"    # Strong multilingual
# BASE_MODEL = "unsloth/Mistral-7B-Instruct-v0.3"  # Fast inference

# Output directory for fine-tuned model
OUTPUT_DIR = "./finetuned_models/my_model"

# Training settings
MAX_SEQ_LENGTH = 2048  # Reduce if OOM, increase for longer context
LOAD_IN_4BIT = True    # QLoRA (4-bit quantization) - saves memory

# LoRA settings
LORA_R = 16            # LoRA rank (higher = more capacity, more memory)
LORA_ALPHA = 16        # LoRA scaling
LORA_DROPOUT = 0.0     # Dropout (0 is fine for most cases)

# Training hyperparameters
BATCH_SIZE = 2              # Increase if you have memory headroom
GRADIENT_ACCUMULATION = 4   # Effective batch = BATCH_SIZE * GRADIENT_ACCUMULATION
LEARNING_RATE = 2e-4
NUM_EPOCHS = 3
WARMUP_STEPS = 5
WEIGHT_DECAY = 0.01

# Logging
USE_WANDB = False      # Set True and configure WANDB_API_KEY in .env
WANDB_PROJECT = "unsloth-finetune"

# ============================================================================
# DATASET PREPARATION
# ============================================================================

def prepare_dataset():
    """
    Prepare your training dataset.
    
    Unsloth expects data in chat format:
    [
        {"role": "user", "content": "..."},
        {"role": "assistant", "content": "..."}
    ]
    
    Or instruction format:
    {"instruction": "...", "input": "...", "output": "..."}
    """
    from datasets import load_dataset, Dataset
    
    # Example 1: Load from Hugging Face
    # dataset = load_dataset("yahma/alpaca-cleaned", split="train")
    
    # Example 2: Load from local JSON/JSONL
    # dataset = load_dataset("json", data_files="my_data.jsonl", split="train")
    
    # Example 3: Create from list
    data = [
        {
            "conversations": [
                {"role": "user", "content": "What is machine learning?"},
                {"role": "assistant", "content": "Machine learning is a subset of artificial intelligence..."}
            ]
        },
        {
            "conversations": [
                {"role": "user", "content": "Explain neural networks."},
                {"role": "assistant", "content": "Neural networks are computing systems inspired by biological neural networks..."}
            ]
        },
    ]
    dataset = Dataset.from_list(data)
    
    return dataset


def format_chat_template(examples, tokenizer):
    """Format examples using the model's chat template."""
    texts = []
    for convo in examples["conversations"]:
        text = tokenizer.apply_chat_template(
            convo,
            tokenize=False,
            add_generation_prompt=False
        )
        texts.append(text)
    return {"text": texts}


# ============================================================================
# MAIN TRAINING SCRIPT
# ============================================================================

def main():
    print("=" * 60)
    print("Unsloth Fine-Tuning")
    print("=" * 60)
    
    # Check GPU
    import torch
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA not available. Fine-tuning requires GPU.")
    
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")
    print()
    
    # Import Unsloth (must be after torch)
    from unsloth import FastLanguageModel
    from trl import SFTTrainer
    from transformers import TrainingArguments
    
    # Load model with Unsloth optimizations
    print(f"Loading model: {BASE_MODEL}")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=BASE_MODEL,
        max_seq_length=MAX_SEQ_LENGTH,
        load_in_4bit=LOAD_IN_4BIT,
        dtype=None,  # Auto-detect
    )
    
    # Add LoRA adapters
    print("Adding LoRA adapters...")
    model = FastLanguageModel.get_peft_model(
        model,
        r=LORA_R,
        lora_alpha=LORA_ALPHA,
        lora_dropout=LORA_DROPOUT,
        target_modules=[
            "q_proj", "k_proj", "v_proj", "o_proj",
            "gate_proj", "up_proj", "down_proj",
        ],
        bias="none",
        use_gradient_checkpointing="unsloth",  # Saves 30% memory
        random_state=42,
    )
    
    # Prepare dataset
    print("Preparing dataset...")
    dataset = prepare_dataset()
    dataset = dataset.map(
        lambda x: format_chat_template(x, tokenizer),
        batched=True,
    )
    
    print(f"Dataset size: {len(dataset)} examples")
    
    # Training arguments
    training_args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        per_device_train_batch_size=BATCH_SIZE,
        gradient_accumulation_steps=GRADIENT_ACCUMULATION,
        learning_rate=LEARNING_RATE,
        num_train_epochs=NUM_EPOCHS,
        warmup_steps=WARMUP_STEPS,
        weight_decay=WEIGHT_DECAY,
        logging_steps=10,
        save_steps=100,
        save_total_limit=3,
        bf16=True,  # Use bfloat16 on modern GPUs
        optim="adamw_8bit",  # Memory-efficient optimizer
        seed=42,
        report_to="wandb" if USE_WANDB else "none",
    )
    
    # Create trainer
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        dataset_text_field="text",
        max_seq_length=MAX_SEQ_LENGTH,
        args=training_args,
    )
    
    # Train
    print("\nStarting training...")
    print(f"Effective batch size: {BATCH_SIZE * GRADIENT_ACCUMULATION}")
    print(f"Total steps: {len(dataset) // (BATCH_SIZE * GRADIENT_ACCUMULATION) * NUM_EPOCHS}")
    print()
    
    trainer.train()
    
    # Save model
    print(f"\nSaving model to {OUTPUT_DIR}")
    model.save_pretrained(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)
    
    # Optional: Save merged model (LoRA merged into base)
    # This creates a standalone model that doesn't need the base model
    print(f"Saving merged model to {OUTPUT_DIR}_merged")
    model.save_pretrained_merged(
        f"{OUTPUT_DIR}_merged",
        tokenizer,
        save_method="merged_16bit",  # or "merged_4bit" for quantized
    )
    
    print("\n" + "=" * 60)
    print("Fine-tuning complete!")
    print("=" * 60)
    print(f"\nLoRA adapter saved to: {OUTPUT_DIR}")
    print(f"Merged model saved to: {OUTPUT_DIR}_merged")
    print("\nTo serve with vLLM:")
    print(f"  VLLM_MODEL='{OUTPUT_DIR}_merged' ./start_server.sh")


if __name__ == "__main__":
    main()
