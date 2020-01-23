import bpy


def meshes_in_selection():
    """ Return selected mesh objects
    """
    return [o for o in bpy.context.selected_objects if o.type == 'MESH']


def meshes_selectable():
    """ Return all mesh objects
    """
    return [o for o in bpy.context.selectable_objects if o.type == 'MESH']


def meshes_without_uv(selected_only=True):
    """ Return meshs without UV1 or UV2
    """
    # var init
    objects_selected = meshes_in_selection() if selected_only else meshes_selectable()
    objects_without_uv = []
    objects_without_uv2 = []

    # function core
    for obj in objects_selected:
        mesh = obj.data
        if len(mesh.uv_layers) > 2:
            # have more than 2 uv
            continue
        if len(mesh.uv_layers) == 0:
            # no uv at all
            objects_without_uv.append(obj)
            objects_without_uv2.append(obj)
            continue
        if len(mesh.uv_layers) == 1:
            # only one chan
            objects_without_uv2.append(obj)
            continue

    return objects_without_uv, objects_without_uv2


def meshes_with_materials(selected_only=True):
    """ Return mesh objects with material, in selection or not
    """
    # var init
    objects_selected = meshes_in_selection() if selected_only else meshes_selectable()
    objects_with_mtl = []

    # function core
    for obj in objects_selected:
        if len(obj.data.materials) == 0:
            continue
        objects_with_mtl.append(obj)

    return objects_with_mtl


def meshes_without_materials(selected_only=True):
    """ Return mesh objects without material, in selection or not
    """
    # var init
    objects_selected = meshes_in_selection() if selected_only else meshes_selectable()
    objects_without_mtl = []

    # function core
    for obj in objects_selected:
        if not obj.data.materials:
            objects_without_mtl.append(obj)

    return objects_without_mtl
