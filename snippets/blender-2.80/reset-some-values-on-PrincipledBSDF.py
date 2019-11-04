import bpy

for mat in bpy.data.materials:
    if mat.use_nodes:
        for node in mat.node_tree.nodes:
            if node.type == 'BSDF_PRINCIPLED':
                node.inputs['Roughness'].default_value = 1
                node.inputs['Specular'].default_value = 0
                node.inputs['Metallic'].default_value = 0
                if len(node.inputs['Roughness'].links) > 0:
                    for link in node.inputs['Roughness'].links:
                        mat.node_tree.links.remove(link)
                if len(node.inputs['Specular'].links) > 0:
                    for link in node.inputs['Specular'].links:
                        mat.node_tree.links.remove(link)
                if len(node.inputs['Metallic'].links) > 0:
                    for link in node.inputs['Metallic'].links:
                        mat.node_tree.links.remove(link)