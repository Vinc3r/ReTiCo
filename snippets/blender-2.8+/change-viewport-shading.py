import bpy

print("---------")

viewports = []

for area in bpy.context.screen.areas:
    if area.type != 'VIEW_3D':
        # https://docs.blender.org/api/current/bpy.types.Area.html#bpy.types.Area.type
        continue
    for space in area.spaces:
        if space.type != 'VIEW_3D':
            # https://docs.blender.org/api/current/bpy.types.Space.html#bpy.types.Space.type
            continue
        space.shading.type = 'SOLID' # https://docs.blender.org/api/current/bpy.types.View3DShading.html#bpy.types.View3DShading.type
        space.shading.color_type = 'TEXTURE' # https://docs.blender.org/api/current/bpy.types.View3DShading.html#bpy.types.View3DShading.color_type
        viewports.append(space)