# Test report: Serve sitemap.xml, robots.txt and favicon.ico on the live site — PASS

## Environment
- Branch `fix/live-sitemap-robots`, HEAD `74d59d2` (code commit `641b4bd`). No code edited.
  The owner's uncommitted `data/products/05-*.json` and `08-*.json` edits were left untouched
  (read only, as every local run seeds its throwaway database from `data/`).
- Windows, project venv. Every run used a throwaway SQLite database (`AR_DATABASE_PATH` in a
  temp folder), a random 64-char `SECRET_KEY` and a test admin login (`tester` / random password).
- Tools (temp scripts in the session scratchpad, outside the repo):
  - `t_ac.py`: Flask test client, AC1-AC5, AC7, AC9, AC12 and edge cases.
  - `t_ac6.py`: a real admin session through the test client (login form + CSRF token, edit
    form POSTs), plus a direct row insert into the throwaway DB.
  - `t_serve.py`: starts this branch's `serve.py` (:8771), the **pre-change** `serve.py` from
    `git archive 325b38c` (:8772) and an empty `python -m http.server` (:8773). It makes raw
    HTTP requests and runs `check_site.py --live --live-url` against each one.
  - `t_one404.py`: this branch's app under waitress, with exactly one of the three files forced to 404.
  - Reference "old GitHub Pages" output: `git archive 325b38c` was extracted to the scratchpad
    with the current `data/` copied in, then its `tools/build_static.py` was run, so its
    `_site/sitemap.xml` is the pre-change sitemap for the same content.
- The developer's helper `drive.py` was read. It does the same as `t_serve.py` (which adds the
  pre-change server), so `t_serve.py` was used instead.

## Regression
`.venv/Scripts/python tools/check_site.py` → **ALL CHECKS PASSED**. It reports: 153 pages
render, 404 for unknown pages, 7 share pages, all 9 sitemap/robots/favicon checks, all 8 admin
checks, and the static build ("Built 153 pages + 404 … All internal links and sitemap OK").
The built robots.txt matches the app, and the built sitemap.xml lists the same 152 pages as the app.

## Acceptance criteria
- **AC1 — PASS.** With `serve.py` on :8771, `GET /sitemap.xml` returned 200,
  `Content-Type: application/xml; charset=utf-8` and 16184 bytes. The body starts with
  `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">`.
  The test client parsed it with ElementTree: the root is `{http://www.sitemaps.org/schemas/sitemap/0.9}urlset`, with 152 `<url>`.
- **AC2 — PASS.** The loc paths equal `set(page_paths()) - NOT_IN_SITEMAP`, with 0 duplicates.
  As an independent check, the list is **identical in order** to the sitemap from the
  pre-change build for the same `data/` (152 = 152, empty symmetric difference).
- **AC3 — PASS.** No `<loc>` contains `/admin`, `/go/` or `/enquiry/thank-you/`.
- **AC4 — PASS.** All 152 locs start with `https://arcooling.in/` and end with `/`. A
  test-client GET of each path returned 200. Over HTTP, `check_site --live --live-url http://127.0.0.1:8771`
  also printed "all 152 live sitemap pages open".
- **AC5 — PASS.** Every `<lastmod>` matches `^\d{4}-\d{2}-\d{2}$` and equals today (`2026-11-16`), per Q2.
- **AC6 — PASS** (method per the Coordinator decision). All steps ran in one process with no restart:
  - (a) An admin edit changed the slug of `02-cassette-ac-units` to `cassette-ac-renamed`.
    `/products/cassette-ac-renamed/` appeared in the sitemap and returns 200. The old
    `/products/cassette-ac-units/` dropped out (that page now returns 404). Renaming it back
    restored the original list exactly.
  - (b) An admin edit added a part `tester-capacitor` (slug + specs) to `04-capacitors`.
    `/parts/capacitors/tester-capacitor/` appeared and returns 200. Removing the part
    restored the original list.
  - (c) An admin edit added model `ZZTEST99` to `01-copeland`.
    `/parts/compressors/copeland-zztest99/` appeared and returns 200. Removing it restored the list.
  - (d) A new product row (`99-tester`, slug `tester-new-product`) was inserted directly into
    the throwaway DB. `/products/tester-new-product/` appeared and returns 200. Deleting the
    row restored the list.
- **AC7 — PASS.** `GET /robots.txt` returned 200 with `text/plain; charset=utf-8`. The body is exactly
  `b'User-agent: *\nAllow: /\nDisallow: /admin\n\nSitemap: https://arcooling.in/sitemap.xml\n'`
  (83 bytes, LF line endings, final newline), the same over HTTP from `serve.py`. Python's
  `urllib.robotparser` on this text allows `/`, `/products/` and `/go/x/`, and blocks `/admin`,
  `/admin/login` and `/admin/products/x/edit`.
- **AC8 — PASS.** With `AR_SITE_URL=https://example.test`, robots.txt says
  `Sitemap: https://example.test/sitemap.xml`. All 152 locs start with `https://example.test/`,
  and the text `arcooling` does not appear in the sitemap.
  `AR_SITE_URL=https://example.test tools/check_site.py --skip-build` → ALL CHECKS PASSED.
  I did not repeat the build with this address, because it would overwrite `_site/`. The
  developer reports that the build run passed.
- **AC9 — PASS.** The build passed in the regression run, including the new `check_sitemap()`.
  The bytes of `_site/robots.txt` equal the Flask response. The `_site/sitemap.xml` loc list
  equals the Flask list, in the same order (152). The bytes of `_site/favicon.ico` equal
  `static/favicon.ico`.
- **AC10 — PASS.** `check_site.py` passes (see Regression).
  - **Positive:** `--live --live-url` against this branch's `serve.py` → exit 0. All 6 live
    checks pass (17 pages/files, robots text, valid sitemap with 152 pages, addresses, all 152
    pages open, favicon).
  - **Negative, pre-change `serve.py` (325b38c):** exit 1, 4 FAILs. The first is
    `17 live pages and files (/sitemap.xml -> 404; /robots.txt -> 404; /favicon.ico -> 404)`,
    followed by the robots, sitemap and favicon checks.
  - **Negative, exactly one file 404** (`t_one404.py`): each case exited 1.
    - Only `/sitemap.xml` missing: 2 FAILs (the pages/files line and "valid sitemap (0 pages)").
    - Only `/robots.txt` missing: 2 FAILs.
    - Only `/favicon.ico` missing: 2 FAILs.
  - **Negative, empty `http.server`:** exit 1, 4 FAILs.
- **AC11 — DEFERRED to deployer verify.** Read-only check of the live site today: `/sitemap.xml`,
  `/robots.txt` and `/favicon.ico` all return 404, as expected before the merge. The
  `--live` run without `--live-url` also checks the www redirect.
- **AC12 — PASS** (local part; the live part is deferred with AC11). Test client and `serve.py`:
  200, `image/vnd.microsoft.icon`, `Cache-Control: public, max-age=86400`, 7077 bytes,
  byte-identical to `static/favicon.ico`.

## Edge cases
All edge cases ran against this branch on the throwaway DB.

**Trailing slash and other variants of the file addresses**
- These return 404: `/sitemap.xml/`, `/robots.txt/`, `/favicon.ico/` (normal HTML 404 page),
  `/sitemap`, `/robots`, `/SITEMAP.XML`, `/sitemap.xml.gz`, `/static/sitemap.xml`.
- `/sitemap.xml?x=1` → 200.

**HEAD and POST requests**
- HEAD on each file (test client and waitress): 200, same Content-Type and Content-Length as
  GET (16184 / 83 / 7077), empty body.
- POST on each file → 405.

**XML escaping**
Each value below was set as a product slug through admin. In every case the sitemap returned
200, ElementTree parsed it, and the loc's page returned 200.
- `a&b` → raw `<loc>https://arcooling.in/products/a&amp;b/</loc>` (escaped correctly).
- `x<y>z` → `x%3Cy%3Ez` (encoded by `url_for`).
- `café ac` → `caf%C3%A9%20ac`.
- `q"'` → `q%22'`.
- A 300-character slug was listed and opens.

**Duplicates and missing data**
- Duplicate slug: two products set to the same slug are listed once (151 locs, no duplicates).
- Product with no `slug` key: `/sitemap.xml` → 500, but `/` and `/products/` are also 500,
  through `get_nav_menus` (KeyError `'slug'`). This existed before the change, the design
  expects the sitemap to fail loudly in this case, and it is not caused by this change. See note N2.

**Other paths and admin**
- Unknown URL `/does-not-exist/` → 404. Unknown share page `/go/nope/` → 404.
- `/admin` without login → 302 to `/admin/login`.
- Admin save without a CSRF token is refused (regression check "save without token refused").
- No public page path starts with `/admin` (AC3/AC4 lists).

**Line endings and leftovers**
- The old Windows build wrote robots.txt with CRLF (I saw `^M` in the pre-change `_site/robots.txt`).
  The new one is always LF, because it uses the route bytes and `write_bytes`. This is an improvement.
- No test servers were left listening afterwards. `git status` shows only the owner's 2 data edits.

## Defects
None that are must-fix or should-fix.

Notes (minor, no action required for this fix):
- **N1 (minor, informational):** `Disallow: /admin` is a prefix rule. It would also block any
  future public page whose address starts with `/admin` (for example `/administration/`). No
  such page exists today, and this matches the owner's Q1 decision and the design.
- **N2 (existing before this change, not in scope):** if a product record loses its `slug` in
  admin, the whole site (home, products and sitemap) returns 500. A candidate for a later
  admin-validation fix.
