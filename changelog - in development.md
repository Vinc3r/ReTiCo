# Dev changelog

Current changes in [source folder](https://github.com/Vinc3r/BlenderScripts/tree/master/nothing-is-3d).

Usually in-dev version is usable... but bugs can appears of course.

### Misc

- Reports can modify selection if needed [#55](https://github.com/Vinc3r/ReTiCo/issues/55)
- UI cleaning
- Ability to operate only on selected objects, or not

### Materials

- better detection of uv map name in material nodes (Materials -> gltF -> Fix -> UV links) [#44](https://github.com/Vinc3r/ReTiCo/issues/44) [#36](https://github.com/Vinc3r/ReTiCo/issues/36)
- mute/unmute better detection for emit nodes [#53](https://github.com/Vinc3r/ReTiCo/issues/53)
- better detection of textures colorspace [#36](https://github.com/Vinc3r/ReTiCo/issues/36)
- objects using multimaterials can be reported [#52](https://github.com/Vinc3r/ReTiCo/issues/52)
- objects sharing materials can be reported [#54](https://github.com/Vinc3r/ReTiCo/issues/54)
- active texture operations can set viewport shading to Solid -> Texture mode
- backface culling only act when in viewport shading solid [#58](https://github.com/Vinc3r/ReTiCo/issues/58)
