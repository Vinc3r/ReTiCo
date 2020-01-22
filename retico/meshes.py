import bpy
import math
from . import selection_sets
from bpy.types import Scene
from bpy.props import (
    EnumProperty,
    FloatProperty,
    FloatVectorProperty,
    BoolProperty,
    IntProperty,
    StringProperty
)


def meshes_names_to_clipboard():
    meshes_names_to_clipboard = ""
    selected_only = bpy.context.scene.retico_mesh_check_only_selected
    objects_selected = selection_sets.meshes_in_selection(
    ) if selected_only else selection_sets.meshes_selectable()

    for obj in objects_selected:
        if obj is objects_selected[-1]:
            meshes_names_to_clipboard += '"{}"'.format(obj.name)
        else:
            meshes_names_to_clipboard += '"{}",'.format(obj.name)
    bpy.context.window_manager.clipboard = meshes_names_to_clipboard
    return {'FINISHED'}


def transfer_names():
    # handling active object
    user_active = bpy.context.view_layer.objects.active
    is_user_in_edit_mode = False
    selected_only = bpy.context.scene.retico_mesh_check_only_selected

    if bpy.context.view_layer.objects.active.mode == 'EDIT':
        is_user_in_edit_mode = True
        bpy.ops.object.mode_set(mode='OBJECT')

    # function core
    objects_selected = selection_sets.meshes_in_selection(
    ) if selected_only else selection_sets.meshes_selectable()

    for obj in objects_selected:
        bpy.context.view_layer.objects.active = obj
        mesh = obj.data
        mesh.name = obj.name

    # handling active object
    bpy.context.view_layer.objects.active = user_active
    if is_user_in_edit_mode:
        bpy.ops.object.mode_set(mode='EDIT')

    return {'FINISHED'}


def set_autosmooth(user_angle=85):
    # handling active object
    user_active = bpy.context.view_layer.objects.active
    is_user_in_edit_mode = False
    selected_only = bpy.context.scene.retico_mesh_check_only_selected

    if bpy.context.view_layer.objects.active.mode == 'EDIT':
        is_user_in_edit_mode = True
        bpy.ops.object.mode_set(mode='OBJECT')

    # function core
    objects_selected = selection_sets.meshes_in_selection(
    ) if selected_only else selection_sets.meshes_selectable()

    for obj in objects_selected:
        bpy.context.view_layer.objects.active = obj
        mesh = obj.data
        if mesh.has_custom_normals:
            bpy.ops.mesh.customdata_custom_splitnormals_clear()
        mesh.use_auto_smooth = True
        mesh.auto_smooth_angle = math.radians(user_angle)
        bpy.ops.object.shade_smooth()

    # handling active object
    bpy.context.view_layer.objects.active = user_active
    if is_user_in_edit_mode:
        bpy.ops.object.mode_set(mode='EDIT')

    return {'FINISHED'}

def report_instances():
    print("youpi yop")
    return {'FINISHED'}


class RETICO_PT_mesh_panel(bpy.types.Panel):
    bl_label = "Meshes"
    bl_idname = "RETICO_PT_mesh_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "ReTiCo"

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        row = box.row()
        row.prop(context.scene, "retico_mesh_check_only_selected",
                 text="only selected")

        box = layout.box()
        # transfer object name to mesh name
        row = box.row()
        row.operator("retico.mesh_transfer_names", text="Transfer names")

        # overwrite autosmooth
        row = box.row(align=True)
        row.operator("retico.mesh_set_autosmooth", text="Set autosmooth")
        row.prop(context.scene, "retico_autosmooth_angle", text="", slider=True)

        # copy names to clipboard
        row = box.row()
        row.operator("retico.mesh_name_to_clipboard",
                     text="Copy names to clipboard")

        # report
        box = layout.box()
        row = box.row()
        row.label(text="Report:")
        """TODO
        row = box.row()
        row.prop(context.scene, "retico_material_report_update_selection",
                 text="update selection")
        grid = box.grid_flow(
            row_major=True, columns=2, even_columns=True, even_rows=True, align=True)
        row = grid.row(align=True)
        row.operator("retico.mesh_report_instances", text="instances")
        """


class RETICO_OT_mesh_name_to_clipboard(bpy.types.Operator):
    bl_idname = "retico.mesh_name_to_clipboard"
    bl_label = "Copy Object name to clipboard"
    bl_description = "Copy Object name to clipboard"

    @classmethod
    def poll(cls, context):
        return len(context.view_layer.objects) > 0

    def execute(self, context):
        meshes_names_to_clipboard()
        return {'FINISHED'}


class RETICO_OT_mesh_transfer_names(bpy.types.Operator):
    bl_idname = "retico.mesh_transfer_names"
    bl_label = "Copy Object name to its Data name"
    bl_description = "Copy Object name to its Data name"

    @classmethod
    def poll(cls, context):
        return len(context.view_layer.objects) > 0

    def execute(self, context):
        transfer_names()
        return {'FINISHED'}


class RETICO_OT_mesh_set_autosmooth(bpy.types.Operator):
    bl_idname = "retico.mesh_set_autosmooth"
    bl_label = "Set autosmooth to 85° and delete custom normals"
    bl_description = "Set autosmooth to 85° and delete custom normals"

    @classmethod
    def poll(cls, context):
        return len(context.view_layer.objects) > 0

    def execute(self, context):
        set_autosmooth(context.scene.retico_autosmooth_angle)
        return {'FINISHED'}


class RETICO_OT_mesh_report_instances(bpy.types.Operator):
    bl_idname = "retico.mesh_report_instances"
    bl_label = "List objects using instances"
    bl_description = "List objects using instances"

    @classmethod
    def poll(cls, context):
        return len(context.view_layer.objects) > 0

    def execute(self, context):
        report_instances()
        return {'FINISHED'}


classes = (
    RETICO_PT_mesh_panel,
    RETICO_OT_mesh_transfer_names,
    RETICO_OT_mesh_set_autosmooth,
    RETICO_OT_mesh_name_to_clipboard,
    RETICO_OT_mesh_report_instances,
)


def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
    Scene.retico_mesh_check_only_selected = BoolProperty(
        name="Mesh tab use selected only",
        description="Mesh operations applies on selection, or not",
        default=True
    )
    Scene.retico_autosmooth_angle = FloatProperty(
        name="autosmooth angle",
        description="autosmooth angle",
        default=85.0,
        min=0.0,
        max=180.0,
    )


def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)

    del Scene.retico_autosmooth_angle
    del Scene.retico_mesh_check_only_selected


if __name__ == "__main__":
    register()
