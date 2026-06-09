---
name: webapp-manual
description: >-
  Build a web system's operation manual (操作說明書/操作手冊/user guide) as a .docx
  from scratch, or maintain an existing one — grounding every page on the live
  running app and editing the OOXML directly. Use this whenever the user works on
  an operation-manual / user-guide .docx for a web system: building a brand-new
  manual (enumerating the nav bar into a table of contents, then documenting each
  screen with function descriptions, annotated screenshots, and field-spec
  tables), remaking or adding chapters, refreshing stale screenshots, auditing the
  table of contents against the real system, or keeping field / dropdown / menu
  documentation in sync with what the app actually shows. Trigger even when the
  user only says "build the operation manual from scratch", "list the menu as a
  TOC and document each page", "update the manual", "remake section X", "compare
  the TOC against the system", "the screenshots are stale", or "document this new
  page" — anytime a doc must match a live, authenticated single-page app. Live
  verification and capture need browser automation — the bundled Playwright
  script (Node + `playwright`) or a Playwright MCP in the agent.
  Complements the document-skills:docx skill (which handles raw unpack/edit/pack
  mechanics) by adding live verification, screenshot annotation, and
  source-grounded content.
license: MIT
---

# Web-System Operation Manual: Build & Sync

## What this skill is for

This skill produces a web system's operation manual (操作說明書 / 操作手冊) as a
`.docx` and keeps it **true to the running system** — every claim grounded in the
live app or its source, every screenshot current, every edit surgical. It works
in two modes:

- **Build from scratch** — no manual exists yet. Enumerate the app's navigation,
  turn it into a table of contents, then document each screen in order: function
  description, annotated screenshots, field-spec table. Start from the clean
  skeleton in `assets/manual-template.docx`. See `references/building-from-scratch.md`.
- **Maintain** — a manual exists but rots. The app ships a new dropdown, a chapter
  gets reordered, a preview screen goes live, and the `.docx` quietly lies. Remake
  a chapter, refresh stale screenshots, audit the TOC against the real system.

Both modes share the same engine and rest on three lower-level capabilities:

1. **Live verification** — sign in to the deployed app and read what each page
   actually renders. This needs browser automation — the bundled Playwright
   capture script (no MCP required) or a Playwright MCP if the agent has one (see
   Prerequisites). **Don't assume
   how it authenticates** — read the source first (login form? router guard? token
   in `localStorage` / cookie / `sessionStorage`?) and pick the sign-in method
   with the user. See `references/live-verification.md`.
2. **Screenshot capture + annotation** — full-page captures with red highlight
   boxes drawn from real element coordinates, then cropped. Scripts in
   `scripts/`.
3. **OOXML section editing** — add/remake/delete chapters, swap images, edit
   field-spec tables and the Table of Contents, following the manual's *existing*
   writing convention (or the template's, when building fresh). See
   `references/ooxml-editing.md`.

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
- **Never hardcode secrets.** The session token, login credentials, the internal
  URL, the client name are not yours to bake into a script or commit. Tokens and
  passwords come from environment variables; URLs and client identifiers live in a
  local, untracked config or get genericised. If you see a real token or password
  in the conversation, keep it in env only.
- **Honesty about preview/mock screens.** If a feature is still mock/preview on
  the live system (hardcoded `default1` options, empty charts, placeholder data),
  say so in the manual and keep any "僅供參考 / for reference only" caveat. A
  current screenshot of a mock screen *is* the honest documentation — the
  placeholder data is the evidence.
- **Stay in scope.** "Remake chapter 5" means chapter 5. If you notice the same
  stale dropdown list also appears in chapter 6, **report it, don't silently
  fix it** — a value that occurs in two chapters and a blind replace-all is how
  you edit the thing you weren't asked to touch.
- **A manual is TOC-ready or it isn't done.** The 目錄 (Table of Contents) is a
  Word *field* generated from the heading styles — structural, not optional
  decoration. Build a standalone `.docx` from `assets/manual-template.docx`, which
  already carries a working TOC field set to update-on-open, rather than
  hand-rolling bare chapters straight from python-docx — that is exactly how a TOC
  silently goes missing. A single chapter still carries its own heading styles so a
  parent manual's TOC catches it; deliver it standalone and you keep the template's
  TOC field. Don't hand a manual back without its 目錄 unless the user explicitly
  asked for a bare fragment.
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
   │   Establish access (analyse the app's auth, pick a sign-in    │
   │   method). Read frontend source for the truth: menu/routes,   │
   │   dropdowns, renamed fields, mock state.                     │
   └──────────────────────────────────────────────────────────────┘
                              │
   ┌─ 3. CAPTURE ────────────────────────────────────────────────┐
   │   Playwright: sign in, open the drawer, screenshot each page, │
   │   record element boundingBoxes for annotation.               │
   └──────────────────────────────────────────────────────────────┘
                              │
   ┌─ 4. ANNOTATE ───────────────────────────────────────────────┐
   │   PIL: draw red boxes from the recorded boxes, crop to the    │
   │   meaningful band. Consolidate redundant near-identical shots.│
   └──────────────────────────────────────────────────────────────┘
                              │
   ┌─ 5. EDIT ───────────────────────────────────────────────────┐
   │   Unpack (docx skill). Insert/replace media + rels, write the │
   │   section in the manual's convention, fix the TOC.           │
   └──────────────────────────────────────────────────────────────┘
                              │
   ┌─ 6. REPACK + VERIFY ────────────────────────────────────────┐
   │   Pack with validation. Grep-check refs, scope, counts.       │
   │   Hand the visual eyeball-check to the user.                 │
   └──────────────────────────────────────────────────────────────┘
```

Two modes feed this loop. **Maintain**: bound the work to the chapters that
changed and run only the arc you need — "the TOC is missing two pages" stops at
VERIFY plus a small EDIT; "remake this chapter with current screenshots" runs the
whole loop. **Build from scratch**: there's no manual yet, so prepend one step —
enumerate the app's navigation and scaffold a table of contents from
`assets/manual-template.docx` — then run the loop once per chapter, in nav order.
See `references/building-from-scratch.md`. Read the request and pick the arc.

## Step-by-step

### 1 · Scope

State, in one or two lines, exactly which chapters/sections you will touch and
which you will not. When **maintaining**, find the section's boundaries in
`word/document.xml` (the heading text, its bookmark, the next chapter's heading)
before editing — see `references/ooxml-editing.md` § "Finding a section". When
**building from scratch**, scope is which slice of the nav tree you'll document
this pass (see "Building a manual from scratch" below).

### 2 · Verify against the live system

First find the **ground truth for navigation and options in the frontend
source**, not by clicking around: the menu/route table (e.g. a `theNavigator`
component), the option lists (`selectMenu.js`-style files), and the page
component's conditional-field logic (`v-if="isProductGroupFiOrEg(...)"`). A grep
here answers "what are the dropdown's real values?" definitively.

**Establish access — don't assume the sign-in method.** Before capturing, work
out how the app authenticates by reading its source: is there a login form? A
router guard (or is the auth check commented out)? Where does the token live —
`localStorage`, a cookie, `sessionStorage`? Is it a JWT or an opaque session?
Then **ask the user which method to use, and for the credentials or token**:

- **Real form login** is preferred when you have an account — the app writes its
  own complete session, so there's nothing to reverse-engineer.
- **Token-into-`localStorage` injection** is the fallback when you only hold a
  token and the app permits it (often when there's no router guard).
- **httpOnly cookie session or SSO redirect** aren't covered by the capture
  script's two built-in modes — surface that to the user and decide together.

`capture_pages.js` supports both built-in modes (an `auth` block and a `login`
block); the full technique — picking the method, deep-linking past a router
guard, reading Vue component data when the DOM is lazy — is in
`references/live-verification.md`.

### 3 · Capture screenshots

Capture needs browser automation (see Prerequisites): either your agent's
Playwright MCP, or the bundled script below. With an MCP, drive the same flow
through its tools — navigate → sign in → screenshot, recording the element boxes
you'll annotate — replicating what `capture_pages.js` does. The bundled, no-MCP
path:

Use `scripts/capture_pages.js`. It reads a small JSON config (base URL; the auth
block for the method you chose — a `login` block with form credentials, or an
`auth` block of `localStorage` keys — with secrets interpolated from env; and a
list of pages with their routes, pre-actions like "expand the filter / open the
add dialog", and the selectors whose boundingBoxes you want recorded). It opens
the nav drawer if it is off-canvas, screenshots each page full, and writes a
`meta.json` of recorded boxes + the deviceScaleFactor.

```bash
# run from the playwright project dir (or set NODE_PATH) so require('playwright') resolves
# token-injection example; for form login export APP_USER / APP_PASS instead
JWT="$THE_TOKEN" NODE_PATH=/tmp/pw/node_modules \
  node /path/to/skill/scripts/capture_pages.js config.json out/
```

A de-identified sample config is in `references/example-walkthrough.md`.
**Whichever method, confirm the session actually took.** With token injection an
incomplete `localStorage` session makes the app clear the keys and redirect to
`/login`; with form login a wrong selector or env var submits a blank form. Either
way capture then silently screenshots the login page (every box null). The script
hard-fails when the post-login URL is still `/login` — heed it; see the reference.

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
- **Write the section** in the manual's convention. The common Traditional-Chinese
  shape is: 【操作路徑】breadcrumb → 【功能說明】numbered actions (buttons in ［］)
  → screenshots → 欄位規格表 (field name / input rule) → 【注意事項】. When
  *maintaining*, match whatever the existing chapters already do; when *building
  from scratch*, follow the shape in `assets/manual-template.docx` (and
  `references/building-from-scratch.md`).
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

## Building a manual from scratch

When no manual exists yet, two steps come *before* the per-screen loop above:

1. **Enumerate the navigation = your table of contents.** The left menu / route
   table is static frontend data — read it from source (the `theNavigator`-style
   component, or the Vue `__vue__` menu state), not by clicking around. That nav
   tree, in order, *is* the chapter outline: top-level groups → chapters, leaf
   routes → sub-sections. Confirm it against the live app and agree the outline
   with the user before writing anything.
2. **Start from the skeleton, not a blank page.** `assets/manual-template.docx`
   is a clean shell with the heading styles, the 標楷體 `eastAsia` font runs, a
   working TOC field, and one example chapter in the canonical section shape.
   Copy it, set the title, and grow the TOC from the nav outline.

Then run VERIFY → CAPTURE → ANNOTATE → EDIT once per screen, in nav order,
filling the section shape for each. Do it **incrementally — one chapter at a
time**: a whole app is dozens of screens and dozens of screenshots, and batching
it all into one pass is how you lose track of what's grounded and what's invented.
Full walkthrough: `references/building-from-scratch.md`.

## Prerequisites

- **Browser automation (required for live verification + capture).** Two ways —
  use whichever your environment has:
  - **Bundled Playwright script (no MCP).** `npm i playwright && npx playwright
    install chromium` (a throwaway project under `/tmp` is fine). Run
    `capture_pages.js` from that project directory, or set
    `NODE_PATH=<that-project>/node_modules`, so `require('playwright')` resolves —
    calling it from the skill dir alone fails with `MODULE_NOT_FOUND`. Encapsulates
    the JWT-injection / drawer / boundingBox handling.
  - **A Playwright MCP in the agent.** If the agent already has one, drive capture
    through it instead — navigate, sign in, screenshot, read the DOM — replicating
    what `capture_pages.js` does (its encapsulated logic isn't there). Token-into-
    `localStorage` injection needs an MCP that can run an init script *before* page
    load; form login works on any.
  - **Neither set up? Say so.** This is the one external thing the skill can't do
    itself — tell the user to install one before the capture step.
- **Python deps for the docx + annotation scripts**: the `document-skills:docx`
  pack/unpack scripts need `defusedxml` + `lxml`; annotation needs `Pillow`.
  macOS is PEP-668 "externally managed" — make a venv:
  `python3 -m venv /tmp/docxvenv && /tmp/docxvenv/bin/pip install defusedxml lxml Pillow pypdf`
  and call scripts with `/tmp/docxvenv/bin/python`.
- **No LibreOffice assumed** — structural verification only. If `soffice` happens
  to be installed you may render to PDF for a visual check, but never install it
  unprompted.

## Reference map

- `references/live-verification.md` — analysing the app's auth and choosing a
  sign-in method (form login vs token-into-localStorage), no-MCP Playwright,
  deep-linking past the router guard, reading lazy Vue data, drawer and timeout
  gotchas, discovering routes/menus from source.
- `references/building-from-scratch.md` — the greenfield mode: enumerating the nav
  into a table of contents, starting from the template skeleton, and the
  incremental per-chapter build order.
- `references/ooxml-editing.md` — finding a section, the heading/TOC model,
  image `<w:drawing>` anatomy, add/replace/delete images, EMU math, the
  duplicate-string and in-scope-only traps, field-spec tables, structural
  verification recipes.
- `references/example-walkthrough.md` — a full de-identified worked example: comparing a
  TOC against the live system, adding missing report pages, remaking a chapter
  with fresh annotated screenshots, and fixing an outdated dropdown list — with a
  sample `capture_pages.js` config.
- `assets/manual-template.docx` — a clean skeleton manual (heading styles, 標楷體
  font, a working TOC field, one placeholder chapter in the canonical section
  shape) to start a from-scratch build from. No real content.
- `scripts/capture_pages.js` — config-driven Playwright capture + boundingBox
  recorder (form-login and token-injection auth modes).
- `scripts/annotate.py` — red-box annotation + crop + preview stacker.
- `scripts/doc_ids.py` — next free rId/image number; `--add` to wire images into
  an unpacked docx and print suggested extents.
