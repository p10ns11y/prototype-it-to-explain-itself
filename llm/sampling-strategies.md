# Sampling Strategies: Temperature, Top-k, and Top-p

Temperature alone is powerful but has limitations. That's why almost every production LLM (including Grok) combines it with **Top-k** or **Top-p** (nucleus) sampling.

This document explains the "why" and "how" behind these techniques, using the same spirit as the prototype: make the invisible mechanics visible and understandable.

---

## The Problem with Temperature Alone

Even with a well-chosen temperature, the model can still:

- Pick very low-probability "weird" or broken tokens (especially at high temperature)
- Become overly repetitive or safe (at low temperature)

**Top-k** and **Top-p** solve this by **restricting the set of tokens** the model is allowed to sample from at each step.

They act as a filter *after* temperature has shaped the distribution.

---

## 1. Top-k Sampling (Simple but Rigid)

### How it works

1. The model calculates probabilities for all tokens in the vocabulary.
2. It keeps only the **k most probable tokens**.
3. It **renormalizes** the probabilities of those k tokens so they sum to 1.
4. It samples from this smaller, high-quality set.

### Example (simplified)

Suppose after the context `"Elara listened in wonder"`, the model's top probabilities look like this:

| Token      | Probability | Rank |
|------------|-------------|------|
| `.`        | 41%         | 1    |
| `,`        | 23%         | 2    |
| `From`     | 18%         | 3    |
| `and`      | 7%          | 4    |
| `she`      | 4%          | 5    |
| `the`      | 2%          | 6    |
| `machinee` | 0.8%        | 7    |
| ...        | ...         | ...  |

- With **top_k = 5**, only the first 5 tokens are kept. `machinee` (and everything below) is thrown away, *even if temperature is high*.
- The 5 remaining probabilities are renormalized (they will now sum to 100%) and we sample from that set.

### Pros
- Simple to understand and implement
- Effectively prevents extremely unlikely or broken tokens

### Cons
- A fixed `k` is problematic in practice:
  - When the model is very confident, many of the "top-k" tokens are actually low quality.
  - When the model is uncertain (flat distribution), you might cut off perfectly reasonable tokens that just happened to rank slightly lower.

This rigidity is why **Top-p** (nucleus sampling) was invented.

---

## 2. Top-p Sampling (Nucleus Sampling) — Usually Better

### How it works

Instead of taking a fixed number of tokens (`k`), we take the **smallest set of tokens** whose **cumulative probability** is at least `p`.

This dynamic set is called the **nucleus**.

### Example (same probabilities, `p = 0.9`)

| Token  | Prob | Cumulative |
|--------|------|------------|
| `.`    | 41%  | 41%        |
| `,`    | 23%  | 64%        |
| `From` | 18%  | **82%**    |
| `and`  | 7%   | 89%        |
| `she`  | 4%   | **93%**    |

- With `top_p = 0.9`, we stop at `"she"` because the cumulative probability just crossed 90%.
- We **only sample from these 5 tokens** (same result as top-k=5 in this specific case).
- But if the distribution was flatter, the nucleus might include 12 tokens.
- If the model was extremely confident (e.g. top token = 85%), the nucleus might contain only **1 or 2 tokens**.

This is **dynamic** — it automatically adapts to how confident (or uncertain) the model is at each generation step.

### Common values used in practice
- `top_p = 0.9` or `0.95` (very common)
- Usually combined with `temperature = 0.7 ~ 1.0`

---

## Temperature + Top-p (The Winning Combination)

Most APIs let you use both together. The typical order of operations is:

1. Apply **temperature** to the logits (`logits = logits / temperature`)
2. Convert to probabilities with softmax
3. Apply **top-p** (or top-k) filtering on those probabilities
4. Renormalize the filtered probabilities and sample

This gives you two independent, intuitive controls:

| Control     | Effect                                      | Analogy                     |
|-------------|---------------------------------------------|-----------------------------|
| Temperature | How *sharp* or *flat* the distribution is   | How "creative" vs "safe"    |
| Top-p       | How *wide* the allowed set of tokens is     | How much "exploration room" |

### Visual Intuition

```
Low Temp + Low Top-p     → Very safe, almost deterministic
Low Temp + High Top-p    → Safe but allows some exploration
High Temp + Low Top-p    → Creative but still constrained (weirdness limited)
High Temp + High Top-p   → Maximum creativity + chaos
```

---

## Real-World Defaults (Approximate)

| Model / API          | Typical Temperature | Typical Top-p |
|----------------------|---------------------|---------------|
| Grok / xAI           | 0.7 – 1.0           | 0.9           |
| GPT-4o               | 0.7                 | 0.9           |
| Claude 3.5           | 0.7                 | — (uses different internal method) |
| Creative writing     | 1.0 – 1.2           | 0.95          |
| Coding / structured  | 0.2 – 0.4           | 0.8           |

> Note: Some models (notably Claude) achieve similar effects through different techniques and may not expose `top_p` directly.

---

## How This Prototype Currently Samples

Look at `generate_text` in [simple_llm_prototype.py](simple_llm_prototype.py):

```python
next_logits = logits[0, -1, :] / max(temperature, 1e-6)
probs = torch.softmax(next_logits, dim=-1)
next_id = torch.multinomial(probs, num_samples=1).item()
```

Currently it only uses **temperature**. Adding top-k or top-p would go between the softmax and the `torch.multinomial` call:

1. Compute `probs` as above.
2. Filter to the nucleus (top-p) or top-k tokens.
3. Renormalize the filtered probabilities.
4. Sample with `torch.multinomial` on the filtered set.

The `--show-probs` flag already uses `torch.topk` internally to display the model's beliefs — the same primitive used in top-k sampling.

---

## Experiments Worth Trying

Once top-p / top-k are added to the prototype (or if you implement them yourself):

- Run the same prompt with `--temp 1.1` and no top-p → watch weird tokens appear.
- Run the same prompt with `--temp 1.1 --top_p 0.9` → creativity without the garbage.
- Try a very low `top_p` (0.6) with medium temperature on a creative prompt → see how the model gets "stuck" in safe but boring continuations.
- Watch how the size of the nucleus changes across different contexts using the probability visualization.

---

## Related Techniques (Advanced)

For even more control, production systems often add:

- **min_p**: A minimum probability threshold (relative to the top token) — keeps tokens above a floor even in flat distributions.
- **Repetition penalty**: Reduces probability of tokens that have already appeared recently.
- **Frequency / presence penalties**: Variants of the above.
- **Mirostat**: Adaptive sampling that tries to maintain a target "surprise" level (perplexity).
- **Typical sampling**: Prefers tokens whose information content is close to the expected value for the distribution.

These are usually combined with temperature + top-p.

---

## Summary

- **Temperature** reshapes the probability distribution.
- **Top-k** and **Top-p** restrict *which* tokens are even eligible to be chosen.
- **Top-p (nucleus)** is generally preferred because it adapts to the model's confidence at each step.
- The combination of temperature + top-p is the practical default across almost all deployed LLMs.

Understanding these three knobs (and their interactions) removes a lot of the mystery around why models sometimes feel "inspired" and sometimes feel "drunk."

---

*This is document "2" in the sampling series for the prototype. The core generation loop remains the same: predict, filter, sample, append, repeat.*