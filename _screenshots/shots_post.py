"""Crop, pair and compress the raw Blender screenshots into the site's images; write a contact sheet."""
import json, os
import numpy as np
from scipy import ndimage
from PIL import Image, ImageChops

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")
SITE = os.path.join(os.path.dirname(HERE), "img")
M = json.load(open(os.path.join(RAW, "meta.json")))
GAP = 16
BG = (29, 29, 29)
OUT = {}


def load(name):
    return Image.open(M[name]["file"]).convert("RGB")


def fit_aspect(box, aspect, w, h):
    l, t, r, b = box
    cx, cy = (l + r) / 2, (t + b) / 2
    bw, bh = r - l, b - t
    if bw / bh < aspect:
        bw = bh * aspect
    else:
        bh = bw / aspect
    bw, bh = min(bw, w), min(bh, h)
    l = max(0, min(cx - bw / 2, w - bw)); t = max(0, min(cy - bh / 2, h - bh))
    return [int(l), int(t), int(l + bw), int(t + bh)]


def crop(name, aspect=None, size=None):
    im = load(name)
    box = M[name]["box"] or [0, 0, im.width, im.height]
    box = fit_aspect(box, aspect, im.width, im.height) if aspect else [int(round(v)) for v in box]
    im = im.crop(box)
    if M[name].get("trim"):
        im = trim(im)
    if size:
        im = im.resize(size if isinstance(size, tuple) else (size, round(size * im.height / im.width)), Image.LANCZOS)
    return im


def trim(im, x0=0, x1=None, tol=8, margin=16):
    """Cut the empty editor background below the content (bg = commonest colour near the bottom)."""
    a = np.array(im).astype(int)
    x1 = x1 or im.width
    band = a[-40:-15, x0 + 20:x1 - 20].reshape(-1, 3)
    vals, counts = np.unique(band, axis=0, return_counts=True)
    bg = vals[np.argmax(counts)]
    rows = np.abs(a[:-8, x0 + 20:x1 - 20] - bg).max(axis=2).max(axis=1) > tol  # skip the area's border rows
    last = np.where(rows)[0]
    if not len(last):
        return im
    return im.crop((0, 0, im.width, min(im.height, int(last[-1]) + margin)))


def panel(name, bottom=None):
    """The whole Properties editor (tabs included), cut below the content."""
    im = load(name)
    if bottom:
        return im.crop((0, 0, im.width, bottom))
    reg = M[name]["regions"]["WINDOW"]; area = M[name]["area"]
    return trim(im, x0=reg[0] - area[0])


def diff_crop(name, pad=10, cap=720, largest=True):
    """Crop the popup that a key opened: the largest changed region between before and after."""
    a, b = load(name + "_before"), load(name)
    d = np.array(ImageChops.difference(a, b).convert("L")) > 12
    if largest:
        lab, n = ndimage.label(ndimage.binary_dilation(d, iterations=4))
        sizes = ndimage.sum(d, lab, range(1, n + 1))
        ys, xs = np.where(lab == int(np.argmax(sizes)) + 1)
    else:
        ys, xs = np.where(d)
    l, t, r, btm = xs.min(), ys.min(), xs.max(), ys.max()
    im = b.crop((max(0, l - pad), max(0, t - pad), min(b.width, r + pad), min(b.height, btm + pad)))
    if max(im.size) > cap:
        k = cap / max(im.size)
        im = im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)
    return im


def row(ims, gap=GAP):
    h = max(i.height for i in ims)
    out = Image.new("RGB", (sum(i.width for i in ims) + gap * (len(ims) - 1), h), (18, 18, 18))
    x = 0
    for i in ims:
        out.paste(i, (x, (h - i.height) // 2)); x += i.width + gap
    return out


def save(im, rel):
    path = os.path.join(SITE, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im.save(path, "WEBP", quality=82, method=6)
    OUT[rel] = im.size


S = "shortcuts/"
# single object shots, 3:2
for n in ["tab_edit", "bevel_edges", "bevel_verts", "loop_cut", "loop_center", "edge_slide", "knife", "extrude",
          "inset", "crease", "wireframe", "xray", "loop_select", "ring_select", "faces_by_sides", "grs"]:
    save(crop(n, 1.5, (480, 320)), S + n.replace("_", "-") + ".webp")
save(crop("subd_levels", 2.2, (616, 280)), S + "subd-levels.webp")
# before/after pairs
for n, (a, b) in {"shade-smooth": ("shade_flat", "shade_smooth"), "fill": ("fill_before", "fill_after"),
                  "tris-to-quads": ("tris_before", "tris_after"), "recalc-normals": ("normals_before", "normals_after"),
                  "clear-transforms": ("clear_before", "clear_after")}.items():
    save(row([crop(a, 1.5, (360, 240)), crop(b, 1.5, (360, 240))]), S + n + ".webp")
save(row([crop("select_" + k, 1.5, (300, 200)) for k in ("vert", "edge", "face")]), S + "select-modes.webp")
# whole-viewport shots
save(row([crop("frame_before", size=360), crop("frame_after", size=360)]), S + "frame-selected.webp")
save(row([crop("view_persp", size=360), crop("view_ortho", size=360)]), S + "persp-ortho.webp")
save(row([crop("local_before", size=360), crop("local_after", size=360)]), S + "local-view.webp")
save(crop("view_front", size=560), S + "view-axis.webp")
# navigation gizmo: top-right corner of the viewport
nav = load("navigate"); l, t, r, b = [int(v) for v in M["navigate"]["box"]]
save(nav.crop((r - 185, t + 118, r - 8, t + 548)), S + "navigate.webp")
# menus and popups
def top(im, frac):
    return im.crop((0, 0, im.width, round(im.height * frac)))


save(top(diff_crop("add_menu", cap=1600), 0.57), S + "add-menu.webp")      # Search… down to Lattice, Empty, Image
save(top(diff_crop("apply_menu", cap=1600), 0.395), S + "apply-menu.webp")  # Location … Rotation & Scale
save(diff_crop("rename"), S + "rename.webp")
save(top(diff_crop("search"), 0.5), S + "search.webp")
save(diff_crop("extrude_menu"), S + "extrude-menu.webp")
save(diff_crop("shading_pie", largest=False), S + "shading-pie.webp")
# outliner, sidebar, modifier panel
out = load("duplicate_outliner")
save(trim(out.crop((0, 0, out.width, min(out.height, 330)))), S + "duplicate.webp")
sb = crop("sidebar"); save(sb.crop((0, 0, sb.width, 790)), S + "sidebar.webp")  # the Transform panel; the sidebar is see-through below
save(panel("apply_modifier_panel"), S + "apply-modifier.webp")
# modifiers: view + panel
for n in ["solidify", "lattice", "screw", "curve_bevel", "mirror"]:
    save(crop("mod_%s_view" % n, 1.5, (720, 480)), "modifiers/%s-view.webp" % n.replace("_", "-"))
    save(panel("mod_%s_panel" % n, 880 if n == "curve_bevel" else None), "modifiers/%s-panel.webp" % n.replace("_", "-"))

json.dump(OUT, open(os.path.join(HERE, "sizes.json"), "w"), indent=1)
# contact sheet for review
ims = [(k, Image.open(os.path.join(SITE, k))) for k in OUT]
cols, cw = 4, 480
tiles = []
for k, im in ims:
    im = im.copy(); im.thumbnail((cw, 360))
    tiles.append(im)
rows = [tiles[i:i + cols] for i in range(0, len(tiles), cols)]
sheet_parts = [row(r, 8) for r in rows]
sheet = Image.new("RGB", (max(p.width for p in sheet_parts), sum(p.height + 8 for p in sheet_parts)), (60, 0, 60))
y = 0
for p in sheet_parts:
    sheet.paste(p, (0, y)); y += p.height + 8
sheet.save(os.path.join(HERE, "contact.png"))
for k, v in OUT.items():
    print(k, v)
