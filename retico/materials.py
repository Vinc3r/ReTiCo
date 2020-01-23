import bpy
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


def set_backface_culling(toggle):
    """ Toggle backface culling mode,
        both in materials settings and viewport
    """
    # var init
    selected_only = bpy.context.scene.retico_material_check_only_selected
    objects_selected = selection_sets.meshes_with_materials(selected_only)

    # materials
    for obj in objects_selected:
        for mat in obj.data.materials:
            if mat is not None:
                mat.use_backface_culling = toggle

    # viewports
    for area in bpy.context.screen.areas:
        if area.type != 'VIEW_3D':
            continue
        for space in area.spaces:
            if space.type != 'VIEW_3D':
                continue
            if space.shading.type == 'SOLID':
                space.shading.show_backface_culling = toggle

    return {'FINISHED'}


def set_active_texture(type="albedo"):
    """ Set a specific texture node to active,
        useful when viewport is shade as Solid -> Texture
    """
    # var init
    selected_only = bpy.context.scene.retico_material_check_only_selected
    # texture_condition = [node.type, node.output.type, node.output.link.to_node.type], default: albedo
    texture_condition = ['TEX_IMAGE', 'RGBA', 'BSDF_PRINCIPLED']
    if type == "orm":
        texture_condition = ['TEX_IMAGE', 'RGBA', 'SEPRGB']
    elif type == "normal":
        texture_condition = ['TEX_IMAGE', 'RGBA', 'NORMAL_MAP']
    elif type == "emit":
        texture_condition = ['TEX_IMAGE', 'RGBA', 'EMISSION']
    objects_selected = selection_sets.meshes_with_materials(selected_only)

    # function core
    for obj in objects_selected:
        mesh = obj.data
        for mat in mesh.materials:
            if mat.use_nodes:
                for node in mat.node_tree.nodes:
                    if node.type != texture_condition[0]:
                        # node have to pass first tests
                        continue
                    for out in node.outputs:
                        if out.type != texture_condition[1]:
                            # output have to pass test
                            continue
                        for link in out.links:
                            if link.to_node.type != texture_condition[2]:
                                # link have to pass test
                                continue
                            # ok we're sure about this node, let's make it active
                            node.select = True
                            mat.node_tree.nodes.active = node

    # update viewport
    bpy.ops.wm.redraw_timer(type='DRAW', iterations=1)

    # viewport shading
    if bpy.context.scene.retico_material_activeTex_viewShading_solid:
        for area in bpy.context.screen.areas:
            if area.type != 'VIEW_3D':
                continue
            for space in area.spaces:
                if space.type != 'VIEW_3D':
                    continue
                space.shading.type = 'SOLID'
                space.shading.color_type = 'TEXTURE'

    return {'FINISHED'}


def transfer_names():
    """ Name materials using "meshName.matID.000" pattern
    """
    # var init
    user_active = bpy.context.view_layer.objects.active
    is_user_in_edit_mode = False
    selected_only = bpy.context.scene.retico_material_check_only_selected

    # handling active object
    if bpy.context.view_layer.objects.active.mode == 'EDIT':
        is_user_in_edit_mode = True
        bpy.ops.object.mode_set(mode='OBJECT')

    # function core
    objects_selected = selection_sets.meshes_in_selection(
    ) if selected_only else selection_sets.meshes_selectable()
    for obj in objects_selected:
        object_materials = obj.data.materials
        if len(object_materials) > 0:
            bpy.context.view_layer.objects.active = obj
            for index in range(len(object_materials)):
                if object_materials[index] is not None:
                    object_materials[index].name = "{}.{:02}.000".format(
                        obj.name, (index + 1))

    # handling active object
    bpy.context.view_layer.objects.active = user_active
    if is_user_in_edit_mode:
        bpy.ops.object.mode_set(mode='EDIT')

    return {'FINISHED'}


def gltf_fix_colorspace():
    """ Set albedo & emit as sRGB colorspace, non-color if not
    """
    # var init
    selected_only = bpy.context.scene.retico_material_check_only_selected
    objects_selected = selection_sets.meshes_with_materials(selected_only)

    # function core
    for obj in objects_selected:
        mesh = obj.data
        for mat in mesh.materials:
            if mat.use_nodes:
                for node in mat.node_tree.nodes:
                    if node.type != 'TEX_IMAGE' or not node.image:
                        # node have to pass first tests
                        continue
                    for out in node.outputs:
                        if out.type != 'RGBA':
                            # output have to pass test
                            continue
                        for link in out.links:
                            # only albedo and emit are sRGB
                            if (link.to_node.type == 'BSDF_PRINCIPLED' and
                                    link.to_socket.name == 'Base Color') or \
                                    link.to_node.type == 'EMISSION':
                                node.image.colorspace_settings.name = 'sRGB'
                            else:
                                node.image.colorspace_settings.name = 'Non-Color'

    return {'FINISHED'}


def gltf_fix_uvnode_naming(operator):
    """ Help to relink correct UV name in nodes
    """
    # var init
    selected_only = bpy.context.scene.retico_material_check_only_selected
    objects_selected = selection_sets.meshes_with_materials(selected_only)
    materials_error = ""
    naming_issue = False

    # function core
    for obj in objects_selected:
        mesh = obj.data
        for mat in mesh.materials:
            if mat.use_nodes:
                naming_issue = False
                for node in mat.node_tree.nodes:
                    # node have to be an UVMAP or NORMAL_MAP type
                    if node.type == 'UVMAP' or node.type == 'NORMAL_MAP':
                        is_uv_chan_exists = False
                        uv_layers_number = len(mesh.uv_layers)

                        # no uv on mesh, skipping
                        if uv_layers_number == 0:
                            naming_issue = True
                            continue

                        # if no uvmap is set, assigning uv1
                        if not node.uv_map and uv_layers_number > 0:
                            node.uv_map = mesh.uv_layers[0].name
                            continue

                        # if node is using existing mesh chan, no pb, skipping
                        for uvchan in mesh.uv_layers:
                            if node.uv_map in uvchan.name:
                                is_uv_chan_exists = True
                        if is_uv_chan_exists:
                            continue

                        # blender default naming
                        if "UVMap." in node.uv_map:
                            # "UVMap.001" give us "1" as int
                            try:
                                channel_number = int(
                                    str(node.uv_map).split("UVMap.")[1])
                                node.uv_map = mesh.uv_layers[channel_number].name
                            except:
                                naming_issue = True
                        # gltf naming
                        elif "TEXCOORD_" in node.uv_map:
                            # "TEXCOORD_0" give us "0" as int
                            try:
                                channel_number = int(
                                    str(node.uv_map).split("TEXCOORD_")[1])
                                node.uv_map = mesh.uv_layers[channel_number].name
                            except:
                                naming_issue = True
                        # random naming, can't guess
                        else:
                            naming_issue = True

                if naming_issue:
                    materials_error += "{} ({}), ".format(mat.name, obj.name)

    if materials_error != "":
        # removing ", " charz
        operator.report(
            {'WARNING'}, "Some node UV links can't be fixed, check: {}".format(materials_error[:-2]))

    return {'FINISHED'}


def gltf_mute_textures(exclude="albedo"):
    """ Help for texture baking operations by disabling some material infos
    """
    # var ini
    selected_only = bpy.context.scene.retico_material_check_only_selected
    # no_muting_condition = [node.type, node.outputs.type, node.outputs.links.to_node.type], default: albedo
    no_muting_condition = ['TEX_IMAGE', 'RGBA', 'BSDF_PRINCIPLED']
    if exclude == "orm":
        no_muting_condition = ['TEX_IMAGE', 'RGBA', 'SEPRGB']
    elif exclude == "normal":
        no_muting_condition = ['TEX_IMAGE', 'RGBA', 'NORMAL_MAP']
    elif exclude == "emit":
        no_muting_condition = ['TEX_IMAGE', 'RGBA', 'EMISSION']
    objects_selected = selection_sets.meshes_with_materials(selected_only)

    # function core
    for obj in objects_selected:
        mesh = obj.data
        for mat in mesh.materials:
            if mat.use_nodes:
                for node in mat.node_tree.nodes:
                    emit_nodes = False
                    if node.type == 'EMISSION':
                        emit_nodes = True
                    if node.type == 'ADD_SHADER' and node.inputs:
                        for inp in node.inputs:
                            if emit_nodes:
                                # no need to go further if True
                                continue
                            if inp.links:
                                for link in inp.links:
                                    if link.from_node.type == 'EMISSION':
                                        emit_nodes = True
                                        continue
                    if node.type != no_muting_condition[0] and not emit_nodes:
                        # node have to pass first tests
                        continue
                    if exclude == "unmute":
                        # in case we jsut want unmuting, no need to go further
                        node.mute = False
                        continue
                    # muting by default, then unmute exception
                    node.mute = True
                    if node.type == 'ADD_SHADER':
                        # emit exception when muting all
                        node.mute = False
                    if exclude != "mute":
                        for out in node.outputs:
                            if out.type != no_muting_condition[1] and not emit_nodes:
                                # output have to pass test
                                continue
                            if emit_nodes and exclude == "emit":
                                if node.type == 'ADD_SHADER':
                                    node.mute = True
                                    continue
                                elif node.type == 'EMISSION':
                                    node.mute = False
                                    continue
                            else:
                                if node.type == 'ADD_SHADER':
                                    node.mute = False
                                    continue
                                elif node.type == 'EMISSION':
                                    node.mute = True
                                    continue
                                for link in out.links:
                                    if link.to_node.type != no_muting_condition[2]:
                                        # link have to pass test
                                        continue
                                    # ok we're sure about this node, let's unmute
                                    node.mute = False

    return {'FINISHED'}


def report_no_materials():
    """ Report mesh objects without materials
    """
    # var init
    objects_without_mtl = []
    objects_without_mtl_name = ""
    message_without_mtl = ""
    objects_index_without_mtl = []
    objects_index_without_mtl_name = ""
    message_index = ""
    is_all_good = False
    update_selection = bpy.context.scene.retico_material_reports_update_selection
    selected_only = bpy.context.scene.retico_material_check_only_selected
    objects_selected = selection_sets.meshes_in_selection(
    ) if selected_only else selection_sets.meshes_selectable()

    # function core
    for obj in objects_selected:
        # no materials at all
        if not obj.data.materials:
            objects_without_mtl.append(obj)
        # if index but without mat
        else:
            object_materials = obj.data.materials
            for index in range(len(object_materials)):
                if object_materials[index] is None:
                    objects_index_without_mtl.append([obj, index])
                    objects_without_mtl.append(obj)

    if len(objects_without_mtl) == 0 and len(objects_index_without_mtl) == 0:
        is_all_good = True
    else:
        # no need to check if alright
        if len(objects_without_mtl) > 0:
            for obj in objects_without_mtl:
                objects_without_mtl_name += "{}, ".format(obj.name)
            message_without_mtl = "No materials on: {}".format(
                objects_without_mtl_name[:-2])  # removing last ", " charz
            if update_selection:
                for obj in bpy.context.selected_objects:
                    obj.select_set(False)
                for obj in objects_without_mtl:
                    obj.select_set(True)
                bpy.context.view_layer.objects.active = objects_without_mtl[0]
        # no need to check if alright
        if len(objects_index_without_mtl) > 0:
            for reports in objects_index_without_mtl:
                objects_index_without_mtl_name += "{} (id {}), ".format(
                    reports[0].name, (reports[1] + 1))
            message_index = "Empty material indexes on: {}".format(
                objects_index_without_mtl_name[:-2])  # removing last ", " charz

    return message_without_mtl, message_index, is_all_good


def report_several_materials():
    """ Report mesh objects with more than 1 material
    """
    # var init
    objects_several_mtl = []
    objects_several_mtl_name = ""
    message_several_mtl = ""
    is_all_good = False
    update_selection = bpy.context.scene.retico_material_reports_update_selection
    selected_only = bpy.context.scene.retico_material_check_only_selected
    objects_selected = selection_sets.meshes_in_selection(
    ) if selected_only else selection_sets.meshes_selectable()

    # function core
    for obj in objects_selected:
        # no materials at all, don't care
        if not obj.data.materials:
            continue
        elif len(obj.data.materials) > 1:
            objects_several_mtl_name += "{}, ".format(obj.name)
            if update_selection:
                objects_several_mtl.append(obj)

    if len(objects_several_mtl_name) == 0:
        is_all_good = True
    else:
        message_several_mtl = "Multi materials on: {}".format(
            objects_several_mtl_name[:-2])  # removing last ", " charz
        if update_selection:
            for obj in bpy.context.selected_objects:
                obj.select_set(False)
            for obj in objects_several_mtl:
                obj.select_set(True)
            bpy.context.view_layer.objects.active = objects_several_mtl[0]

    return message_several_mtl, is_all_good


def report_several_users():
    """ Report shared materials
    """
    # var init
    objects_several_users = []
    objects_several_users_name = ""
    message_several_users = ""
    is_all_good = False
    update_selection = bpy.context.scene.retico_material_reports_update_selection
    selected_only = bpy.context.scene.retico_material_check_only_selected
    objects_selected = selection_sets.meshes_in_selection(
    ) if selected_only else selection_sets.meshes_selectable()

    # function core
    for obj in objects_selected:
        # no materials at all, don't care
        if not obj.data.materials:
            continue
        else:
            for mat in obj.data.materials:
                if mat and mat.users > 1:
                    objects_several_users_name += "{}, ".format(obj.name)
                    if update_selection:
                        objects_several_users.append(obj)
                    continue

    if len(objects_several_users_name) == 0:
        is_all_good = True
    else:
        message_several_users = "Shared materials on: {}".format(
            objects_several_users_name[:-2])  # removing last ", " charz
        if update_selection:
            for obj in bpy.context.selected_objects:
                obj.select_set(False)
            for obj in objects_several_users:
                obj.select_set(True)
            bpy.context.view_layer.objects.active = objects_several_users[0]

    return message_several_users, is_all_good


class RETICO_PT_material_panel(bpy.types.Panel):
    bl_idname = "RETICO_PT_material_panel"
    bl_label = "Materials"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "ReTiCo"

    def draw(self, context):
        layout = self.layout

        box = layout.box()
        row = box.row()
        row.prop(context.scene, "retico_material_check_only_selected",
                 text="only selected")

        # misc
        box = layout.box()
        row = box.row(align=True)

        # backface culling
        row.label(text="BackFace:")
        row.operator("retico.material_backface", text="On").toogle = True
        row.operator("retico.material_backface", text="Off").toogle = False

        # transfer name
        row = box.row(align=True)
        row.operator("retico.material_transfer_names", text="Name from Object")

        # active texture node
        subbox = box.box()
        row = subbox.row(align=True)
        row.label(text="Active texture node:")
        row = subbox.row()
        row.prop(context.scene, "retico_material_activeTex_viewShading_solid",
                 text="set viewport shading")
        grid = subbox.grid_flow(
            row_major=True, even_columns=True, even_rows=True, align=True)
        row = grid.row(align=True)
        row.operator("retico.material_active_texture",
                     text="Albedo").texture_type = "albedo"
        row = grid.row(align=True)
        row.operator("retico.material_active_texture",
                     text="ORM").texture_type = "orm"
        row = grid.row(align=True)
        row.operator("retico.material_active_texture",
                     text="Normal").texture_type = "normal"
        row = grid.row(align=True)
        row.operator("retico.material_active_texture",
                     text="Emissive").texture_type = "emit"

        # glTF workflow
        box = layout.box()
        row = box.row()
        row.label(text="glTF workflow:")

        # muting textures
        subbox = box.box()
        row = subbox.row()
        row.label(text="Mute textures except:")
        grid = subbox.grid_flow(
            row_major=True, even_columns=True, even_rows=True, align=True)
        row = grid.row(align=True)
        row.operator("retico.material_gltf_mute",
                     text="Albedo").exclude = "albedo"
        row = grid.row(align=True)
        row.operator("retico.material_gltf_mute",
                     text="ORM").exclude = "orm"
        row = grid.row(align=True)
        row.operator("retico.material_gltf_mute",
                     text="Normal").exclude = "normal"
        row = grid.row(align=True)
        row.operator("retico.material_gltf_mute",
                     text="Emissive").exclude = "emit"
        grid = subbox.grid_flow(
            row_major=True, even_columns=True, even_rows=True, align=True)
        row = grid.row(align=True)
        row.operator("retico.material_gltf_mute",
                     text="Mute all").exclude = "mute"
        row = grid.row(align=True)
        row.operator("retico.material_gltf_mute",
                     text="Unmute all").exclude = "unmute"

        # fixing
        subbox = box.box()
        row = subbox.row()
        row.label(text="Fix:")
        grid = subbox.grid_flow(
            row_major=True, columns=2, even_columns=True, even_rows=True, align=True)

        # colorspace
        row = grid.row(align=True)
        row.operator("retico.material_gltf_colorspace", text="Colorspace")

        # uv nodes
        row = grid.row(align=True)
        row.operator("retico.material_gltf_uvnode_naming", text="UV links")

        # report
        box = layout.box()
        row = box.row()
        row.label(text="Report:")
        row = box.row()
        row.prop(context.scene, "retico_material_reports_update_selection",
                 text="update selection")
        row.prop(context.scene, "retico_material_reports_to_clipboard",
                 text="to clipboard")
        grid = box.grid_flow(
            row_major=True, columns=2, even_columns=True, even_rows=True, align=True)
        row = grid.row(align=True)
        row.operator("retico.material_report_none", text="no Mat")
        row = grid.row(align=True)
        row.operator("retico.material_report_several", text="1+ Mat")
        row = grid.row(align=True)
        row.operator("retico.material_report_users", text="Shared")


class RETICO_OT_material_backface(bpy.types.Operator):
    bl_idname = "retico.material_backface"
    bl_label = "Turn backFaceCulling on/off"
    bl_description = "Turn backFaceCulling on/off"
    toogle: BoolProperty()

    def execute(self, context):
        set_backface_culling(self.toogle)
        return {'FINISHED'}


class RETICO_OT_material_transfer_names(bpy.types.Operator):
    bl_idname = "retico.material_transfer_names"
    bl_label = "Copy Object name to its material name"
    bl_description = "Copy Object name to its material name"

    @classmethod
    def poll(cls, context):
        return len(context.view_layer.objects) > 0

    def execute(self, context):
        transfer_names()
        return {'FINISHED'}


class RETICO_OT_material_gltf_mute(bpy.types.Operator):
    bl_idname = "retico.material_gltf_mute"
    bl_label = "Mute textures for baking process"
    bl_description = "Mute textures for baking process"
    exclude: StringProperty()

    def execute(self, context):
        gltf_mute_textures(self.exclude)
        return {'FINISHED'}


class RETICO_OT_material_gltf_colorspace(bpy.types.Operator):
    bl_idname = "retico.material_gltf_colorspace"
    bl_label = "Fix gltf textures colorspace"
    bl_description = "Fix gltf textures colorspace"

    def execute(self, context):
        gltf_fix_colorspace()
        return {'FINISHED'}


class RETICO_OT_material_gltf_uvnode_naming(bpy.types.Operator):
    bl_idname = "retico.material_gltf_uvnode_naming"
    bl_label = "Relink TEXCOORD_x naming to actual mesh uv names"
    bl_description = "Relink TEXCOORD_x naming to actual mesh uv names"

    def execute(self, context):
        gltf_fix_uvnode_naming(self)
        return {'FINISHED'}


class RETICO_OT_material_active_texture(bpy.types.Operator):
    bl_idname = "retico.material_active_texture"
    bl_label = "Activate a texture to be shown in viewport Solid Texture mode"
    bl_description = "Activate a texture to be shown in viewport Solid Texture mode"
    texture_type: StringProperty()

    def execute(self, context):
        set_active_texture(self.texture_type)
        return {'FINISHED'}


class RETICO_OT_material_report_none(bpy.types.Operator):
    bl_idname = "retico.material_report_none"
    bl_label = "Report object without materials"
    bl_description = "Report object without materials, both in console and Info editor"

    @classmethod
    def poll(cls, context):
        return len(context.view_layer.objects) > 0

    def execute(self, context):
        message_without_mtl, message_index, is_all_good = report_no_materials()
        self.report({'INFO'}, "---[ Objects without materials ]---")
        if is_all_good:
            self.report({'INFO'}, "All meshes have materials")
        else:
            to_clipboard = context.scene.retico_material_reports_to_clipboard
            if len(message_without_mtl) > 0:
                if to_clipboard:
                    context.window_manager.clipboard = message_without_mtl
                self.report({'WARNING'}, message_without_mtl)
            if len(message_index) > 0:
                if to_clipboard:
                    context.window_manager.clipboard += "\r\n{}".format(
                        message_index)
                self.report({'WARNING'}, message_index)

        return {'FINISHED'}


class RETICO_OT_material_report_several(bpy.types.Operator):
    bl_idname = "retico.material_report_several"
    bl_label = "Report object with more than 1 material"
    bl_description = "Report object with more than 1 material, both in console and Info editor"

    @classmethod
    def poll(cls, context):
        return len(context.view_layer.objects) > 0

    def execute(self, context):
        message_several_mtl, is_all_good = report_several_materials()
        self.report({'INFO'}, "---[ Objects with multimaterials ]---")
        if is_all_good:
            self.report({'INFO'}, "No multi-material found")
        else:
            if len(message_several_mtl) > 0:
                if context.scene.retico_material_reports_to_clipboard:
                    context.window_manager.clipboard = message_several_mtl
                self.report({'WARNING'}, message_several_mtl)

        return {'FINISHED'}


class RETICO_OT_material_report_users(bpy.types.Operator):
    bl_idname = "retico.material_report_users"
    bl_label = "Report object sharing materials"
    bl_description = "Report object sharing materials, both in console and Info editor"

    @classmethod
    def poll(cls, context):
        return len(context.view_layer.objects) > 0

    def execute(self, context):
        message_several_users, is_all_good = report_several_users()
        self.report({'INFO'}, "---[ Objects sharing materials ]---")
        if is_all_good:
            self.report({'INFO'}, "No material shared")
        else:
            if len(message_several_users) > 0:
                if context.scene.retico_material_reports_to_clipboard:
                    context.window_manager.clipboard = message_several_users
                self.report({'WARNING'}, message_several_users)

        return {'FINISHED'}


classes = (
    RETICO_PT_material_panel,
    RETICO_OT_material_backface,
    RETICO_OT_material_transfer_names,
    RETICO_OT_material_gltf_mute,
    RETICO_OT_material_active_texture,
    RETICO_OT_material_gltf_colorspace,
    RETICO_OT_material_gltf_uvnode_naming,
    RETICO_OT_material_report_none,
    RETICO_OT_material_report_several,
    RETICO_OT_material_report_users,
)


def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
    Scene.retico_material_check_only_selected = BoolProperty(
        name="Material tab use selected only",
        description="Material operations applies on selection, or not",
        default=True
    )
    Scene.retico_material_reports_update_selection = BoolProperty(
        name="Report update selection",
        description="Reports applies on selection, or not",
        default=False
    )
    Scene.retico_material_reports_to_clipboard = BoolProperty(
        name="Reports sent to clipboard",
        description="Reports sent to clipboard",
        default=False
    )
    Scene.retico_material_activeTex_viewShading_solid = BoolProperty(
        name="Set 3DView shading to Solid -> Texture",
        description="Set 3DView shading to Solid -> Texture",
        default=True
    )


def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
    del Scene.retico_material_reports_update_selection
    del Scene.retico_material_reports_to_clipboard
    del Scene.retico_material_check_only_selected
    del Scene.retico_material_activeTex_viewShading_solid


if __name__ == "__main__":
    register()
