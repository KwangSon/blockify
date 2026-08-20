"""
rig.py
Standalone Blender 5.2 + Rigify character/animation test.

One Run Script does all of this:

    Character
    ├── GEO
    │   ├── Body
    │   ├── Head
    │   ├── UpperArm.L
    │   ├── LowerArm.L
    │   ├── UpperArm.R
    │   ├── LowerArm.R
    │   ├── UpperLeg.L
    │   ├── LowerLeg.L
    │   ├── UpperLeg.R
    │   └── LowerLeg.R
    └── RIG
        ├── META_Character
        └── RIG_Character

    Action:
        CHR_SitDown   frames 1..24 @ 30 FPS

The meshes are rigidly weighted to Rigify DEF bones.
The animation is keyed only on generated Rigify FK controls.

WARNING:
    This is a standalone test script. It clears objects, collections, and actions
    in the current scene/file before building the test character.
"""

import math

import bpy
from mathutils import Euler, Matrix, Quaternion, Vector


# =============================================================================
# Naming / timing
# =============================================================================

COLLECTION_CHARACTER = "Character"
COLLECTION_GEO = "GEO"
COLLECTION_RIG = "RIG"

METARIG_NAME = "META_Character"
CONTROL_RIG_NAME = "RIG_Character"
WIDGET_COLLECTION_NAME = "WGT_Character"

ACTION_SIT_DOWN = "CHR_SitDown"

FPS = 30
SIT_START = 1
SIT_END = 24


# =============================================================================
# Rigify names
# =============================================================================

FK_SWITCH_BONES = (
    "upper_arm_parent.L",
    "upper_arm_parent.R",
    "thigh_parent.L",
    "thigh_parent.R",
)

CONTROL_BONES = {
    "hips": "hips",
    "upper_arm.L": "upper_arm_fk.L",
    "forearm.L": "forearm_fk.L",
    "upper_arm.R": "upper_arm_fk.R",
    "forearm.R": "forearm_fk.R",
    "thigh.L": "thigh_fk.L",
    "shin.L": "shin_fk.L",
    "foot.L": "foot_fk.L",
    "thigh.R": "thigh_fk.R",
    "shin.R": "shin_fk.R",
    "foot.R": "foot_fk.R",
}

# One mesh object -> one deform bone, 100% weight.
DEFORM_BINDINGS = {
    "Body": "DEF-spine",
    "Head": "DEF-spine.006",
    "UpperArm.L": "DEF-upper_arm.L",
    "LowerArm.L": "DEF-forearm.L",
    "UpperArm.R": "DEF-upper_arm.R",
    "LowerArm.R": "DEF-forearm.R",
    "UpperLeg.L": "DEF-thigh.L",
    "LowerLeg.L": "DEF-shin.L",
    "UpperLeg.R": "DEF-thigh.R",
    "LowerLeg.R": "DEF-shin.R",
}


# =============================================================================
# Scene / collection helpers
# =============================================================================

def ensure_object_mode():
    obj = bpy.context.object
    if obj is not None and obj.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")


def clear_test_scene():
    """Clear this .blend for a deterministic standalone test."""
    ensure_object_mode()

    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    # Remove orphaned collections created by previous runs.
    for collection in list(bpy.data.collections):
        bpy.data.collections.remove(collection)

    # Remove previous/other actions in this standalone test file.
    for action in list(bpy.data.actions):
        bpy.data.actions.remove(action, do_unlink=True)


def create_collection(name, parent):
    collection = bpy.data.collections.new(name)
    parent.children.link(collection)
    return collection


def create_character_collections():
    character = create_collection(COLLECTION_CHARACTER, bpy.context.scene.collection)
    geo = create_collection(COLLECTION_GEO, character)
    rig = create_collection(COLLECTION_RIG, character)
    return character, geo, rig


def move_object_to_collection(obj, destination):
    for collection in list(obj.users_collection):
        collection.objects.unlink(obj)

    if destination.objects.get(obj.name) is None:
        destination.objects.link(obj)


def move_collection_to_parent(collection, destination):
    """Move an existing collection under one destination collection."""
    for scene in bpy.data.scenes:
        if scene.collection.children.get(collection.name) is collection:
            scene.collection.children.unlink(collection)

    for parent in bpy.data.collections:
        if parent == collection or parent == destination:
            continue
        if parent.children.get(collection.name) is collection:
            parent.children.unlink(collection)

    if destination.children.get(collection.name) is None:
        destination.children.link(collection)


# =============================================================================
# Geometry
# =============================================================================

def create_cube(name, location, dimensions, destination):
    bpy.ops.mesh.primitive_cube_add(location=location)

    obj = bpy.context.active_object
    obj.name = name
    obj.data.name = f"{name}.Mesh"
    obj.dimensions = dimensions

    # Rigid-parts pipeline is easier to reason about with identity object scale.
    bpy.ops.object.transform_apply(
        location=False,
        rotation=False,
        scale=True,
    )

    move_object_to_collection(obj, destination)
    return obj


def create_character(geo_collection):
    """Create a 10-part block character in a T-pose."""
    parts = {}

    # Body / head
    parts["Body"] = create_cube(
        "Body",
        (0.0, 0.0, 3.0),
        (1.4, 0.7, 1.8),
        geo_collection,
    )
    parts["Head"] = create_cube(
        "Head",
        (0.0, 0.0, 4.5),
        (1.2, 0.9, 1.2),
        geo_collection,
    )

    # Character-left is world +X. Character faces -Y.
    parts["UpperArm.L"] = create_cube(
        "UpperArm.L",
        (1.25, 0.0, 3.45),
        (1.1, 0.55, 0.55),
        geo_collection,
    )
    parts["LowerArm.L"] = create_cube(
        "LowerArm.L",
        (2.30, 0.0, 3.45),
        (1.0, 0.50, 0.50),
        geo_collection,
    )

    parts["UpperArm.R"] = create_cube(
        "UpperArm.R",
        (-1.25, 0.0, 3.45),
        (1.1, 0.55, 0.55),
        geo_collection,
    )
    parts["LowerArm.R"] = create_cube(
        "LowerArm.R",
        (-2.30, 0.0, 3.45),
        (1.0, 0.50, 0.50),
        geo_collection,
    )

    parts["UpperLeg.L"] = create_cube(
        "UpperLeg.L",
        (0.38, 0.0, 1.50),
        (0.60, 0.65, 1.20),
        geo_collection,
    )
    parts["LowerLeg.L"] = create_cube(
        "LowerLeg.L",
        (0.38, 0.0, 0.45),
        (0.55, 0.60, 0.90),
        geo_collection,
    )

    parts["UpperLeg.R"] = create_cube(
        "UpperLeg.R",
        (-0.38, 0.0, 1.50),
        (0.60, 0.65, 1.20),
        geo_collection,
    )
    parts["LowerLeg.R"] = create_cube(
        "LowerLeg.R",
        (-0.38, 0.0, 0.45),
        (0.55, 0.60, 0.90),
        geo_collection,
    )

    return parts


# =============================================================================
# Rigify Meta-Rig
# =============================================================================

def ensure_rigify():
    required = (
        hasattr(bpy.ops.object, "armature_basic_human_metarig_add")
        and hasattr(bpy.ops.pose, "rigify_generate")
    )
    if required:
        return

    try:
        bpy.ops.preferences.addon_enable(module="rigify")
    except Exception:
        pass

    required = (
        hasattr(bpy.ops.object, "armature_basic_human_metarig_add")
        and hasattr(bpy.ops.pose, "rigify_generate")
    )
    if not required:
        raise RuntimeError(
            "Rigify is unavailable. Enable Rigify in Blender Preferences "
            "and run rig.py again."
        )


def set_active(obj):
    ensure_object_mode()
    bpy.ops.object.select_all(action="DESELECT")
    obj.hide_set(False)
    obj.hide_viewport = False
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def create_basic_human(rig_collection):
    ensure_rigify()

    bpy.ops.object.select_all(action="DESELECT")
    result = bpy.ops.object.armature_basic_human_metarig_add()

    if result != {"FINISHED"}:
        raise RuntimeError("Rigify could not create a Basic Human Meta-Rig.")

    metarig = bpy.context.active_object
    metarig.name = METARIG_NAME
    metarig.data.name = f"{METARIG_NAME}.Armature"
    metarig.show_in_front = True
    metarig.matrix_world = Matrix.Identity(4)

    move_object_to_collection(metarig, rig_collection)
    return metarig


def set_edit_bone(edit_bones, name, head, tail):
    bone = edit_bones.get(name)
    if bone is None:
        raise RuntimeError(f"Basic Human is missing required bone: {name}")

    head = Vector(head)
    tail = Vector(tail)

    if (tail - head).length <= 1.0e-5:
        tail = head + Vector((0.0, 0.0, 0.01))

    bone.head = head
    bone.tail = tail
    return bone


def fit_metarig_t_pose(metarig):
    """Fit Basic Human to the known 10-part T-pose character."""
    set_active(metarig)
    bpy.ops.object.mode_set(mode="EDIT")

    bones = metarig.data.edit_bones

    try:
        # -----------------------------------------------------
        # Torso / head
        # -----------------------------------------------------
        spine_points = (
            (0.0, 0.0, 2.10),
            (0.0, 0.0, 2.45),
            (0.0, 0.0, 2.80),
            (0.0, 0.0, 3.20),
            (0.0, 0.0, 3.65),
            (0.0, 0.0, 3.82),
            (0.0, 0.0, 3.90),
            (0.0, 0.0, 5.10),
        )

        for index in range(7):
            name = "spine" if index == 0 else f"spine.{index:03d}"
            set_edit_bone(
                bones,
                name,
                spine_points[index],
                spine_points[index + 1],
            )

        # -----------------------------------------------------
        # Arms: visually T-pose, tiny -Y elbow hint.
        # -----------------------------------------------------
        shoulder_z = 3.45
        elbow_y = -0.02

        set_edit_bone(
            bones,
            "shoulder.L",
            (0.0, 0.0, shoulder_z),
            (0.70, 0.0, shoulder_z),
        )
        set_edit_bone(
            bones,
            "upper_arm.L",
            (0.70, 0.0, shoulder_z),
            (1.80, elbow_y, shoulder_z),
        )
        set_edit_bone(
            bones,
            "forearm.L",
            (1.80, elbow_y, shoulder_z),
            (2.60, 0.0, shoulder_z),
        )
        set_edit_bone(
            bones,
            "hand.L",
            (2.60, 0.0, shoulder_z),
            (2.80, 0.0, shoulder_z),
        )

        set_edit_bone(
            bones,
            "shoulder.R",
            (0.0, 0.0, shoulder_z),
            (-0.70, 0.0, shoulder_z),
        )
        set_edit_bone(
            bones,
            "upper_arm.R",
            (-0.70, 0.0, shoulder_z),
            (-1.80, elbow_y, shoulder_z),
        )
        set_edit_bone(
            bones,
            "forearm.R",
            (-1.80, elbow_y, shoulder_z),
            (-2.60, 0.0, shoulder_z),
        )
        set_edit_bone(
            bones,
            "hand.R",
            (-2.60, 0.0, shoulder_z),
            (-2.80, 0.0, shoulder_z),
        )

        # -----------------------------------------------------
        # Legs: tiny -Y knee hint.
        # -----------------------------------------------------
        knee_y = -0.02

        set_edit_bone(
            bones,
            "pelvis.L",
            (0.0, 0.0, 2.10),
            (0.38, 0.0, 2.12),
        )
        set_edit_bone(
            bones,
            "thigh.L",
            (0.38, 0.0, 2.10),
            (0.38, knee_y, 0.90),
        )
        set_edit_bone(
            bones,
            "shin.L",
            (0.38, knee_y, 0.90),
            (0.38, 0.0, 0.15),
        )
        set_edit_bone(
            bones,
            "foot.L",
            (0.38, 0.0, 0.15),
            (0.38, -0.40, 0.08),
        )
        set_edit_bone(
            bones,
            "toe.L",
            (0.38, -0.40, 0.08),
            (0.38, -0.65, 0.08),
        )
        set_edit_bone(
            bones,
            "heel.02.L",
            (0.25, 0.10, 0.05),
            (0.50, 0.10, 0.05),
        )

        set_edit_bone(
            bones,
            "pelvis.R",
            (0.0, 0.0, 2.10),
            (-0.38, 0.0, 2.12),
        )
        set_edit_bone(
            bones,
            "thigh.R",
            (-0.38, 0.0, 2.10),
            (-0.38, knee_y, 0.90),
        )
        set_edit_bone(
            bones,
            "shin.R",
            (-0.38, knee_y, 0.90),
            (-0.38, 0.0, 0.15),
        )
        set_edit_bone(
            bones,
            "foot.R",
            (-0.38, 0.0, 0.15),
            (-0.38, -0.40, 0.08),
        )
        set_edit_bone(
            bones,
            "toe.R",
            (-0.38, -0.40, 0.08),
            (-0.38, -0.65, 0.08),
        )
        set_edit_bone(
            bones,
            "heel.02.R",
            (-0.25, 0.10, 0.05),
            (-0.50, 0.10, 0.05),
        )

        # Keep optional breast helper bones valid and close to torso.
        for suffix, x in (("L", 0.25), ("R", -0.25)):
            name = f"breast.{suffix}"
            if bones.get(name) is not None:
                set_edit_bone(
                    bones,
                    name,
                    (x, 0.0, 3.35),
                    (x, -0.15, 3.35),
                )

    finally:
        bpy.ops.object.mode_set(mode="OBJECT")

    metarig.data.update_tag()


# =============================================================================
# Rigify generated Control Rig
# =============================================================================

def generate_control_rig(metarig, rig_collection):
    """
    Generate Rigify output and return the generated armature object.
    """
    armature_data = metarig.data

    # Force a fresh output for this standalone script.
    if hasattr(armature_data, "rigify_target_rig"):
        armature_data.rigify_target_rig = None
    if hasattr(armature_data, "rigify_widgets_collection"):
        armature_data.rigify_widgets_collection = None
    if hasattr(armature_data, "rigify_rig_ui"):
        armature_data.rigify_rig_ui = None
    if hasattr(armature_data, "rigify_rig_basename"):
        armature_data.rigify_rig_basename = CONTROL_RIG_NAME

    before_objects = set(bpy.data.objects)

    set_active(metarig)

    result = bpy.ops.pose.rigify_generate()
    if result != {"FINISHED"}:
        raise RuntimeError("Rigify failed to generate the Control Rig.")

    new_objects = set(bpy.data.objects) - before_objects
    generated_armatures = [
        obj
        for obj in new_objects
        if obj.type == "ARMATURE" and obj != metarig
    ]

    if len(generated_armatures) != 1:
        names = ", ".join(obj.name for obj in generated_armatures) or "<none>"
        raise RuntimeError(
            "Could not uniquely identify generated Rigify Control Rig: "
            f"{names}"
        )

    control_rig = generated_armatures[0]
    control_rig.name = CONTROL_RIG_NAME
    control_rig.data.name = f"{CONTROL_RIG_NAME}.Armature"
    control_rig.show_in_front = True

    move_object_to_collection(control_rig, rig_collection)

    # Organize Rigify's widget collection under RIG.
    widgets = getattr(armature_data, "rigify_widgets_collection", None)
    if widgets is not None:
        widgets.name = WIDGET_COLLECTION_NAME
        move_collection_to_parent(widgets, rig_collection)

    rig_ui = getattr(armature_data, "rigify_rig_ui", None)
    if rig_ui is not None:
        rig_ui.name = f"{CONTROL_RIG_NAME}_ui.py"

    configure_fk_mode(control_rig)
    validate_generated_rig(control_rig)

    return control_rig


def configure_fk_mode(control_rig):
    """
    Rigify limbs can be IK or FK.
    Procedural animation in this file deliberately targets FK controls.
    """
    missing = []

    for name in FK_SWITCH_BONES:
        pose_bone = control_rig.pose.bones.get(name)
        if pose_bone is None:
            missing.append(name)
            continue

        if "IK_FK" not in pose_bone:
            raise RuntimeError(
                f"Rigify control {name} does not expose IK_FK."
            )

        pose_bone["IK_FK"] = 1.0

    if missing:
        raise RuntimeError(
            "Generated Rigify rig is missing FK switch controls: "
            + ", ".join(missing)
        )

    control_rig.update_tag()
    bpy.context.view_layer.update()


def validate_generated_rig(control_rig):
    required = set(CONTROL_BONES.values()) | set(DEFORM_BINDINGS.values())
    missing = [
        name
        for name in sorted(required)
        if control_rig.pose.bones.get(name) is None
    ]

    if missing:
        raise RuntimeError(
            "Generated Rigify rig is missing required bones: "
            + ", ".join(missing)
        )


# =============================================================================
# Rigid skinning
# =============================================================================

def bind_part_rigid(mesh_obj, control_rig, deform_bone_name):
    """
    Give every vertex in one cube 100% weight to one Rigify DEF bone.
    """
    if mesh_obj.type != "MESH":
        raise TypeError(f"{mesh_obj.name} is not a mesh.")

    if control_rig.data.bones.get(deform_bone_name) is None:
        raise RuntimeError(
            f"{control_rig.name} is missing deform bone {deform_bone_name}"
        )

    # Clear previous groups/modifiers in this standalone build.
    mesh_obj.vertex_groups.clear()

    for modifier in list(mesh_obj.modifiers):
        if modifier.type == "ARMATURE":
            mesh_obj.modifiers.remove(modifier)

    group = mesh_obj.vertex_groups.new(name=deform_bone_name)
    group.add(
        [vertex.index for vertex in mesh_obj.data.vertices],
        1.0,
        "REPLACE",
    )

    modifier = mesh_obj.modifiers.new(
        name="Armature",
        type="ARMATURE",
    )
    modifier.object = control_rig
    modifier.use_vertex_groups = True

    # Keep object transforms independent; deformation comes from the modifier.
    mesh_obj.parent = None


def bind_character(parts, control_rig):
    for object_name, deform_bone_name in DEFORM_BINDINGS.items():
        bind_part_rigid(
            parts[object_name],
            control_rig,
            deform_bone_name,
        )


# =============================================================================
# Animation API
# =============================================================================

def reset_control_pose(control_rig):
    """Reset generated controls to their Rigify rest/control pose."""
    for pose_bone in control_rig.pose.bones:
        pose_bone.location = (0.0, 0.0, 0.0)
        pose_bone.scale = (1.0, 1.0, 1.0)

        pose_bone.rotation_mode = "QUATERNION"
        pose_bone.rotation_quaternion = Quaternion((1.0, 0.0, 0.0, 0.0))

    configure_fk_mode(control_rig)
    control_rig.update_tag()


def create_action(control_rig, name, frame_start, frame_end):
    """
    Create one Blender 5.x Action with one Object Action Slot.

    Convention:
        one Action == one game animation clip
    """
    old = bpy.data.actions.get(name)
    if old is not None:
        bpy.data.actions.remove(old, do_unlink=True)

    action = bpy.data.actions.new(name)
    action.use_fake_user = True
    action.use_frame_range = True
    action.frame_start = frame_start
    action.frame_end = frame_end
    action.use_cyclic = False

    # Simple metadata useful to tools/exporters.
    action["clip_name"] = name
    action["fps"] = FPS
    action["loop"] = False

    slot = action.slots.new("OBJECT", control_rig.name)

    animation_data = control_rig.animation_data_create()
    animation_data.action = action
    animation_data.action_slot = slot

    return action


def set_scene_for_action(scene, action):
    scene.render.fps = FPS
    scene.render.fps_base = 1.0
    scene.frame_start = round(action.frame_start)
    scene.frame_end = round(action.frame_end)


def armature_axis_quaternion(pose_bone, axis, angle_degrees):
    """
    Return a local PoseBone quaternion that approximately represents a
    rotation around an armature-space axis while the parent controls are neutral.

    This keeps animation definitions readable in character-space terms:
        X = forward/back bend axis
        Y = arm lowering axis
        Z = twist axis
    """
    axis = Vector(axis).normalized()
    global_rotation = Quaternion(axis, math.radians(angle_degrees))

    rest_rotation = pose_bone.bone.matrix_local.to_quaternion()
    return (
        rest_rotation.inverted()
        @ global_rotation
        @ rest_rotation
    ).normalized()


def armature_delta_to_local_location(pose_bone, delta):
    """
    Convert a desired armature-space translation delta to the pose bone's
    local location coordinates. For Rigify's hips control this makes
    'move down in Z' explicit and readable.
    """
    delta = Vector(delta)
    rest_rotation = pose_bone.bone.matrix_local.to_quaternion()
    return rest_rotation.inverted() @ delta


def set_control_rotation_armature_axis(control_rig, bone_name, axis, degrees):
    pose_bone = control_rig.pose.bones.get(bone_name)
    if pose_bone is None:
        raise RuntimeError(f"Missing animation control: {bone_name}")

    pose_bone.rotation_mode = "QUATERNION"
    pose_bone.rotation_quaternion = armature_axis_quaternion(
        pose_bone,
        axis,
        degrees,
    )
    return pose_bone


def set_control_location_armature(control_rig, bone_name, delta):
    pose_bone = control_rig.pose.bones.get(bone_name)
    if pose_bone is None:
        raise RuntimeError(f"Missing animation control: {bone_name}")

    pose_bone.location = armature_delta_to_local_location(
        pose_bone,
        delta,
    )
    return pose_bone


def key_bone_transform(pose_bone, frame):
    pose_bone.keyframe_insert(
        data_path="location",
        frame=frame,
        group=pose_bone.name,
    )
    pose_bone.keyframe_insert(
        data_path="rotation_quaternion",
        frame=frame,
        group=pose_bone.name,
    )


def key_neutral_controls(control_rig, frame, bone_names):
    for name in bone_names:
        pose_bone = control_rig.pose.bones.get(name)
        if pose_bone is None:
            raise RuntimeError(f"Missing animation control: {name}")

        pose_bone.location = (0.0, 0.0, 0.0)
        pose_bone.rotation_mode = "QUATERNION"
        pose_bone.rotation_quaternion = Quaternion((1.0, 0.0, 0.0, 0.0))
        key_bone_transform(pose_bone, frame)


def key_sit_pose(
    control_rig,
    frame,
    *,
    hips_down,
    thigh_forward,
    knee_bend,
    arm_down,
):
    """
    Key one semantic SitDown pose.

    Character faces -Y:
      - thighs rotate toward -Y around armature X
      - knees counter-rotate so shins fold down
      - left/right arms rotate down from T-pose around armature Y
      - hips translate downward in armature Z
    """
    # Hips
    hips = set_control_location_armature(
        control_rig,
        CONTROL_BONES["hips"],
        (0.0, 0.0, -hips_down),
    )
    hips.rotation_mode = "QUATERNION"
    hips.rotation_quaternion = Quaternion((1.0, 0.0, 0.0, 0.0))
    key_bone_transform(hips, frame)

    # Legs
    for suffix in ("L", "R"):
        thigh = set_control_rotation_armature_axis(
            control_rig,
            CONTROL_BONES[f"thigh.{suffix}"],
            (1.0, 0.0, 0.0),
            -thigh_forward,
        )
        shin = set_control_rotation_armature_axis(
            control_rig,
            CONTROL_BONES[f"shin.{suffix}"],
            (1.0, 0.0, 0.0),
            knee_bend,
        )

        key_bone_transform(thigh, frame)
        key_bone_transform(shin, frame)

    # Lower both arms from the original T-pose.
    left_arm = set_control_rotation_armature_axis(
        control_rig,
        CONTROL_BONES["upper_arm.L"],
        (0.0, 1.0, 0.0),
        arm_down,
    )
    right_arm = set_control_rotation_armature_axis(
        control_rig,
        CONTROL_BONES["upper_arm.R"],
        (0.0, 1.0, 0.0),
        -arm_down,
    )

    key_bone_transform(left_arm, frame)
    key_bone_transform(right_arm, frame)


def polish_action_curves(action):
    """
    Use clamped Bezier handles: smooth animation without wild overshoot.
    Works with Blender 5.x layered Actions.
    """
    for layer in action.layers:
        for strip in layer.strips:
            for channelbag in strip.channelbags:
                for fcurve in channelbag.fcurves:
                    for point in fcurve.keyframe_points:
                        point.interpolation = "BEZIER"
                        point.handle_left_type = "AUTO_CLAMPED"
                        point.handle_right_type = "AUTO_CLAMPED"


# =============================================================================
# Clip definitions
# =============================================================================

def create_sit_down_animation(scene, control_rig):
    """
    Create the first game clip.

    CHR_SitDown:
        1   standing / T-pose rest
        8   anticipation
        16  lowering
        24  seated
    """
    action = create_action(
        control_rig,
        ACTION_SIT_DOWN,
        SIT_START,
        SIT_END,
    )
    set_scene_for_action(scene, action)

    reset_control_pose(control_rig)

    animated_controls = (
        CONTROL_BONES["hips"],
        CONTROL_BONES["upper_arm.L"],
        CONTROL_BONES["upper_arm.R"],
        CONTROL_BONES["thigh.L"],
        CONTROL_BONES["shin.L"],
        CONTROL_BONES["thigh.R"],
        CONTROL_BONES["shin.R"],
    )

    # Start exactly at generated Rigify control rest pose.
    scene.frame_set(1)
    key_neutral_controls(control_rig, 1, animated_controls)

    # Early anticipation.
    scene.frame_set(8)
    key_sit_pose(
        control_rig,
        8,
        hips_down=0.18,
        thigh_forward=18.0,
        knee_bend=20.0,
        arm_down=22.0,
    )

    # Main descent.
    scene.frame_set(16)
    key_sit_pose(
        control_rig,
        16,
        hips_down=0.55,
        thigh_forward=52.0,
        knee_bend=60.0,
        arm_down=58.0,
    )

    # Final seated pose.
    scene.frame_set(24)
    key_sit_pose(
        control_rig,
        24,
        hips_down=0.85,
        thigh_forward=82.0,
        knee_bend=88.0,
        arm_down=82.0,
    )

    polish_action_curves(action)

    # Make sure the Action remains active.
    animation_data = control_rig.animation_data_create()
    animation_data.action = action
    if len(action.slots) == 1:
        animation_data.action_slot = action.slots[0]

    scene.frame_set(SIT_START)
    control_rig.update_tag()
    bpy.context.view_layer.update()

    return action


# =============================================================================
# Main
# =============================================================================

def main():
    scene = bpy.context.scene

    clear_test_scene()

    _character_collection, geo_collection, rig_collection = (
        create_character_collections()
    )

    parts = create_character(geo_collection)

    metarig = create_basic_human(rig_collection)
    fit_metarig_t_pose(metarig)

    control_rig = generate_control_rig(
        metarig,
        rig_collection,
    )

    bind_character(
        parts,
        control_rig,
    )

    action = create_sit_down_animation(
        scene,
        control_rig,
    )

    # Finish ready for inspection/playback.
    set_active(control_rig)
    bpy.ops.object.mode_set(mode="POSE")
    scene.frame_set(SIT_START)

    print("=" * 70)
    print("rig.py complete")
    print(f"Character collection : {COLLECTION_CHARACTER}")
    print(f"Meta-Rig             : {METARIG_NAME}")
    print(f"Control Rig          : {CONTROL_RIG_NAME}")
    print(f"Action               : {action.name}")
    print(f"Frames               : {SIT_START}..{SIT_END} @ {FPS} FPS")
    print("Press Space in the 3D View to play CHR_SitDown.")
    print("=" * 70)


if __name__ == "__main__":
    main()
