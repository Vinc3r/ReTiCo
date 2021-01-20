# Dev changelog

Current changes in [retico source folder](https://github.com/Vinc3r/ReTiCo/tree/master/retico).

Usually in-dev version is usable... but bugs can appears of course.

For Releases'changelogs, see [documentation](https://github.com/Vinc3r/ReTiCo/wiki/Changelog).

---
## Doc' modification needs:
* [ ] custom normals change, below autosmooth
* [ ] new UI
---

### General

- New: detect if selection is empty while "only on selection" is active, and tell the user about the situation
- New: UI is now splitted into sub-categories, allowing better navigation

### Materials

- glTF workflow: allow to mute/unmute individual ORM channels
    - if ORM is a unique image, ReTiCo unlink/link outputs to the SEPRGB node
    - if ORM are separated images, ReTiCo just mute indivudual texture nodes
- emissive texture node are detected more efficiently

### Meshes

- Custom Normals can now be batch deleted or added (below autosmooth function)
- [Fix](https://github.com/Vinc3r/ReTiCo/issues/72): avoid UV naming issue
- [Fix](https://github.com/Vinc3r/ReTiCo/issues/66): transfer name doesn't crash when there isn't active object
