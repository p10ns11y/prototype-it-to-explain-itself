# Prototype It To Explain Itself

> A tiny, runnable prototype that explains how large language models work — by implementing one from scratch.

This project contains a complete, self-contained educational implementation of a character-level LSTM language model in pure PyTorch. The goal is **not** to build production AI, but to make the fundamental mechanisms of LLMs transparent and understandable.

## What This Is

Modern LLMs (Grok, GPT, Claude, Llama, etc.) are fundamentally **next-token predictors**. Given a sequence of tokens, they predict the most likely next token. Everything else — reasoning, conversation, code generation — emerges from scaling this simple loop with clever architecture and massive data.

This prototype demonstrates the full pipeline in ~340 lines:

1. **Tokenization** — Character-level (the simplest possible approach)
2. **Embedding** — Mapping tokens to learned dense vectors
3. **Recurrent memory** — LSTM maintains hidden state across time
4. **Prediction head** — Projects to a probability distribution over the vocabulary
5. **Autoregressive generation** — Sample a token, append it, repeat

### Key Differences from Real LLMs

| Aspect              | This Prototype          | Real LLMs                     |
|---------------------|-------------------------|-------------------------------|
| Tokenization        | Character-level (~50)   | Subword BPE (~30k–100k+)      |
| Architecture        | 2-layer LSTM            | Stacked Transformer decoders  |
| Attention           | None (recurrent only)   | Multi-head self-attention     |
| Parameters          | ~150k                     | 1B – 1T+                      |
| Training data       | One short story ×15     | Internet-scale corpora        |
| Goal                | Understanding           | Capability                    |

The **core loop is identical**: predict next token → append → repeat.

## Quick Start

### Requirements

- Python 3.9+
- PyTorch (CPU is fine; CUDA works if available)

```bash
pip install torch
```

### Run It

```bash
python simple_llm_prototype.py
```

### Command Line Options

```bash
python simple_llm_prototype.py \
  --prompt "Elara dreamed of" \
  --tokens 200 \
  --temp 0.6

python simple_llm_prototype.py --show-probs
```

| Flag           | Default                  | Description |
|----------------|--------------------------|-----------|
| `--prompt`     | `"In a quiet village"`   | Seed text for generation |
| `--tokens`     | `140`                    | Number of new characters to generate |
| `--temp`       | `0.75`                   | Sampling temperature (lower = more deterministic) |
| `--show-probs` | (off)                    | After generation, show the model's top predictions for the next character |
| `--epochs`     | `25`                     | Training epochs |

## How It Works (High Level)

1. **Data**: A short original story about an inventor named Elara is repeated to create a tiny training corpus.
2. **Training**: The model sees many short windows of text and learns to predict the character that immediately follows each window.
3. **Generation**: Start with your prompt. At each step the model outputs a probability distribution over possible next characters. We sample from it (temperature controls how "adventurous" the sampling is) and feed the result back in.
4. **Inspection**: Use `--show-probs` to peek at what the model currently believes are the most likely next characters given a context. This is the closest thing to "seeing inside the mind" of the model.

## Experiments to Try

- Change the `STORY` constant and retrain — watch the model learn a completely different style and vocabulary.
- Increase `--epochs` or model size (`hidden_dim`, `num_layers` in `TinyLLM`).
- Compare temperatures: `0.3` (safe/repetitive) vs `1.2` (wild/chaotic).
- Use `--show-probs` with different prompts to see how context changes the probability distribution.
- Add more layers or replace the LSTM with a small Transformer block (advanced follow-up).

## Philosophy

This project exists to **prototype it to explain itself**. By building the simplest possible version that still captures the essential mechanism, the code becomes its own best documentation. Read the source, run it, tweak it, break it — understanding follows.

The same fundamental next-token prediction loop, just scaled up dramatically with better architecture and data, is what powers today's frontier models.

## License

This is research / educational code. Use it to learn, teach, and experiment.

---

*Run it. Read it. Modify it. Understand it.*