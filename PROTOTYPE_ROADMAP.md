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

Supporting: `llm/sampling-strategies.md`, `llm/architecture.md` (layered diagrams + per-module control/data flows), README updates, git commits of the increments.

**Progress note**: Prototypes 1–3 (plus Predictor + architecture) complete enough for the "small self-explanatory" stage. Proto 2 and 3 were explicitly reviewed as done before moving on. Next natural step per the original sequence: Proto 4 (Trajectory Evaluator).

## The 9 Prototype Ideas (Original Curated List + Todo Mapping)

Each entry below combines the user's original description (core concept, what to build, features, why valuable, extensions) with the todo id, priority/sequencing rationale, and suggested production-mirroring stack from the planning session. The "Idea (from your list)" names and todo ids match what was tracked.

| Priority | Todo ID                    | Idea                              | Core Concept                              | What the Prototype Does (key features) | Why Valuable | Extensions | Suggested Stack (production mirror) | Builds On |
|----------|----------------------------|-----------------------------------|-------------------------------------------|----------------------------------------|--------------|------------|-------------------------------------|-----------|
| 1 (done, highest rec) | proto-1-mini-react | Mini ReAct Agent Loop | Agent Architectures & Control Loops + Tool Use | CLI agent: Think→Act→Observe loop over TinyLLM (or Ollama via Predictor). 2–3 tools (e.g. Calculator, Wikipedia-style lookup (mock), File reader). Proper parsing. Shows the **full reasoning trace** at every step. | This is the foundation of almost every modern agent. Building it from scratch gives deep intuition about where agents succeed and fail. The control loop (not just the LLM) is what makes it an "agent". | Add memory; add planning step before acting; add self-reflection ("Did this action help?"). | Python (PyTorch) — matches current LLM prototype. (Later prototypes deliberately diverge.) | TinyLLM + new Predictor abstraction (narrow waist) |
| 2 (done) | proto-2-tool-reliability | Tool-Use Reliability Lab | Tool Use & Function Calling (Reliably) | Controlled test harness. Define tools with strict schemas. Test prompting strategies (ReAct vs Function Calling format). Inject failures (tool returns error, wrong args) and measure recovery. Track success rate across 50–100 test cases. Batch/silent execution + structured reports (overall rate, per-category, per-case details + actual tool calls captured). | Most production agent failures come from bad tool use / format drift. This prototype teaches you how to make tool calling robust by making the failure modes **visible and quantifiable**. | Add constrained generation (outlines/guidance); compare different models on the same suite. | Python (or small harness + any backend via Predictor). | ReAct + its tools + Predictor (reuses `run_react` silently) |
| 3 (done) | proto-3-memory-chatbot | Memory-Augmented Chatbot (Memory module) | Memory (short-term + long-term retrieval) | Tiny, dependency-free memory module. Short-term: fixed-size sliding window of recent turns. Long-term: simple fact store + cheap keyword-overlap retrieval (no vector DB — keeps it readable/tiny). `format_memories(...)` produces a clean prompt block. Injectable via `extra_context` seam. `memory_explainer.py` shows the full ReAct loop with memory visible in prompts and across goals. | Agents without memory are stateless and repeat mistakes or forget facts. This makes the two common layers (STM vs LTM + retrieval) concrete and shows exactly how they change the prompt the model sees. | Summaries / compression; entity consolidation; user profiles; later swap in real vector store while keeping the same interface. | Python (easy to start); later Rust/perf if needed. | ReAct trajectory + new tiny `memory.py` (hooked into prompt builder) |
| 4 (pending) | proto-4-trajectory-eval | Agent Trajectory Evaluator | Evaluation, scoring, and improvement loops | Define tasks + explicit success criteria. Run many agent episodes on the same questions. Score trajectories on outcome + process (steps, tool correctness, format adherence). Optional: use the tiny model itself as a weak LLM-as-judge. Produce reports, diffs, and (later) regression suites. | Turns one-off demos into something you can **iterate on with data**. Critical for production agent development — you need to know if a prompt tweak or new memory strategy actually helps. | 20–30 task benchmark set; regression test harness; human preference collection; automated prompt search. | Python (excellent for evals, reporting, LLM-as-judge orchestration). | Multiple runs of ReAct + prior scoring primitives from the Reliability Lab |
| 5 (pending) | proto-5-local-inference | Local Inference Playground + Benchmark | Swapping the "brain" while keeping agent logic identical | Multi-backend support behind the same Predictor interface (Ollama, llama.cpp, MLX, etc.). Live metrics (tokens/s, memory, latency, quantization impact). Chat UI or rich CLI with perf overlay. Side-by-side comparisons. | "Our toy model" vs real local models — while the ReAct / memory / eval layers stay 100% unchanged. Makes the abstraction seam real and shows practical trade-offs. | Speculative decoding; KV cache visualization; tool-calling benchmarks per backend; streaming traces. | Mix: Python CLI harness + llama.cpp / MLX / Ollama (real local stacks that teams actually ship). | The Predictor seam + all prior agent pieces (ReAct, tools, memory, evaluator) |
| 6 (pending) | proto-6-synthetic-data | Synthetic Data Factory | Closing the data flywheel / self-improvement | Generate prompts (or goals) → run agent to produce trajectories/responses (with self-critique or judge filtering) → filter high-quality ones → use as training data to fine-tune or improve the smaller model (e.g. the TinyLLM). | Real production pipelines improve models with their own agent outputs. This prototype makes the "use good trajectories to teach better Thought/Action format + domain knowledge" loop visible and runnable end-to-end. | Preference data (for DPO etc.); trajectory filtering by evaluator scores; distillation into even smaller models; curriculum generation. | Python (data gen + fine-tuning scripts) or JAX/TF if we want to show alternatives to PyTorch. | Good trajectories from the Evaluator (proto-4) + the ReAct/Memory system |
| 7 (pending) | proto-7-typed-workflow | Typed Agent Workflow | Reliability by construction (types + state machines) | Agent workflows expressed so that invalid states / bad sequences are unrepresentable at the type level. Strong modeling of steps, observations, final answers. | Many agent bugs are "it took an illegal path." Typed/state-machine versions make whole classes of errors impossible before any LLM call. | Verifiable execution traces; compile-time or runtime guards; integration with the evaluator. | **Rust** (or strict Python + Pydantic + explicit state machine). Rust makes the "invalid states unrepresentable" feeling visceral. | All prior (Predictor + tools + memory + evaluator) |
| 8 (pending) | proto-8-human-loop | Human-in-the-Loop Agent Desktop | Oversight, intervention, and mixed autonomy | Desktop (or small web) app that runs the agent, surfaces low-confidence steps / tool calls / plans, lets a human approve/edit/override, and logs the interventions. Different autonomy modes. | Real production agents are rarely fully autonomous at first. This teaches the UX, logging, and control patterns for human supervision. | Escalation rules; audit trails; "what the agent was about to do" previews; multi-turn oversight sessions. | Rust + Tauri (or Python Textual / NiceGUI / small web frontend). Choose the stack that best illustrates real desktop oversight UX. | The ReAct loop + evaluator + explicit low-confidence / intervention hooks |
| 9 (pending) | proto-9-multi-agent | Multi-Agent Debate / Collaboration | Scaling via collaboration and debate | Orchestrator + specialist agents (or debaters) that propose, critique, and converge on answers for hard tasks. Shared memory / blackboard or structured hand-offs. | Single agents plateau. Debate / mixture-of-agents patterns are a known way to get better performance on complex reasoning without a bigger single model. | Role specialization; voting / ranking; shared long-term memory; hierarchical teams. | Python for the orchestration layer (common pattern); or a small actor-style runtime in another language for the agents themselves. | Predictor + tools + memory + evaluator (each "agent" can be a configured ReAct + memory instance) |

**Recommendation table / rationale** (condensed from session): Start with 1 (highest immediate leverage for understanding agents). 2 quantifies the painful reality the first demo reveals. 3 adds the missing state layer everyone talks about. 4 turns the whole thing into an engineering discipline instead of demos. 5–6 are high-ROI "make it real / improve it" steps that still stay in the same conceptual universe. 7–9 deliberately cross into production-grade concerns and languages so the collection as a whole teaches both the ideas *and* the stacks people actually use for them.

Each step adds **one** clear idea and stays small because it composes on top of prior artifacts.

## How the Roadmap Was Used in the Session

- Full list + concepts + table added to todo list as trackable tasks right at the start of the focused work.
- Plan mode activated to explore the TinyLLM codebase, design the Predictor seam, and produce `plan.md` (captured in the agent's session storage at the time, not written to workspace git).
- User selected "extend the existing Tiny LLM prototype" (one of the three follow-up options) + prioritize the sequence.
- Work proceeded incrementally: Predictor → Proto 1 (ReAct + traces + fixes) → Proto 2 (Reliability Lab + measurement + forcing hack for the weak model + commit) → review complete → Proto 3 (Memory + explainer + integration + architecture doc + polish + commit).
- All changes followed the visual-first, small-prototype, plain-English, reuse-via-abstraction rules.
- The `llm/README.md` "Sequencing — What Comes Next" and root README "Current Prototypes" were kept in sync (they currently reflect up to Proto 3 + the first 4 in the sequence list).

## Where the "Lost" Session Details Lived (Hunt Results)

- Agent's per-project memory: `~/.grok/memory/prototype-it-to-explain-itself-ffb2c9e7/sessions/2026-06-10-interval-019eae0e.md` (full flush of decisions, technical context, problems/solutions, and progress through Proto 3; references the addition of the 9 to todos but the body of the original list lived in the chat that preceded the flush).
- Captured plan-mode artifact (the concrete execution plan after choosing to extend TinyLLM and sequence the 9): `~/.grok/sessions/.../llm/019eae0e-.../plan.md` (contains the full recommended order table, implementation steps, verification, trade-offs, and the sequencing section that maps the 9).
- Raw chat transcripts / updates / resources_state for the session dirs under `~/.grok/sessions/%2Fhome%2Fsustainableabundance%2FWork%2Fresearch%2Faiml%2Fprototype-it-to-explain-itself/...` (the original user message with the detailed 1–9 list + "add these to todo list" was in the chat_history.jsonl; the todo_write call and subsequent reasoning are also there).
- Project workspace `llm/README.md` (partial sequencing list + "See the todo list..." pointer) and root `README.md` (high-level current prototypes).
- The workspace itself had **no** `TODO.md`, `ROADMAP.md`, `PROTOTYPES.md`, or equivalent committed document containing the full 9 with details — that was the gap the user noted.

This `PROTOTYPE_ROADMAP.md` now makes the full curated list + status + principles a first-class, committed, human-readable artifact in the workspace (alongside the code).

## Next Steps (suggested)

1. Mark / review the next todo (proto-4 Trajectory Evaluator) when ready.
2. Keep extending the Predictor-based pieces for 4–6 while staying tiny and visual.
3. When crossing to 7–9, create small subdirs or build instructions for the new stacks (Rust, Tauri, etc.) but continue to document how they plug into the same conceptual seams.
4. Update this roadmap + the llm/root READMEs as each prototype lands.
5. (Optional) Re-run `python llm/tool_reliability_lab.py` or the memory explainer after changes to keep the "it explains itself" loop alive.

---

Build the smallest thing that still carries the heart of the idea. Then let the prototype (and this roadmap) do the explaining.

(Recovered and written explicitly 2026-06-10 from session memory, plan.md, chat artifacts, and current workspace state.)
