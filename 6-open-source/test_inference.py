#!/usr/bin/env python3
"""
Test script for vLLM OpenAI-compatible API server.
Demonstrates single and concurrent multi-inference requests.
"""

import asyncio
import time
from typing import Optional

import httpx
from openai import OpenAI, AsyncOpenAI


# Configuration
VLLM_BASE_URL = "http://localhost:8000/v1"
VLLM_API_KEY = "EMPTY"  # vLLM uses "EMPTY" as default when no key is set


def get_client(api_key: Optional[str] = None) -> OpenAI:
    """Create a synchronous OpenAI client for vLLM."""
    return OpenAI(
        base_url=VLLM_BASE_URL,
        api_key=api_key or VLLM_API_KEY,
    )


def get_async_client(api_key: Optional[str] = None) -> AsyncOpenAI:
    """Create an async OpenAI client for vLLM."""
    return AsyncOpenAI(
        base_url=VLLM_BASE_URL,
        api_key=api_key or VLLM_API_KEY,
    )


def check_server_health() -> bool:
    """Check if vLLM server is running."""
    try:
        response = httpx.get(f"{VLLM_BASE_URL.replace('/v1', '')}/health", timeout=5)
        return response.status_code == 200
    except Exception:
        return False


def list_models() -> list[str]:
    """List available models on the server."""
    client = get_client()
    models = client.models.list()
    return [model.id for model in models.data]


def single_inference(prompt: str, max_tokens: int = 100) -> str:
    """Run a single inference request."""
    client = get_client()
    
    response = client.chat.completions.create(
        model=list_models()[0],  # Use first available model
        messages=[
            {"role": "user", "content": prompt}
        ],
        max_tokens=max_tokens,
        temperature=0.7,
    )
    
    return response.choices[0].message.content


async def async_inference(
    client: AsyncOpenAI,
    model: str,
    prompt: str,
    request_id: int,
    max_tokens: int = 100
) -> tuple[int, str, float]:
    """Run an async inference request."""
    start_time = time.time()
    
    response = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "user", "content": prompt}
        ],
        max_tokens=max_tokens,
        temperature=0.7,
    )
    
    elapsed = time.time() - start_time
    content = response.choices[0].message.content
    
    return request_id, content, elapsed


async def concurrent_inference(prompts: list[str], max_tokens: int = 100) -> list[tuple[int, str, float]]:
    """Run multiple inference requests concurrently."""
    client = get_async_client()
    model = list_models()[0]
    
    tasks = [
        async_inference(client, model, prompt, i, max_tokens)
        for i, prompt in enumerate(prompts)
    ]
    
    results = await asyncio.gather(*tasks)
    return results


def demo_single_inference():
    """Demonstrate single inference."""
    print("\n" + "=" * 60)
    print("SINGLE INFERENCE TEST")
    print("=" * 60)
    
    prompt = "Explain quantum computing in one sentence."
    print(f"\nPrompt: {prompt}")
    
    start_time = time.time()
    response = single_inference(prompt)
    elapsed = time.time() - start_time
    
    print(f"\nResponse: {response}")
    print(f"\nTime: {elapsed:.2f}s")


def demo_concurrent_inference():
    """Demonstrate concurrent multi-inference."""
    print("\n" + "=" * 60)
    print("CONCURRENT MULTI-INFERENCE TEST")
    print("=" * 60)
    
    prompts = [
        "What is machine learning? (1 sentence)",
        "Explain neural networks briefly.",
        "What is natural language processing?",
        "Define deep learning in simple terms.",
        "What is reinforcement learning?",
    ]
    
    print(f"\nSending {len(prompts)} concurrent requests...")
    
    start_time = time.time()
    results = asyncio.run(concurrent_inference(prompts))
    total_elapsed = time.time() - start_time
    
    print("\nResults:")
    print("-" * 60)
    
    for request_id, content, elapsed in sorted(results):
        print(f"\n[Request {request_id}] ({elapsed:.2f}s)")
        print(f"Prompt: {prompts[request_id]}")
        print(f"Response: {content[:200]}..." if len(content) > 200 else f"Response: {content}")
    
    print("\n" + "-" * 60)
    print(f"Total time for {len(prompts)} concurrent requests: {total_elapsed:.2f}s")
    print(f"Average time per request: {total_elapsed / len(prompts):.2f}s")
    
    # Compare with sequential estimate
    individual_times = [elapsed for _, _, elapsed in results]
    sequential_estimate = sum(individual_times)
    speedup = sequential_estimate / total_elapsed
    
    print(f"\nSequential estimate: {sequential_estimate:.2f}s")
    print(f"Speedup from batching: {speedup:.2f}x")


def demo_streaming():
    """Demonstrate streaming inference."""
    print("\n" + "=" * 60)
    print("STREAMING INFERENCE TEST")
    print("=" * 60)
    
    client = get_client()
    model = list_models()[0]
    prompt = "Write a haiku about artificial intelligence."
    
    print(f"\nPrompt: {prompt}")
    print("\nStreaming response: ", end="", flush=True)
    
    stream = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "user", "content": prompt}
        ],
        max_tokens=100,
        temperature=0.7,
        stream=True,
    )
    
    for chunk in stream:
        if chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end="", flush=True)
    
    print("\n")


def main():
    """Main entry point."""
    print("=" * 60)
    print("vLLM Multi-Inference Test Suite")
    print("=" * 60)
    
    # Check server health
    print("\nChecking vLLM server health...")
    if not check_server_health():
        print("❌ vLLM server is not running!")
        print("\nStart the server first:")
        print("  VLLM_MODEL='your-model' ./start_server.sh")
        return
    
    print("✅ vLLM server is running")
    
    # List models
    models = list_models()
    print(f"✅ Available models: {models}")
    
    # Run tests
    demo_single_inference()
    demo_concurrent_inference()
    demo_streaming()
    
    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
