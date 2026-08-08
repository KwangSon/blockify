bl_info = {
    "name": "Blockify",
    "author": "Blockify Contributors",
    "version": (0, 0, 3),
    "blender": (5, 0, 0),
    "location": "Properties > Modifiers > Add Modifier > Blockify",
    "description": "Convert a mesh into blocks with Geometry Nodes",
    "category": "Object",
}

import bpy
from bpy.app.handlers import persistent
from bpy.types import Operator


NODE_GROUP_NAME = "Blockify"
NODE_GROUP_OWNER_KEY = "blockify.node_group"
NODE_GROUP_SCHEMA_KEY = "blockify.schema_version"
NODE_GROUP_SCHEMA_VERSION = 2

GEOMETRY_SOCKET_NAME = "Geometry"
BLOCK_SIZE_SOCKET_NAME = "Block Size"
MAX_BLOCKS_PER_AXIS = 64.0
VOLUME_THRESHOLD = 0.1

LEGACY_SETTING_NAME = "blockify_test_block_size"
MENU_CALLBACK_KEY = "blockify.modifier_menu_callback"
REGISTERED_CLASSES_KEY = "blockify.registered_classes"
MIGRATION_TIMER_KEY = "blockify.migration_timer"
LOAD_POST_CALLBACK_KEY = "blockify.load_post_callback"


def _find_interface_socket(node_group, name, in_out):
    for item in node_group.interface.items_tree:
        if (
            item.item_type == "SOCKET"
            and item.name == name
            and item.in_out == in_out
        ):
            return item
    return None


def _ensure_blockify_interface(node_group):
    geometry_input = _find_interface_socket(
        node_group,
        GEOMETRY_SOCKET_NAME,
        "INPUT",
    )
    if geometry_input is None:
        geometry_input = node_group.interface.new_socket(
            name=GEOMETRY_SOCKET_NAME,
            in_out="INPUT",
            socket_type="NodeSocketGeometry",
        )

    block_size_socket = _find_interface_socket(
        node_group,
        BLOCK_SIZE_SOCKET_NAME,
        "INPUT",
    )
    if block_size_socket is None:
        block_size_socket = node_group.interface.new_socket(
            name=BLOCK_SIZE_SOCKET_NAME,
            in_out="INPUT",
            socket_type="NodeSocketFloat",
        )

    block_size_socket.description = "Size of each block in Blender units"
    block_size_socket.default_value = 0.1
    block_size_socket.min_value = 0.001
    block_size_socket.max_value = 1000.0
    block_size_socket.subtype = "DISTANCE"
    block_size_socket.force_non_field = True

    geometry_output = _find_interface_socket(
        node_group,
        GEOMETRY_SOCKET_NAME,
        "OUTPUT",
    )
    if geometry_output is None:
        geometry_output = node_group.interface.new_socket(
            name=GEOMETRY_SOCKET_NAME,
            in_out="OUTPUT",
            socket_type="NodeSocketGeometry",
        )

    return geometry_input, block_size_socket, geometry_output


def _new_node(node_group, node_type, name, location):
    node = node_group.nodes.new(node_type)
    node.name = name
    node.label = name
    node.location = location
    return node


def _set_menu_socket_value(socket, *candidates):
    last_error = None
    for candidate in candidates:
        try:
            socket.default_value = candidate
            return
        except TypeError as error:
            last_error = error
    raise last_error


def _build_blockify_node_tree(node_group):
    for node in list(node_group.nodes):
        node_group.nodes.remove(node)

    links = node_group.links

    group_input = _new_node(
        node_group,
        "NodeGroupInput",
        "Blockify Input",
        (-1400.0, 200.0),
    )
    bounding_box = _new_node(
        node_group,
        "GeometryNodeBoundBox",
        "Source Bounds",
        (-1400.0, -100.0),
    )
    dimensions = _new_node(
        node_group,
        "ShaderNodeVectorMath",
        "Bounds Dimensions",
        (-1180.0, -120.0),
    )
    dimensions.operation = "SUBTRACT"

    separate_dimensions = _new_node(
        node_group,
        "ShaderNodeSeparateXYZ",
        "Separate Dimensions",
        (-980.0, -120.0),
    )
    longest_xy = _new_node(
        node_group,
        "ShaderNodeMath",
        "Longest XY",
        (-780.0, -80.0),
    )
    longest_xy.operation = "MAXIMUM"
    longest_axis = _new_node(
        node_group,
        "ShaderNodeMath",
        "Longest Axis",
        (-580.0, -80.0),
    )
    longest_axis.operation = "MAXIMUM"

    minimum_safe_size = _new_node(
        node_group,
        "ShaderNodeMath",
        "Minimum Safe Block Size",
        (-380.0, -80.0),
    )
    minimum_safe_size.operation = "DIVIDE"
    minimum_safe_size.inputs[1].default_value = MAX_BLOCKS_PER_AXIS

    effective_size = _new_node(
        node_group,
        "ShaderNodeMath",
        "Effective Block Size",
        (-160.0, 100.0),
    )
    effective_size.operation = "MAXIMUM"
    size_was_clamped = _new_node(
        node_group,
        "ShaderNodeMath",
        "Block Size Was Clamped",
        (-160.0, -160.0),
    )
    size_was_clamped.operation = "LESS_THAN"

    size_vector = _new_node(
        node_group,
        "ShaderNodeCombineXYZ",
        "Block Size Vector",
        (60.0, 100.0),
    )
    bounds_diagonal = _new_node(
        node_group,
        "ShaderNodeVectorMath",
        "Bounds Diagonal",
        (-760.0, -360.0),
    )
    bounds_diagonal.operation = "LENGTH"

    mesh_to_volume = _new_node(
        node_group,
        "GeometryNodeMeshToVolume",
        "Mesh to Filled Volume",
        (280.0, 320.0),
    )
    _set_menu_socket_value(
        mesh_to_volume.inputs["Resolution Mode"],
        "Size",
        "VOXEL_SIZE",
    )
    mesh_to_volume.inputs["Density"].default_value = 1.0

    distribute_points = _new_node(
        node_group,
        "GeometryNodeDistributePointsInVolume",
        "Block Grid Points",
        (520.0, 320.0),
    )
    _set_menu_socket_value(
        distribute_points.inputs["Mode"],
        "Grid",
        "DENSITY_GRID",
    )
    distribute_points.inputs["Threshold"].default_value = VOLUME_THRESHOLD

    block_cube = _new_node(
        node_group,
        "GeometryNodeMeshCube",
        "Block Cube",
        (520.0, 40.0),
    )
    block_cube.inputs["Vertices X"].default_value = 2
    block_cube.inputs["Vertices Y"].default_value = 2
    block_cube.inputs["Vertices Z"].default_value = 2

    instance_blocks = _new_node(
        node_group,
        "GeometryNodeInstanceOnPoints",
        "Instance Blocks",
        (760.0, 300.0),
    )
    realize_blocks = _new_node(
        node_group,
        "GeometryNodeRealizeInstances",
        "Realize Blocks",
        (980.0, 300.0),
    )
    warning_true_geometry = _new_node(
        node_group,
        "GeometryNodeTransform",
        "Warning True Geometry",
        (980.0, 80.0),
    )

    safety_warning = _new_node(
        node_group,
        "GeometryNodeWarning",
        "Block Count Safety Warning",
        (760.0, -80.0),
    )
    safety_warning.warning_type = "WARNING"
    safety_warning.inputs["Message"].default_value = (
        "Block Size was increased to limit the longest axis to 64 blocks"
    )

    warning_switch = _new_node(
        node_group,
        "GeometryNodeSwitch",
        "Evaluate Safety Warning",
        (1200.0, 280.0),
    )
    warning_switch.input_type = "GEOMETRY"

    group_output = _new_node(
        node_group,
        "NodeGroupOutput",
        "Blockify Output",
        (1420.0, 280.0),
    )
    group_output.is_active_output = True

    links.new(group_input.outputs[GEOMETRY_SOCKET_NAME], bounding_box.inputs["Geometry"])
    links.new(bounding_box.outputs["Max"], dimensions.inputs[0])
    links.new(bounding_box.outputs["Min"], dimensions.inputs[1])
    links.new(dimensions.outputs["Vector"], separate_dimensions.inputs["Vector"])
    links.new(separate_dimensions.outputs["X"], longest_xy.inputs[0])
    links.new(separate_dimensions.outputs["Y"], longest_xy.inputs[1])
    links.new(longest_xy.outputs["Value"], longest_axis.inputs[0])
    links.new(separate_dimensions.outputs["Z"], longest_axis.inputs[1])
    links.new(longest_axis.outputs["Value"], minimum_safe_size.inputs[0])

    links.new(group_input.outputs[BLOCK_SIZE_SOCKET_NAME], effective_size.inputs[0])
    links.new(minimum_safe_size.outputs["Value"], effective_size.inputs[1])
    links.new(group_input.outputs[BLOCK_SIZE_SOCKET_NAME], size_was_clamped.inputs[0])
    links.new(minimum_safe_size.outputs["Value"], size_was_clamped.inputs[1])

    for axis_input in ("X", "Y", "Z"):
        links.new(effective_size.outputs["Value"], size_vector.inputs[axis_input])

    links.new(dimensions.outputs["Vector"], bounds_diagonal.inputs[0])
    links.new(group_input.outputs[GEOMETRY_SOCKET_NAME], mesh_to_volume.inputs["Mesh"])
    links.new(effective_size.outputs["Value"], mesh_to_volume.inputs["Voxel Size"])
    links.new(
        bounds_diagonal.outputs["Value"],
        mesh_to_volume.inputs["Interior Band Width"],
    )

    links.new(mesh_to_volume.outputs["Volume"], distribute_points.inputs["Volume"])
    links.new(size_vector.outputs["Vector"], distribute_points.inputs["Spacing"])
    links.new(size_vector.outputs["Vector"], block_cube.inputs["Size"])
    links.new(distribute_points.outputs["Points"], instance_blocks.inputs["Points"])
    links.new(block_cube.outputs["Mesh"], instance_blocks.inputs["Instance"])
    links.new(instance_blocks.outputs["Instances"], realize_blocks.inputs["Geometry"])
    links.new(
        realize_blocks.outputs["Geometry"],
        warning_true_geometry.inputs["Geometry"],
    )

    links.new(size_was_clamped.outputs["Value"], safety_warning.inputs["Show"])
    links.new(safety_warning.outputs["Show"], warning_switch.inputs["Switch"])
    links.new(realize_blocks.outputs["Geometry"], warning_switch.inputs["False"])
    links.new(warning_true_geometry.outputs["Geometry"], warning_switch.inputs["True"])
    links.new(warning_switch.outputs["Output"], group_output.inputs[GEOMETRY_SOCKET_NAME])


def _upgrade_blockify_node_group(node_group):
    _ensure_blockify_interface(node_group)
    _build_blockify_node_tree(node_group)
    node_group.is_modifier = True
    node_group[NODE_GROUP_SCHEMA_KEY] = NODE_GROUP_SCHEMA_VERSION


def _migrate_blockify_node_groups():
    for node_group in bpy.data.node_groups:
        if node_group.bl_idname != "GeometryNodeTree":
            continue
        if not node_group.get(NODE_GROUP_OWNER_KEY, False):
            continue
        if node_group.get(NODE_GROUP_SCHEMA_KEY) == 1:
            _upgrade_blockify_node_group(node_group)


def _run_deferred_migration():
    try:
        _migrate_blockify_node_groups()
    except AttributeError as error:
        # Add-on registration temporarily exposes bpy.data as RestrictData.
        if "node_groups" in str(error):
            return 0.1
        raise

    if bpy.app.driver_namespace.get(MIGRATION_TIMER_KEY) is _run_deferred_migration:
        bpy.app.driver_namespace.pop(MIGRATION_TIMER_KEY, None)
    return None


@persistent
def _migrate_after_load(_unused):
    _migrate_blockify_node_groups()


def _remove_migration_callbacks():
    timer_callback = bpy.app.driver_namespace.pop(MIGRATION_TIMER_KEY, None)
    if timer_callback is not None and bpy.app.timers.is_registered(timer_callback):
        bpy.app.timers.unregister(timer_callback)

    load_callback = bpy.app.driver_namespace.pop(LOAD_POST_CALLBACK_KEY, None)
    if load_callback is not None:
        try:
            bpy.app.handlers.load_post.remove(load_callback)
        except ValueError:
            pass


def _schedule_migration():
    bpy.app.handlers.load_post.append(_migrate_after_load)
    bpy.app.driver_namespace[LOAD_POST_CALLBACK_KEY] = _migrate_after_load

    bpy.app.timers.register(_run_deferred_migration, first_interval=0.0)
    bpy.app.driver_namespace[MIGRATION_TIMER_KEY] = _run_deferred_migration


def _find_blockify_node_group():
    for node_group in bpy.data.node_groups:
        if (
            node_group.bl_idname == "GeometryNodeTree"
            and node_group.get(NODE_GROUP_OWNER_KEY, False)
            and node_group.get(NODE_GROUP_SCHEMA_KEY) == NODE_GROUP_SCHEMA_VERSION
        ):
            return node_group
    return None


def _create_blockify_node_group():
    node_group = bpy.data.node_groups.new(NODE_GROUP_NAME, "GeometryNodeTree")
    node_group[NODE_GROUP_OWNER_KEY] = True

    try:
        _upgrade_blockify_node_group(node_group)
    except Exception:
        bpy.data.node_groups.remove(node_group)
        raise

    return node_group


def _ensure_blockify_node_group():
    node_group = _find_blockify_node_group()
    if node_group is not None:
        return node_group
    return _create_blockify_node_group()


class BLOCKIFY_OT_add_modifier(Operator):
    bl_idname = "object.blockify_add_modifier"
    bl_label = "Blockify"
    bl_description = "Add a Blockify Geometry Nodes modifier"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        source = context.active_object

        if context.mode != "OBJECT":
            cls.poll_message_set("Blockify requires Object Mode")
            return False
        if source is None or source.type != "MESH":
            cls.poll_message_set("Select a mesh object")
            return False
        if not source.is_editable:
            cls.poll_message_set("The selected mesh object is not editable")
            return False
        return True

    def execute(self, context):
        source = context.active_object
        _migrate_blockify_node_groups()
        node_group = _ensure_blockify_node_group()

        modifier = source.modifiers.new(name="Blockify", type="NODES")
        modifier.node_group = node_group
        source.modifiers.active = modifier

        self.report({"INFO"}, f"Added {modifier.name} to {source.name}")
        return {"FINISHED"}


def _draw_blockify_modifier_menu(self, context):
    source = context.active_object
    if source is None or source.type != "MESH":
        return

    self.layout.separator()
    self.layout.operator(
        BLOCKIFY_OT_add_modifier.bl_idname,
        text="Blockify",
        icon="GEOMETRY_NODES",
    )


CLASSES = (BLOCKIFY_OT_add_modifier,)
REGISTERED_CLASS_NAMES = (
    "BLOCKIFY_PT_main",
    "BLOCKIFY_OT_generate",
    "BLOCKIFY_OT_add_modifier",
)


def _remove_menu_callback():
    callback = bpy.app.driver_namespace.pop(MENU_CALLBACK_KEY, None)
    if callback is None:
        return

    try:
        bpy.types.OBJECT_MT_modifier_add.remove(callback)
    except (RuntimeError, ValueError):
        # The callback may already have been removed during an add-on reload.
        pass


def _unregister_blockify_classes():
    previous_classes = bpy.app.driver_namespace.pop(
        REGISTERED_CLASSES_KEY,
        (),
    )
    for registered_class in reversed(previous_classes):
        try:
            bpy.utils.unregister_class(registered_class)
        except (RuntimeError, ValueError):
            pass

    # Handles register() followed by register() in the same module instance.
    for cls in reversed(CLASSES):
        try:
            bpy.utils.unregister_class(cls)
        except (RuntimeError, ValueError):
            pass

    # Clean up class names left by the earliest prototype when possible.
    for class_name in reversed(REGISTERED_CLASS_NAMES):
        registered_class = getattr(bpy.types, class_name, None)
        if registered_class is not None:
            try:
                bpy.utils.unregister_class(registered_class)
            except (RuntimeError, ValueError):
                pass


def _remove_legacy_scene_property():
    if hasattr(bpy.types.Scene, LEGACY_SETTING_NAME):
        delattr(bpy.types.Scene, LEGACY_SETTING_NAME)


def unregister():
    _remove_migration_callbacks()
    _remove_menu_callback()
    _remove_legacy_scene_property()
    _unregister_blockify_classes()


def register():
    # Clean up both the old prototype and a previous Text Editor run.
    unregister()

    for cls in CLASSES:
        bpy.utils.register_class(cls)
    bpy.app.driver_namespace[REGISTERED_CLASSES_KEY] = CLASSES

    bpy.types.OBJECT_MT_modifier_add.append(_draw_blockify_modifier_menu)
    bpy.app.driver_namespace[MENU_CALLBACK_KEY] = _draw_blockify_modifier_menu
    _schedule_migration()


if __name__ == "__main__":
    register()
