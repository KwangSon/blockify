"""
cube.py
Run this AFTER rig.py.

Purpose
-------
Convert the 10 rigid block-character source meshes in:

    Character / GEO

into voxelized meshes on a 0.1 m lattice:

    Character
    ├── GEO           # original source meshes, kept but hidden
    ├── GEO_VOXEL     # voxelized meshes created by this script
    └── RIG           # existing Rigify Meta/Control Rig

The voxelized meshes keep the same rigid DEF-bone binding as the source
objects, so the existing CHR_SitDown Action continues to animate them.

Important design choice
-----------------------
This script does NOT create thousands of Blender Objects.

Each body part stays ONE Blender Mesh Object, but that mesh contains many
disconnected cube islands. This is much lighter for Blender while still
giving us true cube geometry that can later be separated by loose parts
if needed.

Default lattice:
    cell spacing = 0.1 m
    visible gap  = 0.0 m
    cube size    = 0.1 m

Set VOXEL_GAP = 0.002 if you later want a tiny visible gap between blocks.
"""

import math

import bpy
from mathutils import Vector


# =============================================================================
# Configuration
# =============================================================================

CHARACTER_COLLECTION = "Character"
SOURCE_COLLECTION = "GEO"
VOXEL_COLLECTION = "GEO_VOXEL"

CONTROL_RIG_NAME = "RIG_Character"

VOXEL_SIZE = 0.1
VOXEL_GAP = 0.0

# If a source dimension is not an exact multiple of 0.1 m, snap the number
# of cells to the nearest integer while keeping the part centered.
#
# Example:
#     0.55 m -> 6 cells -> 0.60 m lattice envelope
#     0.65 m -> 7 cells -> 0.70 m lattice envelope
#
# This keeps every voxel on the same 0.1 m design unit.
SNAP_TO_NEAREST_CELL = True


# =============================================================================
# Blender helpers
# =============================================================================

def ensure_object_mode():
    obj = bpy.context.object
    if obj is not None and obj.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")


def get_character_collections():
    character = bpy.data.collections.get(CHARACTER_COLLECTION)
    if character is None:
        raise RuntimeError(
            f'Collection "{CHARACTER_COLLECTION}" was not found. '
            "Run rig.py first."
        )

    source = character.children.get(SOURCE_COLLECTION)
    if source is None:
        raise RuntimeError(
            f'Collection "{CHARACTER_COLLECTION}/{SOURCE_COLLECTION}" '
            "was not found. Run rig.py first."
        )

    return character, source


def remove_collection_recursive(collection):
    """Remove an old generated voxel collection and all objects inside it."""
    for child in list(collection.children):
        remove_collection_recursive(child)

    for obj in list(collection.objects):
        bpy.data.objects.remove(obj, do_unlink=True)

    bpy.data.collections.remove(collection)


def recreate_voxel_collection(character):
    old = character.children.get(VOXEL_COLLECTION)
    if old is not None:
        remove_collection_recursive(old)

    collection = bpy.data.collections.new(VOXEL_COLLECTION)
    character.children.link(collection)
    return collection


def direct_mesh_objects(collection):
    return sorted(
        [obj for obj in collection.objects if obj.type == "MESH"],
        key=lambda obj: obj.name,
    )


# =============================================================================
# Source-rig binding discovery
# =============================================================================

def find_armature_modifier(source_obj):
    modifiers = [
        modifier
        for modifier in source_obj.modifiers
        if modifier.type == "ARMATURE" and modifier.object is not None
    ]

    if len(modifiers) != 1:
        raise RuntimeError(
            f"{source_obj.name}: expected exactly one Armature modifier, "
            f"found {len(modifiers)}."
        )

    return modifiers[0]


def find_rigid_deform_group(source_obj, rig):
    """
    rig.py gives each source part one 100% DEF vertex group.

    We discover that group instead of hardcoding part -> bone mappings,
    making cube.py independent from the exact character part names.
    """
    deform_group_names = [
        group.name
        for group in source_obj.vertex_groups
        if group.name.startswith("DEF-")
        and rig.data.bones.get(group.name) is not None
    ]

    if len(deform_group_names) != 1:
        raise RuntimeError(
            f"{source_obj.name}: expected exactly one DEF vertex group, "
            f"found {deform_group_names}."
        )

    return deform_group_names[0]


# =============================================================================
# Voxel grid math
# =============================================================================

def local_bounds(source_obj):
    if not source_obj.data.vertices:
        raise RuntimeError(f"{source_obj.name}: mesh has no vertices.")

    coordinates = [vertex.co.copy() for vertex in source_obj.data.vertices]

    minimum = Vector((
        min(co.x for co in coordinates),
        min(co.y for co in coordinates),
        min(co.z for co in coordinates),
    ))
    maximum = Vector((
        max(co.x for co in coordinates),
        max(co.y for co in coordinates),
        max(co.z for co in coordinates),
    ))

    return minimum, maximum


def round_half_up(value):
    return int(math.floor(value + 0.5))


def cell_count(length):
    if length <= 0.0:
        return 1

    exact = length / VOXEL_SIZE

    if SNAP_TO_NEAREST_CELL:
        return max(1, round_half_up(exact))

    return max(1, int(math.floor(exact + 1.0e-6)))


def axis_centers(center, count):
    """
    Build centers symmetrically around the original part center.

    For six 0.1 m cells:
        -0.25, -0.15, -0.05, +0.05, +0.15, +0.25
    relative to the part center.
    """
    offset = (count - 1) * 0.5

    return [
        center + (index - offset) * VOXEL_SIZE
        for index in range(count)
    ]


def voxel_centers_for_object(source_obj):
    minimum, maximum = local_bounds(source_obj)

    size = maximum - minimum
    center = (minimum + maximum) * 0.5

    counts = (
        cell_count(size.x),
        cell_count(size.y),
        cell_count(size.z),
    )

    xs = axis_centers(center.x, counts[0])
    ys = axis_centers(center.y, counts[1])
    zs = axis_centers(center.z, counts[2])

    centers = [
        Vector((x, y, z))
        for z in zs
        for y in ys
        for x in xs
    ]

    return centers, counts, size


# =============================================================================
# Mesh generation
# =============================================================================

_CUBE_FACE_TEMPLATE = (
    (0, 3, 2, 1),  # bottom
    (4, 5, 6, 7),  # top
    (0, 1, 5, 4),  # -Y
    (1, 2, 6, 5),  # +X
    (2, 3, 7, 6),  # +Y
    (3, 0, 4, 7),  # -X
)


def append_cube_geometry(vertices, faces, center, cube_size):
    half = cube_size * 0.5
    x, y, z = center

    base = len(vertices)

    vertices.extend((
        (x - half, y - half, z - half),
        (x + half, y - half, z - half),
        (x + half, y + half, z - half),
        (x - half, y + half, z - half),
        (x - half, y - half, z + half),
        (x + half, y - half, z + half),
        (x + half, y + half, z + half),
        (x - half, y + half, z + half),
    ))

    for face in _CUBE_FACE_TEMPLATE:
        faces.append(tuple(base + index for index in face))


def voxel_object_name(source_name):
    """
    Keep Blender's side suffix at the END of the name.

    UpperArm.L -> UpperArm.Voxels.L
    UpperArm.R -> UpperArm.Voxels.R
    Body       -> Body.Voxels
    """
    if source_name.endswith(".L"):
        return f"{source_name[:-2]}.Voxels.L"

    if source_name.endswith(".R"):
        return f"{source_name[:-2]}.Voxels.R"

    return f"{source_name}.Voxels"


def create_voxel_mesh(source_obj, destination, rig, deform_group_name):
    centers, counts, original_size = voxel_centers_for_object(source_obj)

    cube_size = VOXEL_SIZE - VOXEL_GAP
    if cube_size <= 0.0:
        raise RuntimeError(
            "VOXEL_GAP must be smaller than VOXEL_SIZE."
        )

    vertices = []
    faces = []

    for center in centers:
        append_cube_geometry(
            vertices,
            faces,
            center,
            cube_size,
        )

    object_name = voxel_object_name(source_obj.name)
    mesh_name = f"{object_name}.Mesh"

    mesh = bpy.data.meshes.new(mesh_name)
    mesh.from_pydata(vertices, [], faces)
    mesh.validate()
    mesh.update()

    # Voxel art should stay flat shaded.
    for polygon in mesh.polygons:
        polygon.use_smooth = False

    voxel_obj = bpy.data.objects.new(object_name, mesh)
    destination.objects.link(voxel_obj)

    # The generated mesh uses the source object's local coordinate system.
    voxel_obj.matrix_world = source_obj.matrix_world.copy()

    # Preserve object display/material settings where useful.
    voxel_obj.color = source_obj.color
    voxel_obj.display_type = source_obj.display_type

    for material in source_obj.data.materials:
        voxel_obj.data.materials.append(material)

    # Rigid skinning: every voxel vertex belongs 100% to the same DEF bone.
    group = voxel_obj.vertex_groups.new(name=deform_group_name)
    group.add(
        list(range(len(mesh.vertices))),
        1.0,
        "REPLACE",
    )

    modifier = voxel_obj.modifiers.new(
        name="Armature",
        type="ARMATURE",
    )
    modifier.object = rig
    modifier.use_vertex_groups = True
    modifier.use_bone_envelopes = False

    voxel_obj["voxel_size"] = VOXEL_SIZE
    voxel_obj["voxel_gap"] = VOXEL_GAP
    voxel_obj["voxel_count_x"] = counts[0]
    voxel_obj["voxel_count_y"] = counts[1]
    voxel_obj["voxel_count_z"] = counts[2]
    voxel_obj["voxel_count_total"] = len(centers)
    voxel_obj["source_object"] = source_obj.name
    voxel_obj["deform_bone"] = deform_group_name

    return voxel_obj, counts, original_size, len(centers)


# =============================================================================
# Main conversion
# =============================================================================

def voxelize_character():
    ensure_object_mode()

    scene = bpy.context.scene
    character, source_collection = get_character_collections()

    rig = bpy.data.objects.get(CONTROL_RIG_NAME)
    if rig is None or rig.type != "ARMATURE":
        raise RuntimeError(
            f'Armature "{CONTROL_RIG_NAME}" was not found. Run rig.py first.'
        )

    voxel_collection = recreate_voxel_collection(character)

    source_objects = direct_mesh_objects(source_collection)
    if not source_objects:
        raise RuntimeError(
            f'No mesh objects found in "{SOURCE_COLLECTION}".'
        )

    total_voxels = 0

    print("=" * 78)
    print("cube.py: voxelizing Character/GEO")
    print(f"Voxel lattice : {VOXEL_SIZE:.3f} m")
    print(f"Visible gap   : {VOXEL_GAP:.3f} m")
    print("-" * 78)

    for source_obj in source_objects:
        armature_modifier = find_armature_modifier(source_obj)

        if armature_modifier.object != rig:
            raise RuntimeError(
                f"{source_obj.name}: Armature modifier points to "
                f"{armature_modifier.object.name}, expected {rig.name}."
            )

        deform_group = find_rigid_deform_group(source_obj, rig)

        voxel_obj, counts, original_size, voxel_count = create_voxel_mesh(
            source_obj,
            voxel_collection,
            rig,
            deform_group,
        )

        total_voxels += voxel_count

        # Keep source geometry for rebuilding, but do not render/display it.
        source_obj.hide_set(True)
        source_obj.hide_render = True

        print(
            f"{source_obj.name:16s} -> {voxel_obj.name:24s} "
            f"{counts[0]} x {counts[1]} x {counts[2]} "
            f"= {voxel_count:5d} cubes "
            f"(source {original_size.x:.2f}, "
            f"{original_size.y:.2f}, {original_size.z:.2f} m)"
        )

    # Leave the character at the standing/T-pose start of CHR_SitDown.
    scene.frame_set(1)

    bpy.ops.object.select_all(action="DESELECT")
    rig.hide_set(False)
    rig.hide_viewport = False
    rig.select_set(True)
    bpy.context.view_layer.objects.active = rig

    try:
        bpy.ops.object.mode_set(mode="POSE")
    except RuntimeError:
        pass

    bpy.context.view_layer.update()

    print("-" * 78)
    print(f"Created {total_voxels} voxel cubes in {VOXEL_COLLECTION}.")
    print("Original GEO meshes are hidden, not deleted.")
    print("Press Space to play the existing CHR_SitDown animation.")
    print("=" * 78)


if __name__ == "__main__":
    voxelize_character()
