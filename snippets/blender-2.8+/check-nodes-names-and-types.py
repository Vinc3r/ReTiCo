import bpy

for obj in [o for o in bpy.context.selected_objects if o.type == 'MESH']:
    mesh = obj.data
    for mat in mesh.materials:
        if mat.use_nodes:
            for node in mat.node_tree.nodes:
                print("{} = {}".format(node.name, node.type))