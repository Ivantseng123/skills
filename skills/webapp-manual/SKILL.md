---
name: webapp-manual
description: >-
  Build and maintain a software system's operation manual (操作說明書/操作手冊/user
  guide) as a .docx by verifying its pages against the live running web app and
  editing the OOXML directly. Use this whenever the user works on an operation
  manual / user guide .docx for a web system — remaking or adding chapters,
  refreshing outdated screenshots, checking the manual's table of contents
  against the real system, or keeping field / dropdown / menu documentation in
  sync with what the app actually shows. Trigger even when the user only says
  "update the manual", "remake section X", "compare the TOC against the system",
  "the screenshots are stale", or "document this new page" — anytime a doc must
  match a live, authenticated single-page app. Complements the
  document-skills:docx skill (which handles raw unpack/edit/pack mechanics) by
  adding live verification, screenshot annotation, and source-grounded content.
license: MIT
---

# Operation Manual ↔ Live System Sync

## What this skill is for

Operation manuals rot. The app ships a new dropdown, a chapter gets reordered, a
preview screen goes live — and the .docx quietly lies. This skill keeps a
system's operation manual **true to the running system**: every claim grounded
in the live app or its source, every screenshot current, every edit surgical.

It is the workflow layer on top of three lower-level capabilities:

1. **Live verification** — log into an authenticated SPA *without* a Playwright
   MCP server (inject a JWT into `localStorage`), navigate any page, read what it
   actually renders. See `references/live-verification.md`.
2. **Screenshot capture + annotation** — full-page captures with red highlight
   boxes drawn from real element coordinates, then cropped. Scripts in
   `scripts/`.
3. **OOXML section editing** — add/remake/delete chapters, swap images, edit
   field-spec tables and the Table of Contents, following the manual's *existing*
   writing convention. See `references/ooxml-editing.md`.

The raw `.docx` unpack → edit XML → repack mechanics are handled by the
**`document-skills:docx`** skill — use it for that part. This skill tells you
*what* to put in the XML and *how to be sure it's correct*.

## Golden rules (read before touching anything)

- **Ground every claim.** A dropdown's options, a field's validation, a menu's
  routes — do not transcribe from memory or from the old manual. Read it from the
  live app or, better, the frontend source (`selectMenu.js`-style option lists,
  the page component's `v-if` conditions). The old manual is a *suspect*, not a
  source. The most valuable edits this workflow produces are usually **fixing
  outdated facts the old manual got wrong** (a dropdown that lost three options, a
  conditional field the doc never mentioned).
- **Never hardcode secrets.** The JWT, the internal URL, the client name are not
  yours to bake into a script or commit. Tokens come from an environment
  variable; URLs and client identifiers live in a local, untracked config or get
  genericised. If you see a real token in the conversation, keep it in env only.
- **Honesty about preview/mock screens.** If a feature is still mock/preview on
  the live system (hardcoded `default1` options, empty charts, placeholder data),
  say so in the manual and keep any "僅供參考 / for reference only" caveat. A
  current screenshot of a mock screen *is* the honest documentation — the
  placeholder data is the evidence.
- **Stay in scope.** "Remake chapter 5" means chapter 5. If you notice the same
  stale dropdown list also appears in chapter 6, **report it, don't silently
  fix it** — a value that occurs in two chapters and a blind replace-all is how
  you edit the thing you weren't asked to touch.
- **Verify, but know your limits.** With no LibreOffice you cannot render the
  .docx to confirm layout visually. Do thorough *structural* verification (pack
  validation, grep that new relationships resolve, old ones are gone, scope-
  preserved chapters are untouched) and tell the user plainly that the final
  "open it and eyeball the layout" step is theirs.

## The core loop

```
   ┌─ 1. SCOPE ──────────────────────────────────────────────────┐
   │   What changed / what's asked? Bound it to specific chapters. │
   └──────────────────────────────────────────────────────────────┘
                              │
   ┌─ 2. VERIFY ─────────────────────────────────────────────────┐
   │   Drive the live app + read frontend source. Find the truth: │
   │   missing pages, wrong dropdowns, renamed fields, mock state. │
   └──────────────────────────────────────────────────────────────┘
                              │
   ┌─ 3. CAPTURE ────────────────────────────────────────────────┐
   │   Playwright: inject JWT, open the drawer, screenshot pages,  │
   │   record element boundingBoxes for annotation.               │
   └──────────────────────────────────────────────────────────────┘
                              │
   ┌─ 4. ANNOTATE ───────────────────────────────────────────────┐
   │   PIL: draw red boxes from the recorded boxes, crop to the    │
   │   meaningful band. Consolidate redundant near-identical shots.│
   └──────────────────────────────────────────────────────────────┘
                              │
   ┌─ 5. EDIT ───────────────────────────────────────────────────┐
   │   Unpack (docx skill). Insert/replace media + rels, rewrite   │
   │   the section following the manual's convention, fix the TOC. │
   └──────────────────────────────────────────────────────────────┘
                              │
   ┌─ 6. REPACK + VERIFY ────────────────────────────────────────┐
   │   Pack with validation. Grep-check refs, scope, counts.       │
   │   Hand the visual eyeball-check to the user.                 │
   └──────────────────────────────────────────────────────────────┘
```

You will not always run all six — "the TOC is missing two pages" stops at VERIFY
plus a small EDIT. "Remake this chapter with current screenshots" runs the whole
loop. Read the request and pick the arc.

## Step-by-step

### 1 · Scope

State, in one or two lines, exactly which chapters/sections you will touch and
which you will not. Find the section's boundaries in `word/document.xml` (the
heading text, its bookmark, the next chapter's heading) before editing — see
`references/ooxml-editing.md` § "Finding a section".

### 2 · Verify against the live system

First find the **ground truth for navigation and options in the frontend
source**, not by clicking around: the menu/route table (e.g. a `theNavigator`
component), the option lists (`selectMenu.js`-style files), and the page
component's conditional-field logic (`v-if="isProductGroupFiOrEg(...)"`). A grep
here answers "what are the dropdown's real values?" definitively.

Then confirm the live render with Playwright. Full technique (JWT injection, no
router-guard deep-linking, reading Vue component data when the DOM is lazy):
`references/live-verification.md`.

### 3 · Capture screenshots

Use `scripts/capture_pages.js`. It reads a small JSON config (base URL, the
`localStorage` auth keys with `${JWT}` pulled from env, and a list of pages with
their routes, pre-actions like "expand the filter / open the add dialog", and the
selectors whose boundingBoxes you want recorded). It opens the nav drawer if it
is off-canvas, screenshots each page full, and writes a `meta.json` of recorded
boxes + the deviceScaleFactor.

```bash
# run from the playwright project dir (or set NODE_PATH) so require('playwright') resolves
JWT="$THE_TOKEN" NODE_PATH=/tmp/pw/node_modules \
  node /path/to/skill/scripts/capture_pages.js config.json out/
```

A de-identified sample config is in `references/example-walkthrough.md`.
**Auth must be complete** — an incomplete `localStorage` session makes the app
redirect to `/login` and capture silently screenshots the login page (every box
null). Mirror a real manual login's keys; see the reference.

### 4 · Annotate + crop

Use `scripts/annotate.py`. It reads the same config + `meta.json`, draws red
boxes (scaled by deviceScaleFactor) around the selectors you flagged to
highlight, and crops each image to its configured band.

```bash
python scripts/annotate.py config.json out/ out/final/
```

**Consolidate.** Old manuals often pad a section with three near-identical list
screenshots that differ only in which button has a red box. One clean annotated
shot per *distinct UI state* reads better and is what "remake" should produce —
keep the section's writing *structure*, drop the redundant frames. Say so when
you do it.

Images wider than ~2000px cannot be viewed directly — downscale/stack a preview
with PIL to sanity-check boxes before embedding (see annotate.py `--preview`).

### 5 · Edit the OOXML

Unpack with the docx skill. Then, per `references/ooxml-editing.md`:

- **Add the images**: `scripts/doc_ids.py <unpacked> --add a.png b.png …` copies
  them into `word/media/`, appends the `<Relationship>` entries, ensures the
  content-type, and prints each new `rId`, file name, and a suggested
  `<wp:extent>` (pixel→EMU at the manual's content width). This is the fiddly
  bookkeeping the script exists to kill.
- **Rewrite the section** following the manual's own convention. The common
  Chinese-manual shape is: 【操作路徑】breadcrumb → 【功能說明】numbered actions
  (buttons in ［］) → screenshots → 欄位規格表 (field name / input rule) →
  【注意事項】. Match whatever the existing chapters do.
- **Replace N images with M**: delete whole image paragraphs by their
  `w14:paraId`, swap the `r:embed` rId on the ones you keep, update extents.
  Do deletions *first* so that duplicated extent strings become unique and safe
  to string-replace. The duplicate-string trap is real — see the reference.
- **Fix the TOC** if you added/removed/renamed headings: add the matching `toc`
  entries and set `<w:updateFields w:val="true"/>` in `settings.xml` so Word
  recalculates page numbers on open.

For multi-paragraph structural deletions, a short Python script with
`assert count == expected` on every match is *safer* than a giant fragile
multi-line Edit — the assertions catch a mismatch before it corrupts the file.
For single targeted string swaps, the Edit tool is clearer. Use the right one.

### 6 · Repack and verify structurally

Pack via the docx skill's `pack.py … --original <previous.docx>` (validation on).
Then prove the edit, since you can't see it:

- the new `rId`s embed and resolve to the new media files;
- the old `rId`s / images are **gone** (count 0);
- chapters you were told **not** to touch are byte-for-byte unchanged
  (grep the in-scope-only string still appears its original number of times
  elsewhere);
- paragraph delta matches what you intended to delete.

Report the checks as a table and explicitly hand off the visual layout check.

## Prerequisites

- **Playwright**: `npm i playwright && npx playwright install chromium` (a throwaway
  project under `/tmp` is fine). Run `capture_pages.js` from that project directory,
  or set `NODE_PATH=<that-project>/node_modules`, so `require('playwright')`
  resolves — calling it from the skill dir alone fails with `MODULE_NOT_FOUND`.
- **Python deps for the docx + annotation scripts**: the `document-skills:docx`
  pack/unpack scripts need `defusedxml` + `lxml`; annotation needs `Pillow`.
  macOS is PEP-668 "externally managed" — make a venv:
  `python3 -m venv /tmp/docxvenv && /tmp/docxvenv/bin/pip install defusedxml lxml Pillow pypdf`
  and call scripts with `/tmp/docxvenv/bin/python`.
- **No LibreOffice assumed** — structural verification only. If `soffice` happens
  to be installed you may render to PDF for a visual check, but never install it
  unprompted.

## Reference map

- `references/live-verification.md` — JWT-into-localStorage auth, no-MCP
  Playwright, deep-linking past the router guard, reading lazy Vue data, drawer
  and timeout gotchas, discovering routes/menus from source.
- `references/ooxml-editing.md` — finding a section, the heading/TOC model,
  image `<w:drawing>` anatomy, add/replace/delete images, EMU math, the
  duplicate-string and in-scope-only traps, field-spec tables, structural
  verification recipes.
- `references/example-walkthrough.md` — a full de-identified worked example: comparing a
  TOC against the live system, adding missing report pages, remaking a chapter
  with fresh annotated screenshots, and fixing an outdated dropdown list — with a
  sample `capture_pages.js` config.
- `scripts/capture_pages.js` — config-driven Playwright capture + boundingBox
  recorder.
- `scripts/annotate.py` — red-box annotation + crop + preview stacker.
- `scripts/doc_ids.py` — next free rId/image number; `--add` to wire images into
  an unpacked docx and print suggested extents.
