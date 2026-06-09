#!/usr/bin/env node
/*
 * capture_pages.js — config-driven Playwright capture for an authenticated SPA,
 * for documenting an operation manual.
 *
 * Why this exists: the boilerplate (launch, inject a JWT into localStorage so a
 * router-guard-less SPA renders, open a nav drawer that defaults off-canvas,
 * wait for the network, screenshot, and record element coordinates for later
 * red-box annotation) is the same every time and is full of small traps
 * (clicks without a timeout hang for 30s; a collapsed drawer reports negative x;
 * lazy nav children aren't in the DOM). Encapsulate it once; supply the
 * app-specific bits as data.
 *
 * Usage:
 *   JWT="<the token>" node capture_pages.js config.json out_dir/
 *
 * Secrets: the token is read from an env var and interpolated into config via
 * ${JWT} (or any ${ENV_VAR}). Never commit a real token into the config file.
 *
 * Output:
 *   out_dir/<page.name>.png        full-page screenshot (deviceScaleFactor applied)
 *   out_dir/meta.json              { deviceScaleFactor, pages: { name: { boxes:{sel:bbox}, options:{} } } }
 *
 * Config schema (see references/example-walkthrough.md for a filled-in sample):
 * {
 *   "baseUrl": "https://your-app.example.com",
 *   "viewport": { "width": 1400, "height": 820 },     // optional, defaults shown
 *   "deviceScaleFactor": 2,                            // optional, default 2
 *   "auth": {        // localStorage keys set before any page script runs.
 *                    // INCOMPLETE auth = the app clears these keys and redirects
 *                    // to /login, so capture silently records the login page and
 *                    // every box comes back null. Mirror EXACTLY what a real
 *                    // manual login writes (DevTools > Application > Local Storage):
 *                    // a full loginData with content.exp, AND every
 *                    // authoritiesTimeKey_<env> expiry marker the app uses.
 *     "Authorization": "JWT ${JWT}",
 *     "loginData": "{\"accessToken\":\"${JWT}\",\"content\":{\"sub\":\"admin\",\"exp\":1781491782},\"principal\":{\"username\":\"admin\"}}",
 *     "authoritiesTimeKey": "9999999999999",
 *     "authoritiesTimeKey_<env>": "9999999999999"
 *   },
 *   "login": {        // PREFERRED when you have credentials: real form login.
 *                     // The app sets the full session itself — no injection guesswork.
 *                     // Omit "auth" when using this. Creds interpolate from env.
 *     "route": "/login",                               // optional, default "/login"
 *     "username": "${USERNAME}", "password": "${PASSWORD}",
 *     "usernameSelector": "input:not([type=password])",  // optional defaults shown
 *     "passwordSelector": "input[type=password]",
 *     "submitSelector": "button:has-text(\"Login\")"
 *   },
 *   "drawerToggle": ".v-app-bar__nav-icon",            // optional: clicked to open an off-canvas nav drawer
 *   "drawerProbe": ".v-list-item__title",              // optional: an element whose x<0 means the drawer is closed
 *   "pages": [
 *     {
 *       "name": "info_list",
 *       "route": "/same-risk/info/list",
 *       "waitMs": 3000,                                // optional extra settle time after networkidle
 *       "navExpand": "同險管理",                        // optional: text of a collapsed nav group to click open
 *       "clicks": ["text=篩選", "button:has-text(\"新增\")"],  // optional pre-actions, each clicked in order
 *       "clickWaitMs": 900,                              // optional: wait after EACH click (default 900)
 *       "afterClickWaitMs": 4000,                        // optional: extra wait after a NAVIGATING click,
 *                                                        // on top of the automatic networkidle settle —
 *                                                        // use when a click opens a detail route that loads data
 *       "boxes": {                                     // selectors whose boundingBox to record (for annotation)
 *         "filter": ".v-expansion-panel",
 *         "add": "button:has-text(\"新增\")",
 *         "dialog": ".v-dialog--active"
 *       },
 *       "options": { "riskGroup": ".v-menu__content .v-list-item" }  // optional: text[] of a dropdown to dump
 *     }
 *   ]
 * }
 */
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

function interpolate(v) {
  if (typeof v !== 'string') return v;
  return v.replace(/\$\{([A-Z_][A-Z0-9_]*)\}/g, (_, k) => {
    if (process.env[k] === undefined) {
      console.error(`WARN: env var ${k} is unset; leaving \${${k}} empty`);
      return '';
    }
    return process.env[k];
  });
}

async function bbox(page, selector) {
  try { return await page.locator(selector).first().boundingBox(); }
  catch (e) { return null; }
}

(async () => {
  const cfgPath = process.argv[2];
  const outDir = process.argv[3] || 'out';
  if (!cfgPath) { console.error('usage: JWT=<tok> node capture_pages.js config.json out_dir/'); process.exit(2); }
  const cfg = JSON.parse(fs.readFileSync(cfgPath, 'utf-8'));
  fs.mkdirSync(outDir, { recursive: true });

  const DSF = cfg.deviceScaleFactor || 2;
  const viewport = cfg.viewport || { width: 1400, height: 820 };
  const auth = {};
  for (const [k, val] of Object.entries(cfg.auth || {})) auth[k] = interpolate(val);

  const browser = await chromium.launch({ headless: true });
  const ctx = await browser.newContext({ viewport, deviceScaleFactor: DSF });
  // Auth option 1 — inject a session into localStorage before any page script runs.
  // Brittle: an incomplete session gets cleared and you land on /login (see refs).
  // Skipped when a login block is present — the two are mutually exclusive, and
  // injecting a partial session alongside a real login only triggers auto-logout.
  if (Object.keys(auth).length && cfg.login) {
    console.error('WARN: both "auth" and "login" set; ignoring "auth" and using form login.');
  }
  if (Object.keys(auth).length && !cfg.login) {
    await ctx.addInitScript((kv) => {
      try { for (const [k, v] of Object.entries(kv)) localStorage.setItem(k, v); } catch (e) {}
    }, auth);
  }
  const page = await ctx.newPage();
  await page.goto(cfg.baseUrl + '/', { waitUntil: 'domcontentloaded' }).catch(() => {});
  await page.waitForTimeout(1500);

  // Auth option 2 — real form login (preferred when credentials are available).
  // The app itself writes the COMPLETE session to localStorage, so you never have
  // to reverse-engineer which keys it needs (no incomplete-session logout trap).
  // Credentials interpolate from env, e.g. "username": "${USERNAME}".
  if (cfg.login) {
    const lg = cfg.login;
    const user = interpolate(lg.username);
    const pass = interpolate(lg.password);
    // Fail loudly on empty creds — otherwise an unset/typo'd env var submits a
    // blank login, fails, and you silently capture the login page for every page.
    if (!user || !pass) {
      console.error(`FATAL: login credential is empty (user=${user ? 'set' : 'EMPTY'}, pass=${pass ? 'set' : 'EMPTY'}). ` +
        `Export the env vars referenced by login.username/password — and don't name them $USERNAME (it collides with the OS login var).`);
      await browser.close();
      process.exit(3);
    }
    await page.goto(cfg.baseUrl + (lg.route || '/login'), { waitUntil: 'networkidle', timeout: 60000 }).catch(() => {});
    await page.waitForTimeout(1500);
    await page.locator(lg.usernameSelector || 'input:not([type="password"])').first()
      .fill(user, { timeout: 8000 }).catch((e) => console.error('username fill failed:', e.message));
    await page.locator(lg.passwordSelector || 'input[type="password"]').first()
      .fill(pass, { timeout: 8000 }).catch((e) => console.error('password fill failed:', e.message));
    await page.locator(lg.submitSelector || 'button:has-text("Login")').first()
      .click({ timeout: 8000 }).catch((e) => console.error('login click failed:', e.message));
    await page.waitForTimeout(3500); // let the app process login, set localStorage, redirect
    const landed = page.url();
    console.error('logged in as', user, '->', landed);
    // Hard-fail if login didn't take — a silent failure means every screenshot is
    // the login screen with null boxes, which looks like a selector bug, not auth.
    const loginRe = new RegExp(lg.failUrlPattern || '/login(\\b|/|$|\\?)');
    if (loginRe.test(landed)) {
      console.error(`FATAL: still on the login page after submit (${landed}). Login failed — ` +
        `check credentials, the submit selector, and env var names. Aborting before capturing the login screen.`);
      await browser.close();
      process.exit(4);
    }
  }

  async function openDrawer() {
    if (!cfg.drawerToggle || !cfg.drawerProbe) return;
    let b = await bbox(page, cfg.drawerProbe);
    let tries = 0;
    while ((!b || b.x < 0) && tries < 3) {
      const ic = page.locator(cfg.drawerToggle).first();
      if (await ic.count()) await ic.click({ timeout: 5000 }).catch(() => {});
      await page.waitForTimeout(900);
      b = await bbox(page, cfg.drawerProbe);
      tries++;
    }
  }

  const meta = { deviceScaleFactor: DSF, viewport, pages: {} };

  for (const p of cfg.pages) {
    await page.goto(cfg.baseUrl + p.route, { waitUntil: 'networkidle', timeout: 60000 }).catch(() => {});
    await page.waitForTimeout(p.waitMs || 3000);
    await openDrawer();
    // expand a collapsed nav group if asked
    if (p.navExpand) {
      const child = page.locator('.v-list-item__title', { hasText: p.navExpand }).first();
      if (!(await child.isVisible().catch(() => false))) {
        const grp = page.locator('.v-list-group__header, .v-list-item', { hasText: p.navExpand }).first();
        if (await grp.count()) { await grp.click({ timeout: 5000 }).catch(() => {}); await page.waitForTimeout(800); }
      }
    }
    // pre-action clicks (expand filter, open dialog, …). ALWAYS pass a timeout —
    // a click on a missing/disabled target otherwise blocks for the full 30s.
    for (const sel of (p.clicks || [])) {
      const loc = page.locator(sel).first();
      if (await loc.count()) await loc.click({ timeout: 5000 }).catch(() => {});
      await page.waitForTimeout(p.clickWaitMs || 900);
    }
    // A click can NAVIGATE (open a detail route / push a new page), not just open
    // a dialog. The per-click wait above is enough to expand a panel but not to
    // load a fresh route, so the screenshot would catch a half-loaded page. When
    // any clicks ran, let the destination settle — wait for networkidle, then an
    // optional extra beat for SPA data to land.
    if ((p.clicks || []).length) {
      await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});
      if (p.afterClickWaitMs) await page.waitForTimeout(p.afterClickWaitMs);
    }
    // record boundingBoxes for annotation
    const boxes = {};
    for (const [name, sel] of Object.entries(p.boxes || {})) boxes[name] = await bbox(page, sel);
    // optionally dump a dropdown's option texts (useful to confirm option lists)
    const options = {};
    for (const [name, sel] of Object.entries(p.options || {})) {
      options[name] = await page.evaluate((s) =>
        [...document.querySelectorAll(s)].map((e) => e.textContent.trim()).filter(Boolean), sel);
    }
    await page.screenshot({ path: path.join(outDir, p.name + '.png'), fullPage: false });
    meta.pages[p.name] = { route: p.route, boxes, options };
    console.error(`captured ${p.name} (${p.route})`);
  }

  fs.writeFileSync(path.join(outDir, 'meta.json'), JSON.stringify(meta, null, 2));
  console.log('OK — wrote ' + path.join(outDir, 'meta.json'));
  await browser.close();
})().catch((e) => { console.error('ERR', e); process.exit(1); });
