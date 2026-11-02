"""Build capture.html: the phone capture card for Weeks 4 and 8.

  python _capture/build_images.py   (once, makes img/capture/*.webp)
  python _capture/build_page.py

Content follows the Week 4 (photogrammetry) and Week 8 (Gaussian splatting)
decks, their homework in "3d Design Foundations Homework Assignments
(revised).md" and "Tool Tutorials.md". When one of those changes, change this.

The diagrams are drawn here from coordinates: the object rings are three
camera loops on one sphere (10, 32 and 58 degrees up, as in the Week 4
boombox capture), the place heights are the Week 8 rings (0.5, 1.2, 1.9 m).
"""
import html
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.dirname(os.path.abspath(__file__))
IMG = "img/capture"
CSS = open(os.path.join(HERE, "capture.css"), encoding="utf-8").read()

from PIL import Image  # noqa: E402  (only for image sizes)


def f(v):
    return f"{v:.1f}".rstrip("0").rstrip(".")


# ---------------------------------------------------------------- diagrams

def svg_object_rings():
    """Three camera loops round an object, seen from a little above."""
    W, H = 420, 240
    cx, gy, s, tilt = 175, 182, 100, 0.30
    D = 1.55
    rings = [("low", 10, 24), ("middle", 32, 24), ("high", 58, 16)]

    def P(x, y, z):
        return cx + x * s, gy - z * s - y * s * tilt

    back, front, rings_svg, labels = [], [], [], []
    for name, elev, n in rings:
        e = math.radians(elev)
        r, z = D * math.cos(e), D * math.sin(e)
        ex, ey = P(0, 0, z)
        rings_svg.append(f'<ellipse class="ring" cx="{f(ex)}" cy="{f(ey)}" rx="{f(r * s)}" ry="{f(r * s * tilt)}"/>')
        # object centre the cameras aim at
        tx, ty = P(0, 0, 0.22)
        for i in range(n):
            a = 2 * math.pi * (i + 0.5 * (name == "high")) / n + 0.13
            x, y = r * math.cos(a), r * math.sin(a)
            px, py = P(x, y, z)
            dx, dy = tx - px, ty - py
            L = math.hypot(dx, dy) or 1
            ax, ay = px + dx / L * 11, py + dy / L * 11
            cls = " back" if y > 0 else ""
            item = (f'<line class="aim{cls}" x1="{f(px)}" y1="{f(py)}" x2="{f(ax)}" y2="{f(ay)}"/>'
                    f'<circle class="cam{cls}" cx="{f(px)}" cy="{f(py)}" r="3.6"/>')
            (back if y > 0 else front).append(item)
        lx, ly = P(r, 0, z)
        labels.append(f'<text x="{f(lx + 12)}" y="{f(ly + 4)}">{name} · {n}</text>')

    # the object: a stump-like cylinder, radius 0.32, height 0.45
    R, Hh = 0.32, 0.45
    lx0, _ = P(-R, 0, 0)
    rx0, _ = P(R, 0, 0)
    _, by = P(0, 0, 0)
    _, tyy = P(0, 0, Hh)
    ry = R * s * tilt
    body = (f'<path class="obj" d="M{f(lx0)},{f(tyy)} L{f(lx0)},{f(by)} '
            f'A{f(R * s)},{f(ry)} 0 0 0 {f(rx0)},{f(by)} L{f(rx0)},{f(tyy)} Z"/>'
            f'<ellipse class="objtop" cx="{f(cx)}" cy="{f(tyy)}" rx="{f(R * s)}" ry="{f(ry)}"/>')
    # a ruler on the ground in front of it
    rp = [P(-1.0, -0.12, 0), P(-0.42, -0.2, 0), P(-0.42, -0.28, 0), P(-1.0, -0.2, 0)]
    ruler = '<polygon class="ruler" points="' + " ".join(f"{f(x)},{f(y)}" for x, y in rp) + '"/>'
    ticks = []
    for k in range(1, 6):
        t = k / 6
        x1 = rp[0][0] + (rp[1][0] - rp[0][0]) * t
        y1 = rp[0][1] + (rp[1][1] - rp[0][1]) * t
        ticks.append(f'<line class="tick" x1="{f(x1)}" y1="{f(y1)}" x2="{f(x1)}" y2="{f(y1 + 4)}"/>')
    gx, gyy = P(0, 0, 0)
    ground = f'<ellipse class="ground" cx="{f(gx)}" cy="{f(gyy)}" rx="{f(D * s * 1.08)}" ry="{f(D * s * 1.08 * tilt)}"/>'
    rl = P(-1.0, -0.2, 0)
    note = f'<text x="{f(rl[0] - 2)}" y="{f(rl[1] - 12)}">ruler</text>'

    return (f'<svg class="dg" viewBox="0 0 {W} {H}" role="img" '
            f'aria-label="An object with a ruler beside it, and camera positions on three loops: low, middle and high.">'
            + ground + "".join(rings_svg) + "".join(back) + body + ruler + "".join(ticks)
            + "".join(front) + "".join(labels) + note + "</svg>")


def cone(x, y, ang, half, length, cls="cone"):
    a1, a2 = math.radians(ang - half), math.radians(ang + half)
    p1 = (x + length * math.cos(a1), y + length * math.sin(a1))
    p2 = (x + length * math.cos(a2), y + length * math.sin(a2))
    return f'<polygon class="{cls}" points="{f(x)},{f(y)} {f(p1[0])},{f(p1[1])} {f(p2[0])},{f(p2[1])}"/>'


def cam(x, y, ang, cls="cam"):
    a = math.radians(ang)
    aim = "aim" + (" bad" if "bad" in cls else "")
    style = ' style="stroke:var(--bad)"' if "bad" in cls else ""
    return (f'<line class="{aim}"{style} x1="{f(x)}" y1="{f(y)}" x2="{f(x + 12 * math.cos(a))}" y2="{f(y + 12 * math.sin(a))}"/>'
            f'<circle class="{cls}" cx="{f(x)}" cy="{f(y)}" r="4.5"/>')


def svg_step_dont_turn():
    """Top view, two panels: turning on the spot against stepping round."""
    W, H = 420, 230
    out = [f'<svg class="dg" viewBox="0 0 {W} {H}" role="img" '
           f'aria-label="Seen from above. Left: one position, the phone turned: no depth. Right: the phone moved in steps round the subject, every picture overlapping the last.">']
    # left panel
    out.append('<text class="t" x="10" y="20">Turn on the spot</text>')
    sx, sy = 100, 150
    for ang in (-150, -120, -90, -60, -30):
        out.append(cone(sx, sy, ang, 16, 92, "cone bad"))
    out.append(cam(sx, sy, -90, "cam bad"))
    out.append(f'<line class="cross" x1="{sx - 9}" y1="{sy + 18}" x2="{sx + 9}" y2="{sy + 36}"/>'
               f'<line class="cross" x1="{sx + 9}" y1="{sy + 18}" x2="{sx - 9}" y2="{sy + 36}"/>')
    out.append(f'<text class="no" x="10" y="{H - 8}">one spot: no depth</text>')
    # right panel
    ox, oy = 320, 92
    out.append('<text class="t" x="222" y="20">Step round it</text>')
    out.append(f'<rect class="obj" x="{ox - 18}" y="{oy - 14}" width="36" height="28" rx="2"/>')
    R = 84
    angs = [200, 230, 260, 290, 320, 350]  # degrees round the subject, 30 apart
    for i, a in enumerate(angs):
        ar = math.radians(a)
        x, y = ox + R * math.cos(ar), oy - R * math.sin(ar)
        look = math.degrees(math.atan2(oy - y, ox - x))
        if i in (2, 3):
            out.append(cone(x, y, look, 20, 96, "cone hi"))
    for i, a in enumerate(angs):
        ar = math.radians(a)
        x, y = ox + R * math.cos(ar), oy - R * math.sin(ar)
        look = math.degrees(math.atan2(oy - y, ox - x))
        out.append(cam(x, y, look))
    # the path
    a0, a1 = math.radians(190), math.radians(360)
    p0 = (ox + R * math.cos(a0), oy - R * math.sin(a0))
    p1 = (ox + R * math.cos(a1), oy - R * math.sin(a1))
    out.insert(1, f'<path class="ring" d="M{f(p0[0])},{f(p0[1])} A{R},{R} 0 0 0 {f(p1[0])},{f(p1[1])}"/>')
    out.append(f'<text class="ok" x="222" y="{H - 8}">every step: a new angle</text>')
    out.append(f'<line class="line" x1="210" y1="34" x2="210" y2="{H - 4}"/>')
    out.append("</svg>")
    return "".join(out)


def svg_place_heights():
    """Side view: the three Week 8 ring heights, with a person for scale."""
    W, H = 420, 250
    gy, m = 222, 92  # ground line, pixels per metre
    out = [f'<svg class="dg" viewBox="0 0 {W} {H}" role="img" '
           f'aria-label="Side view: phone positions at 0.5, 1.2 and 1.9 metres, each looking into the place.">']
    out.append(f'<line class="line" x1="0" y1="{gy}" x2="{W}" y2="{gy}"/>')
    # the place: a table and a wall on the right
    out.append(f'<rect class="ground" x="330" y="{gy - 2.2 * m:.0f}" width="90" height="{2.2 * m:.0f}"/>')
    tx = 300
    out.append(f'<path class="obj" d="M{tx - 40},{f(gy - 0.75 * m)} h80 v6 h-80 Z"/>')
    out.append(f'<path class="fig" style="stroke:var(--ink)" d="M{tx - 34},{f(gy - 0.75 * m + 6)} V{gy} M{tx + 34},{f(gy - 0.75 * m + 6)} V{gy}"/>')
    rings = [("head", 1.9, 14), ("chest", 1.2, 4), ("knee", 0.5, -10)]
    camx = 112
    for name, h, tilt_down in rings:
        y = gy - h * m
        out.append(cone(camx, y, tilt_down, 17, 210))
    for name, h, tilt_down in rings:
        y = gy - h * m
        out.append(cam(camx, y, tilt_down))
        out.append(f'<text x="{camx - 4}" y="{f(y - 10)}" text-anchor="end">{name} {h:g} m</text>')
    out.append("</svg>")
    return "".join(out)


# ---------------------------------------------------------------- helpers

def img(name, alt, cls="", w=None):
    path = os.path.join(ROOT, IMG, name + ".webp")
    iw, ih = Image.open(path).size
    c = f' class="{cls}"' if cls else ""
    return (f'<img{c} src="{IMG}/{name}.webp" width="{iw}" height="{ih}" alt="{html.escape(alt)}" '
            f'loading="lazy" decoding="async">')


def mcls(m):
    return {"both": "", "object": "m-object", "place": "m-place"}[m]


def ticks(group, items):
    """items: (mode, id, text, small). Ids are stored per mode by the script."""
    out = [f'<ul class="ticks" data-group="{group}">']
    for mode, key, text, small in items:
        c = mcls(mode)
        cl = f' class="{c}"' if c else ""
        sm = f"<small>{small}</small>" if small else ""
        out.append(f'<li{cl}><label><input type="checkbox" data-id="{group}-{key}"><span>{text}{sm}</span></label></li>')
    out.append("</ul>")
    return "".join(out)


def rules(items):
    out = ['<ul class="rules">']
    for mode, text, small, *bad in items:
        c = [mcls(mode)] + (["no"] if bad and bad[0] else [])
        c = " ".join(x for x in c if x)
        cl = f' class="{c}"' if c else ""
        sm = f"<small>{small}</small>" if small else ""
        out.append(f"<li{cl}>{text}{sm}</li>")
    out.append("</ul>")
    return "".join(out)


def route(mode, name, on, points, links=(), default=False, tag=None):
    c = " ".join(x for x in ["route", "default" if default else "", mcls(mode)] if x)
    t = f'<span class="tag def">{tag}</span>' if tag else ""
    lis = "".join(f"<li>{p}</li>" for p in points)
    ls = ""
    if links:
        ls = '<div class="links">' + "".join(
            f'<a class="btn" href="{u}" target="_blank" rel="noopener">{label}</a>' for label, u in links) + "</div>"
    return f'<div class="{c}"><h3>{name}{t}</h3><p class="on">{on}</p><ul>{lis}</ul>{ls}</div>'


# ---------------------------------------------------------------- content

SECTIONS = []


def section(sid, title, body):
    n = len(SECTIONS) + 1
    SECTIONS.append((sid, title))
    return f'<section id="{sid}"><h2><span class="n">{n:02d}</span>{title}</h2>{body}</section>'


def build_body():
    parts = []

    # 1 before you go
    parts.append(section("before", "Before you go", ticks("before", [
        ("both", "battery", "Battery charged", "A power bank, if you have one"),
        ("both", "storage", "Space free on the phone", "Enough for the whole capture, twice"),
        ("both", "lens", "Lens wiped clean", ""),
        ("both", "lock", "Focus and exposure locked, if your app lets you", "Often: press and hold on the screen"),
        ("object", "zoom", "One lens, no zoom", "Stay on the main camera for every photo"),
        ("object", "object", "The object from your scene brief", "Matte and textured: not shiny, not see-through"),
        ("object", "ruler", "A ruler or another known length beside it", "It sets the real size later, in Blender"),
        ("object", "route", "Your processing route ready", "RealityScan on a lab PC, or the phone app: see After capture"),
        ("place", "app", "Scaniverse installed and opened once", "iPhone 12 or newer, or Android with ARCore Depth"),
        ("place", "sketch", "Your rings sketched from above", "Where can you walk? Draw the arcs you can"),
        ("place", "marks", "Marked what moves, shines or is see-through", ""),
        ("place", "time", "A time when the place is empty", "Early, or on a quiet day, in even light"),
    ])))

    # 2 light
    parts.append(section("light", "Light", rules([
        ("both", "Overcast or shade", "The best studio you'll ever get"),
        ("both", "No flash", "", True),
        ("both", "No hard sun, no moving shadows", "Shadows get baked into the result", True),
        ("object", "Enough light for a sharp photo", "Steady hands; no motion blur"),
        ("place", "Clouds change the light between rings", "Lock the exposure; pick a day with even light", True),
        ("place", "Short shutter, enough light", "A blurred capture won't train sharp"),
    ])))

    # 3 what scans
    works = rules([
        ("both", "Matte surfaces", ""),
        ("both", "Real texture", "Stone, bark, wood, worn leather"),
        ("both", "Still", "Nothing moves while you shoot"),
        ("place", "Leaves and hair", "Better as splats than as meshes, if they hold still"),
    ])
    fails = rules([
        ("both", "Shiny", "Reflections move with you", True),
        ("both", "See-through", "Glass, water", True),
        ("both", "Moving", "People, leaves, cars: ghosts and blur", True),
        ("object", "Plain", "Nothing to match on a blank surface", True),
        ("object", "Thin", "Antennas and wires vanish", True),
        ("place", "Mirrors", "A different world from every angle: mush", True),
    ])
    what = (f'<div class="split"><div><h3><span class="tag ok">Works</span></h3>{works}</div>'
            f'<div><h3><span class="tag no">Fails</span></h3>{fails}</div></div>'
            '<figure class="card m-object"><div class="shots c3">'
            f'<div class="shot good">{img("scan_textured", "The boombox scan, complete and textured")}<span><b>As it is</b><br>64 of 64 photos</span></div>'
            f'<div class="shot bad">{img("scan_chrome", "The chrome boombox scan: torn shards")}<span><b>Chrome</b><br>42 of 64</span></div>'
            f'<div class="shot bad">{img("scan_white", "The plain white boombox scan: a lumpy slab")}<span><b>Plain white</b><br>44 of 64</span></div>'
            '</div><figcaption>One boombox, photographed 64 times in exactly the same way. '
            'Only the textured one came back: chrome tore into shards, plain white became a lumpy slab.</figcaption></figure>')
    parts.append(section("scans", "What scans, what won't", what))

    # 4 how to move
    move = (
        f'<figure class="card m-object">{svg_object_rings()}'
        '<figcaption><b>Three loops, then the details.</b> Our boombox: 24 + 24 + 16 = 64 photos, '
        'with a ruler in the frame.</figcaption></figure>'
        f'<figure class="card m-place">{svg_place_heights()}'
        '<figcaption><b>Two or three rings at different heights</b>: knee, chest and head, '
        'each looking into the place.</figcaption></figure>'
        + '<div style="margin-top:14px">' + rules([
            ("object", "Full loops at three heights: low, middle, high", ""),
            ("object", "At most 30° between photos", "20 to 30° is safe: 12 to 18 photos a loop"),
            ("object", "About 70 % overlap, photo to photo", "Every point in at least two photos, better three"),
            ("object", "The whole object in every frame", ""),
            ("object", "Then close-ups of the details", ""),
            ("place", "Two or three rings, at different heights", "A big place may need more: up to five"),
            ("place", "30 to 50 % overlap, picture to picture", "A third to a half shared with the one before"),
            ("place", "Walk slowly, at the same distance", ""),
            ("place", "Divide a big place into parts", ""),
            ("place", "Each scan under three minutes", "Scaniverse warns you past that"),
            ("both", "Step, don't turn", "Move the camera; never pan, tilt or roll on the spot"),
        ]) + "</div>"
        + f'<figure class="card">{svg_step_dont_turn()}'
        '<figcaption>Seen from above. Turning on the spot gives a panorama: no parallax, no depth. '
        'Every step gives each point a new angle.</figcaption></figure>'
        + '<figure class="card m-place">'
        + img("place_rings", "A kitchen corner with 72 capture positions on three rings", "full")
        + '<figcaption>The Week 8 kitchen corner: 72 positions on three rings, at 0.5, 1.2 and 1.9 m.</figcaption></figure>'
    )
    parts.append(section("move", "How to move", move))

    # 5 count and check
    check = (
        '<div class="big m-object"><div><b>50–100</b><span>photos for one object</span></div>'
        '<div><b>3</b><span>loops: low, middle, high</span></div></div>'
        '<div class="big m-place"><div><b>2–3</b><span>rings at different heights</span></div>'
        '<div><b>3 min</b><span>at most, for one scan</span></div></div>'
        '<p class="note m-object">Before you leave, scroll through every photo.</p>'
        '<p class="note m-place">While it processes, check your pictures. Then orbit the splat on the phone.</p>'
        + ticks("check", [
            ("object", "count", "50 to 100 photos", ""),
            ("object", "blur", "No blurred photos", "Shaken photos smear the features"),
            ("object", "gaps", "No gaps", "Every side, the top too, seen from several places"),
            ("object", "light", "The light stayed the same", ""),
            ("object", "still", "Nothing moved", ""),
            ("object", "frame", "Never cut off, never zoomed", ""),
            ("object", "exposure", "Nothing burnt out to white", ""),
            ("object", "length", "The known length is in the photos", ""),
            ("object", "delete", "Bad photos deleted", "Better than feeding them to the software"),
            ("place", "rings", "Two or three rings captured", ""),
            ("place", "blur", "No motion blur in the pictures", ""),
            ("place", "worst", "Flew to the worst view of the splat", ""),
            ("place", "floaters", "Floaters or smears? Another ring there", "They come from views you never covered"),
            ("place", "soft", "Blurry everywhere? Check your pictures", "Blurred pictures won't train sharp"),
            ("place", "twice", "Captured twice, if you could", "The second one is almost always better"),
        ])
        + '<figure class="card m-object">'
        + img("keep_or_delete", "Six photos of the boombox, numbered 1 to 6", "full")
        + '<figcaption><b>Keep 1 and 4.</b> Delete 2: shaken. 3: zoomed in. 5: cut off. 6: overexposed.</figcaption></figure>'
        + '<figure class="card m-place"><div class="shots c2">'
        f'<div class="shot good">{img("place_3rings", "The splat trained from three rings: sharp")}<span><b>Three rings</b>, 72 pictures</span></div>'
        f'<div class="shot bad">{img("place_1ring", "The splat trained from one ring: smeared, with a dark floater")}<span><b>One ring</b>, 24 pictures</span></div>'
        '</div><figcaption>The same view, never photographed. With one ring the boombox and window smear, '
        'and a dark floater hangs in the air.</figcaption></figure>'
    )
    parts.append(section("check", "Count and check", check))

    # 6 after capture
    after = (
        '<div class="routes">'
        + route("object", "RealityScan", "Windows · NVIDIA or recent AMD card",
                ["Free for students; free Epic account, through the Epic Games Launcher",
                 "Without a supported card it can only align, not build a mesh",
                 "Simplify to a few hundred thousand triangles, then texture again: a simplified model loses its texture",
                 "No spaces or umlauts in file names, or it refuses to export"],
                [("Get it", "https://dev.epicgames.com/documentation/en-us/realityscan/getting-realityscan"),
                 ("Quick start", "https://rshelp.capturingreality.com/en-US/tutorials/quickstart.htm")],
                default=True, tag="Default")
        + route("object", "RealityScan Mobile", "iPhone or Android · processed in the cloud",
                ["Free, up to 300 photos",
                 "Exports .obj on iPhone, only .glb on Android: open it in Blender, export .fbx"],
                [("Step by step", "https://dev.epicgames.com/documentation/en-us/realityscan-mobile/realityscan-step-by-step-guide")])
        + route("object", "Meshroom", "Windows or Linux · NVIDIA card",
                ["Free, open source", "Without NVIDIA: Draft Meshing only"])
        + '<p class="note m-object">Polycam\'s free tier exports glTF only: convert it in Blender.</p>'
        + route("place", "Scaniverse", "iPhone 12 or newer · Android with ARCore Depth",
                ["Free; makes the splat on the phone in a minute or two",
                 "Exports .ply or .spz, and makes a share link",
                 "Keep each scan under three minutes"],
                [("iPhone", "https://apps.apple.com/us/app/scaniverse-3d-scanner/id1541433223"),
                 ("Android", "https://play.google.com/store/apps/details?id=com.nianticlabs.scaniverse")],
                default=True, tag="Default")
        + route("place", "Postshot", "Windows · NVIDIA card",
                ["Free to train; saves its own .psht",
                 ".ply only with Indie, €204 a year"],
                [("Postshot", "https://www.jawset.com/")])
        + route("place", "Brush or LichtFeld Studio", "PC · free, open source",
                ["Export .ply",
                 "Need the camera positions from COLMAP first: an evening of its own",
                 "LichtFeld needs an NVIDIA card; Brush runs on any graphics card"],
                [("Brush", "https://github.com/ArthurBrussee/brush"),
                 ("LichtFeld", "https://github.com/MrNeRF/LichtFeld-Studio")])
        + route("place", "SuperSplat: clean it", "Any browser with WebGPU",
                ["Free, no account to load, edit and export",
                 "Crop to your place; delete the floaters",
                 "Export .ply; a share link needs a free PlayCanvas account"],
                [("Open the editor", "https://superspl.at/editor")])
        + '</div>'
        + '<h3 class="m-object">Then clean it in Blender</h3>'
        '<ol class="steps m-object">'
        '<li>Delete the floor: select it, <kbd>X</kbd></li>'
        '<li>Delete the floaters: <kbd>L</kbd> on the object, invert, delete</li>'
        '<li>Close the holes: <kbd>F</kbd> or Fill Holes</li>'
        '<li>Scale it from your known length; check a second one</li>'
        '<li>Pivot at the base, Z up (Blender: origin)</li>'
        '<li>Name it, save v001, export .fbx with its texture</li></ol>'
        '<p class="note m-object">Keep the full-resolution scan: it is your second high-poly source for the Week 5 bake.</p>'
        '<p class="note m-place"><b>Keep the .ply</b>, whatever else you export. It goes into Unreal in Week 10.</p>'
    )
    parts.append(section("after", "After capture", after))

    # 7 names
    names = (
        rules([
            ("both", "<code>familyname_asset_task_v001</code>", "Lowercase, underscores, a version"),
            ("both", "No spaces, no umlauts", "ä → ae, ö → oe, ü → ue, ß → ss"),
            ("object", "Each capture in its own folder, in /Scans", "Leave the photos as the camera named them, like IMG_0001"),
        ])
        + '<p class="name m-object">hirsch_sarcophagus_<b>scan</b>_v001.zip<br>'
        'hirsch_sarcophagus_<b>photo_01</b>_v001.jpg</p>'
        '<p class="name m-place">hirsch_kitchen_<b>splat</b>_v001.ply<br>'
        'hirsch_kitchen_<b>splat</b>_v001.jpg</p>'
    )
    parts.append(section("names", "Name your files", names))

    # 8 hand in
    hand = (
        '<p class="note m-object"><b>One zip</b>: the cleaned mesh, its texture and three photos.</p>'
        + ticks("hand", [
            ("object", "clean", "Cleaned: floor, floaters, holes", "Real size from the known length; pivot at the base"),
            ("object", "fbx", "The processed mesh, low-res, as .fbx", ""),
            ("object", "tex", "Its texture map", ""),
            ("object", "photos", "Three photos from your capture", "One from each loop"),
            ("place", "ply", "The .ply, or a link to an online viewer", "Scaniverse's share link or a SuperSplat publish link"),
            ("place", "shot", "A screenshot of the captured scene", "The whole place, from a view between your rings"),
            ("place", "keep", "The .ply kept for Week 10", "Even if you hand in a link"),
        ])
        + '<div class="links"><a class="btn" href="checklists.html#week-4" data-w="4">Week 4 homework checklist</a></div>'
    )
    parts.append(section("hand", "Hand in", hand))
    return "".join(parts)


SCRIPT = r"""
(function () {
  var KEY = "3ddf-capture-v1";
  var state = { mode: "object", ticks: {} };
  try {
    var raw = localStorage.getItem(KEY);
    var p = raw ? JSON.parse(raw) : null;
    if (p && typeof p === "object") {
      if (p.mode === "object" || p.mode === "place") state.mode = p.mode;
      if (p.ticks && typeof p.ticks === "object") state.ticks = p.ticks;
    }
  } catch (e) {}
  var h = location.hash.replace("#", "");
  if (h === "object" || h === "place") state.mode = h;

  function save() {
    try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (e) {}
  }
  var boxes = Array.prototype.slice.call(document.querySelectorAll("input[data-id]"));
  var buttons = Array.prototype.slice.call(document.querySelectorAll(".modes button"));
  var tally = document.getElementById("tally");
  var hw = document.querySelector("a[data-w]");

  function visible(b) {
    var li = b.closest("li");
    return !li.classList.contains(state.mode === "object" ? "m-place" : "m-object");
  }
  function count() {
    var n = 0, d = 0;
    boxes.forEach(function (b) { if (visible(b)) { n++; if (b.checked) d++; } });
    tally.querySelector("b").textContent = d + "/" + n;
    tally.classList.toggle("complete", d === n && n > 0);
  }
  function apply() {
    document.body.setAttribute("data-mode", state.mode);
    buttons.forEach(function (b) { b.setAttribute("aria-pressed", b.dataset.mode === state.mode ? "true" : "false"); });
    var t = state.ticks[state.mode] || {};
    boxes.forEach(function (b) { b.checked = !!t[b.dataset.id]; });
    var w = state.mode === "object" ? "4" : "8";
    hw.href = "checklists.html#week-" + w;
    hw.textContent = "Week " + w + " homework checklist";
    count();
  }
  buttons.forEach(function (b) {
    b.addEventListener("click", function () {
      state.mode = b.dataset.mode;
      try { history.replaceState(null, "", "#" + state.mode); } catch (e) {}
      save(); apply();
    });
  });
  boxes.forEach(function (b) {
    b.addEventListener("change", function () {
      var t = state.ticks[state.mode] || (state.ticks[state.mode] = {});
      if (b.checked) t[b.dataset.id] = 1; else delete t[b.dataset.id];
      save(); count();
    });
  });
  document.getElementById("clear").addEventListener("click", function () {
    state.ticks[state.mode] = {};
    save(); apply();
  });
  apply();
})();
"""


def page():
    body = build_body()
    jump = "".join(f'<a href="#{sid}">{t}</a>' for sid, t in SECTIONS)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Capture Card · 3D Design Foundations</title>
<meta name="description" content="Open it on your phone while you capture: an object for photogrammetry (Week 4) or a place for a Gaussian splat (Week 8). Light, movement, counts, a self-check, processing routes and what to hand in.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=Archivo:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap">
<style>
{CSS}</style>
</head>
<body data-mode="object">
<div class="wrap">

  <header>
    <a class="back" href="index.html">&larr; 3D Design Foundations</a>
    <h1>Capture card</h1>
    <p class="standfirst">
      Open this on your phone while you shoot. Pick what you're capturing: an object for
      photogrammetry in Week 4, or a place for a splat in Week 8. Tick things off as you go;
      your ticks stay on this phone.
    </p>
    <nav class="jump">{jump}</nav>
  </header>

  <div class="bar">
    <div class="modes" role="group" aria-label="What are you capturing?">
      <button type="button" data-mode="object" aria-pressed="true">Object<small>Week 4 · scan</small></button>
      <button type="button" data-mode="place" aria-pressed="false">Place<small>Week 8 · splat</small></button>
    </div>
    <div class="tally" id="tally" aria-live="polite"><b>0/0</b><span>ticked</span></div>
  </div>

  {body}

  <footer>
    <div class="reset"><button class="clear" id="clear" type="button">Clear ticks for this mode</button><span>Saved on this device only.</span></div>
    <p>3D Design Foundations &middot; Smart Interactive Media, TH Rosenheim &middot; Prof. Seb Hirsch</p>
    <p>Pictures from the course's own test captures: Poly Haven's Boombox by Thomas Paul Mouilleron (CC0), rendered in Blender 5.2 and scanned in RealityScan 2.0.1; the kitchen corner trained as a splat in LichtFeld Studio. Diagrams drawn for this page.</p>
  </footer>
</div>
<script>{SCRIPT}</script>
</body>
</html>
"""


def main():
    out = os.path.join(ROOT, "capture.html")
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(page())
    print("wrote", out, os.path.getsize(out) // 1024, "KB")


if __name__ == "__main__":
    main()
