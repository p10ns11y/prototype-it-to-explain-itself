#!/usr/bin/env python3
"""
Typed Agent Workflow
====================

Prototype 7: Reliability by making invalid states impossible.

Many agent bugs are "the code took an illegal path": a Final Answer was
followed by another Action, an Observation appeared without a preceding
Action, the parser returned garbage, etc.

This prototype shows how to model the ReAct loop with strong types + an
explicit state machine so that whole classes of mistakes become
unrepresentable at the type level (or at least very hard to do by accident).

Approach taken here (Python):
- Enums + frozen dataclasses for every possible step (Thought, Action,
  Observation, FinalAnswer, Error).
- A TypedTrajectory that is just a list of these typed steps.
- A tiny state machine (or transition rules) that only permits valid moves:
  Thought → (Action or Final)
  Action → Observation (or Error)
  Observation → Thought
  Final → end
- The existing Predictor + run_react are still used for the "intelligence",
  but we immediately parse their output into the typed world and reject
  anything that doesn't fit the machine.

In a real typed language (especially Rust) you would get compile-time
guarantees via exhaustive match and private constructors. The Python
version here is the closest we can get while staying tiny, runnable, and
in the same repository as the earlier prototypes.

It still reuses the Predictor seam, the Elara tools, and can be dropped
in place of the untyped run_react for any later prototype that wants
stronger guarantees.

Run:
    python llm/typed_agent_workflow.py
    python llm/typed_agent_workflow.py --question "calc[7*8]" --max-steps 4

The output shows both the raw model behavior and the typed, validated
trajectory that the rest of the system can trust.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Union, Optional

import sys
from pathlib import Path

_llm_dir = Path(__file__).resolve().parent
if str(_llm_dir) not in sys.path:
    sys.path.insert(0, str(_llm_dir))

from mini_react import TOOLS, run_react
from tiny_predictor import Predictor
from local_inference_playground import BACKENDS


# ------------------------------------------------------------------
# The typed world — these are the only things that can exist in a
# well-formed trajectory.
# ------------------------------------------------------------------

class StepKind(Enum):
    THOUGHT = auto()
    ACTION = auto()
    OBSERVATION = auto()
    FINAL = auto()
    ERROR = auto()


@dataclass(frozen=True)
class Thought:
    text: str
    kind: StepKind = StepKind.THOUGHT


@dataclass(frozen=True)
class Action:
    tool: str
    arg: str
    kind: StepKind = StepKind.ACTION


@dataclass(frozen=True)
class Observation:
    result: str
    kind: StepKind = StepKind.OBSERVATION


@dataclass(frozen=True)
class FinalAnswer:
    text: str
    kind: StepKind = StepKind.FINAL


@dataclass(frozen=True)
class ErrorStep:
    message: str
    kind: StepKind = StepKind.ERROR


Step = Union[Thought, Action, Observation, FinalAnswer, ErrorStep]


@dataclass(frozen=True)
class TypedTrajectory:
    steps: List[Step]
    goal: str

    def is_complete(self) -> bool:
        return bool(self.steps) and isinstance(self.steps[-1], FinalAnswer)

    def last_final(self) -> Optional[str]:
        for s in reversed(self.steps):
            if isinstance(s, FinalAnswer):
                return s.text
        return None


# ------------------------------------------------------------------
# The state machine / transition validator
# A real version would be even stricter (private constructors, etc.).
# ------------------------------------------------------------------

def validate_transition(prev: Optional[Step], new: Step) -> Optional[str]:
    """Return error message if the transition is illegal, else None."""
    if prev is None:
        if not isinstance(new, Thought):
            return "First step must be a Thought"
        return None

    if isinstance(prev, (FinalAnswer, ErrorStep)):
        return "No steps allowed after Final or Error"

    if isinstance(prev, Thought):
        if not isinstance(new, (Action, FinalAnswer)):
            return "After Thought you must have Action or FinalAnswer"
        return None

    if isinstance(prev, Action):
        if not isinstance(new, (Observation, ErrorStep)):
            return "After Action you must have Observation or Error"
        return None

    if isinstance(prev, Observation):
        if not isinstance(new, Thought):
            return "After Observation you must return to Thought"
        return None

    return None


def to_typed_trajectory(goal: str, raw_trajectory: List[str]) -> TypedTrajectory:
    """
    Take the free-form strings produced by the untyped run_react and turn
    them into a strictly typed, validated trajectory.
    Illegal or unparsable lines become ErrorSteps.
    """
    typed_steps: List[Step] = []
    prev: Optional[Step] = None

    for line in raw_trajectory:
        line = line.strip()
        if not line:
            continue

        new_step: Optional[Step] = None

        if line.lower().startswith("thought:"):
            new_step = Thought(line.split(":", 1)[1].strip())
        elif line.lower().startswith("action:"):
            # parse "Action: calc[3+4]"
            try:
                content = line.split(":", 1)[1].strip()
                tool, arg = content.split("[", 1)
                arg = arg.rstrip("]")
                new_step = Action(tool.strip().lower(), arg.strip())
            except Exception:
                new_step = ErrorStep(f"Bad Action line: {line}")
        elif line.lower().startswith("observation:"):
            new_step = Observation(line.split(":", 1)[1].strip())
        elif line.lower().startswith("final answer:"):
            new_step = FinalAnswer(line.split(":", 1)[1].strip())
        else:
            new_step = ErrorStep(f"Unrecognized step: {line}")

        if new_step:
            err = validate_transition(prev, new_step)
            if err:
                typed_steps.append(ErrorStep(f"{err} (got {new_step})"))
            else:
                typed_steps.append(new_step)
            prev = new_step

    return TypedTrajectory(steps=typed_steps, goal=goal)


def run_typed_workflow(goal: str, predictor: Predictor,
                       max_steps: int = 6) -> TypedTrajectory:
    """
    Run the normal (untyped) ReAct, then immediately lift the result into
    the typed world. This gives you both the raw trace (for teaching) and
    a validated TypedTrajectory that later code can trust.
    """
    # We still get the benefits of the existing loop + forcing hack etc.
    raw_answer, raw_traj, _ = run_react(
        question=goal,
        predictor=predictor,
        tools=TOOLS,
        max_steps=max_steps,
        verbose=False,
        return_trajectory=True,
    )

    # The last entry in raw_traj may be the "last" message on timeout.
    # We still try to parse everything.
    typed = to_typed_trajectory(goal, raw_traj)
    return typed


def main():
    parser = argparse.ArgumentParser(description="Typed Agent Workflow (Proto 7)")
    parser.add_argument("--backend", default="stub-smart",
                        choices=["tiny-lstm", "stub-fast", "stub-smart"])
    parser.add_argument("--question", default="How much energy might the crystals hold if each one gives a small spark?")
    parser.add_argument("--max-steps", type=int, default=5)
    args = parser.parse_args()

    print("=" * 70)
    print("TYPED AGENT WORKFLOW (Reliability by Construction)")
    print("=" * 70)

    predictor = BACKENDS[args.backend]()

    typed = run_typed_workflow(args.question, predictor, max_steps=args.max_steps)

    print(f"\nGoal: {typed.goal}")
    print("\nTyped Trajectory (validated state machine):")
    for i, step in enumerate(typed.steps, 1):
        print(f"  {i}. {step}")

    print(f"\nComplete? {typed.is_complete()}")
    if typed.last_final():
        print(f"Final answer: {typed.last_final()}")

    # ------------------------------------------------------------------
    # WHAT YOU JUST SAW
    # ------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("WHAT YOU JUST SAW")
    print("=" * 70)
    print("""
1. We kept the existing untyped run_react (and all its hacks, forcing logic,
   memory support, etc.) because it is useful for teaching the raw model
   behavior. We then lift its output into a strictly typed representation.

2. The TypedTrajectory + validate_transition make many bad states impossible
   or at least loudly obvious (ErrorStep). In a language with exhaustive
   matching you would get a compile error if you forgot to handle a case.

3. Production version (the reason this is Proto 7 in the roadmap):
   - Rust: enums + match + private newtypes + typestate pattern.
   - The compiler itself becomes part of your reliability story.
   - You can still call out to a Predictor (over FFI, HTTP, or a shared
     library) for the "brain" part.

4. Because this still only talks to a Predictor, you can drop a TypedWorkflow
   into the Local Inference Playground or the Synthetic Data Factory and get
   the typed guarantees "for free".

5. This is the pattern for the remaining prototypes: take a powerful but
   fuzzy concept (agent loops, debate, human oversight) and add just enough
   structure that the dangerous parts become hard to express by accident.

The untyped version is great for exploration.
The typed version is what you ship when correctness matters.
""")

    print("Invalid states are now first-class errors instead of silent bugs.")


if __name__ == "__main__":
    main()
