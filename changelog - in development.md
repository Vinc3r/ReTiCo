# Dev changelog

Current changes in [source folder](https://github.com/Vinc3r/BlenderScripts/tree/master/nothing-is-3d).

- versionning now use date (more convenient)
- object names can be put in OS clipboard
- orm, normal & emit textures nodes can now be activated as well as albedo (useful when in viewport shading solid-texture)
- ability to names material using object names and material id with *objName*.*id*.000 pattern
- report objects without materials and/or object with empty material indexes
- create an uv chan when using "Activate" button when it doesn't exists
- create an uv1 chan when using "Box mapping" button when it doesn't exists  
- fixed: emissive texture node no longer set as linear but sRGB
- fixed: Box mapping in Edit mode only applied on selected faces
