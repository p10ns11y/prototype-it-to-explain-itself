# Prototype Roadmap — 9 Ideas to Explain Agents, Reliability, Memory & Beyond

This document explicitly stores the curated list of 9 prototype ideas (plus supporting tasks) that were added to the live todo list during the recent session. Previously, the full details with concepts, features, value propositions, extensions, and recommendation table existed only in the agent's todo state and session transcripts — not as a committed document in the workspace.

**Source of the list**: User-provided curated list (ended with "add these to todo list"). Immediately turned into trackable todos: `review-prototype-ideas`, `choose-starting-prototype`, and `proto-1-mini-react` through `proto-9-multi-agent`.

**Development principles established for the whole sequence** (from session):
- Extend the existing Tiny LLM prototype as the base (user chose this path) rather than standalone or bloated new ones.
- Use modular abstractions (e.g. the `Predictor` narrow waist: `prompt → text`) so concepts layer on top, remain minimal, self-explanatory, and reusable.
- Keep **all** prototypes small; code + concepts must flow intuitively.
- High-standard readability: short words, active voice, one clear thought per sentence ("Orwell's English").
- Always prefer pictorial/visual explanations (Mermaid flowcharts, tables, step traces, "WHAT YOU JUST SAW" blocks). Text only when it cannot be avoided.
- Prototypes can (and should) be **polyglot** where it teaches the concept better and mirrors real production usage for that slice. The Predictor abstraction is the seam that enables swapping brains (TinyLLM → local models → future) and crossing language boundaries without rewriting control logic.
- Interconnect everything: each new prototype reuses prior artifacts (via imports or thin boundaries) so the collection feels like one coherent, growing explainer rather than isolated demos.
- The "tiny + hold the whole world in your head" constraint: Elara story universe, no external deps/network for core teaching versions, mock tools that are deterministic and inspectable.

## Current Prototypes (Implemented)

See also the live state in [llm/README.md](llm/README.md) (Sequencing section) and root [README.md](README.md) ("Current Prototypes").

- **Base**: Tiny LLM fundamentals (`llm/simple_llm_prototype.py`) — character-level LSTM, full train + autoregressive generate loop, `--show-probs`, sampling strategies doc.
- **Abstraction**: `Predictor` (`llm/tiny_predictor.py`) — the stable `text_in → text_out` contract. Enables all higher layers and future backends.
- **Proto 1 (Highest Recommendation)**: Mini ReAct Agent Loop (`llm/mini_react.py`) — Think → Act → Observe with tools (`calc`, `lookup` in Elara universe). Visible traces, parser, prompt builder with `extra_context` hook, model persistence, educational blocks. (Also `llm/architecture.md` for interconnections.)
- **Proto 2**: Tool-Use Reliability Lab (`llm/tool_reliability_lab.py`) — Batch/scorable harness over the ReAct loop + tools. Categorized cases (direct, ambiguous, no-tool, error-injection), success reporting, tool-call capture + arg scoring. Used to quantify and surface format/tool-use failures with the tiny model (and to exercise the machinery via temporary syntax forcing + few-shot).
- **Proto 3**: Memory module + explainer (`llm/memory.py` + `llm/memory_explainer.py`) — `ShortTermMemory` (sliding window), `LongTermMemory` (simple facts + cheap keyword-overlap retrieval — deliberately no vector DB to stay tiny/dependency-free), `format_memories`, injection via `extra_context` on `build_prompt` / `run_react`. Full demo loop.
- **Proto 4**: Agent Trajectory Evaluator (`llm/trajectory_evaluator.py`) — score many runs on outcome + process + weak self-judge using the tiny model. Produces reports so iteration becomes measurable.
- **Proto 5**: Local Inference Playground (`llm/local_inference_playground.py`) — multiple backends (real tiny + stubs) behind the identical Predictor contract. Live metrics, CLI, benchmark. All upper layers (ReAct, memory, evaluator) unchanged.
- **Proto 6**: Synthetic Data Factory (`llm/synthetic_data_factory.py`) — generate trajectories, self-critique + filter the good ones, turn them into training data, and optionally actually improve the model. The self-improvement flywheel made tiny and visible.
- **Proto 7**: Typed Agent Workflow (`llm/typed_agent_workflow.py`) — strict types + state machine for ReAct steps so many invalid executions become impossible or explicit errors. Python version of the reliability-by-construction pattern.
- **Proto 8**: Human-in-the-Loop Agent Desktop (`llm/human_in_loop.py`) — terminal oversight UI with low-confidence surfacing, human approve/edit/inject, full intervention audit log, and multiple autonomy modes.
- **Proto 9**: Multi-Agent Debate / Collaboration (`llm/multi_agent_debate.py`) — tiny orchestrator + specialist agents + critic + synthesis. The capstone that composes the entire previous stack.

Supporting: `llm/sampling-strategies.md`, `llm/architecture.md` (layered diagrams + per-module control/data flows), README updates, git commits of the increments.

**Progress note**: All 9 prototypes complete. The collection now demonstrates next-token prediction, control loops, reliability measurement, memory, evaluation, backend swapping, self-improvement, typed safety, human oversight, and multi-agent collaboration — all kept tiny, visual, interconnected through the Predictor seam, and runnable from a single short story and a 150k-parameter LSTM.

**Hosted hub (2026)**: Single-file **[Reflect and Attempt Quizz](reflect-and-attempt-quizz.html)** (spaced repetition) + **[Knowledge Reference Site](site/)** (Astro static site from monorepo markdown, Mermaid, Practice CTAs). See root [README.md](README.md) and [site-deploy.md](site-deploy.md).

## The 9 Prototype Ideas (Original Curated List + Todo Mapping)

Each entry below combines the user's original description (core concept, what to build, features, why valuable, extensions) with the todo id, priority/sequencing rationale, and suggested production-mirroring stack from the planning session. The "Idea (from your list)" names and todo ids match what was tracked.

| Priority | Todo ID                    | Idea                              | Core Concept                              | What the Prototype Does (key features) | Why Valuable | Extensions | Suggested Stack (production mirror) | Builds On |
|----------|----------------------------|-----------------------------------|-------------------------------------------|----------------------------------------|--------------|------------|-------------------------------------|-----------|
| 1 (done, highest rec) | proto-1-mini-react | Mini ReAct Agent Loop | Agent Architectures & Control Loops + Tool Use | CLI agent: Think→Act→Observe loop over TinyLLM (or Ollama via Predictor). 2–3 tools (e.g. Calculator, Wikipedia-style lookup (mock), File reader). Proper parsing. Shows the **full reasoning trace** at every step. | This is the foundation of almost every modern agent. Building it from scratch gives deep intuition about where agents succeed and fail. The control loop (not just the LLM) is what makes it an "agent". | Add memory; add planning step before acting; add self-reflection ("Did this action help?"). | Python (PyTorch) — matches current LLM prototype. (Later prototypes deliberately diverge.) | TinyLLM + new Predictor abstraction (narrow waist) |
| 2 (done) | proto-2-tool-reliability | Tool-Use Reliability Lab | Tool Use & Function Calling (Reliably) | Controlled test harness. Define tools with strict schemas. Test prompting strategies (ReAct vs Function Calling format). Inject failures (tool returns error, wrong args) and measure recovery. Track success rate across 50–100 test cases. Batch/silent execution + structured reports (overall rate, per-category, per-case details + actual tool calls captured). | Most production agent failures come from bad tool use / format drift. This prototype teaches you how to make tool calling robust by making the failure modes **visible and quantifiable**. | Add constrained generation (outlines/guidance); compare different models on the same suite. | Python (or small harness + any backend via Predictor). | ReAct + its tools + Predictor (reuses `run_react` silently) |
| 3 (done) | proto-3-memory-chatbot | Memory-Augmented Chatbot (Memory module) | Memory (short-term + long-term retrieval) | Tiny, dependency-free memory module. Short-term: fixed-size sliding window of recent turns. Long-term: simple fact store + cheap keyword-overlap retrieval (no vector DB — keeps it readable/tiny). `format_memories(...)` produces a clean prompt block. Injectable via `extra_context` seam. `memory_explainer.py` shows the full ReAct loop with memory visible in prompts and across goals. | Agents without memory are stateless and repeat mistakes or forget facts. This makes the two common layers (STM vs LTM + retrieval) concrete and shows exactly how they change the prompt the model sees. | Summaries / compression; entity consolidation; user profiles; later swap in real vector store while keeping the same interface. | Python (easy to start); later Rust/perf if needed. | ReAct trajectory + new tiny `memory.py` (hooked into prompt builder) |
| 4 (done) | proto-4-trajectory-eval | Agent Trajectory Evaluator | Evaluation, scoring, and improvement loops | Define tasks + explicit success criteria. Run many agent episodes on the same questions. Score trajectories on outcome + process (steps, tool correctness, format adherence). Optional: use the tiny model itself as a weak LLM-as-judge. Produce reports, diffs, and (later) regression suites. | Turns one-off demos into something you can **iterate on with data**. Critical for production agent development — you need to know if a prompt tweak or new memory strategy actually helps. | 20–30 task benchmark set; regression test harness; human preference collection; automated prompt search. | Python (excellent for evals, reporting, LLM-as-judge orchestration). | Multiple runs of ReAct + prior scoring primitives from the Reliability Lab |
| 5 (done) | proto-5-local-inference | Local Inference Playground + Benchmark | Swapping the "brain" while keeping agent logic identical | Multi-backend support behind the same Predictor interface (Ollama, llama.cpp, MLX, etc.). Live metrics (tokens/s, memory, latency, quantization impact). Chat UI or rich CLI with perf overlay. Side-by-side comparisons. | "Our toy model" vs real local models — while the ReAct / memory / eval layers stay 100% unchanged. Makes the abstraction seam real and shows practical trade-offs. | Speculative decoding; KV cache visualization; tool-calling benchmarks per backend; streaming traces. | Mix: Python CLI harness + llama.cpp / MLX / Ollama (real local stacks that teams actually ship). | The Predictor seam + all prior agent pieces (ReAct, tools, memory, evaluator) |
| 6 (done) | proto-6-synthetic-data | Synthetic Data Factory | Closing the data flywheel / self-improvement | Generate prompts (or goals) → run agent to produce trajectories/responses (with self-critique or judge filtering) → filter high-quality ones → use as training data to fine-tune or improve the smaller model (e.g. the TinyLLM). | Real production pipelines improve models with their own agent outputs. This prototype makes the "use good trajectories to teach better Thought/Action format + domain knowledge" loop visible and runnable end-to-end. | Preference data (for DPO etc.); trajectory filtering by evaluator scores; distillation into even smaller models; curriculum generation. | Python (data gen + fine-tuning scripts) or JAX/TF if we want to show alternatives to PyTorch. | Good trajectories from the Evaluator (proto-4) + the ReAct/Memory system |
| 7 (done) | proto-7-typed-workflow | Typed Agent Workflow | Reliability by construction (types + state machines) | Agent workflows expressed so that invalid states / bad sequences are unrepresentable at the type level. Strong modeling of steps, observations, final answers. | Many agent bugs are "it took an illegal path." Typed/state-machine versions make whole classes of errors impossible before any LLM call. | Verifiable execution traces; compile-time or runtime guards; integration with the evaluator. | **Rust** (or strict Python + Pydantic + explicit state machine). Rust makes the "invalid states unrepresentable" feeling visceral. | All prior (Predictor + tools + memory + evaluator) |
| 8 (done) | proto-8-human-loop | Human-in-the-Loop Agent Desktop | Oversight, intervention, and mixed autonomy | Desktop (or small web) app that runs the agent, surfaces low-confidence steps / tool calls / plans, lets a human approve/edit/override, and logs the interventions. Different autonomy modes. | Real production agents are rarely fully autonomous at first. This teaches the UX, logging, and control patterns for human supervision. | Escalation rules; audit trails; "what the agent was about to do" previews; multi-turn oversight sessions. | Rust + Tauri (or Python Textual / NiceGUI / small web frontend). Choose the stack that best illustrates real desktop oversight UX. | The ReAct loop + evaluator + explicit low-confidence / intervention hooks |
| 9 (done) | proto-9-multi-agent | Multi-Agent Debate / Collaboration | Scaling via collaboration and debate | Orchestrator + specialist agents (or debaters) that propose, critique, and converge on answers for hard tasks. Shared memory / blackboard or structured hand-offs. | Single agents plateau. Debate / mixture-of-agents patterns are a known way to get better performance on complex reasoning without a bigger single model. | Role specialization; voting / ranking; shared long-term memory; hierarchical teams. | Python for the orchestration layer (common pattern); or a small actor-style runtime in another language for the agents themselves. | Predictor + tools + memory + evaluator (each "agent" can be a configured ReAct + memory instance) |

**Recommendation table / rationale** (condensed from session): Start with 1 (highest immediate leverage for understanding agents). 2 quantifies the painful reality the first demo reveals. 3 adds the missing state layer everyone talks about. 4 turns the whole thing into an engineering discipline instead of demos. 5–6 are high-ROI "make it real / improve it" steps that still stay in the same conceptual universe. 7–9 deliberately cross into production-grade concerns and languages so the collection as a whole teaches both the ideas *and* the stacks people actually use for them.

Each step adds **one** clear idea and stays small because it composes on top of prior artifacts.

### Implementation files (protos 4–9)

| Proto | File | Notes |
|-------|------|-------|
| 4 | `llm/trajectory_evaluator.py` | Reuses `run_react(..., return_trajectory=True)`; Elara tasks + heuristic + weak self-judge |
| 5 | `llm/local_inference_playground.py` | Real tiny-lstm + stub backends behind `Predictor`; CLI + benchmark |
| 6 | `llm/synthetic_data_factory.py` | Evaluator + self-critique → filtered corpus → optional continue-training |
| 7 | `llm/typed_agent_workflow.py` | Frozen types + legal-transition validator; comments show Rust ideal |
| 8 | `llm/human_in_loop.py` | Terminal edition; manual / ask-on-low-confidence / run-then-review modes |
| 9 | `llm/multi_agent_debate.py` | Orchestrator + specialists + critic + synthesis; capstone |

## How the Roadmap Was Used in the Session

- Full list + concepts + table added to todo list as trackable tasks right at the start of the focused work.
- Plan mode activated to explore the TinyLLM codebase, design the Predictor seam, and produce `plan.md` (captured in the agent's session storage at the time, not written to workspace git).
- User selected "extend the existing Tiny LLM prototype" (one of the three follow-up options) + prioritize the sequence.
- Work proceeded incrementally: Predictor → Proto 1 → Proto 2 → Proto 3 → … through Proto 9 (multi-agent capstone), with architecture doc + README sync at each step.
- All changes followed the visual-first, small-prototype, plain-English, reuse-via-abstraction rules.
- The `llm/README.md` "Sequencing — What Comes Next" and root README "Current Prototypes" reflect all 9 implemented prototypes.

## Next Steps (suggested)

1. Use the **Reflect and Attempt Quizz** and **Knowledge Reference Site** for active recall over the full collection.
2. Re-run any prototype (`python llm/mini_react.py`, `tool_reliability_lab.py`, etc.) after changes to keep the "it explains itself" loop alive.
3. Optional extensions from the table above (regression suites, real Ollama backends, Rust typed workflow, Tauri desktop UI, etc.).
4. Keep this roadmap + the llm/root READMEs in sync when adding new teaching artifacts.

---

Build the smallest thing that still carries the heart of the idea. Then let the prototype (and this roadmap) do the explaining.

(Recovered 2026-06-10; implementation status updated when all 9 prototypes landed.)
