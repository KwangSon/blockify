# Color and Material Handling

## Goal

Blockify should preserve the recognizable color design of the source while replacing complex material/texture detail with a small set of flat block colors.

The generated model should look intentionally stylized, not like a low-resolution copy of a PBR texture.

## Color Pipeline

```text
Source Material / Texture
          ↓
   Surface Sampling
          ↓
   Raw Voxel Colors
          ↓
 Palette Quantization
          ↓
 Palette Index / Voxel
          ↓
   Cuboid Merging
          ↓
 Flat Blender Materials
```

## Supported Source Color Priority

The implementation should have an explicit priority order.

Recommended initial policy:

1. connected Base Color image texture when evaluable
2. material Base Color
3. vertex/color attribute when explicitly supported
4. neutral fallback color

Do not silently return black because a shader graph is unsupported.

If the source color cannot be evaluated, use a documented fallback and report the limitation.

## Texture Sampling

For texture-based materials, sampling conceptually requires:

1. identify a source surface point
2. identify the source triangle / polygon
3. obtain interpolated UV coordinates
4. evaluate the Base Color texture at that UV
5. obtain linear or sRGB color consistently

The implementation must explicitly manage color space.

Do not mix linear RGB samples with sRGB samples in the same quantization set.

## Representative Voxel Color

A voxel may correspond to a region containing multiple source colors.

Do not rely blindly on one center-point sample.

Possible MVP approach:

- sample several representative points associated with the voxel
- reject invalid/background samples
- choose median or clustered dominant color

Median/dominant color often preserves stylized regions better than an arithmetic mean, which can create muddy colors.

Example:

```text
Samples:
yellow
yellow
yellow
dark brown

Mean    → dirty orange
Dominant→ yellow
```

For Blockify, dominant/representative color is often preferable.

## Palette Quantization

The user provides a target palette size, for example:

```text
4
8
12
16
```

Quantization maps raw voxel colors into that limited set.

The MVP algorithm may use:

- deterministic k-means with fixed initialization/seed
- median cut
- octree quantization
- another deterministic clustering method

The important requirements are:

- stable output
- visually meaningful clusters
- no random palette changes between regenerations

## Palette Size Semantics

`Palette Size = N` is a maximum target, not a promise that exactly N visually distinct colors always exist.

For a two-color source, requesting 8 colors should not invent six arbitrary colors.

## Color Compatibility and Merging

Cuboids may merge only when their voxels share the same **quantized palette index**.

Do not compare raw RGB using arbitrary epsilon values during cuboid decomposition.

Correct:

```python
voxel_a.palette_index == voxel_b.palette_index
```

Avoid:

```python
distance(voxel_a.rgb, voxel_b.rgb) < 0.0317
```

in the merge stage.

Any perceptual similarity decision belongs in quantization, before geometry merging.

## Output Materials

Generated materials should be simple.

Initial material target:

- Principled BSDF or simple Blender-compatible surface
- Base Color = palette color
- Metallic = 0 unless a future mode explicitly preserves it
- conservative/default roughness
- no complex node networks
- flat visual result

Each palette color should normally create one material datablock for the generated model.

Suggested names:

```text
Blockify_Palette_00
Blockify_Palette_01
...
```

## Texture-Free Output

The initial preferred Blockify output is material-color based rather than texture-atlas based.

Reasons:

- easier inspection in Blender
- easy recoloring
- simple block aesthetic
- no UV requirement for generated cuboids
- less fragile than preserving source textures

Texture atlas generation may be added later as an optimization/export feature.

## Color Preservation Is Not Shader Preservation

Do not attempt to reproduce:

- procedural noise networks
- subsurface scattering
- clearcoat complexity
- animated shaders
- displacement
- normal maps

The first product promise is **color recognition**, not shader equivalence.

## Example — Tamago Sushi

Source may visually contain:

- many yellows from lighting and texture
- several rice whites
- dark nori
- ambient shadows

With `Palette Size = 6`, a reasonable output might be:

```text
0  light rice
1  rice shadow
2  egg yellow
3  egg shadow
4  nori
5  accent/highlight
```

This is preferable to preserving hundreds of barely distinguishable colors.

## Tests

Color tests should include:

- solid material color source
- two-color hard boundary
- textured checkerboard
- palette size reduction
- deterministic repeated quantization
- unsupported shader fallback
- color boundary preventing cuboid merge
