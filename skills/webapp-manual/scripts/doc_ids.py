#!/usr/bin/env python3
"""doc_ids.py — image bookkeeping for an unpacked .docx.

Adding an image to a Word document by hand means: find the next free rId, find
the next free imageN filename, copy the file into word/media/, append a
<Relationship> to word/_rels/document.xml.rels, make sure [Content_Types].xml
declares the extension, and compute a <wp:extent> in EMUs that fits the page's
content width. That is five fiddly steps that are easy to get subtly wrong (a
duplicate rId silently breaks the doc). This does them and prints exactly what to
paste into document.xml.

Inspect only:
  python doc_ids.py <unpacked_dir>
      -> highest/next rId, highest/next image number, computed content width

Add images (in the order given; they get consecutive image numbers + rIds):
  python doc_ids.py <unpacked_dir> --add shotA.png shotB.png
      -> copies them in, wires up rels + content-types, prints rId / file /
         pixel size / suggested <wp:extent cx cy> for each.

Report (or clean up) leftover images from past swaps:
  python doc_ids.py <unpacked_dir> --orphans
      -> list image rels/media that document.xml no longer references (a screenshot
         swap leaves the old <Relationship> + media file behind; they pile up and
         bloat the .docx over versions). Read-only.
  python doc_ids.py <unpacked_dir> --prune-orphans
      -> actually delete those orphan rels and their now-unreferenced media files.

Options:
  --width-emu N   Override the content width (EMU) used for extent suggestions.
                  By default it is derived from the document's page size and
                  margins (last <w:sectPr>), so the image spans the text column.
"""
import os
import re
import shutil
import sys
from PIL import Image

EMU_PER_DXA = 635          # 914400 EMU/inch ÷ 1440 DXA/inch
DEFAULT_WIDTH_EMU = 5486400  # 6.0 in — fallback only if page geometry can't be read


def read(path):
    return open(path, encoding="utf-8").read()


def write(path, s):
    open(path, "w", encoding="utf-8").write(s)


def next_rid(rels_xml):
    nums = [int(n) for n in re.findall(r'Id="rId(\d+)"', rels_xml)]
    return (max(nums) if nums else 0) + 1


def next_image_num(media_dir):
    if not os.path.isdir(media_dir):
        return 1
    nums = []
    for f in os.listdir(media_dir):
        m = re.match(r"image(\d+)\.", f)
        if m:
            nums.append(int(m.group(1)))
    return (max(nums) if nums else 0) + 1


def content_width_emu(doc_xml, override=None):
    if override:
        return override, "override"
    # use the last sectPr's geometry (the body's final section). Attribute order
    # in <w:pgMar> follows the schema (top, right, bottom, left, …) — right comes
    # BEFORE left — so pull each attr independently rather than assuming an order.
    sz = list(re.finditer(r'<w:pgSz\b[^>]*\bw:w="(\d+)"', doc_xml))
    mar = list(re.finditer(r'<w:pgMar\b[^>]*/>', doc_xml))
    if not sz or not mar:
        return DEFAULT_WIDTH_EMU, "fallback(no pgSz/pgMar)"
    w = int(sz[-1].group(1))
    tag = mar[-1].group(0)
    lm = re.search(r'\bw:left="(\d+)"', tag)
    rm = re.search(r'\bw:right="(\d+)"', tag)
    if not lm or not rm:
        return DEFAULT_WIDTH_EMU, "fallback(no left/right margin)"
    left, right = int(lm.group(1)), int(rm.group(1))
    dxa = w - left - right
    return dxa * EMU_PER_DXA, f"derived(pgSz {w} - L{left} - R{right} = {dxa} dxa)"


def ensure_content_type(ct_path, ext):
    ct = read(ct_path)
    ext = ext.lower().lstrip(".")
    if re.search(r'<Default\s+Extension="%s"' % re.escape(ext), ct, re.I):
        return
    mime = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
            "gif": "image/gif", "bmp": "image/bmp", "svg": "image/svg+xml"}.get(ext, "image/" + ext)
    decl = f'  <Default Extension="{ext}" ContentType="{mime}"/>\n'
    ct = ct.replace("</Types>", decl + "</Types>", 1)
    write(ct_path, ct)


def find_orphan_image_rels(doc_xml, rels_xml):
    """Image relationships whose rId no r:embed/r:link/r:id in document.xml uses.

    A screenshot swap deletes the <a:blip r:embed="..."> reference but leaves the
    <Relationship> and the media file behind, so they accumulate across versions
    and bloat the .docx. These are valid OOXML (Word ignores them) but unused.
    """
    referenced = set(re.findall(r'r:(?:embed|link|id)="(rId\d+)"', doc_xml))
    orphans = []
    for m in re.finditer(r'<Relationship\b[^>]*/>', rels_xml):
        tag = m.group(0)
        rid = re.search(r'Id="(rId\d+)"', tag)
        tgt = re.search(r'Target="([^"]+)"', tag)
        typ = re.search(r'Type="([^"]*)"', tag)
        if not rid or not tgt:
            continue
        is_image = (typ and 'image' in typ.group(1).lower()) or tgt.group(1).startswith('media/')
        if is_image and rid.group(1) not in referenced:
            orphans.append((rid.group(1), tgt.group(1), tag))
    return orphans


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    root = sys.argv[1]
    doc_xml_path = os.path.join(root, "word", "document.xml")
    rels_path = os.path.join(root, "word", "_rels", "document.xml.rels")
    media_dir = os.path.join(root, "word", "media")
    ct_path = os.path.join(root, "[Content_Types].xml")

    override = None
    if "--width-emu" in sys.argv:
        override = int(sys.argv[sys.argv.index("--width-emu") + 1])

    rels_xml = read(rels_path)
    doc_xml = read(doc_xml_path)
    rid = next_rid(rels_xml)
    imgn = next_image_num(media_dir)
    cw, how = content_width_emu(doc_xml, override)

    print(f"next rId        : rId{rid}")
    print(f"next image num  : image{imgn}")
    print(f"content width   : {cw} EMU  [{how}]  (= {cw/914400:.3f} in)")

    # report (or prune) image rels/media that document.xml no longer references —
    # the residue of past screenshot swaps, which bloats the file over versions.
    if "--orphans" in sys.argv or "--prune-orphans" in sys.argv:
        orphans = find_orphan_image_rels(doc_xml, rels_xml)
        total = sum(os.path.getsize(os.path.join(root, "word", t)) for _, t, _ in orphans
                    if os.path.exists(os.path.join(root, "word", t)))
        print(f"\norphan image rels: {len(orphans)}  (~{total/1024:.0f} KB of unused media)")
        for rid, tgt, _ in orphans:
            print(f"  {rid} -> {tgt}")
        if "--prune-orphans" in sys.argv and orphans:
            still = rels_xml
            for rid, tgt, tag in orphans:
                still = still.replace(tag + "\n", "").replace(tag, "")
                fp = os.path.join(root, "word", tgt)
                # only delete the media file if no remaining relationship targets it
                if os.path.exists(fp) and ('Target="%s"' % tgt) not in still:
                    os.remove(fp)
            write(rels_path, still)
            print(f"pruned {len(orphans)} orphan rels + their unreferenced media.")

    if "--add" not in sys.argv:
        return

    files = sys.argv[sys.argv.index("--add") + 1:]
    files = [f for f in files if not f.startswith("--")]
    os.makedirs(media_dir, exist_ok=True)

    print("\nadded images — paste the rId into <a:blip r:embed> and the extent into <wp:inline>:\n")
    for f in files:
        ext = os.path.splitext(f)[1].lstrip(".").lower()
        target = f"image{imgn}.{ext}"
        shutil.copy(f, os.path.join(media_dir, target))
        with Image.open(f) as im:
            pw, ph = im.size
        cy = round(cw * ph / pw)
        # append relationship
        rel = (f'  <Relationship Id="rId{rid}" '
               f'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" '
               f'Target="media/{target}"/>\n')
        rels_xml = rels_xml.replace("</Relationships>", rel + "</Relationships>", 1)
        ensure_content_type(ct_path, ext)
        print(f"  {f}")
        print(f"      rId{rid}  ->  media/{target}   ({pw}x{ph}px)")
        print(f'      <wp:extent cx="{cw}" cy="{cy}"/>')
        print(f'      <a:blip r:embed="rId{rid}"/>\n')
        rid += 1
        imgn += 1

    write(rels_path, rels_xml)
    print("rels + content-types updated. (document.xml is NOT touched — add the drawing paragraphs yourself.)")


if __name__ == "__main__":
    main()
