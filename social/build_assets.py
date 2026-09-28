# -*- coding: utf-8 -*-
"""
Build clean assets for the social-media card set.

Inputs  : ../images/*  (workshop asset library)
Outputs : ./assets/*.jpg   (cropped + optimised, watermark-free)
          ./fonts/*.woff2 + ./fonts/fonts.css  (Amiri + IBM Plex Sans Arabic)

Run:  python build_assets.py
"""
import io
import os
import re
import urllib.request
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(HERE, "..", "images")
ASSETS = os.path.join(HERE, "assets")
FONTS = os.path.join(HERE, "fonts")
os.makedirs(ASSETS, exist_ok=True)
os.makedirs(FONTS, exist_ok=True)

# --------------------------------------------------------------------------
# 1. Image crops (logo / label bands trimmed, re-encoded as JPEG for web)
# --------------------------------------------------------------------------
# (source, output, crop box as L,T,R,B in source pixels, quality, mode)
#   mode: "fixed"   = use the box as given
#         "dark_bg" = crop to the bright content inside an inset window
#                     (drops the corner watermarks on the black studio shots)
#         "light_bg"= crop to the dark content inside an inset window
JOBS = [
    ("11.png",        "artifact-gold.jpg",      None, 90, "dark_bg"),   # gold cylinder — drop GDH + authority logos
    ("8.png",         "porcelain-plate.jpg",    None, 90, "dark_bg"),   # blue-and-white base
    ("dfdff.png",     "sherd-relief.jpg",       None, 90, "dark_bg"),   # relief-decorated sherd
    ("hfgd8.jpg",     "dirham-scale.jpg",       (0, 128, 1185, 1600), 90, "fixed"),   # Umayyad dirham + scale rule
    ("47-91.png",     "coin-greek.jpg",         None, 90, "light_bg"),  # struck coin on light ground
    ("bef87bdf-d430-49b0-819c-632aa9869438.png", "inscription.jpg", (0, 40, 1257, 700), 90, "fixed"),   # carved inscription
    ("7195313.jpeg",  "excavation.jpg",         (0, 60, 1000, 620), 88, "fixed"),     # excavation trench
    ("al-dhaid-fort-2.webp", "fort-tower.jpg",  (0, 40, 617, 600), 90, "fixed"),      # Al Dhaid round tower
    ("17-gr9.jpg",    "photogrammetry.jpg",     (0, 0, 667, 479), 88, "fixed"),       # digital-twin viewport
]

INSET = 0.16          # fraction of the frame treated as watermark territory
MARGIN = 0.045        # breathing room kept around the detected content


def content_crop(im, mode, inset=INSET, margin=MARGIN):
    """Crop a studio shot down to its subject, ignoring corner watermarks."""
    w, h = im.size
    bx, by = int(w * inset), int(h * inset)
    probe = im.convert("L").crop((bx, by, w - bx, h - by))
    if mode == "dark_bg":                       # subject is brighter than black ground
        mask = probe.point(lambda p: 255 if p > 58 else 0)
    else:                                       # subject is darker than light ground
        mask = probe.point(lambda p: 255 if p < 205 else 0)
    bbox = mask.getbbox()
    if not bbox:
        return im
    x0, y0, x1, y1 = bbox
    pad_x, pad_y = int((x1 - x0) * margin), int((y1 - y0) * margin)
    x0, y0 = max(0, bx + x0 - pad_x), max(0, by + y0 - pad_y)
    x1, y1 = min(w, bx + x1 + pad_x), min(h, by + y1 + pad_y)
    return im.crop((x0, y0, x1, y1))


def build_images():
    for src, dst, box, q, mode in JOBS:
        p = os.path.join(IMG, src)
        if not os.path.exists(p):
            print("missing:", src)
            continue
        im = Image.open(p).convert("RGB")
        if mode != "fixed":
            im = content_crop(im, mode)
        elif box:
            im = im.crop(box)
        im.save(os.path.join(ASSETS, dst), "JPEG", quality=q, optimize=True, progressive=True)
        print(f"{src:44s} -> {dst:24s} {im.size[0]}x{im.size[1]}")


# --------------------------------------------------------------------------
# 2. Fonts: pull the woff2 files and rewrite the CSS to local paths
# --------------------------------------------------------------------------
GOOGLE_CSS = (
    "https://fonts.googleapis.com/css2"
    "?family=Amiri:wght@400;700"
    "&family=IBM+Plex+Sans+Arabic:wght@300;400;600;700"
    "&display=swap"
)
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")


def fetch_fonts():
    req = urllib.request.Request(GOOGLE_CSS, headers={"User-Agent": UA})
    css = urllib.request.urlopen(req, timeout=45).read().decode("utf-8")
    urls = sorted(set(re.findall(r"url\((https://fonts\.gstatic\.com/[^)]+\.woff2)\)", css)))
    mapping = {}
    for i, u in enumerate(urls, 1):
        name = f"f{i:02d}.woff2"
        data = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": UA}),
                                      timeout=45).read()
        with open(os.path.join(FONTS, name), "wb") as fh:
            fh.write(data)
        mapping[u] = name
        print(f"font {name}  {len(data) // 1024} KB")
    local = css
    for remote, local_name in mapping.items():
        local = local.replace(remote, local_name)
    with open(os.path.join(FONTS, "fonts.css"), "w", encoding="utf-8") as fh:
        fh.write(local)
    print(f"fonts.css written ({len(mapping)} files)")


if __name__ == "__main__":
    build_images()
    try:
        fetch_fonts()
    except Exception as exc:  # offline fallback: cards use system Arabic fonts
        print("font download failed:", exc)
