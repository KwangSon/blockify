# AI and Contributor Implementation Guide

## Audience

This document is written for both human contributors and AI coding agents modifying the Blockify repository.

Treat the rules below as implementation constraints, not suggestions.

## First Principle

Before changing code, identify which pipeline stage owns the behavior.

```text
Blender UI
  ↓
Operator
  ↓
Generation Controller
  ↓
Core Stage
  ↓
Output Builder
```

Do not implement functionality in the first convenient file.

## Architectural Rules

### MUST

- keep source meshes non-destructive
- keep generation deterministic
- store geometry logic outside UI/operators
- use explicit intermediate representations
- preserve clear Source → Generated linkage
- make regeneration safe
- validate potentially huge voxel grids before allocation
- make palette assignment happen before color-constrained cuboid merging
- create a small number of Blender objects/datablocks

### MUST NOT

- create one Blender object per voxel by default
- place 500+ lines of geometry logic inside an operator
- read `bpy.context.active_object` from deep core algorithms
- modify the source mesh to simplify implementation
- merge voxels across different palette indices
- rely only on object names to link generated output to source
- introduce random behavior without a fixed deterministic rule
- add CLI architecture as an MVP requirement
- add rigging/AI generation features to the core blockification milestone

## When Requirements Are Ambiguous

Prefer the simplest implementation that preserves these priorities:

1. correctness
2. deterministic behavior
3. source safety
4. clean architecture
5. clean block aesthetic
6. performance
7. additional detail

Do not optimize prematurely by destroying modularity.

## Coding Style

Prefer:

- small modules with one clear responsibility
- descriptive names
- type hints for core data
- dataclasses for stable intermediate records
- pure functions for algorithms where practical
- explicit exceptions for invalid generation states
- comments explaining non-obvious geometry reasoning

Avoid comments that merely restate code.

## Blender API Boundary

Blender types such as:

```python
bpy.types.Object
bpy.types.Mesh
bpy.types.Material
```

should be converted into core-friendly data near the Blender integration boundary.

Core algorithms should ideally work on data such as:

```text
vertices
triangles
bounds
voxel grids
RGB values
palette indices
cuboids
```

This makes algorithms testable and reusable.

## Operator Pattern

Preferred:

```python
class BLOCKIFY_OT_generate(Operator):
    def execute(self, context):
        source = validate_source(context)
        settings = read_settings(source, context)

        try:
            result = generate_block_model(source, settings)
        except BlockifyError as exc:
            self.report({'ERROR'}, str(exc))
            return {'CANCELLED'}

        self.report({'INFO'}, result.summary)
        return {'FINISHED'}
```

Not preferred:

```python
class BLOCKIFY_OT_generate(Operator):
    def execute(self, context):
        # voxelization
        # ray casting
        # k-means
        # greedy merge
        # bmesh construction
        # material creation
        # collection cleanup
        # 1200 lines later...
```

## Data Invariants

AI agents modifying geometry code must preserve:

```text
Every occupied voxel is assigned to exactly one cuboid.
No cuboid contains an unoccupied voxel.
No two cuboids overlap.
Every cuboid has one palette index.
Every cuboid dimension is a positive integer number of cells.
```

If an optimization makes these harder to reason about, add tests before adopting it.

## Deterministic Tie Breaking

Any algorithm that can choose multiple equivalent options must define an order.

Examples:

- voxel iteration order
- cuboid expansion axis order
- palette cluster ordering
- equal-distance color assignment

Never depend implicitly on Python set ordering, hash behavior, or Blender selection order for visible generation output.

## Changing the Pipeline

If adding a new stage, update at least:

- `02_generation_pipeline.md`
- relevant architecture/data contracts
- tests
- user settings if exposed

Do not silently change pipeline semantics in code only.

## Adding a Setting

Every new setting must answer:

1. Is this a user-facing artistic control?
2. Which pipeline stage consumes it?
3. What is its default?
4. What range is safe?
5. Does it affect regeneration metadata?
6. Does it change deterministic output?
7. How is it tested?

Avoid exposing internal tuning constants as UI settings unless users genuinely need them.

## Performance Changes

Measure before changing representations.

Common high-risk mistakes:

- allocating dense 3D Python object arrays for huge grids
- creating a Blender object per cell
- invoking `bpy.ops` repeatedly inside tight loops
- repeated nearest-surface queries without acceleration structures
- rebuilding materials for every block
- leaving temporary evaluated meshes in Blender data

Prefer data-oriented operations and batch mesh creation.

## `bpy.ops` Guidance

Use Blender operators when they represent a real user/context action and there is no better data API.

For internal generation code, prefer direct Blender data APIs and BMesh where appropriate.

Operators are context-sensitive and often harder to test.

## Error Handling

Do not swallow exceptions.

Bad:

```python
try:
    ...
except:
    pass
```

Use explicit Blockify-specific errors where useful.

User-facing errors should include the fix whenever possible.

Example:

```text
Blockify cannot allocate a 620 × 800 × 510 voxel grid.
Increase Block Size from 0.01 to approximately 0.05 or higher.
```

## Scope Discipline

The following requests belong outside the initial Blockify core unless explicitly approved:

- "auto-rig the blockified character"
- "generate the source model from an image"
- "create walking animation"
- "connect to Hunyuan3D/Meshy"
- "batch process a directory from CLI"
- "export Minecraft entities"

Blockify's first job is:

> Existing Blender Mesh → Clean Block Model

Keep that boundary sharp.

## Before Submitting a Change

Check:

- Does source remain unchanged?
- Is generated output deterministic?
- Did I put logic in the correct layer?
- Did I add or update tests?
- Did I introduce hidden Blender context dependencies?
- Does repeated Regenerate leak objects/materials/meshes?
- Are new UI options truly necessary?
- Did I update documentation when behavior changed?

If any answer is uncertain, the change is not ready.
