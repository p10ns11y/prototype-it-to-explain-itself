#!/usr/bin/env python3
"""
Human-in-the-Loop Agent "Desktop"
=================================

Prototype 8: Teach oversight, intervention, and mixed autonomy.

Real production agents are rarely left completely alone, especially when
the stakes are high or the model is still weak. This prototype makes the
human supervision patterns visible and runnable in the terminal.

What it provides:
- Runs the agent (using the typed workflow or plain ReAct) step by step
  or in batch.
- Surfaces "low confidence" signals (long trajectories, low judge scores
  from the evaluator, many errors, etc.).
- At each interesting point the human can:
  - Approve the next step
  - Edit the model's proposed Final Answer
  - Inject a manual Observation or Thought
  - Abort / escalate
  - Log the intervention with a reason
- Different "autonomy modes": fully manual, "ask on low confidence",
  "run to end then review".
- Produces an audit log of every human intervention.

This is the terminal equivalent of what a real desktop app (Tauri + webview,
Textual, NiceGUI, or a small internal tool) would do with nice buttons,
"what the agent was about to do" previews, and persistent logs.

Everything still only talks to a Predictor. You can use the tiny model,
a stub, or (in real life) a strong local model.

Run:
    python llm/human_in_loop.py
    python llm/human_in_loop.py --mode review --question "..."
    python llm/human_in_loop.py --autonomy ask-on-low-confidence

The point is not the fancy UI — it is making the *patterns* of human
oversight, intervention logging, and different autonomy levels concrete.
"""

from __future__ import annotations

import argparse
import datetime as dt
from dataclasses import dataclass, field
from typing import List, Optional

import sys
from pathlib import Path

_llm_dir = Path(__file__).resolve().parent
if str(_llm_dir) not in sys.path:
    sys.path.insert(0, str(_llm_dir))

from mini_react import run_react, TOOLS
from local_inference_playground import BACKENDS
from typed_agent_workflow import run_typed_workflow, TypedTrajectory


@dataclass
class Intervention:
    timestamp: str
    step: int
    action: str          # "approve", "edit_final", "inject_observation", "abort", ...
    reason: str
    before: str
    after: str = ""


@dataclass
class OversightSession:
    goal: str
    backend: str
    interventions: List[Intervention] = field(default_factory=list)
    final_answer: Optional[str] = None
    autonomy_mode: str = "ask-on-low-confidence"

    def log(self, step: int, action: str, reason: str, before: str, after: str = ""):
        self.interventions.append(
            Intervention(
                timestamp=dt.datetime.now().isoformat(timespec="seconds"),
                step=step,
                action=action,
                reason=reason,
                before=before,
                after=after,
            )
        )

    def summary(self) -> str:
        lines = [f"Goal: {self.goal}", f"Backend: {self.backend}", f"Mode: {self.autonomy_mode}"]
        lines.append(f"Interventions: {len(self.interventions)}")
        if self.final_answer:
            lines.append(f"Final: {self.final_answer}")
        return "\n".join(lines)


def is_low_confidence(traj: TypedTrajectory, last_judge: Optional[float] = None) -> bool:
    """Heuristic for 'the human should look at this'."""
    if last_judge is not None and last_judge < 3.0:
        return True
    if len(traj.steps) > 6:
        return True
    if any(isinstance(s, type(traj.steps[0]).__class__()) and "Error" in str(s) for s in traj.steps):  # rough
        return True
    return False


def human_loop(goal: str, backend_name: str = "stub-smart",
               mode: str = "ask-on-low-confidence",
               max_steps: int = 6) -> OversightSession:
    """
    The core "desktop" experience.
    mode: "manual" | "ask-on-low-confidence" | "run-then-review"
    """
    session = OversightSession(goal=goal, backend=backend_name, autonomy_mode=mode)
    predictor = BACKENDS[backend_name]()

    print(f"\n[HIL] Starting human-in-the-loop session")
    print(f"      Goal: {goal}")
    print(f"      Backend: {backend_name}")
    print(f"      Mode: {mode}")
    print("      (type 'h' at any prompt for help)\n")

    # We run the typed workflow so we get nice structure for the human to inspect
    typed = run_typed_workflow(goal, predictor, max_steps=max_steps)

    # Simple interactive loop over the steps
    for idx, step in enumerate(typed.steps):
        print(f"\n--- Step {idx+1} ---")
        print(step)

        low_conf = is_low_confidence(typed)  # simplistic

        if mode == "manual" or (mode == "ask-on-low-confidence" and low_conf):
            action = input("Action? [a]pprove / [e]dit final / [i]nject obs / [s]kip / [q]uit > ").strip().lower()
            if action in ("q", "quit"):
                session.log(idx, "abort", "user quit", str(step))
                break
            if action in ("e", "edit") and isinstance(step, type(typed.steps[0])):  # Final
                new = input("New final answer: ").strip()
                session.log(idx, "edit_final", "human correction", str(step), new)
                typed.steps[idx] = type(step)(new)  # type: ignore
            elif action in ("i", "inject"):
                obs = input("Observation to inject: ").strip()
                session.log(idx, "inject_observation", "human provided info", str(step), obs)
                # In a real system you would splice it into the trajectory and continue
            else:
                session.log(idx, "approve", "human approved", str(step))

        elif mode == "run-then-review":
            # Just collect everything, review at the end
            session.log(idx, "auto", "run-then-review mode", str(step))

    if typed.is_complete():
        session.final_answer = typed.last_final()

    print("\n--- Session complete ---")
    print(session.summary())
    if session.interventions:
        print("\nIntervention log:")
        for iv in session.interventions:
            print(f"  {iv.timestamp} step={iv.step} {iv.action}: {iv.reason}")

    return session


def main():
    parser = argparse.ArgumentParser(description="Human-in-the-Loop Agent Desktop (Proto 8)")
    parser.add_argument("--backend", default="stub-smart")
    parser.add_argument("--question", default="How can Elara measure the power of the glowing crystals?")
    parser.add_argument("--max-steps", type=int, default=6)
    parser.add_argument("--mode", default="ask-on-low-confidence",
                        choices=["manual", "ask-on-low-confidence", "run-then-review"])
    args = parser.parse_args()

    print("=" * 70)
    print("HUMAN-IN-THE-LOOP AGENT DESKTOP (terminal edition)")
    print("=" * 70)
    print("This is what a real Tauri / Textual / web oversight tool would feel like,")
    print("just without the pixels. The important part is the *patterns*:\n"
          "  - low-confidence surfacing\n"
          "  - explicit approval / edit / injection points\n"
          "  - full audit log of every human intervention\n"
          "  - different autonomy modes\n")

    session = human_loop(
        goal=args.question,
        backend_name=args.backend,
        mode=args.mode,
        max_steps=args.max_steps,
    )

    # ------------------------------------------------------------------
    # WHAT YOU JUST SAW
    # ------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("WHAT YOU JUST SAW")
    print("=" * 70)
    print("""
1. The "desktop" is just a loop that pauses at interesting points and asks
   the human what to do. All the intelligence still comes from a Predictor.

2. Low-confidence detection is deliberately simple (step count + judge score).
   In a real system you would combine:
   - model uncertainty / token probabilities (if exposed by the backend)
   - length of trajectory
   - evaluator scores
   - known failure patterns from the reliability lab

3. Every intervention is logged with before/after + human reason. This log
   is gold for later synthetic data, auditing, or training a "when to ask
   for help" policy.

4. The three modes are the classic autonomy spectrum:
   - manual: human is in the loop for everything (great for debugging or high-stakes)
   - ask-on-low-confidence: the sweet spot for most early deployments
   - run-then-review: useful for batch overnight runs + morning oversight

5. Because everything still only depends on the Predictor, you can give the
   human the same oversight UI whether the brain is the tiny LSTM, a local
   Llama, or (in the future) a much stronger model.

Production reality (why this is Proto 8):
- A real desktop would be Rust + Tauri + a small webview, or Python Textual
  / NiceGUI / Streamlit.
- You would persist the session, have "what the agent is about to do" live
  previews, escalation to other humans, and policy rules ("never let the
  agent call the delete tool without two approvals").

The terminal version here makes the *mental model* completely clear and
runnable inside the same tiny project as everything that came before.
""")

    print("Human oversight is not a nice-to-have. It is part of the architecture.")


if __name__ == "__main__":
    main()
