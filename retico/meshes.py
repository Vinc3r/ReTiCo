import bpy
import math
from . import selection_sets
from bpy.types import Scene
from bpy.props import (
    FloatProperty,
    BoolProperty
)

"""
**********************************************************************
*                            def section                             *
**********************************************************************
"""


def meshes_names_to_clipboard():
    """ Send object names to clipboard using "name", "name", "name", pattern
    """
    # var init
    meshes_names_to_list = []
    meshes_names_to_clipboard = ""
    selected_only = bpy.context.scene.retico_mesh_check_only_selected
    objects_selected = selection_sets.meshes_in_selection(
    ) if selected_only else selection_sets.meshes_selectable()

    # function core

    # getting a list, to be able to sort alphabetically
    for obj in objects_selected:
        meshes_names_to_list.append(obj.name)
    meshes_names_to_list = sorted(meshes_names_to_list, key=str.lower)

    # converting all list items to a single string
    for name in meshes_names_to_list:
        if name is meshes_names_to_list[-1]:
            meshes_names_to_clipboard += f'"{name}"'
        else:
            meshes_names_to_clipboard += f'"{name}", '

    # sending to clipboard
    bpy.context.window_manager.clipboard = meshes_names_to_clipboard

    return {'FINISHED'}


def transfer_names():
    """ Copy object name to mesh name
    """
    # var init
    user_active = bpy.context.view_layer.objects.active
    is_user_in_edit_mode = False
    selected_only = bpy.context.scene.retico_mesh_check_only_selected
    objects_selected = selection_sets.meshes_in_selection(
    ) if selected_only else selection_sets.meshes_selectable()

    # handling active object
    if (
        bpy.context.view_layer.objects.active
        and bpy.context.view_layer.objects.active.mode == 'EDIT'
    ):
        is_user_in_edit_mode = True
        bpy.ops.object.mode_set(mode='OBJECT')

    # function core
    for obj in objects_selected:
        obj.data.name = "tmp"  # temp name to avoid naming conflict later

    for obj in objects_selected:
        obj.data.name = obj.name

    # handling active object
    bpy.context.view_layer.objects.active = user_active
    if is_user_in_edit_mode:
        bpy.ops.object.mode_set(mode='EDIT')

    return {'FINISHED'}


def set_autosmooth(user_angle=85):
    """ Activate autosmooth
    """
    # var init
    user_active = bpy.context.view_layer.objects.active
    is_user_in_edit_mode = False
    selected_only = bpy.context.scene.retico_mesh_check_only_selected
    objects_selected = selection_sets.meshes_in_selection(
    ) if selected_only else selection_sets.meshes_selectable()

    # handling active object
    if bpy.context.view_layer.objects.active.mode == 'EDIT':
        is_user_in_edit_mode = True
        bpy.ops.object.mode_set(mode='OBJECT')

    # function core
    for obj in objects_selected:
        bpy.context.view_layer.objects.active = obj
        mesh = obj.data

        mesh.use_auto_smooth = True
        mesh.auto_smooth_angle = math.radians(user_angle)
        bpy.ops.object.shade_smooth()

    # handling active object
    bpy.context.view_layer.objects.active = user_active
    if is_user_in_edit_mode:
        bpy.ops.object.mode_set(mode='EDIT')

    return {'FINISHED'}


def set_custom_normals(apply=True):
    """ Add or delete custom normals if asked
    """
    # var init
    user_active = bpy.context.view_layer.objects.active
    is_user_in_edit_mode = False
    selected_only = bpy.context.scene.retico_mesh_check_only_selected
    objects_selected = selection_sets.meshes_in_selection(
    ) if selected_only else selection_sets.meshes_selectable()

    # handling active object
    if bpy.context.view_layer.objects.active.mode == 'EDIT':
        is_user_in_edit_mode = True
        bpy.ops.object.mode_set(mode='OBJECT')

    # function core
    for obj in objects_selected:
        bpy.context.view_layer.objects.active = obj
        mesh = obj.data

        if apply:
            bpy.ops.mesh.customdata_custom_splitnormals_add()
        else:
            bpy.ops.mesh.customdata_custom_splitnormals_clear()

    # handling active object
    bpy.context.view_layer.objects.active = user_active
    if is_user_in_edit_mode:
        bpy.ops.object.mode_set(mode='EDIT')

    return {'FINISHED'}


def report_instances():
    """ Report meshes using instances
    """
    # var init
    obj_using_instance = []
    meshes_instanced = []
    update_selection = bpy.context.scene.retico_mesh_reports_update_selection
    selected_only = bpy.context.scene.retico_mesh_check_only_selected
    objects_selected = selection_sets.meshes_in_selection(
    ) if selected_only else selection_sets.meshes_selectable()
    report_message = []

    # function core

    if update_selection:
        for obj in bpy.context.selected_objects:
            obj.select_set(False)

    for obj in objects_selected:
        mesh = obj.data
        already_exists = False
        mesh_used_id = 0

        # skipping non-instanced
        if mesh.users <= 1:
            continue

        if update_selection:
            # select those using instances
            obj.select_set(True)

        # checking if instanced mesh already in list
        for mesh_inst_id in range(len(meshes_instanced)):
            if mesh == meshes_instanced[mesh_inst_id]:
                already_exists = True
                mesh_used_id = mesh_inst_id
                continue
        # if not, adding it and save instance id
        if not already_exists:
            meshes_instanced.append(mesh)
            mesh_inst_id = len(meshes_instanced) - 1

        # saving [object, instance_used_id]
        obj_using_instance.append([obj, mesh_inst_id])

    # for each instances, listing objects using it
    for mesh_inst_id in range(len(meshes_instanced)):
        obj_using_instance_list = []
        obj_using_instance_list_name = ""
        for obj_info in obj_using_instance:
            if obj_info[1] == mesh_inst_id:
                obj_using_instance_list.append(obj_info[0])
        for obj in obj_using_instance_list:
            obj_using_instance_list_name += "{}, ".format(obj.name)

        report_message.append("{} used by: {}".format(
            meshes_instanced[mesh_inst_id].name, obj_using_instance_list_name)[:-2])

    if update_selection and len(meshes_instanced) > 0:
        bpy.context.view_layer.objects.active = obj_using_instance[0][0]

    if len(meshes_instanced) == 0:
        return False
    else:
        return report_message


"""
**********************************************************************
*                        Panel class section                         *
**********************************************************************
"""


class RETICO_PT_mesh_3dviewPanel(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "ReTiCo"


class RETICO_PT_mesh(RETICO_PT_mesh_3dviewPanel):
    bl_label = "Meshes"
    bl_idname = "RETICO_PT_mesh"

    def draw(self, context):
        layout = self.layout

        box = layout.box()
        row = box.row()
        row.prop(context.scene, "retico_mesh_check_only_selected",
                 text="only on selection")


class RETICO_PT_mesh_misc(RETICO_PT_mesh_3dviewPanel):
    bl_parent_id = "RETICO_PT_mesh"
    bl_idname = "RETICO_PT_mesh_misc"
    bl_label = "Misc"

    def draw(self, context):
        layout = self.layout
        if (
            not bpy.context.scene.retico_mesh_check_only_selected
            or (
                bpy.context.scene.retico_mesh_check_only_selected
                and len(bpy.context.selected_objects) > 0
            )
        ):
            # transfer object name to mesh name
            row = layout.row()
            row.operator("retico.mesh_transfer_names",
                         text="Transfer names", icon='SORTALPHA')

            # copy names to clipboard
            row = layout.row()
            row.operator("retico.mesh_name_to_clipboard",
                         text="Copy names to clipboard", icon='COPYDOWN')

        else:
            row = layout.row(align=True)
            row.label(text="No object in selection.")


class RETICO_PT_mesh_normals(RETICO_PT_mesh_3dviewPanel):
    bl_parent_id = "RETICO_PT_mesh"
    bl_idname = "RETICO_PT_mesh_normals"
    bl_label = "Normals"

    def draw(self, context):
        layout = self.layout
        if (
            not bpy.context.scene.retico_mesh_check_only_selected
            or (
                bpy.context.scene.retico_mesh_check_only_selected
                and len(bpy.context.selected_objects) > 0
            )
        ):
            # overwrite autosmooth
            row = layout.row(align=True)
            row.operator("retico.mesh_set_autosmooth", text="Set autosmooth")
            row.prop(context.scene, "retico_mesh_autosmooth_angle",
                     text="", slider=True)
            row = layout.row(align=True)
            row.label(text="Custom Normals:")
            row.operator("retico.mesh_set_custom_normals",
                         text="Add").apply = True
            row.operator("retico.mesh_set_custom_normals",
                         text="Del").apply = False
        else:
            row = layout.row(align=True)
            row.label(text="No object in selection.")


class RETICO_PT_mesh_report(RETICO_PT_mesh_3dviewPanel):
    bl_parent_id = "RETICO_PT_mesh"
    bl_idname = "RETICO_PT_mesh_report"
    bl_label = "Report"

    def draw(self, context):
        layout = self.layout

        if (
            not bpy.context.scene.retico_mesh_check_only_selected
            or (
                bpy.context.scene.retico_mesh_check_only_selected
                and len(bpy.context.selected_objects) > 0
            )
        ):

            # report
            box = layout.box()
            row = box.row()
            row.prop(context.scene, "retico_mesh_reports_update_selection",
                     text="update selection")
            row.prop(context.scene, "retico_mesh_reports_to_clipboard",
                     text="to clipboard")
            grid = layout.grid_flow(
                row_major=True, columns=2, even_columns=True, even_rows=True, align=True)
            row = grid.row(align=True)
            row.operator("retico.mesh_report_instances", text="Instances")
        else:
            row = layout.row(align=True)
            row.label(text="No object in selection.")


"""
**********************************************************************
*                     Operator class section                         *
**********************************************************************
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
        self.report({'INFO'}, "---[ Copied to clipboard ]---")

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
        self.report({'INFO'}, "---[ Object name to Mesh ]---")

        return {'FINISHED'}


class RETICO_OT_mesh_set_autosmooth(bpy.types.Operator):
    bl_idname = "retico.mesh_set_autosmooth"
    bl_label = "Batch set autosmooth"
    bl_description = "Batch set autosmooth"

    @classmethod
    def poll(cls, context):
        return len(context.view_layer.objects) > 0

    def execute(self, context):
        set_autosmooth(context.scene.retico_mesh_autosmooth_angle)
        self.report({'INFO'}, "---[ Autosmooth ]---")
        return {'FINISHED'}


class RETICO_OT_mesh_set_custom_normals(bpy.types.Operator):
    bl_idname = "retico.mesh_set_custom_normals"
    bl_label = "Add or delete custom split normals"
    bl_description = "Add or delete custom split normals"
    apply: BoolProperty()

    @classmethod
    def poll(cls, context):
        return len(context.view_layer.objects) > 0

    def execute(self, context):
        set_custom_normals(self.apply)
        self.report({'INFO'}, "---[ Custom Normals ]---")
        return {'FINISHED'}


class RETICO_OT_mesh_report_instances(bpy.types.Operator):
    bl_idname = "retico.mesh_report_instances"
    bl_label = "List objects using instances"
    bl_description = "List objects using instances"

    @classmethod
    def poll(cls, context):
        return len(context.view_layer.objects) > 0

    def execute(self, context):
        message = report_instances()
        self.report({'INFO'}, "---[ Objects using instances ]---")
        if not message:
            self.report({'INFO'}, "No instances detected.")
        else:
            to_clipboard = context.scene.retico_mesh_reports_to_clipboard
            message_to_clipboard = ""
            for report in message:
                message_to_clipboard += ("\r\n" + report)
                self.report({'INFO'}, report)
            if to_clipboard:
                context.window_manager.clipboard = message_to_clipboard
        return {'FINISHED'}


"""
**********************************************************************
* Registration                                                       *
**********************************************************************
"""


classes = (
    RETICO_PT_mesh,
    RETICO_PT_mesh_misc,
    RETICO_PT_mesh_normals,
    RETICO_PT_mesh_report,
    RETICO_OT_mesh_transfer_names,
    RETICO_OT_mesh_set_autosmooth,
    RETICO_OT_mesh_set_custom_normals,
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
    Scene.retico_mesh_reports_update_selection = BoolProperty(
        name="Report update selection",
        description="Reports modify user selection",
        default=False
    )
    Scene.retico_mesh_reports_to_clipboard = BoolProperty(
        name="Reports sent to clipboard",
        description="Reports sent to clipboard",
        default=False
    )
    Scene.retico_mesh_autosmooth_angle = FloatProperty(
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

    del Scene.retico_mesh_autosmooth_angle
    del Scene.retico_mesh_reports_update_selection
    del Scene.retico_mesh_reports_to_clipboard
    del Scene.retico_mesh_check_only_selected


if __name__ == "__main__":
    register()
