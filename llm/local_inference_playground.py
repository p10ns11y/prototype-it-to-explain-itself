#!/usr/bin/env python3
"""
Local Inference Playground + Benchmark
======================================

Prototype 5: Make the "Predictor" seam real by swapping the brain.

This prototype demonstrates that the entire agent stack (ReAct, tools, memory,
evaluator) is completely independent of the underlying LLM. Only the factory
that produces a `Predictor` changes.

Key idea:
    predictor: Callable[[str, Optional[int]], str]
    ^ This is the narrow waist. Everything above it stays identical.

What this playground provides:
- Several "backends" behind the exact same interface:
  - "tiny-lstm" — our real character-level model (the teaching brain)
  - "stub-fast" — simulated local inference (fast, lower quality)
  - "stub-smart" — simulated local inference (slower, better format following)
- Live metrics on every prediction: wall time, simulated tokens/s, latency.
- A CLI to switch backends and run either a direct prompt or a full ReAct
  agent (reusing mini_react.run_react unchanged).
- A tiny benchmark mode that runs the same question N times across backends
  and prints a comparison table.
- Shows that adding memory or the trajectory evaluator works on any backend.

Why this matters:
In real life you want to try:
- Your tiny overfit LSTM (for understanding)
- Ollama / llama.cpp / MLX / vLLM (for speed/quality)
- A fine-tuned model you produced with Proto 6
- Even a completely different language/runtime (Rust inference server)

Because of the Predictor contract, none of the agent code above changes.

Run from project root:
    python llm/local_inference_playground.py --backend tiny-lstm --question "How much energy might the crystals hold?"
    python llm/local_inference_playground.py --backend stub-smart --benchmark --runs 5
    python llm/local_inference_playground.py --help

The agent logic never mentions torch, Ollama, or any specific model.
"""

from __future__ import annotations

import argparse
import os
import time
from typing import Optional, Callable, Dict

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

# ------------------------------------------------------------------
# Backend factories — all return something satisfying the Predictor contract
# ------------------------------------------------------------------

def make_tiny_lstm_predictor(model_path: str = "llm/tiny_model.pt",
                             temperature: float = 0.65,
                             device: str = "cpu") -> Predictor:
    """The real one. Requires the trained tiny model."""
    if not os.path.exists(model_path):
        print(f"[playground] No model at {model_path}, training a quick one...")
        model = build_trained_model(epochs=8, device=device)
        save_model(model, model_path)
    else:
        model = load_model(model_path, device=device)

    return from_tiny_llm(model, temperature=temperature, device=device)


def make_stub_predictor(name: str, latency_ms: float = 80.0,
                        quality: str = "medium") -> Predictor:
    """
    Simulated local inference backend.

    quality:
      - "fast": quick but often fails to emit clean Action: lines
      - "smart": slower, more likely to follow ReAct format (for demo)
    """
    def predict(prompt: str, max_new_tokens: Optional[int] = None) -> str:
        # Simulate real inference cost
        time.sleep(latency_ms / 1000.0)

        # Very crude simulation of "model behavior"
        if quality == "smart":
            recent = prompt[-400:].lower()  # look at the tail of the prompt (recent history)

            # Prefer the expression that was in the original goal/question if present
            import re
            calc_match = re.search(r'calc\[([^\]]+)\]', prompt, re.IGNORECASE)
            expr = calc_match.group(1).strip() if calc_match else "3 * 4 + 2"

            if "observation:" in recent:
                # After we got a tool result, conclude with a Final
                # (for the demo we just echo a plausible answer; the real number
                # will have been computed by the actual tool in run_react)
                try:
                    # safe-ish eval for the demo only
                    if all(ch in "0123456789 +*-/(). " for ch in expr):
                        val = eval(expr, {"__builtins__": {}}, {})
                        return f"Thought: The calculation is complete.\nFinal Answer: {val}\n"
                except Exception:
                    pass
                return "Thought: The calculation is complete.\nFinal Answer: The result of the requested operation.\n"

            if "calc[" in prompt.lower() or "action:" in prompt:
                return f"Thought: I need to calculate that.\nAction: calc[{expr}]\n"

            if "lookup[" in prompt.lower() or "crystals" in prompt.lower():
                return "Thought: The story mentions glowing crystals.\nAction: lookup[crystals]\n"

            return "Thought: I have enough information.\nFinal Answer: The crystals hold a surprising amount of energy according to the machine.\n"
        else:
            # fast / lower quality
            if "Thought:" in prompt:
                return "The machine whispered secrets about the crystals. They glow when the machine is near.\n"
            return "Final Answer: Something about energy and crystals.\n"

    predict.__name__ = f"stub_{name}"
    return predict


BACKENDS: Dict[str, Callable[[], Predictor]] = {
    "tiny-lstm": lambda: make_tiny_lstm_predictor(),
    "stub-fast": lambda: make_stub_predictor("fast", latency_ms=30.0, quality="fast"),
    "stub-smart": lambda: make_stub_predictor("smart", latency_ms=120.0, quality="smart"),
}


def timed_predict(predictor: Predictor, prompt: str,
                  max_new_tokens: Optional[int] = None) -> tuple[str, float, float]:
    """Call predictor and return (output, latency_seconds, simulated_tps)."""
    start = time.perf_counter()
    output = predictor(prompt, max_new_tokens=max_new_tokens)
    latency = time.perf_counter() - start

    # Rough token estimate (char / 4 is a common heuristic)
    tokens = max(1, len(output) // 4)
    tps = tokens / latency if latency > 0 else 0.0
    return output, latency, tps


def run_agent_with_backend(backend_name: str, question: str,
                           max_steps: int = 5, verbose: bool = True) -> str:
    """Run the full ReAct agent using the chosen backend. Agent code is untouched."""
    if backend_name not in BACKENDS:
        raise ValueError(f"Unknown backend {backend_name}. Choices: {list(BACKENDS)}")

    print(f"\n[playground] Using backend: {backend_name}")
    predictor = BACKENDS[backend_name]()

    # The exact same call site used by every other prototype.
    # Nothing here knows it is talking to a stub or a real model.
    answer = run_react(
        question=question,
        predictor=predictor,
        tools=TOOLS,
        max_steps=max_steps,
        verbose=verbose,
    )
    return answer


def benchmark_backend(backend_name: str, question: str, runs: int = 5) -> Dict[str, float]:
    """Simple benchmark: run the predictor N times, collect metrics."""
    predictor = BACKENDS[backend_name]()
    latencies = []
    tps_values = []

    print(f"\n[benchmark] {backend_name} × {runs} runs on: {question[:60]}...")

    for i in range(runs):
        out, lat, tps = timed_predict(predictor, question, max_new_tokens=60)
        latencies.append(lat)
        tps_values.append(tps)
        print(f"  run {i+1}: {lat*1000:.1f} ms  ~{tps:.1f} t/s  len={len(out)}")

    return {
        "backend": backend_name,
        "avg_latency_ms": sum(latencies) / len(latencies) * 1000,
        "avg_tps": sum(tps_values) / len(tps_values),
        "runs": runs,
    }


def main():
    parser = argparse.ArgumentParser(description="Local Inference Playground (Proto 5)")
    parser.add_argument("--backend", choices=list(BACKENDS.keys()), default="stub-smart",
                        help="Which Predictor backend to use")
    parser.add_argument("--question", type=str,
                        default="How can Elara measure the power of the glowing crystals?",
                        help="Question to ask the agent")
    parser.add_argument("--max-steps", type=int, default=5)
    parser.add_argument("--benchmark", action="store_true",
                        help="Run a small benchmark instead of a single agent run")
    parser.add_argument("--runs", type=int, default=5,
                        help="Number of runs for --benchmark mode")
    parser.add_argument("--quiet", action="store_true", help="Less verbose ReAct output")
    args = parser.parse_args()

    print("=" * 70)
    print("LOCAL INFERENCE PLAYGROUND + BENCHMARK")
    print("=" * 70)
    print("The ReAct loop, tools, memory, and evaluator are 100% unchanged.")
    print("Only the thing that satisfies `Predictor` changes.")
    print()

    if args.benchmark:
        # Compare a few backends
        results = []
        for b in ["stub-fast", "stub-smart", "tiny-lstm"]:
            try:
                res = benchmark_backend(b, args.question, runs=args.runs)
                results.append(res)
            except Exception as e:
                print(f"  Skipping {b}: {e}")

        print("\n--- Summary ---")
        for r in results:
            print(f"{r['backend']:12s}  "
                  f"avg {r['avg_latency_ms']:.1f} ms   "
                  f"~{r['avg_tps']:.1f} t/s")
        print("\nNotice: the agent code above never changed. Different backends just")
        print("produce different latency/quality trade-offs behind the same interface.")
    else:
        # Single interesting run with the chosen backend
        answer = run_agent_with_backend(
            args.backend,
            args.question,
            max_steps=args.max_steps,
            verbose=not args.quiet,
        )
        print(f"\nFinal answer from {args.backend}: {answer}")

    # ------------------------------------------------------------------
    # WHAT YOU JUST SAW
    # ------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("WHAT YOU JUST SAW")
    print("=" * 70)
    print("""
1. The Predictor contract (`prompt → text`) is the only thing the agent stack
   ever sees. mini_react.py, memory.py, trajectory_evaluator.py, etc. have zero
   knowledge of torch, Ollama, or any specific model.

2. Swapping backends is just choosing a different factory:
      predictor = BACKENDS["stub-smart"]()
      # or
      predictor = from_tiny_llm(model)
   Then pass the same predictor object to run_react / evaluators.

3. Real local inference (Ollama, llama.cpp, MLX, etc.) would plug in exactly
   the same way. The "stub-*" backends here are only for teaching the seam
   without requiring you to install 800 MB of GGUF files.

4. Metrics (latency, tokens/s) are trivial to add at the Predictor boundary.
   In a real playground you would also measure GPU memory, KV cache size,
   quantization impact, etc.

5. Because Proto 4 (the evaluator) also only talks to Predictors, you can
   now run the trajectory evaluator against "stub-smart" vs "tiny-lstm" and
   see how backend quality affects agent success rate.

Try these experiments:
- python llm/local_inference_playground.py --backend stub-fast --benchmark
- python llm/local_inference_playground.py --backend tiny-lstm
- Change the stub to return better/worse ReAct formatting and watch the
  reliability lab or evaluator numbers move.
- Later (Proto 6/7) you will actually produce a better backend and plug it in
  here without touching a single line of agent code.

This is how the collection stays small while becoming polyglot and realistic.
""")

    print("The seam works. The agent logic is free.")


if __name__ == "__main__":
    main()
