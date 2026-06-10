#!/usr/bin/env python3
"""
Tiny Memory for Agents
======================

A small, self-contained memory module designed to be plugged into the
ReAct-style agent (or any Predictor-based loop).

Core ideas (kept deliberately simple so the whole thing fits in one head):

- Short-term memory: recent turns in the current conversation (fixed-size window).
- Long-term memory: a flat list of facts. Retrieval is by simple keyword overlap
  (no external vector DB yet — keeps the prototype tiny and dependency-free).

The module returns plain text snippets that can be dropped into a prompt.

Usage example (with the ReAct agent):

    short_mem = ShortTermMemory(window=6)
    long_mem  = LongTermMemory()
    long_mem.add_fact("The glowing crystals come from the forest.")
    long_mem.add_fact("Elara built the machine after a lightning strike.")

    ...
    memories = long_mem.retrieve(recent_turns + [current_goal], k=3)
    memory_block = format_memories(short_mem.get(), memories)

    final = run_react(
        question=goal,
        predictor=predictor,
        tools=TOOLS,
        extra_context=memory_block,   # <-- clean injection point
    )
"""

from __future__ import annotations
from collections import deque
from typing import List, Deque, Iterable


class ShortTermMemory:
    """Sliding window of recent conversation turns.

    Each turn is a plain string (e.g. "User: hello" or "Agent: ...").
    Old turns are dropped once the window is full.
    """

    def __init__(self, window: int = 8):
        self.window = window
        self._turns: Deque[str] = deque(maxlen=window)

    def add(self, turn: str) -> None:
        """Add a new turn (e.g. a user message or agent response)."""
        self._turns.append(turn.strip())

    def get(self) -> List[str]:
        """Return the current window, oldest first."""
        return list(self._turns)

    def clear(self) -> None:
        self._turns.clear()

    def __len__(self) -> int:
        return len(self._turns)


class LongTermMemory:
    """Simple long-term fact store.

    Facts are just strings. Retrieval uses cheap keyword overlap scoring.
    Good enough to show the concept without pulling in chromadb / faiss.
    """

    def __init__(self):
        self._facts: List[str] = []

    def add_fact(self, fact: str) -> None:
        fact = fact.strip()
        if fact and fact not in self._facts:
            self._facts.append(fact)

    def add_facts(self, facts: Iterable[str]) -> None:
        for f in facts:
            self.add_fact(f)

    def retrieve(self, context: List[str], k: int = 3) -> List[str]:
        """Return up to k most relevant facts for the given context.

        Scoring is pure overlap of lowercase words (very naive, very small).
        """
        if not self._facts:
            return []

        # Build a bag of words from the recent context
        context_words = set()
        for turn in context:
            for w in turn.lower().split():
                # very light cleanup
                w = w.strip(".,!?;:\"'")
                if len(w) > 2:
                    context_words.add(w)

        scored = []
        for fact in self._facts:
            fact_words = set(fact.lower().split())
            score = len(context_words & fact_words)
            if score > 0:
                scored.append((score, fact))

        scored.sort(reverse=True)  # highest overlap first
        return [fact for _, fact in scored[:k]]

    def all_facts(self) -> List[str]:
        return list(self._facts)

    def clear(self) -> None:
        self._facts.clear()


def format_memories(short_term: List[str], long_term: List[str]) -> str:
    """Turn the two memory sources into a compact block for a prompt."""
    parts = []
    if short_term:
        parts.append("Recent conversation:")
        parts.extend(f"  - {t}" for t in short_term)
    if long_term:
        parts.append("Relevant facts from long-term memory:")
        parts.extend(f"  - {f}" for f in long_term)
    return "\n".join(parts) if parts else ""


# ------------------------------------------------------------------
# Tiny demo / self-test (run this file directly)
# ------------------------------------------------------------------
if __name__ == "__main__":
    print("=== Tiny Memory Demo ===\n")

    stm = ShortTermMemory(window=4)
    ltm = LongTermMemory()

    # Seed long-term memory with story facts (same world as the tiny LLM)
    ltm.add_facts([
        "The glowing crystals come from the forest.",
        "Elara built the machine after lightning struck her workshop.",
        "The machine whispers secrets of the universe.",
        "Elara wants to talk to the stars.",
    ])

    # Simulate a short conversation
    stm.add("User: Tell me about the crystals.")
    stm.add("Agent: They are strange and glowing.")
    stm.add("User: Where did Elara find them?")

    # Retrieve for a new question
    query_turns = stm.get() + ["User: What powers the machine?"]
    relevant = ltm.retrieve(query_turns, k=2)

    print("Short-term memory:")
    for t in stm.get():
        print(f"  {t}")
    print()

    print("Retrieved long-term facts:")
    for f in relevant:
        print(f"  - {f}")
    print()

    block = format_memories(stm.get(), relevant)
    print("Memory block ready for a prompt:")
    print(block)
    print()

    print("You can now pass this block into build_prompt(..., extra_context=block)")
    print("or inject it into the ReAct history so the tiny model sees it.")
