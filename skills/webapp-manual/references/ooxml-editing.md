# Editing an operation-manual .docx (OOXML)

The raw unpack/edit/pack mechanics belong to the **`document-skills:docx`** skill
— use it. This file covers the *manual-specific* patterns: finding a chapter,
the heading/TOC model, the image drawing block, swapping images, the field-spec
table, the EMU math, and the two traps that corrupt the wrong thing.

## Table of contents
- [Finding a section](#finding-a-section)
- [The section writing convention](#the-section-writing-convention)
- [Headings and the Table of Contents](#headings-and-the-table-of-contents)
- [Image drawing blocks](#image-drawing-blocks)
- [Replacing N images with M](#replacing-n-images-with-m)
- [Field-spec tables](#field-spec-tables)
- [The two traps](#the-two-traps)
- [Structural verification](#structural-verification)

## Finding a section

`word/document.xml` is one long file. A chapter is the run of paragraphs from its
heading to the next same-level heading. Locate boundaries by text, but beware the
**heading text also appears in the TOC** — the body occurrence is the one with
the largest line number.

```bash
grep -n '<w:t>五、同險管理</w:t>\|<w:t>六、商品作業</w:t>' word/document.xml
# the larger line number of each is the body heading; the smaller is the TOC entry
```

To understand a section before editing it, extract its skeleton (headings,
images, table rows) rather than reading thousands of lines of XML:

```python
# print TXT/[H2]/<IMG rIdN>/TABLE markers in document order for a line range
import re
lines = open('word/document.xml', encoding='utf-8').read().split('\n')
for ln in lines[START:END]:
    s = ln.strip()
    if '<w:pStyle w:val="2"/>' in s: print('[H2]')
    m = re.search(r'<w:t[^>]*>(.*?)</w:t>', s);  print('TXT:', m.group(1)) if m and m.group(1).strip() else None
    e = re.search(r'r:embed="(rId\d+)"', s);      print(' IMG', e.group(1)) if e else None
```

This skeleton is also your before/after diff: run it again after editing to prove
the section reads the way you intend.

## The section writing convention

Match the manual's existing chapters. The common Traditional-Chinese shape, per
sub-section, is:

```
[H2] 1. <feature name>
【操作路徑】          ［功能群組］→［子頁面］          (breadcrumb; nodes in ［］)
【功能說明】          （1）點擊［篩選］…  （2）點擊［＋新增］…   (numbered; buttons in ［］)
<screenshots>
欄位規格表            a 2-col table: 欄位名稱 | 輸入規則
【注意事項】          optional caveats / preview notes
```

Do not invent a new structure; read two existing sub-sections and mirror them
exactly (the `rPr` font runs too — these manuals pin `eastAsia="標楷體"` with a
Latin face like Calibri on every run). When you "remake" a section, keep this
structure and only refresh the volatile parts: screenshots, dropdown lists,
field rules.

## Headings and the Table of Contents

- Heading level is the paragraph's `<w:pStyle w:val="N"/>` — `"1"`/`"2"`/`"3"` =
  Heading 1/2/3. The TOC's own line styles are different ids (e.g. `"12"`/`"21"`/
  `"31"` for toc1/2/3) — don't confuse the two.
- The TOC is a real Word **field** (`TOC \o "1-3" \h \z \u`), not static text.
  Its visible lines and page numbers are cached. If you **add, remove, or rename
  a heading**, add the matching TOC line(s) with placeholder page numbers, and
  set Word to recalculate on open:

  ```xml
  <!-- in word/settings.xml -->
  <w:updateFields w:val="true"/>
  ```

  Then Word refreshes page numbers (and any you got wrong) the first time the
  user opens the file. If you only change body text *under* an existing heading,
  the TOC is untouched — leave it alone.

## Image drawing blocks

An inline image is a paragraph whose run holds a `<w:drawing>`:

```xml
<w:p w14:paraId="XXXXXXXX" …>
  <w:r>
    <w:rPr><w:noProof/>…</w:rPr>
    <w:drawing>
      <wp:inline …>
        <wp:extent cx="6120130" cy="2273477"/>      <!-- DISPLAY size in EMU -->
        …
        <a:graphic><a:graphicData …><pic:pic>
          <pic:blipFill>
            <a:blip r:embed="rId136"/>              <!-- which media file -->
            <!-- <a:srcRect t=".." b=".."/>  optional crop of the SOURCE image -->
            <a:stretch><a:fillRect/></a:stretch>
          </pic:blipFill>
          <pic:spPr><a:xfrm><a:ext cx="6120130" cy="2273477"/></a:xfrm>…</pic:spPr>
        </pic:pic></a:graphicData></a:graphic>
      </wp:inline>
    </w:drawing>
  </w:r>
</w:p>
```

Key parts: `r:embed` points at a relationship (→ a media file); `<wp:extent>`
**and** the inner `<a:ext>` both carry the display size and should match;
`<a:srcRect>` crops the *source* (omit it if your image is already cropped —
which it is, coming out of `annotate.py`).

**EMU math:** 914400 EMU = 1 inch. Keep `cx` at the content width and scale `cy`
to preserve aspect: `cy = cx * pixel_height / pixel_width`. `doc_ids.py --add`
computes and prints this for each image, using the page's real content width.

Adding the media + relationship + content-type is exactly what `doc_ids.py --add`
automates — run it, then paste the `rId` and `<wp:extent>` it prints into your
new drawing paragraphs.

## Replacing N images with M

When a remade section needs fewer (or different) screenshots than the original:

1. **Delete the surplus image paragraphs first**, by their unique `w14:paraId`.
   Doing deletions *before* any string edits matters — see the duplicate-string
   trap below. A short Python pass with an assertion per deletion is safer than a
   giant multi-line Edit:

   ```python
   import re
   def rm_para(x, pid):
       pat = re.compile(r'    <w:p w14:paraId="%s".*?</w:p>\n' % pid, re.S)
       assert len(pat.findall(x)) == 1, f'{pid}: expected exactly 1'
       return pat.sub('', x, count=1)
   ```

   (Image paragraphs contain no nested `</w:p>`, so the non-greedy `.*?</w:p>`
   matches exactly one paragraph.)

2. **Swap the `r:embed`** on the images you keep to the new rIds, and update both
   `<wp:extent>` and `<a:ext>` to the new dimensions. Drop any `<a:srcRect>` if
   the new image is pre-cropped.

The paragraph-count delta reported by `pack.py` ("Paragraphs: 1324 → 1318 (-6)")
is a free check that you deleted exactly what you meant to.

**Swaps leave orphans.** Deleting a `<a:blip r:embed>` reference does *not* remove
the relationship or the media file — so every swap leaves the old `<Relationship>`
in `document.xml.rels` and the old `imageN.png` in `word/media/`, unreferenced.
These are valid OOXML (Word ignores them) but they pile up and bloat the file
across versions. `doc_ids.py <dir> --orphans` reports them; `--prune-orphans`
deletes the orphan rels and their now-unreferenced media. Pruning is optional and
cosmetic — do it as a deliberate cleanup, not silently inside a content edit.

## Field-spec tables

The 欄位規格表 is a normal `<w:tbl>`: a header row (欄位名稱 / 輸入規則) then one
row per field. To update a dropdown's documented options, replace the `<w:t>`
text of the rule cell. This is where outdated facts hide — e.g. a 險群 dropdown
documented with 12 options when the live `selectMenu.js` now exports 9. Fix the
text to match source, in display order.

## The two traps

**Duplicate-string trap.** The same value often appears in several chapters (the
identical dropdown list documented in both chapter 5 and chapter 6; two adjacent
images with an identical `<wp:extent cx=".." cy="1557655"/>`). A blind
`str.replace` hits all of them. Two defenses, used together:
- Delete surplus paragraphs *first* so that, e.g., the duplicated extent string
  becomes unique before you string-replace it.
- For text that legitimately recurs across chapters, replace with an explicit
  count and assert: `assert x.count(OLD) == 2; x = x.replace(OLD, NEW, 1)` to
  touch only the first (in-scope) occurrence, then `assert x.count(OLD) == 1` to
  prove the other chapter is untouched.

**In-scope-only trap.** "Remake chapter 5" is a fence. If chapter 6 has the same
stale list, **report it; do not fix it**. Silently improving out-of-scope text is
how a tidy edit becomes an unreviewable one. Tell the user it's there and let
them decide.

## Structural verification

You usually can't render the `.docx`. Prove the edit instead. After packing,
unzip the output and check:

```bash
# new images embed and resolve
grep -o 'r:embed="rId13[6-9]"' word/document.xml | sort | uniq -c
grep -o 'Id="rId13[6-9]"[^>]*Target="[^"]*"' word/_rels/document.xml.rels
ls word/media/image12*.png

# old images fully gone
grep -c 'rId10[4-9]\|rId110' word/document.xml          # expect 0

# out-of-scope chapter untouched (the string still occurs its original # of times)
grep -c '新種險／火險／工程險／個人險' word/document.xml   # expect the pre-edit count minus only what you changed
```

Report these as a table, and state plainly that the final "open it in Word and
eyeball the layout" pass is the user's — structural checks can't see a
mis-sized image or an awkward page break.
