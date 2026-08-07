# Blockify

**Turn any 3D mesh into clean, blocky geometry — directly inside Blender.**

Blockify is a Blender add-on that converts existing 3D meshes into simplified models built from cubes and cuboids.

It is designed for block-style and voxel-inspired artwork, including game assets, stylized props, characters, and AI-generated 3D models.

## How It Works

Select a mesh in Blender and generate a blockified version of it.

```text
Source Mesh
     ↓
  Blockify
     ↓
Generated Block Model
```

Blockify does not modify the original object.

Much like Blender's Rigify workflow, the source object acts as the input while Blockify creates and manages a generated result.

Change the settings, regenerate, and iterate until the result matches the style you want.

## Features

- Convert any Blender mesh into block-style geometry
- Adjustable block resolution
- Generate cubes or merged cuboids
- Merge neighboring blocks to reduce complexity
- Preserve colors from the source model
- Reduce source colors into a small, consistent palette
- Generate simple flat materials
- Preserve the original source object
- Regenerate block models after changing settings
- Designed as a native Blender add-on workflow

## Blockify vs. Voxelization

Traditional voxelization often produces one cube for every occupied voxel.

A simple shape may become hundreds or thousands of separate cubes.

```text
■ ■ ■ ■ ■ ■
■ ■ ■ ■ ■ ■
■ ■ ■ ■ ■ ■
```

Blockify can merge compatible neighboring regions into larger cuboids.

```text
┌───────────┐
│           │
└───────────┘
```

This produces cleaner geometry and a stronger hand-built block aesthetic.

## Color Preservation

Blockify can sample colors from the original model and transfer them to the generated blocks.

A detailed source model may contain hundreds of slightly different colors.

Blockify can reduce them to a smaller palette:

```text
Source Model
437 colors

     ↓

Blockify
Palette Size: 8

     ↓

Generated Model
8 colors
```

This helps produce a more consistent block-style appearance.

## Workflow

### 1. Select a Source Mesh

Import a model or select an existing mesh in your Blender scene.

The source can be:

- a traditionally modeled asset
- a sculpted model
- an imported GLB
- an AI-generated 3D model

### 2. Open Blockify

Open the **Blockify** panel in the 3D View sidebar.

### 3. Configure the Style

Choose how much detail the generated model should retain.

Example:

```text
BLOCKIFY
────────────────────

Block Size
[ 0.10 ]

Generation
Mode
[ Cuboid ]

Colors
[x] Preserve Colors
Palette Size
[ 8 ]

Geometry
[x] Fill Interior
[x] Merge Blocks
[x] Remove Hidden Faces

────────────────────

[      BLOCKIFY      ]
```

Smaller blocks preserve more detail.

Larger blocks produce a stronger, chunkier style.

### 4. Generate

Press **Blockify**.

The source object remains untouched and a new generated model is created.

```text
Sushi_Source
Sushi_BLOCKIFIED
```

### 5. Regenerate

Blockify keeps the relationship between the source object, generation settings, and generated model.

Change the settings and press **Regenerate** to rebuild the block model.

```text
Source Mesh
     +
Blockify Settings
     ↓
  Regenerate
     ↓
Generated Model
```

This makes Blockify a non-destructive, iterative workflow rather than a one-time conversion tool.

## Generation Modes

Blockify is designed around interchangeable generation methods.

The initial implementation focuses on **Cuboid** generation.

### Cuboid

Creates a block model while merging compatible neighboring regions into larger rectangular blocks.

Future generation methods may explore different block-based styles.

## Source and Generated Objects

Blockify treats generated geometry separately from the source model.

The source remains the authoritative input.

```text
Collection
│
├── Character_Source
│
└── Character_BLOCKIFIED
```

The generated object can safely be deleted and recreated at any time.

## Use Cases

Blockify can be useful for:

- Minecraft-inspired artwork
- block-style games
- voxel-inspired environments
- stylized props
- block characters
- converting high-detail assets into simpler art styles
- simplifying AI-generated 3D assets
- rapid visual experimentation

## Project Philosophy

Blockify is not intended to be a general-purpose retopology tool.

It does not try to preserve every detail of the source mesh.

Instead, it deliberately rebuilds a model using a constrained visual language:

> **Simple geometry. Clear silhouettes. Clean blocks.**

The goal is not to reproduce the original topology.

The goal is to reproduce the recognizable shape and color of the source using blocks.

## Project Status

Blockify is currently in early development.

The first milestone focuses on:

- mesh sampling
- voxel representation
- cuboid generation
- cuboid merging
- source color sampling
- palette reduction
- Blender-native Generate / Regenerate workflow

## Requirements

- Blender 4.x

## Installation

Installation instructions will be provided with the first release.

Blockify will be distributed as a standard Blender extension/add-on.

## License

TBD
