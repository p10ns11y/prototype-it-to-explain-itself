#!/usr/bin/env python3
"""
Tiny Predictor — The Narrow Waist for All Future Agents
=======================================================

This tiny module defines the simplest possible contract:

    predictor(prompt: str, max_new_tokens: int | None = None) -> str

Everything above the predictor (ReAct loops, memory, evaluators, multi-agent
systems, reliability labs...) only ever talks to this interface.

Why it exists:
- The original simple_llm_prototype.py stays a pure "next-token predictor"
  teaching tool. It is not extended or bloated.
- Higher concepts plug in by importing a Predictor factory.
- The seam is explicit: swapping the brain (our TinyLLM today → Ollama,
  llama.cpp, a Rust inference server, MLX, a real API...) only requires a
  different factory. The agent logic stays identical.

This is the first deliberate step toward polyglot prototypes. A Rust,
TypeScript, or Go implementation can satisfy the exact same callable
contract and be used by the same (or equivalent) agent code.

Read every line. The whole file is the teaching.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Callable, Optional

# Support being imported when the user runs from the project root:
#   python llm/mini_react.py
# or directly from inside llm/.
_llm_dir = Path(__file__).resolve().parent
if str(_llm_dir) not in sys.path:
    sys.path.insert(0, str(_llm_dir))

# A Predictor is just "give me text, I give you more text".
# We type it for clarity, but any callable with this shape works.
Predictor = Callable[[str, Optional[int]], str]


def from_tiny_llm(
    model,
    temperature: float = 0.8,
    device: str = "cpu",
    default_max_new: int = 80,
) -> Predictor:
    """
    Wrap our existing TinyLLM + generate_text into a Predictor.

    The returned callable is what ReAct (and every later prototype) will use.
    It deliberately hides all the tokenization, hidden-state, and sampling
    details that live in simple_llm_prototype.py.
    """
    # Local import: the dependency is clear, and we only pay for it when
    # someone actually wants a TinyLLM-backed predictor.
    # The bootstrap above already put the llm/ dir on sys.path, so this works
    # whether the caller was run from the project root or from inside llm/.
    from simple_llm_prototype import generate_text as _generate_text

    def predict(prompt: str, max_new_tokens: Optional[int] = None) -> str:
        n = max_new_tokens if max_new_tokens is not None else default_max_new
        return _generate_text(
            model,
            seed_text=prompt,
            max_new_tokens=n,
            temperature=temperature,
            device=device,
        )

    # Helpful for debugging / trace printing
    predict.__name__ = "tiny_llm_predictor"
    predict.__doc__ = "TinyLLM-backed predictor (temperature, device closed over)."
    return predict


# ------------------------------------------------------------------
# Future adapter sketch (comment only — keeps this file tiny)
#
# def from_ollama(model: str = "llama3.2", temperature: float = 0.7) -> Predictor:
#     """Example of what a completely different backend looks like."""
#     import requests
#
#     def predict(prompt: str, max_new_tokens: Optional[int] = None) -> str:
#         # ... call Ollama HTTP API ...
#         return response_text
#
#     return predict
#
# The ReAct loop never changes. Only the factory call site changes.
# This is how we will keep prototypes small while going polyglot.
# ------------------------------------------------------------------