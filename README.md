# ReTiCo

**Re**al**Ti**me**Co**mpanion, a Blender add-on made to work faster, oriented 3D realtime workflow.

[Changelog](https://github.com/Vinc3r/ReTiCo/blob/master/changelog.md).

![blender2.8-ui](_readmeAssets_/blender2.8-ui.png)

## Installation

1. download [last version](https://github.com/Vinc3r/BlenderScripts/releases/latest)
2. in Blender go to *File* > *User Preferences* > *Add-ons* Tab
3. remove previous installation if needed (search *retico* to easily find it)
4. install by using *Install from File...* in *Blender User Preferences* > *Add-ons* tab

ReTiCo tools are now available in `3DView` > `Sidebar` > `ReTiCo` tab.

## Features

This addon was made to help using a 3D realtime workflow, and so glTF export.

- <a href="#gltf">glTF</a> panel
- <a href="#materials">Materials</a> panel
- <a href="#meshes">Meshes</a> panel
- <a href="#uvs">UVs</a> panel

### [*glTF* panel](#gltf)

On selected objects:
  - mute texture node by type (useful when baking lighting)
  - help fixing some common potential issues

### [*Material* panel](#materials)

On selected objects:
  - allow backface culling on/off
  - set active texture node by type, useful for Look Dev viewport mode (albedo only for now)

### [*Meshes* panel](#meshes)

On selected objects:
  - copy Object name to Mesh name
  - mass-overwrite autosmooth

### [*UVs* panel](#uvs)

On selected objects:
  - make active first or second UV channel
  - do a box mapping but using MagicUV algorithm (better than the default one)
  - rename channels using this pattern: `UVMap`, `UV2`, `UV3`, etc
  - report object name with missing channels
