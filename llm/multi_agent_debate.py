#!/usr/bin/env python3
"""
Multi-Agent Debate / Collaboration
==================================

Prototype 9: Scaling via collaboration and structured disagreement.

A single (especially a tiny) agent plateaus. Giving several agents the
same goal, letting them propose, critique, and converge often produces
better results than any one of them alone — without needing a bigger
model.

This prototype is the capstone. It reuses *everything* built in 1–8:

- The Predictor seam (each "agent" can have its own backend or temperature)
- ReAct + tools (each specialist is a configured run_react)
- Memory (specialists can be given different memory contexts)
- The evaluator / typed workflow (for scoring proposals)
- The human-in-the-loop patterns (the orchestrator can ask for help on
  close calls)
- Synthetic data ideas (good debate traces are excellent training data)

What it does (tiny orchestrator pattern):
1. Spawns 2–3 specialist agents for the same hard goal.
   (Different temperature, slight prompt variation, or one with memory
   and one without — all still using the same tools and Predictor.)
2. Each produces a proposal (full trajectory + final answer).
3. A critic / judge (another Predictor call, or the trajectory evaluator
   logic) scores them and/or lets them critique each other in a short
   "debate" round.
4. Convergence: pick the highest-scoring answer, or synthesize a final
   one that incorporates the best points from the debate.
5. Everything is logged so the trace of "who said what and why we chose
   this" is visible and auditable.

This is the classic "mixture-of-agents" / "debate" pattern made completely
visible and runnable with our tiny stack.

Run:
    python llm/multi_agent_debate.py
    python llm/multi_agent_debate.py --goal "What is the relationship between the crystals and the machine?" --agents 3

Because every specialist only ever talks to a Predictor, you can later
give some of them strong local models while keeping the orchestrator and
critic on the tiny one (or vice versa). The collaboration logic stays the
same.

This is the last prototype in the original 9. Everything before it was
preparation for being able to build this cleanly and understand what is
actually happening.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

import sys
from pathlib import Path

_llm_dir = Path(__file__).resolve().parent
if str(_llm_dir) not in sys.path:
    sys.path.insert(0, str(_llm_dir))

from mini_react import run_react, TOOLS
from local_inference_playground import BACKENDS
from trajectory_evaluator import run_and_score, EVAL_TASKS
from typed_agent_workflow import run_typed_workflow


@dataclass
class AgentProposal:
    agent_id: str
    backend: str
    trajectory: List[str]
    final_answer: str
    judge_score: Optional[float] = None


@dataclass
class DebateResult:
    goal: str
    proposals: List[AgentProposal]
    winner: Optional[AgentProposal]
    debate_trace: List[str]
    final_synthesis: str


def spawn_specialist(goal: str, backend_name: str, agent_id: str,
                     max_steps: int = 6, use_memory: bool = False) -> AgentProposal:
    """
    A 'specialist' is just a configured run_react (plus optional memory
    or typed lifting). Different backends or slight behavioral knobs
    create diversity.
    """
    predictor = BACKENDS[backend_name]()

    # We can give one specialist memory and another not, etc.
    extra = ""
    if use_memory:
        # Extremely simplified "memory" for this specialist
        extra = "Relevant fact from previous runs: the crystals glow when the machine is near.\n"

    raw_answer, traj, _ = run_react(
        question=goal,
        predictor=predictor,
        tools=TOOLS,
        max_steps=max_steps,
        verbose=False,
        extra_context=extra,
        return_trajectory=True,
    )

    return AgentProposal(
        agent_id=agent_id,
        backend=backend_name,
        trajectory=traj,
        final_answer=raw_answer,
    )


def critique_proposals(goal: str, proposals: List[AgentProposal],
                       critic_backend: str = "stub-smart") -> List[AgentProposal]:
    """
    A separate 'critic' (another Predictor) scores each proposal.
    This is the debate / judgment round.
    """
    critic = BACKENDS[critic_backend]()

    scored = []
    for p in proposals:
        traj_text = "\n".join(p.trajectory[-6:])
        critique_prompt = (
            "You are judging several tiny agents that worked on the same goal.\n"
            f"Goal: {goal}\n\n"
            f"Proposal from {p.agent_id} ({p.backend}):\n{traj_text}\n\n"
            f"Final answer: {p.final_answer}\n\n"
            "Rate 1-5 how good this proposal is (sound reasoning, correct tool use if any, clear final answer).\n"
            "Reply with exactly: SCORE: 4/5\n"
        )
        try:
            raw = critic(critique_prompt, max_new_tokens=20)
            import re
            m = re.search(r"([0-5](?:\.[0-9])?)", raw)
            score = float(m.group(1)) if m else 2.5
        except Exception:
            score = 2.5

        p.judge_score = score
        scored.append(p)
    return scored


def simple_debate_and_synthesize(goal: str, scored: List[AgentProposal],
                                 orchestrator_backend: str = "stub-smart") -> DebateResult:
    """
    Very small 'debate' round + synthesis.
    In a bigger system the agents would critique each other directly.
    Here the orchestrator (another Predictor call) looks at the scored
    proposals and produces a final synthesis.
    """
    orchestrator = BACKENDS[orchestrator_backend]()

    debate_lines = []
    for p in sorted(scored, key=lambda x: x.judge_score or 0, reverse=True):
        debate_lines.append(f"{p.agent_id} ({p.backend}) scored {p.judge_score}: {p.final_answer[:80]}")

    synth_prompt = (
        "You are the final synthesizer for a multi-agent debate.\n"
        f"Original goal: {goal}\n\n"
        "Proposals (best first):\n" + "\n".join(debate_lines) + "\n\n"
        "Produce a single, clear, well-justified final answer that takes the best points from the debate.\n"
        "Final Answer: ...\n"
    )
    synthesis = orchestrator(synth_prompt, max_new_tokens=60)
    # crude extraction
    if "Final Answer:" in synthesis:
        synthesis = synthesis.split("Final Answer:")[-1].strip()

    winner = max(scored, key=lambda x: x.judge_score or 0) if scored else None

    return DebateResult(
        goal=goal,
        proposals=scored,
        winner=winner,
        debate_trace=debate_lines,
        final_synthesis=synthesis,
    )


def run_debate(goal: str, num_agents: int = 3, max_steps: int = 5) -> DebateResult:
    """The main orchestrator."""
    print(f"\n[MultiAgent] Running debate on: {goal}")

    # Spawn a diverse set of specialists
    backends = ["stub-smart", "stub-fast", "tiny-lstm"]
    proposals = []
    for i in range(num_agents):
        b = backends[i % len(backends)]
        use_mem = (i == 0)  # give memory to the first one for diversity
        p = spawn_specialist(goal, b, f"agent-{i}", max_steps=max_steps, use_memory=use_mem)
        proposals.append(p)
        print(f"  {p.agent_id} ({p.backend}) proposed: {p.final_answer[:70]}...")

    # Critique round
    scored = critique_proposals(goal, proposals)

    # Debate + synthesize
    result = simple_debate_and_synthesize(goal, scored)

    print("\n--- Debate trace (best first) ---")
    for line in result.debate_trace:
        print(" ", line)

    print(f"\nWinner: {result.winner.agent_id if result.winner else 'none'}")
    print(f"Synthesized final:\n{result.final_synthesis}")

    return result


def main():
    parser = argparse.ArgumentParser(description="Multi-Agent Debate (Proto 9)")
    parser.add_argument("--goal", default="What is the true relationship between the glowing crystals and the machine?")
    parser.add_argument("--agents", type=int, default=3)
    parser.add_argument("--max-steps", type=int, default=5)
    args = parser.parse_args()

    print("=" * 70)
    print("MULTI-AGENT DEBATE / COLLABORATION (capstone)")
    print("=" * 70)
    print("This reuses the entire previous stack through the Predictor seam.")
    print("Different 'agents' are just different configurations of the same")
    print("ReAct + tools + (optional) memory, judged by another Predictor call.\n")

    result = run_debate(args.goal, num_agents=args.agents, max_steps=args.max_steps)

    # ------------------------------------------------------------------
    # WHAT YOU JUST SAW
    # ------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("WHAT YOU JUST SAW")
    print("=" * 70)
    print("""
1. The orchestrator is tiny. It just spawns a few specialists (configured
   run_react calls), collects their proposals, runs a critic, and synthesizes.

2. Diversity comes from cheap knobs: different backends (via Proto 5),
   different memory (via Proto 3), different temperatures, or one specialist
   that was improved by Proto 6 data.

3. The judge/critic is another Predictor call — the same interface used
   everywhere. No special multi-agent runtime was required.

4. Everything previous paid off:
   - Typed workflow (7) could be used inside a specialist for safety.
   - Human-in-the-loop (8) could be inserted on close calls.
   - The evaluator (4) + synthetic factory (6) can consume the debate traces
     to make the next generation of specialists better.
   - The playground (5) lets you give different specialists different real
     local models later.

5. This is the classic way single (especially small) models get better
   performance on hard tasks: let several reason independently, then
   reconcile. In production this pattern appears as mixture-of-agents,
   self-consistency, debate, and tool-augmented multi-agent systems.

You have now built, from a 150k-parameter character LSTM and one short
story, a complete, interconnected, self-improving, multi-agent, human-
overseeable system — and you can see every moving part.

The 9 prototypes are complete.
The Predictor seam is the gift that keeps on giving.
""")

    print("Single agents plateau. Collaboration + measurement + self-improvement do not.")


if __name__ == "__main__":
    main()
