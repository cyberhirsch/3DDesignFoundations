"""Render the pattern library poster from _topology/poster.html.

  python _topology/build_page.py      (writes poster.html)
  python _topology/build_poster.py    (needs Playwright and Microsoft Edge)

Output: img/topology/topology_poster.png and topology_poster.pdf, one tall
sheet in the light theme.
"""
import os

from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "_topology", "poster.html")
PNG = os.path.join(ROOT, "img", "topology", "topology_poster.png")
PDF = os.path.join(ROOT, "img", "topology", "topology_poster.pdf")

with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge")
    pg = b.new_page(viewport={"width": 1500, "height": 1000}, color_scheme="light")
    pg.goto("file:///" + SRC.replace("\\", "/"), wait_until="networkidle")
    pg.evaluate("document.fonts.ready")
    pg.wait_for_timeout(800)
    broken = pg.evaluate("[...document.images].filter(i => !i.naturalWidth).map(i => i.src)")
    if broken:
        raise SystemExit(f"broken images: {broken}")
    h = pg.evaluate("Math.ceil(document.documentElement.scrollHeight)")
    pg.set_viewport_size({"width": 1500, "height": h})
    pg.screenshot(path=PNG, full_page=True)
    pg.emulate_media(media="screen")
    pg.pdf(path=PDF, width="1500px", height=f"{h + 2}px", print_background=True,
           margin={"top": "0", "right": "0", "bottom": "0", "left": "0"})
    b.close()
for f in (PNG, PDF):
    print(f, os.path.getsize(f) // 1024, "KB")
print("size", 1500, "x", h)
