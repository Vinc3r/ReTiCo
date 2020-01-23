# Dev changelog

Current changes in [source folder](https://github.com/Vinc3r/BlenderScripts/tree/master/nothing-is-3d).

Usually in-dev version is usable... but bugs can appears of course.



### Misc

- new: Reports can modify selection if needed [#55](https://github.com/Vinc3r/ReTiCo/issues/55)
- new: Ability to operate only on selected objects, or not
- new: reports can be sent to clipboard
- UI cleaning
- doc' is now on [Github wiki](https://github.com/Vinc3r/ReTiCo/wiki)

### Materials

- new: Blend mode (in material settings) is set according to alpha value
- new: objects using multimaterials can be reported [#52](https://github.com/Vinc3r/ReTiCo/issues/52)
- new: objects sharing materials can be reported [#54](https://github.com/Vinc3r/ReTiCo/issues/54)
- new: active texture operations can set viewport shading to Solid -> Texture mode
- fix: mute/unmute better detection for emit nodes [#53](https://github.com/Vinc3r/ReTiCo/issues/53)
- fix: better detection of textures colorspace [#36](https://github.com/Vinc3r/ReTiCo/issues/36)
- better detection of uv map name in material nodes (Materials -> gltF -> Fix -> UV links) [#44](https://github.com/Vinc3r/ReTiCo/issues/44) [#36](https://github.com/Vinc3r/ReTiCo/issues/36)
- backface culling enhanced [#58](https://github.com/Vinc3r/ReTiCo/issues/58)

### Meshes

- new:  report to detect instanced meshes
- autosmooth option to delete custom normals, or not