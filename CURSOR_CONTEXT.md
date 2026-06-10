# CURSOR CONTEXT — Prototype It To Explain Itself (Knowledge Hub + 9 Prototypes)

**Project**: `prototype-it-to-explain-itself` (research/aiml)  
**Goal**: Build the smallest runnable thing that makes an idea visible so the code + docs explain themselves.  
**Current phase**: All 9 prototypes complete. Focus is on the hosted "Prove it that you learned it Hub" (single-file SRS tester + Astro reference site) deployed together under the exact Cloudflare Pages project name `prototype-it-to-explain-itself`.

**HOW TO RESUME IN CURSOR**:  
Paste the **entire content** of this `CURSOR_CONTEXT.md` as the very first message in a new chat (or attach it). Then say what you want to do next (e.g. "run a full local test of the site + tester", "prepare the GitHub + CF Pages connect", "add more concept pages", "fix X", "commit the current changes").

---

## Hard Constraints (User-Verbatim, Never Violate)

- **Site / project name**: Exactly `prototype-it-to-explain-itself` (Cloudflare Pages project, URLs, wrangler name, links, everything).
- **Package manager**: **Always use pnpm**. Never npm/yarn. Enforced in root README, site/package.json (packageManager + engines), site-deploy.md, site/README.md.
- **Theme (exact)**: "Use 50 shades of white as general theme for the site and 50 shades of gray for texts". "even CTAs must use white and gray and some variations of red allowed".
  - Backgrounds/surfaces: zinc-50 (#fafafa), white (#ffffff), zinc-100 (#f4f4f5).
  - Text: zinc-900 (#18181b) primary/headings, zinc-700 (#3f3f46) body, zinc-600/500 muted.
  - CTAs (including all "Practice / Test / Open the Tester" links): `bg-white border border-zinc-300 text-zinc-800 hover:bg-zinc-100 hover:border-zinc-400` + red-700 (`#b91c1c`) allowed on hover/emphasis only. See global.css for the attribute selector rule on `/reflect-and-attempt-quizz.html` and the PracticeCTA component.
- **Mandatory doc updates** (after every prototype or significant architectural/site change):
  1. Root `README.md` — "Current Prototypes" list (one concise bullet).
  2. `llm/README.md` — new section for the prototype + update "Sequencing — What Comes Next".
  3. `llm/architecture.md` — layered diagram / interconnections table if affected + runtime notes.
  4. `PROTOTYPE_ROADMAP.md` — status + any new notes.
  - Then commit + push.
- **Mermaid rules** (to prevent GitHub render parse errors like "Expecting 'SEMI'... got 'NODE_STRING'"):
  - `flowchart TD` (or LR).
  - Nodes with `<br/>`/special chars: use `["text<br/>here"]`.
  - Edge labels with `[`, `]`, `:`, punctuation: must be double-quoted: `-->|"label with [brackets]"|`.
  - Minimal subgraphs/classDefs. See architecture.md for the full list.
- **Tester filename**: `reflect-and-attempt-quizz.html` (was renamed from knowledge-reflection-tester.html; all references updated).
- **Tester + Site integration**: Single portable HTML (vanilla + Tailwind CDN + localStorage SRS) + Astro MDX reference site. Bidirectional: tester supports `?concept=xxx&review=1`, concept MDX pages use `<PracticeCTA concept="..." />`.
- **Deployment unity**: `site/` postbuild (`cp ../reflect-and-attempt-quizz.html ./dist/`) ensures the tester ships in the same Pages project. Available at `/reflect-and-attempt-quizz.html`.

---

## What Has Been Built (Status)

### 9 Prototypes (all implemented, in `llm/`)
1. Mini ReAct (mini_react.py) — Think→Act→Observe + tools + traces + persistence.
2. Tool-Use Reliability Lab (tool_reliability_lab.py) — batch harness, success rates, format/tool scoring.
3. Memory (memory.py + memory_explainer.py) — STM (sliding) + LTM (keyword facts) + `extra_context` injection.
4. Trajectory Evaluator (trajectory_evaluator.py) — many runs + outcome/process + weak LLM-judge scoring.
5. Local Inference Playground (local_inference_playground.py) — same ReAct/memory/eval code against real tiny-lstm or stub backends; metrics + benchmark.
6. Synthetic Data Factory (synthetic_data_factory.py) — generate → self-critique/filter → mixed training corpus → optional improve_model.
7. Typed Agent Workflow (typed_agent_workflow.py) — dataclasses + validator for legal ReAct state transitions (reliability by construction).
8. Human-in-the-Loop (human_in_loop.py) — terminal oversight modes, low-confidence surfacing, intervention audit log.
9. Multi-Agent Debate (multi_agent_debate.py) — orchestrator + specialists + critic + synthesis (capstone composing 1-8 via Predictor seam).

**Core seam**: `Predictor` (tiny_predictor.py) — stable `prompt → text` narrow waist. All higher layers are unchanged when you swap the backend.

Base: character-level LSTM (~150k params) on a short repeated story (Elara universe) so everything fits in one head.

See:
- `PROTOTYPE_ROADMAP.md` (full original list + rationale table + "how the roadmap was used")
- `llm/README.md` (Sequencing section + per-prototype run notes)
- `llm/architecture.md` (layered diagram + interconnections)

### The "Prove it that you learned it Hub" (Knowledge Hub)
- **Tester**: `reflect-and-attempt-quizz.html` (root). 13+ high-quality items (reflection + MCQ) covering the Predictor, ReAct, memory, evaluator, synthetic data, typed workflows, HIL, multi-agent, etc. Spaced repetition (SM-2 style interval/ease/due in localStorage). Modal review flow. Keyboard support (guarded against inputs). `getDocsLinkForConcept` + DOCS_BASE for "Read full explainer". Title: "Reflect and Attempt Quizz • Prototype It To Explain Itself".
- **Reference Site**: `site/` — Astro (currently ^6 with mdx + tailwind; pure static output). MDX pages under `src/pages/concepts/` (llm-architecture, llm-readme, sampling-strategies, prototype-roadmap, index). Uses DocsLayout (zinc theme, mermaid neutral). PracticeCTA component emits the correct white/gray + red-hover links with `?concept=...&review=1`. Postbuild + prebuild both ensure the tester HTML is present for dev and dist.
- **Theme implementation**: global.css (custom zinc-50/white surfaces, zinc-900/700/600/500 text, explicit .prose, .mermaid, header rules). CTAs forced via classes on PracticeCTA + attribute selector for the tester link. No blue remnants.
- **wrangler / CF**: `site/wrangler.toml` has `name = "prototype-it-to-explain-itself"`, **no [site]** section (the deprecated Workers Sites key was the root cause of the long "Processing wrangler.toml ... defaulting to workers-site" + repeated ENOENT scandir `dist/_worker.js` errors). Comments in the file explain the history. Root `wrangler.toml` is legacy.
- **site-deploy.md + site/README.md**: Full instructions for GitHub dashboard connect (Root directory = `site`, Build = `pnpm install && pnpm build`, Output = `dist`). Local: `pnpm build && pnpm preview` (recommended for styles) or `wrangler pages dev dist`. postbuild is documented.
- **Astro config**: `site: 'https://prototype-it-to-explain-itself.pages.dev'`, `output: 'static'`, no cloudflare adapter (pure static chosen after the v4/v5 adapter _worker.js pain for reliable wrangler dev + Tailwind asset serving).

**Dist currently contains** the tester (postbuild succeeded on last build).

---

## Recent History / Last Work (for continuity)

- Completed prototypes 5-9 one-by-one, with mandatory README/architecture/PROTOTYPE_ROADMAP updates + commits.
- Fixed (in order of user reports):
  - Mermaid parse errors on combined nodes + bracket labels (split edges, quoted labels).
  - ImportError on `load_model` (centralized to `mini_react` for persistence helpers).
  - Filter keeping 0 items in synthetic factory (lowered default min_score, outcome_success fallback, --min-score flag).
  - Keyboard bug in tester (space/Enter revealing while typing in textarea/input — added guard).
  - pnpm build ERR_PACKAGE_PATH_NOT_EXPORTED on astro@4 + cloudflare (bumped astro + mdx/tailwind; later went pure static).
  - Long wrangler ENOENT on _worker.js (removed [site] from wrangler.toml everywhere + docs explanation).
  - Unstyled site in wrangler dev (removed adapter for pure static, strengthened global.css with zinc prose/CTA rules, prebuild+postbuild).
  - Rename tester file + all cross-references.
  - Exact theme (50 white/gray + CTA rules + red allowed on hover).
  - postbuild auto-include of tester.
  - Site name everywhere.
- Last big commit: `ae07382` "feat(knowledge-hub): bugfix + Cloudflare-ready Knowledge Reflection Tester + Astro site/ ..."
- **Current git state** (as of this context file creation): master, ahead of origin only by uncommitted work. `git status` shows modifications to READMEs, site/ files (css, components, layouts, pages, package.json, astro.config, wrangler.toml), llm docs, site-deploy.md, the rename (D old + new file), and ?? HW5.pdf. These are the final theme + polish + CF prep changes. Review them and commit before big new branches if desired.

---

## Key Commands (Always pnpm)

From repo root:
- Prototypes: `python llm/<file>.py --help` (most have good examples in their "WHAT YOU JUST SAW" or main).

From `site/`:
```bash
pnpm install
pnpm dev                 # (prebuild copies tester to public/)
pnpm build               # (prebuild + build + postbuild copies tester to dist/)
pnpm preview             # best for verifying styles + tester presence locally
pnpm wrangler pages dev dist   # exact CF Pages emulation (after build)
```

Deployment (GitHub + CF Pages):
- Dashboard: Connect repo → Root directory: `site` → Build command: `pnpm install && pnpm build` → Output: `dist`
- Name of the Pages project must be exactly `prototype-it-to-explain-itself`.

---

## Critical File Map

- `reflect-and-attempt-quizz.html` — the SRS tester (single file, all logic + data + Tailwind CDN + FontAwesome). Key functions: `updateItemAfterReview`, `loadState`/`saveState`, `revealAnswer`, `getDocsLinkForConcept`, keydown guard.
- `site/src/styles/global.css` — the authoritative light zinc white/gray theme + CTA rules (attribute selector + .prose overrides).
- `site/src/components/PracticeCTA.astro` — reusable white/gray CTA (used in MDX).
- `site/src/layouts/DocsLayout.astro` — body/header/footer zinc, mermaid init.
- `site/package.json` — scripts (prebuild/predev + postbuild for tester copy), pnpm engines, current astro 6 + mdx/tailwind (no cloudflare adapter).
- `site/astro.config.mjs` — static output, site URL, shiki github-light.
- `site/wrangler.toml` — name="prototype-it-to-explain-itself", no [site], comments explaining the old error.
- `site-deploy.md` — the full deployment playbook (read before touching CF).
- `PROTOTYPE_ROADMAP.md` — the 9-item curated list + original rationale table + implementation notes.
- `llm/architecture.md` — Predictor as narrow waist, full interconnection Mermaid (follows the quote-label rules), doc update mandate.
- `llm/README.md` — per-prototype sections + "Sequencing — What Comes Next".
- Root `README.md` — high-level "Current Prototypes" + the pattern explanation + pnpm note + hub links.
- `site/src/pages/concepts/*.mdx` — the rendered explainer content (frontmatter + prose + `<PracticeCTA concept="predictor-narrow-waist" />` etc.).

Also present: legacy root `wrangler.toml` (can be ignored/deleted), `site/public/` copy of tester (for dev), `site/dist/` (build artifact).

---

## Known Pitfalls Already Solved (Tell Cursor If It Regresses)

- Do not put a `[site]` section in any wrangler.toml for this Pages project.
- Do not rely on the cloudflare adapter for local `wrangler pages dev dist` if you want reliable static asset + CSS serving; pure static has been more robust here.
- Always run `pnpm build` from `site/` (not root) so postbuild resolves `../reflect-and-attempt-quizz.html` correctly.
- Mermaid labels: quote anything with brackets or special chars.
- Tester key handler must ignore focused inputs/textareas.
- In synthetic_data_factory and local_inference_playground, persistence helpers come from `mini_react`, training from the base prototype.
- After any content or component change in site/, rebuild to see postbuild effect.

---

## Suggested Next Steps (Pick One)

1. **Verify locally** (strongly recommended before deploy): `cd site && pnpm build && pnpm preview`. Click around concepts, open the tester from the CTA, check that styles are zinc white/gray + red on hover, confirm `/reflect-and-attempt-quizz.html` is served at root of preview, test a `?concept=...` deep link.
2. **Full wrangler emulation test**: after build, `pnpm wrangler pages dev dist` and spot-check the same.
3. **Commit the current polish changes** (theme, rename, docs, postbuild, wrangler comments) if they look good. Suggested message matches the prior feat style.
4. **Production deploy**: Follow `site-deploy.md` exactly — GitHub connect in CF dashboard with Root=`site`, build command `pnpm install && pnpm build`. After first deploy, the tester and all concept pages + CTAs should be live at the exact project name.
5. **Content expansion**: Add more MDX concept pages (pull real content from root/llm/*.md or architecture), or expand the knowledgeItems array in the tester with new high-quality reflection/MCQ items.
6. **Polish**: Add a `_headers` file for caching, improve mermaid styling further, or prepare a TanStack evolution note.
7. **Any new prototype work** would start a 10th item — but the explicit 9-item roadmap is complete.

---

## Memory / Session Notes

- Full prior session details (including the original 9-item todo list, plan.md artifacts, bug traces, and user verbatim feedback on errors/theme/rename) live in the agent's `~/.grok/memory/prototype-it-to-explain-itself-ffb2c9e7/` and session compaction files. The workspace now has the explicit `PROTOTYPE_ROADMAP.md` so future agents don't have to hunt.
- The provided summary at the start of the low-credit handoff contained the complete prior roll-up.

---

**End of context.** Everything needed to continue without re-exploring history should be here. Update this file (or the living READMEs) when you make progress.

Build the smallest thing that still carries the heart of the idea. Then let the prototype (and the hub) do the explaining.