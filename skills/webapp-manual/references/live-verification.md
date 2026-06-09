# Live verification of an authenticated SPA (no Playwright MCP)

How to log into a deployed single-page app and confirm what it actually renders,
when there is no Playwright MCP server available. Everything here was learned
against a Gridsome + Vuetify SPA, but the techniques generalise to most
token-in-`localStorage` SPAs.

## 1. Find the ground truth in source *before* you click

The fastest, most reliable answers come from the frontend source, not the live
DOM. For documenting a manual you typically need three things, and each has a
canonical home:

| You need | Look in | Example |
|----------|---------|---------|
| The menu structure + routes | the navigator component | `theNavigator.vue` — a `menu`/`menuState` data table mapping label → path |
| A dropdown's real options | a shared options module | `selectMenu.js` exporting `productGroupList = [{text, value}, …]` (watch for commented-out items — those were removed) |
| When a conditional field shows | the page component's template `v-if` + its method | `v-if="isProductGroupFiOrEg(x)"` → `return x === 'F' || x === 'E'` |

A `grep -rn "同險設定\|route\|productGroupList" src/` settles "what are the real
values" definitively and immune to mock/preview rendering. **Match the runtime
version** the deployment is on (check the footer/version string against the
checked-out branch) — `main` may have drifted.

`zsh` glob trap: `grep -r --include=*.vue pattern src/` fails on zsh because the
unquoted glob expands. Quote it (`--include='*.vue'`) or just `grep -rn pattern src/`.

## 2. Inject a JWT into localStorage to authenticate

Many internal SPAs keep the auth token in `localStorage` and attach it via an
HTTP interceptor; crucially, several have **no router guard** (the auth check in
`main.js` is commented out), so a 401/403 only pops an error toast — it does not
redirect. That means: set the right `localStorage` keys before any page script
runs, then deep-link straight to any route and it renders.

Use `context.addInitScript` (runs before page scripts) to set the keys the app's
`authUtils`-style module reads. The common shape:

```js
await ctx.addInitScript((kv) => {
  for (const [k, v] of Object.entries(kv)) localStorage.setItem(k, v);
}, {
  Authorization: 'JWT ' + token,                 // the interceptor reads this
  loginData: JSON.stringify({ accessToken: token, content: { sub: 'admin', exp: <future> }, principal: { username: 'admin' } }),
  authoritiesTimeKey: '9999999999999',           // push any "authorities cache" expiry far out
});
```

`scripts/capture_pages.js` does exactly this, driven by the config's `auth`
block, with `${JWT}` interpolated from the environment so the token never lands
in a file.

**An incomplete session is worse than none — it logs you out.** Several SPAs
validate the injected session on first load and, if it's missing a piece,
**delete the auth keys from `localStorage` and redirect to `/login`**. Capture
then cheerfully screenshots the login page and every recorded boundingBox comes
back `null` — a silent failure that looks like "the selectors are wrong" when the
real problem is auth. Confirm by dumping `localStorage` keys + `location.href`
after navigation: if `Authorization`/`loginData` vanished and the URL is
`/login`, the session was rejected. The fix is to **mirror exactly what a real
manual login writes** — log in by hand, open DevTools → Application → Local
Storage, and copy *every* key. The two that bite:
- `loginData` must be complete, including `content.exp` (a future unix-seconds
  expiry). A bare `{accessToken, principal}` gets rejected.
- **All** the environment-suffixed `authoritiesTimeKey_<env>` markers, not just
  the base one. A single missing expiry marker triggers the auto-logout.

**Keep the token in an env var.** It is a live credential. Do not write it into
the config, a script, or anything that could be committed.

### Better: real form login (when you have credentials)

JWT injection is reverse-engineering the app's session. If you have an account,
**logging in through the form is more robust** — the app writes the *complete,
correct* session to `localStorage` itself, so the incomplete-session logout trap
above simply can't happen. `capture_pages.js` supports a `login` block (route +
username/password + selectors) that fills the form and submits before capturing;
prefer it over `auth` when credentials are available.

Two traps learned the hard way:
- **Don't name credential env vars after system vars.** `${USERNAME}` collided
  with the shell's own `USERNAME` (set to the OS login name), so the script
  logged in as the OS user instead of the intended account, failed, and
  screenshotted the login page. Use app-specific names like `${APP_USER}` /
  `${APP_PASS}`.
- **Confirm the post-login URL.** The script logs `logged in as <user> -> <url>`.
  If that URL still ends in `/login`, the login failed (wrong creds, wrong
  selector, wrong env var) and every capture will be the login screen. Check it
  before trusting the screenshots — a failed login fails *silently* otherwise.

## 3. Drive pages reliably

- **Wait properly.** `goto(url, { waitUntil: 'networkidle', timeout: 60000 })`
  then an extra `waitForTimeout(3000)` for the SPA to settle. SPAs finish
  rendering after `networkidle`.
- **Always pass a timeout to `click()`.** A `click()` on a selector that is
  missing or not actionable blocks for the *full default 30 s* before failing.
  `click({ timeout: 5000 }).catch(()=>{})` fails fast and keeps going. This one
  bit hard — a handful of dead clicks turned a 5 s capture into minutes.
- **The nav drawer is often off-canvas.** A Vuetify `v-navigation-drawer`
  bound to `v-model="drawer"` can default closed on a desktop viewport; its
  elements then report a **negative `x`**. Detect that (probe a known nav item's
  `boundingBox().x < 0`) and click the `v-app-bar__nav-icon` hamburger to open
  it before screenshotting. `capture_pages.js` does this via `drawerToggle` +
  `drawerProbe`.
- **Lazy-rendered nav children aren't in the DOM.** A collapsed
  `v-list-group` doesn't render its children, so you can't select them. Either
  click the group header open (`navExpand` in the config) or, when you just need
  the data and not a screenshot, read the Vue component state directly:

  ```js
  await page.evaluate(() => {
    const root = document.querySelector('#app').__vue__.$root;  // walk down for menu/singleMenu data
    // ...find the component holding the menu array and return it
  });
  ```

  Reading `__vue__` data sidesteps the whole lazy-DOM problem and is the most
  robust way to enumerate a static frontend menu.

## 4. Detecting mock / preview screens

A feature can be "live" (the route renders) but still **mock/preview**: dropdowns
hardcode `default1 / default2`, list rows show placeholder values (`AAA`,
`ADDRESS`), charts are empty axes. Confirm by cross-checking the source — a
`getTypeList()` that `return`s literal `['default1','default2']` instead of
calling an API is the tell. When a screen is mock, **document it honestly**: keep
the "for reference only / 僅供參考" caveat, and note that a current screenshot's
placeholder data *is* the evidence it's unfinished. Don't dress a mock up as
shipped.

## 5. What you can't do here

Reading a screenshot image wider than ~2000px directly isn't supported — use PIL
to downscale or stack a preview (`annotate.py --preview`). And without
LibreOffice you can't render the final `.docx` for a visual layout check; you
verify the document structurally and hand the eyeball check to the user.
