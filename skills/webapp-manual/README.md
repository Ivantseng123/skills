# webapp-manual

Build and maintain a **web system's operation manual** (操作說明書 / 操作手冊 / user guide) as a `.docx`, and keep it **true to the running app**.

Operation manuals rot: the app ships a new dropdown, a chapter gets reordered, a preview screen goes live — and the `.docx` quietly lies. This skill is the workflow that keeps every claim grounded in the live system or its source, every screenshot current, and every edit surgical.

## What it does

It sits on top of three lower-level capabilities and ties them into one loop:

1. **Live verification** — log into an authenticated SPA *without* a Playwright MCP server (inject a JWT into `localStorage`), navigate any page, and read what it actually renders. The old manual is a *suspect*, not a source.
2. **Screenshot capture + annotation** — full-page Playwright captures with red highlight boxes drawn from real element coordinates, then cropped to the meaningful band.
3. **OOXML section editing** — add / remake / delete chapters, swap images, edit field-spec tables and the Table of Contents, following the manual's *existing* writing convention.

The raw `.docx` unpack → edit XML → repack mechanics are handled by the **`document-skills:docx`** skill. This skill tells you *what* to put in the XML and *how to be sure it's correct*.

## The core loop

```
SCOPE → VERIFY → CAPTURE → ANNOTATE → EDIT → REPACK + VERIFY
```

You won't always run all six — "the TOC is missing two pages" stops at VERIFY plus a small EDIT; "remake this chapter with current screenshots" runs the whole loop.

## When it triggers

Anytime a doc must match a live, authenticated single-page app — "update the manual", "remake section X", "compare the TOC against the system", "the screenshots are stale", "document this new page".

## Prerequisites

- **Playwright** (`npm i playwright && npx playwright install chromium`) for capture.
- **Python** with `defusedxml`, `lxml`, `Pillow` for the docx + annotation scripts.
- **No LibreOffice assumed** — structural verification only; the final visual eyeball-check of the rendered `.docx` is yours.

See [`SKILL.md`](SKILL.md) for the full runtime workflow, and `references/` for the deep technique notes (live verification, OOXML editing, a worked example).

## Installation

```bash
npx skills add Ivantseng123/skills --skill webapp-manual -g
```

## License

MIT
