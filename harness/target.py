"""
Wraps calls to the TARGET model - the model you are testing/red-teaming.

Keep this separate from judge.py so the target and the judge can be
different models (recommended - grading your own model's homework with
itself is a weaker signal).
"""

import os
import time

from anthropic import Anthropic

_client = None


def _get_client() -> Anthropic:
    global _client
    if _client is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not set. Copy .env.example to .env and add your key."
            )
        _client = Anthropic(api_key=api_key)
    return _client


def call_target_model(prompt: str, model: str, max_tokens: int = 1024) -> tuple[str, int]:
    """
    Sends a single prompt to the target model.
    Returns (response_text, latency_ms).
    """
    client = _get_client()
    start = time.time()

    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )

    latency_ms = int((time.time() - start) * 1000)
    text = "".join(block.text for block in response.content if block.type == "text")
    return text, latency_ms
