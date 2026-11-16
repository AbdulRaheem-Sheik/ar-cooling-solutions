# Design: Serve sitemap.xml, robots.txt and favicon.ico on the live site

## Approach
Move the "which pages exist" list and the sitemap/robots text out of `tools/build_static.py`
into `app.py`, the same way `render_share_page` is shared, and add three small Flask routes:
`/sitemap.xml`, `/robots.txt`, `/favicon.ico`. The static build then stops generating these
files itself and instead **fetches them from the Flask app through its test client**, exactly as
it already does for every page. Live and static therefore run the same code path; the only way
they can differ is different content (live DB vs `data/`), which is what R2 wants.

The sitemap is built on every request from the database (`store.all_records` has no cache), so
admin edits show up immediately (AC6) without a restart. Cost is a handful of SQLite reads and
string joins, less than rendering a normal page (R9). No new packages.

## Alternatives considered
- **Keep `page_paths()` in build_static.py and import it from app.py** - the app would depend on
  a tool script (and its `sys.path` setup); wrong direction. Rejected.
- **Generate files at deploy time (cron / update.sh writes sitemap.xml, Caddy serves it)** -
  goes stale after admin edits (fails R2/AC6), needs Caddyfile + setup.sh changes. Rejected.
- **Cache the sitemap in memory** - unnecessary at this size and would break AC6. Rejected.
- **Jinja template for sitemap.xml** - adds a file for ~5 lines of string building; a plain
  function like `render_share_page` matches existing style. Rejected.
- **Build keeps its own writer but calls shared functions** - works, but fetching via the test
  client additionally proves the live routes return 200 and gives one code path. Chosen the latter.

## Changes by file

### `app.py`
1. `from datetime import date`, and add `Response`, `send_from_directory` to the flask import.
2. Move `NOT_IN_SITEMAP = {"/enquiry/thank-you/"}` here (comment: pages that render but should
   not be offered to search engines).
3. New `public_page_paths()` - body of today's `build_static.page_paths()` (same endpoints, same
   order), but **without** its own `test_request_context()`: it uses `url_for`, so callers must
   be in a request context (a live request already is; build/check wrap it). Return the list
   de-duplicated in order (`list(dict.fromkeys(paths))`) so two records with the same slug can
   never produce duplicate `<loc>`s (AC2). Docstring: "every public page; a new kind of page
   must be added here, which puts it in the static build, the site check and the sitemap at once" (R7).
4. New `sitemap_paths()` = `[p for p in public_page_paths() if p not in NOT_IN_SITEMAP]`.
5. New `render_sitemap()` -> str. Same output format as the current build (XML declaration,
   `urlset` in the 0.9 namespace, one `<url><loc>{SITE_URL}{path}</loc><lastmod>{today}</lastmod></url>`
   per line), `today = date.today().isoformat()` (Q2). Escape the loc with
   `html.escape(..., quote=False)` (`html` is already imported) so an `&` typed into a slug in
   admin cannot break the XML.
6. New `render_robots_txt()` -> str, exactly:
   ```
   User-agent: *
   Allow: /
   Disallow: /admin

   Sitemap: {SITE_URL}/sitemap.xml
   ```
   (Q1 = yes. Google uses the longest matching rule, so `/admin...` is disallowed and everything
   else allowed. No public URL starts with `/admin`.)
7. Routes (GET only, no login, no CSRF impact since they are GETs):
   ```python
   @app.get("/sitemap.xml")
   def sitemap():
       return Response(render_sitemap(), mimetype="application/xml")

   @app.get("/robots.txt")
   def robots_txt():
       return Response(render_robots_txt(), mimetype="text/plain")

   @app.get("/favicon.ico")
   def favicon():
       # Some browsers and tools ask for /favicon.ico without reading the page's <link> tags.
       return send_from_directory(STATIC_DIR, "favicon.ico",
                                  mimetype="image/vnd.microsoft.icon", max_age=86400)
   ```
   Flask adds `; charset=utf-8` to the two text types. The favicon mimetype is pinned so the
   result does not depend on the Windows registry vs Linux `mimetypes` table. Place the routes
   near `share_page` (end of the public routes).
8. Optional one-line fix while there: the `__main__` comment "The live site is the static build"
   is stale; say the live site is `serve.py` on the Oracle server. (Cosmetic; skip if preferred.)

### `tools/build_static.py`
1. `page_paths(site)` stays (check_site and AC2 use it) but becomes a thin wrapper:
   `with site.app.test_request_context(): return site.public_page_paths()`.
2. Remove `NOT_IN_SITEMAP` and the `date` import; the hand-written sitemap/robots writers and the
   `shutil.copy2(... favicon.ico ...)` line are replaced by fetching from the app:
   ```python
   for path, filename in (("/sitemap.xml", "sitemap.xml"), ("/robots.txt", "robots.txt"),
                          ("/favicon.ico", "favicon.ico")):
       response = client.get(path)
       if response.status_code != 200:
           sys.exit(f"{path} returned {response.status_code}; fix it before publishing.")
       (OUTPUT / filename).write_bytes(response.data)
   ```
   CNAME and `.nojekyll` stay as they are (GitHub Pages only).
3. New `check_sitemap()` called from `main()` after `check_links()`: parse `_site/sitemap.xml`
   with `xml.etree.ElementTree` (stdlib), and for each `<loc>` strip `site.SITE_URL` and require
   `output_file(path).is_file()`; exit with a list of missing pages otherwise. This extends the
   existing internal-link guarantee to the sitemap (R3/R4 for the static copy).
4. Docstring line 3-4: say sitemap.xml, robots.txt and favicon.ico come from the app's own routes.

Effect on the existing build logic:
- **Internal link checker**: only scans `*.html`; sitemap.xml/robots.txt are not HTML and are
  covered by the new `check_sitemap()`. No change in behaviour.
- **Referenced static files**: unchanged. `static/favicon.ico` is still copied to
  `_site/static/` because `base.html` links it; the root copy now comes from the route (same bytes).
- `pages` passed to `build()` and the sitemap both come from `public_page_paths()`, so the
  built page set and the sitemap cannot disagree.

### `tools/check_site.py`
1. Docstring: list the new checks; remove the "may not serve them" idea.
2. New constant `ROBOTS_TEMPLATE` written out literally in check_site (not imported from app, so
   the check is an independent statement of the expected text):
   `"User-agent: *\nAllow: /\nDisallow: /admin\n\nSitemap: {site}/sitemap.xml\n"`.
   A small helper `sitemap_entries(xml_bytes)` -> list of `(loc, lastmod)` using ElementTree
   with the 0.9 namespace, plus root-tag check.
3. New local section `check_seo_files(site, build_static)` ("Sitemap, robots.txt, favicon"),
   called from `main()` after `check_pages` (inside the existing request context):
   - `/sitemap.xml`: 200, `xml` in Content-Type, parses, root is
     `{http://www.sitemaps.org/schemas/sitemap/0.9}urlset` (AC1).
   - loc paths == `set(build_static.page_paths(site)) - site.NOT_IN_SITEMAP`, no duplicates (AC2).
   - no loc contains `/admin`, `/go/`, `/enquiry/thank-you/` (AC3).
   - every loc starts with `site.SITE_URL + "/"`, ends with `/`, and a test-client GET of its
     path is 200 (AC4).
   - every lastmod matches `^\d{4}-\d{2}-\d{2}$` and equals `date.today().isoformat()` (AC5).
   - `/robots.txt`: 200, Content-Type starts with `text/plain`, body ==
     `ROBOTS_TEMPLATE.format(site=site.SITE_URL)` (AC7).
   - `/favicon.ico`: 200, Content-Type starts with `image/`, body == `static/favicon.ico` bytes (AC12).
   Using `site.SITE_URL` everywhere means running the check with `AR_SITE_URL=https://example.test`
   verifies AC8 with no extra code.
4. `check_static_build()`: after a successful build, also check `_site/robots.txt` equals the
   expected text and the loc set of `_site/sitemap.xml` equals the loc set from the Flask
   `/sitemap.xml` (both use fresh databases filled from `data/`, so same content) (AC9).
   Compare locs only, not lastmod, so a run across midnight cannot fail.
5. `check_live()`:
   - New option `--live-url URL` (default `https://arcooling.in`) used as the base for every
     live request; the *expected site address* stays `LIVE_URL = "https://arcooling.in"`.
     This is what makes AC10 testable (point it at a server that lacks the routes).
   - Add `/favicon.ico` to the path list. **Remove the NOTE special case** (lines 131-135): any
     HTTPError on any path is a failure (R8).
   - New live checks, each its own PASS/FAIL line: robots.txt body == template with `LIVE_URL`;
     sitemap.xml parses with the right root and has at least one entry; every loc starts with
     `LIVE_URL + "/"`, ends with `/`, has no `/admin`, `/go/`, `/enquiry/thank-you/`; then a
     sequential GET of each loc path against the base URL must be 200 (R4; roughly 100 small
     requests, only when `--live` is used); favicon bytes == local `static/favicon.ico`.
   - When the base is the default, also GET `https://www.arcooling.in/robots.txt` and require the
     final URL (after urllib follows the redirect) to be `https://arcooling.in/robots.txt` (AC11).
   - Do **not** compare the live loc set with the local one (live DB may differ; see Risks).

### No changes
`store.py`, templates, `static/`, `data/`, `deploy/oracle/*` (Caddy already proxies every path
to the app and already redirects `www.`), `requirements.txt`, `setup.sh`.

## Data & migration
None. No JSON shape or database change. The live sitemap reads the existing collections.

## URLs & SEO
- New: `/sitemap.xml` (application/xml), `/robots.txt` (text/plain), `/favicon.ico`
  (image/vnd.microsoft.icon, cached 1 day). None of them has a trailing slash; they are files,
  not pages, and are not listed in the sitemap.
- No existing URL changes; `/go/<id>/`, `/admin*`, 404 handling untouched (R10).
- robots.txt gains `Disallow: /admin` (Q1). Sitemap entries keep today's date as lastmod (Q2).
- `www.arcooling.in/...` keeps redirecting via Caddy.

## Deployment notes
- Merge to `main` = live within 5 minutes (update.sh pulls and restarts). No setup.sh run, no
  live DB step, no new packages.
- Merge order: this branch sits on `feature/website-team` (PR #4), which brings
  `tools/check_site.py`. Merge PR #4 first (or merge this PR, which contains it).
- After going live: run `tools/check_site.py --live` (AC10/AC11/AC12 live part). The owner may
  then resubmit the sitemap in Search Console (out of scope, owner action).

## Test plan
| AC | How |
|----|-----|
| AC1 | check_site local: status, Content-Type, ElementTree parse, root tag. Manually also via `serve.py` + browser/curl. |
| AC2 | check_site local: loc paths == `page_paths()` - `NOT_IN_SITEMAP` (constant now lives in `app.py`, read as `site.NOT_IN_SITEMAP`); duplicate count. |
| AC3 | check_site local + live: forbidden substrings. |
| AC4 | check_site local: prefix/suffix and test-client GET of each loc. |
| AC5 | check_site local: regex and == today. |
| AC6 | Manual, throwaway DB (`AR_DATABASE_PATH` to a temp file), `app.py`, log in to admin. See Question 1: admin edits existing records, so: change an existing product's `slug` -> new URL appears in /sitemap.xml and old one disappears, no restart; add a part with `slug`+`specs` to a spare-part category (or a model to a compressor brand) -> its page appears; remove it -> gone. |
| AC7 | check_site local: exact text vs independent template. |
| AC8 | Run `tools/check_site.py --skip-build` with `AR_SITE_URL=https://example.test`; all sitemap/robots checks pass using that address. Optionally also run the build with it and inspect `_site/robots.txt`. |
| AC9 | check_site static-build section: build passes (incl. new `check_sitemap()`), `_site/robots.txt` text and `_site/sitemap.xml` loc set equal the Flask versions. |
| AC10 | `check_site.py` passes. Negative: run `serve.py` from a `main` checkout (no new routes) on 127.0.0.1:8080 and run `check_site.py --skip-build --live --live-url http://127.0.0.1:8080` -> must report FAIL for sitemap/robots/favicon. (Simplest alternative: `python -m http.server` on an empty folder; everything fails.) |
| AC11 | After merge: `check_site.py --live` (sitemap content, every loc 200, robots text, www redirect). |
| AC12 | check_site local (bytes, `image/` type) and live (bytes vs local file). |

## Risks & mitigations
- **Sitemap lists a page that does not render live** (e.g. an admin edit leaves a record that
  makes its page 500). The sitemap cannot cheaply render every page per request. Mitigation: the
  page list uses the same functions the routes use, so slugs match; `--live` fetches every loc.
  A record with a missing `slug` makes `public_page_paths()` raise (as the build does today), so
  /sitemap.xml would 500 rather than silently list wrong pages - loud and visible in `--live`.
- **robots.txt mistake hides the site**: exact text compared against an independent literal
  locally, in the build output and live.
- **Live vs data/ differ**: expected; checks never compare the live loc set with local content.
- **Server load**: a few SQLite reads per sitemap request; no cache, no background job; about one
  page render. Crawlers fetch it rarely.
- **Content-type differences across OS** for .ico: pinned explicitly.
- **`--live` gets slower** (~100 extra requests); acceptable for a manual pre/post-deploy check.
- **Name clash**: the view function is called `robots_txt`/`sitemap`/`favicon`; no existing
  endpoint uses these names (checked app.py).

## Coordinator decisions (2026-11-16)
Both questions below are accepted as recommended (no scope change, so not escalated to the
owner): AC6 is tested by slug rename + adding/removing a spare part or compressor model in an
existing record (and `store.save_record` on the throwaway DB for a whole new product);
`NOT_IN_SITEMAP` moves to `app.py`.

## Questions for requirements
1. **AC6 says "add a product in admin"**, but the admin can only edit existing records
   (`/admin/<collection>/<item>/edit`); there is no "add product" button. Recommended answer:
   satisfy AC6 by (a) renaming an existing product's slug in admin and (b) adding/removing a
   spare part with its own page (or a compressor model) inside an existing record, both of which
   create/remove sitemap entries. Adding a whole new product record can be simulated with
   `store.save_record("products", ...)` against the throwaway DB if the tester wants it.
2. **AC2 refers to `NOT_IN_SITEMAP` in build_static.py**; it moves to `app.py`
   (`site.NOT_IN_SITEMAP`). Recommended: accept; same value, single source.
