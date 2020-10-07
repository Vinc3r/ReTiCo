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

"""
**********************************************************************
*                            local variables                         *
**********************************************************************
"""

gltf_active_texnodes = {
    "albedo": True,
    "orm": True,
    "orm_chans": False,
    "orm_chans_R": True,
    "orm_chans_G": True,
    "orm_chans_B": True,
    "normal": True,
    "emit": True
}


"""
**********************************************************************
*                            def section                             *
**********************************************************************
"""


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


def set_blendmode():
    """ Set Blend mode to Alpha Blend if alpha is linked or set
    """
    # var init
    selected_only = bpy.context.scene.retico_material_check_only_selected
    objects_selected = selection_sets.meshes_with_materials(selected_only)

    # function core
    for obj in objects_selected:
        for mat in obj.data.materials:
            if mat is not None and mat.use_nodes:
                for node in mat.node_tree.nodes:
                    if node.type == 'BSDF_TRANSPARENT':
                        mat.blend_method = 'BLEND'
                        continue
                    if node.type == 'BSDF_PRINCIPLED':
                        for inp in node.inputs:
                            if inp.identifier != 'Alpha':
                                continue
                            if inp.default_value == 1.0 and not inp.is_linked:
                                mat.blend_method = 'OPAQUE'
                            if inp.default_value < 1 or inp.is_linked:
                                mat.blend_method = 'BLEND'

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
                            if (
                                (link.to_node.type == 'BSDF_PRINCIPLED'
                                    and link.to_socket.name == 'Base Color')
                                or link.to_node.type == 'EMISSION'
                            ):
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
    is_texnode_detected = False
    objects_selected = selection_sets.meshes_with_materials(selected_only)
    # function core
    for obj in objects_selected:
        mesh = obj.data
        for mat in mesh.materials:
            if mat.use_nodes:
                for node in mat.node_tree.nodes:

                    if node.type == 'OUTPUT_MATERIAL' or node.type == 'ADD_SHADER':
                        # skip if not concern
                        continue

                    if exclude == "unmute":
                        # in case we just want to unmute, no need to go further
                        node.mute = False
                        for textype in gltf_active_texnodes:
                            if textype != "orm_chans":
                                gltf_active_texnodes[textype] = True
                            else:
                                gltf_active_texnodes[textype] = False
                        continue

                    if exclude == "mute" and node.type.find("BSDF") == -1:
                        # even when muting, we still want our basic nodes (BSDF) to be active
                        node.mute = True
                        for textype in gltf_active_texnodes:
                            gltf_active_texnodes[textype] = False
                        continue

                    for out in node.outputs:
                        if (
                            node.type == 'TEX_IMAGE'
                            or node.type == 'NORMAL_MAP'
                            or node.type == 'EMISSION'
                            or node.type == 'SEPRGB'
                        ):

                            if (
                                len(out.links) > 0
                                and (
                                    # albedo nodes
                                    (
                                        exclude == "albedo"
                                        and out.links[0].to_node.type == 'BSDF_PRINCIPLED'
                                        and out.links[0].to_socket.name == 'Base Color'
                                    )
                                    # normal nodes
                                    or (
                                        exclude == "normal"
                                        and (
                                            (
                                                # texnode linked to normal map node
                                                out.links[0].to_node.type == 'NORMAL_MAP'
                                                # texnode linked to principled
                                                or (
                                                    out.links[0].to_node.type == 'BSDF_PRINCIPLED'
                                                    and out.links[0].to_socket.name == 'Normal'
                                                )
                                            )
                                            # normal map node
                                            or node.type == 'NORMAL_MAP'
                                        )
                                    )
                                    # emissive nodes
                                    or (
                                        exclude == "emit"
                                        and (
                                            out.links[0].to_node.type == 'EMISSION'
                                            or node.type == 'EMISSION'
                                        )
                                    )
                                    # orm nodes
                                    or (
                                        exclude == "orm"
                                        and (
                                            node.type == 'SEPRGB'
                                            or out.links[0].to_node.type == 'SEPRGB'
                                        )
                                    )
                                )
                            ):
                                # for ORM, we need to reset some settings
                                if exclude == "orm":
                                    chan_target = ["R", "G", "B"]
                                    for chan in chan_target:
                                        input = mat.node_tree.nodes['Principled BSDF'].inputs['Roughness']
                                        # occlusion specific
                                        if chan == "R":
                                            gltfSettings = [node for node in mat.node_tree.nodes if (
                                                node.type == 'GROUP'
                                                and node.node_tree.original == bpy.data.node_groups['glTF Settings']
                                            )]
                                            if len(gltfSettings) > 0:
                                                gltfSettings = gltfSettings[0]
                                                input = gltfSettings.inputs['Occlusion']
                                        # metallic
                                        elif chan == "B":
                                            input = mat.node_tree.nodes['Principled BSDF'].inputs['Metallic']

                                        sepRGB = [
                                            node for node in mat.node_tree.nodes if node.type == 'SEPRGB'][0]
                                        output = sepRGB.outputs[chan]
                                        if not sepRGB.outputs[chan].is_linked:
                                            mat.node_tree.links.new(
                                                input, output, verify_limits=True)

                                    gltf_active_texnodes["orm_chans"] = False
                                    gltf_active_texnodes["orm_chans_R"] = True
                                    gltf_active_texnodes["orm_chans_G"] = True
                                    gltf_active_texnodes["orm_chans_B"] = True

                                node.mute = gltf_active_texnodes[exclude]
                                is_texnode_detected = True

                            elif (
                                exclude.find("orm_chans_") != -1
                                and node.type == 'SEPRGB'
                            ):

                                gltf_active_texnodes["orm"] = False

                                # occlusion (R) roughness (G) metallic (B)
                                chan_name = exclude.split("orm_chans_")[1]
                                # occlusion is handled in a different way
                                chan_target = (
                                    "Roughness" if chan_name == "G" else "Metallic")

                                # unlink
                                if (
                                    gltf_active_texnodes["orm_chans_{}".format(
                                        chan_name)]
                                    and len(node.outputs[chan_name].links) > 0
                                ):
                                    link = node.outputs[chan_name].links[0]
                                    mat.node_tree.links.remove(link)
                                # link
                                else:
                                    input = mat.node_tree.nodes['Principled BSDF'].inputs[chan_target]
                                    # occlusion specific
                                    if chan_name == "R":
                                        gltfSettings = [node for node in mat.node_tree.nodes if (
                                            node.type == 'GROUP'
                                            and node.node_tree.original == bpy.data.node_groups['glTF Settings']
                                        )]
                                        if len(gltfSettings) > 0:
                                            gltfSettings = gltfSettings[0]
                                            input = gltfSettings.inputs['Occlusion']
                                            output = node.outputs[chan_name]
                                            mat.node_tree.links.new(
                                                input, output, verify_limits=True)
                                    else:
                                        output = node.outputs[chan_name]
                                        mat.node_tree.links.new(
                                            input, output, verify_limits=True)

                                is_texnode_detected = True

    if is_texnode_detected:
        gltf_active_texnodes[exclude] = not gltf_active_texnodes[exclude]
        is_texnode_detected = False

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


"""
**********************************************************************
*                        Panel class section                         *
**********************************************************************
"""


class RETICO_PT_material_3dviewPanel(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "ReTiCo"


class RETICO_PT_material(RETICO_PT_material_3dviewPanel):
    bl_idname = "RETICO_PT_material"
    bl_label = "Materials"

    def draw(self, context):
        layout = self.layout

        box = layout.box()
        row = box.row()
        row.prop(context.scene, "retico_material_check_only_selected",
                 text="only on selection")


class RETICO_PT_material_misc(RETICO_PT_material_3dviewPanel):
    bl_parent_id = "RETICO_PT_material"
    bl_idname = "RETICO_PT_material_misc"
    bl_label = "Misc"

    def draw(self, context):
        layout = self.layout

        if (
            not bpy.context.scene.retico_material_check_only_selected
            or (
                bpy.context.scene.retico_material_check_only_selected
                and len(bpy.context.selected_objects) > 0
            )
        ):

            # backface culling
            row = layout.row(align=True)
            row.label(text="BackFace:")
            row.operator("retico.material_backface", text="On").toogle = True
            row.operator("retico.material_backface", text="Off").toogle = False

            # blend mode
            row = layout.row(align=True)
            row.operator("retico.material_blendmode", text="Detect Blend Mode")

            # transfer name
            row = layout.row(align=True)
            row.operator("retico.material_transfer_names",
                         text="Name from Object")
        else:
            row = layout.row(align=True)
            row.label(text="No object in selection.")


class RETICO_PT_material_texnode(RETICO_PT_material_3dviewPanel):
    bl_parent_id = "RETICO_PT_material"
    bl_idname = "RETICO_PT_material_texnode"
    bl_label = "Active texture"

    def draw(self, context):
        layout = self.layout

        if (
            not bpy.context.scene.retico_material_check_only_selected
            or (
                bpy.context.scene.retico_material_check_only_selected
                and len(bpy.context.selected_objects) > 0
            )
        ):
            box = layout.box()
            row = box.row(align=True)
            row.prop(context.scene, "retico_material_activeTex_viewShading_solid",
                     text="set viewport shading")
            grid = layout.grid_flow(
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
        else:
            row = layout.row(align=True)
            row.label(text="No object in selection.")


class RETICO_PT_material_gltf(RETICO_PT_material_3dviewPanel):
    bl_parent_id = "RETICO_PT_material"
    bl_idname = "RETICO_PT_material_gltf"
    bl_label = "glTF workflow"

    def draw(self, context):
        layout = self.layout

        if (
            not bpy.context.scene.retico_material_check_only_selected
            or (
                bpy.context.scene.retico_material_check_only_selected
                and len(bpy.context.selected_objects) > 0
            )
        ):

            # muting textures
            row = layout.row()
            row.label(text="Active textures nodes:")
            grid = layout.grid_flow(
                row_major=True, columns=2, even_columns=True, even_rows=True, align=True)
            row = grid.row(align=True)
            row.operator("retico.material_gltf_mute",
                         text="Albedo", depress=gltf_active_texnodes["albedo"]).exclude = "albedo"
            row = grid.row(align=True)
            row.operator("retico.material_gltf_mute",
                         text="Normal", depress=gltf_active_texnodes["normal"]).exclude = "normal"
            row = grid.row(align=True)
            row.operator("retico.material_gltf_mute",
                         text="ORM", depress=gltf_active_texnodes["orm"]).exclude = "orm"
            row = grid.row(align=True)
            row.operator("retico.material_gltf_mute",
                         text="Emissive", depress=gltf_active_texnodes["emit"]).exclude = "emit"
            # ORM channels are not asked
            if gltf_active_texnodes["orm_chans"] == False:
                row = grid.row(align=True)
                row.operator("retico.material_gltf_mute",
                             icon='TRIA_RIGHT', text="ORM chans", depress=gltf_active_texnodes["orm_chans"]).exclude = "orm_chans"
            # ORM channels are asked
            else:
                row = grid.row(align=True)
                row.operator("retico.material_gltf_mute",
                             icon='TRIA_DOWN', text="ORM chans", depress=gltf_active_texnodes["orm_chans"]).exclude = "orm_chans"
                # empty operator needed to return to line
                row = grid.row(align=True)
                row.operator("retico.material_gltf_mute",
                             text="", emboss=False).exclude = ""
                # occlusion
                row = grid.row(align=True)
                row.operator("retico.material_gltf_mute",
                             text="Occlusion (R)", depress=gltf_active_texnodes["orm_chans_R"]).exclude = "orm_chans_R"
                # empty operator needed to return to line
                row = grid.row(align=True)
                row.operator("retico.material_gltf_mute",
                             text="", emboss=False).exclude = ""
                # roughness
                row = grid.row(align=True)
                row.operator("retico.material_gltf_mute",
                             text="Roughness (G)", depress=gltf_active_texnodes["orm_chans_G"]).exclude = "orm_chans_G"
                # empty operator needed to return to line
                row = grid.row(align=True)
                row.operator("retico.material_gltf_mute",
                             text="", emboss=False).exclude = ""
                # metallic
                row = grid.row(align=True)
                row.operator("retico.material_gltf_mute",
                             text="Metallic (B)", depress=gltf_active_texnodes["orm_chans_B"]).exclude = "orm_chans_B"
            # global mute/unmute
            grid = layout.grid_flow(
                row_major=True, even_columns=True, even_rows=True, align=True)
            row = grid.row(align=True)
            row.operator("retico.material_gltf_mute",
                         text="Mute all").exclude = "mute"
            row = grid.row(align=True)
            row.operator("retico.material_gltf_mute",
                         text="Unmute all").exclude = "unmute"
        else:
            row = layout.row(align=True)
            row.label(text="No object in selection.")


class RETICO_PT_material_fix(RETICO_PT_material_3dviewPanel):
    bl_parent_id = "RETICO_PT_material"
    bl_idname = "RETICO_PT_material_fix"
    bl_label = "Fix"

    def draw(self, context):
        layout = self.layout

        if (
            not bpy.context.scene.retico_material_check_only_selected
            or (
                bpy.context.scene.retico_material_check_only_selected
                and len(bpy.context.selected_objects) > 0
            )
        ):
            grid = layout.grid_flow(
                row_major=True, columns=2, even_columns=True, even_rows=True, align=True)

            # colorspace
            row = grid.row(align=True)
            row.operator("retico.material_gltf_colorspace", text="Colorspace")

            # uv nodes
            row = grid.row(align=True)
            row.operator("retico.material_gltf_uvnode_naming", text="UV links")
        else:
            row = layout.row(align=True)
            row.label(text="No object in selection.")


class RETICO_PT_material_report(RETICO_PT_material_3dviewPanel):
    bl_parent_id = "RETICO_PT_material"
    bl_idname = "RETICO_PT_material_report"
    bl_label = "Report"

    def draw(self, context):
        layout = self.layout

        if (
            not bpy.context.scene.retico_material_check_only_selected
            or (
                bpy.context.scene.retico_material_check_only_selected
                and len(bpy.context.selected_objects) > 0
            )
        ):

            row = layout.row()
            row.prop(context.scene, "retico_material_reports_update_selection",
                     text="update selection")
            row.prop(context.scene, "retico_material_reports_to_clipboard",
                     text="to clipboard")
            grid = layout.grid_flow(
                row_major=True, columns=2, even_columns=True, even_rows=True, align=True)
            row = grid.row(align=True)
            row.operator("retico.material_report_none", text="no Mat")
            row = grid.row(align=True)
            row.operator("retico.material_report_several", text="1+ Mat")
            row = grid.row(align=True)
            row.operator("retico.material_report_users", text="Shared")
        else:
            row = layout.row(align=True)
            row.label(text="No object in selection.")


"""
**********************************************************************
*                     Operator class section                         *
**********************************************************************
"""


class RETICO_OT_material_backface(bpy.types.Operator):
    bl_idname = "retico.material_backface"
    bl_label = "Turn backFaceCulling on/off"
    bl_description = "Turn backFaceCulling on/off"
    toogle: BoolProperty()

    def execute(self, context):
        set_backface_culling(self.toogle)
        return {'FINISHED'}


class RETICO_OT_material_blendmode(bpy.types.Operator):
    bl_idname = "retico.material_blendmode"
    bl_label = "Set Blend mode according to alpha values"
    bl_description = "Set Blend mode according to alpha values"

    def execute(self, context):
        set_blendmode()
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
        if self.exclude == "orm_chans":
            gltf_active_texnodes["orm_chans"] = not gltf_active_texnodes["orm_chans"]
        if self.exclude != "":
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
            message_to_clipboard = ""
            if len(message_without_mtl) > 0:
                if to_clipboard:
                    message_to_clipboard = message_without_mtl
                self.report({'WARNING'}, message_without_mtl)
            if len(message_index) > 0:
                if to_clipboard:
                    message_to_clipboard += ("\r\n{}" + message_index)
                self.report({'WARNING'}, message_index)
            if to_clipboard:
                context.window_manager.clipboard = message_to_clipboard

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


"""
**********************************************************************
* Registration                                                       *
**********************************************************************
"""

classes = (
    RETICO_PT_material,
    RETICO_PT_material_misc,
    RETICO_PT_material_texnode,
    RETICO_PT_material_gltf,
    RETICO_PT_material_fix,
    RETICO_PT_material_report,
    RETICO_OT_material_backface,
    RETICO_OT_material_blendmode,
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
        name="Set 3DView shading to Solid: Texture",
        description="Set 3DView shading to Solid: Texture",
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
