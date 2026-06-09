# Worked example (de-identified)

A real run of this workflow, with the credential, host, and client name stripped.
The system here is an internal admin SPA (Gridsome + Vuetify) reached at
`https://app.example.com`; the operation manual is
`op_manual_vX.Y.Z.docx`, versioned by bumping the suffix each pass.

It shows two of the arcs from the core loop: a TOC audit (VERIFY + small EDIT)
and a chapter remake (the full loop).

---

## Arc A — "compare the TOC against the system; what pages are missing?"

**Scope.** Only chapters 5–9. State that up front.

**Verify.** The left menu and routes are static frontend data, so the source is
the ground truth — read the navigator component's menu table and list every
route under chapters 5–9. Then deep-link each (JWT injected, no router guard) to
confirm it renders. Cross-reference against the manual's TOC entries.

Result: chapter 9 ("單據報表 / Reports") had **two report pages with no TOC
entry** — they exist in the app but the manual never documented them.

**Edit (small).** Added two sub-sections under chapter 9 following the existing
convention (操作路徑 → 功能說明 → filter + list screenshots → notes), wired the
two new screenshots in with `doc_ids.py --add`, added two TOC lines with
placeholder page numbers, and set `<w:updateFields w:val="true"/>` so Word
recalculates on open. Chapters 5–8 matched the system — no change.

---

## Arc B — "remake chapter 5 (Same-Risk Management); follow the original style"

**Scope.** Chapter 5 only. Chapter 6 turned out to share an identical (stale)
dropdown list — flagged to the user, left untouched.

**Premise check first.** Before remaking, verify the chapter's premise. Chapter
5's feature was still **mock/preview** on the live system: the source's
`getTypeList()` returned literal `['default1','default2','default3']`, the live
list showed placeholder rows (`Q / AAA / default1`), and the add form had an
empty chart. The original manual already carried a "畫面僅供參考，待後續開發 /
screens for reference only, pending development" caveat. So the remake **keeps the
caveat** and the current mock screenshots are honest evidence — surfaced this to
the user rather than dressing it up as shipped.

**Verify the facts that were wrong.** The manual documented the 險群 (risk-group)
dropdown with **12 options**; the live `selectMenu.js` `productGroupList` now
exports **9** (three were commented out, one renamed). Confirmed the conditional
"distance" field shows for two groups, not one: `isProductGroupFiOrEg(x)` returns
`x === 'F' || x === 'E'`. These outdated facts were the highest-value fixes in
the whole remake.

**Capture.** With `capture_pages.js` and the config below: the list page (filter
expanded, add button visible), the add/edit dialog, and the add form — drawer
opened so the nav menu shows the active item.

**Annotate.** With `annotate.py`: red box around the filter panel and the ＋新增
button on each list shot. The original padded the section with three
near-identical list screenshots differing only in which button was boxed — that
was consolidated to one annotated shot per distinct UI state (list, dialog, add
form). Kept the section's writing structure; dropped the redundant frames; said
so to the user.

**Edit.** `doc_ids.py --add` wired four screenshots into `word/media` (printing
each rId + `<wp:extent>`). Then, in one asserted Python pass: deleted the surplus
image paragraphs by `w14:paraId` (deletions first), swapped `r:embed` on the kept
images, updated extents, fixed the 12→9 dropdown list with
`replace(OLD, NEW, 1)` (asserting the count was 2 before and 1 after, so chapter
6 stayed put), and updated the distance-field note to name both groups.

**Repack + verify.** `pack.py … --original <prev>` validated; it reported
`Paragraphs: 1324 → 1318 (-6)` — exactly the six paragraphs intended for
deletion. Structural grep confirmed the new rIds resolved, the old ones were
gone, and chapter 6's list still occurred once. Handed the visual layout check
to the user.

---

## Sample `capture_pages.js` config

The token comes from `$JWT` at runtime — it is never written here.

> **Get the `auth` block right or every screenshot is the login page.** This SPA
> validates the injected session on load and, if it is incomplete, *clears the
> auth keys and redirects to `/login`* — capture then silently records the login
> screen and every boundingBox comes back null. The fix is to **mirror exactly
> what a real manual login writes to `localStorage`**: open DevTools →
> Application → Local Storage after logging in by hand and copy *every* key.
> The ones that bite: a complete `loginData` (including `content.exp`, a
> future unix-seconds expiry) and **all** the environment-suffixed
> `authoritiesTimeKey_<env>` markers — a single missing expiry marker triggers an
> auto-logout. The suffixes are app/deployment-specific (e.g. `_test`, `_uat`,
> `_prod`, or one per tenant); replace the placeholders below with the exact keys
> your manual login wrote.

```json
{
  "baseUrl": "https://app.example.com",
  "viewport": { "width": 1400, "height": 820 },
  "deviceScaleFactor": 2,
  "auth": {
    "Authorization": "JWT ${JWT}",
    "loginData": "{\"accessToken\":\"${JWT}\",\"content\":{\"sub\":\"admin\",\"exp\":1781491782},\"principal\":{\"username\":\"admin\"}}",
    "authoritiesTimeKey": "9999999999999",
    "authoritiesTimeKey_<env>": "9999999999999",
    "authoritiesTimeKey_<tenant>": "9999999999999"
  },
  "drawerToggle": ".v-app-bar__nav-icon",
  "drawerProbe": ".v-list-item__title",
  "pages": [
    {
      "name": "info_list",
      "route": "/same-risk/info/list",
      "navExpand": "同險管理",
      "clicks": ["text=篩選"],
      "boxes": {
        "filter": ".v-expansion-panel",
        "add": "button:has-text(\"新增\")"
      },
      "annotate": { "highlight": ["filter", "add"], "crop": [0, 0, null, 1040] }
    },
    {
      "name": "info_dialog",
      "route": "/same-risk/info/list",
      "navExpand": "同險管理",
      "clicks": ["button:has-text(\"新增\")"],
      "boxes": { "dialog": ".v-dialog--active" },
      "annotate": { "highlight": ["dialog"], "crop": [0, 0, null, 1100] }
    },
    {
      "name": "mgmt_add",
      "route": "/same-risk/management/add",
      "boxes": {},
      "annotate": { "highlight": [], "crop": [0, 0, null, 820] }
    }
  ]
}
```

Run:

```bash
JWT="$THE_TOKEN" node scripts/capture_pages.js config.json out/
python scripts/annotate.py config.json out/ out/final/ --preview out/_preview.png
# eyeball out/_preview.png, then:
python scripts/doc_ids.py /tmp/unpacked --add out/final/info_list.png out/final/info_dialog.png out/final/mgmt_add.png
```
