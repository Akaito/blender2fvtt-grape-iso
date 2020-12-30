Work in progress!  Very much not ready yet!

Shield: [![CC BY 4.0][cc-by-shield]][cc-by]

This work is licensed under a
[Creative Commons Attribution 4.0 International License][cc-by].

[![CC BY 4.0][cc-by-image]][cc-by]

[cc-by]: http://creativecommons.org/licenses/by/4.0/
[cc-by-image]: https://i.creativecommons.org/l/by/4.0/88x31.png
[cc-by-shield]: https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg

## TODO / next steps

- [ ] Better tile positions
      Tile positioning is _close_, but there's something I'm missing.
- [x] Render walls from Blender.
- [ ] Figure out how to handle complex meshes.
      Maybe complex meshes (for rendering purposes) have
      parent objects that are the collision mesh?
      Or, if we do keep non-wall objects turned on during
      renders of walls, this problem may already be solved for us.
      Save for if someone wants to start bouncing light/reflections around...
      There _may_ be a shadow-catcher-like setting to handle that case.


## Ideas / future
- Can we provide a quick-wall macro?
  1. Draw a (square) template.
  2. Hover its control icon.
  3. Press the macro's hotkey.
  4. Macro makes walls at the template's edges.
  5. Macro makes a tile and hooks it to the walls.
  6. User manually changes wall's image.

