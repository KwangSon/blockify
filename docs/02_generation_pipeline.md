# Generation Pipeline

## Overview

The Blockify generation pipeline is a sequence of explicit transformations.

```text
Selected Blender Mesh
        ↓
Source Preparation
        ↓
Grid Construction
        ↓
Occupancy / Voxelization
        ↓
Optional Interior Fill
        ↓
Source Color Sampling
        ↓
Palette Quantization
        ↓
Palette Assignment
        ↓
Cuboid Decomposition
        ↓
Output Mesh Construction
        ↓
Flat Materials
        ↓
Generated Blender Object
```

Every stage should be independently understandable and testable.

## Stage 1 — Source Preparation

Input:

- selected mesh object
- evaluated geometry
- Blockify settings

The source object must not be modified.

Use evaluated geometry when appropriate so visible modifiers can be reflected in the generated result.

Before voxelization, determine:

- world/local-space policy
- source bounds
- grid origin
- grid cell size
- grid dimensions

### Transform Policy

The initial implementation should choose one consistent coordinate policy.

Recommended:

1. sample evaluated mesh in source-local coordinates
2. generate the block model in the same local coordinate frame
3. copy source object transform to the generated object

This avoids baking arbitrary object transforms into geometry unless explicitly desired.

Do not mix local and world coordinates mid-pipeline.

## Stage 2 — Grid Construction

`block_size` is the primary style parameter.

For source bounding box:

```text
min = (min_x, min_y, min_z)
max = (max_x, max_y, max_z)
```

Grid dimensions are conceptually:

```text
ceil((max - min) / block_size)
```

Add only the minimum padding required for robust sampling.

### Safety Limit

Very small block sizes can explode memory and runtime.

The implementation must estimate grid cell count before allocation.

Example:

```text
grid_cells = size_x * size_y * size_z
```

If the count exceeds a configured safety threshold:

- do not proceed silently
- show the user an actionable error
- suggest increasing Block Size

## Stage 3 — Occupancy

A voxel is occupied when the source volume meaningfully intersects the corresponding grid cell.

The exact algorithm may evolve.

Possible approaches include:

- voxel remesh-derived occupancy
- ray parity / inside-outside tests
- triangle-box intersection
- sampled surface + interior filling

The MVP algorithm should prioritize correctness and predictable behavior over exotic optimization.

### Important

Surface-only sampling is insufficient when `Fill Interior` is enabled.

A solid source should result in a solid block volume, not merely a hollow shell.

## Stage 4 — Interior Fill

When `Fill Interior = true`, closed source meshes should generate interior occupied cells.

When false, Blockify may preserve only surface-adjacent cells.

The implementation must document behavior for non-manifold and open meshes.

Do not pretend an open mesh has a well-defined interior unless the chosen algorithm provides a clearly documented heuristic.

## Stage 5 — Color Sampling

Color sampling happens against the **source model**, not the generated cuboids.

Each occupied voxel should receive a representative source color before palette quantization.

Recommended conceptual process:

```text
voxel
  ↓
sample one or more representative surface positions
  ↓
find nearest source surface
  ↓
evaluate source color/material
  ↓
raw voxel color
```

Color details are defined in `04_color_and_materials.md`.

## Stage 6 — Palette Quantization

Raw sampled colors are reduced to a finite palette.

Example:

```text
15,000 sampled RGB values
          ↓
     quantization
          ↓
       8 colors
```

Palette generation must be deterministic.

The palette should be computed before cuboid merging because color compatibility is one of the merge constraints.

## Stage 7 — Palette Assignment

Every occupied voxel receives an integer palette index.

Example:

```text
0 = rice white
1 = rice shadow
2 = egg yellow
3 = egg shadow
4 = nori dark green
```

After this stage, geometry algorithms should generally operate on palette indices, not floating-point RGB comparisons.

## Stage 8 — Cuboid Decomposition

Input:

```text
occupied[x, y, z]
palette_index[x, y, z]
```

Output:

```text
List[Cuboid]
```

A cuboid may include multiple voxels only when all included cells:

- are occupied
- have the same palette index
- are not already consumed
- form an axis-aligned rectangular volume

The goal is not necessarily to find the mathematically minimum cuboid cover.

The goal is to produce:

- deterministic
- clean
- visually coherent
- reasonably compact

results.

See `03_geometry_and_cuboids.md`.

## Stage 9 — Mesh Construction

Prefer one generated Blender mesh containing the visible surfaces of all cuboids unless an explicit generation mode requires separate objects.

Do not create thousands of Blender objects.

For each cuboid:

- calculate its physical bounds from the grid
- emit only required exterior faces where possible
- assign material index according to palette index
- preserve hard/flat normals

The output should be simple to inspect and export.

## Stage 10 — Materials

Create a small set of flat materials corresponding to the output palette.

One palette color should map to one reusable material in the generated model.

Avoid:

```text
Cube.001 → Material.001
Cube.002 → Material.002
Cube.003 → Material.003
```

when all three have the same color.

Prefer:

```text
Palette_00
Palette_01
Palette_02
...
```

## Stage 11 — Generated Object

The result should be:

- clearly named
- placed in the Blockify output collection
- linked to its source
- marked as generated
- safe to regenerate

Suggested object name:

```text
<SourceName>_BLOCKIFIED
```

Naming is for humans. Internal source linkage must not rely solely on the name.

## Generation Statistics

After a successful generation, expose useful stats:

- source triangles
- grid dimensions
- occupied voxels
- palette colors
- generated cuboids
- generated vertices/faces
- generation time

These numbers are important for both UX and algorithm development.
