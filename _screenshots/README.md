# Screenshots for shortcuts.html

Not published: GitHub Pages skips folders that start with an underscore.

The page and its 47 images are generated. Edit the rows in `build_shortcuts.py` and the
page frame in `shortcuts_template.html`, not `shortcuts.html` itself.

## Rebuild after a Blender update

Run in this folder with Git Bash. Blender opens behind other windows; `--factory-startup`
keeps your preferences untouched.

```bash
B="/c/Program Files/Blender Foundation/Blender 5.2/blender.exe"
"$B" -b --factory-startup --python-expr "import bpy; bpy.ops.wm.save_as_mainfile(filepath=r'$(pwd -W)/shots_base.blend')"
"$B" --factory-startup --enable-event-simulate --no-window-focus -p 0 0 2560 1400 "$(pwd -W)/shots_base.blend" --python shots.py
python shots_post.py        # crops into ../img and writes sizes.json
python build_shortcuts.py   # writes ../shortcuts.html
```

- `SHOTS=bevel_edges,knife` in front of the Blender command re-shoots only those.
- Opening `shots_base.blend` adds it to Blender's recent-files list; clear the line afterwards in
  `%APPDATA%\Blender Foundation\Blender\5.2\config\recent-files.txt`.
- The window is 2560 × 1400 at UI scale 2. The Curve Bevel shot Ctrl-clicks the Geometry panel
  header at a fixed position, and a few crops in `shots_post.py` are fractions of a menu. Check
  those if the window size or Blender's layout changes.
