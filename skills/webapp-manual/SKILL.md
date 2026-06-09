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

Produce a web system's operation manual (操作說明書 / 操作手冊) as a `.docx` and keep
it **true to the running system** — every claim grounded in the live app or its
source, every screenshot current, every edit surgical. Two modes:

- **Build from scratch** — no manual yet. Enumerate the nav into a table of
  contents, then document each screen (function description → annotated screenshots
  → field-spec table), starting from `assets/manual-template.docx`. See
  `references/building-from-scratch.md`.
- **Maintain** — a manual exists but rots. Remake a chapter, refresh stale
  screenshots, audit the TOC against the real system.

Both rest on three capabilities: **live verification** (sign in to the deployed app
and read what it renders — don't assume the auth method, read the source first;
`references/live-verification.md`), **screenshot capture + annotation** (`scripts/`),
and **OOXML section editing** (`references/ooxml-editing.md`). The raw `.docx`
unpack → edit → repack is the **`document-skills:docx`** skill's job; this skill
tells you *what* to put in the XML and *how to be sure it's correct*.

## Golden rules (read before touching anything)

- **Ground every claim — in the right source.** Never transcribe from memory or the
  old manual (it's a *suspect*). The **frontend** is authoritative for the UI
  surface: menu / routes, field labels, conditional display (`v-if`), and
  frontend-hardcoded dropdown options (`selectMenu.js`-style). The **backend** is
  authoritative for what the UI can't prove: a field's real input rules (required /
  length / format — in DTO/validator annotations, not the UI's soft checks), options
  served from an API or DB enum, and the business logic a function actually runs. The
  欄位規格表's input-rule column is where the backend matters most. The highest-value
  edits are usually **fixing outdated facts the old manual got wrong**.
- **Never hardcode secrets.** The session token, credentials, internal URL, and
  client name are not yours to bake into a script or commit. Tokens/passwords come
  from env vars; URLs and client identifiers live in a local untracked config or get
  genericised. A real token in the conversation stays in env only.
- **Honesty about preview/mock screens.** If a feature is still mock/preview
  (hardcoded `default1` options, empty charts, placeholder data), say so and keep a
  "僅供參考 / for reference only" caveat — a current screenshot of a mock screen *is*
  the honest documentation.
- **Stay in scope.** "Remake chapter 5" means chapter 5. If the same stale dropdown
  also appears in chapter 6, **report it, don't silently fix it** — a blind
  replace-all of a value that recurs across chapters edits what you weren't asked to.
- **A manual is TOC-ready or it isn't done.** The 目錄 is a Word *field* generated
  from heading styles — structural, not decoration. Build a standalone `.docx` from
  `assets/manual-template.docx` (it carries a TOC field set to update-on-open), not
  by hand-rolling bare chapters from python-docx — that's exactly how a TOC goes
  missing. Don't hand back a manual without its 目錄 unless the user asked for a bare
  fragment.
- **Verify, but know your limits.** Without LibreOffice you can't render the `.docx`
  to check layout. Do thorough *structural* verification (pack validation, grep that
  new rels resolve / old ones are gone / untouched chapters are unchanged) and tell
  the user plainly that the final eyeball-the-layout step is theirs.

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

Two modes feed this loop. **Maintain**: bound the work to the changed chapters and
run only the arc you need (a missing TOC entry stops at VERIFY + a small EDIT; a
chapter remake runs the whole loop). **Build from scratch**: prepend one step —
enumerate the nav and scaffold a TOC from `assets/manual-template.docx` — then run
the loop once per chapter, in nav order. Read the request and pick the arc.

## Step-by-step

1. **Scope.** State in a line or two exactly which chapters you'll touch and which
   you won't. Maintaining: find the section's boundaries in `word/document.xml`
   first (`ooxml-editing.md` § "Finding a section"). Building: scope is which slice
   of the nav tree you document this pass.

2. **Verify against the live system.** Find ground truth in **source** first, not by
   clicking. The **frontend** gives the menu/route table, the `selectMenu.js`-style
   option lists, and the page's conditional-field `v-if` logic. The **backend** gives
   what the frontend can't: a field's authoritative input rules (validator / DTO
   constraints), options served from an API or DB enum, and the business logic behind
   a function — read it when the 欄位規格表 or 功能說明 must be precise. Then
   **establish access without assuming
   the method**: read the source for how it authenticates (login form? router guard?
   token in localStorage / cookie / sessionStorage? JWT or opaque?), then ask the
   user which to use. Form login is preferred (the app writes a complete session);
   token-into-`localStorage` injection is the fallback; httpOnly-cookie / SSO aren't
   covered by the script — surface them. Full technique: `references/live-verification.md`.

3. **Capture.** Browser automation required (see Prerequisites) — your agent's
   Playwright MCP, or the bundled `scripts/capture_pages.js` (config-driven: base
   URL, the chosen auth block with secrets from env, and the pages with their routes
   / pre-actions / boundingBox selectors). **Whichever method, confirm the session
   took** — an incomplete session or a failed form login silently screenshots the
   `/login` page with null boxes; the script hard-fails on a post-login `/login`
   URL, heed it. Sample config: `references/example-walkthrough.md`.

4. **Annotate + crop.** `scripts/annotate.py` draws red boxes from the recorded
   boxes (scaled by deviceScaleFactor) and crops to the meaningful band.
   **Consolidate** — one clean annotated shot per *distinct UI state*, not three
   near-identical frames differing only in which button is boxed; say so when you
   drop frames. Shots wider than ~2000px can't be viewed directly — use
   `annotate.py --preview`. (No capture `meta.json`? It runs crop-only; supply
   `annotate.boxesPx` for manual boxes.)

5. **Edit the OOXML** (unpack via the docx skill; full detail in `ooxml-editing.md`):
   - **Add images** with `scripts/doc_ids.py <unpacked> --add a.png …` — it wires
     media + rels + content-type and prints each `rId` and a suggested `<wp:extent>`.
   - **Write the section** in the manual's convention — the common shape is
     【操作路徑】 → 【功能說明】(buttons in ［］) → screenshots → 欄位規格表 → 【注意事項】.
     Maintaining: match the existing chapters. Building: follow the template.
   - **Replace N images with M**: delete whole image paragraphs by `w14:paraId`
     *first* (so duplicated extent strings become unique), then swap `r:embed` rIds.
   - **Fix the TOC** for any added/removed/renamed heading, and set
     `<w:updateFields w:val="true"/>` in `settings.xml`.
   For multi-paragraph structural deletes, a short Python pass with
   `assert count == expected` per match beats a giant fragile Edit.

6. **Repack + verify structurally.** Pack via the docx skill's `pack.py …
   --original <prev.docx>` (validation on). Then prove the edit, since you can't see
   it: new `rId`s resolve to the new media; old ones are gone (count 0); out-of-scope
   chapters are byte-for-byte unchanged; the paragraph delta matches your intent.
   Report the checks as a table and hand the visual layout check to the user.

## Building a manual from scratch

Two steps come *before* the per-screen loop. **(1) The navigation is your table of
contents** — read the nav/route table from source (not by clicking), map it to the
outline (top groups → chapters, leaf routes → sub-sections), and agree it with the
user before writing. **(2) Start from `assets/manual-template.docx`**, not a blank
page — it carries the heading styles, 標楷體 font, and a working TOC field; copy it,
set the title, grow the TOC from the outline. Then run the loop once per screen, in
nav order, **incrementally — one chapter at a time** (batching a whole app is how
you lose track of grounded vs invented). Full walkthrough:
`references/building-from-scratch.md`.

## Prerequisites

- **Browser automation** (for live verification + capture) — one of: the **bundled
  Playwright script** (`npm i playwright && npx playwright install chromium` in a
  throwaway project; run `capture_pages.js` from there or set `NODE_PATH` so
  `require('playwright')` resolves), or **a Playwright MCP** in the agent (note:
  token-into-`localStorage` injection needs an MCP that runs an init script *before*
  page load; form login works on any). If neither is set up, that's the one external
  thing the skill can't do itself — tell the user.
- **Python deps**: `defusedxml` + `lxml` for the docx pack/unpack, `Pillow` for
  annotation. On macOS (PEP-668) use a venv:
  `python3 -m venv /tmp/docxvenv && /tmp/docxvenv/bin/pip install defusedxml lxml Pillow pypdf`.
- **No LibreOffice assumed** — structural verification only; never install `soffice`
  unprompted.

## Reference map

- `references/live-verification.md` — analysing auth + choosing a sign-in method,
  no-MCP Playwright, deep-linking past the router guard, reading lazy Vue data,
  drawer/timeout gotchas, discovering routes/menus from source.
- `references/building-from-scratch.md` — greenfield mode: nav → table of contents,
  starting from the template skeleton, the incremental per-chapter order.
- `references/ooxml-editing.md` — finding a section, the heading/TOC model, image
  `<w:drawing>` anatomy, add/replace/delete images, EMU math, the duplicate-string
  and in-scope-only traps, field-spec tables, structural verification.
- `references/example-walkthrough.md` — a full de-identified worked example (TOC
  audit + chapter remake) with a sample `capture_pages.js` config.
- `assets/manual-template.docx` — clean skeleton (heading styles, 標楷體, a working
  TOC field, one placeholder chapter) to start a from-scratch build. No real content.
- `scripts/capture_pages.js` — config-driven Playwright capture + boundingBox
  recorder (form-login and token-injection modes).
- `scripts/annotate.py` — red-box annotation + crop + preview stacker.
- `scripts/doc_ids.py` — next free rId/image number; `--add` wires images into an
  unpacked docx and prints suggested extents.
