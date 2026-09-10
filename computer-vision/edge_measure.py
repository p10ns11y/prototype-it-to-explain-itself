#!/usr/bin/env python3
"""
See → structure: pixels to edges and a bounding box with real numbers.

Synthetic 24×24 image: bright rectangle on dark background.
Sobel edges + simple connected-region stats — no deep learning, no deps.

Run from project root:
    python computer-vision/edge_measure.py
    python computer-vision/edge_measure.py --save computer-vision/out_edges.ppm
"""

from __future__ import annotations

import argparse
from pathlib import Path


def make_scene(width: int = 24, height: int = 24) -> list[list[int]]:
    """Bright box — the 'object' we want to measure."""
    img = [[20] * width for _ in range(height)]
    for y in range(6, 18):
        for x in range(8, 20):
            img[y][x] = 230
    return img


def sobel_edges(img: list[list[int]]) -> list[list[float]]:
    h, w = len(img), len(img[0])
    gx_k = [[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]]
    gy_k = [[-1, -2, -1], [0, 0, 0], [1, 2, 1]]
    edges = [[0.0] * w for _ in range(h)]

    for y in range(1, h - 1):
        for x in range(1, w - 1):
            gx = gy = 0.0
            for ky in range(3):
                for kx in range(3):
                    v = img[y + ky - 1][x + kx - 1]
                    gx += v * gx_k[ky][kx]
                    gy += v * gy_k[ky][kx]
            edges[y][x] = (gx * gx + gy * gy) ** 0.5
    return edges


def threshold_mask(edges: list[list[float]], t: float) -> list[list[bool]]:
    return [[e >= t for e in row] for row in edges]


def bounding_box(mask: list[list[bool]]) -> tuple[int, int, int, int] | None:
    ys, xs = [], []
    for y, row in enumerate(mask):
        for x, on in enumerate(row):
            if on:
                ys.append(y)
                xs.append(x)
    if not xs:
        return None
    return min(xs), min(ys), max(xs), max(ys)


def centroid(img: list[list[int]], thresh: int = 100) -> tuple[float, float]:
    sx = sy = n = 0
    for y, row in enumerate(img):
        for x, v in enumerate(row):
            if v >= thresh:
                sx += x
                sy += y
                n += 1
    return (sx / n, sy / n) if n else (0.0, 0.0)


def save_ppm(path: Path, img: list[list[int]], edges: list[list[float]]) -> None:
    """Left half = raw, right half = edge magnitude."""
    h, w = len(img), len(img[0])
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="ascii") as f:
        f.write(f"P3\n{w * 2} {h}\n255\n")
        for y in range(h):
            for x in range(w):
                g = img[y][x]
                f.write(f"{g} {g} {g}\n")
            for x in range(w):
                e = min(255, int(edges[y][x]))
                f.write(f"{e} {e} {e}\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Pixels → edges → measurements")
    parser.add_argument("--edge-threshold", type=float, default=80.0)
    parser.add_argument("--save", type=str, default="")
    args = parser.parse_args()

    img = make_scene()
    edges = sobel_edges(img)
    mask = threshold_mask(edges, args.edge_threshold)
    bbox = bounding_box(mask)
    cx, cy = centroid(img)

    edge_count = sum(row.count(True) for row in mask)
    max_edge = max(max(row) for row in edges)

    print("=== INPUT ===")
    print(f"image size: {len(img[0])}×{len(img)}")
    print(f"bright-region centroid (intensity ≥ 100): ({cx:.1f}, {cy:.1f})")

    print("\n=== STRUCTURE (edges) ===")
    print(f"edge pixels (≥ {args.edge_threshold}): {edge_count}")
    print(f"max gradient magnitude: {max_edge:.1f}")

    if bbox:
        x0, y0, x1, y1 = bbox
        w, h = x1 - x0 + 1, y1 - y0 + 1
        print(f"edge bounding box: x={x0}..{x1}, y={y0}..{y1}  →  {w}×{h} px")
        print(f"box center: ({(x0 + x1) / 2:.1f}, {(y0 + y1) / 2:.1f})")
    else:
        print("no edge box found — lower --edge-threshold")

    print("\n=== CONTRAST WITH DIFFUSION ===")
    print("This script *reads* pixels into facts. Diffusion *writes* pixels from noise.")

    if args.save:
        save_ppm(Path(args.save), img, edges)
        print(f"\nSaved raw|edges PPM → {args.save}")


if __name__ == "__main__":
    main()
