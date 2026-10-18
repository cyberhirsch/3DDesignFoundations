"""Render the cage / subdivided pairs for topology.html.

Run headless with Blender 5.2:
  "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" -b --factory-startup --python _topology/build_renders.py

Every example is built from code, so the cage in the picture is exactly the
mesh that was subdivided. Output: img/topology/<key>_cage.webp, _subd.webp and,
for some, _refl.webp (reflection matcap, no wire). A report of face counts
(quads / tris / n-gons) is printed for each example.
"""
import math
import os
import sys

import bmesh
import bpy
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "img", "topology")
os.makedirs(OUT, exist_ok=True)

ONLY = None
if "--" in sys.argv:
    args = sys.argv[sys.argv.index("--") + 1:]
    if args:
        ONLY = set(args)


def lin(hex_rgb):
    """sRGB hex to linear RGBA."""
    h = hex_rgb.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    c = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return (*c, 1.0)


BG = lin("#EEF0F3")
CAGE = lin("#D5D9E1")
WIRE = lin("#1C2028")
SURF = lin("#E3E6EC")
BLUE = lin("#2439D4")

W, H = 720, 540


# ---------------------------------------------------------------- scene

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_WORKBENCH"
    sc.render.resolution_x = W
    sc.render.resolution_y = H
    sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = "WEBP"
    sc.render.image_settings.quality = 86
    sc.display.render_aa = "16"
    sc.view_settings.view_transform = "Standard"
    sh = sc.display.shading
    sh.light = "STUDIO"
    sh.studio_light = "Default"
    sh.color_type = "OBJECT"
    sh.show_specular_highlight = True
    sh.show_object_outline = False
    sh.show_cavity = False
    sh.show_shadows = False
    world = bpy.data.worlds.new("bg")
    world.color = BG[:3]
    sc.world = world
    return sc


def link(obj):
    bpy.context.scene.collection.objects.link(obj)
    return obj


def obj_from_bm(name, bm):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    return link(bpy.data.objects.new(name, me))


def obj_from_pydata(name, verts, faces):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], faces)
    me.validate()
    me.update()
    return link(bpy.data.objects.new(name, me))


def report(key, obj):
    me = obj.data
    q = sum(1 for p in me.polygons if len(p.vertices) == 4)
    t = sum(1 for p in me.polygons if len(p.vertices) == 3)
    n = sum(1 for p in me.polygons if len(p.vertices) > 4)
    print(f"[{key}] faces {len(me.polygons)}: quads {q}, tris {t}, ngons {n}")


def wire_copy(src, thickness, color, name):
    o = link(bpy.data.objects.new(name, src.data))
    o.matrix_world = src.matrix_world.copy()
    m = o.modifiers.new("wire", "WIREFRAME")
    m.thickness = thickness
    m.use_replace = True
    m.use_even_offset = True
    m.use_relative_offset = False
    m.offset = 0.0
    m.use_boundary = True
    o.color = color
    return o


def camera(direction, target, scale):
    cam_data = bpy.data.cameras.new("cam")
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = scale
    cam = link(bpy.data.objects.new("cam", cam_data))
    d = Vector(direction).normalized()
    cam.location = Vector(target) + d * 20
    cam.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = cam
    return cam


def render(path):
    bpy.context.scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


def shoot(key, cage, cam_dir, target, scale, wire=0.016, levels=3,
          refl=False, keep_corners=False, extra_mods=None):
    """Render <key>_cage.webp, <key>_subd.webp (and <key>_refl.webp)."""
    report(key, cage)
    camera(cam_dir, target, scale)
    sh = bpy.context.scene.display.shading

    # cage: flat, grey, dark wire
    cage.color = CAGE
    w1 = wire_copy(cage, wire, WIRE, "wire_dark")
    render(os.path.join(OUT, f"{key}_cage.webp"))
    cage.hide_render = True
    w1.hide_render = True

    # subdivided: smooth surface with the cage wire in blue
    sub = link(bpy.data.objects.new("subd", cage.data.copy()))
    sub.matrix_world = cage.matrix_world.copy()
    sub.data.shade_smooth()
    m = sub.modifiers.new("sub", "SUBSURF")
    m.levels = levels
    m.render_levels = levels
    if keep_corners:
        m.boundary_smooth = "PRESERVE_CORNERS"
    sub.color = SURF
    w2 = wire_copy(cage, wire * 0.75, BLUE, "wire_blue")
    render(os.path.join(OUT, f"{key}_subd.webp"))

    if refl:
        w2.hide_render = True
        sh.light = "MATCAP"
        sh.studio_light = "check_reflection_horizontal.exr"
        render(os.path.join(OUT, f"{key}_refl.webp"))
        sh.light = "STUDIO"
        sh.studio_light = "Default"
    return sub


VIEW = (1.0, -1.25, 0.95)
TOP = (0.0, -0.0001, 1.0)


# ---------------------------------------------------------------- builders

def cube_bm(size=2.0):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=size)
    return bm


def support_cube(width):
    bm = cube_bm()
    bmesh.ops.bevel(bm, geom=list(bm.edges), offset=width, offset_type="OFFSET",
                    profile_type="SUPERELLIPSE", segments=2, profile=1.0,
                    affect="EDGES", clamp_overlap=True)
    return bm


def ex_support():
    for key, width in (("support_none", None), ("support_loose", 0.5),
                       ("support_mid", 0.2), ("support_tight", 0.05)):
        if ONLY and key not in ONLY:
            continue
        reset()
        bm = cube_bm() if width is None else support_cube(width)
        cage = obj_from_bm(key, bm)
        shoot(key, cage, VIEW, (0, 0, -0.1), 4.7)

    key = "support_crease"
    if not ONLY or key in ONLY:
        reset()
        cage = obj_from_bm(key, cube_bm())
        attr = cage.data.attributes.new("crease_edge", "FLOAT", "EDGE")
        sharp = cage.data.attributes.new("sharp_edge", "BOOLEAN", "EDGE")
        for i in range(len(cage.data.edges)):
            attr.data[i].value = 1.0
            sharp.data[i].value = True
        shoot(key, cage, VIEW, (0, 0, -0.1), 4.7)


def ex_levels():
    for lv in (0, 1, 2, 3):
        key = f"levels_{lv}"
        if ONLY and key not in ONLY:
            continue
        reset()
        cage = obj_from_bm(key, support_cube(0.35))
        shoot(key, cage, VIEW, (0, 0, -0.1), 4.7, levels=lv)


def ex_ngon():
    key = "ngon_top"
    if not ONLY or key in ONLY:
        reset()
        bm = support_cube(0.2)
        top = [f for f in bm.faces if all(v.co.z > 0.999 for v in f.verts)]
        bmesh.ops.dissolve_faces(bm, faces=top)
        cage = obj_from_bm(key, bm)
        shoot(key, cage, VIEW, (0, 0, -0.1), 4.7, refl=True)
    key = "quad_top"
    if not ONLY or key in ONLY:
        reset()
        cage = obj_from_bm(key, support_cube(0.2))
        shoot(key, cage, VIEW, (0, 0, -0.1), 4.7, refl=True)


def ex_sphere():
    key = "sphere_uv"
    if not ONLY or key in ONLY:
        reset()
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=8, radius=1.0)
        cage = obj_from_bm(key, bm)
        shoot(key, cage, (0.6, -1.0, 1.1), (0, 0, 0), 3.0, wire=0.012, refl=True)
    key = "sphere_quad"
    if not ONLY or key in ONLY:
        reset()
        bm = cube_bm(2.0)
        bmesh.ops.subdivide_edges(bm, edges=list(bm.edges), cuts=2, use_grid_fill=True)
        for v in bm.verts:
            v.co = v.co.normalized()
        cage = obj_from_bm(key, bm)
        shoot(key, cage, (0.6, -1.0, 1.1), (0, 0, 0), 3.0, wire=0.012, refl=True)


def ring(n, r, z=0.0, phase=0.0):
    return [Vector((r * math.cos(phase + 2 * math.pi * k / n),
                    r * math.sin(phase + 2 * math.pi * k / n), z)) for k in range(n)]


PANEL_N = 16         # faces per side, evenly spaced over -1..1
BLOCK_N = 4          # the middle BLOCK_N x BLOCK_N faces become the circle


def grid_with_circle(rs, rh, boss=False, boolean=False):
    """An evenly spaced 16x16 panel whose middle 4x4 block becomes a 16-sided circle.

    No border loops: the panel's edge stays open, far from the hole.
    rs: radius the block's border is pushed to (To Sphere style: the edge
    midpoints move out, the corners in), rh: radius of the rim ring just
    inside it, which is the support loop. Without boss the rim is a hole.
    boolean: the same panel and the same 16-sided hole, but the block's
    square border is joined to it by four n-gons, as a Boolean modifier
    leaves it.
    """
    n, b = PANEL_N, BLOCK_N
    cs = [-1.0 + 2.0 * i / n for i in range(n + 1)]
    lo, hi = (n - b) // 2, (n + b) // 2
    idx = {}
    verts = []
    for j, y in enumerate(cs):
        for i, x in enumerate(cs):
            if lo < i < hi and lo < j < hi:
                continue            # the block's inner vertices go
            idx[i, j] = len(verts)
            verts.append(Vector((x, y, 0.0)))
    faces = []
    for j in range(n):
        for i in range(n):
            if lo <= i < hi and lo <= j < hi:
                continue
            faces.append([idx[i, j], idx[i + 1, j], idx[i + 1, j + 1], idx[i, j + 1]])
    # the block's border, counter-clockwise from the (+x, -y) corner
    ring_ij = ([(hi, j) for j in range(lo, hi)] + [(i, hi) for i in range(hi, lo, -1)]
               + [(lo, j) for j in range(hi, lo, -1)] + [(i, lo) for i in range(lo, hi)])
    border = [idx[p] for p in ring_ij]
    nb = len(border)                # 16
    if boolean:
        circ = []
        for k in range(nb):
            a = -math.pi / 4 + 2 * math.pi * k / nb
            circ.append(len(verts))
            verts.append(Vector((rh * math.cos(a), rh * math.sin(a), 0.0)))
        q4 = nb // 4
        for q in range(4):
            side = [border[(q4 * q + s) % nb] for s in range(q4 + 1)]
            arc = [circ[(q4 * q + s) % nb] for s in range(q4 + 1)]
            faces.append(side + arc[::-1])
        return verts, faces
    for bi in border:
        v = verts[bi]
        a = math.atan2(v.y, v.x)
        verts[bi] = Vector((rs * math.cos(a), rs * math.sin(a), 0.0))
    rim = []
    for bi in border:
        a = math.atan2(verts[bi].y, verts[bi].x)
        rim.append(len(verts))
        verts.append(Vector((rh * math.cos(a), rh * math.sin(a), 0.0)))
    for k in range(nb):
        faces.append([border[k], border[(k + 1) % nb], rim[(k + 1) % nb], rim[k]])
    if not boss:
        return verts, faces

    # boss: wall up with support loops at base and top, then the block's
    # own 4x4 quads as the cap
    def lift(ids, r, z):
        out = []
        for bi in ids:
            a = math.atan2(verts[bi].y, verts[bi].x)
            out.append(len(verts))
            verts.append(Vector((r * math.cos(a), r * math.sin(a), z)))
        return out

    h = 0.3
    top_r = rh - 0.045
    l1 = lift(rim, rh, 0.035)
    l2 = lift(rim, rh, h - 0.035)
    l3 = lift(rim, rh, h)
    l4 = lift(rim, top_r, h)
    for a_, b_ in ((rim, l1), (l1, l2), (l2, l3), (l3, l4)):
        for k in range(nb):
            faces.append([a_[k], a_[(k + 1) % nb], b_[(k + 1) % nb], b_[k]])
    cap = dict(zip(ring_ij, l4))
    s = top_r / rs
    for j in range(lo + 1, hi):
        for i in range(lo + 1, hi):
            cap[i, j] = len(verts)
            verts.append(Vector((cs[i] * s, cs[j] * s, h)))
    for j in range(lo, hi):
        for i in range(lo, hi):
            faces.append([cap[i, j], cap[i + 1, j], cap[i + 1, j + 1], cap[i, j + 1]])
    return verts, faces


HOLE_VIEW = (0.45, -1.0, 1.5)
BEND_R = 2.2


def bend(verts):
    """Roll the flat panel onto a cylinder around the x axis (a car door):
    every cross-section along x is the same arc, so the reflection stripes
    run straight along x wherever the topology is clean."""
    out = []
    for v in verts:
        a = v.y / BEND_R
        out.append(Vector((v.x, BEND_R * math.sin(a), v.z + BEND_R * (math.cos(a) - 1.0))))
    return out


def ex_holes():
    rs, rh = 0.28, 0.22
    key = "hole_grid"
    if not ONLY or key in ONLY:
        reset()
        v, f = grid_with_circle(rs, rh)
        cage = obj_from_pydata(key, bend(v), f)
        shoot(key, cage, HOLE_VIEW, (0, 0, -0.12), 2.45, wire=0.006, keep_corners=True, refl=True)
    key = "hole_boolean"
    if not ONLY or key in ONLY:
        reset()
        v, f = grid_with_circle(rs, rh, boolean=True)
        cage = obj_from_pydata(key, bend(v), f)
        shoot(key, cage, HOLE_VIEW, (0, 0, -0.12), 2.45, wire=0.006, keep_corners=True, refl=True)
    key = "boss_grid"
    if not ONLY or key in ONLY:
        reset()
        v, f = grid_with_circle(rs, rh, boss=True)
        cage = obj_from_pydata(key, v, f)
        shoot(key, cage, VIEW, (0, 0, 0.05), 2.3, wire=0.005, keep_corners=True)

def capped_cylinder(cap):
    n = 16
    verts, faces = [], []

    def add_ring(r, z):
        start = len(verts)
        verts.extend(ring(n, r, z))
        return list(range(start, start + n))

    rings = [add_ring(1.0, 0.0), add_ring(1.0, 1.05), add_ring(1.0, 1.2), add_ring(0.88, 1.2)]
    for lo, hi in zip(rings, rings[1:]):
        for k in range(n):
            faces.append([lo[k], lo[(k + 1) % n], hi[(k + 1) % n], hi[k]])
    rim = rings[-1]

    def dome(r):
        return 1.2 + 0.22 * (1 - (r / 0.88) ** 2)

    if cap == "ngon":
        # the n-gon itself cannot dome; it stays flat
        faces.append(rim[:])
    elif cap == "fan":
        c = len(verts)
        verts.append(Vector((0, 0, dome(0))))
        for k in range(n):
            faces.append([rim[k], rim[(k + 1) % n], c])
        # a middle ring so the fan can carry the dome like the grid does
    elif cap == "grid":
        a = 0.5
        cs = [-a, -a / 2, 0.0, a / 2, a]
        gid = {}
        for j, y in enumerate(cs):
            for i, x in enumerate(cs):
                gid[i, j] = len(verts)
                p = Vector((x, y, 0))
                if i in (0, 4) or j in (0, 4):
                    ang = math.atan2(y, x)
                    circ = Vector((0.62 * math.cos(ang), 0.62 * math.sin(ang), 0))
                    p = p.lerp(circ, 0.6)
                p.z = dome(p.length)
                verts.append(p)
        for j in range(4):
            for i in range(4):
                faces.append([gid[i, j], gid[i + 1, j], gid[i + 1, j + 1], gid[i, j + 1]])
        bnd = [gid[i, 0] for i in range(5)] + [gid[4, j] for j in range(1, 5)] + \
              [gid[i, 4] for i in range(3, -1, -1)] + [gid[0, j] for j in range(3, 0, -1)]
        bnd.sort(key=lambda vi: math.atan2(verts[vi].y, verts[vi].x) % (2 * math.pi))
        # ring vertex k sits at angle k*22.5 deg; the boundary vertex at 0 deg is gid[4,2]
        start = bnd.index(gid[4, 2])
        bnd = bnd[start:] + bnd[:start]
        for k in range(n):
            faces.append([rim[k], rim[(k + 1) % n], bnd[(k + 1) % n], bnd[k]])
    return verts, faces


def ex_caps():
    for cap in ("ngon", "fan", "grid"):
        key = f"cap_{cap}"
        if ONLY and key not in ONLY:
            continue
        reset()
        v, f = capped_cylinder(cap)
        cage = obj_from_pydata(key, v, f)
        shoot(key, cage, (0.5, -1.0, 1.3), (0, 0, 0.75), 3.2, wire=0.011, refl=True)


# ---------------------------------------------------------------- pattern library tiles
#
# Small renders for the pattern library: 360x270, only the subdivided result
# with the cage in blue on top. Keys start with "pl_". Run them all with
#   blender -b --factory-startup --python _topology/build_renders.py -- pl
# Each report line must show tris 0, ngons 0 for a "Do" tile.

TW, TH = 360, 270


def want(key):
    return not ONLY or key in ONLY or "pl" in ONLY


class Soup:
    """Faces given as point lists; points at the same spot become one vertex."""

    def __init__(self):
        self.verts, self.faces, self.key = [], [], {}

    def v(self, p):
        k = tuple(round(c, 5) + 0.0 for c in p)
        if k not in self.key:
            self.key[k] = len(self.verts)
            self.verts.append(Vector(p))
        return self.key[k]

    def add(self, poly):
        self.faces.append([self.v(p) for p in poly])

    def obj(self, name):
        return obj_from_pydata(name, self.verts, self.faces)


def shoot_tile(key, cage, cam_dir, target, scale, wire=None, levels=3, keep_corners=False):
    """Render <key>_subd.webp at tile size: the subdivided surface, cage in blue."""
    report(key, cage)
    bm = bmesh.new()
    bm.from_mesh(cage.data)
    open_edges = sum(1 for e in bm.edges if len(e.link_faces) == 1)
    bad_edges = sum(1 for e in bm.edges if len(e.link_faces) > 2)
    bm.free()
    print(f"[{key}] open edges {open_edges}, edges with 3+ faces {bad_edges}")
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y = TW, TH
    sc.render.image_settings.quality = 82
    wire = wire or scale * 0.0055
    camera(cam_dir, target, scale)
    cage.hide_render = True
    sub = link(bpy.data.objects.new("subd", cage.data.copy()))
    sub.matrix_world = cage.matrix_world.copy()
    sub.data.shade_smooth()
    m = sub.modifiers.new("sub", "SUBSURF")
    m.levels = m.render_levels = levels
    if keep_corners:
        m.boundary_smooth = "PRESERVE_CORNERS"
    sub.color = SURF
    wire_copy(cage, wire, BLUE, "wire_blue")
    render(os.path.join(OUT, f"{key}_subd.webp"))


def feature(us, vs, blk, rings, shape="circle", cap=False):
    """A flat grid (us x vs) whose block of cells blk=(i0, i1, j0, j1) is
    replaced by rings. rings[0] = (r, 0) moves the block's border (a circle of
    radius r, or for shape "square" the border scaled by r); every further
    (r, z) adds a ring. cap fills the last ring with the block's own grid.
    Returns quads as lists of (u, v, z) and the set of points the feature made.
    """
    i0, i1, j0, j1 = blk
    P = {}
    for j, v in enumerate(vs):
        for i, u in enumerate(us):
            if i0 < i < i1 and j0 < j < j1:
                continue
            P[i, j] = (u, v, 0.0)
    ring_ij = ([(i1, j) for j in range(j0, j1)] + [(i, j1) for i in range(i1, i0, -1)]
               + [(i0, j) for j in range(j1, j0, -1)] + [(i, j0) for i in range(i0, i1)])
    cu, cv = (us[i0] + us[i1]) / 2, (vs[j0] + vs[j1]) / 2
    hu, hv = (us[i1] - us[i0]) / 2, (vs[j1] - vs[j0]) / 2
    nb = len(ring_ij)
    u0, v0 = P[ring_ij[0]][:2]
    a0 = math.atan2(v0 - cv, u0 - cu)

    def pos(k, r, z):
        if shape == "circle":
            a = a0 + 2 * math.pi * k / nb
            return (cu + r * math.cos(a), cv + r * math.sin(a), z)
        u, v = us[ring_ij[k][0]], vs[ring_ij[k][1]]
        return (cu + (u - cu) * r, cv + (v - cv) * r, z)

    made = set()
    for k, ij in enumerate(ring_ij):
        P[ij] = pos(k, rings[0][0], 0.0)
        made.add(P[ij])
    quads = []
    for j in range(len(vs) - 1):
        for i in range(len(us) - 1):
            if i0 <= i < i1 and j0 <= j < j1:
                continue
            quads.append([P[i, j], P[i + 1, j], P[i + 1, j + 1], P[i, j + 1]])
    prev = [P[ij] for ij in ring_ij]
    for r, z in rings[1:]:
        cur = [pos(k, r, z) for k in range(nb)]
        made.update(cur)
        for k in range(nb):
            quads.append([prev[k], prev[(k + 1) % nb], cur[(k + 1) % nb], cur[k]])
        prev = cur
    if cap:
        r, z = rings[-1]
        C = dict(zip(ring_ij, prev))
        for j in range(j0 + 1, j1):
            for i in range(i0 + 1, i1):
                s, t = (us[i] - cu) / hu, (vs[j] - cv) / hv
                if shape == "circle":
                    p = (cu + r * s * math.sqrt(1 - t * t / 2), cv + r * t * math.sqrt(1 - s * s / 2), z)
                else:
                    p = (cu + (us[i] - cu) * r, cv + (vs[j] - cv) * r, z)
                C[i, j] = p
                made.add(p)
        for j in range(j0, j1):
            for i in range(i0, i1):
                quads.append([C[i, j], C[i + 1, j], C[i + 1, j + 1], C[i, j + 1]])
    return quads, made


def even(n, a, b):
    return [a + (b - a) * k / n for k in range(n + 1)]


def tube(soup, rings):
    """Quads between consecutive closed rings of points."""
    for lo, hi in zip(rings, rings[1:]):
        n = len(lo)
        for k in range(n):
            soup.add([lo[k], lo[(k + 1) % n], hi[(k + 1) % n], hi[k]])


def box_grid(soup, xs, ys, zs, skip=None):
    """The six sides of a box gridded at xs, ys, zs; skip(i, j) drops top cells."""
    X, Y, Z = len(xs) - 1, len(ys) - 1, len(zs) - 1
    for j in range(Y):
        for k in range(Z):
            soup.add([(xs[-1], ys[j], zs[k]), (xs[-1], ys[j + 1], zs[k]), (xs[-1], ys[j + 1], zs[k + 1]), (xs[-1], ys[j], zs[k + 1])])
            soup.add([(xs[0], ys[j], zs[k]), (xs[0], ys[j], zs[k + 1]), (xs[0], ys[j + 1], zs[k + 1]), (xs[0], ys[j + 1], zs[k])])
    for i in range(X):
        for k in range(Z):
            soup.add([(xs[i], ys[-1], zs[k]), (xs[i], ys[-1], zs[k + 1]), (xs[i + 1], ys[-1], zs[k + 1]), (xs[i + 1], ys[-1], zs[k])])
            soup.add([(xs[i], ys[0], zs[k]), (xs[i + 1], ys[0], zs[k]), (xs[i + 1], ys[0], zs[k + 1]), (xs[i], ys[0], zs[k + 1])])
    for i in range(X):
        for j in range(Y):
            if not (skip and skip(i, j)):
                soup.add([(xs[i], ys[j], zs[-1]), (xs[i + 1], ys[j], zs[-1]), (xs[i + 1], ys[j + 1], zs[-1]), (xs[i], ys[j + 1], zs[-1])])
            soup.add([(xs[i], ys[j], zs[0]), (xs[i], ys[j + 1], zs[0]), (xs[i + 1], ys[j + 1], zs[0]), (xs[i + 1], ys[j], zs[0])])


def bevelled(segments, profile, width):
    bm = cube_bm()
    bmesh.ops.bevel(bm, geom=list(bm.edges), offset=width, offset_type="OFFSET",
                    profile_type="SUPERELLIPSE", segments=segments, profile=profile,
                    affect="EDGES", clamp_overlap=True)
    return bm


def support_bevel(bm, edges, width):
    bmesh.ops.bevel(bm, geom=edges, offset=width, offset_type="OFFSET",
                    profile_type="SUPERELLIPSE", segments=2, profile=1.0,
                    affect="EDGES", clamp_overlap=True)


def sharp_edges(bm, angle=0.5):
    return [e for e in bm.edges if len(e.link_faces) == 2 and
            e.link_faces[0].normal.angle(e.link_faces[1].normal) > angle]


def pl_corners():
    key = "pl_corner_support"
    if want(key):
        reset()
        cage = obj_from_bm(key, bevelled(2, 1.0, 0.12))
        shoot_tile(key, cage, (1.0, -1.0, 1.15), (0.9, -0.9, 0.88), 1.0)
    key = "pl_corner_round"
    if want(key):
        reset()
        cage = obj_from_bm(key, bevelled(4, 0.5, 0.55))
        shoot_tile(key, cage, (1.0, -1.0, 1.15), (0.72, -0.72, 0.68), 1.75)
    key = "pl_corner_odd"
    if want(key):
        reset()
        cage = obj_from_bm(key, bevelled(3, 0.5, 0.55))
        shoot_tile(key, cage, (1.0, -1.0, 1.15), (0.72, -0.72, 0.68), 1.75)
    key = "pl_chamfer_tri"
    if want(key):
        reset()
        bm = bevelled(1, 0.5, 0.45)
        support_bevel(bm, sharp_edges(bm, 0.3), 0.05)
        cage = obj_from_bm(key, bm)
        shoot_tile(key, cage, (1.0, -1.0, 1.15), (0.8, -0.8, 0.86), 1.5)
    key = "pl_chamfer_quad"
    if want(key):
        reset()
        # 2 segments, Shape 1, then the middle loop pulled flat: a chamfer whose
        # corner is three quads instead of a triangle
        w = 0.45
        bm = bevelled(2, 1.0, w)
        for v in bm.verts:
            big = [i for i in range(3) if abs(abs(v.co[i]) - 1) < 1e-6]
            if len(big) == 2:
                for i in big:
                    v.co[i] = math.copysign(1 - w / 2, v.co[i])
            elif len(big) == 3:
                for i in big:
                    v.co[i] = math.copysign(1 - 2 * w / 3, v.co[i])
        bm.normal_update()
        support_bevel(bm, sharp_edges(bm, 0.3), 0.05)
        cage = obj_from_bm(key, bm)
        shoot_tile(key, cage, (1.0, -1.0, 1.15), (0.8, -0.8, 0.86), 1.5)
    key = "pl_inside_corner"
    if want(key):
        reset()
        # an L-shaped block; the top and bottom are cut into two quads along
        # the diagonal from the inside corner, then every hard edge gets support loops
        bm = bmesh.new()
        L = [(-1, -1), (1, -1), (1, 0), (0, 0), (0, 1), (-1, 1)]
        bot = [bm.verts.new((x, y, -0.4)) for x, y in L]
        top = [bm.verts.new((x, y, 0.4)) for x, y in L]
        bm.faces.new(top)
        bm.faces.new(bot[::-1])
        n = len(L)
        for k in range(n):
            bm.faces.new([bot[k], bot[(k + 1) % n], top[(k + 1) % n], top[k]])
        bmesh.ops.connect_verts(bm, verts=[top[0], top[3]])
        bmesh.ops.connect_verts(bm, verts=[bot[0], bot[3]])
        bm.normal_update()
        support_bevel(bm, sharp_edges(bm), 0.08)
        cage = obj_from_bm(key, bm)
        shoot_tile(key, cage, (0.8, -1.0, 1.1), (0.05, 0.1, -0.1), 3.0)


def wrap_pipe(R, h_top=None):
    """(u, v, z) on a flat grid -> a pipe of radius R along x. Points off the
    surface move straight along z, so a branch stays a straight cylinder."""
    def M(p):
        u, v, z = p
        a = v / R
        x, y, zc = u, R * math.sin(a), R * math.cos(a)
        if z > 0 and h_top:
            t = z / h_top
            return (x, y, (1 - t) * (zc + z) + t * (R + z))
        return (x, y, zc + z)
    return M


def prewarp(R, made):
    """Bend the feature's own points so a circle in (u, v) lands as a circle in
    plan view once the grid is rolled into a pipe."""
    def W(p):
        if p in made:
            u, v, z = p
            return (u, R * math.asin(max(-1, min(1, v / R))), z)
        return p
    return W


def pipe_with(nseg, nx, blk, rings, cap, R=1.0, h_top=None):
    seg = 2 * math.pi * R / nseg
    us = [(-nx / 2 + i) * seg for i in range(nx + 1)]
    vs = [(-nseg / 2 + j) * seg for j in range(nseg + 1)]
    quads, made = feature(us, vs, blk, rings, cap=cap)
    W, M = prewarp(R, made), wrap_pipe(R, h_top)
    s = Soup()
    for q in quads:
        s.add([M(W(p)) for p in q])
    return s


def pl_cylinders():
    key = "pl_pipe_wall"
    if want(key):
        reset()
        n, b = 9, 3
        us = even(n, -1.1, 1.1)
        lo = (n - b) // 2
        rs, rh = 0.42, 0.34
        quads, _ = feature(us, us, (lo, lo + b, lo, lo + b),
                           [(rs, 0), (rh, 0), (rh, 0.04), (rh, 0.4), (rh, 0.76), (rh, 0.8),
                            (rh - 0.04, 0.8), (rh - 0.1, 0.8), (rh - 0.1, 0.76), (rh - 0.1, 0.55)])
        s = Soup()
        for q in quads:
            s.add(q)
        cage = s.obj(key)
        shoot_tile(key, cage, (0.8, -1.2, 1.0), (0, 0, 0.3), 2.5, keep_corners=True)
    for key, b, rs, rh in (("pl_t_same", 4, 0.66, 0.56), ("pl_t_diff", 2, 0.36, 0.29)):
        if not want(key):
            continue
        reset()
        nseg, nx = 16, 12
        i0 = (nx - b) // 2
        j0 = (nseg - b) // 2
        h = 1.0
        rings = [(rs, 0), (rh, 0), (rh, 0.04), (rh, 0.5), (rh, h - 0.04), (rh, h), (rh - 0.04, h)]
        s = pipe_with(nseg, nx, (i0, i0 + b, j0, j0 + b), rings, cap=True, h_top=h)
        cage = s.obj(key)
        shoot_tile(key, cage, (0.9, -1.3, 0.9), (0, 0, 0.8), 3.7, keep_corners=True)
    key = "pl_hole_pipe"
    if want(key):
        reset()
        nseg, nx, b = 16, 12, 4
        i0, j0 = (nx - b) // 2, (nseg - b) // 2
        rs, rh, d = 0.66, 0.56, 0.12
        rings = [(rs, 0), (rh, 0), (rh, -0.03), (rh, -d + 0.03), (rh, -d)]
        s = pipe_with(nseg, nx, (i0, i0 + b, j0, j0 + b), rings, cap=False)
        cage = s.obj(key)
        shoot_tile(key, cage, (0.5, -1.0, 1.4), (0, 0, 0.45), 3.6, keep_corners=True)
    key = "pl_cyl_box"
    if want(key):
        reset()
        c = [-1, -0.93, -0.6, -0.3, 0, 0.3, 0.6, 0.93, 1]
        zs = [-0.6, -0.53, 0, 0.53, 0.6]
        s = Soup()
        box_grid(s, c, c, zs, skip=lambda i, j: 1 <= i < 7 and 1 <= j < 7)
        rs, rh, top = 0.62, 0.5, 0.6
        quads, _ = feature(c[1:8], c[1:8], (1, 5, 1, 5),
                           [(rs, 0), (rh, 0), (rh, 0.04), (rh, 0.5), (rh, 0.86), (rh, 0.9), (rh - 0.04, 0.9)],
                           cap=True)
        for q in quads:
            s.add([(u, v, z + top) for u, v, z in q])
        cage = s.obj(key)
        shoot_tile(key, cage, (0.9, -1.25, 0.95), (0, 0, 0.2), 3.0)
    for key, m in (("pl_elbow", 6), ("pl_elbow_few", 1)):
        if not want(key):
            continue
        reset()
        n, r, Rb = 12, 0.3, 0.75
        frames = []      # (centre, axis a, axis b) of each ring
        for z in (-0.9, -0.55, -0.2):
            frames.append(((0, 0, z), (1, 0, 0), (0, 1, 0)))
        for k in range(m + 1):
            t = (math.pi / 2) * k / m
            cx, cz = Rb - Rb * math.cos(t), Rb * math.sin(t)
            frames.append(((cx, 0, cz), (math.cos(t), 0, -math.sin(t)), (0, 1, 0)))
        for x in (Rb + 0.35, Rb + 0.7, Rb + 1.05):
            frames.append(((x, 0, Rb), (0, 0, -1), (0, 1, 0)))
        rings = []
        for (c0, a, b_) in frames:
            rings.append([tuple(c0[i] + r * (math.cos(2 * math.pi * k / n) * a[i] + math.sin(2 * math.pi * k / n) * b_[i])
                                for i in range(3)) for k in range(n)])
        s = Soup()
        tube(s, rings)
        cage = s.obj(key)
        shoot_tile(key, cage, (0.15, -1.0, 0.25), (0.45, 0, 0.2), 2.6, keep_corners=True)


def pl_surface():
    key = "pl_groove"
    if want(key):
        reset()
        # cross-section of a panel line: flat, support, edge, wall, floor, wall, edge, support, flat
        prof = [(-1.0, 0), (-0.6, 0), (-0.3, 0), (-0.15, 0), (-0.1, 0), (-0.1, -0.08),
                (-0.05, -0.12), (0.05, -0.12), (0.1, -0.08), (0.1, 0), (0.15, 0),
                (0.3, 0), (0.6, 0), (1.0, 0)]
        xs = even(8, -1, 1)
        s = Soup()
        for i in range(len(xs) - 1):
            for k in range(len(prof) - 1):
                (y0, z0), (y1, z1) = prof[k], prof[k + 1]
                s.add([(xs[i], y0, z0), (xs[i + 1], y0, z0), (xs[i + 1], y1, z1), (xs[i], y1, z1)])
        s.verts = bend(s.verts)
        cage = s.obj(key)
        shoot_tile(key, cage, (0.55, -0.9, 1.2), (0, 0, -0.1), 2.2, keep_corners=True)
    key = "pl_inset"
    if want(key):
        reset()
        us = even(8, -1, 1)
        quads, _ = feature(us, us, (2, 6, 3, 5),
                           [(1.12, 0), (1.0, 0), (1.0, -0.035), (1.0, -0.085), (1.0, -0.12), (0.95, -0.12)],
                           shape="square", cap=True)
        s = Soup()
        for q in quads:
            s.add(q)
        cage = s.obj(key)
        shoot_tile(key, cage, (0.5, -1.0, 1.3), (0, 0, -0.05), 2.4, keep_corners=True)
    key = "pl_boss_curve"
    if want(key):
        reset()
        n, b = 12, 4
        us = even(n, -1, 1)
        lo = (n - b) // 2
        rs, rh = 0.42, 0.33
        quads, _ = feature(us, us, (lo, lo + b, lo, lo + b),
                           [(rs, 0), (rh, 0), (rh, 0.035), (rh, 0.22), (rh, 0.25), (rh - 0.04, 0.25)], cap=True)
        s = Soup()
        for q in quads:
            s.add(q)
        s.verts = bend(s.verts)
        cage = s.obj(key)
        shoot_tile(key, cage, (0.55, -1.0, 1.0), (0, 0, -0.05), 2.4, keep_corners=True)
    key = "pl_circle_sphere"
    if want(key):
        reset()
        # a cube gridded 6 x 6, its top block of 4 x 4 made round with a support
        # ring, then the whole cage pushed onto a sphere
        c = even(6, -1, 1)
        s = Soup()
        box_grid(s, c, c, c, skip=lambda i, j: True)
        quads, _ = feature(c, c, (1, 5, 1, 5), [(0.76, 0), (0.62, 0)], cap=True)
        for q in quads:
            s.add([(u, v, 1.0) for u, v, z in q])
        s.verts = [v.normalized() for v in s.verts]
        cage = s.obj(key)
        shoot_tile(key, cage, (0.25, -0.75, 1.0), (0, 0, 0), 2.85)
    key = "pl_capsule"
    if want(key):
        reset()
        # a gridded box whose ends are pushed onto half spheres: all quads,
        # the eight 3-edge poles sit on the round ends
        c = even(4, -1, 1)
        H = 1.2
        zs = [-H - 1, -H - 0.5, -H, -0.8, -0.4, 0, 0.4, 0.8, H, H + 0.5, H + 1]
        s = Soup()
        box_grid(s, c, c, zs)
        out = []
        for p in s.verts:
            if abs(p.z) > H + 1e-6:
                cz = math.copysign(H, p.z)
                q = Vector((p.x, p.y, p.z - cz)).normalized()
                out.append(Vector((q.x, q.y, q.z + cz)))
            else:
                q = Vector((p.x, p.y, 0)).normalized()
                out.append(Vector((q.x, q.y, p.z)))
        s.verts = [Vector((v.z, v.y, -v.x)) for v in out]      # lie it down along x
        cage = s.obj(key)
        shoot_tile(key, cage, (0.35, -1.0, 0.6), (0, 0, 0), 5.0)


def pattern_library():
    pl_corners()
    pl_cylinders()
    pl_surface()


def print_modifier_options():
    reset()
    o = obj_from_bm("probe", cube_bm())
    m = o.modifiers.new("sub", "SUBSURF")
    for p in m.bl_rna.properties:
        if p.identifier in {"rna_type"}:
            continue
        extra = ""
        if p.type == "ENUM":
            extra = " " + str([(i.identifier, i.name) for i in p.enum_items])
        print(f"SUBSURF {p.identifier!r} name={p.name!r}{extra}")
    for p in bpy.ops.wm.usd_export.get_rna_type().properties:
        if "subdiv" in p.identifier.lower():
            extra = str([(i.identifier, i.name) for i in p.enum_items]) if p.type == "ENUM" else ""
            print(f"USD {p.identifier!r} name={p.name!r} {extra}")


if __name__ == "__main__":
    if ONLY and "probe" in ONLY:
        print_modifier_options()
    else:
        ex_support()
        ex_levels()
        ex_ngon()
        ex_sphere()
        ex_holes()
        ex_caps()
        pattern_library()
    print("DONE")
