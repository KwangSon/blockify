# Blockify Documentation

These documents define the Blockify Blender add-on for both human contributors and AI coding agents.

Read in this order:

1. `00_overview.md` — product scope, principles, terminology
2. `01_architecture.md` — package boundaries and data ownership
3. `02_generation_pipeline.md` — end-to-end generation stages
4. `03_geometry_and_cuboids.md` — voxel representation and cuboid decomposition
5. `04_color_and_materials.md` — source color sampling and palette rules
6. `05_blender_addon_design.md` — Blender UX and Rigify-inspired Generate/Regenerate model
7. `06_testing_and_quality.md` — invariants, tests, release quality
8. `07_ai_contributor_guide.md` — concrete implementation rules for humans and AI agents
9. `08_milestones.md` — implementation order and MVP definition

## Canonical Product Boundary

> Existing Blender Mesh → Clean Block Model

Blockify is a native Blender add-on. It is not primarily a CLI tool, image-to-3D generator, rigging system, or animation system.

When code and documentation disagree, update both in the same change. Do not silently redefine product behavior in implementation only.
