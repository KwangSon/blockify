# Geometry and Cuboid Decomposition

## Artistic Target

Blockify is not merely a voxelizer.

The desired visual result is a model that looks intentionally assembled from clean rectangular blocks.

The most important geometry feature is therefore **cuboid decomposition**.

## Internal Voxel Representation

The source mesh is first represented on a regular grid.

Example 2D slice:

```text
. . X X X .
. X X X X .
. X X X X .
. . X X . .
```

`X` means occupied.

The voxel grid allows arbitrary source geometry to be converted into a representation that is easy to reason about deterministically.

## Final Representation

Do not emit one object per occupied voxel.

Instead, merge compatible cells into axis-aligned cuboids.

Example:

```text
X X X X
X X X X
X X X X
```

should ideally become one:

```text
size = (4, 3, 1)
```

cuboid.

## Merge Constraints

Cells may belong to the same cuboid only if:

1. all cells are occupied
2. all cells have the same palette index
3. all cells are unassigned
4. the resulting region is a complete rectangular prism

Never merge through empty cells.

Never merge different palette indices in the initial implementation.

## Deterministic Greedy Strategy

An initial deterministic strategy is sufficient.

Example:

1. iterate cells in a defined order, such as Z → Y → X or X → Y → Z
2. when an unconsumed occupied cell is found:
   - expand along X while compatible
   - expand the resulting strip along Y while the full area is compatible
   - expand the resulting rectangle along Z while the full volume is compatible
3. emit one cuboid
4. mark its cells consumed
5. continue

Pseudo-code:

```python
for cell in ordered_cells:
    if not compatible_unconsumed(cell):
        continue

    sx = maximal_x_extent(cell)
    sy = maximal_y_extent(cell, sx)
    sz = maximal_z_extent(cell, sx, sy)

    cuboid = Cuboid(cell, sx, sy, sz)
    consume(cuboid)
```

This does not guarantee a globally minimal cuboid count.

That is acceptable for the MVP.

Predictability and maintainability matter more than solving an expensive optimization problem.

## Axis Bias

Greedy decomposition is affected by expansion order.

For example:

```text
expand X → Y → Z
```

may produce a different decomposition than:

```text
expand Z → Y → X
```

The initial implementation must choose and document one order.

Do not silently change the order because visual output may change across versions.

Future versions may expose merge strategy as a setting.

## Color Boundaries

Color boundaries are geometry boundaries for cuboid merging.

Example:

```text
Y Y Y Y
Y Y Y Y
W W W W
W W W W
```

where `Y` = yellow and `W` = white should produce at least:

```text
Yellow cuboid
White cuboid
```

even though the full shape is geometrically rectangular.

This is intentional: color blocks are part of the art style.

## Hidden Face Removal

There are two valid implementation levels.

### Level A — Emit complete cuboids

Each cuboid has six faces.

Advantages:

- simple
- easy to edit
- semantically clear blocks

Disadvantages:

- coplanar/internal faces may overlap

### Level B — Remove invisible/internal faces

When a cuboid face is completely hidden by another generated region, do not emit it.

Advantages:

- cleaner rendering mesh
- fewer polygons

Disadvantages:

- more complex mesh building

The MVP may start with Level A if required, but hidden-face removal is a core target.

## Separate Cuboids vs Single Mesh

The default generated result should preferably be a **single Blender mesh**, not hundreds of objects.

Cuboids can remain logically distinct in intermediate data while being emitted into one mesh.

Reasons:

- Blender scene performance
- simpler selection
- simpler export
- fewer object datablocks
- easier material reuse

Future character-oriented workflows may introduce optional separate block objects, but that is not the default MVP.

## Mesh Construction Rules

Generated faces should:

- be axis-aligned
- use flat shading
- avoid smoothing across cuboid corners
- use exact grid-aligned coordinates
- avoid tiny floating-point drift

Coordinates should derive mathematically from:

```text
grid_origin + grid_index * block_size
```

not accumulated floating-point stepping.

## Geometry Invariants

After decomposition:

- every occupied voxel is covered exactly once
- no empty voxel is covered
- every cuboid has positive integer dimensions
- every cuboid uses one palette index
- cuboids do not overlap in voxel space

These invariants should have tests.

## Style vs Fidelity

Increasing resolution should preserve more detail but usually increase:

- voxel count
- cuboid count
- generation time

Decreasing resolution should produce:

- stronger block aesthetic
- simpler silhouettes
- fewer cuboids

The algorithm must not add smoothing intended to recreate the original curved surface.

Angular/blocky output is the desired result.
