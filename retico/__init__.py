bl_info = {
    "name": "ReTiCo (RealTime Companion)",
    "description": "RealTime Companion, a 3D realtime workflow addon oriented.",
    "author": "Vincent (V!nc3r) Lamy",
    "category": "3D View",
    "wiki_url": 'https://github.com/Vinc3r/ReTiCo#ReTiCo',
    "tracker_url": 'https://github.com/Vinc3r/ReTiCo/issues',
    "version": (2019, 11, 17),
    "blender": (2, 80, 0)
}

"""A bunch of Thanks for some snippets, ideas, inspirations, to:
    - of course, Ton & all Blender devs,
    - Henri Hebeisen (henri-hebeisen.com), Pitiwazou (pitiwazou.com), Pistiwique (github.com/pistiwique),
    - and finally all Blender community and the ones I forget.
    - Cstfan for his feedbacks
"""

modulesNames = ['materials', 'meshes', 'selection_sets', 'uvs']

modulesFullNames = []
for currentModuleName in modulesNames:
    modulesFullNames.append('{}.{}'.format(__name__, currentModuleName))

import bpy
import sys
import importlib

for currentModuleFullName in modulesFullNames:
    if currentModuleFullName in sys.modules:
        importlib.reload(sys.modules[currentModuleFullName])
    else:
        globals()[currentModuleFullName] = importlib.import_module(
            currentModuleFullName)
        setattr(globals()[currentModuleFullName],
                'modulesNames', modulesFullNames)


def register():
    for currentModuleName in modulesFullNames:
        if currentModuleName in sys.modules:
            if hasattr(sys.modules[currentModuleName], 'register'):
                sys.modules[currentModuleName].register()


def unregister():
    for currentModuleName in modulesFullNames:
        if currentModuleName in sys.modules:
            if hasattr(sys.modules[currentModuleName], 'unregister'):
                sys.modules[currentModuleName].unregister()


if __name__ == "__main__":
    register()
