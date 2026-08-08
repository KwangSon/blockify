bl_info = {
    "name": "Blockify Modifier Prototype",
    "author": "Blockify Contributors",
    "version": (0, 0, 2),
    "blender": (5, 0, 0),
    "location": "Properties > Modifiers > Add Modifier > Blockify",
    "description": "Add a Blockify Geometry Nodes modifier to a mesh",
    "category": "Object",
}

import bpy
from bpy.types import Operator


NODE_GROUP_NAME = "Blockify"
NODE_GROUP_OWNER_KEY = "blockify.node_group"
NODE_GROUP_SCHEMA_KEY = "blockify.schema_version"
NODE_GROUP_SCHEMA_VERSION = 1

LEGACY_SETTING_NAME = "blockify_test_block_size"
MENU_CALLBACK_KEY = "blockify.modifier_menu_callback"


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
    node_group.is_modifier = True
    node_group[NODE_GROUP_OWNER_KEY] = True
    node_group[NODE_GROUP_SCHEMA_KEY] = NODE_GROUP_SCHEMA_VERSION

    node_group.interface.new_socket(
        name="Geometry",
        in_out="INPUT",
        socket_type="NodeSocketGeometry",
    )

    block_size_socket = node_group.interface.new_socket(
        name="Block Size",
        in_out="INPUT",
        socket_type="NodeSocketFloat",
    )
    block_size_socket.description = "Size of each block in Blender units"
    block_size_socket.default_value = 0.1
    block_size_socket.min_value = 0.001
    block_size_socket.max_value = 1000.0
    block_size_socket.subtype = "DISTANCE"
    block_size_socket.force_non_field = True

    node_group.interface.new_socket(
        name="Geometry",
        in_out="OUTPUT",
        socket_type="NodeSocketGeometry",
    )

    input_node = node_group.nodes.new("NodeGroupInput")
    input_node.name = "Blockify Input"
    input_node.label = "Blockify Input"
    input_node.location = (-200.0, 0.0)

    output_node = node_group.nodes.new("NodeGroupOutput")
    output_node.name = "Blockify Output"
    output_node.label = "Blockify Output"
    output_node.location = (200.0, 0.0)
    output_node.is_active_output = True

    node_group.links.new(
        input_node.outputs["Geometry"],
        output_node.inputs["Geometry"],
    )

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
    for class_name in reversed(REGISTERED_CLASS_NAMES):
        registered_class = getattr(bpy.types, class_name, None)
        if registered_class is not None:
            bpy.utils.unregister_class(registered_class)


def _remove_legacy_scene_property():
    if hasattr(bpy.types.Scene, LEGACY_SETTING_NAME):
        delattr(bpy.types.Scene, LEGACY_SETTING_NAME)


def unregister():
    _remove_menu_callback()
    _remove_legacy_scene_property()
    _unregister_blockify_classes()


def register():
    # Clean up both the old prototype and a previous Text Editor run.
    unregister()

    for cls in CLASSES:
        bpy.utils.register_class(cls)

    bpy.types.OBJECT_MT_modifier_add.append(_draw_blockify_modifier_menu)
    bpy.app.driver_namespace[MENU_CALLBACK_KEY] = _draw_blockify_modifier_menu


if __name__ == "__main__":
    register()
