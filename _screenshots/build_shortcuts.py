"""Write shortcuts.html for the 3D Design Foundations site from one data list."""
import html, json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
SIZES = json.load(open(os.path.join(HERE, "sizes.json")))  # written by shots_post.py
OUT = os.path.join(os.path.dirname(HERE), "shortcuts.html")
E = html.escape


def keys(spec):
    """'Ctrl+Shift+B' -> kbd chips; ' / ' and ' · ' separate alternatives; '→' starts a menu path."""
    if spec.startswith("Select →"):
        return f'<span class="path">{E(spec)}</span>'
    if spec.endswith(" during slide"):
        return f'<kbd>{E(spec[:-13])}</kbd> during slide'
    if re.fullmatch(r"[A-Z] [A-Z]", spec):
        return " ".join(f"<kbd>{c}</kbd>" for c in spec.split())
    out = []
    for alt in re.split(r"( / | · )", spec):
        if alt in (" / ", " · "):
            out.append(f'<span class="sep">{alt.strip()}</span>')
            continue
        if "→" in alt:
            first, rest = alt.split("→", 1)
            out.append(f"<kbd>{E(first.strip())}</kbd> <span class=\"path\">→ {E(rest.strip())}</span>")
            continue
        parts = alt.split("+") if alt not in ("+",) else [alt]
        chips = []
        for p in parts:
            p = p.strip()
            if p.endswith(" drag"):
                chips.append(f"<kbd>{E(p[:-5])}</kbd> drag")
            else:
                chips.append(f"<kbd>{E(p)}</kbd>")
        out.append('<span class="plus">+</span>'.join(chips))
    return " ".join(out)


# (action, keys, notes, image, caption)
BASICS = [
    ("General", None, [
        ("Toggle Edit Mode", "Tab", "", "tab-edit", "Edit Mode: the cube's vertices, edges and faces become selectable."),
        ("Vertex / Edge / Face mode", "1 / 2 / 3", "In Edit Mode (top row keys)", "select-modes", "A vertex, an edge and a face selected, in that order."),
        ("Add object (e.g. Lattice)", "Shift+A", "In Object Mode", "add-menu", "The Add menu."),
        ("Shade Smooth", "Right-click → Shade Smooth", "No default key", "shade-smooth", "The same sphere, flat and then smooth."),
    ]),
    ("Navigate", None, [
        ("Orbit / pan / zoom", "Middle mouse drag · Shift+Middle mouse drag · Scroll", "Or drag the gizmo at the top right of the viewport", "navigate",
         "The navigation gizmo: drag the axes to orbit; zoom, pan, camera and orthographic below."),
        ("Frame selected", "Numpad .", "Home frames everything", "frame-selected", "Before and after: the view jumps to the selection."),
        ("Front / right / top view", "Numpad 1 / Numpad 3 / Numpad 7", "Add Ctrl for the opposite side; model from references here", "view-axis", "Numpad 1: Front Orthographic."),
        ("Perspective / orthographic", "Numpad 5", "", "persp-ortho", "The same row of cubes in perspective, then orthographic."),
        ("Local view", "Numpad /", "Shows only the selection; press again to go back", "local-view", "Four objects, then only the selected sphere."),
    ]),
    ("Transform", None, [
        ("Move / rotate / scale", "G / R / S", "Then X, Y or Z to lock an axis; type a number, Enter", "grs", "G, then X: the cube slides along the red X axis."),
        ("Clear move / rotation / scale", "Alt+G / Alt+R / Alt+S", "Back to the origin, unrotated, scale 1", "clear-transforms", "Before and after Alt+G, Alt+R and Alt+S."),
        ("Apply transforms", "Ctrl+A", "Object Mode; apply the scale before you model or export", "apply-menu", "The Apply menu."),
    ]),
    ("Objects and interface", None, [
        ("Duplicate", "Shift+D", "The copy is named .001; rename it", "duplicate", "The Outliner after Shift+D: Cube and Cube.001."),
        ("Rename", "F2", "Ctrl+F2 renames many at once", "rename", "F2: the active object's name, ready to type over."),
        ("Search any command", "F3", "The results show each command's shortcut", "search", "F3, then “bevel”: Bevel Edges is Ctrl B, Bevel Vertices Shift Ctrl B."),
        ("Sidebar", "N", "Item tab: location, rotation, scale and dimensions", "sidebar", "The sidebar's Item tab."),
    ]),
    ("Views", None, [
        ("Shading pie (Wireframe/Solid)", "Z", "", "shading-pie", "The shading pie."),
        ("Toggle full wireframe", "Shift+Z", "Edged-faces overlay has no key; use Overlays menu", "wireframe", "Wireframe shading."),
        ("X-ray", "Alt+Z", "See and select through the mesh", "xray", "X-ray on: the vertices at the back show, and can be selected."),
    ]),
]
MODELING = [
    ("Bevel", None, [
        ("Bevel edges", "Ctrl+B", "Scroll = segments", "bevel-edges", "One edge, beveled with three segments."),
        ("Bevel vertices", "Ctrl+Shift+B", "", "bevel-verts", "One corner vertex, beveled."),
    ]),
    ("Loop Cut", None, [
        ("Loop cut", "Ctrl+R", "Scroll = cuts, click, drag to slide", "loop-cut", "Ctrl+R, scrolled to three cuts: the yellow preview before the click."),
        ("Center loop", "Right-click during slide", "", "loop-center", "The new loop, left in the middle."),
        ("Slide existing loop", "G G", "", "edge-slide", "A loop slid down; it stays on the surface."),
        ("Knife", "K", "Enter to confirm", "knife", "Two knife cuts, across the top face and down the front."),
    ]),
    ("Extrude", None, [
        ("Extrude", "E", "", "extrude", "The top face, extruded upwards."),
        ("Extrude options menu", "Alt+E", "Along Normals, Individual Faces", "extrude-menu", "The Extrude menu."),
        ("Inset", "I", "", "inset", "The top face, inset."),
    ]),
    ("Subdivision", None, [
        ("Add Subdivision level 1/2/3", "Ctrl+1 / 2 / 3", "Object Mode", "subd-levels", "The same cube at levels 1, 2 and 3, wireframe overlay on."),
        ("Edge crease", "Shift+E", "Edit Mode, drag or type 1", "crease", "The top edges creased to 1: sharp on top, round below."),
    ]),
    ("Select and clean up", None, [
        ("Select edge loop", "Alt+click", "On an edge", "loop-select", "One edge loop around the cylinder."),
        ("Select edge ring", "Ctrl+Alt+click", "On an edge", "ring-select", "One edge ring: the parallel edges across a band."),
        ("Fill / make face", "F", "Between selected vertices or edges", "fill", "Four vertices around a hole, then F."),
        ("Triangles to quads", "Alt+J", "", "tris-to-quads", "A triangulated grid, then Alt+J."),
        ("Recalculate normals", "Shift+N", "The Face Orientation overlay shows flipped faces in red", "recalc-normals", "Two flipped faces in red, then Shift+N."),
        ("Find n-gons and triangles", "Select → Select All by Trait → Faces by Sides", "Number of Vertices 4, Type Not Equal To; no default key", "faces-by-sides",
         "Every face that isn't a quad, selected."),
    ]),
    ("Modifiers", None, [
        ("Apply modifier", "Ctrl+A", "Mouse over the modifier panel", "apply-modifier", "Hover over the panel and press Ctrl+A: the modifier becomes real geometry."),
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
    head = f'<h3 id="{anchor}">{E(title)}</h3>'
    body = "\n".join(
        f'        <tr><td>{E(a)}</td><td class="keys">{peek(img, cap, k)}</td><td class="note">{E(n)}</td></tr>'
        for a, k, n, img, cap in rows)
    return f"""    {head}
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


basics = "".join(table(t, rows, "basics-" + slug(t)) for t, _, rows in BASICS)
modeling = "".join(table(t, rows, "subd-" + slug(t)) for t, _, rows in MODELING)
mods = "".join(mod_card(*m) for m in MODS)
count = sum(len(r) for _, _, r in BASICS + MODELING)

page = open(os.path.join(HERE, "shortcuts_template.html"), encoding="utf-8").read()
page = page.replace("{{BASICS}}", basics).replace("{{MODELING}}", modeling).replace("{{MODS}}", mods)
open(OUT, "w", encoding="utf-8", newline="\n").write(page)
print("rows", count, "->", OUT)
