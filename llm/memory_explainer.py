#!/usr/bin/env python3
"""
Memory Explainer — Full ReAct Loop with Memory Injected
=======================================================

This small explainer shows how the tiny Memory module can be composed with
the existing ReAct agent (via the Predictor abstraction).

What it demonstrates:
- Short-term memory (recent turns the agent itself maintains).
- Long-term memory (simple facts retrieved by keyword overlap).
- How retrieved memories are turned into prompt context.
- The effect on the prompt the tiny model sees (via extra_context).
- Actual tool calls (using the "direct action syntax" hack for demo purposes
  because the tiny model is still weak at format following).

Run from the project root (after you have a saved model from mini_react.py):

    python llm/memory_explainer.py
    python llm/memory_explainer.py --temp 0.8 --max-steps 5

Memory is injected cleanly using the `extra_context` parameter of `run_react`
(the recommended integration point).

The explainer keeps everything small and self-contained so you can see the
memory → prompt → ReAct loop clearly.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# Make sure we can import from the llm/ package when run from project root
_llm_dir = Path(__file__).resolve().parent
if str(_llm_dir) not in sys.path:
    sys.path.insert(0, str(_llm_dir))

from mini_react import (
    TOOLS,
    run_react,
    build_trained_model,
    load_model,
    save_model,
)
from tiny_predictor import from_tiny_llm
from memory import ShortTermMemory, LongTermMemory, format_memories


def main():
    parser = argparse.ArgumentParser(
        description="Memory demo: ReAct loop with short-term + long-term memory"
    )
    parser.add_argument(
        "--model-path", type=str, default="llm/tiny_model.pt",
        help="Path to saved model (created by mini_react.py)"
    )
    parser.add_argument(
        "--force-train", action="store_true",
        help="Force training even if model file exists"
    )
    parser.add_argument(
        "--max-steps", type=int, default=5,
        help="Maximum ReAct steps per goal"
    )
    parser.add_argument(
        "--temp", type=float, default=0.7,
        help="Sampling temperature for the predictor"
    )
    args = parser.parse_args()

    device = "cpu"  # keep deterministic for the demo

    # --- Load or train the tiny brain (same as everywhere else) ---
    if os.path.exists(args.model_path) and not args.force_train:
        model = load_model(args.model_path, device=device)
    else:
        model = build_trained_model(epochs=12, device=device)
        save_model(model, args.model_path)

    predictor = from_tiny_llm(model, temperature=args.temp, device=device)

    # --- Set up memory (this is the new part) ---
    stm = ShortTermMemory(window=6)           # short-term: last few turns
    ltm = LongTermMemory()                    # long-term: story facts

    # Seed long-term memory with the same world the tiny LLM was trained on.
    # In a real system this could come from a vector DB, user profile, etc.
    ltm.add_facts([
        "The glowing crystals come from the forest.",
        "Elara built the machine after lightning struck her workshop.",
        "The machine whispers secrets of the universe.",
        "Elara wants to talk to the stars.",
        "The village lies between mountains and a sparkling river.",
    ])

    print("=" * 70)
    print("MEMORY RUN THE PROTOTYPE — ReAct with Short-Term + Long-Term Memory")
    print("=" * 70)
    print(f"Model: {args.model_path}")
    print(f"Temperature: {args.temp}")
    print(f"Max steps per goal: {args.max_steps}")
    print()
    print("Long-term memory facts loaded:")
    for f in ltm.all_facts():
        print(f"  - {f}")
    print()

    # A couple of goals that benefit from memory.
    # We use the "direct action syntax" so tools actually fire (the tiny
    # model still struggles to produce clean Action lines on its own).
    goals = [
        "lookup[crystals]",           # should retrieve the forest fact
        "What powers the machine?",   # natural language — memory helps here too
    ]

    for i, goal in enumerate(goals, 1):
        print(f"\n{'='*70}")
        print(f"GOAL {i}: {goal}")
        print(f"{'='*70}")

        # --- Build memory context for this goal ---
        # Short-term is still empty for the first goal (we'll add turns after).
        # Long-term retrieval uses the current goal + any prior turns.
        context_for_retrieval = stm.get() + [f"User: {goal}"]
        relevant_facts = ltm.retrieve(context_for_retrieval, k=3)
        memory_block = format_memories(stm.get(), relevant_facts)

        if memory_block:
            print("\n[MEMORY] Injected into prompt:")
            print(memory_block)
            print()

        # --- Run the ReAct loop with memory injected ---
        # We pass the memory block via the extra_context parameter that was
        # added to build_prompt. The rest of the ReAct machinery is unchanged.
        final = run_react(
            question=goal,
            predictor=predictor,
            tools=TOOLS,
            max_steps=args.max_steps,
            verbose=True,   # show the full [AGENT]/[MODEL] trace
            extra_context=memory_block,   # clean way to inject memory
        )

        # After the run, "remember" what happened for the next goal.
        # In a real agent you would append the user turn + the agent's final response.
        stm.add(f"User: {goal}")
        stm.add(f"Agent: {final}")

        print(f"\n[RESULT] Final answer: {final}")
        print()

    print("=" * 70)
    print("WHAT YOU JUST SAW")
    print("=" * 70)
    print("""
1. Short-term memory (the agent's recent turns) was maintained across goals
   and injected into later prompts.

2. Long-term memory (story facts) was queried with simple keyword overlap.
   Relevant facts were pulled in and formatted cleanly.

3. The memory block was passed as extra_context to build_prompt, so it
   appeared in the exact place the tiny model could see it — right before
   the final "Thought:" hand-off.

4. Tool calls still worked (via the action-syntax forcing we added for
   demo purposes) even while memory was active.

5. The tiny model itself is still weak at format following, but the
   *architecture* (separate memory module + prompt injection) is now visible
   and reusable.

Try these experiments:
- Change the long-term facts and re-run.
- Increase short-term window size.
- Use a natural-language goal that would benefit from the retrieved facts.
- Turn verbose off in a real agent and just look at the final answers.

This is the same fundamental idea that production agents use (RAG, memory
stores, context compression) — just small enough to hold in your head.
""")
    print("=" * 70)


if __name__ == "__main__":
    main()
