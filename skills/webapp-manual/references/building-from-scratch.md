# Building an operation manual from scratch

When there's no manual yet. The maintenance flow assumes existing chapters to
mirror and a `document.xml` to find boundaries in — a greenfield build has
neither. This is the entry path that gets you to a first draft, then hands off to
the same CAPTURE → ANNOTATE → EDIT loop, run once per chapter.

## The shape of the work

1. Enumerate the nav → a table of contents (the outline).
2. Start from the skeleton template (`assets/manual-template.docx`).
3. Per chapter, in nav order: verify → capture → annotate → write the section.
4. Grow the TOC as you go; recalc on open.

Do it **incrementally — one chapter (or one nav group) at a time.** A real app is
dozens of screens; capturing everything and then writing everything is how you
lose the thread of what's grounded versus invented. Land one chapter end-to-end,
show the user, then continue.

## 1. The navigation *is* the table of contents

The left menu / route table is static frontend data — read it from source, not by
clicking around (`live-verification.md` §1 and §3 give the exact techniques: the
`theNavigator`-style component, or reading `__vue__` menu state for lazy menus).

Map the nav tree to the outline directly:

- a top-level menu group → a chapter (Heading 1)
- a sub-item / leaf route → a sub-section (Heading 2)
- nested groups → deeper headings

Write the outline out as plain text first and **agree it with the user before
writing any `.docx`** — ordering, which groups are in scope this pass, what to
skip (a "登出 / logout" item rarely needs a chapter). The outline is cheap to
change as text and expensive to change once it's headings plus a TOC field.

Cross-check the outline against the live app: every route should actually render
(deep-link each), and a route that 404s or is mock/preview gets flagged now —
not discovered mid-write.

## 2. Start from the skeleton, not a blank page

`assets/manual-template.docx` is a clean shell — heading styles, the 標楷體
`eastAsia` font runs, a working TOC field, and **one** example chapter in the
canonical section shape. It exists so you never hand-build OOXML styles and a TOC
field from nothing (fiddly and easy to get subtly wrong).

- Copy it to your working path and set the document title / cover line.
- The example chapter is your pattern: duplicate its paragraph structure per real
  chapter, then replace the placeholder text. Keep the `rPr` font runs intact
  (`eastAsia="標楷體"` + a Latin face) — matching them is what makes the output
  read as native rather than pasted-in.
- Grow the TOC field's cached lines from your outline (placeholder page numbers
  are fine) and set `<w:updateFields w:val="true"/>` so Word recomputes them on
  open — see `ooxml-editing.md` § "Headings and the Table of Contents".

## 3. Fill each chapter from the section shape

For each leaf screen, in nav order, run the loop and write the section in the
canonical shape (`ooxml-editing.md` § "The section writing convention"):

- **【操作路徑】** — the breadcrumb to the screen (［group］→［sub-page］), taken
  from the nav path you already enumerated.
- **【功能說明】** — numbered actions, buttons in ［］. Ground these in what the
  screen actually does: the buttons present, the dialogs they open. Capture and
  annotate the screen, then reference the shots here.
- **screenshots** — annotated, one per distinct UI state (list / dialog / form),
  not three near-identical frames.
- **欄位規格表** — one row per field: name + input rule. **Ground the rules in
  source**, not guesses: required/optional, max length, the dropdown's real
  option list (`selectMenu.js`-style), and any conditional-display logic
  (`v-if`). This table is where a from-scratch manual earns its keep — it's the
  part a human writer most often gets wrong or omits.
- **【注意事項】** — caveats. If the screen is mock/preview, say so here and keep a
  "僅供參考 / for reference only" note (see the skill's Golden rules).

## 4. Order, checkpoints, and what to defer

- **One chapter at a time, verified before moving on.** After each chapter: pack,
  structurally verify (`ooxml-editing.md` § "Structural verification"), and
  ideally let the user eyeball it before you build the next.
- **Front matter and the TOC settle last.** The cover page, revision history, and
  final TOC page numbers are easier once the chapters exist. Leave the TOC on
  update-on-open until the end.
- **Defer what isn't ready.** A nav item behind a feature flag, or a screen that's
  pure mock, can be a stub section that says so — don't invent content to fill it.

## What each step leans on

- `live-verification.md` — auth, driving pages, enumerating the menu from source.
- `scripts/capture_pages.js` + `scripts/annotate.py` — screenshots and annotation.
- `ooxml-editing.md` — headings/TOC, image drawing blocks, field-spec tables,
  structural verification.
- `assets/manual-template.docx` — the skeleton you copy and grow.
