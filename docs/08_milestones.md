# Development Milestones

## Strategy

Build Blockify in vertical slices that produce visible Blender results early.

Do not implement the entire ideal pipeline before a usable Generate button exists.

Each milestone must leave the add-on in a coherent state.

## M0 — Add-on Skeleton

Goal: Blockify installs and behaves like a real Blender add-on.

Deliver:

- `blender_manifest.toml`
- module registration
- Blockify sidebar panel
- settings property group
- `BLOCKIFY_OT_generate`
- validation for selected mesh
- generated collection setup

Generate may initially create a trivial placeholder object.

Done when:

- add-on installs/enables
- panel appears
- operator works with Undo
- disable/uninstall does not leave broken registration

## M1 — Geometry-only Blockification

Goal: Produce a recognizable block model with one color.

Deliver:

- source preparation
- bounds/grid calculation
- safety grid estimation
- voxel occupancy
- optional interior fill
- basic cuboid decomposition
- output mesh creation
- flat single material

Ignore source texture/color for this milestone.

Done when:

- cube blockifies correctly
- sphere becomes recognizable block volume
- source remains untouched
- generated result is deterministic

## M2 — Cuboid Quality

Goal: Make output clean rather than merely voxelized.

Deliver:

- deterministic cuboid merging
- documented axis order
- no duplicate voxel coverage
- optional hidden-face optimization
- generation statistics

Done when:

- full rectangular regions collapse into large cuboids
- L shapes do not fill empty space
- repeated generation produces same decomposition
- cuboid count is meaningfully below occupied voxel count on simple shapes

## M3 — Color Preservation

Goal: Preserve recognizable source color regions.

Deliver:

- source Base Color sampling
- material fallback color
- per-voxel raw color
- deterministic palette quantization
- palette assignment
- color-constrained cuboid merging
- flat palette materials

Done when:

- two-color object keeps its boundary
- textured test object produces recognizable colors
- palette size limit is respected
- same input gives stable palette/result

## M4 — Generate / Regenerate Model

Goal: Establish the Rigify-like generated workflow.

Deliver:

- generated metadata
- source linkage
- persisted per-source settings
- Regenerate operator
- safe replacement transaction
- generated-object cleanup
- UI stats/result section

Done when:

- user can generate
- change Block Size
- regenerate
- old generated result is replaced cleanly
- source remains unchanged
- repeated regeneration does not leak datablocks

## M5 — Robust Blender Behavior

Goal: Make the add-on usable on real assets.

Deliver:

- imported GLB testing
- evaluated modifier handling
- transform policy validation
- open/non-manifold mesh handling
- clearer error reporting
- progress/status handling
- performance guardrails

Done when a small collection of real game assets can be processed without manual scene cleanup.

## Post-MVP Candidates

Only after the core is stable:

- alternate cuboid decomposition strategies
- user-defined palettes
- texture atlas output
- optional separate-block output
- character-oriented part grouping
- origin/scale normalization tools
- geometry-node-assisted previews
- batch actions inside Blender UI

Rigging, animation, and image-to-3D integration should remain separate concerns unless the project scope is intentionally expanded.

## MVP Definition

The MVP is complete when a Blender user can:

1. import/select a GLB mesh
2. open Blockify
3. choose Block Size and Palette Size
4. click Blockify
5. receive a recognizable cuboid-based model
6. modify settings
7. regenerate non-destructively
8. export or continue editing the result using ordinary Blender workflows

No external automation is required for MVP completion.
