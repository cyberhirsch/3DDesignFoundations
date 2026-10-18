"""Build topology.html: the SubD topology cheat sheet.

  python _topology/build_page.py

The renders come from build_renders.py (run that first, in Blender). The
pattern diagrams are drawn here from vertex lists; every face is checked
(quad, convex, counter-clockwise) and every pole is counted, so a drawing
can't show a pattern that doesn't close.
"""
import math
import os
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = "img/topology"


# ---------------------------------------------------------------- diagrams

def check(name, verts, faces, allow=()):
    for f in faces:
        if len(f) != 4 and name not in allow:
            raise ValueError(f"{name}: face {f} has {len(f)} sides")
        area = 0.0
        n = len(f)
        for i in range(n):
            x1, y1 = verts[f[i]]
            x2, y2 = verts[f[(i + 1) % n]]
            area += x1 * y2 - x2 * y1
        if area <= 0:
            raise ValueError(f"{name}: face {f} is clockwise or degenerate")
        for i in range(n):
            ax, ay = verts[f[i]]
            bx, by = verts[f[(i + 1) % n]]
            cx, cy = verts[f[(i + 2) % n]]
            if (bx - ax) * (cy - by) - (by - ay) * (cx - bx) < -1e-9:
                raise ValueError(f"{name}: face {f} is not convex")
    edges = Counter()
    for f in faces:
        for i in range(len(f)):
            edges[frozenset((f[i], f[(i + 1) % len(f)]))] += 1
    if any(c > 2 for c in edges.values()):
        raise ValueError(f"{name}: an edge has more than two faces")
    return edges


def valence(edges):
    v = defaultdict(int)
    boundary = set()
    for e, c in edges.items():
        for i in e:
            v[i] += 1
        if c == 1:
            boundary.update(e)
    return v, boundary


def svg(name, verts, faces, w=220, pad=0.18, poles=None, accent_edges=(), accent_faces=(),
        labels=(), allow=(), title=""):
    edges = check(name, verts, faces, allow)
    val, boundary = valence(edges)
    if poles is None:
        poles = [i for i in val if i not in boundary and val[i] != 4]
    # labels count towards the bounds, so they never spill out of the drawing
    xs = [p[0] for p in verts] + [x for x, _, _ in labels]
    ys = [p[1] for p in verts] + [y + d for _, y, _ in labels for d in (-0.12, 0.12)]
    minx, maxx, miny, maxy = min(xs) - pad, max(xs) + pad, min(ys) - pad, max(ys) + pad
    s = w / (maxx - minx)
    h = (maxy - miny) * s

    def P(i):
        x, y = verts[i]
        return (x - minx) * s, (maxy - y) * s

    out = [f'<svg class="dg" viewBox="0 0 {w:.0f} {h:.0f}" width="{w:.0f}" height="{h:.0f}" role="img" aria-label="{title}">']
    for k, f in enumerate(faces):
        cls = "f hi" if k in accent_faces else "f"
        pts = " ".join(f"{P(i)[0]:.1f},{P(i)[1]:.1f}" for i in f)
        out.append(f'<polygon class="{cls}" points="{pts}"/>')
    acc = {frozenset(e) for e in accent_edges}
    for e in edges:
        a, b = tuple(e)
        (x1, y1), (x2, y2) = P(a), P(b)
        cls = "e hi" if e in acc else "e"
        out.append(f'<line class="{cls}" x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}"/>')
    for i in poles:
        x, y = P(i)
        n = val[i]
        cls = "p3" if n == 3 else "p5" if n == 5 else "p6"
        out.append(f'<circle class="{cls}" cx="{x:.1f}" cy="{y:.1f}" r="5.5"><title>{n} edges</title></circle>')
    for (x, y, text) in labels:
        px, py = (x - minx) * s, (maxy - y) * s
        out.append(f'<text x="{px:.1f}" y="{py:.1f}">{text}</text>')
    out.append("</svg>")
    return "".join(out)


def star(n):
    rb = {3: 1.35, 4: math.sqrt(2), 5: 1.25, 6: 1.15}[n]
    verts = [(0.0, 0.0)]
    for i in range(n):
        a = math.pi / 2 + 2 * math.pi * i / n
        verts.append((math.cos(a), math.sin(a)))
    for i in range(n):
        a = math.pi / 2 + 2 * math.pi * (i + 0.5) / n
        verts.append((rb * math.cos(a), rb * math.sin(a)))
    faces = []
    for i in range(n):
        s0, s1, b = 1 + i, 1 + (i + 1) % n, 1 + n + i
        faces.append([0, s0, b, s1])
    return verts, faces


def poles_row():
    names = {3: "3 edges", 4: "4 edges: regular", 5: "5 edges", 6: "6 or more"}
    cells = []
    for n in (3, 4, 5, 6):
        v, f = star(n)
        cells.append(f'<figure class="dgc">{svg(f"star{n}", v, f, w=150, poles=[0] if n != 4 else [], title=names[n])}'
                     f'<figcaption>{names[n]}</figcaption></figure>')
    return '<div class="dgrow">' + "".join(cells) + "</div>"


def reductions():
    out = []
    # 2 -> 1: the extra loop leaves to the side
    v = [(0, 0), (1, 0), (2, 0), (0, 1), (1, 1), (0, 2), (2, 2)]
    f = [[0, 1, 4, 3], [1, 2, 6, 4], [3, 4, 6, 5]]
    out.append(("2 → 1", svg("r21", v, f, w=170, accent_edges=[(3, 4), (4, 6)],
                            labels=[(1, -0.42, "2"), (1, 2.25, "1")], title="Two to one reduction"),
                "Two rows become one. The loop in blue turns away to the side, so this one needs room next to it."))
    # 3 -> 1
    v = [(0, 0), (1, 0), (2, 0), (3, 0), (1, 1), (2, 1), (0, 2), (3, 2)]
    f = [[0, 1, 4, 6], [1, 2, 5, 4], [2, 3, 7, 5], [4, 5, 7, 6]]
    out.append(("3 → 1", svg("r31", v, f, w=200, accent_edges=[(4, 5)],
                            labels=[(1.5, -0.42, "3"), (1.5, 2.25, "1")], title="Three to one reduction"),
                "Three edges in, one out, all quads. Two 3-edge poles; the middle loop ends between them."))
    # 4 -> 2
    v = [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0), (1, 1), (2, 1), (3, 1), (0, 2), (2, 2), (4, 2)]
    f = [[0, 1, 5, 8], [1, 2, 6, 5], [2, 3, 7, 6], [3, 4, 10, 7], [8, 5, 6, 9], [9, 6, 7, 10]]
    out.append(("4 → 2", svg("r42", v, f, w=230, accent_edges=[(5, 6), (6, 7)],
                            labels=[(2, -0.42, "4"), (2, 2.25, "2")], title="Four to two reduction"),
                "Halves the density across a whole row. For 8 → 4, see the pattern library."))
    cells = "".join(f'<figure class="dgc"><div class="dgt">{t}</div>{s}<figcaption>{c}</figcaption></figure>'
                    for t, s, c in out)
    return '<div class="dgrow red">' + cells + "</div>"


def loop_ring():
    nx, ny = 5, 3
    v = [(i, j) for j in range(ny + 1) for i in range(nx + 1)]
    idx = lambda i, j: j * (nx + 1) + i
    f = [[idx(i, j), idx(i + 1, j), idx(i + 1, j + 1), idx(i, j + 1)] for j in range(ny) for i in range(nx)]
    loop = [(idx(i, 1), idx(i + 1, 1)) for i in range(nx)]
    ring = [(idx(2, j), idx(3, j)) for j in range(ny + 1)]
    ring_faces = [j * nx + 2 for j in range(ny)]
    a = svg("loop", v, f, w=200, accent_edges=loop, poles=[], title="An edge loop")
    b = svg("ring", v, f, w=200, accent_edges=ring, accent_faces=ring_faces, poles=[], title="An edge ring")
    return ('<div class="dgrow">'
            f'<figure class="dgc">{a}<figcaption>Edge loop: edges end to end (Alt+click)</figcaption></figure>'
            f'<figure class="dgc">{b}<figcaption>Edge ring: parallel edges across faces (Ctrl+Alt+click)</figcaption></figure>'
            '</div>')


def inside_corner():
    d = 0.3
    V = {}
    def add(k, x, y):
        V[k] = len(V)
        pts.append((x, y))
    pts = []
    # outer L
    add("o0", 0, 0); add("o1", 2 - d, 0); add("o2", 4, 0); add("o3", 4, 2); add("C", 2, 2)
    add("o5", 2, 4); add("o6", 0, 4); add("o7", 0, 2 - d)
    # inner offset
    add("A", d, d); add("AB", 2 - d, d); add("B", 4 - d, d); add("Cc", 4 - d, 2 - d); add("S", 2 - d, 2 - d)
    add("E", 2 - d, 4 - d); add("F", d, 4 - d); add("AF", d, 2 - d)
    q = lambda *ks: [V[k] for k in ks]
    faces = [
        q("o0", "o1", "AB", "A"), q("o1", "o2", "B", "AB"),       # bottom strip
        q("o2", "o3", "Cc", "B"),                                 # right strip
        q("o3", "C", "S", "Cc"),                                  # strip into the corner
        q("C", "o5", "E", "S"),                                   # strip out of the corner
        q("o5", "o6", "F", "E"),                                  # top strip
        q("o6", "o7", "AF", "F"), q("o7", "o0", "A", "AF"),       # left strip
        q("A", "AB", "S", "AF"), q("AB", "B", "Cc", "S"), q("AF", "S", "E", "F"),
    ]
    return svg("corner", pts, faces, w=260, accent_edges=[(V["C"], V["S"])], poles=[V["S"]],
               title="Top face of an L-shaped part with support loops")


# ---------------------------------------------------------------- pattern library

def merge(parts):
    """Join (verts, faces) parts; vertices at the same spot become one."""
    verts, faces, key = [], [], {}
    for v, f in parts:
        m = []
        for p in v:
            k = (round(p[0], 6) + 0.0, round(p[1], 6) + 0.0)
            if k not in key:
                key[k] = len(verts)
                verts.append((float(p[0]), float(p[1])))
            m.append(key[k])
        faces += [[m[i] for i in face] for face in f]
    return verts, faces


def at(verts, p):
    """Index of the vertex at point p."""
    for i, q in enumerate(verts):
        if abs(q[0] - p[0]) < 1e-6 and abs(q[1] - p[1]) < 1e-6:
            return i
    raise KeyError(p)


def path_edges(verts, pts):
    ids = [at(verts, p) for p in pts]
    return list(zip(ids, ids[1:]))


def moved(part, dx=0.0, dy=0.0, sx=1.0, sy=1.0):
    v, f = part
    return [(x * sx + dx, y * sy + dy) for x, y in v], f


def bilinear(a, b, c, d, s, t):
    return tuple(a[i] * (1 - s) * (1 - t) + b[i] * s * (1 - t) + c[i] * s * t + d[i] * (1 - s) * t
                 for i in range(2))


def patch(a, b, c, d, n=2):
    """A quad a-b-c-d (counter-clockwise) split n x n."""
    v, f, idx = [], [], {}
    for j in range(n + 1):
        for i in range(n + 1):
            idx[i, j] = len(v)
            v.append(bilinear(a, b, c, d, i / n, j / n))
    for j in range(n):
        for i in range(n):
            f.append([idx[i, j], idx[i + 1, j], idx[i + 1, j + 1], idx[i, j + 1]])
    return v, f


def grid_part(nx, ny, x0=0.0, y0=0.0, dx=1.0, dy=1.0):
    v = [(x0 + i * dx, y0 + j * dy) for j in range(ny + 1) for i in range(nx + 1)]
    f = [[j * (nx + 1) + i, j * (nx + 1) + i + 1, (j + 1) * (nx + 1) + i + 1, (j + 1) * (nx + 1) + i]
         for j in range(ny) for i in range(nx)]
    return v, f


R21 = ([(0, 0), (1, 0), (2, 0), (0, 1), (1, 1), (0, 2), (2, 2)],
       [[0, 1, 4, 3], [1, 2, 6, 4], [3, 4, 6, 5]])
R31 = ([(0, 0), (1, 0), (2, 0), (3, 0), (1, 1), (2, 1), (0, 2), (3, 2)],
       [[0, 1, 4, 6], [1, 2, 5, 4], [2, 3, 7, 5], [4, 5, 7, 6]])
R42 = ([(0, 0), (1, 0), (2, 0), (3, 0), (4, 0), (1, 1), (2, 1), (3, 1), (0, 2), (2, 2), (4, 2)],
       [[0, 1, 5, 8], [1, 2, 6, 5], [2, 3, 7, 6], [3, 4, 10, 7], [8, 5, 6, 9], [9, 6, 7, 10]])


def ring_pts(n, r, a0, c=(0.0, 0.0)):
    return [(c[0] + r * math.cos(a0 + 2 * math.pi * k / n), c[1] + r * math.sin(a0 + 2 * math.pi * k / n))
            for k in range(n)]


def grid_fill(k, rim=True):
    """A k x k grid whose border is a circle (Grid Fill of 4k edges), with a
    ring of quads around it standing for the rim."""
    v, f, idx = [], [], {}
    nb = 4 * k
    border = ([(k, j) for j in range(k)] + [(i, k) for i in range(k, 0, -1)]
              + [(0, j) for j in range(k, 0, -1)] + [(i, 0) for i in range(k)])
    circ = ring_pts(nb, 1.0, -math.pi / 4)
    pos = dict(zip(border, circ))
    for j in range(k + 1):
        for i in range(k + 1):
            if (i, j) in pos:
                p = pos[i, j]
            else:
                s, t = 2 * i / k - 1, 2 * j / k - 1
                p = (s * math.sqrt(1 - t * t / 2), t * math.sqrt(1 - s * s / 2))
            idx[i, j] = len(v)
            v.append(p)
    for j in range(k):
        for i in range(k):
            f.append([idx[i, j], idx[i + 1, j], idx[i + 1, j + 1], idx[i, j + 1]])
    if rim:
        outer = ring_pts(nb, 1.38, -math.pi / 4)
        o0 = len(v)
        v += outer
        b = [idx[p] for p in border]
        for m in range(nb):
            f.append([b[m], o0 + m, o0 + (m + 1) % nb, b[(m + 1) % nb]])
    return v, f


def grid_circle(b, extra=1):
    """A grid with its middle b x b block made round, a support ring, and a hole."""
    n = b + 2 * extra
    lo, hi = extra, extra + b
    v, f, idx = [], [], {}
    for j in range(n + 1):
        for i in range(n + 1):
            if lo < i < hi and lo < j < hi:
                continue
            idx[i, j] = len(v)
            v.append((i - n / 2, j - n / 2))
    for j in range(n):
        for i in range(n):
            if lo <= i < hi and lo <= j < hi:
                continue
            f.append([idx[i, j], idx[i + 1, j], idx[i + 1, j + 1], idx[i, j + 1]])
    border = ([(hi, j) for j in range(lo, hi)] + [(i, hi) for i in range(hi, lo, -1)]
              + [(lo, j) for j in range(hi, lo, -1)] + [(i, lo) for i in range(lo, hi)])
    nb = len(border)
    half = b / 2
    rs = half * 1.08 if b > 1 else 0.6
    rh = rs - (0.16 if b == 1 else 0.24)
    for p, q in zip(border, ring_pts(nb, rs, -math.pi / 4)):
        v[idx[p]] = q
    r0 = len(v)
    v += ring_pts(nb, rh, -math.pi / 4)
    bi = [idx[p] for p in border]
    for m in range(nb):
        f.append([bi[m], bi[(m + 1) % nb], r0 + (m + 1) % nb, r0 + m])
    return v, f


def rounded_rect(nx=4, ny=2, offsets=(0.55, 0.85)):
    v, f = grid_part(nx, ny)
    border = ([(i, 0) for i in range(nx)] + [(nx, j) for j in range(ny)]
              + [(i, ny) for i in range(nx, 0, -1)] + [(0, j) for j in range(ny, 0, -1)])
    rings = [[at(v, p) for p in border]]
    for d in offsets:
        cur = []
        for (x, y) in border:
            nxv = (-1 if x == 0 else 1 if x == nx else 0)
            nyv = (-1 if y == 0 else 1 if y == ny else 0)
            ln = math.hypot(nxv, nyv)
            cur.append(len(v))
            v.append((x + d * nxv / ln, y + d * nyv / ln))
        rings.append(cur)
    nb = len(border)
    for a, b in zip(rings, rings[1:]):
        for m in range(nb):
            f.append([b[m], b[(m + 1) % nb], a[(m + 1) % nb], a[m]])
    return v, f


def lib_svgs():
    """name -> svg markup for every planar pattern tile."""
    S = {}
    W = 160      # about the width a tile shows it at, so lines and dots keep their size

    S["r21"] = svg("pl_r21", *R21, w=W, accent_edges=[(3, 4), (4, 6)],
                   labels=[(1, -0.42, "2"), (1, 2.25, "1")], title="Two to one")
    S["r31"] = svg("pl_r31", *R31, w=W, accent_edges=[(4, 5)],
                   labels=[(1.5, -0.42, "3"), (1.5, 2.25, "1")], title="Three to one")
    S["r42"] = svg("pl_r42", *R42, w=W, accent_edges=[(5, 6), (6, 7)],
                   labels=[(2, -0.42, "4"), (2, 2.25, "2")], title="Four to two")
    v = [(0, 0), (1, 0), (2, 0), (3, 0), (0, 1), (1, 1), (2, 1), (0, 2), (1.5, 2), (3, 2)]
    f = [[0, 1, 5, 4], [4, 5, 8, 7], [1, 2, 6, 5], [2, 3, 9, 6], [5, 6, 9, 8]]
    S["r32"] = svg("pl_r32", v, f, w=W, accent_edges=[(4, 5), (5, 6)],
                   labels=[(1.5, -0.42, "3"), (1.5, 2.25, "2")], title="Three to two")
    v = [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0), (5, 0), (2, 1), (3, 1), (0, 2), (5 / 3, 2), (10 / 3, 2), (5, 2)]
    f = [[0, 1, 9, 8], [1, 2, 6, 9], [2, 3, 7, 6], [3, 4, 10, 7], [6, 7, 10, 9], [4, 5, 11, 10]]
    S["r53"] = svg("pl_r53", v, f, w=W, accent_edges=[(6, 7)],
                   labels=[(2.5, -0.42, "5"), (2.5, 2.25, "3")], title="Five to three")
    # 8 -> 4: a 3 -> 1, two plain columns, a mirrored 3 -> 1. (Two 4 -> 2 side
    # by side would leave a 6-edge pole on their shared top corner.)
    left = ([(0, 0), (1, 0), (2, 0), (3, 0), (0.9, 1), (1.7, 1), (0, 2), (2, 2), (4, 0), (4, 2)],
            [[0, 1, 4, 6], [1, 2, 5, 4], [2, 3, 7, 5], [4, 5, 7, 6], [3, 8, 9, 7]])
    right = ([(8 - x, y) for x, y in left[0]], [face[::-1] for face in left[1]])
    R84 = merge([left, right])
    v, f = R84
    acc = path_edges(v, [(0.9, 1), (1.7, 1)]) + path_edges(v, [(6.3, 1), (7.1, 1)])
    S["r84"] = svg("pl_r84", v, f, w=W, accent_edges=acc,
                   labels=[(4, -0.5, "8"), (4, 2.35, "4")], title="Eight to four")
    v, f = merge([R84, moved(R42, dy=2, sx=2)])
    S["density"] = svg("pl_density", v, f, w=W,
                       labels=[(4, -0.55, "8"), (4, 4.4, "2")], title="Eight to four to two")

    # N-pole: a square in three patches; one loop turns the corner
    A, E, B, C, D, H, P = (0, 0), (2, 0), (4, 0), (4, 4), (0, 4), (0, 2), (1.6, 1.6)
    v, f = merge([patch(A, E, P, H), patch(E, B, C, P), patch(P, C, D, H)])
    pts = [bilinear(E, B, C, P, 0.5, 0), bilinear(E, B, C, P, 0.5, 0.5), bilinear(E, B, C, P, 0.5, 1),
           bilinear(P, C, D, H, 0.5, 0.5), bilinear(P, C, D, H, 0.5, 1)]
    S["npole"] = svg("pl_npole", v, f, w=W, accent_edges=path_edges(v, pts), title="N-pole turning a loop")

    # E-pole: five patches around one vertex
    sv, sf = star(5)
    parts = [patch(*[sv[i] for i in face]) for face in sf]
    v, f = merge(parts)
    a, b, c, d = [sv[i] for i in sf[0]]
    a2, b2, c2, d2 = [sv[i] for i in sf[1]]
    pts = [bilinear(a, b, c, d, 1, 0.5), bilinear(a, b, c, d, 0.5, 0.5), bilinear(a, b, c, d, 0, 0.5),
           bilinear(a2, b2, c2, d2, 0.5, 0.5), bilinear(a2, b2, c2, d2, 0.5, 1)]
    S["epole"] = svg("pl_epole", v, f, w=W, accent_edges=path_edges(v, pts), title="E-pole")

    # Rotate Edge in a grid: two 3s and two 5s that cancel out
    v, f = grid_part(4, 3)
    g = lambda i, j: j * 5 + i
    h0, h1, h2, h3, h4, h5 = g(1, 1), g(2, 1), g(3, 1), g(3, 2), g(2, 2), g(1, 2)
    v[h1] = (2, 0.7)
    v[h4] = (2, 2.3)
    f = [q for q in f if q not in ([h0, h1, h4, h5], [h1, h2, h3, h4])]
    f += [[h0, h1, h2, h3], [h0, h3, h4, h5]]
    S["pair"] = svg("pl_pair", v, f, w=W, accent_edges=[(h0, h3)], title="Pole pairs")

    # poles on the curve or on the flat: a 4 -> 2 above three straight rows
    v, f = merge([grid_part(4, 2), moved(R42, dy=2), grid_part(2, 1, y0=4, dx=2)])
    rows = [k for k, q in enumerate(f) if max(v[i][1] for i in q) <= 2]
    cell = [k for k, q in enumerate(f) if 2 <= min(v[i][1] for i in q) and max(v[i][1] for i in q) <= 4]
    S["pole_curve"] = svg("pl_pole_curve", v, f, w=W, accent_faces=cell, title="Poles on the curve")
    S["pole_flat"] = svg("pl_pole_flat", v, f, w=W, accent_faces=rows, title="Poles on the flat part")

    # shapes cut into quads
    T = [(0, 0), (2, 0), (1, math.sqrt(3))]
    c = (1, math.sqrt(3) / 3)
    mid = lambda p, q: ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2)
    v = T + [mid(T[0], T[1]), mid(T[1], T[2]), mid(T[2], T[0]), c]
    S["tri"] = svg("pl_tri", v, [[0, 3, 6, 5], [3, 1, 4, 6], [6, 4, 2, 5]], w=W, title="Triangle as three quads")
    pent = ring_pts(5, 1.0, math.pi / 2)
    v = pent + [mid(pent[k], pent[(k + 1) % 5]) for k in range(5)] + [(0, 0)]
    f = [[k, 5 + k, 10, 5 + (k - 1) % 5] for k in range(5)]
    S["pent"] = svg("pl_pent", v, f, w=W, title="Pentagon as five quads")
    hexa = ring_pts(6, 1.0, 0)
    S["hex"] = svg("pl_hex", hexa, [[0, 1, 2, 3], [3, 4, 5, 0]], w=W,
                   accent_edges=[(0, 3)], title="Hexagon as two quads")
    for k in (2, 3, 4):
        v, f = grid_fill(k)
        S[f"fill{4 * k}"] = svg(f"pl_fill{4 * k}", v, f, w=W, title=f"Grid Fill, {4 * k} sides")
    v, f = grid_fill(4)
    # the grid's 25 points come first, then the 16 rim points: the cut runs
    # from the first border point (grid point 4) out to the first rim point
    S["fill_odd"] = svg("pl_fill_odd", v, f, w=W, accent_edges=[(4, 25)],
                        labels=[(1.3, -1.2, "+1")], title="Odd edge count fixed")

    # circles from grids
    for b in (1, 2, 3, 4):
        v, f = grid_circle(b)
        S[f"circle{4 * b}"] = svg(f"pl_circle{4 * b}", v, f, w=W, title=f"Circle with {4 * b} segments")

    v, f = rounded_rect()
    S["rrect"] = svg("pl_rrect", v, f, w=W, title="Rounded rectangle")
    return S


def tile(group, t, verdict, media, cap):
    cls = {"good": " good", "bad": " bad"}[verdict]
    tag = {"good": '<span class="tag ok">Do</span>', "bad": '<span class="tag no">Avoid</span>'}[verdict]
    return (f'<figure class="pt{cls}"><span class="pk">{group}</span>'
            f'<figcaption class="pt-t">{tag}<b>{t}</b></figcaption>'
            f'<div class="pv">{media}</div><p>{cap}</p></figure>')


def render_tile(key, alt, img=IMG):
    return (f'<img src="{img}/{key}_subd.webp" width="360" height="270" loading="lazy" decoding="async" '
            f'alt="{alt}">')


def library(img=IMG, eager=False):
    S = lib_svgs()

    def R(key, alt):
        out = render_tile(key, alt, img)
        return out.replace(' loading="lazy"', "") if eager else out

    groups = [
        ("Reducing loops", [
            ("2 → 1", "good", S["r21"], "Two rows become one. The extra loop turns the corner and leaves at the side, so it needs room there."),
            ("3 → 1", "good", S["r31"], "Three in, one out. The middle loop ends between two 3-edge poles."),
            ("4 → 2", "good", S["r42"], "Halves a whole row. The workhorse for changing density."),
            ("3 → 2", "good", S["r32"], "An odd step: one loop comes in from the side and ends at a 3-edge pole."),
            ("5 → 3", "good", S["r53"], "A 3 → 1 in the middle, plain columns on both sides."),
            ("8 → 4", "good", S["r84"], "Two 3 → 1 with plain columns between. Two 4 → 2 side by side would leave a 6-edge pole where they meet."),
        ]),
        ("Poles", [
            ("N-pole turns a loop", "good", S["npole"], "Three patches meet at a 3-edge pole. The blue loop comes in at the bottom and leaves at the side."),
            ("E-pole", "good", S["epole"], "Five patches meet at a 5-edge pole; the blue loop bends round it. Typical where a form branches off."),
            ("Poles come in pairs", "good", S["pair"], "Edge &rarr; Rotate Edge CW on the blue edge: two 3s and two 5s. A 3 and a 5 cancel out, so the grid around stays regular."),
            ("Pole on the curve", "bad", S["pole_curve"], "The shaded band bends. A reduction there puts its poles right in the highlight."),
            ("Pole on the flat", "good", S["pole_flat"], "Same patch: the dense rows carry the curve, and the reduction sits on the flat part."),
        ]),
        ("Shapes into quads", [
            ("Triangle → 3 quads", "good", S["tri"], "A point in the middle and one on each edge. The middle becomes a 3-edge pole."),
            ("Pentagon → 5 quads", "good", S["pent"], "The same trick for 5 sides; the middle becomes a 5-edge pole."),
            ("6 sides → 2 quads", "good", S["hex"], "One cut across with Connect Vertex Path (" + k("J") + ")."),
            ("Grid Fill, 8 sides", "good", S["fill8"], "A 2&times;2 grid. Face &rarr; Grid Fill. Four 3-edge poles land on the rim."),
            ("Grid Fill, 12 sides", "good", S["fill12"], "A 3&times;3 grid, the same four 3-edge poles."),
            ("Grid Fill, 16 sides", "good", S["fill16"], "A 4&times;4 grid. The cap for a 16-sided cylinder."),
            ("Odd edge count", "good", S["fill_odd"], "15 edges can't be filled with quads. Add one cut (blue) through the whole ring for 16, then Grid Fill."),
        ]),
        ("Circles", [
            ("4 segments", "bad", S["circle4"], "One face can only give a square. It subdivides to a soft square, not a circle."),
            ("8 segments", "good", S["circle8"], "From a 2&times;2 block: the smallest hole that reads as round. The block's corners become 5-edge poles; keep them on the flat."),
            ("12 segments", "good", S["circle12"], "From a 3&times;3 block."),
            ("16 segments", "good", S["circle16"], "From a 4&times;4 block. Round enough for most props."),
            ("Circle on a curve", "good", R("pl_circle_sphere", "A circle with a support ring on a sphere"),
             "A 4&times;4 block on a cube made round, then the whole cage pushed onto a sphere."),
        ]),
        ("Corners", [
            ("Support-loop corner", "good", R("pl_corner_support", "A box corner with support loops"),
             "Bevel, Shape 1, 2 segments. The three loops meet in a 3-edge pole right on the corner."),
            ("Rounded corner", "good", R("pl_corner_round", "A rounded box corner in quads"),
             "Bevel, 4 segments, Shape 0.5. An even number of segments fills the corner with quads around one 3-edge pole."),
            ("Odd segments", "bad", R("pl_corner_odd", "A rounded corner with a triangle"),
             "3 segments leave a triangle in each corner: a pinch in the subdivision."),
            ("Chamfer, 1 segment", "bad", R("pl_chamfer_tri", "A chamfered corner with a triangle"),
             "A flat chamfer meets the other two in a triangle."),
            ("Chamfer in quads", "good", R("pl_chamfer_quad", "A chamfered corner made of quads"),
             "Bevel with 2 segments and flatten the middle loop: the corner is three quads. Then support loops."),
            ("Inside corner", "good", R("pl_inside_corner", "An L-shaped block with support loops"),
             "Cut the top along the diagonal from the inside corner before you bevel. All quads."),
        ]),
        ("Cylinders", [
            ("Pipe on a wall", "good", R("pl_pipe_wall", "A pipe rising from a flat plate"),
             "A 3&times;3 block made round (12 sides), Inset, then Extrude. Loops at the base and the lip."),
            ("T-joint, same count", "good", R("pl_t_same", "A T-joint of two 16-sided cylinders"),
             "A 4&times;4 block of a 16-sided pipe gives the 16 sides of the branch."),
            ("Branch, fewer sides", "good", R("pl_t_diff", "A thin 8-sided branch on a 16-sided pipe"),
             "A 2&times;2 block gives an 8-sided branch. The pipe's loops stay untouched."),
            ("Cylinder on a box", "good", R("pl_cyl_box", "A cylinder on top of a box"),
             "The box top is gridded so its middle 4&times;4 block can become the circle."),
            ("Elbow", "good", R("pl_elbow", "A tube bent through 90 degrees in even steps"),
             "Rings every 15&deg; through the bend, the same spacing as on the straight parts."),
            ("Elbow, too few rings", "bad", R("pl_elbow_few", "A tube bend with no rings in the bend"),
             "No rings in the bend: the inside pinches and the outside goes flat."),
        ]),
        ("Surface details", [
            ("Panel line", "good", R("pl_groove", "A groove across a curved panel"),
             "A groove is a strip of loops: support, edge, wall, floor, and the same back up."),
            ("Inset panel", "good", R("pl_inset", "A sunk rectangular panel in a plate"),
             "Inset (" + k("I") + ") the faces, Inset again for the support, then move them down."),
            ("Boss on a curve", "good", R("pl_boss_curve", "A round boss on a curved panel"),
             "The circle comes from the grid; extrude it and add loops at the base and the top."),
            ("Hole in a pipe", "good", R("pl_hole_pipe", "A round hole through a pipe wall"),
             "The same 4&times;4 block, deleted. A short wall down gives the hole its thickness."),
        ]),
        ("Density and flow", [
            ("8 → 4 → 2", "good", S["density"], "Stack reductions to go from dense to light over a flat area. Each row adds its poles; keep them off the curves."),
            ("Rounded rectangle", "good", S["rrect"], "Loops follow the outline. The four 3-edge poles sit at the inner corners, on the flat."),
            ("Capsule", "good", R("pl_capsule", "A capsule built from a box"),
             "A gridded box with its ends pushed round: all quads, the poles on the ends."),
        ]),
    ]
    tiles = [tile(name, *it) for name, items in groups for it in items]
    return '<div class="pl">' + "".join(tiles) + "</div>", len(tiles)


# ---------------------------------------------------------------- figures

def pic(key, which, alt):
    return (f'<img src="{IMG}/{key}_{which}.webp" width="720" height="540" loading="lazy" '
            f'alt="{alt}">')


def pair(key, title, note, refl=False, verdict=""):
    cls = {"good": " good", "bad": " bad", "": ""}[verdict]
    tag = {"good": '<span class="tag ok">Do</span>', "bad": '<span class="tag no">Avoid</span>', "": ""}[verdict]
    cols = [("cage", "Cage"), ("subd", "Subdivided, cage in blue")]
    if refl:
        cols.append(("refl", "Reflection check"))
    imgs = "".join(f'<div class="shot">{pic(key, w, f"{title.rstrip('.')}: {lab}")}<span>{lab}</span></div>' for w, lab in cols)
    n = len(cols)
    return (f'<figure class="ex{cls}"><figcaption><b>{tag}{title}</b> {note}</figcaption>'
            f'<div class="shots c{n}">{imgs}</div></figure>')


def strip(keys, labels, alt):
    cells = "".join(f'<div class="shot">{pic(k, "subd", f"{alt}: {l}")}<span>{l}</span></div>'
                    for k, l in zip(keys, labels))
    return f'<div class="shots c{len(keys)}">{cells}</div>'


def k(*keys):
    return '<span class="sep">+</span>'.join(f"<kbd>{x}</kbd>" for x in keys)


# ---------------------------------------------------------------- page

CSS = open(os.path.join(os.path.dirname(__file__), "topology.css"), encoding="utf-8").read()


def page():
    support = (
        pair("support_none", "No support loops.", "Six faces subdivide into a ball. The cage is a box; the result shrinks to whatever the cage can hold.")
        + pair("support_loose", "Loops far from the edge.", "A soft, pillowy edge: the wider the gap, the rounder the corner.")
        + pair("support_mid", "Loops close to the edge.", "A believable rounded edge, like moulded plastic or a sanded board.", verdict="good")
        + pair("support_tight", "Loops very close.", "Razor sharp. Looks fake in a render, catches no highlight, and every later edit fights the tiny faces.")
        + pair("support_crease", "Crease 1.0, no loops.", "Perfectly sharp with almost no geometry. Handy while blocking out, but only subdivision reads creases: game engines ignore them, so export loops, not creases.")
    )
    levels = strip(["levels_0", "levels_1", "levels_2", "levels_3"],
                   ["Level 0: the cage, shaded smooth", "Level 1", "Level 2", "Level 3"],
                   "The same cage at four subdivision levels")
    lib, n_lib = library()
    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>SubD Topology · 3D Design Foundations</title>
<meta name="description" content="Subdivision surface topology cheat sheet: support loops, poles, n-gons, holes, caps, loop reductions, corners and a pattern library of {n_lib} solved topology problems, each a real, checked mesh.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=Archivo:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap">
<style>
{CSS}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <a class="back" href="index.html">&larr; 3D Design Foundations</a>
    <h1>SubD topology</h1>
    <p class="standfirst">
      How to build a cage that subdivides cleanly. Every picture on this page is a real mesh: the
      cage on the left, the same mesh with a Subdivision Surface modifier on the right, and where it
      matters a reflection check that shows dents a plain render hides.
    </p>
    <p class="standfirst">Keys are Blender 5.2's. The full list is on the <a href="shortcuts.html">shortcuts page</a>.</p>
    <p class="poster-dl"><a href="#library">Pattern library</a>: {n_lib} solved problems on one page. Download the poster: <a href="{IMG}/topology_poster.png" download>PNG</a> &middot; <a href="{IMG}/topology_poster.pdf" download>PDF</a></p>
    <nav class="jump" aria-label="On this page">
      <a href="#rules">Maxims</a>
      <a href="#words">Words</a>
      <a href="#support">Support loops</a>
      <a href="#levels">Levels</a>
      <a href="#poles">Poles</a>
      <a href="#ngons">N-gons</a>
      <a href="#holes">Holes</a>
      <a href="#caps">Caps</a>
      <a href="#reduce">Reducing loops</a>
      <a href="#corners">Corners</a>
      <a href="#library">Pattern library</a>
      <a href="#check">Check</a>
      <a href="#fix">Fix</a>
    </nav>
  </header>

  <section id="rules">
    <h2>The 15 SubD modelling maxims</h2>
    <p class="lede">From Week 2. Prompts for judgement, not laws: run through them before you hand in.</p>
    <ol class="rules">
      <li><b>Start simple.</b> Begin with basic shapes and add detail progressively. One Subdivision Surface modifier on a low cage; a new loop ({k("Ctrl", "R")}) only when the silhouette asks for it.</li>
      <li><b>Maintain quad dominance.</b> Use quads as the primary geometry. <a href="#ngons">N-gons and triangles</a> become poles with dents around them.</li>
      <li><b>Use supporting edges for sharpness.</b> Avoid creasing. Bevel ({k("Ctrl", "B")}) with Shape 1 and 2 segments puts a loop on each side of the edge; apply the scale first ({k("Ctrl", "A")} &rarr; Scale). See <a href="#support">support loops</a>.</li>
      <li><b>Avoid long, thin polygons.</b> They subdivide into stretched, uneven curvature, and slivers are expensive to render. Support loops are the one exception.</li>
      <li><b>Check for non-manifold geometry.</b> Two solids that share only a vertex or an edge are non-manifold. Select &rarr; Select All by Trait &rarr; Non Manifold finds them.</li>
      <li><b>Keep polygon density consistent.</b> Avoid areas of dense or sparse detail. Change density with a <a href="#reduce">loop reduction</a>, not a triangle.</li>
      <li><b>Manage edge flow.</b> Ensure the edge flow complements the form: loops run along the curvature and around <a href="#holes">holes</a> and bosses. Parts that meet have the same number of edges where they meet; cylinders in multiples of 4 fit a grid.</li>
      <li><b>Avoid complex topology pitfalls.</b> Like triangles, n-gons and excessive <a href="#poles">poles</a>. A 3- or 5-edge pole is fine on a flat area; avoid 6 or more.</li>
      <li><b>Optimize for end use.</b> Tailor the level of detail to where the model goes. Viewport Overlays &rarr; Statistics counts the faces; see <a href="#levels">levels</a>.</li>
      <li><b>Work symmetrically.</b> Symmetry can halve your workload; don't forget radial symmetry. Mirror modifier with Clipping and Merge on; Array with an Object Offset for radial repeats.</li>
      <li><b>Check the subdivided state regularly.</b> It catches issues early. Flip levels with {k("Ctrl", "0")} and {k("Ctrl", "2")}, and turn the model under a <a href="#check">reflection matcap</a>.</li>
      <li><b>Stay organized and flexible.</b> Keep the workflow non-destructive: modifiers unapplied, objects named. Hand in with the Subdivision Surface modifier still on the stack.</li>
      <li><b>Isolate complex areas.</b> Model complex detail as a separate part, so the main body keeps its calm, even grid.</li>
      <li><b>Avoid boolean, unless you're prepared to retopo.</b> A boolean cut leaves n-gons and long triangles; rebuild the hole from a <a href="#holes">grid circle</a>.</li>
      <li><b>Use reference images.</b> Collect them in one place, for example in PureRef. Add &rarr; Image &rarr; Reference puts a photo into the viewport.</li>
    </ol>
  </section>

  <section id="words">
    <h2>Words</h2>
    <table class="words">
      <tbody>
        <tr><td>Cage</td><td>The low-poly mesh you edit. The subdivided surface lies inside it.</td></tr>
        <tr><td>Subdivision surface</td><td>Splits every quad into four and smooths, again at every level (Catmull-Clark). Blender's modifier: Subdivision Surface, {k("Ctrl", "1")} to {k("Ctrl", "3")}.</td></tr>
        <tr><td>Edge loop</td><td>Edges joined end to end through 4-edge vertices, around the form or until they hit a pole.</td></tr>
        <tr><td>Edge ring</td><td>The parallel edges across a strip of faces. A loop cut adds a loop across a ring.</td></tr>
        <tr><td>Support loop</td><td>Also holding or control loop: a loop next to an edge that keeps it from rounding off.</td></tr>
        <tr><td>Pole</td><td>A vertex with other than four edges. 3 edges: an N-pole; 5 edges: an E-pole.</td></tr>
        <tr><td>N-gon</td><td>A face with more than four sides.</td></tr>
        <tr><td>Crease</td><td>A sharpness value on an edge ({k("Shift", "E")}) that the Subdivision Surface modifier reads.</td></tr>
        <tr><td>Edge flow</td><td>The direction the loops run. Good flow follows the shape.</td></tr>
      </tbody>
    </table>
    {loop_ring()}
  </section>

  <section id="support">
    <h2>Support loops</h2>
    <p class="lede">The same 2 m cube, five ways. Add loops with Bevel ({k("Ctrl", "B")}, Shape 1, 2 segments), Loop Cut ({k("Ctrl", "R")}) or Edge &rarr; Offset Edge Slide ({k("Ctrl", "Shift", "R")}).</p>
    {support}
    <p class="note">Real objects are rarely razor sharp. Pick the loop distance from the real edge: a few millimetres on a phone, a centimetre on a table top. Keep that distance the same everywhere on one object.</p>
  </section>

  <section id="levels">
    <h2>Levels</h2>
    {levels}
    <p class="note">Each level splits every face into four: this cage has 54 faces, then 216, 864 and 3,456. Model at Levels Viewport 1 or 2, render at 2 or 3. In the modifier, Optimal Display shows only the cage's edges on the result.</p>
  </section>

  <section id="poles">
    <h2>Poles</h2>
    {poles_row()}
    <p class="lede">Every mesh that isn't a flat grid has poles: a cube has eight 3-edge corners. They are fine where the surface is flat and calm. On a curve they leave a dent or a ripple you will see in every highlight.</p>
    {pair("sphere_uv", "UV sphere.", "The top is a fan of 16 triangles meeting in a 16-edge pole. The stripes ripple around it.", refl=True, verdict="bad")}
    {pair("sphere_quad", "Quad sphere.", "A subdivided cube pushed into a sphere: all quads, eight 3-edge poles, and the stripes run clean.", refl=True, verdict="good")}
    <p class="note">Move a pole by sliding loops ({k("G", "G")}), by dissolving an edge ({k("Ctrl", "X")}) and cutting a new one with the Knife ({k("K")}), or by rotating edges (Edge &rarr; Rotate Edge CW). Aim for flat areas, the underside, or behind another part.</p>
  </section>

  <section id="ngons">
    <h2>N-gons and triangles</h2>
    {pair("ngon_top", "One n-gon on top.", "The same cube with the top's support faces dissolved into one 12-sided face. The subdivision turns it into a fan around a 12-edge pole: the reflection shows a star.", refl=True, verdict="bad")}
    {pair("quad_top", "All quads.", "The top keeps its loops. Flat stays flat, the edges stay even.", refl=True, verdict="good")}
    <p class="note">In this course every face going into the subdivision is a quad. Find the others with Select &rarr; Select All by Trait &rarr; Faces by Sides (Number of Vertices 4, Type Not Equal To). Turn triangle pairs into quads with {k("Alt", "J")}, and cut n-gons into quads with the Knife ({k("K")}) or Connect Vertex Path ({k("J")}).</p>
  </section>

  <section id="holes">
    <h2>Holes and bosses</h2>
    {pair("hole_boolean", "A boolean hole.", "A 16-sided hole in a curved panel, joined to the grid by four n-gons, as a Boolean modifier leaves it. The stripes break up where the n-gons meet the hole.", refl=True, verdict="bad")}
    {pair("hole_grid", "A grid circle.", "The same panel and the same 16-sided hole, but the middle 4&times;4 faces are made round, with a support loop around the rim. All quads: the stripes bend gently around the hole and stay smooth.", refl=True, verdict="good")}
    {pair("boss_grid", "A boss from the same circle.", "Extrude the circle up instead of deleting it: support loops at the base and the top, and the cap is the 16 quads that were already there.", verdict="good")}
    <p class="note">How: select a 4&times;4 block of faces (for 8 sides: 2&times;2), Mesh &rarr; Transform &rarr; To Sphere ({k("Shift", "Alt", "S")}), type 1. Inset ({k("I")}) for the support loop, then delete the faces for a hole or Extrude ({k("E")}) them for a boss. More segments need a bigger block: the rim has as many edges as the block's border.</p>
  </section>

  <section id="caps">
    <h2>Caps</h2>
    <p class="lede">The top of a 16-sided cylinder, three ways. All three have the same rim and support loops.</p>
    {pair("cap_ngon", "N-gon cap.", "One 16-sided face. It can't follow the dome, and the subdivision fans it into a star.", refl=True, verdict="bad")}
    {pair("cap_fan", "Triangle fan.", "Poke Faces gives a 16-edge pole in the middle: a pinch right where the light lands.", refl=True, verdict="bad")}
    {pair("cap_grid", "Grid cap.", "A 4&times;4 grid of quads in the middle, joined to the rim by a ring of quads. Inset (" + k("I") + ") the top once, delete the inner face, then Face &rarr; Grid Fill (Face menu: " + k("Ctrl", "F") + "). The stripes stay smooth.", refl=True, verdict="good")}
    <p class="note">Grid Fill needs an even number of edges around the opening. 16 segments give a 4&times;4 middle, 12 give 3&times;3, 8 give 2&times;2.</p>
  </section>

  <section id="reduce">
    <h2>Reducing loops</h2>
    <p class="lede">Dense where there is detail, light where it is flat: change density with these patterns instead of triangles. Each is all quads; the dots are the poles they create, so put them on flat areas.</p>
    {reductions()}
    <p class="legend"><span class="p3d"></span> 3 edges <span class="p5d"></span> 5 edges <span class="p6d"></span> 6 or more</p>
  </section>

  <section id="corners">
    <h2>Inside corners</h2>
    <div class="side">
      {inside_corner()}
      <div>
        <p class="lede">An inward corner, like a notch in a seat, needs its own topology; no Bevel miter setting fixes it.</p>
        <p class="note">Apply the bevel, then add a diagonal from the corner (blue). The two support strips meet on it, and the rest of the face is cut into quads that continue to the outer edges. The vertex at the end of the diagonal has 5 edges: keep the face around it flat.</p>
      </div>
    </div>
  </section>

  <section id="library">
    <h2>Pattern library</h2>
    <p class="lede">{n_lib} small problems and how to solve them in quads. Blue edges are the loop to watch, the dots are poles. The renders show the subdivided result with the cage in blue.</p>
    <p class="plegend"><span><i class="p3d"></i>3 edges</span><span><i class="p5d"></i>5 edges</span><span><i class="p6d"></i>6 or more</span><span><i class="hid"></i>Shaded: the part that curves</span></p>
    {lib}
  </section>

  <section id="check">
    <h2>Check before you hand in</h2>
    <table class="check">
      <thead><tr><th>Check</th><th>Where</th></tr></thead>
      <tbody>
        <tr><td>Only quads</td><td>Select &rarr; Select All by Trait &rarr; Faces by Sides (4, Not Equal To): nothing gets selected</td></tr>
        <tr><td>Face count</td><td>Viewport Overlays &rarr; Statistics</td></tr>
        <tr><td>Dents and ripples</td><td>Viewport Shading &rarr; Lighting: MatCap, the striped reflection matcap. Turn the model: the stripes should flow, not kink</td></tr>
        <tr><td>Shape of the result</td><td>Subdivision on, Optimal Display, Viewport Overlays &rarr; Wireframe</td></tr>
        <tr><td>No duplicate vertices</td><td>{k("M")} &rarr; By Distance</td></tr>
        <tr><td>Normals point out</td><td>Viewport Overlays &rarr; Face Orientation: blue outside; fix with {k("Shift", "N")}</td></tr>
        <tr><td>Scale applied</td><td>Sidebar ({k("N")}) &rarr; Item: Scale 1, 1, 1; else {k("Ctrl", "A")} &rarr; Scale</td></tr>
        <tr><td>Modifier live</td><td>Subdivision Surface still on the stack, Levels Viewport 1&ndash;2, Render 2&ndash;3</td></tr>
      </tbody>
    </table>
    <p class="note">The full list for each week is on the <a href="checklists.html">homework checklist</a>.</p>
  </section>

  <section id="fix">
    <h2>Fix it</h2>
    <table class="fix">
      <thead><tr><th>You see</th><th>Usually because</th><th>Fix</th></tr></thead>
      <tbody>
        <tr><td>Edges too round</td><td>No support loops, or too far away</td><td>Bevel or Loop Cut closer to the edge</td></tr>
        <tr><td>A star or a dimple</td><td>An n-gon or a pole on a curved face</td><td>Cut the n-gon into quads; move the pole to a flat area</td></tr>
        <tr><td>Ripples beside a hard edge</td><td>Support loops spaced unevenly, or a loop ending on the curve</td><td>Even the spacing; let the loop run all the way round</td></tr>
        <tr><td>A wobbly circle</td><td>Too few or uneven segments</td><td>8 or more, made round with To Sphere</td></tr>
        <tr><td>Pinch at a cylinder's centre</td><td>A triangle fan or n-gon cap</td><td>Grid Fill the cap</td></tr>
        <tr><td>Faceted or dark streaks</td><td>Flat shading or flipped normals</td><td>Shade Smooth; {k("Shift", "N")}</td></tr>
        <tr><td>A seam down the middle</td><td>Mirror without Clipping, centre vertices not merged</td><td>Mirror modifier: Clipping and Merge on</td></tr>
        <tr><td>Bevels of different widths</td><td>Unapplied scale</td><td>{k("Ctrl", "A")} &rarr; Scale, then bevel again</td></tr>
        <tr><td>The shape shrinks too much</td><td>Too few loops where the form turns</td><td>Add a loop to hold it, or move the cage out</td></tr>
        <tr><td>Stretched texture after subdividing</td><td>Uneven face sizes</td><td>Spread the loops evenly; UV Smooth in the modifier's Advanced panel</td></tr>
      </tbody>
    </table>
  </section>

  <section id="read">
    <h2>Read more</h2>
    <ul class="read">
      <li>Johnson Martin, <a href="https://topologyguides.com/loop-reduction">Optimal Edge Loop Reduction Flows</a> and <a href="https://topologyguides.com/manipulating-edge-poles">Moving and Manipulating Edge Poles</a>, Topology Guides.</li>
      <li>Johnson Martin, <a href="https://topologyguides.com/artifacts">Dealing with Mesh Artifacts in Subdivision Modeling</a>, Topology Guides.</li>
      <li>Blender 5.2 Manual: <a href="https://docs.blender.org/manual/en/latest/modeling/modifiers/generate/subdivision_surface.html">Subdivision Surface Modifier</a>, <a href="https://docs.blender.org/manual/en/latest/modeling/meshes/editing/face/grid_fill.html">Grid Fill</a>, <a href="https://docs.blender.org/manual/en/latest/modeling/meshes/editing/mesh/transform/to_sphere.html">To Sphere</a>.</li>
    </ul>
  </section>

  <footer>
    <p>3D Design Foundations &middot; Smart Interactive Media, TH Rosenheim &middot; Prof. Seb Hirsch</p>
    <p>Renders made in Blender 5.2 from meshes built by script, so the cage shown is exactly the mesh subdivided.</p>
  </footer>
</div>
</body>
</html>
"""
    return html


POSTER_CSS = """
body { background: var(--ground); }
.wrap { max-width: none; width: 1500px; padding: 56px 48px 40px; }
.phead { display: flex; justify-content: space-between; align-items: flex-end; gap: 40px; border-bottom: 1px solid var(--rule); padding-bottom: 22px; }
.phead h1 { font-size: 72px; margin: 0; }
.phead .standfirst { font-size: 17px; margin: 12px 0 0; max-width: 70ch; }
.phead .plegend { justify-content: flex-end; font-size: 13px; max-width: 420px; }
.pl { grid-template-columns: repeat(6, 1fr); gap: 12px; margin-top: 22px; }
.pt-t b { font-size: 16px; }
figure.pt p { font-size: 13px; }
.pfoot { display: flex; justify-content: space-between; margin-top: 22px; font-family: var(--mono); font-size: 12px; color: var(--ink-3); }
"""


def poster():
    lib, n = library(img="../" + IMG, eager=True)
    return f"""<!doctype html>
<html lang="en" data-theme="light">
<head>
<meta charset="utf-8">
<title>SubD Topology Patterns · Poster</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=Archivo:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap">
<style>
{CSS}
{POSTER_CSS}
</style>
</head>
<body>
<div class="wrap">
  <div class="phead">
    <div>
      <h1>SubD topology patterns</h1>
      <p class="standfirst">{n} solved problems for subdivision modelling. Quads only into the subdivision; poles on flat areas; support loops with Bevel, Shape 1, 2 segments. Every pattern is a real, checked mesh.</p>
    </div>
    <p class="plegend"><span><i class="p3d"></i>3 edges</span><span><i class="p5d"></i>5 edges</span><span><i class="p6d"></i>6 or more</span><span><i class="hid"></i>Shaded: the part that curves</span><span>Renders: subdivided, cage in blue</span></p>
  </div>
  {lib}
  <div class="pfoot"><span>3D Design Foundations &middot; Smart Interactive Media, TH Rosenheim &middot; Prof. Seb Hirsch</span><span>cyberhirsch.github.io/3DDesignFoundations/topology.html</span></div>
</div>
</body>
</html>
"""


if __name__ == "__main__":
    out = os.path.join(ROOT, "topology.html")
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(page())
    print("wrote", out)
    out = os.path.join(ROOT, "_topology", "poster.html")
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(poster())
    print("wrote", out, "(input for build_poster.py)")
