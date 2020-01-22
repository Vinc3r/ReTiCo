import bpy

baseName = "myWonderfullName" #set your name here

""" This script will rename all selected objects and give you this kind of result:
        - myWonderfullName.000
        - myWonderfullName.001
        - myWonderfullName.002
        ...
"""

number = 0

for obj in [o for o in bpy.context.selected_objects if o.type == 'MESH']:
    if number < 10:
        obj.name = "{}.00{}".format(baseName, number)
    elif number < 100:
        obj.name = "{}.0{}".format(baseName, number)
    else:
        obj.name = "{}.{}".format(baseName, number)
    number += 1
    
