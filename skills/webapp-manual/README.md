# webapp-manual

Build a **web system's operation manual** (操作說明書 / 操作手冊 / user guide) as a `.docx` from scratch, or maintain an existing one — kept **true to the running app**.

Operation manuals rot: the app ships a new dropdown, a chapter gets reordered, a preview screen goes live — and the `.docx` quietly lies. This skill is the workflow that keeps every claim grounded in the live system or its source, every screenshot current, and every edit surgical.

## Two modes

- **Build from scratch** — no manual yet. Enumerate the app's navigation, turn it into a table of contents, then document each screen in order (function description → annotated screenshots → field-spec table). Starts from the clean skeleton in `assets/manual-template.docx`.
- **Maintain** — a manual exists but drifts. Remake a chapter, refresh stale screenshots, audit the TOC against the real system, fix an outdated dropdown list.

## What it does

Both modes rest on three lower-level capabilities, tied into one loop:

1. **Live verification** — sign in to the deployed app and read what each page actually renders (via the bundled Playwright script, or your agent's Playwright MCP — see Prerequisites). It **doesn't assume how the app authenticates** — it reads the source first (login form? router guard? token in `localStorage` / cookie?) and picks the sign-in method with you. The old manual is a *suspect*, not a source.
2. **Screenshot capture + annotation** — full-page Playwright captures with red highlight boxes drawn from real element coordinates, then cropped to the meaningful band.
3. **OOXML section editing** — add / remake / delete chapters, swap images, edit field-spec tables and the Table of Contents, following the manual's existing convention (or the template's, when building fresh).

The raw `.docx` unpack → edit XML → repack mechanics are handled by the **`document-skills:docx`** skill. This skill tells you *what* to put in the XML and *how to be sure it's correct*.

## The core loop

```
SCOPE → VERIFY → CAPTURE → ANNOTATE → EDIT → REPACK + VERIFY
```

You won't always run all six — "the TOC is missing two pages" stops at VERIFY plus a small EDIT; "remake this chapter" runs the whole loop; "build the manual from scratch" enumerates the nav into a TOC first, then runs the loop once per chapter, in nav order.

## When it triggers

Anytime a doc must match a live, authenticated single-page app — "build the operation manual from scratch", "list the menu as a TOC and document each page", "update the manual", "remake section X", "compare the TOC against the system", "the screenshots are stale", "document this new page".

## Prerequisites

- **Browser automation** for live verification + capture — either the bundled Playwright script (`npm i playwright && npx playwright install chromium`) or a **Playwright MCP** in your agent. One must be set up; it's the skill's only external requirement.
- **Python** with `defusedxml`, `lxml`, `Pillow` for the docx + annotation scripts.
- **No LibreOffice assumed** — structural verification only; the final visual eyeball-check of the rendered `.docx` is yours.

See [`SKILL.md`](SKILL.md) for the full runtime workflow, `references/` for the deep technique notes (live verification, building from scratch, OOXML editing, a worked example), and `assets/manual-template.docx` for the from-scratch skeleton.

## Installation

```bash
npx skills add Ivantseng123/skills --skill webapp-manual -g
```

## License

MIT
