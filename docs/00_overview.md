# Blockify — Project Overview

## Purpose

Blockify is a native Blender add-on that converts an existing mesh into a clean block-style model made from axis-aligned cubes and cuboids.

The project is inspired by Rigify's workflow philosophy:

```text
Source Mesh + Blockify Settings
              ↓
           Generate
              ↓
     Generated Block Model
```

The source mesh is authoritative and must remain untouched. The generated model is disposable and can be regenerated at any time.

Blockify is **not** a command-line asset converter and is **not** an image-to-3D system. The primary product is an interactive Blender add-on.

## Primary Use Case

A user imports or creates a mesh, selects it, chooses Blockify settings, and generates a stylized block model.

Typical source assets include:

- imported GLB/GLTF models
- AI-generated 3D models
- sculpted objects
- ordinary Blender meshes
- props, food, furniture, buildings, and characters

## Core Product Principles

### 1. Non-destructive generation

Never destructively modify the source object.

Generated geometry must be stored separately and must be safe to delete and rebuild.

### 2. Recognizable shape over topology preservation

Blockify does not preserve the source topology.

The generated model should preserve:

1. silhouette
2. major volumes
3. important color regions

Fine surface topology is intentionally discarded.

### 3. Cuboids, not thousands of cubes

Voxelization is an intermediate representation, not the final artistic goal.

The preferred result is a small number of meaningful cuboids.

```text
Bad final representation:

■■■■■■
■■■■■■
■■■■■■

18 independent cubes


Preferred representation:

┌────────────┐
│  6 × 3 × 1 │
└────────────┘

1 cuboid
```

### 4. Flat, controlled color

Generated blocks should normally have flat colors.

Complex source shaders should not be copied blindly.

The first implementation should preserve recognizable source colors through sampling and palette reduction.

### 5. Blender-native UX

The user should work entirely inside Blender:

1. Select source object.
2. Open Blockify panel.
3. Configure settings.
4. Click **Blockify**.
5. Inspect result.
6. Change settings.
7. Click **Regenerate**.

The add-on should behave like a Blender tool, not like an external pipeline wrapped in Blender.

## Initial Scope

The first stable release should support:

- one selected mesh object as source
- configurable block size
- voxel occupancy generation
- interior filling
- source color sampling
- palette quantization
- cuboid decomposition / merging
- hidden-face removal
- generated object creation
- Generate / Regenerate workflow
- useful generation statistics

## Explicit Non-Goals for the Initial Release

Do not implement these as part of the core MVP:

- automatic character rigging
- animation generation
- AI image-to-3D
- external AI APIs
- automatic semantic body-part detection
- arbitrary polygon retopology
- Minecraft file-format export
- headless CLI workflow
- procedural texture generation

They may be added later as separate systems.

## Success Criteria

A successful Blockify result should:

- be immediately recognizable as the source asset
- visibly use a block/cuboid aesthetic
- contain dramatically simpler geometry than the source
- use a small controlled color palette
- remain easy to edit in Blender
- regenerate predictably from the same source and settings

## Terminology

**Source Mesh**  
The original Blender mesh selected by the user.

**Voxel Grid**  
A discrete 3D occupancy grid used internally during generation.

**Voxel**  
One occupied grid cell. A voxel is not necessarily emitted as an individual cube.

**Block / Cuboid**  
An axis-aligned rectangular prism produced by merging one or more compatible voxels.

**Palette**  
The finite set of colors used by generated blocks.

**Generated Model**  
The result created by Blockify. It is derived data and may be regenerated.

## Rule for Contributors and AI Agents

When implementation choices conflict, optimize in this order:

1. deterministic generation
2. clean cuboid output
3. recognizable silhouette
4. recognizable color regions
5. performance
6. preservation of small detail

Do not sacrifice clean block structure merely to preserve noisy source detail.
