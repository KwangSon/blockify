# Architecture

## Design Goal

Blockify should follow the same broad architectural discipline that makes mature Blender add-ons such as Rigify maintainable:

- Blender registration is separate from algorithms.
- Operators orchestrate work but do not contain large algorithms.
- UI code contains no geometry logic.
- Core generation stages have explicit inputs and outputs.
- Generated results are derived from a source object and stored settings.
- Functionality is modular enough to replace individual generation stages later.

## Proposed Package Structure

```text
blockify/
├── __init__.py
├── blender_manifest.toml
│
├── generate.py
│
├── operators/
│   ├── __init__.py
│   ├── generate.py
│   └── regenerate.py
│
├── ui/
│   ├── __init__.py
│   └── panels.py
│
├── properties/
│   ├── __init__.py
│   └── settings.py
│
├── core/
│   ├── __init__.py
│   ├── model.py
│   ├── voxelize.py
│   ├── color_sample.py
│   ├── palette.py
│   ├── cuboids.py
│   └── mesh_data.py
│
├── generators/
│   ├── __init__.py
│   ├── base.py
│   └── cuboid.py
│
├── utils/
│   ├── __init__.py
│   ├── blender.py
│   ├── mesh.py
│   ├── materials.py
│   ├── collections.py
│   └── log.py
│
└── tests/
    ├── test_voxelize.py
    ├── test_palette.py
    ├── test_cuboids.py
    └── test_generation.py
```

The exact filenames may evolve, but the dependency direction below is an invariant.

## Dependency Direction

```text
UI
 ↓
Operators
 ↓
Generator / generate.py
 ↓
Core algorithms
 ↓
Small utility/data modules
```

Blender-specific adapters may call Blender APIs, but core geometry algorithms should avoid direct dependence on UI state.

### Forbidden dependency patterns

Do not introduce:

```text
core → ui
core → operator
palette algorithm → bpy.context
cuboid algorithm → active Blender selection
```

Core functions should receive explicit data.

## Main Generation Controller

`generate.py` owns the high-level generation transaction.

Conceptually:

```python
def generate(source_object, settings):
    source = prepare_source(source_object)

    grid = voxelize(source.mesh, settings)
    colors = sample_source_colors(source, grid, settings)
    palette = build_palette(colors, settings)
    colored_grid = assign_palette(grid, colors, palette)

    cuboids = decompose_into_cuboids(colored_grid, settings)
    mesh_data = build_output_mesh(cuboids, palette, settings)

    generated_object = create_blender_object(mesh_data)
    attach_generation_metadata(
        generated_object,
        source_object,
        settings,
    )

    return generated_object
```

This is orchestration only. Each substantial step belongs in its own module.

## Core Data Model

Use explicit intermediate data rather than passing Blender objects throughout the pipeline.

Suggested conceptual types:

```python
@dataclass(frozen=True)
class GridSpec:
    origin: Vector3
    cell_size: float
    size_x: int
    size_y: int
    size_z: int


@dataclass
class VoxelGrid:
    spec: GridSpec
    occupied: Array3D[bool]


@dataclass
class ColoredVoxelGrid:
    spec: GridSpec
    occupied: Array3D[bool]
    palette_index: Array3D[int]


@dataclass(frozen=True)
class Cuboid:
    x: int
    y: int
    z: int
    size_x: int
    size_y: int
    size_z: int
    palette_index: int
```

Actual Python storage may use lists, arrays, compact integer buffers, or NumPy only if dependency policy explicitly permits it.

Do not let storage choices leak into every layer.

## Source / Generated Relationship

The generated object must contain enough metadata to identify:

- that it is a Blockify-generated object
- its source object
- generation version/schema
- settings required for regeneration

Example conceptual metadata:

```text
blockify.generated = true
blockify.source_object = <reference>
blockify.schema_version = 1
blockify.block_size = 0.10
blockify.palette_size = 8
blockify.fill_interior = true
blockify.merge_cuboids = true
```

Prefer Blender-native pointer properties where reliable. Avoid depending on names alone because users can rename objects.

## Generated Collections

Do not scatter generated objects unpredictably.

Recommended initial behavior:

```text
Scene Collection
├── MySource
└── BLOCKIFY
    └── MySource_BLOCKIFIED
```

If multiple sources are supported later, preserve one clear generated result per source.

## Regeneration

Regeneration is not an incremental mesh edit in the MVP.

Preferred behavior:

1. identify source
2. read current Blockify settings
3. generate replacement result
4. replace old generated object only after generation succeeds
5. preserve user-visible transform/collection behavior where defined

If generation fails, the previous valid generated object should remain whenever practical.

## Error Boundaries

User-facing validation belongs near the operator/controller boundary.

Examples:

- no active object
- active object is not a mesh
- object has invalid dimensions
- block size is too small and would create an unsafe grid
- unsupported material setup

Core algorithms should raise explicit errors rather than silently guessing.

## Determinism

Given the same evaluated source geometry and the same settings, Blockify should generate the same voxel occupancy, palette assignment, and cuboid decomposition.

Avoid nondeterministic iteration where it changes visible output.

If an algorithm has ties, define a deterministic tie-break rule.
