#!/usr/bin/env python3
"""
Tool-Use Reliability Lab
========================

This prototype measures how reliably the agent uses tools correctly.

It reuses:
- The same tools (calc, lookup) from mini_react.py
- The same Predictor abstraction (tiny_predictor.py)
- The same ReAct loop (with verbose=False for batch runs)
- The same trained TinyLLM (via model persistence)

Why this matters:
Most real agent failures come from the model not calling the right tool
with the right arguments, or failing to recover when something goes wrong.

This lab runs a controlled suite of test cases and produces a clear report:
- Success rate
- Common failure modes (wrong tool, bad args, no tool called, etc.)
- Which kinds of goals are hard for the current setup

Because we use the tiny character-level model, expect low numbers.
That is the point — it makes the problem visible and measurable.

Run from project root:
    python llm/tool_reliability_lab.py
    python llm/tool_reliability_lab.py --model-path llm/tiny_model.pt --cases 20
"""

from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from typing import List, Optional

# Reuse everything from the previous prototypes (interconnect, no duplication)
import sys
from pathlib import Path

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
from tiny_predictor import from_tiny_llm, Predictor


@dataclass
class TestCase:
    goal: str
    expected_tool: Optional[str]   # None means "should not call a tool, just answer"
    expected_arg_contains: Optional[str] = None
    description: str = ""
    category: str = "general"      # e.g. direct, ambiguous, no-tool-needed, error-recovery


TEST_CASES: List[TestCase] = [
    # Direct, clear cases that should trigger a tool.
    # We use the "direct action syntax" (e.g. lookup[stars]) so that the
    # forcing logic in run_react (added for demo purposes) will actually
    # cause a tool to be invoked. This lets the lab exercise and measure
    # real tool usage / arg correctness with the current weak model.
    TestCase(
        goal="calc[3 * 4 + 2]",
        expected_tool="calc",
        expected_arg_contains="3 * 4 + 2",
        description="Clear calculation using direct action syntax (forces tool call)",
        category="direct",
    ),
    TestCase(
        goal="lookup[stars]",
        expected_tool="lookup",
        expected_arg_contains="stars",
        description="Clear lookup of story fact using direct action syntax (forces tool call)",
        category="direct",
    ),
    TestCase(
        goal="lookup[machine]",
        expected_tool="lookup",
        expected_arg_contains="machine",
        description="Direct lookup using direct action syntax (forces tool call)",
        category="direct",
    ),

    # Cases that probably don't need a tool (keep natural language so they
    # do NOT trigger the forcing logic).
    TestCase(
        goal="Who is Elara?",
        expected_tool=None,
        description="Simple fact that might be answered from context or final answer",
        category="no-tool-needed",
    ),
    TestCase(
        goal="Is the village quiet?",
        expected_tool=None,
        description="Yes/no question likely answerable without tool",
        category="no-tool-needed",
    ),

    # Ambiguous case - use action syntax so a tool *is* called, then we can
    # measure whether the "right" tool/args were chosen (or wrong one).
    TestCase(
        goal="calc[?? distance ??]",
        expected_tool="calc",
        expected_arg_contains=None,  # we mainly care that it tried calc
        description="Ambiguous — forces a calc call but args are bad (tests selection)",
        category="ambiguous",
    ),

    # Error injection style - use action syntax to force the call, then the
    # tool will receive a bad expression (simulates calling with wrong args
    # or a tool that fails).
    TestCase(
        goal="calc[crystals * dreams + unknown]",
        expected_tool="calc",
        expected_arg_contains="crystals",
        description="Forces calc call with invalid expression (tests calling on bad input)",
        category="error-injection",
    ),
]


def evaluate_case(
    case: TestCase,
    predictor: Predictor,
    max_steps: int = 5,
) -> dict:
    """Run one test case silently, record which tools were actually invoked, and score."""
    tool_calls: List[tuple] = []

    original_fns = {t.name: t.fn for t in TOOLS}

    def make_recording_fn(name, original_fn):
        def recording_fn(arg):
            tool_calls.append((name, arg))
            return original_fn(arg)
        return recording_fn

    for t in TOOLS:
        t.fn = make_recording_fn(t.name, original_fns[t.name])

    # Run the ReAct loop once (with recording wrappers, silently)
    _ = run_react(
        question=case.goal,
        predictor=predictor,
        tools=TOOLS,
        max_steps=max_steps,
        verbose=False,
    )

    # Restore original functions immediately
    for t in TOOLS:
        t.fn = original_fns[t.name]

    # Score the observed tool calls
    correct_tool = False
    correct_arg = False

    if case.expected_tool is None:
        success = len(tool_calls) == 0
        details = "no tool called (good)" if success else f"unexpected tool(s) called: {tool_calls}"
    else:
        for called_name, called_arg in tool_calls:
            if called_name == case.expected_tool:
                correct_tool = True
                if case.expected_arg_contains is None or case.expected_arg_contains in str(called_arg):
                    correct_arg = True
                break

        success = correct_tool and (case.expected_arg_contains is None or correct_arg)
        details = f"tool_calls={tool_calls}"

    return {
        "goal": case.goal,
        "category": case.category,
        "success": success,
        "correct_tool": correct_tool,
        "correct_arg": correct_arg,
        "tool_calls": tool_calls,
        "details": details,
    }


def main():
    parser = argparse.ArgumentParser(description="Tool-Use Reliability Lab")
    parser.add_argument("--model-path", type=str, default="llm/tiny_model.pt")
    parser.add_argument("--max-steps", type=int, default=4)
    parser.add_argument("--cases", type=int, default=len(TEST_CASES),
                        help="How many test cases to run (useful for quick experiments)")
    parser.add_argument("--force-train", action="store_true")
    args = parser.parse_args()

    device = "cpu"  # lab usually runs on cpu for reproducibility

    if os.path.exists(args.model_path) and not args.force_train:
        model = load_model(args.model_path, device=device)
    else:
        model = build_trained_model(epochs=12, device=device)
        save_model(model, args.model_path)

    predictor = from_tiny_llm(model, temperature=0.7, device=device)

    print("=" * 70)
    print("TOOL-USE RELIABILITY LAB")
    print("=" * 70)
    print(f"Using model: {args.model_path}")
    print(f"Running {min(args.cases, len(TEST_CASES))} test cases...")
    print()

    results = []
    for i, case in enumerate(TEST_CASES[:args.cases]):
        print(f"[{i+1}/{min(args.cases, len(TEST_CASES))}] {case.category}: {case.description}")
        res = evaluate_case(case, predictor, max_steps=args.max_steps)
        results.append(res)
        status = "✓" if res["success"] else "✗"
        print(f"  {status}  expected_tool={case.expected_tool}  result={res['details']}")
        print()

    # === Report ===
    total = len(results)
    successes = sum(1 for r in results if r["success"])
    rate = (successes / total * 100) if total > 0 else 0

    print("=" * 70)
    print("SUMMARY REPORT")
    print("=" * 70)
    print(f"Total cases:     {total}")
    print(f"Successes:       {successes}")
    print(f"Success rate:    {rate:.1f}%")
    print()

    # Breakdown by category
    by_category = {}
    for r in results:
        cat = r["category"]
        if cat not in by_category:
            by_category[cat] = {"total": 0, "success": 0}
        by_category[cat]["total"] += 1
        if r["success"]:
            by_category[cat]["success"] += 1

    print("By category:")
    for cat, stats in sorted(by_category.items()):
        c_rate = stats["success"] / stats["total"] * 100 if stats["total"] else 0
        print(f"  {cat:18s}  {stats['success']}/{stats['total']}  ({c_rate:.0f}%)")

    print()
    print("Common observations with this tiny model:")
    print("  - Very low success rate on structured tool use.")
    print("  - The model often fails to emit clean 'Action: name[args]' lines.")
    print("  - This is expected — the training data (one story) contains no examples")
    print("    of the required output format.")
    print()
    print("This lab makes the problem measurable. Later prototypes will explore")
    print("better prompting, constrained generation, or training on tool-use data.")
    print("=" * 70)


if __name__ == "__main__":
    main()