# Serve sitemap.xml and robots.txt on the live site

## Goal
"Google should be able to find the list of all my pages again." Since the move to the Oracle
server, https://arcooling.in/sitemap.xml and https://arcooling.in/robots.txt return
"page not found". Bring them back with the same content they had on GitHub Pages.

## Users & context
- Search engines (Google, Bing) and Google Search Console, which read these two files to find
  and recrawl the site's pages. Visitors never see them.
- The owner, who may have submitted the sitemap in Search Console. Today it reports an error.

## Current behaviour
- Live (checked 2026-11-16): `GET https://arcooling.in/sitemap.xml` returns 404 and
  `GET https://arcooling.in/robots.txt` returns 404. `app.py` has no route for either path.
- `tools/build_static.py` (GitHub Pages copy, no longer what visitors see) writes them as files:
  - **sitemap.xml**: one `<url><loc>https://arcooling.in<path></loc><lastmod>YYYY-MM-DD</lastmod></url>`
    per public page, where the date is the build date. The pages come from `page_paths()`:
    home, /products/, /services/, /parts/, /clients/, /about/, /enquiry/, /privacy/, every
    product, every service, /parts/compressors/ and every compressor model, every gas, every
    copper coil that has a slug, and every spare part with its own page.
    `NOT_IN_SITEMAP = {"/enquiry/thank-you/"}` is left out. Never listed: /go/<id>/ share
    pages (they are `noindex`), /admin pages, the 404 page.
  - **robots.txt**: exactly
    ```
    User-agent: *
    Allow: /

    Sitemap: https://arcooling.in/sitemap.xml
    ```
    It does **not** block /admin today.
  - The site address comes from `SITE_URL` in `app.py` (env `AR_SITE_URL`, default https://arcooling.in).
- `tools/check_site.py --live` asks for both files but only prints a NOTE when they are
  missing (lines 131-135), so the missing files never made the check fail.
- On the live server, products, services and parts come from the database that the admin
  edits, so the live list of pages can differ from the `data/` files the static build uses.

## Requirements
- **R1** `https://arcooling.in/sitemap.xml` returns status 200 with an XML content type and a
  valid sitemap (`urlset` in the `http://www.sitemaps.org/schemas/sitemap/0.9` namespace).
- **R2** The sitemap lists the same set of public pages that `build_static.py` builds (see
  "Current behaviour"), worked out from the **live content**, so a product, service or part
  added, renamed or removed in admin shows up in (or drops out of) the sitemap without a code change.
- **R3** The sitemap does not list: /enquiry/thank-you/, any /go/<id>/ share page, any /admin
  address, the 404 page, or any address that does not return 200.
- **R4** Every `<loc>` is a full address starting with `https://arcooling.in` (the configured
  site address), ends with `/`, appears once, and returns 200 on the live site.
- **R5** Every entry has a `<lastmod>` date in `YYYY-MM-DD` form, as before (see Q2 for which date).
- **R6** `https://arcooling.in/robots.txt` returns status 200 as plain text with the same
  content as the static build (above), with the Sitemap line using the configured site address.
  If the owner agrees to Q1, it also has `Disallow: /admin` under `User-agent: *`.
- **R7** The static build keeps producing sitemap.xml and robots.txt, and the live and static
  versions agree: same page list (given the same content) and same robots.txt text. They
  should not be able to drift apart when someone adds a new kind of page later.
- **R8** `tools/check_site.py --live` fails (not just a NOTE) when either file is missing or
  not 200 on the live site. The local checks also confirm both addresses work in the Flask app.
- **R9** Light on the 1 GB server: no new packages; answering these two addresses costs about
  the same as a normal page.
- **R10** No public page address changes; /go/<id>/ pages keep working as now.

## Acceptance criteria
- **AC1** Locally (`serve.py`): GET /sitemap.xml returns 200, `Content-Type` contains `xml`,
  and the body parses as XML with root `{http://www.sitemaps.org/schemas/sitemap/0.9}urlset`.
- **AC2** The set of `<loc>` paths equals `page_paths()` from `build_static.py` minus
  `NOT_IN_SITEMAP`, for the same content. No duplicates.
- **AC3** No `<loc>` contains `/admin`, `/go/` or `/enquiry/thank-you/`.
- **AC4** Every `<loc>` starts with `https://arcooling.in/`, ends with `/`, and a local GET of
  each path returns 200.
- **AC5** Every `<lastmod>` matches `^\d{4}-\d{2}-\d{2}$` (and follows the Q2 decision).
- **AC6** Add a product in a local admin session (throwaway database) -> its page appears in
  /sitemap.xml without a restart; remove it -> it disappears.
- **AC7** GET /robots.txt returns 200, `Content-Type` starts with `text/plain`, and the body
  equals the static-build text (plus `Disallow: /admin` if Q1 = yes).
- **AC8** With `AR_SITE_URL` set to another address, both files use that address.
- **AC9** `tools/build_static.py` still passes; `_site/sitemap.xml` and `_site/robots.txt`
  have the same URLs/text as the Flask versions for the same content.
- **AC10** `tools/check_site.py` passes; with the live check pointed at a server where one of
  the files is 404, `--live` reports a failure.
- **AC11** After going live: `https://arcooling.in/sitemap.xml` and `/robots.txt` return 200
  with the above content; `https://www.arcooling.in/robots.txt` redirects to the main address.

## Out of scope
- Submitting or resubmitting the sitemap in Google Search Console (the owner does that; see
  Risks).
- Image or news sitemaps, sitemap index files, `changefreq`/`priority` tags.
- Adding `noindex` to admin pages, and the other items under "Next candidates".

## Risks
- **Wrong page list = SEO harm**: listing pages that 404 or leaving out real pages. Covered by
  AC2-AC4 and AC6.
- **Live content differs from `data/`**: the live sitemap must follow the live database, not
  the JSON files; testers must not assume the two lists are identical on the live site.
- **robots.txt mistakes can hide the whole site** (e.g. `Disallow: /`). AC7 compares the exact text.
- `Disallow: /admin` is not a lock: it only asks well-behaved crawlers not to visit; the
  login stays the protection. It also tells anyone reading robots.txt where admin is (it is
  already at the obvious /admin).
- Going live = merging to `main`; the server picks it up within 5 minutes.
- This branch is based on `feature/website-team` (PR #4 not merged yet); merge order matters.

## Open questions
- **Q1** Should robots.txt ask search engines to stay out of /admin? The old file did not.
  **Proposed default: yes, add `Disallow: /admin`** (harmless, keeps the login page out of
  search results).
- **Q2** Which date goes in `<lastmod>`? The old sitemap used the build date (every page
  "changed" on every push). Served live, "today" would mean every page always looks freshly
  changed, which Google learns to ignore. **Proposed default: keep the established behaviour
  (today's date) for this fix**; a real "last changed" date per page can be a later improvement.

## Owner decisions (2026-11-16)
- Requirements **approved** as written.
- **Q1 = yes**: robots.txt gets `Disallow: /admin` under `User-agent: *`.
- **Q2 = proposed default**: `<lastmod>` stays today's date for this fix.
- **Scope added: `/favicon.ico`** (next candidate 2) is part of this fix:
  - **R11** `https://arcooling.in/favicon.ico` returns 200 with the same bytes as
    `static/favicon.ico` and an icon content type; it is not listed in the sitemap.
  - **AC12** Locally and after going live, GET /favicon.ico returns 200, an image/icon
    content type, and a body identical to `static/favicon.ico`.
- **Not in this fix**: hiding the sample reviews (next candidate 1) — a separate job later.

## Next candidates (found while checking; not in this fix)
1. **Sample reviews are showing on the live home page.** All six reviews on https://arcooling.in/
   show a "Sample" badge. `SHOW_SAMPLE_CONTENT` in `app.py` hides samples only when
   `AR_STATIC_BUILD=1`, which the static build sets but the Oracle server does not. Visitors see
   made-up reviews marked "Sample", which hurts trust. High value, small effort; arguably more
   urgent than this fix.
2. **`/favicon.ico` returns 404 on the live site.** The static build copied `static/favicon.ico`
   to the site root because some browsers and tools ask for that address directly. Pages link
   the icon at `/static/favicon.ico`, so browser tabs and Google still find it; low impact, tiny
   effort (could be bundled with this fix if the owner wants).
3. Other static-build-only files need nothing: `CNAME` and `.nojekyll` are GitHub Pages only,
   and the live 404 page is already served by the Flask error handler.
