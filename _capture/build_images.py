"""Make the WebP pictures for capture.html from the Week 4 and Week 8 decks.

  python _capture/build_images.py

Only images the decks' Assets/SOURCES.md list as own work (the boombox
capture, the kitchen-corner splat) are used; nothing from "Teaching use only".
"""
import os
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "img", "capture")
COURSE = r"D:\Google Drive\THRO\Lectures\S1_3D Design Foundations"
W4 = os.path.join(COURSE, "Week 04 - Photogrammetry.dek", "Assets")
W8 = os.path.join(COURSE, "Week 08 - Gaussian Splatting.dek", "Assets")

# (source, output name, crop box or None, output width)
JOBS = [
    (os.path.join(W4, "week_04_scan_clean.png"), "scan_textured", None, 480),
    (os.path.join(W4, "week_04_fail_chrome.png"), "scan_chrome", None, 480),
    (os.path.join(W4, "week_04_fail_white.png"), "scan_white", None, 480),
    (os.path.join(W4, "week_04_fix_photos.jpg"), "keep_or_delete", None, 960),
    (os.path.join(W8, "week_08_capture_positions.jpg"), "place_rings", None, 900),
    (os.path.join(W8, "week_08_view_3rings.jpg"), "place_3rings", None, 560),
    (os.path.join(W8, "week_08_view_1ring.jpg"), "place_1ring", None, 560),
]


def main():
    os.makedirs(OUT, exist_ok=True)
    for src, name, box, w in JOBS:
        im = Image.open(src).convert("RGB")
        if box:
            im = im.crop(box)
        h = round(im.height * w / im.width)
        im = im.resize((w, h), Image.LANCZOS)
        path = os.path.join(OUT, name + ".webp")
        im.save(path, "WEBP", quality=72, method=6)
        print(f"{name}.webp {w}x{h} {os.path.getsize(path) // 1024} KB")


if __name__ == "__main__":
    main()
