# LLM Prototype

This folder holds a tiny, complete language model. It exists so you can see how text generation works from the inside.

The model has only ~150k parameters. Real models have billions. The goal is not power. The goal is clarity.

## The One Big Idea

Every large language model does the same core job:

> Look at the text so far. Predict the next token. Append it. Repeat.

That loop, scaled up, produces fluent writing, code, and reasoning.

This prototype makes that loop visible and runnable.

## How Text Flows During Generation

```mermaid
flowchart LR
    P[Prompt text] --> E[Encode<br/>to token IDs]
    E --> V[Embedding layer<br/>learned vectors]
    V --> L[LSTM layers<br/>carry memory]
    L --> H[Linear head<br/>raw scores]
    H --> S[Softmax<br/>probabilities]
    S --> Sample[Sample one token]
    Sample --> Append[Append to context]
    Append -->|repeat| L
```

The model never plans the whole reply at once. At every step it only chooses what comes next.

## Code Structure & Big-Picture Flow

The entire prototype lives in one file, deliberately. The numbered sections below map directly to the code.

```mermaid
flowchart TD
    subgraph SRC["simple_llm_prototype.py — 7 Sections"]
        direction TB
        C1["1. CORPUS<br/>STORY repeated 15×"]
        C2["2. TOKENIZER<br/>char ↔ id + encode/decode"]
        C3["3. DATASET<br/>CharDataset — sliding windows"]
        C4["4. MODEL<br/>TinyLLM — Embed + LSTM + Head"]
        C5["5. TRAIN<br/>train_model — next-char loss"]
        C6["6. GENERATE<br/>generate_text + show_top_predictions"]
        C7["7. main<br/>CLI + full pipeline orchestration"]
    end

    C1 --> C2
    C2 --> C3
    C3 --> C5
    C4 --> C5 & C6
    C7 -->|orchestrates| C3 & C4 & C5 & C6
```

### Runtime Execution Flow (what happens when you run the script)

```mermaid
flowchart TD
    Start["python llm/simple_llm_prototype.py<br/>--prompt ... --tokens ..."] --> D1["Encode CORPUS → token tensor"]
    D1 --> D2["CharDataset + DataLoader<br/>creates (context_window, next_char) pairs"]
    D2 --> M["Instantiate TinyLLM<br/>~150k parameters"]
    M --> T["train_model<br/>25 epochs, AdamW, loss only on last position"]
    T --> G["generate_text<br/>autoregressive loop: predict → sample → append → repeat"]
    G --> Opt{"--show-probs ?"}
    Opt -->|yes| P["show_top_predictions<br/>prints the model's actual probability distribution"]
    Opt -->|no| Out["Print generated text + educational summary"]
    P --> Out
```

### Model Architecture (with shapes)

```mermaid
flowchart LR
    subgraph TinyLLM
        direction TB
        In["input_ids<br/>(B, T)"] --> Emb["Embedding<br/>(B, T, 64)"]
        Emb --> Lstm["2-layer LSTM<br/>(B, T, 128)"]
        Lstm --> Head["Linear head<br/>(B, T, vocab_size)"]
        Head --> Logits["logits<br/>(B, T, V)"]
    end

    Logits --> Train["Training: use only [:, -1, :]<br/>CrossEntropy with true next char"]
    Logits --> Gen["Generation: softmax last position<br/>sample 1 token, append, repeat"]

    style In fill:#e3f2fd
    style Logits fill:#fff3e0
```

### Training vs Generation (the same model, two very different loops)

```mermaid
flowchart LR
    subgraph Train["TRAINING (batched, offline)"]
        direction TB
        TW["Many fixed windows<br/>(30 chars)"] --> TF["Forward pass<br/>(teacher forced)"]
        TF --> TL["Loss only on position -1<br/>(predict the 31st char)"]
        TL --> TBK["Backprop + AdamW step"]
    end

    subgraph Gen["GENERATION (online, one token at a time)"]
        direction TB
        GS["Current context + hidden state"] --> GF["Forward pass (small window)"]
        GF --> GSamp["Softmax + temperature<br/>sample ONE token"]
        GSamp --> GApp["Append sampled token<br/>to context + hidden"]
        GApp -->|repeat N times| GS
    end

    Train ~~~ Gen
```

These diagrams show the *structure of the code* and how data moves, not just the abstract idea. The source is intentionally small so you can hold the whole picture in your head while reading any one section.

## Training Teaches the Guesses

We turn the story into many short examples by sliding a window across it.

```mermaid
flowchart LR
    Corpus["...the machine whispered secrets..."] --> Window1["window: 'the machine w'"]
    Corpus --> Window2["window: 'machine whis'"]
    Window1 --> Target1["target: 'h'"]
    Window2 --> Target2["target: 'p'"]
    Target1 --> Learn["model learns:<br/>after 'the machine w'<br/>'h' is likely"]
```

Each training step asks only one question: given these characters, what comes next? The model sees thousands of such questions from the repeated story.

We repeat one short story 15 times. The model overfits on purpose. It learns the names, the rhythm, and the world of that story.

## The Main Parts

1. **Data** — One story, repeated. See `STORY` and `CORPUS`.
2. **Tokenizer** — Characters only. About 50 symbols. Real systems use subword tokens (30k–100k).
3. **Dataset** — Sliding windows that create (context, next-char) pairs.
4. **Model** — Embedding → 2-layer LSTM → Linear prediction head.
5. **Training** — AdamW optimizer. Loss only on the single next character.
6. **Generation** — The autoregressive loop with temperature control.
7. **Inspection** — `--show-probs` shows the model's top guesses for the next character.

The script runs all of these steps in order when you execute it.

## Run It

From the project root:

```bash
python llm/simple_llm_prototype.py
```

Useful variants:

```bash
python llm/simple_llm_prototype.py --prompt "Elara dreamed of" --tokens 180 --temp 0.6
python llm/simple_llm_prototype.py --show-probs
```

See the module docstring in `simple_llm_prototype.py` for every flag and example.

## What We Left Out (on purpose)

| Real LLMs                     | This Version               | Reason for the cut                     |
|-------------------------------|----------------------------|----------------------------------------|
| Subword tokenization (BPE)    | Character level            | Characters are simple to watch and debug |
| Transformer blocks + attention| 2-layer LSTM               | LSTM state is easier to follow step by step |
| Billions to trillions of params | ~150k parameters         | Small enough that one person can read it all |
| Internet-scale training data  | One story repeated 15×     | You can hold the whole set in your head |
| Long training runs            | 25 short epochs            | Fast edit-run-inspect cycle            |

The central act stays identical: predict, append, repeat.

## Experiments That Teach

- Change the `STORY` text. Retrain. Notice how the generated voice changes.
- Set `--temp 0.3` (safe) vs `--temp 1.3` (wild).
- Use `--show-probs` and watch how the ending context shifts the probabilities.
- Increase `hidden_dim` or `num_layers` in the model and measure the effect.

## This Prototype Fits a Larger Pattern

This is one working example of the "prototype it to explain itself" method.

See the [main README](../README.md) for the intent behind the whole collection and the plan for more prototypes.

---

Run it. Read every line. Change one thing. Run it again. The mechanism stops being abstract.