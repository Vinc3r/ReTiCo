import bpy
import bmesh
print("+++++++++++++++++")
"""
    thanks to glTF developpers https://github.com/KhronosGroup/glTF-Blender-IO/blob/master/addons/io_scene_gltf2/blender/exp/gltf2_blender_gather_nodes.py#L268
"""
for obj in bpy.context.view_layer.objects:

    edge_split = obj.modifiers.new('Temporary_Auto_Smooth', 'EDGE_SPLIT')
    edge_split.split_angle = obj.data.auto_smooth_angle
    edge_split.use_edge_angle = not obj.data.has_custom_normals
    obj.data.use_auto_smooth = True
    bpy.context.view_layer.update()

    depsgraph = bpy.context.evaluated_depsgraph_get()
    blender_mesh_owner = obj.evaluated_get(depsgraph)
    blender_mesh = blender_mesh_owner.to_mesh(
        preserve_all_data_layers=True, depsgraph=depsgraph)

    bm = bmesh.new()
    bm.from_mesh(blender_mesh)
    bm.faces.ensure_lookup_table()
    has_ngon = False
    area = 0

    for face in bm.faces:
        area += face.calc_area()
        if len(face.edges) > 4:
            has_ngon = True
    verts = len(bm.verts)
    tri = len(bm.calc_loop_triangles())
    faces = len(bm.faces)
    area = round(area, 1)
    polycount = [verts, tri, faces, has_ngon, area]

    obj.modifiers.remove(edge_split)

    print(obj.name)
    print("  verts: {}".format(polycount[0]))
    print("  tri: {}".format(polycount[1]))
    print("  faces: {}".format(polycount[2]))
    print("  ngon: {}".format(polycount[3]))
    print("  area: {}".format(polycount[4]))
    bm.free()
