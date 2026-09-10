#!/usr/bin/env python3
"""
1D diffusion toy — add noise, then walk back toward structure.

No ML framework. A tiny linear "network" learns to predict noise on a 1D signal.
At inference you start from pure noise and denoise step by step.

Run from project root:
    python diffusion/toy_denoise_1d.py
    python diffusion/toy_denoise_1d.py --steps 40 --save diffusion/out_denoise.ppm
"""

from __future__ import annotations

import argparse
import math
import random
from pathlib import Path


def make_signal(n: int = 64) -> list[float]:
    """A simple square pulse — easy to see recover."""
    x0 = [0.0] * n
    for i in range(n // 4, 3 * n // 4):
        x0[i] = 1.0
    return x0


def add_noise(x0: list[float], t: float, rng: random.Random) -> list[float]:
    """Forward diffusion: mix signal with Gaussian noise at level t in [0, 1]."""
    alpha = 1.0 - t
    return [math.sqrt(alpha) * v + math.sqrt(t) * rng.gauss(0, 1) for v in x0]


def train_noise_predictor(
    x0: list[float],
    steps: int,
    epochs: int,
    rng: random.Random,
) -> tuple[float, float]:
    """
    Fit w * x_t + b ≈ noise added at random t.
    This is the training asymmetry: we know the clean x0 and the noise we injected.
    """
    w, b = 0.0, 0.0
    lr = 0.05
    n = len(x0)

    for _ in range(epochs):
        t = rng.uniform(0.05, 0.95)
        noise = [rng.gauss(0, 1) for _ in range(n)]
        alpha = 1.0 - t
        x_t = [math.sqrt(alpha) * x0[i] + math.sqrt(t) * noise[i] for i in range(n)]

        # Predict noise from x_t (linear probe — enough for this toy)
        pred = [w * x_t[i] + b for i in range(n)]
        grad_w = sum(2 * (pred[i] - noise[i]) * x_t[i] for i in range(n)) / n
        grad_b = sum(2 * (pred[i] - noise[i]) for i in range(n)) / n
        w -= lr * grad_w
        b -= lr * grad_b

    return w, b


def predict_noise(x_t: list[float], w: float, b: float) -> list[float]:
    return [w * v + b for v in x_t]


def denoise(
    x_t: list[float],
    w: float,
    b: float,
    schedule: list[float],
) -> list[list[float]]:
    """Reverse loop: at each step subtract a slice of predicted noise."""
    history = [x_t[:]]
    x = x_t[:]
    for t_cur, t_next in zip(schedule[:-1], schedule[1:]):
        eps_hat = predict_noise(x, w, b)
        # DDPM-style update (simplified, 1D)
        dt = t_cur - t_next
        x = [x[i] - dt * eps_hat[i] for i in range(len(x))]
        history.append(x[:])
    return history


def ascii_plot(rows: list[list[float]], width: int = 56) -> str:
    """Stack denoise steps as a terminal image."""
    lines: list[str] = []
    for row in rows:
        chars = []
        for v in row:
            v = max(0.0, min(1.0, (v + 2) / 4))  # squash for display
            idx = int(v * (width - 1))
            chars.append("█" if idx > width // 3 else "·")
        lines.append("".join(chars))
    return "\n".join(lines)


def save_ppm(path: Path, rows: list[list[float]]) -> None:
    """Save each denoise step as a horizontal stripe in a PPM image."""
    h = len(rows)
    w = len(rows[0])
    pixels: list[tuple[int, int, int]] = []
    for row in rows:
        for v in row:
            v = max(0.0, min(1.0, (v + 2) / 4))
            g = int(v * 255)
            pixels.append((g, g, g))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="ascii") as f:
        f.write(f"P3\n{w} {h}\n255\n")
        for r, g, b in pixels:
            f.write(f"{r} {g} {b}\n")


def mse(a: list[float], b: list[float]) -> float:
    return sum((x - y) ** 2 for x, y in zip(a, b)) / len(a)


def main() -> None:
    parser = argparse.ArgumentParser(description="1D diffusion denoise toy")
    parser.add_argument("--steps", type=int, default=30, help="Denoise steps")
    parser.add_argument("--epochs", type=int, default=800, help="Training epochs")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--save", type=str, default="", help="Optional PPM output path")
    args = parser.parse_args()

    rng = random.Random(args.seed)
    x0 = make_signal()
    w, b = train_noise_predictor(x0, args.steps, args.epochs, rng)

    print("=== TRAIN (forward: clean → noisy) ===")
    t_train = 0.7
    x_noisy = add_noise(x0, t_train, rng)
    print(f"noise level t={t_train:.2f}  MSE(x_noisy, x0)={mse(x_noisy, x0):.4f}")
    print(f"learned noise predictor: eps_hat ≈ {w:.3f} * x_t + {b:.3f}")

    print("\n=== INFER (reverse: noise → structure) ===")
    x_start = add_noise(x0, 1.0, rng)  # almost pure noise
    schedule = [1.0 - i / args.steps for i in range(args.steps + 1)]
    history = denoise(x_start, w, b, schedule)

    print(f"start MSE vs clean: {mse(history[0], x0):.4f}")
    print(f"final MSE vs clean: {mse(history[-1], x0):.4f}")
    print("\nDenoise progression (top=noisy, bottom=recovered):")
    print(ascii_plot(history[:: max(1, len(history) // 8)]))

    if args.save:
        save_ppm(Path(args.save), history)
        print(f"\nSaved step stack → {args.save}")


if __name__ == "__main__":
    main()
