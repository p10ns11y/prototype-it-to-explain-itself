# Multimodal Spine: One World, Many Tongues

**One world state, many sensors and languages.**

Vision, text, generators, and 3D carriers meet in a shared latent (or token) space. Questions in language can move geometry or pixels because they land in the same place the vision encoder wrote into.

## Map

```mermaid
flowchart TD
  World["World / scene"]
  CV["Vision encoder CV<br/>photos, video"]
  Latent["Shared latent / tokens<br/>meaning both sides can touch"]
  Lang["Language / agents<br/>questions, plans, captions"]
  Diff["Generators<br/>diffusion: new views or images"]
  GS["3D carriers<br/>Gaussian splats: editable scene"]

  World --> CV
  CV --> Latent
  Lang --> Latent
  Latent --> Lang
  Latent --> Diff
  Latent --> GS
  Diff --> World
  GS --> World
```

## Roles

- **CV** lifts pixels into the shared space.
- **Language** (and other modalities) lands in the same space so a question like “what’s behind the chair?” can drive geometry or pixels.
- **Diffusion** samples *new* observations consistent with the latent.
- **Splatting** stores a *persistent, renderable* 3D explanation you can walk around — a prototype that explains itself by being the scene.

## One sentence

**See (CV) → bind (multimodal latent) → show (diffusion or splats) so the artifact teaches the idea without a lecture.**

## Run

| File | What it does |
|------|----------------|
| `shared_latent.py` | Fake vision encoder + question embedding in one 8-D space; dot-product retrieval |

```bash
python multimodal/shared_latent.py
python multimodal/shared_latent.py --question "where is the window"
python multimodal/shared_latent.py --question "what material is the chair"
```

## WHAT YOU JUST SAW

Vision wrote a scene vector into a shared space. Language asked a question in that **same** space. A dot product picked the best-matching attribute — no separate pipeline per modality.

That binding is what lets a caption steer a generator or a splat edit: different tongues, one latent room. The script is hand-wired so you can read every vector; production models learn the encoders from data.
