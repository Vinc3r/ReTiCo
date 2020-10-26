# Dev changelog

Current changes in [retico source folder](https://github.com/Vinc3r/ReTiCo/tree/master/retico).

Usually in-dev version is usable... but bugs can appears of course.

For Releases'changelogs, see [documentation](https://github.com/Vinc3r/ReTiCo/wiki/Changelog).

---
## Doc' modification needs:
* [ ] custom normals change, below autosmooth
---

### General

- detect if selection is empty while "only on selection" is active, and tell the user about the situation

### Materials

- glTF workflow: new way for muting textures
- glTF workflow: allow to mute individual ORM channels (by unlinking outputs of SEPRGB node)
- emissive texture node are detected more efficiently

### Meshes

- Custom Normals can now be batch deleted or added (below autosmooth function)
- [Fix](https://github.com/Vinc3r/ReTiCo/issues/72): avoid UV naming issue
- [Fix](https://github.com/Vinc3r/ReTiCo/issues/66): transfer name doesn't crash when there isn't active object
