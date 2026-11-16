# Implementation: Serve sitemap.xml, robots.txt and favicon.ico on the live site

## Summary
The Flask app now answers `/sitemap.xml`, `/robots.txt` and `/favicon.ico` itself, so the
Oracle server serves them. The list of public pages moved from `tools/build_static.py` into
`app.py` (`public_page_paths()`); the sitemap is built from the live database on every
request, so admin edits show up straight away. The static build no longer writes these files
by hand: it fetches them from the same routes, so the live and static versions cannot drift.
`robots.txt` now also has `Disallow: /admin` (owner decision Q1); `<lastmod>` stays today's
date (Q2). `tools/check_site.py` checks all three files locally, in the static build and live,
and a missing live file is now a failure instead of a NOTE.

## Files changed
- `app.py`: `datetime.date`, `Response`, `send_from_directory` imports; `NOT_IN_SITEMAP` moved
  here; new `public_page_paths()` (same endpoints and order as the old `page_paths`, plus
  de-duplication), `sitemap_paths()`, `render_sitemap()` (locs XML-escaped), `render_robots_txt()`;
  routes `sitemap` (application/xml), `robots_txt` (text/plain), `favicon`
  (image/vnd.microsoft.icon, `max_age=86400`), placed after `share_page`. Stale `__main__`
  comment fixed (live site = serve.py on Oracle).
- `tools/build_static.py`: `page_paths(site)` is now a thin wrapper around
  `site.public_page_paths()`; `NOT_IN_SITEMAP`, the `date` import, the hand-written
  sitemap/robots writers and the favicon copy are gone; `ROOT_FILES` are fetched from the app's
  routes (build exits if any is not 200); new `check_sitemap()` (every `<loc>` must be a built
  page) called after `check_links()`; docstring and final message updated.
- `tools/check_site.py`: docstring; `SITEMAP_NS`, independent `ROBOTS_TEMPLATE`,
  `FORBIDDEN_IN_SITEMAP`; helpers `sitemap_entries()`, `bad_locs()`, `favicon_bytes()`, `fetch()`;
  new local section `check_seo_files()`; `check_static_build(site)` also compares
  `_site/robots.txt` text and `_site/sitemap.xml` loc set with the app; `check_live(site, base_url)`
  adds `/favicon.ico`, drops the NOTE special case, checks robots text, sitemap validity and
  addresses, GETs every sitemap page one by one, favicon bytes, and the www redirect (only when
  the base is the real site); new option `--live-url`.
- `docs/work/2026-11-16-live-sitemap-robots/01-requirements.md`, `02-design.md`, this file.

## Requirements covered
- **R1 / AC1**: `/sitemap.xml` route, `application/xml; charset=utf-8`, 0.9 `urlset`. Checked in `check_seo_files`.
- **R2 / AC2 / AC6**: `public_page_paths()` reads the database on every request (no cache).
  check_site compares loc set with `page_paths()` minus `NOT_IN_SITEMAP` and checks duplicates.
  AC6 smoke-tested: renaming a product slug with `store.save_record` on a throwaway DB moved the
  entry in `/sitemap.xml` with no restart, and the new address returned 200.
- **R3 / AC3**: `NOT_IN_SITEMAP`; `/go/`, admin, 404 are never in the list; `bad_locs()` checks
  local and live.
- **R4 / AC4**: full `SITE_URL` prefix, trailing `/`, de-duplicated; every loc GET 200 locally,
  in the build (`check_sitemap`) and live (`--live` fetches every loc).
- **R5 / AC5**: `date.today().isoformat()`; checked by regex and == today.
- **R6 / AC7**: `render_robots_txt()` with `Disallow: /admin`, `text/plain`; compared to the
  independent `ROBOTS_TEMPLATE` locally, in the build and live.
- **R7 / AC9**: one page list in `app.py`; build fetches the files from the routes; check_site
  compares the built files with the app's.
- **R8 / AC10**: `--live` fails on any non-200 (NOTE removed); local checks cover the routes.
- **R9**: no new packages; a few SQLite reads per sitemap request.
- **R10**: no existing URL changed; `/go/<id>/` untouched (share page checks pass).
- **R11 / AC12**: `/favicon.ico` route, pinned icon type, bytes compared locally and live.
- **AC8**: `AR_SITE_URL=https://example.test` run of check_site passes (incl. build; `_site/`
  robots.txt, sitemap and CNAME use example.test).
- **AC11**: covered by `--live` after deployment (www redirect check included).

## Deviations from design
- `build_static.check_sitemap()` compares `output_file(path)` without `unquote`, matching how
  pages are written by `build()` (from the raw `url_for` path).
- `fetch()` returns `error.geturl()` for HTTP errors so a failed redirect reports the final address.
- Design's test plan mentions `store.save_record` to simulate a whole new product: it can only
  replace an existing record (raises `KeyError` otherwise). A tester wanting a brand-new record
  must insert a row directly in the throwaway DB, or use the slug-rename / spare-part routes.
- `check_live` also requires the live sitemap and robots content types (`xml`, `text/plain`)
  and the favicon type (`image/`), per AC7/AC12.

## Checks run
- `.venv/Scripts/python tools/check_site.py` -> ALL CHECKS PASSED (153 pages, 152 in sitemap,
  7 share pages, build 153 pages + 404, built robots/sitemap match the app).
- `AR_SITE_URL=https://example.test .venv/Scripts/python tools/check_site.py` -> ALL CHECKS PASSED (AC8).
- `.venv/Scripts/python tools/check_site.py --skip-build --live` -> FAILS as expected (live
  server lacks this code): `/sitemap.xml -> 404; /robots.txt -> 404; /favicon.ico -> 404`, plus
  robots text, sitemap validity, favicon and www-redirect checks (the www URL redirects but ends
  at the 404 robots.txt).
- `--live --live-url http://127.0.0.1:8765` against this branch's `serve.py` (throwaway DB):
  all live checks PASS, 152 sitemap pages open.
- `--live --live-url http://127.0.0.1:8766` against `python -m http.server` on an empty folder:
  4 FAILs (AC10 negative).
- Headers via test client: sitemap `application/xml; charset=utf-8`, robots
  `text/plain; charset=utf-8`, favicon `image/vnd.microsoft.icon`, `Cache-Control: public, max-age=86400`;
  `/sitemap.xml/` and `/favicon.ico/` give 404.

## Commits
See the final report (hash of the commit on `fix/live-sitemap-robots`).
