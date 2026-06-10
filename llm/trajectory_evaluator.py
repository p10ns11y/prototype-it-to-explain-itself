#!/usr/bin/env python3
"""
Agent Trajectory Evaluator
==========================

Prototype 4: Turn the ReAct agent into something we can measure and iterate on.

This prototype reuses:
- The exact same tools (calc, lookup) from mini_react.py
- The Predictor abstraction (tiny_predictor.py)
- The ReAct control loop via run_react(..., verbose=False, return_trajectory=True)
- The same persisted TinyLLM (fast after first train)

What it does:
- Defines a small benchmark suite of goals (some need tools, some don't, some ambiguous).
- Runs the agent on each (silently, multiple times if you want variance).
- Scores every trajectory on three axes:
  1. Outcome: did we get a usable Final Answer that satisfies simple success criteria?
  2. Process: steps taken, number of tool calls (efficiency + tool use).
  3. Soundness: weak "LLM-as-judge" using the *same* tiny model to rate the reasoning 1-5.
- Produces a clear report + shows example trajectories so you can see what "good" and "bad" look like.

Why this matters:
Demos are fun. Production agents need *measurement*. This is the smallest possible
version of an evaluator that makes iteration (prompt changes, memory, better parsing,
future synthetic data) visible and comparable.

Because we use the tiny overfit character-level LSTM, expect:
- Low outcome success on anything requiring precise format or novel reasoning.
- Noisy or failed judge scores (the model is not a good critic of itself yet).
- High variance between runs.

That is the pedagogical point. Later prototypes (synthetic data, stronger backends
via the Predictor, typed workflows) will attack exactly these gaps.

Run from project root:
    python llm/trajectory_evaluator.py
    python llm/trajectory_evaluator.py --max-steps 6 --episodes 12 --judge
    python llm/trajectory_evaluator.py --force-train --max-steps 4
"""

from __future__ import annotations

import argparse
import os
import random
import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

# --- Reuse previous prototypes (the Predictor seam makes this trivial) ---
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
class EvalTask:
    goal: str
    category: str                  # needs-tool, no-tool, ambiguous, reasoning
    description: str
    success_substrings: List[str] = field(default_factory=list)  # any of these in answer => heuristic success
    notes: str = ""


# Small, self-contained benchmark in the Elara universe.
# We deliberately mix easy wins and things the tiny model will struggle with.
EVAL_TASKS: List[EvalTask] = [
    EvalTask(
        goal="How much energy might the crystals hold if each one gives a small spark? Use calc.",
        category="needs-tool",
        description="Direct calc with natural language (hopes model emits Action)",
        success_substrings=["14", "energy", "spark"],
        notes="Classic example from the story + ReAct traces.",
    ),
    EvalTask(
        goal="What does the story say about the glowing crystals?",
        category="needs-tool",
        description="Should trigger lookup[crystals] or similar",
        success_substrings=["glow", "crystal", "machine", "energy"],
    ),
    EvalTask(
        goal="Who is Elara?",
        category="no-tool",
        description="Simple fact that can be answered from context or memory of the story",
        success_substrings=["dreamed", "Elara", "girl", "curious"],
    ),
    EvalTask(
        goal="Is the village quiet at night?",
        category="no-tool",
        description="Yes/no style question likely answerable without tool",
        success_substrings=["quiet", "yes", "night", "village"],
    ),
    EvalTask(
        goal="Calculate the distance to the machine if it is three times farther than the crystals.",
        category="needs-tool",
        description="Requires calc after possible lookup",
        success_substrings=["distance", "calc", "3"],
    ),
    EvalTask(
        goal="Tell me something surprising about the machine from the story.",
        category="reasoning",
        description="Open-ended; success if it produces a coherent Final Answer at all",
        success_substrings=["machine", "whisper", "secret", "power"],
    ),
    EvalTask(
        goal="What is 7 plus the number of crystals Elara found?",
        category="ambiguous",
        description="Needs both lookup-ish memory and calc; tests chaining",
        success_substrings=["7", "ten", "crystal"],
    ),
]


def parse_judge_score(text: str) -> Optional[float]:
    """Very forgiving parser for the weak model's judge output."""
    m = re.search(r"SCORE[:\s]*([0-5](?:\.[0-9])?)\s*/\s*5", text, re.IGNORECASE)
    if m:
        try:
            return float(m.group(1))
        except ValueError:
            pass
    # fallback: any lone digit 1-5 near "score" or at end
    m2 = re.search(r"\b([1-5])\b", text)
    if m2:
        return float(m2.group(1))
    return None


def run_and_score(
    task: EvalTask,
    predictor: Predictor,
    max_steps: int = 5,
    use_judge: bool = True,
) -> Dict[str, Any]:
    """Run one trajectory (silently) and return rich scoring dict."""
    answer, trajectory, steps = run_react(
        question=task.goal,
        predictor=predictor,
        tools=TOOLS,
        max_steps=max_steps,
        verbose=False,
        return_trajectory=True,
    )

    # Outcome (heuristic)
    ans_lower = (answer or "").lower()
    outcome_success = any(s.lower() in ans_lower for s in task.success_substrings)

    # Process metrics
    tool_call_count = sum(1 for t in trajectory if t.lower().startswith("action:"))
    thought_count = sum(1 for t in trajectory if t.lower().startswith("thought:"))

    # Weak LLM-as-judge (using the exact same tiny brain)
    judge_score = None
    judge_reason = ""
    if use_judge and predictor is not None:
        # Keep the judge prompt tiny and structured so even the weak model has a chance
        traj_text = "\n".join(trajectory[-6:])  # last few turns are usually most relevant
        judge_prompt = (
            "You are judging a tiny agent.\n"
            f"Goal: {task.goal}\n\n"
            f"Trajectory:\n{traj_text}\n\n"
            f"Final answer: {answer}\n\n"
            "Rate 1-5 how well the agent helped with the goal (5 = excellent reasoning + useful tools).\n"
            "Reply with exactly this format:\n"
            "SCORE: 3/5\n"
            "REASON: one short sentence.\n"
        )
        try:
            judge_raw = predictor(judge_prompt, max_new_tokens=40)
            # strip any prompt echo
            if judge_raw.startswith(judge_prompt):
                judge_raw = judge_raw[len(judge_prompt):].strip()
            judge_score = parse_judge_score(judge_raw)
            # crude reason grab
            m = re.search(r"REASON[:\s]*(.+)", judge_raw, re.IGNORECASE | re.DOTALL)
            if m:
                judge_reason = m.group(1).strip()[:120]
        except Exception:
            judge_score = None

    return {
        "goal": task.goal,
        "category": task.category,
        "answer": answer,
        "trajectory": trajectory,
        "steps": steps,
        "tool_calls": tool_call_count,
        "thoughts": thought_count,
        "outcome_success": outcome_success,
        "judge_score": judge_score,
        "judge_reason": judge_reason,
    }


def main():
    parser = argparse.ArgumentParser(description="Agent Trajectory Evaluator (Proto 4)")
    parser.add_argument("--model-path", type=str, default="llm/tiny_model.pt",
                        help="Path to persisted tiny model")
    parser.add_argument("--max-steps", type=int, default=5,
                        help="Max ReAct steps per episode")
    parser.add_argument("--episodes", type=int, default=len(EVAL_TASKS),
                        help="How many tasks to evaluate (subset for speed)")
    parser.add_argument("--force-train", action="store_true",
                        help="Retrain even if model file exists")
    parser.add_argument("--judge", action="store_true", default=True,
                        help="Enable the weak LLM-as-judge (uses same tiny model)")
    parser.add_argument("--no-judge", dest="judge", action="store_false",
                        help="Disable the LLM judge for pure speed/heuristic only")
    parser.add_argument("--seed", type=int, default=42, help="For reproducibility of task order")
    args = parser.parse_args()

    random.seed(args.seed)

    device = "cpu"  # evaluators usually want reproducibility

    print("=" * 72)
    print("AGENT TRAJECTORY EVALUATOR")
    print("=" * 72)
    print("Reusing: mini_react.run_react + Predictor + persisted TinyLLM + Elara tools")
    print(f"Model: {args.model_path}")
    print(f"Episodes: {min(args.episodes, len(EVAL_TASKS))}  |  max-steps: {args.max_steps}")
    print(f"LLM judge: {'on' if args.judge else 'off'}")
    print()

    # Load or train (same pattern as the lab and mini_react)
    if os.path.exists(args.model_path) and not args.force_train:
        model = load_model(args.model_path, device=device)
    else:
        print("Training fresh tiny model for evaluation...")
        model = build_trained_model(epochs=12, device=device)
        save_model(model, args.model_path)

    predictor = from_tiny_llm(model, temperature=0.65, device=device)

    tasks_to_run = EVAL_TASKS[: args.episodes]
    results: List[Dict[str, Any]] = []

    for i, task in enumerate(tasks_to_run):
        print(f"[{i+1}/{len(tasks_to_run)}] {task.category}: {task.description}")
        print(f"     Goal: {task.goal[:80]}{'...' if len(task.goal) > 80 else ''}")
        res = run_and_score(task, predictor, max_steps=args.max_steps, use_judge=args.judge)
        results.append(res)

        status = "✓" if res["outcome_success"] else "✗"
        judge_str = f"  judge={res['judge_score']}/5" if res["judge_score"] is not None else ""
        print(f"     {status}  steps={res['steps']}  tools={res['tool_calls']}  answer={res['answer'][:60]!r}{judge_str}")
        print()

    # === Aggregate Report ===
    total = len(results)
    successes = sum(1 for r in results if r["outcome_success"])
    rate = (successes / total * 100) if total else 0

    avg_steps_all = sum(r["steps"] for r in results) / total if total else 0
    avg_tools_all = sum(r["tool_calls"] for r in results) / total if total else 0

    successes_only = [r for r in results if r["outcome_success"]]
    avg_steps_success = sum(r["steps"] for r in successes_only) / len(successes_only) if successes_only else 0

    judge_scores = [r["judge_score"] for r in results if r["judge_score"] is not None]
    avg_judge = sum(judge_scores) / len(judge_scores) if judge_scores else None

    print("=" * 72)
    print("SUMMARY REPORT")
    print("=" * 72)
    print(f"Episodes run:      {total}")
    print(f"Outcome successes: {successes}  ({rate:.1f}%)")
    print(f"Avg steps (all):   {avg_steps_all:.1f}")
    print(f"Avg steps (success): {avg_steps_success:.1f}")
    print(f"Avg tool calls:    {avg_tools_all:.1f}")
    if avg_judge is not None:
        print(f"Avg judge score:   {avg_judge:.1f}/5  (from {len(judge_scores)} parsable judgments)")
    print()

    # Category breakdown
    by_cat: Dict[str, Dict[str, Any]] = {}
    for r in results:
        c = r["category"]
        if c not in by_cat:
            by_cat[c] = {"total": 0, "success": 0, "steps": [], "tools": []}
        by_cat[c]["total"] += 1
        if r["outcome_success"]:
            by_cat[c]["success"] += 1
        by_cat[c]["steps"].append(r["steps"])
        by_cat[c]["tools"].append(r["tool_calls"])

    print("By category:")
    for cat, stats in sorted(by_cat.items()):
        srate = (stats["success"] / stats["total"] * 100) if stats["total"] else 0
        avg_s = sum(stats["steps"]) / len(stats["steps"])
        print(f"  {cat:12s}  {stats['success']}/{stats['total']} ({srate:4.1f}%)   avg_steps={avg_s:.1f}")
    print()

    # Show a couple of representative trajectories (the most interesting part)
    print("=" * 72)
    print("EXAMPLE TRAJECTORIES (truncated)")
    print("=" * 72)
    # Pick one success and one non-success if possible
    success_ex = next((r for r in results if r["outcome_success"]), None)
    fail_ex = next((r for r in results if not r["outcome_success"]), None)

    for label, ex in [("SUCCESS-ish", success_ex), ("FAIL-ish", fail_ex)]:
        if not ex:
            continue
        print(f"\n--- {label} ---")
        print(f"Goal: {ex['goal']}")
        print(f"Final: {ex['answer']}")
        print("Trajectory (last entries):")
        for entry in ex["trajectory"][-5:]:
            short = entry[:95] + "..." if len(entry) > 95 else entry
            print(f"  {short}")
        if ex["judge_score"] is not None:
            print(f"Judge: {ex['judge_score']}/5  {ex['judge_reason'][:80]}")
        print()

    # ------------------------------------------------------------------
    # WHAT YOU JUST SAW
    # ------------------------------------------------------------------
    print("=" * 72)
    print("WHAT YOU JUST SAW")
    print("=" * 72)
    print("""
1. The evaluator is ordinary Python. It calls the exact same run_react that the
   interactive demo and the reliability lab use (now with return_trajectory=True
   for measurement).

2. Three cheap axes of scoring:
   - Outcome (substring heuristics on the final answer) — crude but automatic.
   - Process (step count + tool call count) — tells you about efficiency and
     whether the agent even tried to use tools.
   - Weak self-judge — we literally ask the same tiny model "how did I do?"
     This almost always produces noisy or unparsable output. That is *expected*
     and useful data.

3. Because the underlying model only ever saw one short story repeated, it has
   almost no ability to follow the ReAct format on novel goals. The evaluator
   makes the cost of that limitation quantitative instead of anecdotal.

4. The return_trajectory extension to run_react is tiny and backward-compatible.
   All previous callers (mini_react CLI, reliability lab, memory explainer)
   continue to work unchanged.

5. This is the beginning of an improvement flywheel:
   - Run evaluator
   - Look at the worst trajectories
   - Improve prompt / memory / parser / model
   - Re-run evaluator and watch the numbers move

Try these experiments:
- Run with --max-steps 3 vs --max-steps 8. See how extra steps affect success vs
  "just rambling until timeout".
- Add your own EvalTask with a goal that requires two tool uses in sequence.
- Turn off the judge (--no-judge) and compare speed.
- After you improve something in mini_react or add better memory, re-run the
  evaluator and compare the success rate / avg judge score.

This prototype (plus the reliability lab) is what makes the later items on the
roadmap (synthetic data from good trajectories, stronger local models behind
the Predictor, typed workflows) obviously necessary instead of abstract.
""")

    print(f"Overall outcome success rate in this run: {rate:.1f}%")
    if successes_only:
        print(f"Successful runs tended to finish in ~{avg_steps_success:.1f} steps.")


if __name__ == "__main__":
    main()
