"""Write shortcuts.html for the 3D Design Foundations site from one data list."""
import html, json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
SIZES = json.load(open(os.path.join(HERE, "sizes.json")))  # written by shots_post.py
OUT = os.path.join(os.path.dirname(HERE), "shortcuts.html")
E = html.escape
MENU_FIRST = ("Select →", "File →", "Overlays →", "Scene Properties →", "Sidebar →")


def chips(alt):
    """'Ctrl+Shift+B' -> <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>B</kbd>; 'Middle mouse drag' -> chip + 'drag'."""
    out = []
    for p in alt.split("+"):
        p = p.strip()
        if p.endswith(" drag"):
            out.append(f"<kbd>{E(p[:-5])}</kbd> drag")
        else:
            out.append(f"<kbd>{E(p)}</kbd>")
    return '<span class="plus">+</span>'.join(out)


def keys(spec):
    """Key chips; ' / ' and ' · ' separate alternatives; 'Key → Menu item' is a key followed by a menu path;
    a spec that starts with a menu name ('File → Import') is a menu path without a key."""
    if spec.startswith(MENU_FIRST):
        return ' <span class="sep">·</span> '.join(f'<span class="path">{E(p)}</span>' for p in spec.split(" · "))
    if spec.endswith(" during slide"):
        return f'<kbd>{E(spec[:-13])}</kbd> during slide'
    if re.fullmatch(r"[A-Z] [A-Z]", spec):
        return " ".join(f"<kbd>{c}</kbd>" for c in spec.split())
    out = []
    for alt in re.split(r"( / | · )", spec):
        if alt in (" / ", " · "):
            out.append(f'<span class="sep">{alt.strip()}</span>')
        elif "→" in alt:
            first, rest = alt.split("→", 1)
            out.append(f'{chips(first.strip())} <span class="path">→ {E(rest.strip())}</span>')
        else:
            out.append(chips(alt))
    return " ".join(out)


# (action, keys, notes, image, caption)
BASICS = [
    ("General", [
        ("Toggle Edit Mode", "Tab", "", "tab-edit", "Edit Mode: the cube's vertices, edges and faces become selectable."),
        ("Vertex / Edge / Face mode", "1 / 2 / 3", "In Edit Mode (top row keys)", "select-modes", "A vertex, an edge and a face selected, in that order."),
        ("Add object (e.g. Lattice)", "Shift+A", "In Object Mode", "add-menu", "The Add menu."),
        ("Undo / redo", "Ctrl+Z / Ctrl+Shift+Z", "Edit → Undo History lists every step", "undo", "The Edit menu: Undo and Redo, with their keys."),
        ("Save", "Ctrl+S", "Ctrl+Shift+S saves as; Ctrl+Alt+S saves the next numbered version", "save",
         "The File menu: Save, Save As and Save Incremental."),
        ("Delete", "X", "In Edit Mode it asks what: vertices, edges, faces, or dissolve", "delete", "The Delete menu in Edit Mode."),
        ("Hide / unhide / hide others", "H / Alt+H / Shift+H", "", "hide", "Three objects, then H with the sphere selected."),
        ("Shade Smooth", "Right-click → Shade Smooth", "No default key", "shade-smooth", "The same sphere, flat and then smooth."),
    ]),
    ("Select", [
        ("Select all / none / invert", "A / Alt+A / Ctrl+I", "", "select-all", "A, then Alt+A, then Ctrl+I with the middle cube selected."),
        ("Box / circle select", "B / C", "Or drag with the Select Box tool", "box-select", "B, then drag: the vertices in the box get selected."),
    ]),
    ("Navigate", [
        ("Orbit / pan / zoom", "Middle mouse drag · Shift+Middle mouse drag · Scroll", "Or drag the gizmo at the top right of the viewport", "navigate",
         "The navigation gizmo: drag the axes to orbit; zoom, pan, camera and orthographic below."),
        ("Frame selected", "Numpad .", "Home frames everything", "frame-selected", "Before and after: the view jumps to the selection."),
        ("Front / right / top view", "Numpad 1 / Numpad 3 / Numpad 7", "Add Ctrl for the opposite side; model from references here", "view-axis", "Numpad 1: Front Orthographic."),
        ("Perspective / orthographic", "Numpad 5", "", "persp-ortho", "The same row of cubes in perspective, then orthographic."),
        ("Local view", "Numpad /", "Shows only the selection; press again to go back", "local-view", "Four objects, then only the selected sphere."),
        ("Camera view / camera to view", "Numpad 0 / Ctrl+Alt+Numpad 0", "Look through the camera; put the camera where you are looking from", "camera-view",
         "Numpad 0: Camera Perspective, the frame your render shows."),
        ("Frame the camera by navigating", "Sidebar → View → View Lock → Camera to View", "Then orbit and zoom to frame your render; no default key", "lock-camera",
         "Camera to View on: the frame gets a dashed red border and follows your navigation."),
    ]),
    ("Transform", [
        ("Move / rotate / scale", "G / R / S", "Then X, Y or Z to lock an axis; type a number, Enter", "grs", "G, then X: the cube slides along the red X axis."),
        ("Snap / fine control while moving", "Ctrl · Shift", "Hold while moving: Ctrl snaps, Shift slows down. Shift+Tab turns snapping on", "snapping",
         "The snapping options: what to snap to."),
        ("Proportional editing", "O", "Edit Mode: the neighbours follow; scroll to change the radius", "proportional",
         "O on, then G, Z: the neighbours follow inside the radius."),
        ("Clear move / rotation / scale", "Alt+G / Alt+R / Alt+S", "Back to the origin, unrotated, scale 1", "clear-transforms", "Before and after Alt+G, Alt+R and Alt+S."),
        ("Apply transforms", "Ctrl+A", "Object Mode; apply the scale before you model or export", "apply-menu", "The Apply menu."),
        ("Place the 3D cursor", "Shift+right-click", "", "cursor", "The 3D cursor, placed on the top face."),
        ("Snap pie", "Shift+S", "Cursor to Selected, Selection to Cursor", "snap-pie", "The Snap pie."),
        ("Set the origin (pivot)", "Right-click → Set Origin", "Origin to Geometry, or to 3D Cursor; no default key", "set-origin",
         "The origin at a corner, then Origin to Geometry."),
    ]),
    ("Objects and interface", [
        ("Duplicate", "Shift+D", "The copy is named .001; rename it", "duplicate", "The Outliner after Shift+D: Cube and Cube.001."),
        ("Join / separate", "Ctrl+J / P", "P in Edit Mode: Selection, By Material, By Loose Parts", "separate", "The Separate menu in Edit Mode."),
        ("Parent / clear parent", "Ctrl+P / Alt+P", "The child follows its parent", "parent", "The Outliner after Ctrl+P: Lid now sits under Vase."),
        ("Move to collection", "M", "", "collection", "The Move to Collection menu."),
        ("Rename", "F2", "Ctrl+F2 renames many at once", "rename", "F2: the active object's name, ready to type over."),
        ("Search any command", "F3", "The results show each command's shortcut", "search", "F3, then “bevel”: Bevel Edges is Ctrl B, Bevel Vertices Shift Ctrl B."),
        ("Sidebar", "N", "Item tab: location, rotation, scale and dimensions", "sidebar", "The sidebar's Item tab."),
        ("Mode pie", "Ctrl+Tab", "", "mode-pie", "The mode pie."),
        ("Toolbar at the mouse", "Shift+Space", "", "toolbar", "The toolbar, opened at the mouse, with a key for each tool."),
        ("Maximize an area", "Ctrl+Space", "Press again to go back", "maximize", "The layout, then Ctrl+Space over the viewport."),
        ("Copy, paste or reset a value", "Ctrl+C / Ctrl+V · Backspace", "Hover over the field; hold Alt while editing to change all selected objects",
         "field-menu", "Right-click on a field: Reset to Default is Backspace."),
    ]),
    ("Views", [
        ("Shading pie (Wireframe/Solid)", "Z", "", "shading-pie", "The shading pie."),
        ("Toggle full wireframe", "Shift+Z", "Edged-faces overlay has no key; use Overlays menu", "wireframe", "Wireframe shading."),
        ("X-ray", "Alt+Z", "See and select through the mesh", "xray", "X-ray on: the vertices at the back show, and can be selected."),
        ("Face and vertex counts", "Overlays → Statistics", "Top left of the viewport; no default key", "statistics",
         "Statistics on: vertices, edges, faces and triangles."),
    ]),
    ("Files and render", [
        ("Import USD / export glTF", "File → Import · File → Export", "Universal Scene Description in, glTF 2.0 out", "import-export", "The Import and Export menus."),
        ("Scene units", "Scene Properties → Units", "Unit Scale and Length: what one unit means", "units", "The Units panel."),
        ("Pack textures into the .blend", "File → External Data → Pack Resources", "Before you hand in the .blend", "pack", "The External Data menu."),
        ("Render / show the last render", "F12 / F11", "", "render", "The Render menu: Render Image F12, View Render F11."),
    ]),
]
MODELING = [
    ("Bevel", [
        ("Bevel edges", "Ctrl+B", "Scroll = segments", "bevel-edges", "One edge, beveled with three segments."),
        ("Bevel vertices", "Ctrl+Shift+B", "", "bevel-verts", "One corner vertex, beveled."),
    ]),
    ("Loop Cut", [
        ("Loop cut", "Ctrl+R", "Scroll = cuts, click, drag to slide", "loop-cut", "Ctrl+R, scrolled to three cuts: the yellow preview before the click."),
        ("Center loop", "Right-click during slide", "", "loop-center", "The new loop, left in the middle."),
        ("Slide existing loop", "G G", "", "edge-slide", "A loop slid down; it stays on the surface."),
        ("Offset edge loops", "Ctrl+Shift+R", "Support loops on both sides of an edge", "offset-loops", "A loop, then Ctrl+Shift+R: a new loop on each side."),
        ("Knife", "K", "Enter to confirm", "knife", "Two knife cuts, across the top face and down the front."),
    ]),
    ("Extrude", [
        ("Extrude", "E", "", "extrude", "The top face, extruded upwards."),
        ("Extrude options menu", "Alt+E", "Along Normals, Individual Faces", "extrude-menu", "The Extrude menu."),
        ("Inset", "I", "", "inset", "The top face, inset."),
    ]),
    ("Subdivision", [
        ("Add Subdivision level 1/2/3", "Ctrl+1 / 2 / 3", "Object Mode", "subd-levels", "The same cube at levels 1, 2 and 3, wireframe overlay on."),
        ("Edge crease", "Shift+E", "Edit Mode, drag or type 1", "crease", "The top edges creased to 1: sharp on top, round below."),
    ]),
    ("Select", [
        ("Select edge loop", "Alt+click", "On an edge", "loop-select", "One edge loop around the cylinder."),
        ("Select edge ring", "Ctrl+Alt+click", "On an edge", "ring-select", "One edge ring: the parallel edges across a band."),
        ("Select linked", "L / Ctrl+L", "L picks the part under the mouse; Ctrl+L grows the selection to whole parts", "select-linked",
         "One loose part, selected with L."),
        ("Grow / shrink selection", "Ctrl+Numpad Plus / Ctrl+Numpad Minus", "", "grow", "One face, then Ctrl+Numpad Plus."),
        ("Select shortest path", "Ctrl+click", "From the active element to the clicked one", "shortest-path",
         "Two corners: everything on the shortest path between them."),
        ("Select similar", "Shift+G", "Same material, area, number of sides …", "select-similar", "The Select Similar menu."),
    ]),
    ("Clean up", [
        ("Fill / make face", "F", "Between selected vertices or edges", "fill", "Four vertices around a hole, then F."),
        ("Dissolve", "Ctrl+X", "Removes a loop without leaving a hole; X → Edges would", "dissolve", "A loop, then Ctrl+X: gone, and the faces stay closed."),
        ("Merge", "M", "By Distance welds duplicate vertices", "merge", "The Merge menu."),
        ("Triangles to quads", "Alt+J", "", "tris-to-quads", "A triangulated grid, then Alt+J."),
        ("Recalculate normals", "Shift+N", "The Face Orientation overlay shows flipped faces in red", "recalc-normals", "Two flipped faces in red, then Shift+N."),
        ("Find n-gons and triangles", "Select → Select All by Trait → Faces by Sides", "Number of Vertices 4, Type Not Equal To; no default key", "faces-by-sides",
         "Every face that isn't a quad, selected."),
    ]),
    ("Menus", [
        ("Edge and face menus", "Ctrl+E / Ctrl+F", "Bridge Edge Loops, Mark Seam; Poke Faces, Grid Fill", "edge-menu", "The Edge menu (Ctrl+E)."),
    ]),
    ("Modifiers", [
        ("Apply modifier", "Ctrl+A", "Mouse over the modifier panel", "apply-modifier", "Hover over the panel and press Ctrl+A: the modifier becomes real geometry."),
    ]),
]
SCULPT = [
    ("Sculpt Mode", [
        ("Brush size / strength", "F / Shift+F", "Move the mouse, click to set", "brush-size", "F: the brush radius, set with the mouse."),
        ("Invert / smooth a stroke", "Ctrl+drag / Shift+drag", "Ctrl carves in instead of building up; Shift smooths", "sculpt-invert",
         "Two Draw strokes: the upper one plain, the lower one with Ctrl held."),
        ("Sculpt level", "Ctrl+1 / 2 / 3 / 4 / 5", "Sets the Multires level you sculpt on, and adds levels if needed", "sculpt-level", "Level 1, then Ctrl+3."),
    ]),
]
UVS = [
    ("UV editing", [
        ("Unwrap menu", "U", "Edit Mode: Unwrap (three methods), Smart UV Project", "unwrap-menu", "The UV Mapping menu."),
        ("Mark a seam", "Ctrl+E → Mark Seam", "Seams show red; unwrapping cuts along them", "mark-seam", "Seams marked on the top edges and one corner."),
    ]),
]
NODES = [
    ("Shader Editor", [
        ("Add a node", "Shift+A", "In the Shader Editor", "node-add", "The Add menu in the Shader Editor."),
        ("Frame all nodes", "Home", "", "node-home", "Home: every node in view."),
    ]),
]
MODS = [
    ("Solidify", "solidify", "Properties → Modifiers → Add Modifier → Generate → Solidify",
     "Gives a surface a wall. Model a thin object — a bowl, a lampshade, a leaf — as a single layer, and Solidify adds the thickness. Offset decides which side the wall grows on."),
    ("Lattice", "lattice", "Shift+A → Lattice, then Add Modifier → Deform → Lattice, Object: the lattice",
     "Bends a mesh with a coarse cage. Move the lattice's points in Edit Mode and the mesh follows, however dense it is."),
    ("Screw", "screw", "Properties → Modifiers → Add Modifier → Generate → Screw",
     "Spins a profile around an axis. Draw half the silhouette of a vase or a bottle as a line of vertices; Screw turns it into the surface. Steps sets how smooth the turn is."),
    ("Curve Bevel", "curve-bevel", "Select the path curve → Properties → Object Data → Geometry → Bevel → Object",
     "Sweeps a profile along a path. Draw the path as one curve and the cross-section as a second; the path's Bevel takes the second as its shape. In Blender this is a curve setting, not a modifier."),
    ("Mirror", "mirror", "Properties → Modifiers → Add Modifier → Generate → Mirror",
     "Model one half, see the whole. Delete the other half and add Mirror; Clipping keeps the middle vertices on the seam, and Merge welds them."),
]


def peek(img, cap, spec):
    w, h = SIZES["shortcuts/%s.webp" % img]
    return (f'<button type="button" class="peek" data-img="img/shortcuts/{img}.webp" data-w="{w}" data-h="{h}" '
            f'data-cap="{E(cap, quote=True)}" aria-label="{E(spec, quote=True)}: show what it does">{keys(spec)}</button>')


def table(title, rows, anchor):
    body = "\n".join(
        f'        <tr><td>{E(a)}</td><td class="keys">{peek(img, cap, k)}</td><td class="note">{E(n)}</td></tr>'
        for a, k, n, img, cap in rows)
    return f"""    <h3 id="{anchor}">{E(title)}</h3>
    <table>
      <thead><tr><th>Action</th><th>Shortcut</th><th>Notes</th></tr></thead>
      <tbody>
{body}
      </tbody>
    </table>
"""


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def mod_card(name, key, where, text):
    vw, vh = SIZES["modifiers/%s-view.webp" % key]
    pw, ph = SIZES["modifiers/%s-panel.webp" % key]
    return f"""    <article class="mod" id="mod-{key}">
      <h3>{E(name)}</h3>
      <p>{E(text)}</p>
      <p class="where">{E(where)}</p>
      <div class="shots">
        <a href="img/modifiers/{key}-view.webp"><img src="img/modifiers/{key}-view.webp" width="{vw // 2}" height="{vh // 2}" loading="lazy" alt="{E(name)} in the viewport"></a>
        <a href="img/modifiers/{key}-panel.webp"><img src="img/modifiers/{key}-panel.webp" width="{pw // 2}" height="{ph // 2}" loading="lazy" alt="The {E(name)} settings in the Properties editor"></a>
      </div>
    </article>
"""


def section(groups, prefix):
    return "".join(table(t, rows, prefix + "-" + slug(t)) for t, rows in groups)


page = open(os.path.join(HERE, "shortcuts_template.html"), encoding="utf-8").read()
for key, val in {"{{BASICS}}": section(BASICS, "basics"), "{{MODELING}}": section(MODELING, "subd"),
                 "{{SCULPT}}": section(SCULPT, "sculpt"), "{{UVS}}": section(UVS, "uv"),
                 "{{NODES}}": section(NODES, "nodes"), "{{MODS}}": "".join(mod_card(*m) for m in MODS)}.items():
    assert page.count(key) == 1, key
    page = page.replace(key, val)
open(OUT, "w", encoding="utf-8", newline="\n").write(page)
count = sum(len(r) for _, r in BASICS + MODELING + SCULPT + UVS + NODES)
print("rows", count, "->", OUT)
