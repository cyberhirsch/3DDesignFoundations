"""Blender 5.2 UI screenshots for the 3D course's shortcut cheat sheet.

Run: blender --factory-startup --enable-event-simulate --no-window-focus -p 0 0 2560 1400 shots_base.blend --python shots.py
Env SHOTS=name,name limits the run. Writes raw PNGs + meta.json into ./raw; shots_post.py crops them.
"""
import bpy, bmesh, json, math, os, sys, traceback
from mathutils import Vector, Euler
from bpy_extras.view3d_utils import location_3d_to_region_2d

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")
os.makedirs(RAW, exist_ok=True)
ONLY = [s for s in os.environ.get("SHOTS", "").split(",") if s]
META = {}
if ONLY and os.path.exists(os.path.join(RAW, "meta.json")):
    META = json.load(open(os.path.join(RAW, "meta.json")))
LOG = open(os.path.join(HERE, "shots.log"), "w", encoding="utf-8")


def log(*a):
    LOG.write(" ".join(str(x) for x in a) + "\n"); LOG.flush()


W = A = R = PROP = OUT = None


def areas():
    global W, A, R, PROP, OUT
    W = bpy.context.window_manager.windows[0]
    scr = W.screen
    A = max((a for a in scr.areas if a.type == "VIEW_3D"), key=lambda a: a.width * a.height)
    R = next(r for r in A.regions if r.type == "WINDOW")
    PROP = next((a for a in scr.areas if a.type == "PROPERTIES"), None)
    OUT = next((a for a in scr.areas if a.type == "OUTLINER"), None)


def ov(area=None, region=None):
    area = area or A
    region = region or next(r for r in area.regions if r.type == "WINDOW")
    return bpy.context.temp_override(window=W, screen=W.screen, area=area, region=region)


def space():
    return A.spaces.active


def rect(x):
    return [x.x, x.y, x.width, x.height]


# ---------------------------------------------------------------- scene helpers
def clean(text=False):
    act = bpy.context.view_layer.objects.active
    if act is not None and act.mode != "OBJECT":
        with ov():
            bpy.ops.object.mode_set(mode="OBJECT")
    sp = space()
    if sp.local_view:
        with ov():
            bpy.ops.view3d.localview()
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for coll in (bpy.data.meshes, bpy.data.curves, bpy.data.lattices):
        for d in list(coll):
            if d.users == 0:
                coll.remove(d)
    sp.shading.type = "SOLID"
    sp.shading.show_xray = False
    sp.overlay.show_wireframes = False
    sp.overlay.show_face_orientation = False
    sp.overlay.show_cursor = False
    sp.overlay.show_text = text
    sp.show_region_ui = False
    sp.show_region_hud = False
    sp.overlay.show_stats = False
    sp.lock_camera = False
    ts = bpy.context.scene.tool_settings
    ts.mesh_select_mode = (True, False, False)
    ts.use_proportional_edit = False
    ts.use_snap = False
    bpy.context.scene.cursor.location = (0, 0, 0)


def add(kind, **kw):
    with ov():
        getattr(bpy.ops.mesh, "primitive_%s_add" % kind)(**kw)
    return bpy.context.view_layer.objects.active


def only(obj):
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def mode(m, sel=None):
    with ov():
        bpy.ops.object.mode_set(mode=m)
        if sel:
            bpy.ops.mesh.select_mode(type=sel)


def deselect_all(bm):
    for seq in (bm.verts, bm.edges, bm.faces):
        for el in seq:
            el.select = False


def bm_select(obj, kind, pred, extend=False):
    bm = bmesh.from_edit_mesh(obj.data)
    if not extend:
        deselect_all(bm)
    seq = {"V": bm.verts, "E": bm.edges, "F": bm.faces}[kind]
    for el in seq:
        if pred(el):
            el.select = True
    bm.select_mode = {{"V": "VERT", "E": "EDGE", "F": "FACE"}[kind]}
    bm.select_flush_mode()
    bmesh.update_edit_mesh(obj.data)
    return bm


def select_none(obj):
    bm = bmesh.from_edit_mesh(obj.data); deselect_all(bm); bmesh.update_edit_mesh(obj.data)


def ez(e):
    return [v.co for v in e.verts]


def look(target=(0, 0, 0), dist=7.5, rot=(62, 0, 40), persp="PERSP"):
    rv = R.data
    rv.view_perspective = persp
    rv.view_location = Vector(target)
    rv.view_distance = dist
    rv.view_rotation = Euler([math.radians(a) for a in rot], "XYZ").to_quaternion()


def op(fn, *a, **kw):
    with ov():
        return fn(*a, **kw)


# ---------------------------------------------------------------- capture
def box_of(objs=None, pts=None, pad=70):
    """Crop box in area-image pixels (origin top-left) around 3D points."""
    ps = [Vector(p) for p in (pts or [])]
    for o in objs or []:
        ps += [o.matrix_world @ Vector(c) for c in o.bound_box]
    xs, ys = [], []
    for p in ps:
        c = location_3d_to_region_2d(R, R.data, p)
        if c is not None:
            xs.append(c.x); ys.append(c.y)
    ox, oy = R.x - A.x, R.y - A.y
    return [ox + min(xs) - pad, A.height - (oy + max(ys)) - pad,
            ox + max(xs) + pad, A.height - (oy + min(ys)) + pad]


def region_box(area=None, rtype="WINDOW"):
    area = area or A
    r = next(x for x in area.regions if x.type == rtype)
    ox, oy = r.x - area.x, r.y - area.y
    return [ox, area.height - (oy + r.height), ox + r.width, area.height - oy]


def grab(name, area=None, box=None, kind="area", extra=None):
    area = area or A
    path = os.path.join(RAW, name + ".png")
    if kind == "window":
        with bpy.context.temp_override(window=W, screen=W.screen):
            bpy.ops.screen.screenshot(filepath=path)
    else:
        with ov(area):
            bpy.ops.screen.screenshot_area(filepath=path)
    META[name] = {"file": path, "kind": kind, "area": rect(area), "box": box,
                  "regions": {r.type: rect(r) for r in area.regions}, "window": [W.width, W.height]}
    if extra:
        META[name].update(extra)
    log("grab", name, kind, box)


def redraw():
    for a in W.screen.areas:
        a.tag_redraw()


MOUSE = [0, 0]


def ev(type, value="PRESS", **kw):
    W.event_simulate(type=type, value=value, x=MOUSE[0], y=MOUSE[1], **kw)


def key(type, **mods):
    ev(type, "PRESS", **mods); ev(type, "RELEASE", **mods)


def mouse_to(wx, wy):
    MOUSE[:] = [int(wx), int(wy)]
    W.event_simulate(type="MOUSEMOVE", value="NOTHING", x=MOUSE[0], y=MOUSE[1])


def view_center():
    return R.x + R.width // 2, R.y + R.height // 2


def to_window(p):
    c = location_3d_to_region_2d(R, R.data, Vector(p))
    return R.x + c.x, R.y + c.y


def menu_shot(name, press, at=None, typed="", nudge=0):
    """Open a menu with a simulated key over the viewport; window grabs before/after for a diff crop."""
    cx, cy = at or view_center()
    mouse_to(cx, cy); yield 0.25
    grab(name + "_before", kind="window"); yield 0.1
    press(); yield 0.5
    if nudge:
        mouse_to(MOUSE[0], MOUSE[1] + nudge); yield 0.4
    for ch in typed:
        ev(ch.upper(), "PRESS", unicode=ch); ev(ch.upper(), "RELEASE"); yield 0.05
    yield 0.5
    grab(name, kind="window", extra={"diff": name + "_before"}); yield 0.1
    key("ESC"); yield 0.2
    key("ESC"); yield 0.3


# ---------------------------------------------------------------- shots
SHOTS = []


def shot(fn):
    SHOTS.append(fn)
    return fn


def cube_edit(sel="EDGE"):
    clean(); o = add("cube", size=2); only(o); mode("EDIT", sel)
    return o


def settle():
    redraw()
    return 0.45


# ---- General
@shot
def tab_edit():
    clean(); o = add("cube", size=2); only(o); mode("EDIT", "VERT")
    look(); yield settle()
    grab("tab_edit", box=box_of([o]))


@shot
def select_modes():
    for kind, sel, pred in [
        ("V", "VERT", lambda v: v.co.x > .9 and v.co.y < -.9 and v.co.z > .9),
        ("E", "EDGE", lambda e: all(c.z > .9 and c.y < -.9 for c in ez(e))),
        ("F", "FACE", lambda f: f.normal.z > .9),
    ]:
        o = cube_edit(sel); bm_select(o, kind, pred); look(); yield settle()
        grab("select_" + sel.lower(), box=box_of([o]))


@shot
def add_menu():
    clean(); o = add("cube", size=2); only(o); look(dist=11); yield settle()
    cx, cy = view_center()
    yield from menu_shot("add_menu", lambda: key("A", shift=True), at=(cx - 200, cy + 380))


@shot
def shade_smooth():
    for tag in ("flat", "smooth"):
        clean(); o = add("uv_sphere", segments=16, ring_count=8, radius=1.2); only(o)
        op(bpy.ops.object.shade_smooth if tag == "smooth" else bpy.ops.object.shade_flat)
        look(dist=6.5); yield settle()
        grab("shade_" + tag, box=box_of([o]))


# ---- Navigate
@shot
def navigate():
    clean(text=True); o = add("cube", size=2); only(o); look(dist=11); yield settle()
    grab("navigate", box=region_box())


@shot
def frame_selected():
    clean(text=True); o = add("cube", size=2, location=(6, 5, 0)); only(o)
    look(target=(-4, -3, 0), dist=26); yield settle()
    grab("frame_before", box=region_box())
    op(bpy.ops.view3d.view_selected); yield settle()
    grab("frame_after", box=region_box())


@shot
def view_axis():
    clean(text=True); o = add("monkey", size=2); only(o); look(dist=7)
    op(bpy.ops.view3d.view_axis, type="FRONT"); yield settle()
    grab("view_front", box=region_box())


@shot
def persp_ortho():
    for tag in ("PERSP", "ORTHO"):
        clean(text=True); objs = []
        for i in range(4):
            objs.append(add("cube", size=1.4, location=(0, i * 2.6, 0)))
        only(objs[0]); look(target=(0, 4, 0), dist=13, rot=(72, 0, 28), persp=tag); yield settle()
        grab("view_" + tag.lower(), box=region_box())


@shot
def local_view():
    clean(text=True); objs = [add("cube", size=1.5, location=(-3, 0, 0)), add("uv_sphere", radius=0.9, location=(0, 0, 0)),
                             add("cylinder", radius=0.8, depth=1.8, location=(3, 0, 0)), add("monkey", size=1.6, location=(0, 3, 0))]
    only(objs[1]); look(target=(0, 1, 0), dist=14); yield settle()
    grab("local_before", box=region_box())
    op(bpy.ops.view3d.localview); yield settle()
    grab("local_after", box=region_box())


# ---- Transform
@shot
def grs():
    clean(); o = add("cube", size=2); only(o); look(dist=13); yield settle()
    wx, wy = to_window((0, 0, 0))
    mouse_to(wx, wy); yield 0.3
    key("G"); yield 0.25
    key("X"); yield 0.25
    mouse_to(wx + 330, wy - 40); yield 0.6
    grab("grs", box=box_of([o], pts=[(-1, -1, -1), (1, 1, 1)], pad=90)); yield 0.1
    key("ESC"); yield 0.3


@shot
def clear_transforms():
    clean(); o = add("cube", size=2); only(o)
    o.location = (2.2, 1.2, 0.8); o.rotation_euler = (0.3, 0.5, 0.9); o.scale = (1.4, 0.8, 0.8)
    look(target=(1, 0.5, 0.3), dist=14); yield settle()
    box = box_of([o], pts=[(-1, -1, -1), (1, 1, 1)], pad=80)
    grab("clear_before", box=box)
    op(bpy.ops.object.location_clear); op(bpy.ops.object.rotation_clear); op(bpy.ops.object.scale_clear)
    yield settle()
    grab("clear_after", box=box)


@shot
def apply_menu():
    clean(); o = add("cube", size=2); only(o); o.scale = (1.5, 1.5, 1.5); look(dist=11); yield settle()
    cx, cy = view_center()
    yield from menu_shot("apply_menu", lambda: key("A", ctrl=True), at=(cx - 150, cy + 250))


# ---- Objects and interface
@shot
def duplicate():
    clean(); o = add("cube", size=2); o.name = "Cube"; only(o)
    op(bpy.ops.object.duplicate_move, TRANSFORM_OT_translate={"value": (2.6, 0, 0)})
    yield settle()
    grab("duplicate_outliner", area=OUT)


@shot
def rename():
    clean(); o = add("cube", size=2); o.name = "Cube.037"; only(o); look(dist=11); yield settle()
    cx, cy = view_center()
    yield from menu_shot("rename", lambda: key("F2"), at=(cx - 100, cy + 150))


@shot
def search():
    clean(); o = add("cube", size=2); only(o); mode("EDIT", "EDGE"); look(dist=11); yield settle()
    cx, cy = view_center()
    yield from menu_shot("search", lambda: key("F3"), at=(cx - 250, cy + 300), typed="bevel")


@shot
def sidebar():
    clean(); o = add("cube", size=2); only(o); o.scale = (1.2, 0.6, 0.9)
    space().show_region_ui = True; look(dist=11); yield settle()
    grab("sidebar", box=region_box(rtype="UI"))


# ---- Bevel, loops, knife
@shot
def bevel_edges():
    o = cube_edit("EDGE")
    bm_select(o, "E", lambda e: all(c.z > .9 and c.y < -.9 for c in ez(e)))
    op(bpy.ops.mesh.bevel, offset=0.45, segments=3, affect="EDGES")
    look(); yield settle()
    grab("bevel_edges", box=box_of([o]))


@shot
def bevel_verts():
    o = cube_edit("VERT")
    bm_select(o, "V", lambda v: v.co.x > .9 and v.co.y < -.9 and v.co.z > .9)
    op(bpy.ops.mesh.bevel, offset=0.7, segments=2, affect="VERTICES")
    look(); yield settle()
    grab("bevel_verts", box=box_of([o]))


def vertical_edge(o, pick=lambda a: a.x > .9 and a.y < -.9):
    """(index, midpoint) of a vertical edge; plain values, since BMesh refs die with their wrapper."""
    bm = bmesh.from_edit_mesh(o.data); bm.edges.ensure_lookup_table()
    for e in bm.edges:
        a, b = ez(e)
        if abs(a.z - b.z) > 1.0 and pick(a):
            return e.index, (a + b) / 2


def loopcut(o, cuts, slide=0.0, pick=None):
    idx, _ = vertical_edge(o, pick) if pick else vertical_edge(o)
    op(bpy.ops.mesh.loopcut_slide,
       MESH_OT_loopcut={"number_cuts": cuts, "smoothness": 0, "falloff": "INVERSE_SQUARE",
                        "object_index": 0, "edge_index": idx},
       TRANSFORM_OT_edge_slide={"value": slide})


@shot
def loop_cut():
    o = cube_edit("EDGE"); select_none(o); look(); yield settle()
    _, mid = vertical_edge(o)
    wx, wy = to_window(o.matrix_world @ mid)
    mouse_to(wx, wy); yield 0.3
    key("R", ctrl=True); yield 0.4
    for _ in range(2):
        ev("WHEELUPMOUSE", "PRESS"); yield 0.15
    yield 0.4
    grab("loop_cut", box=box_of([o])); yield 0.1
    key("ESC"); yield 0.3


@shot
def loop_center():
    o = cube_edit("EDGE"); loopcut(o, 1)
    look(); yield settle()
    grab("loop_center", box=box_of([o]))


@shot
def edge_slide():
    o = cube_edit("EDGE"); loopcut(o, 1)
    op(bpy.ops.transform.edge_slide, value=0.6)
    look(); yield settle()
    grab("edge_slide", box=box_of([o]))


@shot
def knife():
    o = cube_edit("EDGE")
    bm = bmesh.from_edit_mesh(o.data); deselect_all(bm)
    e1 = next(e for e in bm.edges if all(c.z > .9 and c.y > .9 for c in ez(e)))
    e2 = next(e for e in bm.edges if all(c.z > .9 and c.y < -.9 for c in ez(e)))
    e3 = next(e for e in bm.edges if all(c.x > .9 and c.y < -.9 for c in ez(e)))
    v1 = bmesh.utils.edge_split(e1, e1.verts[0], 0.3)[1]
    v2 = bmesh.utils.edge_split(e2, e2.verts[0], 0.55)[1]
    v3 = bmesh.utils.edge_split(e3, e3.verts[0], 0.5)[1]
    new = bmesh.ops.connect_verts(bm, verts=[v1, v2])["edges"] + bmesh.ops.connect_verts(bm, verts=[v2, v3])["edges"]
    for e in new:
        e.select = True
        for v in e.verts:
            v.select = True
    bmesh.update_edit_mesh(o.data)
    look(); yield settle()
    grab("knife", box=box_of([o]))


# ---- Extrude, inset
@shot
def extrude():
    o = cube_edit("FACE"); bm_select(o, "F", lambda f: f.normal.z > .9)
    op(bpy.ops.mesh.extrude_region_move, TRANSFORM_OT_translate={"value": (0, 0, 1.2)})
    look(target=(0, 0, 0.5), dist=9); yield settle()
    grab("extrude", box=box_of([o]))


@shot
def extrude_menu():
    o = cube_edit("FACE"); bm_select(o, "F", lambda f: f.normal.z > .9); look(dist=11); yield settle()
    cx, cy = view_center()
    yield from menu_shot("extrude_menu", lambda: key("E", alt=True), at=(cx - 100, cy + 200))


@shot
def inset():
    o = cube_edit("FACE"); bm_select(o, "F", lambda f: f.normal.z > .9)
    op(bpy.ops.mesh.inset, thickness=0.3, depth=0)
    look(); yield settle()
    grab("inset", box=box_of([o]))


# ---- Subdivision
@shot
def subd_levels():
    clean(); objs = []
    for i, lvl in enumerate((1, 2, 3)):
        o = add("cube", size=2, location=(i * 3 - 3, 0, 0)); only(o)
        op(bpy.ops.object.subdivision_set, level=lvl, relative=False); objs.append(o)
    for o in objs:
        o.select_set(False)
    space().overlay.show_wireframes = True
    look(dist=12, rot=(70, 0, 20)); yield settle()
    grab("subd_levels", box=box_of(objs, pad=40))


@shot
def crease():
    clean(); o = add("cube", size=2); only(o)
    op(bpy.ops.object.subdivision_set, level=2, relative=False)
    mode("EDIT", "EDGE"); bm_select(o, "E", lambda e: all(c.z > .9 for c in ez(e)))
    op(bpy.ops.transform.edge_crease, value=1.0)
    look(); yield settle()
    grab("crease", box=box_of([o]))


# ---- Views
@shot
def shading_pie():
    clean(); o = add("monkey", size=2); only(o); look(dist=9); yield settle()
    yield from menu_shot("shading_pie", lambda: key("Z"))


@shot
def wireframe():
    clean(); o = add("monkey", size=2); only(o)
    space().shading.type = "WIREFRAME"
    look(dist=6.5, rot=(80, 0, 25)); yield settle()
    grab("wireframe", box=box_of([o]))


@shot
def xray():
    clean(); o = add("cube", size=2); only(o); mode("EDIT", "VERT")
    op(bpy.ops.mesh.subdivide, number_cuts=1)
    bm_select(o, "V", lambda v: v.co.y > .9)
    space().shading.show_xray = True
    look(); yield settle()
    grab("xray", box=box_of([o]))


# ---- Modeling selection and cleanup
def ring_cylinder():
    clean(); o = add("cylinder", vertices=12, radius=1, depth=2.4); only(o); mode("EDIT", "EDGE")
    loopcut(o, 2, pick=lambda a: a.x > .9)
    return o


@shot
def loop_select():
    o = ring_cylinder()
    zs = sorted({round(v.co.z, 3) for v in bmesh.from_edit_mesh(o.data).verts})
    z0 = zs[1]
    bm_select(o, "E", lambda e: all(abs(c.z - z0) < 1e-3 for c in ez(e)))
    look(dist=8, rot=(65, 0, 30)); yield settle()
    grab("loop_select", box=box_of([o]))


@shot
def ring_select():
    o = ring_cylinder()
    zs = sorted({round(v.co.z, 3) for v in bmesh.from_edit_mesh(o.data).verts})
    lo, hi = zs[0], zs[1]
    bm_select(o, "E", lambda e: {round(c.z, 3) for c in ez(e)} == {lo, hi})
    look(dist=8, rot=(65, 0, 30)); yield settle()
    grab("ring_select", box=box_of([o]))


def hole_grid():
    clean(); o = add("grid", x_subdivisions=3, y_subdivisions=3, size=3); only(o); mode("EDIT", "FACE")
    bm_select(o, "F", lambda f: f.calc_center_median().length < 0.1)
    op(bpy.ops.mesh.delete, type="FACE")
    return o


@shot
def fill():
    o = hole_grid(); mode("EDIT", "VERT")
    bm_select(o, "V", lambda v: max(abs(v.co.x), abs(v.co.y)) < 0.6)
    look(dist=7, rot=(50, 0, 30)); yield settle()
    grab("fill_before", box=box_of([o]))
    op(bpy.ops.mesh.edge_face_add); yield settle()
    grab("fill_after", box=box_of([o]))


@shot
def tris_quads():
    clean(); o = add("grid", x_subdivisions=3, y_subdivisions=3, size=3); only(o); mode("EDIT", "FACE")
    op(bpy.ops.mesh.select_all, action="SELECT"); op(bpy.ops.mesh.quads_convert_to_tris)
    op(bpy.ops.mesh.select_all, action="DESELECT")
    look(dist=7, rot=(50, 0, 30)); yield settle()
    grab("tris_before", box=box_of([o]))
    op(bpy.ops.mesh.select_all, action="SELECT"); op(bpy.ops.mesh.tris_convert_to_quads)
    op(bpy.ops.mesh.select_all, action="DESELECT"); yield settle()
    grab("tris_after", box=box_of([o]))


@shot
def recalc_normals():
    clean(); o = add("cube", size=2); only(o); mode("EDIT", "FACE")
    bm_select(o, "F", lambda f: f.normal.z > .9 or f.normal.y < -.9)
    op(bpy.ops.mesh.flip_normals); mode("OBJECT")
    space().overlay.show_face_orientation = True
    look(); yield settle()
    grab("normals_before", box=box_of([o]))
    mode("EDIT", "FACE"); op(bpy.ops.mesh.select_all, action="SELECT")
    op(bpy.ops.mesh.normals_make_consistent, inside=False); mode("OBJECT"); yield settle()
    grab("normals_after", box=box_of([o]))


@shot
def faces_by_sides():
    clean(); o = add("grid", x_subdivisions=4, y_subdivisions=4, size=3.2); only(o); mode("EDIT", "FACE")
    bm = bmesh.from_edit_mesh(o.data)
    faces = sorted(bm.faces, key=lambda f: (round(f.calc_center_median().y, 2), round(f.calc_center_median().x, 2)))
    bmesh.ops.triangulate(bm, faces=[faces[5]])
    a, b = faces[10], faces[11]
    shared = [e for e in a.edges if e in b.edges]
    bmesh.ops.dissolve_edges(bm, edges=shared)
    bmesh.update_edit_mesh(o.data)
    op(bpy.ops.mesh.select_all, action="DESELECT")
    op(bpy.ops.mesh.select_face_by_sides, number=4, type="NOTEQUAL")
    look(dist=7, rot=(45, 0, 25)); yield settle()
    grab("faces_by_sides", box=box_of([o]))


# ---------------------------------------------------------------- modifiers (view + panel)
def props_ctx(ctx):
    PROP.spaces.active.context = ctx


def widen_props(px=820):
    """Drag the edge between the 3D view and the right column with simulated mouse events."""
    edge = (A.x + A.width + PROP.x) // 2
    cur = W.width - PROP.x
    if cur >= px - 20:
        return
    y = A.y + A.height // 2
    mouse_to(edge, y); yield 0.3
    ev("LEFTMOUSE", "PRESS"); yield 0.15
    mouse_to(edge - (px - cur) // 2, y); yield 0.1
    mouse_to(edge - (px - cur), y); yield 0.15
    ev("LEFTMOUSE", "RELEASE"); yield 0.4
    areas()
    log("props width", W.width - PROP.x)


@shot
def apply_modifier():
    clean(); o = add("cube", size=2); only(o)
    op(bpy.ops.object.subdivision_set, level=2, relative=False)
    props_ctx("MODIFIER"); look(); yield settle()
    grab("apply_modifier_panel", area=PROP, box=region_box(PROP), extra={"trim": True})


@shot
def mod_solidify():
    clean(); o = add("uv_sphere", segments=32, ring_count=16, radius=1.3); only(o)
    mode("EDIT", "VERT"); bm_select(o, "V", lambda v: v.co.z > 0.01)
    op(bpy.ops.mesh.delete, type="VERT"); mode("OBJECT")
    op(bpy.ops.object.shade_smooth)
    m = o.modifiers.new("Solidify", "SOLIDIFY"); m.thickness = 0.14; m.offset = -1
    props_ctx("MODIFIER")
    look(target=(0, 0, -0.5), dist=6.5, rot=(52, 0, 35)); yield settle()
    grab("mod_solidify_view", box=box_of([o]))
    grab("mod_solidify_panel", area=PROP, box=region_box(PROP), extra={"trim": True})


@shot
def mod_lattice():
    clean(); o = add("cylinder", vertices=32, radius=0.8, depth=2.4); only(o); mode("EDIT", "EDGE")
    loopcut(o, 10, pick=lambda a: a.x > .7)
    mode("OBJECT"); op(bpy.ops.object.shade_smooth)
    with ov():
        bpy.ops.object.add(type="LATTICE", location=(0, 0, 0))
    lat = bpy.context.view_layer.objects.active
    lat.scale = (1.8, 1.8, 2.6)
    ld = lat.data
    ld.points_u = ld.points_v = ld.points_w = 3
    for p in ld.points:
        x, y, z = p.co
        k = {-0.5: 0.75, 0.0: 0.55, 0.5: 1.45}[round(z * 2) / 2]
        ang = {-0.5: 0.0, 0.0: 0.2, 0.5: 0.6}[round(z * 2) / 2]
        ca, sa = math.cos(ang), math.sin(ang)
        p.co_deform = ((x * ca - y * sa) * k, (x * sa + y * ca) * k, z)
    m = o.modifiers.new("Lattice", "LATTICE"); m.object = lat
    only(o); lat.select_set(False)
    props_ctx("MODIFIER")
    look(dist=9, rot=(68, 0, 30)); yield settle()
    grab("mod_lattice_view", box=box_of([o, lat]))
    grab("mod_lattice_panel", area=PROP, box=region_box(PROP), extra={"trim": True})


@shot
def mod_screw():
    clean()
    prof = [(0.35, 0, -1.2), (0.78, 0, -1.0), (0.98, 0, -0.45), (0.86, 0, 0.15),
            (0.5, 0, 0.62), (0.36, 0, 0.98), (0.52, 0, 1.3)]
    me = bpy.data.meshes.new("Profile")
    me.from_pydata(prof, [(i, i + 1) for i in range(len(prof) - 1)], [])
    o = bpy.data.objects.new("Vase", me); bpy.context.collection.objects.link(o); only(o)
    m = o.modifiers.new("Screw", "SCREW")
    m.angle = 2 * math.pi; m.steps = 48; m.render_steps = 48; m.axis = "Z"
    m.use_smooth_shade = True; m.show_in_editmode = True
    mode("EDIT", "VERT"); op(bpy.ops.mesh.select_all, action="SELECT")
    props_ctx("MODIFIER")
    look(dist=7.5, rot=(72, 0, 20)); yield settle()
    grab("mod_screw_view", box=box_of([o]))
    grab("mod_screw_panel", area=PROP, box=region_box(PROP), extra={"trim": True})


@shot
def mod_curve_bevel():
    clean()
    cu = bpy.data.curves.new("Path", "CURVE"); cu.dimensions = "3D"
    sp = cu.splines.new("BEZIER"); sp.bezier_points.add(2)
    for bp, co in zip(sp.bezier_points, [(-2.4, -0.6, 0), (0, 0.5, 0.6), (2.4, -0.4, 0)]):
        bp.co = co; bp.handle_left_type = bp.handle_right_type = "AUTO"
    sp.use_smooth = False  # flat shading, so the star profile's ridges read
    pr = bpy.data.curves.new("Profile", "CURVE"); pr.dimensions = "2D"
    s2 = pr.splines.new("POLY"); n = 10; s2.points.add(n - 1)
    for i, pt in enumerate(s2.points):
        r = 0.42 if i % 2 == 0 else 0.2
        a = 2 * math.pi * i / n
        pt.co = (r * math.cos(a), r * math.sin(a), 0, 1)
    s2.use_cyclic_u = True
    prof = bpy.data.objects.new("Profile", pr); bpy.context.collection.objects.link(prof)
    prof.location = (-2.4, 1.9, 0.9)
    cu.bevel_mode = "OBJECT"; cu.bevel_object = prof; cu.use_fill_caps = True
    path = bpy.data.objects.new("Path", cu); bpy.context.collection.objects.link(path)
    only(path); props_ctx("DATA")
    look(target=(0.2, 0.4, 0.3), dist=9, rot=(60, 0, 62)); yield settle()
    grab("mod_curve_bevel_view", box=box_of([path, prof]))
    # Ctrl+click the collapsed Geometry header (row 904 of the area image at this window size and
    # UI scale): collapses Shape and the others, opens Geometry with its Bevel subpanel.
    mouse_to(PROP.x + 170, PROP.y + PROP.height - 904); yield 0.3
    ev("LEFTMOUSE", "PRESS", ctrl=True); ev("LEFTMOUSE", "RELEASE", ctrl=True); yield 0.6
    mouse_to(A.x + 40, A.y + 40); yield 0.3
    grab("mod_curve_bevel_panel", area=PROP, box=region_box(PROP), extra={"trim": True})


@shot
def mod_mirror():
    clean(); o = add("monkey", size=2); only(o); mode("EDIT", "VERT")
    bm_select(o, "V", lambda v: v.co.x < -0.001)
    op(bpy.ops.mesh.delete, type="VERT")
    op(bpy.ops.mesh.select_all, action="SELECT")
    m = o.modifiers.new("Mirror", "MIRROR"); m.use_clip = True; m.show_in_editmode = True
    props_ctx("MODIFIER")
    look(dist=6.5, rot=(82, 0, 28)); yield settle()
    grab("mod_mirror_view", box=box_of([o]))
    grab("mod_mirror_panel", area=PROP, box=region_box(PROP), extra={"trim": True})


# ---------------------------------------------------------------- round 2 (27 September 2026)
def bind(idname, **props):
    """A spare key (F20) bound for the run only, so menus and panels without a key open at the mouse."""
    km = bpy.context.window_manager.keyconfigs.addon.keymaps.new(name="Window", space_type="EMPTY", region_type="WINDOW")
    kmi = km.keymap_items.new(idname, "F20", "PRESS")
    for k, v in props.items():
        setattr(kmi.properties, k, v)
    return km, kmi


def popup_shot(shot_name, idname, at=None, nudge=0, **props):
    km, kmi = bind(idname, **props)
    try:
        yield from menu_shot(shot_name, lambda: key("F20"), at=at, nudge=nudge)
    finally:
        km.keymap_items.remove(kmi)


def upper_left():
    cx, cy = view_center()
    return cx - 350, cy + 330


def objects_row():
    return [add("cube", size=1.6, location=(-2.6, 0, 0)), add("uv_sphere", radius=0.95, location=(0, 0, 0)),
            add("monkey", size=1.7, location=(2.6, 0, 0))]


@shot
def undo():
    clean(); o = add("cube", size=2); only(o); look(dist=11); yield settle()
    yield from popup_shot("undo", "wm.call_menu", at=upper_left(), name="TOPBAR_MT_edit")


@shot
def save():
    clean(); o = add("cube", size=2); only(o); look(dist=11); yield settle()
    yield from popup_shot("save", "wm.call_menu", at=upper_left(), nudge=46, name="TOPBAR_MT_file")


@shot
def render_menu():
    clean(); o = add("cube", size=2); only(o); look(dist=11); yield settle()
    yield from popup_shot("render", "wm.call_menu", at=upper_left(), name="TOPBAR_MT_render")


@shot
def delete_menu():
    o = cube_edit("FACE"); bm_select(o, "F", lambda f: f.normal.z > .9); look(dist=11); yield settle()
    cx, cy = view_center()
    yield from menu_shot("delete", lambda: key("X"), at=(cx - 150, cy + 250))


@shot
def hide():
    clean(); objs = objects_row(); only(objs[1]); look(dist=11, rot=(66, 0, 12)); yield settle()
    box = box_of(objs, pad=60)
    grab("hide_before", box=box)
    op(bpy.ops.object.hide_view_set, unselected=False); yield settle()
    grab("hide_after", box=box)


@shot
def select_all():
    clean(); objs = [add("cube", size=1.6, location=(x, 0, 0)) for x in (-2.4, 0, 2.4)]
    look(dist=11, rot=(66, 0, 12))
    steps = [("all", lambda: op(bpy.ops.object.select_all, action="SELECT")),
             ("none", lambda: op(bpy.ops.object.select_all, action="DESELECT")),
             ("invert", lambda: (only(objs[1]), op(bpy.ops.object.select_all, action="INVERT")))]
    for tag, fn in steps:
        fn(); yield settle()
        grab("selectall_" + tag, box=box_of(objs, pad=50))


@shot
def box_select():
    clean(); o = add("grid", x_subdivisions=7, y_subdivisions=7, size=3); only(o); mode("EDIT", "VERT")
    op(bpy.ops.mesh.select_all, action="DESELECT")
    look(dist=7, rot=(40, 0, 20)); yield settle()
    x1, y1 = to_window((-1.3, 0.9, 0)); x2, y2 = to_window((0.4, -0.5, 0))
    mouse_to(x1, y1); yield 0.2
    key("B"); yield 0.3
    ev("LEFTMOUSE", "PRESS"); yield 0.1
    mouse_to((x1 + x2) / 2, (y1 + y2) / 2); yield 0.1
    mouse_to(x2, y2); yield 0.4
    grab("box_select", box=box_of([o], pad=40))
    ev("LEFTMOUSE", "RELEASE"); yield 0.2
    key("ESC"); yield 0.2


def camera_scene():
    clean(text=True); o = add("monkey", size=2); only(o)
    cam_data = bpy.data.cameras.new("Camera"); cam = bpy.data.objects.new("Camera", cam_data)
    bpy.context.collection.objects.link(cam)
    cam.location = (4.2, -5.4, 2.6)
    cam.rotation_euler = Euler((math.radians(72), 0, math.radians(38)), "XYZ")
    bpy.context.scene.camera = cam
    look(dist=12)
    return o, cam


@shot
def camera_view():
    o, cam = camera_scene(); op(bpy.ops.view3d.view_camera); yield settle()
    grab("camera_view", box=region_box())


@shot
def lock_camera():
    o, cam = camera_scene(); op(bpy.ops.view3d.view_camera)
    space().lock_camera = True; yield settle()
    grab("lock_camera", box=region_box())


@shot
def snapping():
    clean(); o = add("cube", size=2); only(o); look(dist=11)
    bpy.context.scene.tool_settings.use_snap = True; yield settle()
    yield from popup_shot("snapping", "wm.call_panel", at=upper_left(), name="VIEW3D_PT_snapping", keep_open=True)


@shot
def proportional():
    clean(); o = add("grid", x_subdivisions=24, y_subdivisions=24, size=4); only(o); mode("EDIT", "VERT")
    bm_select(o, "V", lambda v: v.co.length < 0.09)
    ts = bpy.context.scene.tool_settings
    ts.use_proportional_edit = True; ts.proportional_size = 1.3
    look(dist=9, rot=(58, 0, 25)); yield settle()
    wx, wy = to_window((0, 0, 0)); mouse_to(wx, wy); yield 0.3
    key("G"); yield 0.2
    key("Z"); yield 0.2
    mouse_to(wx, wy + 90); yield 0.1
    mouse_to(wx, wy + 170); yield 0.5
    grab("proportional", box=box_of([o], pts=[(0, 0, 1.4)], pad=30)); yield 0.1
    key("ESC"); yield 0.3


@shot
def cursor():
    clean(); o = add("cube", size=2); only(o)
    bpy.context.scene.cursor.location = (0.35, -0.3, 1.0)
    space().overlay.show_cursor = True
    op(bpy.ops.object.select_all, action="DESELECT")
    look(); yield settle()
    grab("cursor", box=box_of([o]))


@shot
def snap_pie():
    clean(); o = add("cube", size=2); only(o); look(dist=9); yield settle()
    yield from menu_shot("snap_pie", lambda: key("S", shift=True))


@shot
def set_origin():
    clean(); o = add("cube", size=2); only(o); mode("EDIT", "VERT")
    op(bpy.ops.mesh.select_all, action="SELECT")
    op(bpy.ops.transform.translate, value=(1, 1, 1)); mode("OBJECT")
    look(target=(1, 1, 0.8), dist=9); yield settle()
    box = box_of([o], pts=[(0, 0, 0)], pad=60)
    grab("origin_before", box=box)
    op(bpy.ops.object.origin_set, type="ORIGIN_GEOMETRY"); yield settle()
    grab("origin_after", box=box)


def two_islands():
    clean(); a = add("cube", size=1.6, location=(-1.4, 0, 0)); b = add("uv_sphere", radius=0.9, location=(1.4, 0, 0))
    for x in (a, b):
        x.select_set(True)
    bpy.context.view_layer.objects.active = a
    op(bpy.ops.object.join)
    o = bpy.context.view_layer.objects.active
    mode("EDIT", "VERT")
    return o


@shot
def separate():
    o = two_islands(); bm_select(o, "V", lambda v: v.co.x > 0.3); look(dist=11); yield settle()
    cx, cy = view_center()
    yield from menu_shot("separate", lambda: key("P"), at=(cx - 150, cy + 200))


@shot
def select_linked():
    o = two_islands(); bm_select(o, "V", lambda v: v.co.x > 0.3)
    look(dist=9, rot=(64, 0, 12)); yield settle()
    grab("select_linked", box=box_of([o]))


@shot
def parent():
    clean(); vase = add("cylinder", radius=0.8, depth=2); vase.name = "Vase"
    lid = add("cylinder", radius=0.85, depth=0.2, location=(0, 0, 1.15)); lid.name = "Lid"
    for x in (vase, lid):
        x.select_set(True)
    bpy.context.view_layer.objects.active = vase
    op(bpy.ops.object.parent_set, type="OBJECT")
    OUT.spaces.active.use_filter_object_content = False; yield settle()
    for _ in range(2):
        with ov(OUT):
            bpy.ops.outliner.show_one_level(open=True)
        yield settle()
    grab("parent_outliner", area=OUT)


@shot
def collection_menu():
    clean(); o = add("cube", size=2); only(o); look(dist=11); yield settle()
    cx, cy = view_center()
    yield from menu_shot("collection", lambda: key("M"), at=(cx - 150, cy + 200))


@shot
def mode_pie():
    clean(); o = add("cube", size=2); only(o); look(dist=9); yield settle()
    yield from menu_shot("mode_pie", lambda: key("TAB", ctrl=True))


@shot
def toolbar_popup():
    clean(); o = add("cube", size=2); only(o); look(dist=11); yield settle()
    cx, cy = view_center()
    yield from menu_shot("toolbar", lambda: key("SPACE", shift=True), at=(cx - 250, cy + 150))


@shot
def maximize():
    clean(); o = add("cube", size=2); only(o); look(dist=11); yield settle()
    grab("maximize_before", kind="window")
    with ov():
        bpy.ops.screen.screen_full_area()
    areas(); yield 0.6
    grab("maximize_after", kind="window")
    with ov():
        bpy.ops.screen.back_to_previous()
    areas(); yield 0.6


@shot
def field_menu():
    clean(); o = add("cube", size=2); only(o); o.location = (0.5, 0, 0)
    space().show_region_ui = True; look(dist=11); yield settle()
    ui = next(r for r in A.regions if r.type == "UI")
    mouse_to(ui.x + 300, ui.y + ui.height - 130); yield 0.3
    grab("field_menu_before", kind="window"); yield 0.1
    key("RIGHTMOUSE"); yield 0.7
    grab("field_menu", kind="window", extra={"diff": "field_menu_before"}); yield 0.1
    key("ESC"); yield 0.3


@shot
def statistics():
    clean(text=True); o = add("monkey", size=2); only(o)
    space().overlay.show_stats = True; look(dist=8); yield settle()
    grab("statistics", box=region_box())


@shot
def import_export():
    clean(); o = add("cube", size=2); only(o); look(dist=11); yield settle()
    yield from popup_shot("import", "wm.call_menu", at=upper_left(), name="TOPBAR_MT_file_import")
    yield from popup_shot("export", "wm.call_menu", at=upper_left(), name="TOPBAR_MT_file_export")


@shot
def units():
    clean(); o = add("cube", size=2); only(o); look(dist=11); yield settle()
    yield from popup_shot("units", "wm.call_panel", at=upper_left(), name="SCENE_PT_unit", keep_open=True)


@shot
def pack():
    clean(); o = add("cube", size=2); only(o); look(dist=11); yield settle()
    yield from popup_shot("pack", "wm.call_menu", at=upper_left(), name="TOPBAR_MT_file_external_data")


@shot
def offset_loops():
    o = cube_edit("EDGE"); loopcut(o, 1)
    op(bpy.ops.mesh.offset_edge_loops_slide, MESH_OT_offset_edge_loops={"use_cap_endpoint": False},
       TRANSFORM_OT_edge_slide={"value": 0.45})
    look(); yield settle()
    grab("offset_loops", box=box_of([o]))


@shot
def grow():
    clean(); o = add("grid", x_subdivisions=6, y_subdivisions=6, size=3.6); only(o); mode("EDIT", "FACE")
    bm_select(o, "F", lambda f: f.calc_center_median().length < 0.35)
    look(dist=7.5, rot=(45, 0, 25)); yield settle()
    box = box_of([o], pad=30)
    grab("grow_before", box=box)
    op(bpy.ops.mesh.select_more); yield settle()
    grab("grow_after", box=box)


@shot
def shortest_path():
    clean(); o = add("grid", x_subdivisions=6, y_subdivisions=6, size=3.6); only(o); mode("EDIT", "VERT")
    bm = bmesh.from_edit_mesh(o.data); deselect_all(bm)
    vs = sorted(bm.verts, key=lambda v: (v.co.x + v.co.y))
    a, b = vs[0], vs[-1]
    a.select = True; b.select = True
    bm.select_history.clear(); bm.select_history.add(a); bm.select_history.add(b)
    bmesh.update_edit_mesh(o.data)
    op(bpy.ops.mesh.shortest_path_select)
    look(dist=7.5, rot=(45, 0, 25)); yield settle()
    grab("shortest_path", box=box_of([o], pad=30))


@shot
def select_similar():
    o = cube_edit("FACE"); bm_select(o, "F", lambda f: f.normal.z > .9); look(dist=11); yield settle()
    cx, cy = view_center()
    yield from menu_shot("select_similar", lambda: key("G", shift=True), at=(cx - 150, cy + 250))


@shot
def dissolve():
    o = ring_cylinder()
    zs = sorted({round(v.co.z, 3) for v in bmesh.from_edit_mesh(o.data).verts})
    z0 = zs[1]
    bm_select(o, "E", lambda e: all(abs(c.z - z0) < 1e-3 for c in ez(e)))
    look(dist=8, rot=(65, 0, 30)); yield settle()
    box = box_of([o])
    grab("dissolve_before", box=box)
    op(bpy.ops.mesh.dissolve_mode); yield settle()
    grab("dissolve_after", box=box)


@shot
def merge_menu():
    o = cube_edit("VERT"); bm_select(o, "V", lambda v: v.co.z > .9); look(dist=11); yield settle()
    cx, cy = view_center()
    yield from menu_shot("merge", lambda: key("M"), at=(cx - 150, cy + 250))


@shot
def edge_menu():
    o = cube_edit("EDGE"); bm_select(o, "E", lambda e: all(c.z > .9 and c.y < -.9 for c in ez(e)))
    look(dist=11); yield settle()
    cx, cy = view_center()
    yield from menu_shot("edge_menu", lambda: key("E", ctrl=True), at=(cx - 250, cy + 330))


def sculpt_sphere(level=2, segments=32, rings=16):
    clean(); o = add("uv_sphere", segments=segments, ring_count=rings, radius=1.4); only(o)
    op(bpy.ops.object.shade_smooth)
    m = o.modifiers.new("Multires", "MULTIRES")
    for _ in range(3):
        op(bpy.ops.object.multires_subdivide, modifier="Multires", mode="CATMULL_CLARK")
    m.sculpt_levels = level
    mode("SCULPT")
    return o, m


def hide_shelf():
    for r in A.regions:
        log("region", r.type, r.height)
    if any(r.type == "ASSET_SHELF" and r.height > 1 for r in A.regions):
        with ov():
            bpy.ops.screen.region_toggle(region_type="ASSET_SHELF")


@shot
def brush_size():
    o, m = sculpt_sphere(); look(target=(0, 0, -0.6), dist=8.5); yield settle(); hide_shelf(); yield settle()
    wx, wy = to_window((0, 0, 0)); mouse_to(wx, wy); yield 0.3
    key("F"); yield 0.3
    mouse_to(wx + 60, wy + 20); yield 0.5
    grab("brush_size", box=box_of([o], pad=90)); yield 0.1
    key("ESC"); yield 0.3


@shot
def sculpt_invert():
    o, m = sculpt_sphere(3); look(target=(0, 0, -0.2), dist=7, rot=(80, 0, 0)); yield settle(); hide_shelf(); yield settle()
    for ctrl, z in ((False, 0.45), (False, 0.45), (True, -0.45), (True, -0.45)):
        x1, y1 = to_window((-0.9, -1.2, z)); x2, y2 = to_window((0.9, -1.2, z))
        mouse_to(x1, y1); yield 0.2
        ev("LEFTMOUSE", "PRESS", ctrl=ctrl); yield 0.05
        for i in range(1, 25):
            t = i / 24
            mouse_to(x1 + (x2 - x1) * t, y1 + (y2 - y1) * t); yield 0.02
        ev("LEFTMOUSE", "RELEASE", ctrl=ctrl); yield 0.3
    grab("sculpt_invert", box=box_of([o]))


@shot
def sculpt_level():
    o, m = sculpt_sphere(1, segments=8, rings=4); space().overlay.show_wireframes = True
    look(target=(0, 0, -0.6), dist=7); yield settle(); hide_shelf(); yield settle()
    box = box_of([o])
    grab("sculptlevel_before", box=box)
    op(bpy.ops.object.subdivision_set, level=3, relative=False); yield settle()
    grab("sculptlevel_after", box=box)


@shot
def unwrap_menu():
    o = cube_edit("FACE"); op(bpy.ops.mesh.select_all, action="SELECT"); look(dist=11); yield settle()
    cx, cy = view_center()
    yield from menu_shot("unwrap_menu", lambda: key("U"), at=(cx - 150, cy + 250))


@shot
def mark_seam():
    o = cube_edit("EDGE")
    bm_select(o, "E", lambda e: all(c.z > .9 for c in ez(e)) or all(c.x > .9 and c.y < -.9 for c in ez(e)))
    op(bpy.ops.mesh.mark_seam, clear=False); select_none(o)
    look(); yield settle()
    grab("mark_seam", box=box_of([o]))


def to_nodes():
    """Turn the 3D view into a Shader Editor showing a small material."""
    clean(); o = add("uv_sphere", radius=1); only(o)
    mat = bpy.data.materials.new("Ceramic"); mat.use_nodes = True
    nt = mat.node_tree; bsdf = nt.nodes.get("Principled BSDF")
    tex = nt.nodes.new("ShaderNodeTexImage"); tex.location = (-420, 260)
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    o.data.materials.append(mat)
    A.type = "NODE_EDITOR"; A.ui_type = "ShaderNodeTree"
    A.spaces.active.show_region_ui = False
    return o


def back_to_3d():
    A.type = "VIEW_3D"
    areas()


@shot
def node_home():
    to_nodes(); yield 0.4
    reg = next(r for r in A.regions if r.type == "WINDOW")
    with bpy.context.temp_override(window=W, screen=W.screen, area=A, region=reg):
        bpy.ops.node.view_all()
    yield 0.6
    ox, oy = reg.x - A.x, reg.y - A.y
    nodes = A.spaces.active.edit_tree.nodes
    k = bpy.context.preferences.view.ui_scale  # node locations are drawn scaled by the UI scale
    xs, ys = [], []
    for n in nodes:
        x0, y0 = n.location.x * k, n.location.y * k
        for vx, vy in ((x0, y0), (x0 + n.dimensions.x, y0 - n.dimensions.y)):
            rx, ry = reg.view2d.view_to_region(vx, vy, clip=False)
            xs.append(rx); ys.append(ry)
    pad = 60
    grab("node_home", area=A, box=[ox + min(xs) - pad, A.height - (oy + max(ys)) - pad,
                                   ox + max(xs) + pad, A.height - (oy + min(ys)) + pad])
    back_to_3d(); yield 0.3


@shot
def node_add():
    to_nodes(); yield 0.6
    reg = next(r for r in A.regions if r.type == "WINDOW")
    mouse_to(reg.x + 240, reg.y + reg.height // 2 + 330); yield 0.3
    grab("node_add_before", kind="window"); yield 0.1
    key("A", shift=True); yield 0.7
    grab("node_add", kind="window", extra={"diff": "node_add_before"}); yield 0.1
    key("ESC"); yield 0.3
    back_to_3d(); yield 0.3


# ---------------------------------------------------------------- runner
def runner_steps():
    yield from widen_props()
    for fn in SHOTS:
        if ONLY and fn.__name__ not in ONLY:
            continue
        log("shot", fn.__name__)
        try:
            for d in fn():
                yield d
        except Exception:
            log(traceback.format_exc())
            try:
                key("ESC"); key("ESC")
            except Exception:
                pass
        yield 0.1


STEPS = None


def setup():
    p = bpy.context.preferences
    p.view.ui_scale = 2.0
    p.view.show_tooltips = False
    p.view.smooth_view = 0
    areas()


def tick():
    global STEPS
    try:
        if STEPS is None:
            setup()
            STEPS = runner_steps()
            return 1.2
        d = next(STEPS)
        return d if d is not None else 0.2
    except StopIteration:
        json.dump(META, open(os.path.join(RAW, "meta.json"), "w"), indent=1)
        log("done", len(META))
        bpy.ops.wm.quit_blender()
        return None
    except Exception:
        log(traceback.format_exc())
        return 0.2


bpy.app.timers.register(tick, first_interval=1.5)
