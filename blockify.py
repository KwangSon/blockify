bl_info = {
    "name": "Blockify Prototype",
    "author": "Blockify Contributors",
    "version": (0, 0, 1),
    "blender": (5, 0, 0),
    "location": "3D Viewport > Sidebar > Blockify",
    "description": "Create a test block next to the selected mesh",
    "category": "Object",
}

import math

import bpy
from bpy.props import FloatProperty
from bpy.types import Operator, Panel
from mathutils import Vector


SETTING_NAME = "blockify_test_block_size"


class BLOCKIFY_OT_generate(Operator):
    bl_idname = "blockify.generate"
    bl_label = "Create Test Block"
    bl_description = "Create a test block next to the selected mesh"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        source = context.active_object
        return (
            context.mode == "OBJECT"
            and source is not None
            and source.type == "MESH"
            and len(source.data.vertices) > 0
        )

    def execute(self, context):
        source = context.active_object

        if context.mode != "OBJECT":
            self.report({"ERROR"}, "Blockify requires Object Mode")
            return {"CANCELLED"}

        if source is None or source.type != "MESH":
            self.report({"ERROR"}, "Select a mesh object first")
            return {"CANCELLED"}

        if len(source.data.vertices) == 0:
            self.report({"ERROR"}, "The selected mesh has no vertices")
            return {"CANCELLED"}

        block_size = float(getattr(context.scene, SETTING_NAME))
        if not math.isfinite(block_size) or block_size <= 0.0:
            self.report({"ERROR"}, "Test Block Size must be greater than zero")
            return {"CANCELLED"}

        world_corners = [
            source.matrix_world @ Vector(corner) for corner in source.bound_box
        ]
        min_y = min(corner.y for corner in world_corners)
        max_x = max(corner.x for corner in world_corners)
        max_y = max(corner.y for corner in world_corners)
        min_z = min(corner.z for corner in world_corners)
        max_z = max(corner.z for corner in world_corners)

        block_center = Vector(
            (
                max_x + block_size,
                (min_y + max_y) * 0.5,
                (min_z + max_z) * 0.5,
            )
        )

        mesh = self._create_cube_mesh(
            f"{source.name}_BLOCKIFIED_TEST_MESH",
            block_size,
        )
        result = bpy.data.objects.new(f"{source.name}_BLOCKIFIED_TEST", mesh)
        result.location = block_center

        target_collection = (
            source.users_collection[0]
            if source.users_collection
            else context.scene.collection
        )
        target_collection.objects.link(result)

        for selected_object in context.selected_objects:
            selected_object.select_set(False)

        result.select_set(True)
        context.view_layer.objects.active = result

        self.report({"INFO"}, f"Created test block for {source.name}")
        return {"FINISHED"}

    @staticmethod
    def _create_cube_mesh(name, size):
        half_size = size * 0.5
        vertices = [
            (-half_size, -half_size, -half_size),
            (half_size, -half_size, -half_size),
            (half_size, half_size, -half_size),
            (-half_size, half_size, -half_size),
            (-half_size, -half_size, half_size),
            (half_size, -half_size, half_size),
            (half_size, half_size, half_size),
            (-half_size, half_size, half_size),
        ]
        faces = [
            (0, 3, 2, 1),
            (4, 5, 6, 7),
            (0, 1, 5, 4),
            (1, 2, 6, 5),
            (2, 3, 7, 6),
            (3, 0, 4, 7),
        ]

        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata(vertices, [], faces)
        mesh.update()
        return mesh


class BLOCKIFY_PT_main(Panel):
    bl_label = "Blockify"
    bl_idname = "BLOCKIFY_PT_main"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Blockify"

    def draw(self, context):
        layout = self.layout
        source = context.active_object

        if source is not None and source.type == "MESH":
            layout.label(text=f"Source: {source.name}", icon="MESH_DATA")
        else:
            layout.label(text="Select a mesh object", icon="INFO")

        layout.prop(context.scene, SETTING_NAME, text="Test Block Size")

        is_valid_source = (
            context.mode == "OBJECT"
            and source is not None
            and source.type == "MESH"
            and len(source.data.vertices) > 0
        )

        if source is not None and context.mode != "OBJECT":
            layout.label(text="Switch to Object Mode", icon="INFO")
        elif source is not None and source.type == "MESH" and not source.data.vertices:
            layout.label(text="The selected mesh is empty", icon="INFO")

        row = layout.row()
        row.enabled = is_valid_source
        row.operator(BLOCKIFY_OT_generate.bl_idname, icon="CUBE")


CLASSES = (
    BLOCKIFY_OT_generate,
    BLOCKIFY_PT_main,
)


def unregister():
    if hasattr(bpy.types.Scene, SETTING_NAME):
        delattr(bpy.types.Scene, SETTING_NAME)

    for cls in reversed(CLASSES):
        registered_class = getattr(bpy.types, cls.__name__, None)
        if registered_class is not None:
            bpy.utils.unregister_class(registered_class)


def register():
    # Make repeated runs from Blender's Text Editor safe during development.
    unregister()

    for cls in CLASSES:
        bpy.utils.register_class(cls)

    setattr(
        bpy.types.Scene,
        SETTING_NAME,
        FloatProperty(
            name="Test Block Size",
            description="Size of the generated test block in Blender units",
            default=1.0,
            min=0.01,
            soft_max=10.0,
            unit="LENGTH",
        ),
    )


if __name__ == "__main__":
    register()
