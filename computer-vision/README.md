# Computer Vision: See → Structure

Classic computer vision turns pixels into edges, depth, poses, boxes, and features. Modern computer vision does the same job with learned encoders (CNNs, Vision Transformers). The output is **measurements about the world** — geometry, identity, motion — not “pretty pixels.”

## The job

```mermaid
flowchart LR
  Pixels["Photos / video"] --> Enc["Vision encoder"]
  Enc --> Struct["Structure:<br/>boxes, depth, pose,<br/>features, embeddings"]
```

## What “structure” means

- **Where** things are (boxes, masks, depth)
- **What** they are (classes, identities)
- **How** they move (tracks, optical flow)
- **How they relate** (scene graphs, embeddings you can compare)

These are facts the rest of a system can act on: planners, agents, 3D reconstructors, captioners.

## Contrast

| System | Arrow | Product |
|--------|-------|---------|
| Computer vision | pixels → meaning | measurements / embeddings |
| Diffusion | meaning or noise → pixels | new observations |
| Gaussian splatting | multi-view photos → editable 3D | a renderable scene |

Vision lifts the world into a shared space. Generators and 3D carriers put something back you can see.

## Run

| File | What it does |
|------|----------------|
| `edge_measure.py` | Synthetic 24×24 scene → Sobel edges → bounding box + centroid (stdlib only) |

```bash
python computer-vision/edge_measure.py
python computer-vision/edge_measure.py --save computer-vision/out_edges.ppm
```

## WHAT YOU JUST SAW

Pixels became **numbers about the world**: edge count, gradient strength, box size, centroid. Nothing here invents new pixels — it **reads** structure out of an image. Contrast that with diffusion, which starts from noise and **writes** pixels into place.
