#!/usr/bin/env python3
"""
Thin NLP demo: left-to-right sampling with temperature and top-p.

This is NOT the full LSTM in llm/simple_llm_prototype.py — just a tiny bigram
model that makes decoding policy visible. For train + generate end-to-end, see llm/.

Run from project root:
    python nlp/style_sampler.py
    python nlp/style_sampler.py --prompt "The model" --temp 0.4 --top-p 0.9
    python nlp/style_sampler.py --corpus terse --temp 1.2
"""

from __future__ import annotations

import argparse
import math
import random
import re
from collections import defaultdict


CORPORA: dict[str, str] = {
    "warm": (
        "The model writes one token at a time. Each choice depends on everything before it. "
        "Warm prose invites the reader in. It uses short sentences and plain words. "
        "The model writes one token at a time. Warm prose invites the reader in."
    ),
    "terse": (
        "State the fact. Cut filler. One line per idea. State the fact. Cut filler. "
        "Numbers beat adjectives. State the fact. One line per idea."
    ),
}


def tokenize(text: str) -> list[str]:
    return re.findall(r"[A-Za-z]+|[^A-Za-z\s]", text)


def build_bigrams(tokens: list[str]) -> dict[str, dict[str, int]]:
    counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for a, b in zip(tokens, tokens[1:]):
        counts[a][b] += 1
    return counts


def softmax(logits: list[float]) -> list[float]:
    m = max(logits)
    exps = [math.exp(x - m) for x in logits]
    s = sum(exps) or 1.0
    return [e / s for e in exps]


def apply_temperature(probs: list[float], temp: float) -> list[float]:
    if temp <= 0:
        i = max(range(len(probs)), key=lambda j: probs[j])
        return [1.0 if j == i else 0.0 for j in range(len(probs))]
    logits = [math.log(max(p, 1e-12)) / temp for p in probs]
    return softmax(logits)


def top_p_filter(ids: list[str], probs: list[float], top_p: float) -> tuple[list[str], list[float]]:
    ranked = sorted(zip(probs, ids), reverse=True)
    kept_ids, kept_p, mass = [], [], 0.0
    for p, tok in ranked:
        if mass + p > top_p and kept_ids:
            break
        kept_ids.append(tok)
        kept_p.append(p)
        mass += p
    s = sum(kept_p) or 1.0
    return kept_ids, [p / s for p in kept_p]


def sample_token(
    context: str,
    model: dict[str, dict[str, int]],
    rng: random.Random,
    temp: float,
    top_p: float,
) -> str:
    bucket = model.get(context, {})
    if not bucket:
        return ""

    ids = list(bucket.keys())
    counts = [bucket[t] for t in ids]
    total = sum(counts)
    probs = [c / total for c in counts]
    probs = apply_temperature(probs, temp)
    ids, probs = top_p_filter(ids, probs, top_p)
    r = rng.random()
    acc = 0.0
    for tok, p in zip(ids, probs):
        acc += p
        if r <= acc:
            return tok
    return ids[-1]


def generate(
    prompt: str,
    model: dict[str, dict[str, int]],
    rng: random.Random,
    max_tokens: int,
    temp: float,
    top_p: float,
) -> str:
    tokens = tokenize(prompt)
    if not tokens:
        tokens = ["The"]

    for _ in range(max_tokens):
        ctx = tokens[-1]
        nxt = sample_token(ctx, model, rng, temp, top_p)
        if not nxt or nxt in {".", "!", "?"} and len(tokens) > 12:
            break
        tokens.append(nxt)
        if nxt in ".!?":
            break

    out = []
    for t in tokens:
        if out and re.match(r"[A-Za-z]", t) and re.match(r"[A-Za-z]", out[-1]):
            out.append(" ")
        out.append(t)
    return "".join(out)


def main() -> None:
    parser = argparse.ArgumentParser(description="Next-token sampling toy (no torch)")
    parser.add_argument("--corpus", choices=list(CORPORA), default="warm")
    parser.add_argument("--prompt", default="The model")
    parser.add_argument("--tokens", type=int, default=40)
    parser.add_argument("--temp", type=float, default=0.85)
    parser.add_argument("--top-p", type=float, default=0.92)
    parser.add_argument("--seed", type=int, default=3)
    parser.add_argument("--compare-temp", action="store_true", help="Show low vs high temperature")
    args = parser.parse_args()

    rng = random.Random(args.seed)
    toks = tokenize(CORPORA[args.corpus])
    model = build_bigrams(toks)

    print(f"corpus={args.corpus!r}  vocab contexts={len(model)}  tokens={len(toks)}")
    print(f"decoding: temp={args.temp}  top_p={args.top_p}")
    print(f"prompt: {args.prompt!r}\n")

    if args.compare_temp:
        for t in (0.3, 1.4):
            text = generate(args.prompt, model, random.Random(args.seed), args.tokens, t, args.top_p)
            print(f"temp={t:.1f} → {text}\n")
    else:
        text = generate(args.prompt, model, rng, args.tokens, args.temp, args.top_p)
        print(f"sample → {text}")

    print("\nFull train+generate loop with LSTM: see llm/simple_llm_prototype.py")


if __name__ == "__main__":
    main()
