#!/usr/bin/env python3
"""annotate.py — draw red highlight boxes on captured screenshots and crop them.

Pairs with capture_pages.js. It reads the same config plus the meta.json that
capture wrote (which holds each recorded element's boundingBox, in CSS pixels,
and the deviceScaleFactor). Screenshots are at deviceScaleFactor resolution, so
every boundingBox must be multiplied by it before drawing — that off-by-2x is
the classic mistake.

Per page, the config's "annotate" block says which recorded boxes to outline and
where to crop:

  "pages": [
    {
      "name": "info_list",
      ...capture fields...,
      "annotate": {
        "highlight": ["filter", "add"],   // box names from this page's "boxes"
        "crop": [0, 0, null, 1040]        // [left, top, right, bottom]; null = image edge
      }
    }
  ]

Usage:
  python annotate.py config.json captured_dir/ output_dir/
  python annotate.py config.json captured_dir/ output_dir/ --preview preview.png

--preview stacks every output image (downscaled to a viewable width) into one
PNG so you can eyeball the boxes before embedding — individual captures are
usually wider than 2000px and can't be opened directly.
"""
import json
import os
import sys
from PIL import Image, ImageDraw

RED = (229, 57, 53)  # Material red 600 — reads clearly on light Vuetify UIs


def draw_box(draw, b, scale, pad=10, width=6):
    """Outline boundingBox b (CSS px) scaled to screenshot px, with padding."""
    x0 = b["x"] * scale - pad
    y0 = b["y"] * scale - pad
    x1 = (b["x"] + b["width"]) * scale + pad
    y1 = (b["y"] + b["height"]) * scale + pad
    for i in range(width):
        draw.rectangle([x0 - i, y0 - i, x1 + i, y1 + i], outline=RED)


def crop_box(im, crop):
    if not crop:
        return im
    l, t, r, b = crop
    r = im.width if r is None else r
    b = im.height if b is None else b
    return im.crop((l or 0, t or 0, r, b))


def main():
    if len(sys.argv) < 4:
        print("usage: python annotate.py config.json captured_dir/ output_dir/ [--preview out.png]")
        sys.exit(2)
    cfg = json.load(open(sys.argv[1], encoding="utf-8"))
    cap_dir = sys.argv[2]
    out_dir = sys.argv[3]
    preview_path = None
    if "--preview" in sys.argv:
        preview_path = sys.argv[sys.argv.index("--preview") + 1]
    os.makedirs(out_dir, exist_ok=True)

    meta = json.load(open(os.path.join(cap_dir, "meta.json"), encoding="utf-8"))
    scale = meta.get("deviceScaleFactor", 2)

    produced = []
    for p in cfg["pages"]:
        name = p["name"]
        src = os.path.join(cap_dir, name + ".png")
        if not os.path.exists(src):
            print(f"skip {name}: {src} missing")
            continue
        im = Image.open(src).convert("RGB")
        d = ImageDraw.Draw(im)
        ann = p.get("annotate", {})
        recorded = meta["pages"].get(name, {}).get("boxes", {})
        for box_name in ann.get("highlight", []):
            b = recorded.get(box_name)
            if not b:
                print(f"  {name}: box '{box_name}' had no boundingBox (selector missed?) — skipping")
                continue
            draw_box(d, b, scale, pad=ann.get("pad", 10), width=ann.get("width", 6))
        im = crop_box(im, ann.get("crop"))
        dst = os.path.join(out_dir, name + ".png")
        im.save(dst)
        produced.append((name, dst, im.size))
        print(f"  {name}: {im.size} -> {dst}")

    if preview_path and produced:
        cols_w = 900
        thumbs = []
        for name, dst, _ in produced:
            t = Image.open(dst).convert("RGB")
            r = cols_w / t.width
            thumbs.append((name, t.resize((cols_w, int(t.height * r)))))
        pad = 22
        H = sum(t.height + pad for _, t in thumbs)
        canvas = Image.new("RGB", (cols_w, H), "white")
        dd = ImageDraw.Draw(canvas)
        y = 0
        for name, t in thumbs:
            dd.rectangle([0, y, cols_w, y + pad - 2], fill=(20, 20, 20))
            dd.text((6, y + 5), name, fill="white")
            canvas.paste(t, (0, y + pad))
            y += t.height + pad
        canvas.save(preview_path)
        print(f"preview -> {preview_path} {canvas.size}")


if __name__ == "__main__":
    main()
