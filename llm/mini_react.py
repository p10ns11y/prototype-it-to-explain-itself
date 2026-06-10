#!/usr/bin/env python3
"""
Mini ReAct Agent — Think → Act → Observe on top of the Tiny Predictor
====================================================================

This is a complete, tiny, runnable prototype of the ReAct pattern
(Reason + Act).

What it teaches:
- The "agent" is not the LLM. The agent is a simple Python loop.
- The LLM is only a predictor: you feed it a prompt, it gives you text.
- Tools are ordinary Python functions. The loop decides when to call them.
- The magic (and the brittleness) lives in how you format the prompt and
  how you parse the model's reply.

We reuse the exact same TinyLLM you already understand from
simple_llm_prototype.py via the thin Predictor abstraction in
tiny_predictor.py. No bloat to the core model file.

The story world (Elara, the machine, glowing crystals) is deliberately
reused so everything feels like one coherent, hold-in-your-head universe.

Run it. Watch the trace. Change the question. Change the temperature.
The first run trains the model (same as simple_llm_prototype.py).
Every run after that loads the saved weights instantly — no more waiting.

Memory support: Pass `extra_context=...` (see memory.py + memory_explainer.py)
to inject short-term and/or retrieved long-term memory into the prompt.

Usage (from project root):
    python llm/mini_react.py
    python llm/mini_react.py --question "How much energy might the crystals hold?" --max-steps 5 --temp 0.7
"""

from __future__ import annotations

import argparse
import os
import re
from dataclasses import dataclass
from typing import List, Optional, Tuple

# ------------------------------------------------------------------
# 1. REUSE THE EXISTING TINY LLM WORLD (via import, no copy-paste of logic)
# ------------------------------------------------------------------
# We import the building blocks so the "brain" definition stays in one place.
# The training code below is the same pattern as simple_llm_prototype.py
# so the reader sees the connection immediately.

# Robust import bootstrap so this works cleanly when run as:
#   python llm/mini_react.py          (recommended, from project root)
#   python mini_react.py              (from inside the llm/ folder)
import sys
from pathlib import Path

_llm_dir = Path(__file__).resolve().parent
if str(_llm_dir) not in sys.path:
    sys.path.insert(0, str(_llm_dir))

from simple_llm_prototype import (
    STORY,
    CORPUS,
    CharDataset,
    TinyLLM,
    train_model,
    encode,
    decode,
    vocab_size,
)
from tiny_predictor import from_tiny_llm, Predictor

import torch
from torch.utils.data import DataLoader


# ------------------------------------------------------------------
# 2. THE TOOLS (ordinary Python functions that live in the Elara world)
# ------------------------------------------------------------------
# Tools are small, deterministic, and described in plain English.
# Their descriptions go straight into the prompt the model sees.

@dataclass
class Tool:
    name: str
    description: str
    fn: callable


def tool_calc(expr: str) -> str:
    """Safe little calculator for an inventor measuring things."""
    expr = expr.strip()
    # Very small allow-list to keep the demo safe and obvious.
    if not re.match(r"^[0-9+\-*/().\s]+$", expr):
        return "I can only do simple arithmetic with numbers, +, -, *, /, and parentheses."
    try:
        # eval is acceptable here because of the allow-list above
        result = eval(expr, {"__builtins__": {}}, {})
        return str(float(result)) if isinstance(result, (int, float)) else str(result)
    except Exception as e:
        return f"Could not compute that: {e}"


def tool_lookup(topic: str) -> str:
    """Recall a fact from the village / machine knowledge (our tiny "memory")."""
    topic = topic.lower().strip()
    facts = {
        "machine": "The machine was born from lightning and now whispers secrets of the universe.",
        "crystals": "Strange glowing crystals from the forest power the machine and Elara's dreams.",
        "elara": "Elara is the young inventor who believes science and curiosity are the same thing.",
        "village": "The quiet village sits between mountains and a sparkling river.",
        "stars": "Elara dreamed of building a machine that could talk to the stars.",
        "language": "Elara and the machine explored the mysteries of language, numbers, and dreams together.",
    }
    for key, fact in facts.items():
        if key in topic:
            return fact
    return "I remember something about that, but the details are still hazy in the story."


TOOLS: List[Tool] = [
    Tool(
        name="calc",
        description="Perform simple arithmetic. Use it for measurements, energy, distances. Example: calc[2 * 3 + 1]",
        fn=tool_calc,
    ),
    Tool(
        name="lookup",
        description="Recall a known fact from Elara's world (machine, crystals, village, stars...). Example: lookup[crystals]",
        fn=tool_lookup,
    ),
]


# ------------------------------------------------------------------
# 3. PROMPT BUILDING (plain English, explicit sections)
# ------------------------------------------------------------------

def build_prompt(question: str, tools: List[Tool], trajectory: List[str],
                 extra_context: str = "") -> str:
    """Build the prompt the predictor will continue.

    This version uses clear instructions + concrete few-shot examples
    written in the style of the Elara story. The tiny character-level model
    needs very explicit patterns to copy, otherwise it just rambles or
    echoes the instructions in broken form.

    extra_context can be memory snippets, previous observations, etc.
    It is inserted right before the final "Thought:" hand-off.
    """
    tool_lines = "\n".join(
        f"- {t.name}: {t.description}" for t in tools
    )

    history = "\n".join(trajectory) if trajectory else ""

    context_block = f"\n{extra_context}\n" if extra_context else ""

    # The final "Thought:" is the hand-off to the model.
    # We repeat the format and give two worked examples that match the
    # actual tools and the world of the story. This greatly helps the
    # weak model produce something that the parser can recognize.
    prompt = f"""You are helping Elara, the inventor, think step by step.

You have these tools:
{tool_lines}

Here are two examples of the exact format you must use:

Goal: What do we know about the glowing crystals?
Thought: Elara found strange glowing crystals in the forest. I should use the lookup tool to recall what the story says about them.
Action: lookup[crystals]

Goal: How much energy might the crystals hold if each one gives a small spark?
Thought: The crystals glow when the machine is near. To find the total energy I need to do simple arithmetic.
Action: calc[3 * 4 + 2]

Now solve this new goal. You must respond in this exact style:

Thought: what you are thinking right now
Action: toolname[argument]   (only when you decide to use a tool)
or
Final Answer: your best answer for Elara (do this when you are done)

Goal: {question}
{context_block}
{history}
Thought:"""

    # Strong priming for this iteration: if the goal itself looks like a tool call
    # (e.g. "lookup[stars]"), append a complete correct example right before the
    # final "Thought:". This gives the tiny model a very strong pattern to copy.
    # This is a temporary hack to make a tool call happen in this run for illustration.
    if '[' in question and ']' in question:
        try:
            tool_name = question.split('[')[0].strip()
            arg = question.split('[')[1].split(']')[0].strip()
            if tool_name in [t.name for t in tools]:
                priming = f"""
Goal: {question}
Thought: The goal is written in the tool call style. I will follow the format exactly and use the tool.
Action: {tool_name}[{arg}]
"""
                prompt = prompt.rstrip() + priming + "\nThought:"
        except Exception:
            pass

    return prompt


# ------------------------------------------------------------------
# 4. SIMPLE (INTENTIONALLY NAIVE) PARSER
# ------------------------------------------------------------------
# This parser is deliberately small and brittle. That is the point.
# Real agents spend a lot of effort here (better prompting, constrained
# decoding, retries, etc.). Later prototypes will improve exactly this.

ACTION_RE = re.compile(r"Action:\s*(\w+)\s*\[(.*?)\]", re.IGNORECASE)
FINAL_RE = re.compile(r"(?:Final Answer|Final):\s*(.+)", re.IGNORECASE | re.DOTALL)


def parse_action(text: str) -> Optional[Tuple[str, str]]:
    """Try to find an Action: name[args] in the model's output."""
    m = ACTION_RE.search(text)
    if m:
        name = m.group(1).strip().lower()
        arg = m.group(2).strip()
        return name, arg
    return None


def parse_final(text: str) -> Optional[str]:
    m = FINAL_RE.search(text)
    if m:
        return m.group(1).strip()
    return None


# ------------------------------------------------------------------
# 5. THE REACT LOOP (the actual agent)
# ------------------------------------------------------------------

def run_react(
    question: str,
    predictor: Predictor,
    tools: List[Tool],
    max_steps: int = 5,
    verbose: bool = True,
    extra_context: str = "",
) -> str:
    """Run the classic ReAct loop and return the final answer (or best effort).

    extra_context: Optional text (e.g. memory snippets from memory.py) that will
    be inserted into the prompt right before the final "Thought:" hand-off.
    This is the supported way to inject memory or other context without changing
    the core ReAct logic.
    """
    trajectory: List[str] = []
    tool_map = {t.name.lower(): t for t in tools}

    if verbose:
        print("\n" + "=" * 70)
        print("REACT AGENT START")
        print("=" * 70)
        print(f"Goal (question for Elara): {question}")
        print()
        print("Legend:")
        print("  [AGENT]  = Python control loop (the actual 'agent' code)")
        print("  [MODEL]  = Output from the tiny character-level LSTM predictor")
        print("  The loop tries: Thought → (optional) Action → Observation → repeat")
        print("-" * 70)

    for step in range(1, max_steps + 1):
        prompt = build_prompt(question, tools, trajectory, extra_context=extra_context)

        # ------------------------------------------------------------------
        # AGENT: Prepare and send the prompt
        # ------------------------------------------------------------------
        if verbose:
            print(f"\n{'='*70}")
            print(f"STEP {step} / {max_steps}")
            print(f"{'='*70}")
            print(f"[AGENT] Building prompt for the model")
            print(f"        Current trajectory turns: {len(trajectory)}")

            # Show the *tail* of the prompt so you can see what context the model sees
            # (the full prompt would be huge and noisy)
            tail = prompt[-650:] if len(prompt) > 650 else prompt
            print(f"\n[AGENT] Last part of prompt sent to model:\n{tail}")
            if len(prompt) > 650:
                print("        ... (earlier history truncated for readability)")

        # ------------------------------------------------------------------
        # MODEL: Call the predictor
        # ------------------------------------------------------------------
        if verbose:
            print(f"\n[MODEL] Calling predictor (max_new_tokens=70)...")
        full_output = predictor(prompt, max_new_tokens=70)

        # We only want the newly generated text, not the prompt we just fed it
        if full_output.startswith(prompt):
            model_output = full_output[len(prompt):].lstrip()
        else:
            model_output = full_output.strip()

        if verbose:
            # Show the raw model output clearly. Using repr() helps see newlines,
            # spaces, and weird characters the tiny model actually produced.
            display = repr(model_output[:550])
            if len(model_output) > 550:
                display += " ..."

            print(f"\n[MODEL] Raw output from TinyLLM:\n{display}")
            print()

            # ------------------------------------------------------------------
            # AGENT: Parse what the model said
            # ------------------------------------------------------------------
            print("[AGENT] Parsing model output...")

        if verbose:
            # ------------------------------------------------------------------
            # AGENT: Parse what the model said
            # ------------------------------------------------------------------
            print("[AGENT] Parsing model output...")

        # 1. Did it give a final answer?
        final = parse_final(model_output)
        if final:
            if verbose:
                print("        → Detected: Final Answer")
            trajectory.append(f"Final Answer: {final}")
            if verbose:
                print(f"\n[AGENT] ReAct loop finished with final answer.")
                print(f"        Elara's answer: {final}\n")
            return final

        # 2. Did it request an action?
        action = parse_action(model_output)
        if not action:
            # Temporary hack for this iteration: if the question itself was
            # written in tool-call syntax (e.g. "lookup[stars]"), force the
            # action so the user can see a tool actually being called.
            # This is only to demonstrate the loop when the model fails to
            # produce the format (which the tiny char-level model often does).
            if '[' in question and ']' in question:
                try:
                    name = question.split('[')[0].strip()
                    arg = question.split('[')[1].split(']')[0].strip()
                    if name in [t.name for t in tools]:
                        action = (name, arg)
                        if verbose:
                            print(f"        → No Action from model, but question looks like tool call.")
                            print(f"        → FORCING Action for this iteration: name={name} arg={arg!r}")
                except Exception:
                    pass

        if action:
            name, arg = action
            if verbose:
                print(f"        → Detected: Action  name={name}  arg={arg!r}")

            tool = tool_map.get(name)
            if tool:
                try:
                    obs = tool.fn(arg)
                except Exception as e:
                    obs = f"Tool failed: {e}"
                if verbose:
                    print(f"[AGENT] Executing tool '{name}' ...")
                    print(f"        Observation: {obs}")

                # Store only a short, clean version in the trajectory so we
                # don't pollute future prompts with the model's garbage
                clean_thought = model_output[:280].replace('\n', ' ').strip()
                trajectory.append(f"Thought: {clean_thought}")
                trajectory.append(f"Action: {name}[{arg}]")
                trajectory.append(f"Observation: {obs}")
            else:
                obs = f"Unknown tool '{name}'. Available: {', '.join(tool_map.keys())}"
                if verbose:
                    print(f"        Observation: {obs}")
                clean_thought = model_output[:280].replace('\n', ' ').strip()
                trajectory.append(f"Thought: {clean_thought}")
                trajectory.append(f"Action: {name}[{arg}]")
                trajectory.append(f"Observation: {obs}")
        else:
            # 3. No clear Action or Final — the model just produced more "thought"
            if verbose:
                print("        → No clear Action or Final Answer detected.")
                print("        → Treating as additional Thought and continuing the loop.")

            clean_thought = model_output[:280].replace('\n', ' ').strip()
            trajectory.append(f"Thought: {clean_thought}")

        if verbose:
            # Small visual summary of what the agent decided to remember
            print(f"\n[AGENT] Trajectory now has {len(trajectory)} entries.")
            if trajectory:
                print("        Last 3 entries (what the agent will remember):")
                for entry in trajectory[-3:]:
                    short = entry[:90] + "..." if len(entry) > 90 else entry
                    print(f"          {short}")
            print("-" * 70)

    # Ran out of steps (only reached if no Final Answer was produced)
    last = trajectory[-1] if trajectory else "No thoughts produced."
    if verbose:
        print("\n" + "=" * 70)
        print("REACT AGENT STOPPED (max steps reached)")
        print("=" * 70)
        print("No clear 'Final Answer' was produced within the step limit.")
        print("Last thing recorded in trajectory:")
        print(f"  {last}")
        print()
        print("This is common with the tiny model because it struggles with the")
        print("required output format. The loop itself ran correctly.")
    return last


# ------------------------------------------------------------------
# 6. TRAINING (same tiny world as the original prototype)
# ------------------------------------------------------------------

def build_trained_model(epochs: int = 25, device: Optional[str] = None) -> TinyLLM:
    """Train a fresh TinyLLM exactly the way the base prototype does."""
    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"

    print(f"Device: {device}")
    data_tensor = encode(CORPUS)
    print(f"Corpus size: {len(CORPUS):,} characters → {len(data_tensor):,} tokens")

    seq_len = 30
    dataset = CharDataset(data_tensor, seq_len=seq_len)
    dataloader = DataLoader(dataset, batch_size=48, shuffle=True, drop_last=True)
    print(f"Training examples: {len(dataset):,}\n")

    model = TinyLLM(vocab_size, embed_dim=64, hidden_dim=128, num_layers=2)
    total_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"Model: {total_params:,} parameters (tiny on purpose)\n")

    model = train_model(model, dataloader, epochs=epochs, lr=0.0035, device=device)
    return model


def save_model(model: TinyLLM, path: str):
    """Persist the trained weights so we don't have to retrain every time."""
    torch.save(model.state_dict(), path)
    print(f"Saved trained model to {path}")


def load_model(path: str, device: str = "cpu") -> TinyLLM:
    """Load a previously saved model. Tokenizer is rebuilt from the same CORPUS."""
    model = TinyLLM(vocab_size, embed_dim=64, hidden_dim=128, num_layers=2)
    model.load_state_dict(torch.load(path, map_location=device))
    model = model.to(device)
    print(f"Loaded model from {path} (skipped training)")
    return model


# ------------------------------------------------------------------
# 7. MAIN / CLI
# ------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Mini ReAct Agent — watch an LLM become an agent that uses tools",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python llm/mini_react.py
  python llm/mini_react.py --question "How can Elara measure the power of the glowing crystals?" --max-steps 6 --temp 0.65

  # Subsequent runs are fast because we load the saved model instead of retraining
  python llm/mini_react.py --question "..." --max-steps 8

  # Force a fresh training run
  python llm/mini_react.py --force-train --epochs 15
""",
    )
    parser.add_argument(
        "--question",
        type=str,
        default="What should Elara ask the machine about the glowing crystals?",
        help="The goal the agent must help Elara achieve",
    )
    parser.add_argument(
        "--max-steps", type=int, default=5, help="Maximum Think-Act-Observe cycles"
    )
    parser.add_argument(
        "--temp", type=float, default=0.7, help="Sampling temperature for the predictor"
    )
    parser.add_argument(
        "--epochs", type=int, default=20, help="Training epochs (smaller = faster demo)"
    )
    parser.add_argument(
        "--model-path", type=str, default="llm/tiny_model.pt",
        help="Where to save/load the trained model weights. If the file exists, training is skipped."
    )
    parser.add_argument(
        "--force-train", action="store_true",
        help="Ignore any existing saved model and train from scratch anyway."
    )

    args = parser.parse_args()

    device = "cuda" if torch.cuda.is_available() else "cpu"

    print("=" * 65)
    print("MINI REACT AGENT ON TINY LLM")
    print("=" * 65)

    # Only train if we don't already have a saved model.
    # This is the main practical improvement over the original prototype.
    if os.path.exists(args.model_path) and not args.force_train:
        model = load_model(args.model_path, device=device)
    else:
        model = build_trained_model(epochs=args.epochs, device=device)
        save_model(model, args.model_path)

    # Wrap it in the clean Predictor abstraction
    predictor = from_tiny_llm(model, temperature=args.temp, device=device)

    # Run the loop
    answer = run_react(
        question=args.question,
        predictor=predictor,
        tools=TOOLS,
        max_steps=args.max_steps,
    )

    # ------------------------------------------------------------------
    # WHAT YOU JUST SAW (educational block — same spirit as the base prototype)
    # ------------------------------------------------------------------
    print("\n" + "=" * 65)
    print("WHAT YOU JUST SAW")
    print("=" * 65)
    print(
        """
1. The "agent" is ordinary Python code (the loop in run_react).
   It builds a prompt, calls the predictor, parses the reply, calls tools,
   appends observations, and repeats.

2. The LLM (our TinyLLM) only ever did one thing: given some text, predict
   more text. We reused the exact same generate_text via the Predictor
   wrapper. No magic.

3. We no longer waste time retraining on every run.
   - First run: trains the model (same code as simple_llm_prototype.py) and
     saves the weights to --model-path (default: llm/tiny_model.pt).
   - Later runs: load the weights instantly and skip training entirely.
   - Use --force-train if you actually want to retrain (e.g. after changing
     the STORY or model size).
   This is the key practical difference from the original prototype.

4. Tools are just functions. calc and lookup are tiny, deterministic, and
   live inside the Elara story so you can hold the whole example in your head.

5. Parsing is the weak point right now. The model often produces beautiful
   story-like thoughts but fails to emit clean "Action: name[args]" lines.
   This is expected — the training data never contained that format.
   Later prototypes (Tool Reliability Lab, Typed Workflow, better prompting)
   will attack exactly this gap.

6. Temperature still matters. Higher temp → more creative (and usually more
   chaotic) thoughts and worse format following.

Try these experiments:
- Run the same command twice in a row. Notice how fast the second run is.
- Change --question and --max-steps without waiting for training.
- Use --force-train --epochs 15 after you modify the STORY in the code.
- Add a third tool in the TOOLS list and give it a description.

This is the same fundamental ReAct pattern used by production agents,
just small enough that you can see every moving part.
"""
    )

    print(f"Final answer returned to Elara: {answer}")
    print("-" * 65)


if __name__ == "__main__":
    main()