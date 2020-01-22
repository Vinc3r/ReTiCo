import bpy

print("----------")

obj_using_instance = []
meshes_instanced = []

for obj in [o for o in bpy.context.selectable_objects if o.type == 'MESH']:
    mesh = obj.data
    already_exists = False
    mesh_used_id = 0
    
    # skipping non-instanced
    if mesh.users <= 1:
        continue

    # checking if instanced mesh already in list
    for mesh_inst_id in range(len(meshes_instanced)):
        if mesh == meshes_instanced[mesh_inst_id]:
            already_exists = True
            mesh_used_id = mesh_inst_id
            continue
    if not already_exists:
        meshes_instanced.append(mesh)
        mesh_inst_id = len(meshes_instanced) - 1
        
    obj_using_instance.append([obj, mesh_inst_id])

for mesh_inst_id in range(len(meshes_instanced)):
    obj_using_instance_list = []
    obj_using_instance_list_name = ""
    for obj_info in obj_using_instance:
        if obj_info[1] == mesh_inst_id:
            obj_using_instance_list.append(obj_info[0])
    for obj in obj_using_instance_list:
        obj_using_instance_list_name += "{}, ".format(obj.name)

    print("{} is used by: {}".format(meshes_instanced[mesh_inst_id].name, obj_using_instance_list_name)[:-2])
