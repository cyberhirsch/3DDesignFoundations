"""Build pipeline.html: the asset pipeline cheat sheet (Blender 5.2 -> Substance 3D Painter -> Unreal 5.8).

  python _pipeline/build_page.py

The page text is the template below; the CSS is base.css (copied from
_topology/topology.css) plus page.css. The four normal-map tiles are drawn
here from the normals of a hemisphere, so the colours are the real encoding.
Edit this script and the CSS, not pipeline.html.
"""
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


# ------------------------------------------------------------ normal tiles

N = 20            # cells per side
R = 0.78          # bump radius, in tile units (-1..1)
LIGHT = (-0.45, 0.62, 0.64)   # from the top left, y up


def _norm(v):
    l = math.sqrt(sum(c * c for c in v))
    return tuple(c / l for c in v)


def bump_normal(x, y):
    """Normal of a dome of radius R; y points up."""
    d2 = x * x + y * y
    if d2 >= R * R:
        return (0.0, 0.0, 1.0)
    h = math.sqrt(R * R - d2)
    return _norm((x, y, h))


def tile(kind, label):
    L = _norm(LIGHT)
    cells = []
    s = 120 / N
    for j in range(N):
        y = 1 - 2 * (j + 0.5) / N
        for i in range(N):
            x = -1 + 2 * (i + 0.5) / N
            nx, ny, nz = bump_normal(x, y)
            if kind == "gl":       # OpenGL: green = +Y
                rgb = (nx * .5 + .5, ny * .5 + .5, nz * .5 + .5)
            elif kind == "dx":     # DirectX: green = -Y
                rgb = (nx * .5 + .5, -ny * .5 + .5, nz * .5 + .5)
            else:
                if kind == "bad":  # a DirectX map read as OpenGL: Y flipped
                    ny = -ny
                d = max(0.0, nx * L[0] + ny * L[1] + nz * L[2])
                g = 0.12 + 0.82 * d
                rgb = (g, g, g)
            hexc = "#%02x%02x%02x" % tuple(round(max(0, min(1, c)) * 255) for c in rgb)
            cells.append(f'<rect x="{i * s:.1f}" y="{j * s:.1f}" width="{s + .05:.2f}" height="{s + .05:.2f}" fill="{hexc}"/>')
    return (f'<svg viewBox="0 0 120 120" width="120" height="120" role="img" aria-label="{label}" '
            f'shape-rendering="crispEdges">{"".join(cells)}</svg>')


NORMALS = f"""
    <div class="nm">
      <figure class="gl">{tile("gl", "A bump stored as an OpenGL normal map: the top half is greener")}
        <figcaption><b>OpenGL: Blender</b>Green grows upwards: the top of the bump is green.</figcaption></figure>
      <figure class="dx">{tile("dx", "The same bump stored as a DirectX normal map: the bottom half is greener")}
        <figcaption><b>DirectX: Unreal</b>Green grows downwards. Red and blue are the same.</figcaption></figure>
      <figure class="good">{tile("good", "Read with the right convention, the bump is lit from the top left and looks raised")}
        <figcaption><b>Read right: a bump</b>Lit from the top left, like the scene.</figcaption></figure>
      <figure class="bad">{tile("bad", "Read with the wrong convention, the bump is lit from below and looks like a dent")}
        <figcaption><b>Green flipped: a dent</b>The same light seems to come from below.</figcaption></figure>
    </div>"""


# ------------------------------------------------------------ the page

TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Asset Pipeline · 3D Design Foundations</title>
<meta name="description" content="Asset pipeline cheat sheet: Blender 5.2 to Substance 3D Painter to Unreal Engine 5.8. What to export at each hand-off, every map's colour space and Unreal settings, normal map conventions, scale and axes, a hand-in check and a fix table.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=Archivo:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap">
<style>
%%CSS%%
</style>
</head>
<body>
<div class="wrap">
  <header>
    <a class="back" href="index.html">&larr; 3D Design Foundations</a>
    <h1>Asset pipeline</h1>
    <p class="standfirst">
      From Blender 5.2 through Substance 3D Painter into Unreal Engine 5.8: what leaves each program,
      in which format, with which settings, and what to check when it arrives. For Weeks 5, 6, 10 and 11.
    </p>
    <p class="standfirst">Why colour maps and data maps are read differently is on the <a href="colour.html">linear colour page</a>. This page says where to set it.</p>
    <nav class="jump" aria-label="On this page">
      <a href="#route">Route</a>
      <a href="#handoff-1">1 Blender &rarr; Painter</a>
      <a href="#handoff-2">2 Painter &rarr; Unreal</a>
      <a href="#handoff-3">3 Blender &rarr; Unreal</a>
      <a href="#names">Names</a>
      <a href="#maps">Maps</a>
      <a href="#normals">Normals</a>
      <a href="#scale">Scale and axes</a>
      <a href="#agree">Bake = engine</a>
      <a href="#check">Check</a>
      <a href="#fix">Fix</a>
    </nav>
  </header>

  <section id="route">
    <h2>The route</h2>
    <p class="lede">
      Your asset travels on two roads. The mesh goes from Blender straight to Unreal. Its textures take
      the detour through Painter, which bakes the high-poly onto the low-poly and paints the layers.
      The two meet again in Unreal, in a material instance.
    </p>
    <div class="strip">
      <div class="tool"><b>Blender 5.2</b><span class="wk">Weeks 2&ndash;5</span><p>Model, sculpt, retopologize, unwrap.</p></div>
      <a class="hop" href="#handoff-1"><span class="n">1</span><span class="arrow" aria-hidden="true">&rarr;</span><small><span>FBX</span> <span>low + high</span></small></a>
      <div class="tool"><b>Painter</b><span class="wk">Week 6</span><p>Bake, layers and masks, export.</p></div>
      <a class="hop" href="#handoff-2"><span class="n">2</span><span class="arrow" aria-hidden="true">&rarr;</span><small><span>3 PNG</span> <span>textures</span></small></a>
      <div class="tool"><b>Unreal 5.8</b><span class="wk">Weeks 10&ndash;11</span><p>Assemble, material, light.</p></div>
      <a class="road" href="#handoff-3"><span class="n">3</span><span>The mesh skips Painter: Blender &rarr; Unreal as USD, the whole scene at once (Week 10).</span></a>
    </div>
    <p class="note">Week 6&rsquo;s rule for every hand-off: author freely, export explicitly, validate somewhere else. Open each export in a second program before you trust it.</p>
  </section>

  <section id="handoff-1">
    <h2>Hand-off 1 &middot; Blender &rarr; Painter</h2>
    <div class="card">
      <h3><span class="n">1</span>The mesh pair, for baking</h3>
      <p class="when">Exported in Week 5 &middot; baked in Week 6</p>
      <table>
        <tr><td>Export</td><td>The low-poly with its UVs, and the high-poly it bakes from, as two files:
          <span class="file">familyname_asset_low_v001.fbx</span> and <span class="file">familyname_asset_high_v001.fbx</span>.</td></tr>
        <tr><td>Before</td><td><ul>
          <li>Scale applied: Sidebar (<kbd>N</kbd>) &rarr; Item shows Scale 1, 1, 1. If not, save a new version, then <kbd>Ctrl</kbd><span class="sep">+</span><kbd>A</kbd> &rarr; Scale.</li>
          <li>Low and high sit in exactly the same place. Never move one of them.</li>
          <li>Every part named in pairs, <code>seat_low</code> and <code>seat_high</code>. Name the mesh data like the object.</li>
          <li>UVs on the low-poly: no overlaps, no flipped islands, a UV seam on every hard edge.</li>
          <li>If you triangulate, add a Triangulate modifier as the last modifier of the low-poly now, and keep it. See <a href="#agree">Bake = engine</a>.</li>
        </ul></td></tr>
        <tr><td>Blender</td><td>File &rarr; Export &rarr; FBX (.fbx): Limit to <b>Selected Objects</b>, Object Types <b>Mesh</b>, <b>Apply Modifiers</b> on.
          Leave the rest at its defaults: Forward &minus;Z, Up Y, Apply Scalings All Local, Apply Unit on, Smoothing Normals Only.</td></tr>
        <tr><td>Painter</td><td>File &rarr; New: File = the low-poly FBX, Resolution 2048. Under Advanced: Normal Map Format <b>DirectX</b>, <b>Compute Tangent Space per Fragment</b> on (Adobe: Unreal needs it).</td></tr>
        <tr><td>Bake</td><td>Baking mode (<kbd>F8</kbd>). High Definition Meshes: the high-poly FBX. Match <b>By Mesh Name</b>, suffixes <code>_low</code> and <code>_high</code>. Cage: distance based, Max Frontal and Max Rear Distance. Bake all seven maps.</td></tr>
        <tr><td>Check</td><td>Read the log. Red zones mean the cage cuts into the model. Look at every map: no holes, no foreign shapes, no dark seams.</td></tr>
      </table>
    </div>
  </section>

  <section id="handoff-2">
    <h2>Hand-off 2 &middot; Painter &rarr; Unreal</h2>
    <div class="card">
      <h3><span class="n">2</span>The texture set</h3>
      <p class="when">Exported in Week 6 &middot; imported in Week 11</p>
      <table>
        <tr><td>Painter</td><td>File &rarr; Export Textures, Export settings tab:
          Output template <b>Unreal Engine (Packed)</b>, File type PNG 8 bit, Size based on each Texture Set&rsquo;s size, Padding <b>Dilation infinite</b>.</td></tr>
        <tr><td>Out come</td><td>Three files per Texture Set: <code>&hellip;_BaseColor</code> (colour), <code>&hellip;_Normal</code> (DirectX) and
          <code>&hellip;_OcclusionRoughnessMetallic</code> (AO in red, roughness in green, metallic in blue).</td></tr>
        <tr><td>Store</td><td>In a folder <span class="file">familyname_asset_textures_v001</span>, the files named Unreal&rsquo;s way: <code>T_Chair_BaseColor.png</code>, <code>T_Chair_Normal.png</code>, <code>T_Chair_OcclusionRoughnessMetallic.png</code>.</td></tr>
        <tr><td>Unreal</td><td>Drag the PNGs into a Content Browser folder. Double-click each texture and set sRGB and Compression Settings as in the <a href="#maps">map table</a>.
          Then one parent material <code>M_</code> with a Texture Sample per map, Sampler Type to match, converted to parameters, and one instance <code>MI_</code> per object.</td></tr>
        <tr><td>Check</td><td>Open the three PNGs in a second program first. Then in Unreal, the Detail Lighting view: the normal detail should look raised, not dented.</td></tr>
      </table>
    </div>
  </section>

  <section id="handoff-3">
    <h2>Hand-off 3 &middot; Blender &rarr; Unreal</h2>
    <div class="card">
      <h3><span class="n">3</span>The scene, as USD</h3>
      <p class="when">Week 10 &middot; one late object can come as FBX</p>
      <table>
        <tr><td>Before</td><td><ul>
          <li>Procedural materials baked to image textures: node trees don&rsquo;t travel.</li>
          <li>Pivot at the base, where the object touches the floor: Object &rarr; Set Origin (Blender calls the pivot the origin).</li>
          <li>Scale applied, and Scene Properties &rarr; Units: Unit Scale left at 1.0.</li>
          <li>The low-poly with the same modifiers it had for the bake.</li>
        </ul></td></tr>
        <tr><td>Blender</td><td>File &rarr; Export &rarr; Universal Scene Description: <span class="file">familyname_scene_layout_v001.usdc</span>.
          General: Units <b>Meters</b>. Object Types: <b>World Dome Light off</b>. Keep UV Maps, Normals and Materials on (the defaults).</td></tr>
        <tr><td>Unreal</td><td>A Blank project with the USD Importer plugin on. File &rarr; Import Into Level, pick the <code>.usdc</code>: this is the route for the scene you hand in.
          The USD Stage keeps a live link instead, for trying changes.</td></tr>
        <tr><td>One object</td><td>FBX with the settings of hand-off 1, from an object at the world origin: otherwise its distance from the origin ends up inside the mesh and the pivot lands beside it.
          In Unreal&rsquo;s import options, leave Convert Scene and Convert Scene Unit on.</td></tr>
        <tr><td>Check</td><td>Measure one object you know: drag with the middle mouse button in the viewport, in centimetres. Our chair: 95 cm. A size that&rsquo;s wrong gets fixed in Blender and exported again, never scaled in Unreal.</td></tr>
      </table>
    </div>
  </section>

  <section id="names">
    <h2>Names</h2>
    <table class="grid names stack">
      <thead><tr><th>What</th><th>Pattern</th><th>Example</th></tr></thead>
      <tbody>
        <tr><td>Every file you save</td><td data-l="Pattern"><code>familyname_asset_task_v001</code></td><td data-l="Example" class="mut"><code>hirsch_cutting_board_low_v001.fbx</code></td></tr>
        <tr><td>Bake pairs: objects and their mesh data</td><td data-l="Pattern"><code>part_low</code>, <code>part_high</code></td><td data-l="Example" class="mut"><code>seat_low</code>, <code>seat_high</code></td></tr>
        <tr><td>Texture folder</td><td data-l="Pattern"><code>familyname_asset_textures_v001</code></td><td data-l="Example" class="mut"><code>hirsch_ladder_back_chair_textures_v001</code></td></tr>
        <tr><td>Texture files</td><td data-l="Pattern"><code>T_Asset_Map</code></td><td data-l="Example" class="mut"><code>T_Chair_OcclusionRoughnessMetallic.png</code></td></tr>
        <tr><td>Objects in Blender</td><td data-l="Pattern"><code>GEO-</code>, <code>LGT-</code>, <code>CAM-</code></td><td data-l="Example" class="mut"><code>GEO-cutting_board</code></td></tr>
        <tr><td>Assets in Unreal</td><td data-l="Pattern"><code>SM_</code>, <code>M_</code>, <code>MI_</code>, <code>T_</code></td><td data-l="Example" class="mut"><code>MI_CuttingBoard</code></td></tr>
      </tbody>
    </table>
    <p class="note">USD allows no hyphens, so <code>GEO-boombox</code> arrives as <code>GEO_boombox</code>: expected. Save a new version instead of overwriting: <code>v002</code>, <code>v003</code>.</p>
  </section>

  <section id="maps">
    <h2>Every map, every setting</h2>
    <table class="grid maps stack">
      <thead><tr><th>Map</th><th>Painter</th><th>Packed file</th><th>Blender</th><th>Unreal texture</th><th>Sampler type</th></tr></thead>
      <tbody>
        <tr><td>Base colour</td><td data-l="Painter">Base Color channel</td><td data-l="File"><code>_BaseColor</code>, RGB</td><td data-l="Blender">sRGB</td><td data-l="Unreal">sRGB <span class="on">on</span> &middot; Default (BC1 or BC3 with A)</td><td data-l="Sampler">Color</td></tr>
        <tr><td>Normal</td><td data-l="Painter">baked Normal + Normal channel</td><td data-l="File"><code>_Normal</code>, RGB, DirectX</td><td data-l="Blender">Non-Color, into a Normal Map node</td><td data-l="Unreal">sRGB <span class="off">off</span> &middot; Normalmap (BC5)</td><td data-l="Sampler">Normal</td></tr>
        <tr><td>Ambient occlusion</td><td data-l="Painter">baked AO + AO channel</td><td data-l="File"><code>_OcclusionRoughnessMetallic</code>, R</td><td data-l="Blender">Non-Color</td><td data-l="Unreal">sRGB <span class="off">off</span> &middot; Masks (no sRGB)</td><td data-l="Sampler">Masks</td></tr>
        <tr><td>Roughness</td><td data-l="Painter">Roughness channel</td><td data-l="File">same file, G</td><td data-l="Blender">Non-Color</td><td data-l="Unreal">the ORM texture&rsquo;s settings</td><td data-l="Sampler">Masks</td></tr>
        <tr><td>Metallic</td><td data-l="Painter">Metallic channel</td><td data-l="File">same file, B</td><td data-l="Blender">Non-Color</td><td data-l="Unreal">the ORM texture&rsquo;s settings</td><td data-l="Sampler">Masks</td></tr>
        <tr><td>Curvature, world space normal, position, thickness, ID</td><td data-l="Painter">baked mesh maps</td><td data-l="File">not exported</td><td data-l="Blender">Non-Color, if you bake them there</td><td data-l="Unreal">&ndash;</td><td data-l="Sampler">&ndash;</td></tr>
      </tbody>
    </table>
    <ol class="rules">
      <li>Only base colour is a colour. Every other map is data: sRGB off in Unreal, Non-Color in Blender.</li>
      <li>In Unreal: double-click the texture &rarr; Details &rarr; Texture &rarr; sRGB, and Compression &rarr; Compression Settings.</li>
      <li>In the material, the ORM sample feeds three inputs: R &rarr; Ambient Occlusion, G &rarr; Roughness, B &rarr; Metallic.</li>
      <li>A Texture Sample&rsquo;s Sampler Type must match its texture, or the material won&rsquo;t compile.</li>
      <li>Unreal spots most normal maps by their pixels and sets them itself. It imported our ORM with sRGB on. Check every texture after import.</li>
    </ol>
    <p class="note">The full colour-space table for each program, and a game to practise sorting colour from data: <a href="colour.html#tools">linear colour page</a>.</p>
  </section>

  <section id="normals">
    <h2>Normal maps: OpenGL or DirectX</h2>
    <p class="lede">
      A tangent-space normal map stores a direction in red, green and blue. Programs disagree about one thing:
      which way green points. Read with the wrong convention, every bump turns into a dent.
    </p>
%%NORMALS%%
    <table class="grid where stack">
      <thead><tr><th>Program</th><th>Expects</th><th>Where to set or flip</th></tr></thead>
      <tbody>
        <tr><td>Blender 5.2</td><td data-l="Expects">OpenGL</td><td data-l="Where">Image Texture on Non-Color &rarr; Normal Map node, Tangent Space. Its own bakes are OpenGL (Normal Space Tangent; swizzle +X, +Y, +Z). There is no DirectX switch: for a DirectX map, invert green with Separate Color, Math (1 &minus; G) and Combine Color.</td></tr>
        <tr><td>Painter</td><td data-l="Expects">your choice</td><td data-l="Where">File &rarr; New &rarr; Normal Map Format. The export converts: Unreal Engine (Packed) writes DirectX, whatever the project uses.</td></tr>
        <tr><td>Unreal 5.8</td><td data-l="Expects">DirectX</td><td data-l="Where">For an OpenGL map: double-click the texture &rarr; Texture, open the advanced options &rarr; Flip Green Channel.</td></tr>
      </tbody>
    </table>
    <p class="note">The test: light a bump from above. If it looks raised, the convention is right. If the light seems to come from below, green is flipped.</p>
  </section>

  <section id="scale">
    <h2>Scale and axes at each hand-off</h2>
    <table class="grid units stack">
      <thead><tr><th>Where</th><th>One unit</th><th>Up</th><th>Set it in</th></tr></thead>
      <tbody>
        <tr><td>Blender</td><td data-l="Unit">1 m</td><td data-l="Up">Z, right-handed</td><td data-l="Set it in">Scene Properties &rarr; Units: Unit Scale 1.0, and keep it</td></tr>
        <tr><td>FBX from Blender</td><td data-l="Unit">converted by Apply Unit</td><td data-l="Up">written as Y up, &minus;Z forward</td><td data-l="Set it in">Export &rarr; FBX &rarr; Transform: leave the defaults; the importers turn it back</td></tr>
        <tr><td>USD from Blender</td><td data-l="Unit"><code>metersPerUnit = 1</code></td><td data-l="Up"><code>upAxis = "Z"</code></td><td data-l="Set it in">Export &rarr; USD &rarr; General &rarr; Units: Meters. It ignores the scene&rsquo;s Unit Scale</td></tr>
        <tr><td>Unreal</td><td data-l="Unit">1 cm</td><td data-l="Up">Z, left-handed</td><td data-l="Set it in">converts on import: Convert Scene and Convert Scene Unit for FBX, metersPerUnit for USD</td></tr>
      </tbody>
    </table>
    <ol class="rules">
      <li>Leave the axis settings at their defaults on both ends. An object lying on its back means a setting was changed; fix the setting, don&rsquo;t rotate the object by hand.</li>
      <li>Blender&rsquo;s +Y is Unreal&rsquo;s &minus;Y, and turns about Z change sign: &minus;14&deg; in Blender reads +14&deg; in Unreal. The importer handles it; only numbers you type across by hand go wrong.</li>
      <li>Apply scale in Blender before the bake and before every export, so bevels, bakes and sizes agree.</li>
      <li>After every import, measure one object you know.</li>
    </ol>
  </section>

  <section id="agree">
    <h2>The bake and the engine must agree</h2>
    <p class="lede">
      A normal map is made for one set of mesh normals and one set of triangles. Change either after the bake,
      and seams and wavy shading appear in Unreal that weren&rsquo;t there in Painter.
    </p>
    <ol class="rules">
      <li><b>Same normals.</b> Set the smoothing before the bake (Shade Smooth or Shade Auto Smooth, weighted normals if you use them) and don&rsquo;t touch it after.</li>
      <li><b>Hard edge, UV seam.</b> Every hard edge gets a UV seam, or the bake draws a dark line along it.</li>
      <li><b>Same triangles.</b> Painter and Unreal both cut your quads into triangles, and not always the same way. A Triangulate modifier, last on the low-poly&rsquo;s stack before the Week 5 export, fixes the triangles for good; the USD export applies it again in Week 10.</li>
      <li><b>Same tangents.</b> Blender, Painter and Unreal all use MikkTSpace. In Unreal&rsquo;s FBX import options (Common Meshes, Build), keep Use Mikk TSpace on.</li>
      <li><b>Keep your normals.</b> Recompute Normals is on by default in those options: Unreal then ignores the normals in the file and calculates its own. If you set custom or weighted normals, switch it off.</li>
      <li><b>One file, both ways.</b> Bake from the same low-poly you send to Unreal. Edit the mesh after the bake, and you bake again.</li>
    </ol>
    <p class="note">Clean topology first: the <a href="topology.html">SubD topology page</a> for the cage and the <a href="shortcuts.html#uvs">UV shortcuts</a> for unwrapping.</p>
  </section>

  <section id="check">
    <h2>Check before you hand in</h2>
    <table class="check stack">
      <thead><tr><th>Check</th><th>Where</th></tr></thead>
      <tbody>
        <tr class="wk"><td colspan="2">Week 5</td></tr>
        <tr><td>Scale 1, 1, 1</td><td>Sidebar (<kbd>N</kbd>) &rarr; Item; else <kbd>Ctrl</kbd><span class="sep">+</span><kbd>A</kbd> &rarr; Scale</td></tr>
        <tr><td>Parts named <code>_low</code> and <code>_high</code></td><td>Outliner: objects and their mesh data</td></tr>
        <tr><td>No overlapping or flipped UVs</td><td>UV Editor &rarr; Select &rarr; Select All by Trait &rarr; Overlap, then Winding (Negative): nothing should get selected</td></tr>
        <tr><td>Normals point out</td><td>Viewport Overlays &rarr; Face Orientation: blue outside</td></tr>
        <tr><td>Data map on Non-Color</td><td>Image Texture node &rarr; Color Space</td></tr>
        <tr class="wk"><td colspan="2">Week 6</td></tr>
        <tr><td>Bake clean</td><td>The log read, no red cage zones, every map looked at</td></tr>
        <tr><td>Three files per Texture Set</td><td>Unreal Engine (Packed); opened in a second program</td></tr>
        <tr class="wk"><td colspan="2">Week 10</td></tr>
        <tr><td>No second sky</td><td>USD export &rarr; Object Types: World Dome Light off</td></tr>
        <tr><td>Real size</td><td>One known object measured in Unreal</td></tr>
        <tr><td>Pivots at the base</td><td>Select an object in Unreal: the gizmo sits where it touches the floor</td></tr>
        <tr class="wk"><td colspan="2">Week 11</td></tr>
        <tr><td>Texture settings</td><td>BaseColor sRGB on; Normal off, Normalmap; ORM off, Masks</td></tr>
        <tr><td>Sampler types match</td><td>Material Editor: Color, Normal, Masks; the material compiles</td></tr>
        <tr><td>Bumps, not dents</td><td>Viewport &rarr; Detail Lighting</td></tr>
        <tr class="wk"><td colspan="2">Any scene file</td></tr>
        <tr><td>Textures travel with it</td><td>File &rarr; External Data &rarr; Pack Resources, or the project folder zipped</td></tr>
      </tbody>
    </table>
    <p class="note">The full list for each week is on the <a href="checklists.html">homework checklist</a>.</p>
  </section>

  <section id="fix">
    <h2>Fix it</h2>
    <table class="fix stack">
      <thead><tr><th>You see</th><th>Usually because</th><th>Fix</th></tr></thead>
      <tbody>
        <tr><td>Too glossy, AO too dark, in Unreal</td><td data-l="Because">The ORM texture is read as sRGB</td><td data-l="Fix">sRGB off, Compression Settings Masks, Sampler Type Masks</td></tr>
        <tr><td>Relief patchy, tilted on every island, in Blender</td><td data-l="Because">The normal map is read as sRGB</td><td data-l="Fix">Color Space Non-Color, through a Normal Map node</td></tr>
        <tr><td>Base colour pale and washed out</td><td data-l="Because">A colour map on Non-Color, or sRGB off</td><td data-l="Fix">Back to sRGB</td></tr>
        <tr><td>Bumps look like dents</td><td data-l="Because">The normal map has the other convention</td><td data-l="Fix">Unreal: Flip Green Channel; Blender: invert green, or export with the right template</td></tr>
        <tr><td>The material won&rsquo;t compile</td><td data-l="Because">A Sampler Type doesn&rsquo;t match its texture</td><td data-l="Fix">Color, Normal or Masks, as in the map table</td></tr>
        <tr><td>Dark lines along seams or hard edges</td><td data-l="Because">A hard edge without a UV seam, too little padding, or different tangents</td><td data-l="Fix">Seam every hard edge; Dilation infinite; MikkTSpace everywhere</td></tr>
        <tr><td>Wavy shading in Unreal, fine in Painter</td><td data-l="Because">Different triangles, or Unreal recomputed the normals</td><td data-l="Fix">Triangulate modifier before bake and export; Recompute Normals off for custom normals</td></tr>
        <tr><td>Shapes of another part in the bake</td><td data-l="Because">Matching off, or names that don&rsquo;t pair</td><td data-l="Fix">Match By Mesh Name; every part <code>_low</code> and <code>_high</code></td></tr>
        <tr><td>Holes and missing detail in the bake</td><td data-l="Because">The cage is too short</td><td data-l="Fix">Raise Max Frontal and Max Rear Distance, test, bake again</td></tr>
        <tr><td>An object 100 times too small or too big</td><td data-l="Because">Unit Scale changed, Units changed on export, or scaled in Unreal</td><td data-l="Fix">Unit Scale 1.0, Units Meters; fix in Blender, export again</td></tr>
        <tr><td>An object lying on its back</td><td data-l="Because">An axis setting changed on export or import</td><td data-l="Fix">Defaults back on; never rotate it upright by hand</td></tr>
        <tr><td>It turns around a point beside it</td><td data-l="Because">The pivot isn&rsquo;t at the base, or an FBX object wasn&rsquo;t at the world origin</td><td data-l="Fix">Object &rarr; Set Origin at the base; FBX from the world origin</td></tr>
        <tr><td>An extra Sky Light, an actor called root</td><td data-l="Because">Blender&rsquo;s USD export: World Dome Light and Root Prim</td><td data-l="Fix">World Dome Light off; sort or remove root after the import</td></tr>
        <tr><td>A rug called Cube_013</td><td data-l="Because">USD names meshes after their mesh data</td><td data-l="Fix">Name the mesh data like the object</td></tr>
        <tr><td>Magenta surfaces on another computer</td><td data-l="Because">Textures not packed</td><td data-l="Fix">File &rarr; External Data &rarr; Pack Resources</td></tr>
      </tbody>
    </table>
  </section>

  <section id="read">
    <h2>Read more</h2>
    <ul class="read">
      <li>Blender 5.2 Manual: <a href="https://docs.blender.org/manual/en/latest/files/import_export/fbx.html">FBX</a>, <a href="https://docs.blender.org/manual/en/latest/files/import_export/usd.html">Universal Scene Description</a>, <a href="https://docs.blender.org/manual/en/latest/render/cycles/baking.html">Render Baking</a>, <a href="https://docs.blender.org/manual/en/latest/render/shader_nodes/textures/image.html">Image Texture node</a>.</li>
      <li>Adobe, Substance 3D Painter: <a href="https://experienceleague.adobe.com/en/docs/substance-3d-painter/using/getting-started/project-creation">Project creation</a>, <a href="https://experienceleague.adobe.com/en/docs/substance-3d-painter/using/baking/mesh-map-settings">Mesh map settings</a>, <a href="https://experienceleague.adobe.com/en/docs/substance-3d-painter/using/export/export-window/export-settings">Export settings</a>, <a href="https://experienceleague.adobe.com/en/docs/substance-3d-painter/using/export/export-window/output-templates">Output templates</a>.</li>
      <li>Epic Games, Unreal Engine 5.8: <a href="https://dev.epicgames.com/documentation/unreal-engine/creating-and-using-material-instances-in-unreal-engine">Material instances</a>, <a href="https://dev.epicgames.com/documentation/en-us/unreal-engine/usd-stage-editor-quick-start-in-unreal-engine">USD Stage Editor quick start</a>.</li>
    </ul>
  </section>

  <footer>
    <p>3D Design Foundations &middot; Smart Interactive Media, TH Rosenheim &middot; Prof. Seb Hirsch</p>
    <p>Settings checked in Blender 5.2, against Unreal Engine 5.8&rsquo;s source and a test import, and in Adobe&rsquo;s Substance 3D Painter documentation, October 2026. The normal map tiles are drawn by this page from a hemisphere&rsquo;s normals.</p>
  </footer>
</div>
</body>
</html>
"""


def main():
    css = open(os.path.join(HERE, "base.css"), encoding="utf-8").read()
    css += open(os.path.join(HERE, "page.css"), encoding="utf-8").read()
    html = TEMPLATE.replace("%%CSS%%", css.strip()).replace("%%NORMALS%%", NORMALS.strip("\n"))
    with open(os.path.join(ROOT, "pipeline.html"), "w", encoding="utf-8", newline="\n") as f:
        f.write(html)
    print("pipeline.html", len(html) // 1024, "KB")


if __name__ == "__main__":
    main()
