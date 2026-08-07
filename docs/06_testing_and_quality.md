# Testing and Quality

## Purpose

Blockify changes geometry, colors, Blender datablocks, and generated/source relationships.

Visual inspection alone is not sufficient.

Tests should focus on invariants that must remain true even as algorithms are optimized.

## Test Layers

### 1. Pure algorithm tests

Test without depending on active Blender UI context where possible.

Primary targets:

- voxel grid indexing
- occupancy representation
- palette quantization
- cuboid decomposition
- cuboid coverage invariants

### 2. Blender integration tests

Test:

- registration
- operator validation
- source preservation
- generated object creation
- material creation
- regeneration
- cleanup

### 3. Golden scene tests

Maintain a very small set of known source meshes and expected high-level results.

Examples:

- cube
- two-color stacked cube
- L shape
- sphere
- open plane
- simple sushi-like shape

Golden tests should compare stable structural properties rather than binary `.blend` bytes.

## Required Geometry Invariants

For every successful cuboid decomposition:

```text
occupied voxel coverage == exactly once
empty voxel coverage    == zero
cuboid overlap          == none
cuboid dimensions       > 0
cuboid palette          == one palette index
```

These are mandatory.

## Core Test Cases

### Full Rectangular Volume

Input occupancy:

```text
2 × 2 × 2 fully occupied
single palette
```

Expected:

```text
1 cuboid of size 2 × 2 × 2
```

### Two Colors

Input:

```text
top layer    = yellow
bottom layer = white
```

Expected:

- no cuboid crosses the color boundary
- ideally 2 cuboids for a simple full rectangular case

### L Shape

Input:

```text
XXX
X..
X..
```

Expected:

- complete coverage
- no empty cell covered
- deterministic decomposition

Do not require a mathematically minimal cuboid count unless the algorithm explicitly guarantees it.

### Hole

Input:

```text
XXX
X.X
XXX
```

Expected:

- center empty cell remains uncovered

### Repeated Generation

Generate twice with identical source/settings.

Expected:

- equivalent structural result
- same palette ordering under deterministic rules
- no accumulating temporary datablocks

## Color Tests

Test:

- solid red material → red output palette
- hard red/blue boundary remains separate after merge
- 100 similar colors with palette size 4 produce <= 4 colors
- same input/settings produce same palette order
- unsupported shader path produces documented fallback, not crash

## Source Preservation Tests

Record before generation:

- source vertex count
- source mesh identity where relevant
- source material slots
- source transform
- source name

After generation, assert source remains unchanged unless an operation is explicitly documented as non-preserving.

## Regeneration Tests

Scenario:

1. generate output
2. change block size
3. regenerate

Verify:

- new result uses new setting
- source unchanged
- stale Blockify-owned result removed/replaced
- no duplicate generated collections accumulate
- old result remains if regeneration fails before commit where transaction behavior is implemented

## Performance Guardrails

Do not use exact runtime as a fragile unit test.

Instead test safety behavior:

- grid size estimator works
- excessive grid request is rejected before enormous allocation
- reasonable small fixtures complete

Performance benchmarks may be maintained separately.

## Manual QA Checklist

Before release, manually test:

- installation
- enable/disable add-on
- generate from basic cube
- generate from imported GLB
- textured source
- non-uniform object scale
- rotated source object
- open mesh
- multiple source objects in scene
- regenerate repeatedly
- save/reopen `.blend`
- undo/redo
- delete source after generation
- rename source/generated objects

## Definition of Done for a Feature

A geometry/color feature is not complete when it merely "looks right" once.

It is complete when:

1. behavior is documented
2. core invariants are tested
3. invalid inputs fail clearly
4. source data is preserved
5. repeated generation is deterministic
6. Blender datablocks are cleaned correctly
