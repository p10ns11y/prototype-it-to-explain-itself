# Gaussian Splatting: Scene as Glowing Blobs

A 3D scene can be millions of anisotropic Gaussians: each has a position, a covariance (“blob shape”), a color, and an opacity. Rendering **splats** those blobs onto the image plane and alpha-blends them. The pipeline is fast, differentiable, and strong at novel views.

Training starts from multi-view photos plus camera poses. The optimizer moves, reshapes, and recolors the blobs until rendered views match the photos.

## Explicit cloud vs continuous field

| Approach | Representation | Query |
|----------|----------------|-------|
| **3D Gaussian Splatting** | Explicit particle cloud | Project / splat to screen |
| **NeRF** | Continuous field | Shoot rays; sample along each ray |

Splats are editable as objects in space. A NeRF is a function you query; editing it usually means changing the field, not moving a particle.

## Why it fits “prototype explains itself”

A splat scene *is* the explanation: you walk around a persistent, renderable 3D account of what the cameras saw. The idea lives in the artifact, not only in a paragraph about the artifact.
