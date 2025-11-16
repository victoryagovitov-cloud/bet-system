#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import time
import statistics
from typing import List, Dict

try:
    import anthropic
except ImportError:
    raise SystemExit("anthropic package not installed. Install with: pip install anthropic>=0.35.0")


def run_single_request(client: anthropic.Client, model: str, prompt: str, max_tokens: int = 256) -> Dict[str, float]:
    """Run one request and measure timings.

    Returns dict with: total_s, first_token_s (approx), output_tokens, input_tokens
    """
    start = time.perf_counter()
    # Non-streamed request: total latency
    msg = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        temperature=0.2,
        system="You are a helpful, concise assistant.",
        messages=[{"role": "user", "content": prompt}],
    )
    end = time.perf_counter()

    # Approximate first token time = total when non-streaming (we'll add a streamed pass below if needed)
    total_s = end - start
    output_text = "".join([b.text for b in msg.content if getattr(b, "type", "") == "text"]) if hasattr(msg, "content") else ""

    input_tokens = getattr(msg.usage, "input_tokens", None) if hasattr(msg, "usage") else None
    output_tokens = getattr(msg.usage, "output_tokens", None) if hasattr(msg, "usage") else None

    return {
        "total_s": total_s,
        "first_token_s": total_s,  # non-stream approximation
        "input_tokens": float(input_tokens or 0),
        "output_tokens": float(output_tokens or 0),
        "chars": float(len(output_text)),
    }


def run_stream_request(client: anthropic.Client, model: str, prompt: str, max_tokens: int = 256) -> Dict[str, float]:
    """Run one streamed request and measure time-to-first-token and total."""
    start = time.perf_counter()
    first_token_s = None
    output_chars = 0

    with client.messages.stream(
        model=model,
        max_tokens=max_tokens,
        temperature=0.2,
        system="You are a helpful, concise assistant.",
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        for event in stream:
            # The first content delta marks first token
            if first_token_s is None and getattr(event, "type", "") in ("content_block_delta", "message_start"):
                first_token_s = time.perf_counter() - start
            if getattr(event, "type", "") == "content_block_delta":
                delta = getattr(event, "delta", None)
                if delta and getattr(delta, "type", "") == "text_delta":
                    output_chars += len(getattr(delta, "text", ""))
        msg = stream.get_final_message()

    end = time.perf_counter()
    total_s = end - start

    input_tokens = getattr(msg.usage, "input_tokens", None) if hasattr(msg, "usage") else None
    output_tokens = getattr(msg.usage, "output_tokens", None) if hasattr(msg, "usage") else None

    return {
        "total_s": total_s,
        "first_token_s": float(first_token_s or total_s),
        "input_tokens": float(input_tokens or 0),
        "output_tokens": float(output_tokens or 0),
        "chars": float(output_chars),
    }


def summarize(results: List[Dict[str, float]]) -> Dict[str, float]:
    def m(values):
        return statistics.mean(values) if values else 0.0

    return {
        "n": len(results),
        "avg_total_s": m([r["total_s"] for r in results]),
        "avg_first_token_s": m([r["first_token_s"] for r in results]),
        "avg_input_toks": m([r["input_tokens"] for r in results]),
        "avg_output_toks": m([r["output_tokens"] for r in results]),
        "avg_chars": m([r["chars"] for r in results]),
    }


def main():
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise SystemExit("Set ANTHROPIC_API_KEY env var before running.")

    client = anthropic.Client(api_key=api_key)

    # Default recommended model; adjust if needed
    model = os.getenv("ANTHROPIC_MODEL", "claude-3-7-sonnet-20250219")

    prompt = (
        "Коротко, в 1-2 предложениях: Сформулируй 3 разных причины, почему важно "
        "проверять live-матчи на Scores24 перед ставкой, с упором на xG."
    )

    runs = int(os.getenv("BENCH_RUNS", "3"))

    cold_non_stream: List[Dict[str, float]] = []
    cold_stream: List[Dict[str, float]] = []

    print(f"\n=== Anthropic benchmark ===\nModel: {model}\nRuns: {runs}")

    for i in range(runs):
        r1 = run_single_request(client, model, prompt)
        cold_non_stream.append(r1)
        print(f"Non-stream #{i+1}: total={r1['total_s']:.2f}s, out_toks={r1['output_tokens']:.0f}")

    for i in range(runs):
        r2 = run_stream_request(client, model, prompt)
        cold_stream.append(r2)
        print(
            f"Stream  #{i+1}: total={r2['total_s']:.2f}s, first_token={r2['first_token_s']:.2f}s, out_toks={r2['output_tokens']:.0f}"
        )

    s1 = summarize(cold_non_stream)
    s2 = summarize(cold_stream)

    print("\n--- Summary ---")
    print(
        f"Non-stream: n={s1['n']}, avg_total={s1['avg_total_s']:.2f}s, avg_out_toks={s1['avg_output_toks']:.0f}"
    )
    print(
        f"Stream:     n={s2['n']}, avg_total={s2['avg_total_s']:.2f}s, avg_first_token={s2['avg_first_token_s']:.2f}s, avg_out_toks={s2['avg_output_toks']:.0f}"
    )

    # Rough TPS (tokens per second) on output for stream
    if s2["avg_total_s"] > 0 and s2["avg_output_toks"] > 0:
        tps = s2["avg_output_toks"] / s2["avg_total_s"]
        print(f"Approx stream output speed: {tps:.1f} tok/s")


if __name__ == "__main__":
    main()


