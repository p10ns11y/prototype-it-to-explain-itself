#!/usr/bin/env python3
"""
Toy shared latent: vision features and language land in one small vector space.

A fake scene has attributes (chair, red, window, …). A vision encoder maps a
"frame tag" into the space. A question embedding pulls toward the answer attribute.

Run from project root:
    python multimodal/shared_latent.py
    python multimodal/shared_latent.py --question "what color is the chair"
"""

from __future__ import annotations

import argparse
import math
import re


DIM = 8

# Hand-built attribute vectors (not learned — visible geometry in the space)
ATTRIBUTES: dict[str, list[float]] = {
    "chair":    [1, 0, 0, 0, 0, 0, 0, 0],
    "red":      [0, 1, 0, 0, 0, 0, 0, 0],
    "window":   [0, 0, 1, 0, 0, 0, 0, 0],
    "left":     [0, 0, 0, 1, 0, 0, 0, 0],
    "wood":     [0, 0, 0, 0, 1, 0, 0, 0],
    "sunlight": [0, 0, 0, 0, 0, 1, 0, 0],
    "small":    [0, 0, 0, 0, 0, 0, 1, 0],
    "room":     [0, 0, 0, 0, 0, 0, 0, 1],
}

# Scene = weighted sum of present attributes (vision encoder output)
SCENES: dict[str, dict[str, float]] = {
    "living_room_frame_3": {
        "chair": 0.9, "red": 0.85, "window": 0.7, "left": 0.4,
        "wood": 0.5, "sunlight": 0.6, "room": 0.8,
    },
}

# Question words → directions in the same space
WORD_VEC: dict[str, list[float]] = {
    "what": [0.1] * DIM,
    "color": ATTRIBUTES["red"],  # "color" points toward color-like answers
    "chair": ATTRIBUTES["chair"],
    "where": ATTRIBUTES["left"],
    "window": ATTRIBUTES["window"],
    "size": ATTRIBUTES["small"],
    "material": ATTRIBUTES["wood"],
    "light": ATTRIBUTES["sunlight"],
    "is": [0.05] * DIM,
    "the": [0.02] * DIM,
    "a": [0.02] * DIM,
}


def normalize(v: list[float]) -> list[float]:
    n = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / n for x in v]


def encode_scene(weights: dict[str, float]) -> list[float]:
    out = [0.0] * DIM
    for name, w in weights.items():
        vec = ATTRIBUTES[name]
        for i in range(DIM):
            out[i] += w * vec[i]
    return normalize(out)


def encode_question(text: str) -> list[float]:
    tokens = re.findall(r"[a-z]+", text.lower())
    out = [0.0] * DIM
    for tok in tokens:
        if tok in WORD_VEC:
            vec = WORD_VEC[tok]
            for i in range(DIM):
                out[i] += vec[i]
    return normalize(out) if any(out) else [0.0] * DIM


def dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def rank_attributes(query: list[float], top_k: int = 4) -> list[tuple[str, float]]:
    scores = [(name, dot(query, normalize(vec))) for name, vec in ATTRIBUTES.items()]
    scores.sort(key=lambda t: t[1], reverse=True)
    return scores[:top_k]


PROPERTY_WORDS = {"color", "where", "size", "material", "light"}


def bind_scene_and_question(scene_vec: list[float], question: str) -> list[float]:
    """Scene context + question — property words steer harder than filler."""
    tokens = re.findall(r"[a-z]+", question.lower())
    prop_vec = [0.0] * DIM
    for tok in tokens:
        if tok in PROPERTY_WORDS:
            vec = WORD_VEC[tok]
            for i in range(DIM):
                prop_vec[i] += vec[i]
    if any(tok in PROPERTY_WORDS for tok in tokens):
        prop_vec = normalize(prop_vec)
        return normalize([0.35 * scene_vec[i] + 0.65 * prop_vec[i] for i in range(DIM)])
    q_vec = encode_question(question)
    return normalize([scene_vec[i] + q_vec[i] for i in range(DIM)])


def main() -> None:
    parser = argparse.ArgumentParser(description="Shared latent toy")
    parser.add_argument("--scene", default="living_room_frame_3")
    parser.add_argument("--question", default="what color is the chair")
    args = parser.parse_args()

    weights = SCENES[args.scene]
    scene_vec = encode_scene(weights)
    q_vec = encode_question(args.question)
    bound = bind_scene_and_question(scene_vec, args.question)
    hits = rank_attributes(bound)

    print("=== SCENE (vision encoder → latent) ===")
    print(f"frame: {args.scene}")
    print("active attributes:", ", ".join(f"{k}={v:.2f}" for k, v in weights.items()))
    print("scene vector (first 4 dims):", [round(x, 3) for x in scene_vec[:4]])

    print("\n=== QUESTION (language → same latent) ===")
    print(f"Q: {args.question!r}")
    print("question vector (first 4 dims):", [round(x, 3) for x in q_vec[:4]])

    print("\n=== RETRIEVAL (dot product in shared space) ===")
    for rank, (name, score) in enumerate(hits, 1):
        print(f"  {rank}. {name:10s}  score={score:.3f}")

    print("\n=== MAP TO OTHER HEADS ===")
    print("→ language answer: ", hits[0][0])
    print("→ diffusion head would sample pixels consistent with", hits[0][0])
    print("→ splat head would nudge blobs tagged", hits[0][0])


if __name__ == "__main__":
    main()
