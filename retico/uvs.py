import bpy
import bmesh
from . import selection_sets
from math import sin, cos, pi
from mathutils import Vector
from bpy.types import Scene
from bpy.props import (
    EnumProperty,
    FloatProperty,
    FloatVectorProperty,
    BoolProperty,
    IntProperty,
    StringProperty
)


def rename_uv_channels(selected_only=True):
    objects_selected = selection_sets.meshes_in_selection(
    ) if selected_only else selection_sets.meshes_selectable()

    for obj in objects_selected:
        mesh = obj.data
        if len(mesh.uv_layers) < 0:
            continue
        for uv_chan in range(len(mesh.uv_layers)):
            if uv_chan == 0:
                mesh.uv_layers[0].name = "UVMap"
            else:
                mesh.uv_layers[uv_chan].name = "UV{}".format((uv_chan + 1))

    return {'FINISHED'}


def activate_uv_channels(selected_only=True, uv_chan=0):
    objects_selected = selection_sets.meshes_in_selection(
    ) if selected_only else selection_sets.meshes_selectable()

    for obj in objects_selected:
        mesh = obj.data
        if len(mesh.uv_layers) == 0 or \
                len(mesh.uv_layers) <= uv_chan:
            for index in range(uv_chan + 1):
                # UV1 creation
                if index == 0 and len(mesh.uv_layers) == 0:
                    mesh.uv_layers.new()
                # others UV, slipping existing
                elif len(mesh.uv_layers) < (index + 1):
                    mesh.uv_layers.new(name="UV{}".format(uv_chan + 1))

        obj.data.uv_layers[uv_chan].active = True

    return {'FINISHED'}


def report_no_uv(update_selection=False, channel=0):
    objects_no_uv = []
    obj_no_uv_names: str = ""
    message_suffix = "no UV on:"
    is_all_good = False
    selected_only = bpy.context.scene.retico_uvs_check_only_selected

    if channel == 1:
        # UV2 check
        objects_no_uv = selection_sets.meshes_without_uv(selected_only)[1]
        message_suffix = "no UV2 on:"
    else:
        # ask to report no UV at all
        objects_no_uv = selection_sets.meshes_without_uv(selected_only)[0]
    if len(objects_no_uv) == 0:
        if channel == 1:
            message = "All your meshes have UV2."
        else:
            message = "All your meshes have UV1."
        is_all_good = True
    else:
        if update_selection:
            for obj in bpy.context.selected_objects:
                obj.select_set(False)

        for obj in objects_no_uv:
            obj_no_uv_names += "{}, ".format(obj.name)
            if update_selection:
                obj.select_set(True)

        if update_selection:
            bpy.context.view_layer.objects.active = objects_no_uv[0]

        message = "{} {}".format(message_suffix, obj_no_uv_names)

    # removing last ", " charz
    return message[:-2], is_all_good


def box_mapping(selected_only=True, size=1.0):
    """ This apply a box mapping into UV channel 0.
    """
    objects_selected = selection_sets.meshes_in_selection(
    ) if selected_only else selection_sets.meshes_selectable()
    user_active = bpy.context.view_layer.objects.active
    is_user_in_edit_mode = False

    if bpy.context.view_layer.objects.active.mode == 'EDIT':
        is_user_in_edit_mode = True

    for obj in objects_selected:
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.context.view_layer.objects.active = obj
        mesh = obj.data
        if len(mesh.uv_layers) == 0:
            mesh.uv_layers.new()
        mesh.uv_layers[0].active = True
        bpy.ops.object.mode_set(mode='EDIT')
        mesh_box_mapping(mesh, size, is_user_in_edit_mode)

    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.view_layer.objects.active = user_active
    if is_user_in_edit_mode:
        bpy.ops.object.mode_set(mode='EDIT')

    return {'FINISHED'}


def mesh_box_mapping(mesh, size=1.0, only_selected=False):
    """ This function is shamefully copy-pasted from MagicUV addon (UVW function)
        and rudely adapt for my needs.
    """

    offset = [0.0, 0.0, 0.0]
    rotation = [0.0, 0.0, 0.0]
    tex_aspect = 1.0
    bm = bmesh.new()
    bm = bmesh.from_edit_mesh(mesh)
    uv_layer = bm.loops.layers.uv.active

    scale = 1.0 / size

    sx = 1.0 * scale
    sy = 1.0 * scale
    sz = 1.0 * scale
    ofx = offset[0]
    ofy = offset[1]
    ofz = offset[2]
    rx = rotation[0] * pi / 180.0
    ry = rotation[1] * pi / 180.0
    rz = rotation[2] * pi / 180.0
    aspect = tex_aspect

    faces_to_map = bm.faces
    if only_selected:
        faces_to_map = [f for f in bm.faces if f.select == True]

    # update UV coordinate
    for f in faces_to_map:
        n = f.normal
        for l in f.loops:
            co = l.vert.co
            x = co.x * sx
            y = co.y * sy
            z = co.z * sz

            # X-plane
            if abs(n[0]) >= abs(n[1]) and abs(n[0]) >= abs(n[2]):
                if n[0] >= 0.0:
                    u = (y - ofy) * cos(rx) + (z - ofz) * sin(rx)
                    v = -(y * aspect - ofy) * sin(rx) + \
                        (z * aspect - ofz) * cos(rx)
                else:
                    u = -(y - ofy) * cos(rx) + (z - ofz) * sin(rx)
                    v = (y * aspect - ofy) * sin(rx) + \
                        (z * aspect - ofz) * cos(rx)
            # Y-plane
            elif abs(n[1]) >= abs(n[0]) and abs(n[1]) >= abs(n[2]):
                if n[1] >= 0.0:
                    u = -(x - ofx) * cos(ry) + (z - ofz) * sin(ry)
                    v = (x * aspect - ofx) * sin(ry) + \
                        (z * aspect - ofz) * cos(ry)
                else:
                    u = (x - ofx) * cos(ry) + (z - ofz) * sin(ry)
                    v = -(x * aspect - ofx) * sin(ry) + \
                        (z * aspect - ofz) * cos(ry)
            # Z-plane
            else:
                if n[2] >= 0.0:
                    u = (x - ofx) * cos(rz) + (y - ofy) * sin(rz)
                    v = -(x * aspect - ofx) * sin(rz) + \
                        (y * aspect - ofy) * cos(rz)
                else:
                    u = -(x - ofx) * cos(rz) - (y + ofy) * sin(rz)
                    v = -(x * aspect + ofx) * sin(rz) + \
                        (y * aspect - ofy) * cos(rz)

            l[uv_layer].uv = Vector((u, v))

    bmesh.update_edit_mesh(mesh)
    bm.free()


class RETICO_PT_uv_panel(bpy.types.Panel):
    bl_label = "UVs"
    bl_idname = "RETICO_PT_uv_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "ReTiCo"

    def draw(self, context):
        layout = self.layout

        box = layout.box()
        row = box.row()
        row.prop(context.scene, "retico_uvs_check_only_selected",
                 text="only selected")

        box = layout.box()
        # activate
        row = box.row(align=True)
        row.label(text="Active:")
        row.operator("retico.uv_activate_channel", text="1").channel = 0
        row.operator("retico.uv_activate_channel", text="2").channel = 1
        # rename channels
        row = box.row(align=True)
        row.operator("retico.uv_rename_channel", text="Rename channels")
        # box mapping
        row = box.row(align=True)
        row.operator("retico.uv_box_mapping", text="Box mapping")
        row.prop(context.scene, "retico_box_mapping_size", text="")

        # report
        box = layout.box()
        row = box.row(align=True)
        row.label(text="Report: ")
        row = box.row()
        row.prop(context.scene, "retico_uvs_report_update_selection",
                 text="update selection")
        grid = box.grid_flow(
            row_major=True, columns=2, even_columns=True, even_rows=True, align=True)
        row = grid.row(align=True)
        row.operator("retico.uv_report_none", text="no UV").channel = 0
        row = grid.row(align=True)
        row.operator("retico.uv_report_none", text="2").channel = 1


class RETICO_OT_uv_activate_channel(bpy.types.Operator):
    bl_idname = "retico.uv_activate_channel"
    bl_label = "Set active UV"
    bl_description = "Set active UV"
    channel: IntProperty()

    @classmethod
    def poll(cls, context):
        return len(context.view_layer.objects) > 0

    def execute(self, context):
        message, is_all_good = report_no_uv(
            context.scene.retico_uvs_check_only_selected, self.channel)
        if not is_all_good:
            self.report({'WARNING'}, "{}... Now fixed!".format(message))
        activate_uv_channels(
            context.scene.retico_uvs_check_only_selected, self.channel)

        return {'FINISHED'}


class RETICO_OT_uv_box_mapping(bpy.types.Operator):
    bl_idname = "retico.uv_box_mapping"
    bl_label = "UV1 box mapping (MagicUV UVW algorithm)"
    bl_description = "UV1 box mapping (MagicUV UVW algorithm)"

    @classmethod
    def poll(cls, context):
        return len(context.view_layer.objects) > 0

    def execute(self, context):
        message, is_all_good = report_no_uv(
            context.scene.retico_uvs_check_only_selected, 0)
        if not is_all_good:
            self.report({'WARNING'}, "{}... Now fixed!".format(message))
        box_mapping(context.scene.retico_uvs_check_only_selected,
                    context.scene.retico_box_mapping_size)

        return {'FINISHED'}


class RETICO_OT_uv_rename_channel(bpy.types.Operator):
    bl_idname = "retico.uv_rename_channel"
    bl_label = "Normalize UV channels naming"
    bl_description = "Normalize UV channels naming (UVMap, then UV2, UV3...)"

    @classmethod
    def poll(cls, context):
        return len(context.view_layer.objects) > 0

    def execute(self, context):
        rename_uv_channels(context.scene.retico_uvs_check_only_selected)

        return {'FINISHED'}


class RETICO_OT_uv_report_none(bpy.types.Operator):
    bl_idname = "retico.uv_report_none"
    bl_label = "Report object without UV chan"
    bl_description = "Report object without UV chan, both in console and Info editor"
    channel: IntProperty()

    @classmethod
    def poll(cls, context):
        return len(context.view_layer.objects) > 0

    def execute(self, context):
        message, is_all_good = report_no_uv(
            context.scene.retico_uvs_report_update_selection, self.channel)
        if is_all_good:
            self.report({'INFO'}, message)
        else:
            self.report({'WARNING'}, message)

        return {'FINISHED'}


classes = (
    RETICO_PT_uv_panel,
    RETICO_OT_uv_activate_channel,
    RETICO_OT_uv_box_mapping,
    RETICO_OT_uv_rename_channel,
    RETICO_OT_uv_report_none,
)


def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
    Scene.retico_uvs_check_only_selected = BoolProperty(
        name="UVs tab use selected only",
        description="Should Uvs operations only check selected objects?",
        default=True
    )
    Scene.retico_box_mapping_size = FloatProperty(
        name="box mapping size",
        description="box mapping size",
        default=1.0,
        min=0.0,
    )
    Scene.retico_uvs_report_update_selection = BoolProperty(
        name="Report update selection",
        description="Should reports also update your selection?",
        default=False
    )


def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)

    del Scene.retico_box_mapping_size
    del Scene.retico_uvs_check_only_selected
    del Scene.retico_uvs_report_update_selection


if __name__ == "__main__":
    register()
