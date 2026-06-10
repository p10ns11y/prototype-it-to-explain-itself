#!/usr/bin/env python3
"""
Synthetic Data Factory
======================

Prototype 6: Close the data flywheel using the agent itself.

Real production systems improve the model with its own successful (or
preference-ranked) outputs. This tiny prototype makes that loop visible
and runnable without leaving the Elara universe or requiring external
data.

The flow (all inside this one small file):
1. Use the Trajectory Evaluator (or direct ReAct runs) + good trajectories
   from previous prototypes.
2. Add a cheap self-critique / filter step (another Predictor call that
   judges "was this a high-quality, correctly formatted, helpful run?").
3. Collect only the "good" full trajectories or (prompt, completion) pairs.
4. Turn them into training data that teaches the model the ReAct format
   + domain facts from successful tool use.
5. (Optional) Mix with the original STORY and train a new checkpoint.
   The new model should be better at emitting clean "Action: ..." lines.

Everything reuses:
- The Predictor seam (so you can generate data with "stub-smart" then
  fine-tune the real tiny model, or vice versa).
- run_react (with return_trajectory=True)
- The existing Elara tasks from trajectory_evaluator
- The same tiny training loop from simple_llm_prototype

Because the original model only ever saw repeated story text, it is bad
at structured output. Synthetic agent data is the natural cure.

Run:
    python llm/synthetic_data_factory.py --episodes 12 --filter
    python llm/synthetic_data_factory.py --episodes 20 --train --epochs 5

The output dataset + (optionally) an improved model checkpoint demonstrate
the self-improvement loop that powers Proto 7+.
"""

from __future__ import annotations

import argparse
import os
import random
from typing import List, Dict, Any, Optional

import sys
from pathlib import Path

_llm_dir = Path(__file__).resolve().parent
if str(_llm_dir) not in sys.path:
    sys.path.insert(0, str(_llm_dir))

from mini_react import run_react, TOOLS
from tiny_predictor import from_tiny_llm, Predictor
from trajectory_evaluator import EVAL_TASKS, run_and_score  # reuse the tasks + scorer

# We also need the training pieces for the optional "improve" step
from simple_llm_prototype import (
    build_trained_model, save_model, load_model, train_model,
    CharDataset, DataLoader, STORY as ORIGINAL_STORY
)


def generate_trajectories(predictor: Predictor, n: int = 12,
                          max_steps: int = 6) -> List[Dict[str, Any]]:
    """Run many episodes and return rich trajectory records."""
    records = []
    tasks = EVAL_TASKS * ((n // len(EVAL_TASKS)) + 1)

    for i, task in enumerate(tasks[:n]):
        rec = run_and_score(task, predictor, max_steps=max_steps, use_judge=True)
        rec["episode"] = i
        records.append(rec)
    return records


def self_critique_and_filter(records: List[Dict[str, Any]],
                             predictor: Predictor,
                             min_score: float = 3.5) -> List[Dict[str, Any]]:
    """
    For each trajectory, ask the (same) predictor to critique it.
    Keep only those that the critic thinks are high quality.
    This is the cheap "preference / quality filter" step.
    """
    kept = []
    for rec in records:
        if not rec.get("trajectory"):
            continue

        traj_text = "\n".join(rec["trajectory"][-8:])
        critique_prompt = (
            "You are a strict critic of tiny agents.\n"
            f"Goal: {rec['goal']}\n\n"
            f"Trajectory:\n{traj_text}\n\n"
            f"Final answer: {rec.get('answer', '')}\n\n"
            "Is this a high-quality, correctly formatted, helpful run that "
            "reached a reasonable conclusion using tools properly when needed?\n"
            "Reply with exactly:\n"
            "SCORE: 4/5\n"
            "KEEP: yes\n"
            "REASON: one short sentence.\n"
        )
        try:
            raw = predictor(critique_prompt, max_new_tokens=30)
            score = 0.0
            keep = False
            for line in raw.splitlines():
                if "SCORE" in line.upper():
                    import re
                    m = re.search(r"([0-5](?:\.[0-9])?)", line)
                    if m:
                        score = float(m.group(1))
                if "KEEP" in line.upper() and "yes" in line.lower():
                    keep = True
            rec["critic_score"] = score
            rec["critic_keep"] = keep
            if keep and score >= min_score:
                kept.append(rec)
        except Exception:
            pass
    return kept


def trajectory_to_training_examples(rec: Dict[str, Any]) -> List[str]:
    """
    Turn a good trajectory into one or more training "stories".
    We treat the full ReAct dialogue as text the model should be able to
    continue in the right style.
    """
    examples = []
    traj = rec.get("trajectory", [])
    if len(traj) < 2:
        return examples

    full = "\n".join(traj)
    # Create a few sliding "next token" style examples from the successful trace
    # (keeps everything tiny and compatible with the existing CharDataset)
    for i in range(0, len(full) - 40, 25):
        chunk = full[i:i+120]
        examples.append(chunk)
    return examples


def build_synthetic_corpus(good_records: List[Dict[str, Any]]) -> str:
    """Concatenate the best trajectories into one big training string."""
    pieces = []
    for rec in good_records:
        pieces.append(f"Goal: {rec['goal']}")
        pieces.append("\n".join(rec.get("trajectory", [])))
        pieces.append("\n---\n")
    return "\n".join(pieces)


def improve_model(original_model, good_records: List[Dict[str, Any]],
                  epochs: int = 5, device: str = "cpu"):
    """
    Mix the original STORY with synthetic ReAct traces and train a bit more.
    This is the "fine-tune on your own agent's successful outputs" step.
    """
    synthetic = build_synthetic_corpus(good_records)
    mixed = (ORIGINAL_STORY + "\n\n" + synthetic) * 3   # repeat for more weight on new style

    # Reuse the exact training machinery
    from simple_llm_prototype import encode, CharDataset, DataLoader, train_model

    data = [encode(mixed)]
    dataset = CharDataset(data, seq_len=30)
    loader = DataLoader(dataset, batch_size=32, shuffle=True)

    # Continue training the existing model weights
    trained = train_model(original_model, loader, epochs=epochs, device=device)
    return trained


def main():
    parser = argparse.ArgumentParser(description="Synthetic Data Factory (Proto 6)")
    parser.add_argument("--episodes", type=int, default=15,
                        help="How many agent runs to generate data from")
    parser.add_argument("--filter", action="store_true", default=True,
                        help="Run self-critique filter (recommended)")
    parser.add_argument("--no-filter", dest="filter", action="store_false")
    parser.add_argument("--train", action="store_true",
                        help="After filtering, actually improve a model checkpoint")
    parser.add_argument("--epochs", type=int, default=4,
                        help="Extra training epochs on the synthetic data")
    parser.add_argument("--model-path", type=str, default="llm/tiny_model.pt")
    parser.add_argument("--out-dataset", type=str, default="llm/synthetic_react.txt",
                        help="Where to write the filtered high-quality trajectories")
    args = parser.parse_args()

    print("=" * 70)
    print("SYNTHETIC DATA FACTORY")
    print("=" * 70)
    print("Generate → Critique/Filter → (optionally) Improve the model")
    print("All on top of the existing Predictor + ReAct + Evaluator stack.")
    print()

    # Use a reasonably good backend for data generation
    # (you can also generate with "stub-smart" and improve the real tiny model)
    from local_inference_playground import BACKENDS
    predictor = BACKENDS["stub-smart"]()   # or switch to tiny-lstm

    print(f"Generating {args.episodes} trajectories...")
    records = generate_trajectories(predictor, n=args.episodes)

    if args.filter:
        print("Running self-critique filter...")
        good = self_critique_and_filter(records, predictor)
    else:
        # fallback: keep anything that at least reached a Final Answer
        good = [r for r in records if any("Final Answer" in t for t in r.get("trajectory", []))]

    print(f"Kept {len(good)} high-quality trajectories out of {len(records)}")

    # Write the synthetic dataset (the "good" agent outputs)
    if good:
        corpus = build_synthetic_corpus(good)
        with open(args.out_dataset, "w") as f:
            f.write(corpus)
        print(f"Wrote filtered synthetic data to {args.out_dataset}")

        # Show one nice example
        example = good[0]
        print("\n--- Example good trajectory (first kept) ---")
        print(f"Goal: {example['goal']}")
        print("\n".join(example["trajectory"][:6]))
        print("...")

    if args.train and good:
        print("\nImproving model on synthetic + original data...")
        if os.path.exists(args.model_path):
            from simple_llm_prototype import load_model
            base_model = load_model(args.model_path)
        else:
            base_model = None  # will be created inside improve_model

        improved = improve_model(base_model, good, epochs=args.epochs)
        out_path = args.model_path.replace(".pt", "_synthetic.pt")
        save_model(improved, out_path)
        print(f"Saved improved checkpoint to {out_path}")
        print("In a real run you would now evaluate the new model with the")
        print("trajectory_evaluator or local_inference_playground to see gains.")

    # ------------------------------------------------------------------
    # WHAT YOU JUST SAW
    # ------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("WHAT YOU JUST SAW")
    print("=" * 70)
    print("""
1. The factory is just "run the agent many times + keep the good ones".
   The self-critique step is another cheap Predictor call — exactly the same
   interface used by ReAct itself.

2. Good trajectories contain the exact format ("Thought:", "Action: name[args]",
   "Observation:", "Final Answer:") that the original story-only model never saw.
   Feeding them back as training data teaches the model the control language.

3. Because everything goes through the Predictor, you can:
   - Generate data with a "smart" stub (or a real strong local model)
   - Improve the tiny teaching model
   - Then use the improved tiny model inside the same playground / evaluator

4. This is the beginning of the real flywheel:
   Evaluator (Proto 4) → filter good traces → Synthetic Data (this) →
   better model → plug back into Playground (Proto 5) → repeat.

5. In production this becomes RLHF / DPO / iterative fine-tuning on agent
   trajectories. Here it is the smallest possible visible version.

Try these experiments:
- Run with --no-filter and compare how noisy the dataset becomes.
- Generate with stub-smart, then --train, then run the trajectory_evaluator
  on the new _synthetic.pt model and watch the success rate / judge scores move.
- Add preference pairs (chosen vs rejected trajectory for the same goal).
- Curriculum: start with easy goals from the evaluator, then harder ones.

Proto 6 turns measurement (Proto 4) into improvement. The next prototypes
(typed workflows, human oversight, multi-agent) become much more powerful
once the base model has seen its own successful behavior.
""")

    print(f"Generated {len(good) if 'good' in locals() else 0} usable synthetic examples.")
    print("The loop is now visible and runnable.")


if __name__ == "__main__":
    main()
